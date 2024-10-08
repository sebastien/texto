#!/usr/bin/env python
# Encoding: utf8
# -----------------------------------------------------------------------------
# Project           :   Texto
# -----------------------------------------------------------------------------
# Author            :   Sebastien Pierre           <sebastien.pierre@gmail.com>
# License           :   Revised BSD License
# -----------------------------------------------------------------------------
# Creation date     :   07-Fev-2006
# Last mod.         :   09-Oct-2023
# -----------------------------------------------------------------------------

import sys
import re
import operator
import xml.dom.minidom
from .inlines import *
from .blocks import *

dom = xml.dom.minidom.getDOMImplementation()

# ------------------------------------------------------------------------------
#
# GLOBALS
#
# ------------------------------------------------------------------------------

# How many spaces a tab represent.
TAB_SIZE = 4

# ------------------------------------------------------------------------------
#
# REGULAR EXPRESSIONS
#
# ------------------------------------------------------------------------------

RE_BLOCK_SEPARATOR = re.compile("[ \t\r]*\n[ \t\r]*\n", re.MULTILINE)
RE_SPACES = re.compile(r"[\s\n]+", re.MULTILINE)
RE_TABS = re.compile("\t+")
NAME = r"[A-Za-z0-9\-_]+"
STR_SQ = r"'(\\'|[^'])*'"
STR_DQ = r'"(\\"|[^"])*"'
# A value is either a quoted string or a sequence without spaces
VALUE = f"({STR_SQ}|{STR_DQ}|" r"[^ \t\r\n]+)"
RE_ATTR = re.compile(f"[ \t]*((?P<ns>{NAME}):)?(?P<name>{NAME})=(?P<value>{VALUE})?")

# ------------------------------------------------------------------------------
#
# PARSING CONTEXT
#
# ------------------------------------------------------------------------------


