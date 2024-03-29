#!/usr/bin/env python
# -----------------------------------------------------------------------------
# Project           : Texto
# -----------------------------------------------------------------------------
# Author            : Sebastien Pierre             <sebastien.pierre@gmail.com>
# -----------------------------------------------------------------------------
# Creation  date    : 07-Feb-2006
# Last mod.         : 16-Aug-2016
# -----------------------------------------------------------------------------

import sys
import re
import xml.dom
import texto.formats

# ------------------------------------------------------------------------------
#
# PROCESSOR
#
# ------------------------------------------------------------------------------


class Processor(texto.formats.Processor):

    def defaultProcessElement(self, element, selector):
        """We override this for elements with the 'html' attribute."""
        if element.getAttributeNS(None, "_html"):
            res = "<" + element.nodeName
            att = element.attributes
            for i in range(att.length):
                a = att.item(i)
                if a.name == "_html":
                    continue
                res += " %s='%s'" % (a.name,
                                     element.getAttributeNS(None, a.name))
            if element.childNodes:
                res += ">"
                for e in element.childNodes:
                    res += self.processElement(e)
                res += "</%s>" % (element.tagName)
            else:
                res += "/>"
            return res
        else:
            return super(Processor, self).defaultProcessElement(element, selector)

    def on_Document(self, element):
        if self.bodyOnly:
            return self.process(element, """\
	$(header:title)
	$(content)
	$(references)
	""")
        else:
            return self.process(element, """\
	<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
		"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
	<html xmlns="http://www.w3.org/1999/xhtml">
	<head>
	<meta http-equiv="Content-Type" content="text/html; charset=$(=ENCODING)" />
	$(header)$(=HEADER)
	</head>
	<body>
	<div class="use-texto document">
	$(header:title)
	$(content)
	$(references)
	</div>
	</body>
	</html>""")

    def _elementNumber(self, element):
        """Utility function that returns the element number (part of the element
        offset attributes)"""
        number = element.getAttributeNS(None, "_number")
        if number:
            return int(number)
        else:
            return None

    def _wdiv(self, element, text):
        """Wraps the given text in a DIV extended with offsets attributes if the
        given element has offset attributes."""
        number = self._elementNumber(element)
        if number == None:
            return text
        return "<div class='texto N%s' ostart='%s' oend='%s'>%s</div>" % (
            element.getAttributeNS(None, '_number'),
            element.getAttributeNS(None, '_start'),
            element.getAttributeNS(None, '_end'),
            text
        )

    def _wspan(self, element, text):
        """Wraps the given text in a SPAN extended with offsets attributes if the
        given element has offset attributes."""
        number = self._elementNumber(element)
        if number == None:
            return text
        return "<div class='texto N%s' ostart='%s' oend='%s'>%s</div>" % (
            element.getAttributeNS(None, '_number'),
            element.getAttributeNS(None, '_start'),
            element.getAttributeNS(None, '_end'),
            text
        )

    def _wattrs(self, element):
        """Returns the offset attributes of this element if it has any."""
        res = ""
        number = self._elementNumber(element)
        if number != None:
            res = " class='texto N%s' ostart='%s' oend='%s'" % (
                element.getAttributeNS(None, '_number'),
                element.getAttributeNS(None, '_start'),
                element.getAttributeNS(None, '_end')
            )
        if element.attributes:
            for k, v in element.attributes.items():
                if not k.startswith("_"):
                    res += " %s='%s'" % (k, v)
        return res

    def processTextNode(self, element, seelctor, isSelectorOptional=False):
        return texto.formats.escapeHTML(element.data)

    def getSectionNumberPrefix(self, element):
        if not element:
            return ""
        if not element.nodeName in ("chapter", "section"):
            return ""
        parent = element.parentNode
        section_count = 1
        for child in parent.childNodes:
            if child == element:
                break
            if child.nodeName in ("chapter", "section"):
                section_count += 1
        parent_number = self.getSectionNumberPrefix(parent.parentNode)
        if parent_number:
            return "%s.%s" % (parent_number, section_count)
        else:
            return str(section_count)

    def formatSectionNumber(self, number):
        return str(number)

    def on_content(self, element):
        return self.process(element, self._wdiv(element, """$(*)"""))

    def on_content_bodyonly(self, element):
        return self.process(element, self._wdiv(element, """$(*)"""))

    def on_content_table(self, element):
        return self.process(element, """<tbody%s>$(*)</tbody>""" % (self._wattrs(element)))

    def on_header(self, element):
        return self.process(element, "<title%s>$(header/title)</title>" % (self._wattrs(element)))

    def on_title(self, element):
        return self.process(element, self._wspan(element, "$(*)"))

    def on_section(self, element):
        offset = element._processor.variables.get("LEVEL") or 0
        level = int(element.getAttributeNS(None, "depth")) + offset
        return self.process(element,
                            '<div class="section level-%d" data-level="%d">' % (
                                level, level)
                            + '<div class="header"><h%d><a class="number" name="S%s"></a>$(title)</h%d></div>' % (
                                level, self.formatSectionNumber(self.getSectionNumberPrefix(element)), level)
                            + '<div class="body">$(content:section)</div></div>'
                            )

    def on_references(self, element):
        return self.process(element, """<div class="references">$(entry)</div>""")

    def on_entry(self, element):
        return self.process(element, """<div class="entry"><div class="name"><a name="%s">%s</a></div><div class="content">$(*)</div></div>""" %
                            (element.getAttributeNS(None, "id"), element.getAttributeNS(None, "id")))

    def on_header_title(self, element):
        return self.process(element, """<div class="title">$(header/title:header)$(header/subtitle:header)</div>$(Meta)""")

    def on_title_header(self, element):
        return self.process(element, """<h1%s>$(*)</h1>""" % (self._wattrs(element)))

    def on_subtitle_header(self, element):
        return self.process(element, """<h2%s>$(*)</h2>""" % (self._wattrs(element)))

    def on_paragraph(self, element):
        return self.process(element, """<p%s>$(*)</p>""" % (self._wattrs(element)))

    def on_paragraph_cell(self, element):
        return self.process(element, """$(*)<br />""")

    def on_list(self, element):
        list_type = element.getAttributeNS(None, "type")
        attrs = [""]
        if list_type:
            attrs.append('class="%s"' % (list_type))
        if list_type == "ordered":
            return self.process(element, """<ol%s%s>$(*)</ol>""" % (self._wattrs(element), " ".join(attrs)))
        else:
            return self.process(element, """<ul%s%s>$(*)</ul>""" % (self._wattrs(element), " ".join(attrs)))

    # FIXME: List items are not expanded
    def on_list_item(self, element):
        attrs = [""]
        is_todo = element.getAttributeNS(None, "todo")
        if is_todo:
            if is_todo == "done":
                attrs.append('class="todo done"')
                return self.process(element, """<li%s%s><input type='checkbox' checked='true' readonly>$(*)</input></li>""" % (self._wattrs(element), " ".join(attrs)))
            else:
                attrs.append('class="todo"')
                return self.process(element, """<li%s%s><input type='checkbox' readonly>$(*)</input></li>""" % (self._wattrs(element), " ".join(attrs)))
        else:
            return self.process(element, """<li%s%s>$(*)</li>""" % (self._wattrs(element), " ".join(attrs)))

    def on_table(self, element):
        tid = element.getAttributeNS(None, "id")
        if tid:
            tid = ' id="%s"' % (tid)
        else:
            tid = ""
        return self.process(element, """<div class="table"%s><table cellpadding="0" cellspacing="0" align="center">$(caption)$(content:table)</table></div>""" % (tid))

    def on_definition_list(self, element):
        return self.process(element, """<dl%s>$(*)</dl>""" % (self._wattrs(element)))

    def on_definition_item(self, element):
        return self.process(element, """<dt>$(Title)</dt><dd>$(content)</dd>""")

    def on_caption_(self, element):
        return self.process(element, """<caption%s>$(*)</caption>""" % (self._wattrs(element)))

    def on_row(self, element):
        try:
            index = element.parentNode.childNodes.index(element) % 2 + 1
        except:
            index = 0
        classes = ("", "even", "odd")
        return self.process(element, """<tr class='%s'%s>$(*)</tr>""" % (classes[index], self._wattrs(element)))

    def on_cell(self, element):
        cell_attrs = ""
        node_type = element.getAttributeNS(None, "type")
        if element.hasAttributeNS(None, "colspan"):
            cell_attrs += " colspan='%s'" % (
                element.getAttributeNS(None, "colspan"))
        if node_type == "header":
            return self.process(element, """<th%s%s>$(*:cell)</th>""" % (cell_attrs, self._wattrs(element)))
        else:
            return self.process(element, """<td%s%s>$(*:cell)</td>""" % (cell_attrs, self._wattrs(element)))

    def on_block(self, element):
        title = element.getAttributeNS(
            None, "title") or element.getAttributeNS(None, "type") or ""
        css_class = ""
        if title:
            css_class = " class='tagged-block %s'" % (
                element.getAttributeNS(None, "type").lower())
            div_type = "div"
        elif not element.getAttributeNS(None, "type"):
            div_type = "blockquote"
        return self.process(element, """<%s%s%s>$(*)</%s>""" % (div_type, css_class, self._wattrs(element), div_type))

    def on_link(self, element):
        if element.getAttributeNS(None, "type") == "ref":
            return self.process(element, """<a href="#%s" class="internal">$(*)</a>""" % (self.stringToTarget(element.getAttributeNS(None, "target"))))
        else:
            # TODO: Support title
            return self.process(element, """<a href="%s" class="external">$(*)</a>""" % (element.getAttributeNS(None, "target")))

    def on_target(self, element):
        name = element.getAttributeNS(None, "name")
        return self.process(element, """<a class="anchor" name="%s">$(*)</a>""" % (self.stringToTarget(name)))

    def on_meta(self, element):
        return self.process(element, "<table class='meta'>$(*)</table>")

    def on_meta(self, element):
        return self.process(element,
                            "<tr><td width='0px' class='name'>%s</td><td width='100%%' class='value'>$(*)</td></tr>" %
                            (element.getAttributeNS(None, "name")))

    def on_email(self, element):
        mail = ""
        for c in process(element, """$(*)"""):
            mail += "&#%d;" % (ord(c))
        return """<a href="mailto:%s">%s</a>""" % (mail, mail)

    def on_url(self, element):
        return self.process(element, """<a href="$(*)" target="_blank">$(*)</a>""")

    def on_url_header(self, element):
        return self.process(element, """<div class='url'>%s</div>""" % (self.on_url(element)))

    def on_term(self, element):
        return self.process(element, """<span class='term'>$(*)</span>""")

    def on_strikethrough(self, element):
        return self.process(element, """<s class='strikethrough'>$(*)</s>""")

    def on_checkbox(self, element):
        # FIXME: Not the right one
        return "<input type=\"checkbox\"" + (" checked" if element.getAttributeNS(None, "checked") == "true" else "") + " />"

    def on_quote(self, element):
        return self.process(element, """&ldquo;<span class='quote'>$(*)</span>&rdquo;""")

    def on_citation(self, element):
        return self.process(element, """&laquo;<span class='citation'>$(*)</span>&raquo;""")

    def on_variable(self, element):
        return self.process(element, """<span id='$(*)' class='variable'></span>""")

    def on_strong(self, element):
        return self.process(element, """<strong>$(*)</strong>""")

    def on_pre(self, element):
        lang = ""
        return self.process(element, """<pre%s><code%s>$(*)</code></pre>""" % (self._wattrs(element), lang)).replace("\r\n", "\n")

    def on_code(self, element):
        return self.process(element, """<code>$(*)</code>""")

    def on_coderef(self, element):
        return self.process(element, """<code class='ref'>$(*)</code>""")

    def on_em(self, element):
        return self.process(element, """<em>$(*)</em>""")

    def on_break(self, element):
        return self.process(element, """<br />""")

    def on_newline(self, element):
        return self.process(element, """<br />""")

    def on_arrow(self, element):
        arrow = element.getAttributeNS(None, "type")
        if arrow == "left":
            return "&larr;"
        elif arrow == "right":
            return "&rarr;"
        else:
            return "&harr;"

    def on_dots(self, element):
        return "&hellip;"

    def on_endash(self, element):
        return "&ndash;"

    def on_emdash(self, element):
        return "&mdash;"

    def on_entity(self, element):
        return "&%s;" % (element.getAttributeNS(None, "num"))

    def stringToTarget(self, text):
        return text.replace("  ", " ").strip().replace(" ", "_")

# ------------------------------------------------------------------------------
#
#  Actual element processing
#
# ------------------------------------------------------------------------------


# We create the processor, register the rules and define the process variable
processor = Processor()
process = processor.process

# EOF
