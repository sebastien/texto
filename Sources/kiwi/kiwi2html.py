#!/usr/bin/env python
# Encoding: iso-8859-1
# vim: tw=80 ts=4 sw=4 noet fenc=latin-1
# -----------------------------------------------------------------------------
# Project           :   Kiwi
# -----------------------------------------------------------------------------
# Author            :   Sebastien Pierre                 <sebastien@type-z.org>
# -----------------------------------------------------------------------------
# Creation date     :   07-Feb-2006
# Last mod.         :   17-Jul-2006
# -----------------------------------------------------------------------------

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

	def defaultProcessElement( self, element, selector ):
		"""We override this for elements with the 'html' attribute."""
		if element.getAttributeNS(None, "_html"):
			res = "<" + element.nodeName
			att = element.attributes
			for i in range(att.length):
				a = att.item(i)
				if a.name == "_html": continue
				res += " %s='%s'" % (a.name, element.getAttributeNS(None, a.name))
			if element.childNodes:
				res + ">"
				for e in element.childNodes:
					res += self.processElement(e)
				res += "</%s>" % (element.tagName)
			else:
				res += "/>"
			return res
		else:
			return kiwi.templates.Processor.defaultProcessElement(self,element,selector)
		
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
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=$(=ENCODING)" />
<script type="text/javascript">

function init()
{
}

function kiwi_toggleSection(e)
{
	var target = e.target;
	var parent = target.parentNode.parentNode;
	for ( var i=0 ; i<parent.childNodes.length ; i++ )
	{
		var child = parent.childNodes[i];
		if ( child.getAttribute("class") && child.getAttribute("class").indexOf("level",0)==0 )
		{
			if ( child.style.display != "block" )
			{	child.style.display = "block";}
			else
			{	child.style.display = "none";}
		}
	}
}
</script>
$(Header)$(=HEADER)
</head>
<body onload="init()">
$(Header:title)
$(Content)
$(References)
</body>
</html>""")

def convertContent( element ):
	return process(element, """ <div id='content'>$(*)</div>""")

def convertContent_bodyonly( element ):
	return process(element, """$(*)""")

def convertContent_table( element ):
	return process(element, """<tbody>$(*)</tbody>""")

def convertHeader( element ):
	return process(element, """<title>$(Title/title)</title>""")

def convertSection( element ):
	level = int(element.getAttributeNS(None, "_depth")) + 2
	return process(element,
	  '<div class="section"><a class="link" onclick="kiwi_toggleSection(event);"><h%d class="heading">$(Heading)</h%d></a>' % (level, level)
	  + '<div class="level%d">$(Content:section)</div>' % (level)
	)

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

def convertParagraph_cell( element ):
	return process(element, """$(*)<br />""")

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
	return process(element, """<td>$(*:cell)</td>""")

def convertBlock( element ):
	title = element.getAttributeNS(None,"title") or element.getAttributeNS(None, "type") or ""
	css_class = ""
	if title:
		css_class=" class='%s'" % (element.getAttributeNS(None, "type").lower())
		title = "<div class='title'>%s</div>"  % (title)
		div_type = "div"
	elif not element.getAttributeNS(None, "type"):
		div_type = "blockquote"
	return process(element, """<%s%s>%s<div class='content'>$(*)</div></%s>""" % (div_type, css_class, title, div_type))

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
	for c in  process(element, """$(*)"""):
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

def convertcitation( element ):
	return process(element, """&laquo;<span class='citation'>$(*)</span>&raquo;""")

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
