# -----------------------------------------------------------------------------
# Project           :   Texto
# -----------------------------------------------------------------------------
# Author            :   Sebastien Pierre           <sebastien.pierre@gmail.com>
# License           :   Revised BSD License
# -----------------------------------------------------------------------------
# Creation date     :   2003-11-19
# Last mod.         :   2021-06-05
# -----------------------------------------------------------------------------

import os
import sys
import argparse
import imp
from typing import Optional, List
from . import formats
from .parser import Parser, ParsingContext

__doc__ = """Texto is an advanced markup text processor, which can be used as
an embedded processor in any application. It is fast, extensible and outputs an
XML DOM.

See <http://www.github.com/sebastien/texto>
"""


FORMATS = formats.get()
FORMATS["xml"] = True
FORMATS["dom"] = True


def run(args=sys.argv[1:], name=None):
    """The command-line interface of this module."""
    if type(args) not in (type([]), type(())):
        args = [args]
    oparser = argparse.ArgumentParser(
        prog="texto",
        description=__doc__,
    )
    # TODO: Rework command lines arguments, we want something that follows
    # common usage patterns.
    oparser.add_argument("files", metavar="FILE", type=str, nargs='+',
                         help='The files to extract dependencies from')
    oparser.add_argument("-o", "--output",    type=str,  dest="output", default="-",
                         help="Specifies an output file")
    oparser.add_argument("-t", "--type",      type=str,  dest="format", default="html",
                         help=f"The format type to be output, one of {', '.join(FORMATS.keys())}")
    oparser.add_argument("-b", "--body-only", action="store_true", default=False,
                         help="Only outputs the body of the document (HTML,XML)")
    oparser.add_argument("-f", "--offsets",   dest="offsets",   action="store_true", default=False,
                         help="Outputs offsets in source file (HTML, XML)")
    oparser.add_argument("-x", "--ext", dest="extensions", nargs="+", default=[],
                         help="Uses the given extension (Python module name)")
    # We create the parse and register the options
    args = oparser.parse_args(args=args)
    out = sys.stdout
    parser = extendParser(Parser, args.extensions or [])
    inputs = args.files or ["-"]
    for _ in inputs:
        if _ == "-":
            data = sys.stdin.read()
        else:
            with open(_) as f:
                data = f.read()
        result = parse(data, offsets=args.offsets, parser=parser)
        r = render(result, args.format)
        print(r)
        out.write(r)


def render(result: ParsingContext, format: str):
    xml_document = result.document
    if format == "dom":
        return xml_document
    elif format == "xml":
        return xml_document.toprettyxml("  ")
    elif format in FORMATS:
        # We use the dynamic formatters to dispatch that
        variables = {}
        variables["LEVEL"] = 0
        css_path = None
        if css_path:
            if os.path.exists(css_path):
                with open(css_path) as f:
                    variables["HEADER"] = "\n<style><!-- \n%s --></style>" % (
                        f.read())
            else:
                variables["HEADER"] = "\n<link rel='stylesheet' type='text/css' href='%s' />" % (
                    css_path)
        processor = FORMATS[format].processor
        return processor.generate(xml_document, False, variables) or ""
    else:
        raise RuntimeError(
            f"Unknown output format: {format}, choose one of {', '.join(FORMATS.keys())}")


def parse(text: str, offsets=False, parser: Optional[Parser] = None) -> ParsingContext:
    parser = parser or Parser()
    result = parser.parse(text, offsets=offsets)
    return result


def extendParser(parser: Parser, extensions: List[str]) -> Parser:
    # We load the extensions
    for ext in extensions:
        # TODO: http://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path#67692
        if os.path.exists(ext):
            name = os.path.basename(ext).rsplit(".", 1)[0]
            module = imp.load_source(name, ext)
        else:
            module = __import__(ext)
        assert module.on_texto_parser, "Module {0} is expected to define `on_texto_parser`".format(
            ext)
        parser = module.on_texto_parser(texto_parser) or texto_parser
        return parser


# ------------------------------------------------------------------------------
#
# COMMAND-LINE INTERFACE
#
# ------------------------------------------------------------------------------


if __name__ == "__main__":
    run()

# EOF
