#!/usr/bin/env python
# Encoding: utf8
# -----------------------------------------------------------------------------
# Project           :   Texto
# -----------------------------------------------------------------------------
# Author            :   Sebastien Pierre           <sebastien.pierre@gmail.com>
# License           :   Revised BSD License
# -----------------------------------------------------------------------------
# Creation date     :   19-Nov-2003
# Last mod.         :   16-Aug-2016
# -----------------------------------------------------------------------------

import os, sys, io, imp

__doc__ = """Texto is an advanced markup text processor, which can be used as
an embedded processor in any application. It is fast, extensible and outputs an
XML DOM."""

__pychecker__ = "blacklist=cDomlette,cDomlettec"

import re, string, operator, getopt, codecs

from  texto import parser, formats, VERSION
FORMATS = formats.get()
FORMATS["xml"] = True
FORMATS["dom"] = True

IS_PYTHON3 = sys.version_info[0] > 2
if IS_PYTHON3:
	unicode = str

def ensureUnicode( t, encoding="utf8" ):
	if IS_PYTHON3:
		return t if isinstance(t, str) else str(t, encoding)
	else:
		return t if isinstance(t, unicode) else str(t).decode(encoding)

#------------------------------------------------------------------------------
#
# COMMAND-LINE INTERFACE
#
#------------------------------------------------------------------------------

USAGE = "Texto v."+VERSION+""",
   A flexible tool for converting plain text markup to XML and HTML.
   Texto can be used to easily generate documentation from plain files or to
   convert exiting Wiki markup to other formats.

   See <http://www.github.com/sebastien/texto>

Usage: texto [options] source [destination]

   source:
      The text file to be parsed (usually an .stx file, "-" for stdin)
   destination:
      The optional destination file (otherwise result is dumped on stdout)

Options:

   -i --input-encoding           Specifie the input encoding
   -o --output-encoding          Specify the output encoding
   -t --tab                      The space value for tabs (default=4).
   -f --offsets                  Add offsets information
   -s --stylesheet               Path or URL to the CSS stylesheet (HTML output)
   -O --output-format            Specifies and alternate output FORMAT
   -x --extension                Specifies a comma-separated list of python
                                 modules to load as extension to the parser.
      --body-only                Only returns the content of the <body> element
      --level=n                  If n>0, n will transform HTML h1 to h2, etc...

   The available encodings are   %s
   The available formats are     %s

Misc:
   -h,  --help                   prints this help.
   -v,  --version                prints the version of Texto.
"""

# Error codes

ERROR   = -1
INFO    = 0
SUCCESS = 1

# Normalised encodings

ASCII  = "us-ascii"
LATIN1 = "iso-8859-1"
LATIN2 = "iso-8859-2"
UTF8   = "utf-8"
UTF16  = "utf-16"
MACROMAN  = "macroman"
NORMALISED_ENCODINGS = (UTF8, UTF16, LATIN1, LATIN2, MACROMAN)

# Supported encodings

ENCODINGS = {
	ASCII:ASCII, "usascii":ASCII, "plain":ASCII, "text":ASCII, "ascii":ASCII,
	LATIN1:LATIN1, "latin-1":LATIN1, "latin1":LATIN1, "iso8859":LATIN1,
	"iso8859-1":LATIN1, "iso88591":LATIN1, "iso-88591":LATIN1,
	LATIN2:LATIN2, "latin2":LATIN2, "latin-2":LATIN2, "iso8859-2":LATIN2,
	"iso88592":LATIN2, "iso-88592":LATIN2,
	UTF8:UTF8, "utf8":UTF8,
	UTF16:UTF16, "utf16":UTF16,
	MACROMAN:MACROMAN, "mac-roman":MACROMAN
}