class ParsingContext:
    """The context stores information on the currently processed document. It
    has the following attributes:

            - document: a reference to the current XML document.
            - rootNode: the current XML document root  node.
            - header: the XML node corresponding to the header.
            - content: the XML node corresponding to the content.
            - references: the XML node corresponding to the references.
            - appendices: the XML node corresponding to the appendices.
            - currentNode: the XML node to which attributes/nodes are added during
            parsing.
            - blockStartOffset: the offset in the text where the currently parsed block
            starts.
            - blockEndOffset: the offset in the text where the currently parsed block
            ends.
            - parser: a reference to the Texto parser instance using the context.
    """

    def __init__(self, documentText, markOffsets=False, parser=None):
        self.parser = parser
        self.document = None
        self.rootNode = None
        self.header = None
        self.content = None
        self.references = None
        self.appendices = None
        self.currentNode = None
        self.lastBlockNode = None
        self._offset = 0
        self.blockStartOffset = 0
        self.blockEndOffset = -1
        self.setDocumentText(documentText)
        self._currentFragment = None
        self.parser = None
        self.markOffsets = markOffsets
        self.meta = {}
        self.sections = []
        # These are convenience attributes used to make it easy for
        # post-verification of the links (are they all resolved)
        self._links = []
        self._targets = []
        self._keys = {}

    def asKey(self, text, node=None):
        key = "".join(
            [
                _ if _ in "abcdefghijklmnopqrstuvwxyz0123456789-_" else "-"
                for _ in text.lower().strip()
            ]
        )
        if key in self._keys:
            i = 1
            base = key
            while key in self._keys:
                key = base + "-" + str(i)
                i += 1
        self._keys[key] = node
        return key

    def _getElementsByTagName(self, node, name):
        if node.nodeType == node.ELEMENT_NODE and node.localName == name:
            result = [node]
        else:
            result = []
        for child in node.childNodes:
            result.extend(self._getElementsByTagName(child, name))
        return result

    def ensureElement(self, node, elementName, index=0):
        """Ensures that the given element exists in the given node at the given
        index."""
        result = self._getElementsByTagName(node, elementName)
        if len(result) <= index:
            newElement = self.document.createElementNS(None, elementName)
            node.appendChild(newElement)
            return newElement
        else:
            return result[index]

    def ensureParent(self, parentNames, predicate=lambda x: True):
        """Ensures that the parent node name is one of the following name. This
        is useful for block parsers which want to ensure that their parent is a
        specific node"""
        if self.currentNode != None:
            while (
                self.currentNode.nodeName not in parentNames
                or not predicate(self.currentNode)
            ) and self.currentNode.nodeName != "document":
                if self.currentNode.parentNode:
                    self.currentNode = self.currentNode.parentNode
                else:
                    return

    def declareSection(self, node, contentNode, depth):
        """Declares a section node with the given depth (which can be
        negative)."""
        self.sections.append((node, contentNode, depth))

    def getParentSection(self, depth, indent):
        """Gets the section that would be the parent section for the
        given depth."""
        for i in range(len(self.sections) - 1, -1, -1):
            section = self.sections[i]
            section_node = section[0]
            section_content = section[1]
            section_depth = section[2]
            section_indent = int(section_node.getAttributeNS(None, "_indent"))
            if indent > section_indent:
                return section_content
            elif section_indent <= indent and section_depth < depth:
                return section_content
        return self.content

    def getDepthInSection(self, node):
        """Returns the number of parent sections of the given node."""
        sections = 0
        while node.parentNode:
            if node.nodeName == "section":
                sections += 1
            node = node.parentNode
        return sections

    def setDocumentText(self, text):
        """Sets the text of the current document. This should only be called
        at context initialisation."""
        self.documentText = text
        self.documentTextLength = len(text)
        self.blockEndOffset = self.documentTextLength
        self.setOffset(0)

    def setOffset(self, offset):
        """Sets the current offset."""
        self._offset = offset
        self._currentFragment = None

    def getOffset(self):
        """Returns the current offset."""
        return self._offset

    def findNextBlockOffset(self):
        if self.parser:
            cur_end, next_start = self.parser._findNextBlockSeparator(self)
            return next_start
        else:
            o = context.blockEndOffset
            l = len(context.documentText)
            while o < l and context.documentText[o] in "\t\n ":
                o += 1
            return l if o < l else context.blockEndOffset

    def increaseOffset(self, increase):
        """Increases the current offset"""
        # We get the current fragment, because it will be freed by changing the
        # offset
        fragment = self.currentFragment()
        self.setOffset(self.getOffset() + increase)
        # We optimise current fragment access, by restoring it with a proper
        # value when possible
        if self.getOffset() < self.blockEndOffset:
            self._currentFragment = fragment[increase:]

    def decreaseOffset(self, decrease):
        """Decreases the offset."""
        self.increaseOffset(-decrease)

    def fragment(self, start, end):
        """Returns the text fragment that starts and ends at the given
        offsets."""
        return self.documentText[start:end]

    def currentFragment(self):
        """Returns the current text fragment, from the current offset to the
        block end offset."""
        assert (
            self.getOffset() < self.blockEndOffset
        ), "Offset greater than block end: %s >= %s" % (
            self.getOffset(),
            self.blockEndOffset,
        )
        if not self._currentFragment:
            self._currentFragment = self.documentText[
                self.getOffset() : self.blockEndOffset
            ]
        return self._currentFragment

    def documentEndReached(self):
        """Returns true if the current offset is greater than the document
        length"""
        return self.getOffset() >= self.documentTextLength

    def blockEndReached(self):
        """Returns true when the current offset has exceeded the current block
        end offset"""
        return self.getOffset() >= self.blockEndOffset

    def offsetInBlock(self, offset):
        """Tells if the given offset is in the current block."""
        return self.blockStartOffset <= offset <= self.blockEndOffset

    def setCurrentBlock(self, startOffset, endOffset):
        """Sets the start and end offset of the current block. The current
        offset is set to the current block start."""
        if endOffset <= 0:
            endOffset += self.documentTextLength
        assert startOffset >= 0
        assert endOffset <= self.documentTextLength
        assert startOffset <= endOffset, "Start offset too big: %s > %s" % (
            startOffset,
            endOffset,
        )
        self.setOffset(startOffset)
        self.blockStartOffset = startOffset
        self.blockEndOffset = endOffset
        self._currentFragment = None

    def setCurrentBlockEnd(self, endOffset):
        assert endOffset >= self.blockStartOffset
        self.blockEndOffset = endOffset
        self._currentFragment = None

    def getBlockIndentation(self):
        """Returns the indentation of the current block."""
        return self.parser.getIndentation(
            self.documentText[self.blockStartOffset : self.blockEndOffset]
        )

    def saveOffsets(self):
        """Returns a value that can be later used with the restoreOffsets
        method to restore the offsets as they were."""
        return (self.blockStartOffset, self.getOffset(), self.blockEndOffset)

    def restoreOffsets(self, offsets):
        """Takes a value returned by saveOffsets and restores the offsets as
        they were."""
        self.blockStartOffset = offsets[0]
        self.setOffset(offsets[1])
        self.blockEndOffset = offsets[2]

    def clone(self):
        """Returns a clone of the current context, which can be changed safely
        without modifying the current context."""
        clone = ParsingContext(self.documentText)
        clone.document = self.document
        clone.rootNode = self.rootNode
        clone.header = self.header
        clone.content = self.content
        clone.references = self.references
        clone.appendices = self.appendices
        clone.currentNode = self.currentNode
        clone.parser = self.parser
        clone.document = self.document
        clone.setOffset(self.getOffset())
        clone.setCurrentBlock(self.blockStartOffset, self.blockEndOffset)
        return clone

    def findNextInline(self, inlineParsers):
        """Finds the next inline in the given context, using the given list of
        inline parsers. This does not modifies the context.

        Returns either None or a triple (offset, information, parser), where
        the offset is relative to the context offset and indicates the start
        offset where the parser recognised its tag and information is the
        information returned by the parser."""
        # We look for the inline parser that parses an inline with the lowest
        # offset
        results = []
        for inlineParser in inlineParsers:
            match_offset, result = inlineParser.recognises(self)
            if match_offset != None:
                assert match_offset >= 0
                results.append((match_offset, result, inlineParser))
        matchedResult = None
        minimumOffset = self.documentTextLength + 1
        # We get the closest matching parser
        for result in results:
            if result[0] < minimumOffset:
                minimumOffset = result[0]
                matchedResult = result
        return matchedResult

    def parseAttributes(self, line: str) -> dict[str, str]:
        """Parses the attributes and returns a stream of `(key,value)` pairs."""
        res: dict[str, str] = {}
        # We remove the trailing spaces.
        while line and line[-1] in "\n \t":
            line = line[:-1]
        # Inline attributes are like
        #   ATTR=VALUE ATTR=VALUE…
        # Where value can be unquoted, single quoted or double quoted,
        # with \" or \' to escape quotes.
        o = 0
        while m := RE_ATTR.match(line, o):
            v = m.group("value")
            if not v:
                w = v
            # This little dance corrects the string escaping
            elif len(v) < 2:
                w = v
            else:
                s = v[0]
                e = v[-1]
                if s != e:
                    w = v
                elif s == '"':
                    w = v[1:-1].replace('\\"', '"')
                elif s == "'":
                    w = v[1:-1].replace("\\'", "'")
                else:
                    w = v
            res[m.group("name")] = w or ""
            o = m.end()
        return res

    def node(self, node, *children, **attributes):
        if isinstance(node, str):
            node = self.document.createElementNS(None, node)
        for _ in children:
            if isinstance(_, str):
                _ = self.document.createTextNode(_)
            node.appendChild(_)
        for k, v in attributes.items():
            node.setAttributeNS(None, k, v)
        return node

    def addNode(self, node, *children, **attributes):
        self.currentNode.appendChild(self.node(node, *children, **attributes))
        return node


