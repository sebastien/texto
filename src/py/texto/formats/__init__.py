#!/usr/bin/env python
# -----------------------------------------------------------------------------
# Project           : Texto
# -----------------------------------------------------------------------------
# Author            : Sebastien Pierre           <sebastien.pierre@gmail.com>
# -----------------------------------------------------------------------------
# Creation date     : 06-Mar-2006
# Last mod.         : 07-Aug-2021
# -----------------------------------------------------------------------------

import os
import glob
import re
import xml.dom


RE_EXPRESSION = re.compile(r"\$\(([^\)]+)\)")

__doc__ = """\
The `formats` module implements a simple way to convert an XML document to another
format (HTML or text) by expanding simple XPath-like expressions. Of
course, it is a very-small subset of what you could do in XSLT, but it has a
Python syntax and is very, very easy to use.

At first, your define `convertXXX' functions where XXX is your case-sensitive
tagName. All these functions should take an element as parameter and run the
`process' function with the element and template string as parameter.

Expressions like `$(XXX)' (XXX being the expression) in the template strings
will be expanded by processing the set of nodes indicated by the XXX expression.

 - `$(*)` will process all children
 - `$(MyNode)` will process only nodes with 'MyNode' tagName
 - `$(MyParent/MyNode)` will process only the children of MyParent named MyNode
 - `$(MyNode:alt)` will use the function `convertMyNode_alt' instead of the
   default 'convertMyNode', if available. This allows to setup 'processing
   modes' for your document (like table of content, references, etc).
 - `$(MyNode:alt?)` will use the function `convertMyNode_alt' if it is defined, or
   fallback to `convertMyNode`.

"""

# ------------------------------------------------------------------------------
#
#  PROCESSOR
#
# ------------------------------------------------------------------------------