def run( arguments, input=None, noOutput=False ):
	"""Returns a couple (STATUS, VALUE), where status is 1 when OK, 0 when
	informative, and -1 when error, and value is a string.

	The given arguments can be either a string or an array, the input can be
	None (it will be then taken from the arguments), or be a file-like object,
	and the noOutput flag will not output the result on stdout or whatever file
	is given on the command line.
	"""
	if type(arguments) == str: arguments = arguments.split()

	# --We extract the arguments
	try:
		optlist, args = getopt.getopt(arguments, "ahpmfO:vi:o:t:s:x:",\
		["append", "input-encoding=", "output-encoding=", "output-format=",
		"offsets", "help", "html", "tab=", "version",
		"stylesheet=", "extension=",
		"body-only", "bodyonly", "level="])
	except:
		args=[]
		optlist = []

	# We get the list of available encodings
	available_enc = []
	ENCODINGS_LIST=""
	for encoding in sorted(NORMALISED_ENCODINGS):
		try:
			codecs.lookup(encoding)
			available_enc.append(encoding)
			ENCODINGS_LIST+=encoding+", "
		except:
			pass
	ENCODINGS_LIST=ENCODINGS_LIST[:-2]+"."

	usage = USAGE % (ENCODINGS_LIST, ", ".join(list(sorted(FORMATS.keys()))))

	# We set attributes
	show_offsets    = False
	validate_output = 0
	no_style        = 0
	body_only       = 0
	level_offset    = 0
	input_enc       = ASCII
	output_enc      = ASCII
	output_format   = "html"
	stylesheet      = None
	append_list     = []
	extensions      = []
	# FIXME: Why be so restrictive?
	if UTF8 in ENCODINGS:
		input_enc  = UTF8
		output_enc = UTF8
	elif LATIN1 in ENCODINGS:
		input_enc  = LATIN1
		output_enc = LATIN1
	# We parse the options
	for opt, arg in optlist:
		if opt in ('-h', '--help'):
			return (INFO, usage.encode(LATIN1))
		elif opt in ('-v', '--version'):
			return (INFO, VERSION)
		elif opt in ('-i', '--input-encoding'):
			arg = arg.lower()
			if arg in list(ENCODINGS.keys()) and ENCODINGS[arg] in available_enc:
				input_enc=output_enc=ENCODINGS[arg]
			else:
				r  = "Texto error : Specified input encoding is not available, choose between:"
				r += ENCODINGS_LIST
				return (ERROR, r)
		elif opt in ('-o', '--output-encoding'):
			arg = arg.lower()
			if arg in list(ENCODINGS.keys()) and ENCODINGS[arg] in available_enc:
				output_enc=ENCODINGS[arg]
			else:
				r  = "Texto error: Specified output encoding is not available, choose between:"
				r += ENCODINGS_LIST
				return (ERROR, r)
		elif opt in ('-O', '--output-format'):
			arg = arg.lower()
			if arg in list(FORMATS.keys()):
				output_format=arg
			else:
				r  = "Texto error: Given format (%s) not supported. Choose one of:\n" % (arg)
				r += "\n  - ".join(FORMATS)
				return (ERROR, r)
		elif opt in ('-t', '--tab'):
			TAB_SIZE = int(arg)
			if TAB_SIZE<1:
				return (ERROR, "Texto error: Specified tab value (%s) should be superior to 0." %\
				(TAB_SIZE))
		elif opt in ('--body-only', "--bodyonly"):
			no_style      = 1
			body_only     = 1
		elif opt in ('-s', '--stylesheet'):
			stylesheet    = arg
		elif opt in ('-x', '--extension'):
			extensions += [_.strip() for _ in arg.split(",")]
		elif opt in ('-f', '--offsets'):
			show_offsets = True
		elif opt in ('-a', '--append'):
			append_list.append(arg)
		elif opt in ('--level'):
			level_offset = min(10, max(0, int(arg)))

	# We check the arguments
	if input==None and len(args)<1:
		return (INFO, usage.encode("iso-8859-1"))

	# We set default values
	if input == None: source = args[0]
	else: source = None
	output = None
	if len(args)>1: output = args[1]

	#sys.stderr.write("Texto started with input as %s and output as %s.\n"\
	#% (input_enc, output_enc))
	if input: base_dir = os.getcwd()
	elif source=='-': base_dir = os.path.abspath(".")
	else: base_dir = os.path.abspath(os.path.dirname(source))

	# We instanciate the parser
	texto_parser = parser.Parser(base_dir, input_enc, output_enc)

	# We load the extensions
	for ext in extensions:
		# TODO: http://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path#67692
		if os.path.exists(ext):
			name = os.path.basename(ext).rsplit(".", 1)[0]
			module = imp.load_source(name, ext)
		else:
			module = __import__(ext)
		assert module.on_texto_parser, "Module {0} is expected to define `on_texto_parser`".format(ext)
		texto_parser = module.on_texto_parser(texto_parser) or texto_parser

	if source == output and not noOutput:
		return(ERROR, "Cannot overwrite the source file.")

	# We open the input file, taking care of stdin
	if input != None:
		ifile = input
	elif source=="-":
		ifile = sys.stdin
	else:
		try:
			ifile = codecs.open(source,"r",input_enc)
		except:
			return (ERROR, "Unable to open input file: %s" % (input))

	if noOutput: pass
	elif output==None: ofile = sys.stdout
	else: ofile = open(output,"w")

	try:
		data = ifile.read()
	except UnicodeDecodeError as e:
		r  = "Unable to decode input %s as %s\n" % (source, input_enc)
		r += "--> %s\n" % (e)
		return (ERROR, r)

	if source!="-": ifile.close()

	if type(data) != unicode:
		data = data.decode(input_enc)
	xml_document = texto_parser.parse(data, offsets=show_offsets).document

	result = None
	if output_format == "dom":
		return (SUCCESS, xml_document)
	elif output_format == "xml":
		result = xml_document.toprettyxml("  ").encode(output_enc)
		#result = xml_document.toxml().encode(output_enc)
		if not noOutput: ofile.write(result)
	else:
		variables = {}
		variables["LEVEL"] = level_offset
		css_path = None
		if not no_style and css_path:
			if os.path.exists(css_path):
				with file(css_path) as f:
					variables["HEADER"] = "\n<style><!-- \n%s --></style>" % (f.read())
			else:
				variables["HEADER"] = "\n<link rel='stylesheet' type='text/css' href='%s' />" % (css_path)
		variables["ENCODING"] = output_enc
		processor = FORMATS[output_format].processor
		result = processor.generate(xml_document, body_only, variables)
		if result: result = result.encode(output_enc)
		else: result = ""
		if not noOutput: ofile.write(result)
	return (SUCCESS, result)

def text2htmlbody( text, inputEncoding=None, outputEncoding=None, offsets=True, format=None):
	"""Converts the given text to HTML, returning only the body."""

	text = ensureUnicode(text)
	s = io.StringIO(text)
	command = "-m --body-only"
	if format: command += " -O" + str(format)
	if offsets: command += " -f"
	if inputEncoding: command += " -i " + inputEncoding
	if outputEncoding: command += " -o " + outputEncoding
	_, text = run(command + " --", s, noOutput=True)
	s.close()
	return text

def runAsCommand():
	status, result = run(sys.argv[1:])
	if status == ERROR:
		sys.stderr.write(result + "\n")
		sys.exit(-1)
	elif status == INFO:
		sys.stdout.write(result + "\n")
		sys.exit(0)

if __name__ == "__main__":
	runAsCommand()

# EOF - vim: tw=80 ts=4 sw=4 noet
