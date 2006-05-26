#!/usr/bin/env python
# Encoding: iso-8859-1
# -----------------------------------------------------------------------------
# Project           :   Kiwi
# Module            :   Main parser
# -----------------------------------------------------------------------------
# Author            :   Sebastien Pierre (SPE)           <sebastien@type-z.org>
# -----------------------------------------------------------------------------
# Creation date     :   19-Nov-2003
# Last mod.         :   10-Fev-2006
# History           :
#                       10-Feb-2006 Added stylesheet selection mode
#                       07-Feb-2006 Moved some stuff to the core module.
#                       10-Jan-2006 Reverted to minidom support
#                       26-Dec-2004 Moved attributes parsing code (SPE)
#                       22-Dec-2004 Indent bug fix (SPE)
#                       05-Oct-2004 Small fixes, doc update (SPE)
#                       27-Sep-2004 Cleans out empty document elements, logger
#                       handles unicode (SPE)
#                       19-Jan-2004 Split `parseNextInline' into
#                       `findNextInline' and `parseNextInline' (SPE)
#                       13-Jan-2004 Added escaped text support (SPE)
#                       07-Jan-2004 Updated to used 4Suite DOM, for speed (SPE)
#                       15-Dec-2003 Added ensureParent method in context (SPE)
#                       12-Dec-2003 Fixed bugs with empty blocks, rewrote block
#                       indentation function. (SPE)
#                       23-Nov-2003 Added error handling with line and
#                       character. Inserted code for markup recognition in
#                       block end detection (almost working) (SPE)
#                       22-Nov-2003 Added proper tab expansion and
#                       unindentation (SPE)
#                       19-Nov-2003 Integrated code from previous Kiwi, from
#                       24-Apr-2001 to 9-Jul-2003 (SPE)
#
# Bugs              :
#                       -
# To do             :
#                       -
#

import os, sys

__doc__ = """Kiwi is an advanced markup text processor, which can be used as
an embedded processor in any application. It is fast, extensible and outputs an
XML DOM."""

__version__ = "0.7.1"
__pychecker__ = "blacklist=cDomlette,cDomlettec"

import re, string, operator, getopt, codecs

# NOTE: I disabled 4Suite support, as minidom is good as it is right now
# We use 4Suite domlette
#import Ft.Xml.Domlette
#dom = Ft.Xml.Domlette.implementation
# We use minidom implementation
import xml.dom.minidom
dom = xml.dom.minidom.getDOMImplementation()

from kiwi import core, html

#------------------------------------------------------------------------------
#
#  Command-line interface
#
#------------------------------------------------------------------------------

usage = u"Kiwi v."+__version__+u""",
   A flexible tool for converting plain text markup to XML and HTML.
   Kiwi can be used to easily generate documentation from plain files or to
   convert exiting Wiki markup to other formats.

   See <http://www.ivy.fr/kiwi>

Usage: kiwi [options] source [destination]

   source:
      The text file to be parsed (usually an .stx file, "-" for stdin)
   destination:
      The optional destination file (otherwise result is dumped on stdout)

Options:

   -i --input-encoding           Allows to specify the input encoding
   -o --output-encoding          Allows to specify the output encoding
   -t --tab                      The value for tabs (tabs equal N sapces).
                                 Set to 4 by default.
   -p --pretty                   Pretty prints the output XML, this should only
                                 be used for viewing the output.
   -m --html                     Outputs an HTML file corresponding to the Kiwi
                                 document
      --no-style                 Does not include the default CSS in the HTML

   The available encodings are %s

Misc:
   -h,  --help                    prints this help.
   -v,  --version                 prints the version of Kiwi.
"""

# Normalised encodings

ASCII  = "us-ascii"
LATIN1 = "iso-8859-1"
LATIN2 = "iso-8859-2"
UTF8   = "utf-8"
UTF16  = "utf-16"
MACROMAN  = "macroman"
NORMALISED_ENCODINGS = (LATIN1, LATIN2, UTF8, UTF16, MACROMAN)

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