class Processor(object):
    """The processor is the core of the template engine. It registers handlers
    to handle elements on a by-name basis."""

    def __init__(self, module=None, default=None):
        self.expressionTable = {}
        self.variables = {}
        self._defaultProcess = default
        self.bindInstance(self)
        if module:
            self.bindModule(module)

    def bindModule(self, module):
        # FIXME: legacy
        symbols = [_ for _ in dir(module) if _.startswith("convert")]
        functions = dict((_, getattr(module, _)) for _ in symbols)
        self.register(functions)

    def bindInstance(self, instance):
        """Registers any function that starts with `on` as a processor
        for the node with the given name."""
        return self.register(
            dict(
                (_[3:], getattr(instance, _))
                for _ in dir(instance)
                if _.startswith("on_")
            )
        )

    def register(self, name2functions):
        """Fills the EXPRESSION_TABLE which maps element names to processing
        functions. This function is only useful when you implement your
        templates in the same way as the `texto2html` module, ie. with processing
        functions like `convertXXX_VVV` where `XXX` stands for the element name,
        and `_VVV` is the optional variant (selected by`$(element:variant)`).

        You may prefer to use the `registerElementProcessor` instead if you want
        to register a processor for an individual tag.
        """
        for name, function in list(name2functions.items()):
            if name.startswith("convert"):
                ename = name[len("convert") :]
            else:
                ename = name
            ename = ename.replace("__", ":")
            self.expressionTable[ename] = function

    def registerElementProcessor(self, function, elementName, variant=None):
        """Registers the given function to process the given element name and
        the given optional variant.

        Note that this will replace any previously registered processor for the
        element and variant."""
        if variant:
            elementName += ":" + variant
        self.expressionTable[elementName] = function

    def resolveSet(self, element, names):
        """Resolves the set of names in the given element. When ["Paragraph"] is
        given, then all child paragraph nodes of the current node will be returned,
        while ["section", "paragraph"] will return all paragraphs for all
        sections."""
        s = []
        if len(names) == 1:
            name = names[0]
            for child in element.childNodes:
                if name != "*" and not child.nodeType == xml.dom.Node.ELEMENT_NODE:
                    continue
                if name == "*" or child.tagName == name:
                    s.append(child)
        else:
            name = names[0]
            for child in element.childNodes:
                if name != "*" and not child.nodeType == xml.dom.Node.ELEMENT_NODE:
                    continue
                if name == "*" or child.tagName == name:
                    s.extend(self.resolveSet(child, names[1:]))
        return s

    def apply(self, element):
        return self.processElement(element)

    def processElement(self, element, selector=None) -> str:
        """Processes the given element according to the EXPRESSION_TABLE, using the
        given selector to select an alternative function."""
        selector_optional = False
        if selector and selector[-1] == "?":
            selector = selector[:-1]
            selector_optional = True
        if element.nodeType == xml.dom.Node.TEXT_NODE:
            return self.processTextNode(element, selector, selector_optional)
        elif element.nodeType == xml.dom.Node.ELEMENT_NODE:
            return self.processElementNode(element, selector, selector_optional)
        else:
            return ""

    def text(self, element, selector=None):
        if element and hasattr(element, "nodeType"):
            if element.nodeType == xml.dom.Node.TEXT_NODE:
                return element.data
            elif element.nodeType == xml.dom.Node.ELEMENT_NODE:
                return "".join([self.text(e) for e in element.childNodes])
            else:
                return ""
        else:
            return ""

    def processElementNode(
        self, element: xml.dom.Node, selector: str, isSelectorOptional=False
    ):
        """"""
        # FIXME: Monkey patching objects is not ideal
        element._processor = self
        fname = element.nodeName.replace("-", "_")
        if selector:
            fname += ":" + selector
        func = self.expressionTable.get(fname)
        # In case we have no custom processing function, we look for one
        # without the variant
        if not func:
            func = self.expressionTable.get(fname.split(":")[0])
        # There is a function for the element in the EXPRESSION TABLE
        if func:
            return func(element)
        elif isSelectorOptional:
            self.processElement(element)
        # Otherwise we simply expand its text
        else:
            return self.defaultProcessElement(element, selector)

    def processTextNode(self, element, selector, isSelectorOptional=False) -> str:
        """Returns the text node"""
        return element.data

    def defaultProcessElement(self, element, selector):
        """Default function for processing elements. This returns the text."""
        if self._defaultProcess:
            return self._defaultProcess(element, selector, self)
        else:
            return "".join([self.processElement(e) for e in element.childNodes])

    def first(self, element, expression):
        r = self.query(element, expression)
        return r[0][0] if r else None

    def query(self, element, expression):
        """Queries the given expression at the given element, returning
        matching (element,selector) couples."""
        assert self.expressionTable
        # =VARIABLE means that we replace the expression by the content of the
        # variable in the variables directory
        if expression.startswith("="):
            vname = expression[1:].upper()
            return [(self.variables.get(vname) or "", None)]
        # Otherwise, the expression is a node selection expression, which may also
        # have a selector
        elif expression.rfind(":") != -1:
            names, selector = expression.split(":")
        # There may be no selector as well
        else:
            names = expression
            selector = None
        names = names.split("/")
        return [(_, selector) for _ in self.resolveSet(element, names)]

    # SYNTAX: $(EXPRESSION)
    # Where EXPRESSION is a "/" separated list of element names, optionally followed
    # by a colon ':' and a name
    def process(self, element, template: str):
        """Expands the given template string with the given element as data."""
        i = 0
        r = ""
        while i < len(template):
            m = RE_EXPRESSION.search(template, i)
            if m:
                r += template[i : m.start()]
                # Call the query with the template expression
                for e, s in self.query(element, m.group(1)):
                    r += e if isinstance(e, str) else self.processElement(e, s)
                i = m.end()
            else:
                r += template[i:]
                break
        return r

    def generate(self, xmlDocument, bodyOnly=False, variables={}):
        node = xmlDocument.getElementsByTagName("document")[0]
        self.variables = variables
        # FIXME: Not ideal for multithreading
        self.bodyOnly = bodyOnly
        if bodyOnly:
            for child in node.childNodes:
                if child.nodeName == "content":
                    return self.processElement(node)
        else:
            return self.processElement(node)


# ------------------------------------------------------------------------------
#
#  FUNCTIONS
#
# ------------------------------------------------------------------------------


def escapeHTML(text):
    """Escapes &, < and > into corresponding HTML entities."""
    text = text.replace("&", "&amp;")
    text = text.replace(">", "&gt;")
    text = text.replace("<", "&lt;")
    return text


def get():
    """Returns a map of formats and the corresponding formatters."""
    formats = {}
    for path in glob.glob(os.path.dirname(__file__) + "/*.py"):
        name = os.path.basename(path).rsplit(".", 1)[0]
        if name != "__init__":
            fullname = "texto.formats." + name
            # NOTE: __import__ does not work
            submodule = __import__(fullname)
            # submodule = imp.load_source(fullname, path)
            formats[name] = submodule
    return formats


# EOF
