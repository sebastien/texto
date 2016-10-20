#!/usr/bin/env python
# Encoding: utf8
# -----------------------------------------------------------------------------
# Project           : Texto
# -----------------------------------------------------------------------------
# Author            : Sebastien Pierre             <sebastien.pierre@gmail.com>
# -----------------------------------------------------------------------------
# Creation date     : 19-Nov-2007
# Last mod.         : 16-Aug-2016
# -----------------------------------------------------------------------------

import re, sys, xml.dom
from texto.formats import Processor, escapeHTML

#------------------------------------------------------------------------------
#
# ACTUAL ELEMENT PROCESSING
#
#------------------------------------------------------------------------------

def convertDocument(element):
	return process(element, """\
$(Header:title)
$(Content)
$(References)
""")

def convertHeader( element ):
	return process(element, "# $(Title/title)\n## $(Title/subtitle)\n" )

def convertHeading( element ):
	return process(element, "$(*)")

def convertSection( element ):
	level = int(element.getAttributeNS(None, "_depth"))
	prefix = "#" + "#" * level
	return process(element,
		prefix + " $(Heading)\n\n"
		+ "$(Content:section)"
	)

def convertReferences( element ):
	return process(element, """  $(Entry)""")

def convertParagraph( element ):
	return process(element, """$(*)\n\n""")

def convertParagraph_cell( element ):
	return process(element, """$(*)\n""")

def convertList( element ):
	is_todo = element.getAttributeNS(None, "type")
	attrs = [""]
	return process(element, """$(*)\n\n""")

def convertListItem( element ):
	attrs   = [""]
	is_todo = element.getAttributeNS(None, "todo")
	return process(element, """ - $(*)\n""")

def convertTable( element ):
	return process(element, """$(Content:table)\n\n""")

def convertDefinitionList( element ):
	return process(element, """<dl>\n\n$(*)\n</dl>\n\n""")

def convertDefinitionItem( element ):
	return process(element, """<dt>$(Title)<dt>\n<dd>$(Content)</dd>\n\n""")

def convertRow( element ):
	try: index = element.parentNode.childNodes.index(element) % 2 + 1
	except: index = 0
	classes = ( "", "even", "odd" )
	return process(element, """$(*) |\n""")

def convertCell( element ):
	suffix     = ""
	if element.hasAttributeNS(None, "colspan"):
		suffix = " " + "|" * (int(element.getAttributeNS(None,"colspan")) - 2)
	cell = process(element, "$(*:cell)")[:-1]
	return ("| " + cell + suffix)

def convertBlock( element ):
	title = element.getAttributeNS(None,"title") or element.getAttributeNS(None, "type") or ""
	css_class = ""
	if title:
		css_class=" class='ann%s'" % (element.getAttributeNS(None, "type").capitalize())
		title = "<div class='title'>%s</div>"  % (title)
		div_type = "div"
	elif not element.getAttributeNS(None, "type"):
		div_type = "blockquote"
	return process(element, """<%s%s>%s<div class='content'%s>$(*)</div></%s>""" % (div_type, css_class, title, "", div_type))

def convertMeta( element ):
	return process(element, """---\n$(*)---\n\n""")

def convertmeta( element ):
	return "{0}: {1}\n".format(element.getAttribute("name"), element.getAttribute("value"))

def stringToTarget( text ):
	return text.replace("  ", " ").strip().replace(" ", "-").upper()

def convertlink( element ):
	if element.getAttributeNS(None, "type") == "ref":
		return process(element, """[$(*)][#%s]""" %
		(stringToTarget(element.getAttributeNS(None, "target"))))
	else:
		# TODO: Support title
		return process(element, """[$(*)](%s)""" %
		(element.getAttributeNS(None, "target")))

def converttarget( element ):
	name = element.getAttributeNS(None, "name")
	return process(element, """<a name='%s'>$(*)""" % (stringToTarget(name)))


def convertemail( element ):
	mail = ""
	for c in  process(element, """$(*)"""):
		mail += c
	return """[%s]<mailto:%s>""" % (mail, mail)

def converturl( element ):
	return process(element, """<$(*)>""")

def convertterm( element ):
	return process(element, """*$(*)*""")

def convertquote( element ):
	return process(element, """''$(*)''""")

def convertstrong( element ):
	return process(element, """__$(*)__""")

def convertpre( element ):
	prefix = ""
	if element.hasAttribute("data-lang"):
		prefix += element.getAttribute("data-lang")
	if element.hasAttribute("data-ranges"):
		prefix += "{" + element.getAttribute("data-ranges") + "}"
	return process(element, """```{0}\n$(*)\n```\n\n""".format(prefix))

def convertcode( element ):
	return process(element, """`$(*)`""")

def convertemphasis( element ):
	return process(element, """_$(*)_""")

def convertbreak( element ):
	return process(element, """ """)

def convertnewline( element ):
	return process(element, """ """)

def convertarrow( element ):
	arrow = element.getAttributeNS(None, "type")
	if   arrow == "left":
		return "←"
	elif arrow == "right":
		return "→"
	else:
		return "←→"

def convertdots( element ):
	return "‥"

def convertendash( element ):
	return " -- "

def convertemdash( element ):
	return " -- "

def convertentity( element ):
	return "&%s;" % (element.getAttributeNS( None, "num"))

def defaultProcess( element, selector, processor ):
	if element.getAttribute("_html") == "true":
		if element.nodeName == "script" and (not element.childNodes):
			return element.toprettyxml("").replace("/>",">/**/</script>\n")
		else:
			return element.toprettyxml("")
	else:
		return "".join([processor.processElement(e) for e in element.childNodes])

# We create the processor, register the rules and define the process variable
processor  = Processor(sys.modules[__name__], default=defaultProcess)
process    = processor.process

# EOF - vim: tw=80 ts=4 sw=4 noet
