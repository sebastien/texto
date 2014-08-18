#!/usr/bin/env python
# Encoding: iso-8859-1
# -----------------------------------------------------------------------------
# Project           :   Texto
# -----------------------------------------------------------------------------
# Author            :   Sebastien Pierre                 <sebastien@type-z.org>
# -----------------------------------------------------------------------------
# Creation date     :   06-Mar-2006
# Last mod.         :   06-Mar-2006
# History           :
#                       06-Mar-2006 First implementation
#                       06-Mar-2006 First implementation
#
# Bugs              :
#                       -
# To do             :
#                       -
#

import re, textwrap, xml.dom
from .templates import Processor

# Text to HTML: http://bhaak.dyndns.org/vilistextum/screenshots.html
# From <http://www.boddie.org.uk/python/HTML.html>
try:
	from html.parser import HTMLParser
except ImportError:
	from html.parser import HTMLParser

# We create the processor, register the rules and define the process variable
processor      = Processor()

#------------------------------------------------------------------------------
#
#  Actual element processing
#
#------------------------------------------------------------------------------

def convertHTML(element):
	return process(element, "$(*)\n")

def convertP(element):
	return "\n".join(textwrap.wrap(process(element, "$(*)"), 79)) + "\n\n"

def convertPRE(element):
	res = "\n"
	for line in process(element, "$(*)").split("\n"):
		res += ">    %s\n" % (line)
	return res + "\n"

def convertUL(element):
	res = ""
	for line in process(element, "$(*)").split("\n"):
		res += "  %s\n" % (line)
	return res + "\n\n"

def convertLI(element):
	lines = process(element, "$(*)").split("\n")
	res = " * " + lines[0]
	for line in lines[1:]:
		res += "   %s\n" % (line)
	return res + "\n"

def convertH1(element):
	res = process(element, "$(*)")
	return "\n" + res + "\n" + "=" * len(res) + "\n\n"

def convertH2(element):
	res = process(element, "$(*)")
	return "\n" + res + "\n" + "-" * len(res) + "\n\n"


name2functions = {}
for symbol in [x for x in dir() if x.startswith("convert")]:
	name2functions[symbol] = eval(symbol)
processor.register(name2functions)
process = processor.process

def convertDocument( text ):
	import BeautifulSoup
	# FUCK ME! This does not work
	doc = BeautifulSoup.BeautifulSoup(text)
	return processor.generate(doc)

if __name__ == "__main__":
	import sys
	fd = file(sys.argv[1], 'rt')
	print(convertDocument(fd.read()))
	fd.close()

# EOF
