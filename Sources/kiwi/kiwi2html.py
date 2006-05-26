#!/usr/bin/env python
# Encoding: iso-8859-1
# -----------------------------------------------------------------------------
# Project           :   Kiwi
# -----------------------------------------------------------------------------
# Author            :   Sebastien Pierre (SPE)           <sebastien@type-z.org>
# -----------------------------------------------------------------------------
# Creation date     :   07-Feb-2006
# Last mod.         :   15-Mar-2006
# History           :
#                       15-Mar-2006 Added support for title headers
#                       06-Mar-2006 Uses the templates processor
#                       22-Feb-2006 Fixes, added reference and link support
#                       14-Feb-2006 Updated to new table model
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
import kiwi.templates

#------------------------------------------------------------------------------
#
#  Processing functions
#
#------------------------------------------------------------------------------

class Processor(kiwi.templates.Processor):

	def generate( self, xmlDocument, bodyOnly=False, variables={} ):
		node = xmlDocument.getElementsByTagName("Document")[0]
		self.variables = variables
		if bodyOnly:
			for child in node.childNodes:
				if child.nodeName == "Content":
					return convertContent_bodyonly(child)
		else:
			return convertDocument(node)

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
$(References)
</body>
</html>""")

def convertContent( element ):
	return process(element, """ <div id='#content'>$(*)</div>""")

def convertContent_bodyonly( element ):
	return process(element, """$(*)""")

def convertContent_table( element ):
	return process(element, """<tbody>$(*)</tbody>""")

def convertHeader( element ):
	return process(element, """<title>$(Title/title)</title>""")

def convertSection( element ):
	return process(element, """<div class="section"><h2>$(Heading)</h2></div><div>$(Content:section)</div>""")

def convertReferences( element ):
	return process(element, """<div id="references">$(Entry)</div>""")

def convertEntry( element ):
	return process(element, """<div class="entry"><div class="name"><a name="%s">%s</a></div><div class="content">$(*)</div></div>""" %
	(element.getAttributeNS(None, "id"), element.getAttributeNS(None, "id")))

def convertHeader_title( element ):
	return process(element, """<div
	class="title">$(Title/title:header)$(Title/subtitle:header)</div>$(Meta)""")

def converttitle_header( element ):
	return process(element, """<h1>$(*)</h1>""")

def convertsubtitle_header( element ):
	return process(element, """<h2>$(*)</h2>""")

def convertParagraph( element ):
	return process(element, """<p>$(*)</p>""")

def convertList( element ):
	return process(element, """<ul>$(*)</ul>""")

def convertListItem( element ):
	return process(element, """<li>$(*)</li>""")

def convertTable( element ):
	return process(element, """<table cellpadding="0" cellspacing="0" align="center">$(Caption)$(Content:table)</table>""")

def convertCaption( element ):
	return process(element, """<caption>$(*)</caption>""")

def convertRow( element ):
	try: index = element.parentNode.childNodes.index(element) % 2 + 1
	except: index = 0 
	classes = ( "", "even", "odd" )
	return process(element, """<tr class='%s'>$(*)</tr>""" % (classes[index]))

def convertCell( element ):
	return process(element, """<td>$(*)</td>""")

def convertBlock( element ):
	title = element.getAttributeNS(None,"title") or element.getAttributeNS(None, "type") or ""
	css_class = ""
	if title:
		css_class=" class='%s'" % (element.getAttributeNS(None, "type").lower())
		title = "<div class='title'>%s</div>"  % (title)
	return process(element, """<blockquote%s>%s$(*)</blockquote>""" % (css_class, title))

def convertlink( element ):
	if element.getAttributeNS(None, "type") == "ref":
		return process(element, """<a href="#%s">$(*)</a>""" %
		(element.getAttributeNS(None, "target")))
	else:
		# TODO: Support title
		return process(element, """<a href="%s">$(*)</a>""" %
		(element.getAttributeNS(None, "target")))

def convertMeta( element ):
	return process(element, "<table id='meta'>$(*)</table>")

def convertmeta( element ):
	return process(element,
	"<tr><td class='name'>%s</td><td class='value'>$(*)</td></tr>" %
	(element.getAttributeNS(None, "name")))

def convertemail( element ):
	mail = ""
	for c in  process(element, """<a href="mailto:$(*)">$(*)</a>"""):
		mail += "&#%d;" % (ord(c))
	return """<a href="mailto:%s">%s</a>""" % (mail, mail)

def converturl( element ):
	return process(element, """<a href="$(*)">$(*)</a>""")

def converturl_header( element ):
	return process(element, """<div class='url'>%s</div>""" % (
	converturl(element)))

def convertterm( element ):
	return process(element, """<span class='term'>$(*)</span>""")

def convertquote( element ):
	return process(element, """&ldquo;<span class='quote'>$(*)</span>&rdquo;""")

def convertemphasis( element ):
	return process(element, """<b>$(*)</b>""")

def convertstrong( element ):
	return process(element, """<strong>$(*)</strong>""")

def convertpre( element ):
	return process(element, """<pre>$(*)</pre>""")

def convertcode( element ):
	return process(element, """<code>$(*)</code>""")

def convertemphasis( element ):
	return process(element, """<b>$(*)</b>""")

def convertbreak( element ):
	return process(element, """<br />""")

def convertnewline( element ):
	return process(element, """<br />""")

# We create the processor, register the rules and define the process variable
processor      = Processor()
name2functions = {}
for symbol in filter(lambda x:x.startswith("convert"), dir()):
	name2functions[symbol] = eval(symbol)
processor.register(name2functions)
process = processor.process

# EOF