if __name__ == "__main__":

	# --We extract the arguments
	try:
		optlist, args = getopt.getopt(sys.argv[1:], "hpmvi:o:t:",\
		["input-encoding=", "output-encoding=", "help", "html",
		"tab=", "version", "pretty", "no-style", "nostyle"])
	except:
		args=[]
		optlist = []

	# We get the list of available encodings
	available_enc = []
	ENCODINGS_LIST=""
	for encoding in NORMALISED_ENCODINGS:
		try:
			codecs.lookup(encoding)
			available_enc.append(encoding)
			ENCODINGS_LIST+=encoding+", "
		except:
			pass
	ENCODINGS_LIST=ENCODINGS_LIST[:-2]+"."

	usage = usage % (ENCODINGS_LIST)

	# We set attributes
	pretty_print    = 0
	validate_output = 0
	generate_html   = 0
	no_style        = 0
	input_enc       = ASCII
	output_enc      = ASCII
	if LATIN1 in ENCODINGS:
		input_enc  = LATIN1
		output_enc = LATIN1
	elif UTF8 in ENCODINGS:
		input_enc  = UTF8
		output_enc = UTF8

	# We parse the options
	for opt, arg in optlist:
		if opt in ('-h', '--help'):
			print usage.encode(LATIN1); sys.exit()
		elif opt in ('-v', '--version'):
			print __version__
			sys.exit()
		elif opt in ('-i', '--input-encoding'):
			arg = string.lower(arg)
			if arg in ENCODINGS.keys() and ENCODINGS[arg] in available_enc:
				input_enc=ENCODINGS[arg]
			else:
				print "Kiwi error : Specified input encoding is not available, choose between:"
				print ENCODINGS_LIST
				sys.exit(3)
		elif opt in ('-o', '--output-encoding'):
			arg = string.lower(arg)
			if arg in ENCODINGS.keys() and ENCODINGS[arg] in available_enc:
				output_enc=ENCODINGS[arg]
			else:
				print "Kiwi error: Specified output encoding is not available, choose between:"
				print ENCODINGS_LIST
				sys.exit(3)
		elif opt in ('-t', '--tab'):
			TAB_SIZE = int(arg)
			if TAB_SIZE<1:
				print "Kiwi error: Specified tab value (%s) should be superior to 0." %\
				(TAB_SIZE)
				sys.exit(3)
			else:
				sys.stderr.write("Tab value set to %s\n" % (TAB_SIZE))
		elif opt in ('--no-style', "--nostyle"):
			no_style     = 1
		elif opt in ('-p', '--pretty'):
			pretty_print = 1
		elif opt in ('-m', '--html'):
			generate_html = 1

	# We check the arguments
	if len(args)<1:
		print usage.encode("iso-8859-1")
		sys.exit(2)

	# We set default values
	source = args[0]
	output = None
	if len(args)>1: output = args[1]

	#sys.stderr.write("Kiwi started with input as %s and output as %s.\n"\
	#% (input_enc, output_enc))
	if source=='-': base_dir = os.path.abspath(".")
	else: base_dir = os.path.abspath(os.path.dirname(source))

	parser = core.Parser(base_dir, input_enc, output_enc)

	# We open the input file, taking care of stdin
	if source=="-":
		ifile = sys.stdin
	else:
		try:
			ifile = codecs.open(source,"r",input_enc)
		except:
			sys.stderr.write("Unable to open input file.\n")
			sys.exit()

	if output==None: ofile = sys.stdout
	else: ofile = open(output,"w")

	try:
		data = ifile.read()
	except UnicodeDecodeError, e:
		sys.stderr.write("Impossible to decode input %s as %s\n" % (source, input_enc))
		sys.stderr.write("--> %s\n" % (e))
		sys.exit(-1)

	if source!="-": ifile.close()

	xml_document = parser.parse(data)

	if generate_html:
		variables = {}
		css_file = file(os.path.dirname(__file__) + "/screen-kiwi.css")
		if not no_style:
			variables["HEADER"] = "\n<style><!-- \n%s --></style>" % (css_file.read())
		css_file.close()
		ofile.write(html.generate(xml_document, variables).encode(output_enc))
	elif pretty_print:
		#Ft.Xml.Lib.Print.PrettyPrint(xml_document, ofile, output_enc)
		#MiniDom:
		ofile.write(xml_document.toprettyxml("  ").encode(output_enc))
	else:
		#Ft.Xml.Lib.Print.Print(xml_document, ofile, output_enc)
		#MiniDom:
		ofile.write(xml_document.toxml().encode(output_enc))

	if output!=None: ofile.close()

# EOF-UNIX/iso-8895-1-------------------------------@RisingSun//Python//1.0//EN
