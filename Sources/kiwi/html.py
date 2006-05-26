#!/usr/bin/env python
# Encoding: iso-8859-1
# -----------------------------------------------------------------------------
# Project           :   Kiwi
# -----------------------------------------------------------------------------
# Author            :   Sebastien Pierre (SPE)           <sebastien@type-z.org>
# -----------------------------------------------------------------------------
# Creation date     :   10-Fev-2006
# Last mod.         :   10-Fev-2006
# History           :
#                       10-Feb-2006 Minor bug fixes, and added docuemntation.
#                       07-Feb-2006 First implementation
#
# Bugs              :
#                       -
# To do             :
#                       -
#

import re, xml.dom
import sys
from kiwi.formatting import *

EXPRESSION_TABLE = None
FUNCTIONS        = None
RE_EXPRESSION    =re.compile("\$\(([^\)]+)\)")
variables        = {}

__doc__ = """\
The HTML module implements a simple way to convert an XML document to another
format (here, we have HTML) by expanding very simple XPath-like expressions. Of
course, it is a very-small subset of what you could do in XSLT, but it has a
Python syntax and is very, very easy to use.

At first, your define `convertXXX' functions where XXX is your case-sensitive
tagName. All these functions should take an element as parameter and run the
`process' function with the element and template string as parameter.

Expressions like `$(XXX)' (XXX being the expression) in the template strings
will be expanded by procesing the set of nodes indicated by the XXX expression.

 - $(*) will process all children
 - $(MyNode) will process only nodes with 'MyNode' tagName
 - $(MyParent/MyNode) will process only the children of MyParent named MyNode
 - $(MyNode:alt) will use the function `convertMyNode_alt' instead of the
   default 'convertMyNode', if available. This allows to setup 'processing
   modes' for your document (like table of content, references, etc).

"""

#------------------------------------------------------------------------------
#
#  Processing functions
#
#------------------------------------------------------------------------------

def buildExpressionTable():
	"""Fills the EXPRESSION_TABLE which maps element names to processing
	functions."""
	global EXPRESSION_TABLE
	EXPRESSION_TABLE = {}
	for name in FUNCTIONS:
		if name.startswith("convert"):
			ename = name[len("convert"):]
			ename = ename.replace("_", ":")
			EXPRESSION_TABLE[ename] = eval(name)

def resolveSet(element, names ):
	"""Resolves the set of names in the given element. When ["Paragraph"] is
	given, then all child paragraph nodes of the current node will be returned,
	while ["Section", "Paragraph"] will return all paragraphs for all
	sections."""
	s = []
	if len(names) == 1:
		name = names[0]
		for child in element.childNodes:
			if name != "*" and not child.nodeType == xml.dom.Node.ELEMENT_NODE: continue
			if name == "*" or child.tagName == name: s.append(child)
	else:
		name = names[0]
		for child in element.childNodes:
			if name != "*" and not child.nodeType == xml.dom.Node.ELEMENT_NODE: continue
			if name == "*" or child.tagName == name: s.extend(resolveSet(child, names[1:]))
	return s

def processElement( element, selector=None ):
	"""Processes the given element according to the EXPRESSION_TABLE, using the
	given selector to select an alternative function."""
	if element.nodeType == xml.dom.Node.TEXT_NODE:
		return escapeHTML(element.data)
	elif element.nodeType == xml.dom.Node.ELEMENT_NODE:
		fname = element.tagName
		if selector: fname += ":" + selector
		func  = EXPRESSION_TABLE.get(fname)
		# There is a function for the element in the EXPRESSION TABLE
		if func:
			return func(element)
		# Otherwise we simply expand its text
		else:
			return "".join([processElement(e) for e in element.childNodes])
	else:
		return ""

def interpret( element, expression ):
	"""Interprets the given expression for the given element"""
	if EXPRESSION_TABLE == None: buildExpressionTable()
	# =VARIABLE means that we replace the expression by the content of the
	# variable in the varibales directory
	if expression.startswith("="):
		vname = expression[1:].upper()
		return variables.get(vname) or ""
	# Otherwise, the expression is a node selection expression, which may also
	# have a selector
	elif expression.rfind(":") != -1:
		names, selector = expression.split(":")
	# There may be no selector as well
	else:
		names           = expression
		selector        = None
	names = names.split("/")
	r     = ""
	for element in resolveSet(element, names):
		r += processElement(element, selector)
	return r

# SYNTAX: $(EXPRESSION)
# Where EXPRESSION is a "/" separated list of element names, optionally followed
# by a colon ':' and a name
def process( element, text ):
	i = 0
	r = ""
	while i < len(text):
		m = RE_EXPRESSION.search(text, i)
		if not m:
			r += text[i:]
			break
		else:
			r += text[i:m.start()]
		r+= interpret(element, m.group(1))
		i = m.end()
	return r

def generate( xmlDocument, vars={} ):
	global variables
	variables = vars
	return convertDocument(xmlDocument.getElementsByTagName("Document")[0])

#------------------------------------------------------------------------------
#
#  Actual element processing
#
#------------------------------------------------------------------------------

def convertDocument(element):
	 return process(element, """\
<html>
<head>$(Header)$(=HEADER)</head>
<body>
$(Header:title)
$(Content)
</body>
</html>""")

def convertHeader( element ):
	return process(element, """<title>$(Title/title)</title>""")

def convertSection( element ):
	return process(element, """<div class="section"><h2>$(Heading)</h2></div><div>$(Content:section)</div>""")

def convertHeader_title( element ):
	return process(element, """<div class="title"><h1>$(Title/title)</h1></div>""")

def convertParagraph( element ):
	return process(element, """<p>$(*)</p>""")

def convertList( element ):
	return process(element, """<ul>$(*)</ul>""")

def convertListItem( element ):
	return process(element, """<li>$(*)</li>""")

def convertTable( element ):
	return process(element, """<table cellpadding="0" cellspacing="0" align="center">$(*)</table>""")

def convertRow( element ):
	try: index = element.parentNode.childNodes.index(element) % 2 + 1
	except: index = 0 
	classes = ( "", "even", "odd" )
	return process(element, """<tr class='%s'>$(*)</tr>""" % (classes[index]))

def convertCell( element ):
	return process(element, """<td>$(*)</td>""")

def convertContent( element ):
	return process(element, """ <div id='#content'>$(*)</div>""")

def convertBlock( element ):
	return process(element, """ <blockquote>$(*)</blockquote>""")

def convertemail( element ):
	return process(element, """ <a href="mailto:$(*)">$(*)</a>""")

def convertTerm( element ):
	return process(element, """ <b>$(*)</b>""")

def convertpre( element ):
	return process(element, """<pre>$(*)</pre>""")

def convertcode( element ):
	return process(element, """<code>$(*)</code>""")

def convertemphasis( element ):
	return process(element, """<b>$(*)</b>""")

def convertbreak( element ):
	return process(element, """<br />""")

def convertnewline( element ):
	return process(element, """&nbsp;""")

# We set this at that time because we wait for all functions to be declared
FUNCTIONS = dir()

# EOF