# ------------------------------------------------------------------------------
#
# TEXTO PARSER
#
# ------------------------------------------------------------------------------


class Parser:

    def __init__(
        self,
        baseDirectory=".",
        inputEncoding="utf8",
        outputEncoding="utf8",
        inlineParsers=None,
        blockParsers=None,
        customParsers=None,
        document=None,
        root=None,
    ):
        self.document = document
        self.root = root
        self.blockParsers = []
        self.inlineParsers = []
        self.customParsers = {}
        self.baseDirectory = baseDirectory
        self.defaultBlockParser = ParagraphBlockParser()
        if blockParsers is not None:
            self.blockParsers.extend(blockParsers)
        else:
            self.createBlockParsers()
        if inlineParsers is not None:
            self.inlineParsers.extend(inlineParsers)
        else:
            self.createInlineParsers()
        self.createCustomParsers()

    def createBlockParsers(self):
        self.blockParsers.extend(
            (
                CommentBlockParser(),
                SeparatedBlockParser(),
                MarkupBlockParser(),
                PreBlockParser(),
                PreBlockParser2(),
                MetaBlockParser(),
                TableBlockParser(),
                ReferenceEntryBlockParser(),
                TitleBlockParser(),
                SectionBlockParser(),
                DefinitionBlockParser(),
                ListItemBlockParser(),
                ReferenceEntryBlockParser(),
                TaggedBlockParser(),
            )
        )

    def createCustomParsers(self):
        self.customParsers["pre"] = PreBlockParser()
        # self.customParsers["table"]= TableBlockParser()
        pass

    def createInlineParsers(self):
        # Escaped and markup inline parser are the most important parsers,
        # because they MUST be invoked before any other.
        self.escapedParser = EscapedInlineParser()
        self.commentParser = CommentInlineParser()
        self.markupParser = MarkupInlineParser()

        def normal(x, y):
            return self.normaliseText(x.group(1))

        def term(x, y):
            return self.normaliseText(x.group()[1:-1])

        self.inlineParsers.extend(
            (
                self.escapedParser,
                self.commentParser,
                self.markupParser,
                TargetInlineParser(),
                EscapedStringInlineParser(),
                InlineParser("email", RE_EMAIL),
                InlineParser("url", RE_URL),
                InlineParser("url", RE_URL_2),
                EntityInlineParser(),
                LinkInlineParser(),
                PreInlineParser(),
                EmbedInlineParser(),
                InlineParser("coderef", RE_CODE_REF_1),
                InlineParser("coderef", RE_CODE_REF_2),
                InlineParser("code", RE_CODE),
                InlineParser("term", RE_TERM, normal),
                InlineParser("strong", RE_STRONG, normal),
                InlineParser("em", RE_EMPHASIS, normal),
                InlineParser("quote", RE_QUOTED, normal),
                InlineParser("citation", RE_CITATION, normal),
                InlineParser("variable", RE_VARIABLE, normal),
                InlineParser("strikethrough", RE_STRIKETHROUGH, normal),
                CheckboxParser(),
                # Special characters
                InlineParser("break", RE_BREAK),
                InlineParser(None, RE_SWALLOW_BREAK),
                InlineParser("newline", RE_NEWLINE),
                InlineParser("dots", RE_DOTS),
                ArrowInlineParser(),
                InlineParser("endash", RE_LONGDASH),
                InlineParser("emdash", RE_LONGLONGDASH),
            )
        )

    def _initialiseContextDocument(self, context):
        """Creates the XML document that will be populated by Texto
        parsing."""
        if not self.document:
            document = dom.createDocument(None, None, None)
        else:
            document = self.document
        if not self.root:
            root_node = document.createElementNS(None, "document")
            document.appendChild(root_node)
        else:
            root_node = self.root
        context.rootNode = root_node
        context.document = document
        context.header = document.createElementNS(None, "header")
        context.content = document.createElementNS(None, "content")
        context.references = document.createElementNS(None, "references")
        context.appendices = document.createElementNS(None, "appendices")
        root_node.appendChild(context.header)
        root_node.appendChild(context.content)
        root_node.appendChild(context.references)
        root_node.appendChild(context.appendices)
        context.currentNode = context.content

    # EXCEPTIONS_______________________________________________________________

    def _print(self, message, context):
        text = context.documentText[: context.getOffset()]
        line = len(text.split("\n"))
        offset = context.getOffset() - text.rfind("\n") - 1
        message = str(message % (line, offset) + "\n")
        sys.stderr.write(message)

    def warning(self, message, context):
        self._print("WARNING at line %4d, character %3d: " + message, context)

    def tip(self, message, context):
        self._print("%4d:%3d >> " + message, context)

    def error(self, message, context):
        self._print("ERROR at line %4d, character %3d: " + message, context)

    # PARSING__________________________________________________________________

    def parse(self, text, offsets=False) -> ParsingContext:
        """Parses the given text, and returns an XML document. If `offsets` is
        set to True, then all nodes of the document are annotated with their
        position in the original text as well with a number. The document will
        also have an `offsets` attribute that will contain a list of (start,
        end) offset tuples for each element."""
        # Text MUST be unicode
        assert isinstance(text, str)
        context = ParsingContext(text, markOffsets=offsets, parser=self)
        self._initialiseContextDocument(context)
        context.parser = self
        while not context.documentEndReached():
            self._parseNextBlock(context)
        # We remove unnecessary nodes
        for node in (
            context.header,
            context.content,
            context.references,
            context.appendices,
        ):
            if len(node.childNodes) == 0:
                context.rootNode.removeChild(node)
        if offsets:
            context.offsets = self._updateElementOffsets(context, offsets=[])
        return context

    def parseContext(self, context):
        while not context.documentEndReached():
            self._parseNextBlock(context)

    def _parseNextBlock(self, context, end=None):
        """Parses the block identified in the given context, ending at the given
        'end' (if 'end' is not None)."""
        assert context != None
        # This variable indicates if at least one block parser recognised the
        # current block
        recognised = None
        # We find block start and end
        block_start_offset = context.getOffset()
        block_end_offset, next_block_start_offset = self._findNextBlockSeparator(
            context
        )
        # If we specify the end
        if end != None:
            block_end_offset = min(end, block_end_offset)
        # If the block is an empty block (a SEPARATOR), we try to find the
        # parent node
        if block_end_offset == block_start_offset:
            context.lastBlockNode = context.currentNode
            # We rewind until we find a "content" block
            while (
                context.currentNode.nodeName != "content"
                and context.currentNode.parentNode != None
            ):
                context.currentNode = context.currentNode.parentNode
        # Otherwise we set the current block and process it
        else:
            context.setCurrentBlock(block_start_offset, block_end_offset)
            assert block_start_offset < block_end_offset <= next_block_start_offset
            # We first look for a block parser that recognises the current
            # context
            for blockParser in self.blockParsers:
                context.setOffset(block_start_offset)
                recognised = blockParser.recognises(context)
                context.setOffset(block_start_offset)
                if recognised:
                    break
            # If no block parser was recognised, we used the default block
            # parser
            if not recognised:
                blockParser = self.defaultBlockParser
                recognised = self.defaultBlockParser.recognises(context)
                context.setOffset(block_start_offset)
                assert recognised
            start_offset = str(context.getOffset())
            blockParser.process(context, recognised)
            # Just in case the parser modified the end offset, we update
            # the next block start offset
            next_block_start_offset = context.blockEndOffset
            node = context.currentNode
        # Anyway, we set the offset to the next block start
        context.setOffset(next_block_start_offset)

    def parseBlock(self, context, node, textProcessor):
        """Parses the current block, looking for the inlines it may contain."""
        # if context.markOffsets and not node.getAttributeNS(None,"_start"):
        # 	node.setAttributeNS(None, "_start", str(context.getOffset()))
        while not context.blockEndReached():
            self._parseNextInline(context, node, textProcessor)
        # if context.markOffsets and not node.getAttributeNS(None,"_end"):
        # 	node.setAttributeNS(None, "_end", str(context.getOffset()))

    def _parseNextInline(self, context, node, textProcessor):
        """Parses the content of the current block, starting at the context
        offset, modifying the given node and updating the context offset.
        This returns the a triple (offset, information, parser) where
        information is the result of the parser `recognises' method."""
        assert context and node and textProcessor
        assert not context.blockEndReached()
        parse_offset = context.getOffset()
        matchedResult = context.findNextInline(self.inlineParsers)
        # If an inline parser recognised the block content then we can parse
        # it without problem
        if matchedResult:
            # We append the text between the search start offset and the matched
            # block start
            text = context.currentFragment()[: matchedResult[0]]
            if text:
                text = textProcessor(context, text)
                text_node = context.document.createTextNode(text)
                node.appendChild(text_node)
            new_offset = matchedResult[2].parse(context, node, matchedResult[1])
            # We increase the offset so that the next parsing offset will be
            # the end of the parsed inline.
            context.increaseOffset(new_offset)
        # When we have not found any matched result, this means that we simply
        # have to append the whole block as a text node
        else:
            assert parse_offset < context.blockEndOffset
            text = textProcessor(
                context, context.documentText[parse_offset : context.blockEndOffset]
            )
            text_node = context.document.createTextNode(text)
            node.appendChild(text_node)
            # We set the end to the block end
            context.setOffset(context.blockEndOffset)
        # We make sure the parsers have actually augmented the offset
        assert context.getOffset() >= parse_offset
        return matchedResult

    def _findNextBlockSeparator(self, context):
        """Returns a match object that matches the next block separator, taking
        into account possible custom block objects."""
        # FIXME: Should check if the found block separator is contained in a
        # custom block or not.
        block_match = RE_BLOCK_SEPARATOR.search(
            context.documentText, context.getOffset()
        )
        if block_match:
            local_offset = context.getOffset()
            # We look for a markup inline between the current offset and the
            # next block separator
            while local_offset < block_match.start():
                markup_match = RE_MARKUP.search(
                    context.documentText, local_offset, block_match.start()
                )
                # If we have not found a markup, we break
                if not markup_match:
                    break
                if markup_match:
                    # We have specified that markup inlines should not be searched
                    # after the block separator
                    local_offset, result = self._delimitXMLMarkupBlock(
                        context, markup_match, block_match, local_offset
                    )
                    if not result is None:
                        return result
            # We have found a block with no nested markup
            return (block_match.start(), block_match.end())
        # There was no block separator, so we reached the document end
        else:
            return (context.documentTextLength, context.documentTextLength)

    def _delimitXMLMarkupBlock(self, context, markupMatch, blockMatch, localOffset):
        markup_match = markupMatch
        block_match = blockMatch
        local_offset = localOffset
        assert markup_match.start() < block_match.start()
        # Case 1: Markup is a start tag
        if Markup_isStartTag(markup_match):
            # We look for the markup end inline
            offsets = context.saveOffsets()
            context.setCurrentBlock(markup_match.end(), context.documentTextLength)
            # There may be no 2nd group, so we  have to check this. Old
            # Texto documents may have [start:something] instead of
            # [start something]
            markup_end = None
            if markup_match.group(1):
                markup_end = self.markupParser.findEnd(
                    markup_match.group(1).strip(), context
                )
            context.restoreOffsets(offsets)
            # If we found an end markup
            if markup_end:
                # The returned end is relative to the start markup end
                # offset (markup_end is a couple indicating the range
                # covered by the matched end markup)
                markup_end = markup_match.end() + markup_end[1]
                # If the end is greater than the block end, then we have
                # to recurse to look for a new block separator
                # after the block end
                if markup_end > block_match.start():
                    offsets = context.saveOffsets()
                    context.setOffset(markup_end)
                    result = self._findNextBlockSeparator(context)
                    context.restoreOffsets(offsets)
                    # NOTE: This is the case where we found
                    # the block
                    return local_offset, result
                # Otherwise we simply increase the offset, and look for
                # other possible markup inlines
                else:
                    local_offset = markup_end
            # If there was not markup end, we skip the markup inline
            else:
                local_offset = markup_match.end()
        # We have a single tag, so we simply increase the offset
        else:
            local_offset = markup_match.end()
        return local_offset, None

    def _nodeHasOffsets(self, node):
        start, end = self._nodeGetOffsets(node)
        return start != None and end != None

    def _nodeGetOffsets(self, node):
        start = node.getAttributeNS(None, "_start")
        end = node.getAttributeNS(None, "_end")
        if start == "":
            start = None
        if end == "":
            end = None
        if start != None:
            start = int(start)
        else:
            start = None
        if end != None:
            end = int(end)
        else:
            end = None
        return (start, end)

    def _nodeEnsureOffsets(self, node, start=None, end=None):
        nstart, nend = self._nodeGetOffsets(node)
        if nstart is None and start != None:
            node.setAttributeNS(None, "_start", str(start))
        if nend is None and end != None:
            node.setAttributeNS(None, "_end", str(end))

    def _updateElementOffsets(self, context, node=None, counter=0, offsets=None):
        """This function ensures that every element has a _start and _end
        attribute indicating the bit of original data it comes from."""
        if node == None:
            node = context.document.childNodes[0]
            self._nodeEnsureOffsets(node, 0, context.documentTextLength)
        node.setAttributeNS(None, "_number", str(counter))
        # The given offsets parameter is an array with the node number and the
        # offsets. It can be used by embedders to easily access nods by offset
        if offsets != None:
            assert len(offsets) == counter, "%s != %s" % (len(offsets), counter)
            this_offsets = [None, None]
            offsets.append(this_offsets)
        # The first step is to fill an array with the child nodes offsets
        # Each child node may or may not have an offset
        child_nodes = tuple(
            [n for n in node.childNodes if n.nodeType == n.ELEMENT_NODE]
        )
        nstart, nend = self._nodeGetOffsets(node)
        if child_nodes:
            self._nodeEnsureOffsets(child_nodes[0], start=nstart)
            self._nodeEnsureOffsets(child_nodes[-1], end=nend)
        child_offsets = []
        start = end = None
        for e in child_nodes:
            counter = self._updateElementOffsets(context, e, counter + 1)
            child_offsets.append(self._nodeGetOffsets(e))
        # Once this list is created, we retried the start offset of the earliest
        # child that has a start offset, same for the end offset of the latest
        # child
        child_start = None
        child_end = None
        if child_offsets:
            i = 0
            j = len(child_offsets) - 1
            while i < len(child_offsets) and child_offsets[i][0] == None:
                i += 1
            while j >= 0 and child_offsets[j][1] == None:
                j -= 1
            if i < len(child_offsets):
                child_start = child_offsets[i][0]
            if j >= 0:
                child_end = child_offsets[j][1]
        # We update the current node with the child offsets (this allows node
        # that have incomplete offsets to be completed)
        self._nodeEnsureOffsets(node, child_start, child_end)
        # And now we update the children offsets again (so that they actually
        # all have offsets), because we have all the information we need to
        # actually update the children offsets
        start, end = self._nodeGetOffsets(node)
        self._propagateElementOffsets(node, start, end)
        # As we now the current node offsets, we can set the real values in the
        # fiven offsets array, by simply updating the offsets value in the
        # `this_offsets` list.
        if offsets != None:
            o = self._nodeGetOffsets(node)
            this_offsets[0] = o[0]
            this_offsets[1] = o[1]
        # And we return the number of this node
        return counter

    def _propagateElementOffsets(self, element, start=None, end=None):
        """Used by the _updateElementOffsets to ensure start and end offsets in
        all children and descendants."""
        # if start is None or end is None: return
        child_nodes = list(
            [n for n in element.childNodes if n.nodeType == n.ELEMENT_NODE]
        )
        self._nodeEnsureOffsets(element, start, end)
        # At first, we set the bounds properly, so that the first child node
        # start is this node start, and the last node end is this node end
        if child_nodes:
            self._nodeEnsureOffsets(child_nodes[0], start=start)
            self._nodeEnsureOffsets(child_nodes[-1], end=end)
        # Now
        for child in child_nodes:
            self._propagateElementOffsets(child, start=start)
            if self._nodeGetOffsets(child)[1] != None:
                _, nstart = self._nodeGetOffsets(child)
                if nstart != None:
                    start = nstart
        child_nodes.reverse()
        for child in child_nodes:
            self._propagateElementOffsets(child, end=end)
            if self._nodeGetOffsets(child)[0] != None:
                nend, _ = self._nodeGetOffsets(child)
                if nend != None:
                    end = nend
        # TODO: Maybe update the element offsetsd

    # TEXT PROCESSING UTILITIES________________________________________________

    def normaliseText(self, text):
        """Treats tabs eols and multiples spaces as single space, plus removes
        leading and trailing spaces."""
        # We do not strip the text because white spaces are important
        return RE_SPACES.sub(" ", text)

    def expandTabs(self, text, cut=0):
        """Expands the tabs in the given text, cutting the n first characters
        of each line, where n is given by the 'cut' argument.  This tabs
        expansion algorithm works better than Python line expansion
        algorithms."""
        if not text:
            return ""
        new_text = ""
        for line in text.split("\n"):
            start = 0
            match = 1
            new_line = ""
            while match != None:
                match = RE_TABS.search(line, start)
                if match:
                    rest = TAB_SIZE - operator.mod(match.start(), TAB_SIZE)
                    new_line += line[start : match.start()]
                    # We grow the line with additional tabs
                    value = rest + (len(match.group()) - 1) * TAB_SIZE
                    while value > 0:
                        new_line += " "
                        value -= 1
                    # It is important to mutate the original line
                    line = new_line + line[match.end() :]
                    start = len(new_line)
            new_line += line[start:]
            cut_offset = min(len(new_line), cut)
            new_text += new_line[cut_offset:] + "\n"
        # We make sure that we do not add an extra empty line
        if text[-1] != new_text[-1]:
            return new_text[:-1]
        else:
            return new_text

    @classmethod
    def getIndentation(self, text):
        """Returns the indentation of a string.

        Basically if a string has the first three lines at the same
        indentation level, then it is indentation will be the number
        of spaces or tabs that lead the first three lines.

        Tabs have the value given by the *TAB_SIZE* variable."""
        lines = [x for x in text.split("\n", 4) if len(x) > 0]
        indent = list(map(self.countLeadingSpaces, lines))
        if len(lines) == 0:
            res = 0
        elif len(lines) == 1:
            res = indent[0]
        elif len(lines) == 2:
            res = indent[1]
        else:
            res = max(max(indent[0], indent[1]), indent[2])
        return res

    @classmethod
    def countLeadingSpaces(self, text):
        """Returns the number of leading spaces in the given line.
        A tab will have the value given by the TAB_SIZE global."""
        count = 0
        for char in text:
            if char == "\t":
                count += TAB_SIZE - operator.mod(count, TAB_SIZE)
            elif char == " ":
                count += 1
            else:
                return count
        return count

    @classmethod
    def removeLeadingSpaces(self, text, maximum=None):
        i = 0
        count = 0
        for char in text:
            if not maximum is None and count >= maximum:
                return text[i:]
            if char == "\t":
                count += TAB_SIZE - operator.mod(count, TAB_SIZE)
            elif char == " ":
                count += 1
            else:
                return text[i:]
            i += 1
        return ""

    @classmethod
    def charactersToSpaces(self, text):
        """Returns a string where all characters are converted to spaces.
        Newlines and tabs are preserved"""
        new_text = ""
        for char in text:
            if char in ("\t", "\n", " "):
                new_text += char
            else:
                new_text += " "
        return new_text


# EOF - vim: tw=80 ts=4 sw=4 et
