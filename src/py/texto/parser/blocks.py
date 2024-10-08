# Encoding: utf8
# -----------------------------------------------------------------------------
# Project           : Texto
# Module            : Block parsers
# -----------------------------------------------------------------------------
# Author            : Sebastien Pierre             <sebastien.pierre@gmail.com>
# License           : Revised BSD License
# -----------------------------------------------------------------------------
# Creation date     : 2003-11-19
# Last mod.         : 2024-10-09
# -----------------------------------------------------------------------------

import re

# FIXME: Not great
from . import *

__pychecker__ = "unusednames=recogniseInfo,content"

EMPTY_LIST_ITEM = "Empty list item."
BLOCK_ELEMENTS = (
    "block",
    "list-item",
    "definition",
    "content",
    "chapter",
    "section",
    "appendix",
)

STANDARD_LIST = 1
DEFINITION_LIST = 2
TODO_LIST = 3
ORDERED_LIST = 4
TAB_VALUE = "    "

STANDARD_ITEM = 100
TODO_ITEM = 101
TODO_DONE_ITEM = 102


# ------------------------------------------------------------------------------
#
# REGULAR EXPRESSIONS
#
# ------------------------------------------------------------------------------

RE_BLANK = re.compile(r"\s*", re.MULTILINE)
RE_COMMENT = re.compile(r"^//")

TITLE = r"^\s*(==)([^=].+)$"
RE_TITLE = re.compile(TITLE, re.MULTILINE)

TITLE_HEADER = r"^\s*(--)([^\:]+):(.+)?$"
RE_TITLES = re.compile("%s|%s" % (TITLE, TITLE_HEADER), re.MULTILINE)


BLOCK_SEPARATOR = r"^\s*(--)\s+(?P<name>[A-z0-9][A-z0-9_\-]+)(?P<attributes>(\s+([A-z0-9][A-z0-9_\-]+)=[^\s]+)*)$"
RE_BLOCK_SEPARATOR = re.compile(BLOCK_SEPARATOR)


SECTION_HEADING = r"^\s*((([0-9]+|[A-z])\.)+([0-9]+|[A-z])?\.?)"
RE_SECTION_HEADING = re.compile(SECTION_HEADING)

SECTION_HEADING_ALT = r"^(\s*(#+)\s*).+$"
RE_SECTION_HEADING_ALT = re.compile(SECTION_HEADING_ALT)

SECTION_UNDERLINE = r"^\s*[\*\-\=#][\*\-\=#][\*\-\=#]+\s*$"
RE_SECTION_UNDERLINE = re.compile(SECTION_UNDERLINE, re.MULTILINE)

DEFINITION_ITEM = r"^(\s*(\:[^\:]|[^\:])+)\:\:+\s*(\n+\s*|\s*\|\s*\n)*$"
RE_DEFINITION_ITEM = re.compile(DEFINITION_ITEM, re.MULTILINE)

TAGGED_BLOCK = r"^\s*(([^_]+\s*)(\:[^_]+)?)?(___+)\s*$"
RE_TAGGED_BLOCK = re.compile(TAGGED_BLOCK, re.MULTILINE)
LIST_ITEM = r"^(\s*)(-|\*\)|[0-9A-z]+[\)/]|\[[ \-\~xX]\])\s*"
RE_LIST_ITEM = re.compile(LIST_ITEM, re.MULTILINE)
LIST_HEADING = r"(^\s*[^:{().<]*:)"
RE_LIST_HEADING = re.compile(LIST_HEADING, re.MULTILINE)
LIST_ITEM_HEADING = r"^([^:\(\`]+(:\s*\n\s*|::\s*))|([^/\\]+[/\\]\s*\n\s*)$"
RE_LIST_ITEM_HEADING = re.compile(LIST_ITEM_HEADING, re.MULTILINE)
RE_NUMBER = re.compile(r"\d+[\)\.]")

PREFORMATTED = r"^(\s*\>(\t|   ))(.*)$"
RE_PREFORMATTED = re.compile(PREFORMATTED)

PREFORMATTED_2_START = re.compile(r"^(\s*)```((\w+)?.*)$")
PREFORMATTED_2_END = re.compile(r"^\s*```\s*$")

CUSTOM_MARKUP = r"\s*-\s*\"([^\"]+)\"\s*[=:]\s*([\w\-_]+)(\s*\(\s*(\w+)\s*\))?"
RE_CUSTOM_MARKUP = re.compile(CUSTOM_MARKUP, re.MULTILINE)

RE_DOCSTRING = re.compile(r"^\s*@(param|return[s]?)\s")
RE_META_START = re.compile(r"^(\s*)--\s*$")
RE_META_END = re.compile(r"^(\s*)--\s*$")

META_TYPE = r"\s*(\w+)\s*(\((\w+)\))?"
RE_META_TYPE = re.compile(META_TYPE, re.MULTILINE)

META_FIELD = r"(^|\n)\s*([\w\-]+)\s*:\s*"
RE_META_FIELD = re.compile(META_FIELD)
RE_META_AUTHOR_EMAIL = re.compile(r"\<([^>]+)\>")

REFERENCE_ENTRY = r"\s+\[([^\]]+)]:"
RE_REFERENCE_ENTRY = re.compile(REFERENCE_ENTRY, re.MULTILINE)

TABLE_ROW_SEPARATOR = r"^\s*([\-\+]+|[\=\+]+)\s*$"
RE_TABLE_ROW_SEPARATOR = re.compile(TABLE_ROW_SEPARATOR)

LANGUAGE_CODES = ("EN", "FR", "DE", "UK")

# ------------------------------------------------------------------------------
#
#  ERROR MESSAGES
#
# ------------------------------------------------------------------------------

ERROR_TITLE_TOO_DEEPLY_NESTED = "Title too deeply nested"

# ------------------------------------------------------------------------------
#
# BLOCKPARSER
#
# ------------------------------------------------------------------------------


class BlockParser:

    def __init__(self, name=None):
        self.name = name or self.__class__.__name__.rsplit(".", 1)[-1]

    def recognises(self, context):
        """Tells wether the given block is recognised or not. This returns
        this block recognition information, or False (or None) if the block was
        not recognised."""
        return False

    def process(self, context, recogniseInfo):
        return None

    def processText(self, context, text):
        assert context, text
        return text


# ------------------------------------------------------------------------------
#
# PARAGRAPH BLOCK PARSER
#
# ------------------------------------------------------------------------------


class ParagraphBlockParser(BlockParser):
    """Parses a paragraph block. This parser always recognised the given block,
    so it should not appear in the block parsers."""

    def __init__(self):
        BlockParser.__init__(self, "p")

    def recognises(self, context):
        return True

    def process(self, context, recogniseInfo):
        # We make sure that the current node is a block element
        paragraph_depth = context.getBlockIndentation()
        # Here we move to the first block element that has an indentation that
        # is lower or equal to this paragraph
        while (
            context.currentNode.nodeName not in BLOCK_ELEMENTS
            or context.currentNode.getAttribute("_indent")
            and int(context.currentNode.getAttribute("_indent")) > paragraph_depth
        ):
            context.currentNode = context.currentNode.parentNode
        # If the currentNode last element is a paragraph with a higher
        # indentation than the current one, then we create a block, and set it
        # as current node (this allows to create "indented paragraphs" - the
        # equivalent of blockquotes).
        if (
            context.currentNode.childNodes
            and context.currentNode.childNodes[-1].nodeName == "p"
            and context.currentNode.childNodes[-1].getAttribute("_indent")
            and int(context.currentNode.childNodes[-1].getAttribute("_indent"))
            < paragraph_depth
        ):
            block_node = context.document.createElementNS(None, "Block")
            block_node.setAttributeNS(None, "_indent", str(paragraph_depth))
            context.currentNode.appendChild(block_node)
            context.currentNode = block_node
        # Now we can process the document
        para_node = context.document.createElementNS(None, self.name)
        para_node.setAttributeNS(None, "_indent", str(paragraph_depth))
        para_node.setAttributeNS(None, "_start", str(context.blockStartOffset))
        para_node.setAttributeNS(None, "_end", str(context.blockEndOffset))
        context.parser.parseBlock(context, para_node, self.processText)
        # Now we suppress leading and trailing whitespaces
        if para_node.childNodes:
            first_text_node = para_node.childNodes[0]
            last_text_node = para_node.childNodes[-1]
            if first_text_node.nodeType != para_node.TEXT_NODE:
                first_text_node = None
            if last_text_node.nodeType != para_node.TEXT_NODE:
                last_text_node = None
            # Removed first and last text nodes if empty
            if first_text_node != None and first_text_node.data.strip() == "":
                para_node.removeChild(first_text_node)
                first_text_node = None
            if last_text_node != None and last_text_node.data.strip() == "":
                para_node.removeChild(last_text_node)
                last_text_node = None
            # We strip the leading whitespace
            if (
                first_text_node != None
                and len(first_text_node.data) > 0
                and first_text_node.data[0] == " "
            ):
                first_text_node.data = first_text_node.data[1:]
            if (
                last_text_node != None
                and len(last_text_node.data) > 0
                and last_text_node.data[-1] == " "
            ):
                last_text_node.data = last_text_node.data[:-1]
        # FIXME: Maybe the paragraph contains text nodes with only spaces ?
        if len(para_node.childNodes) > 0:
            context.currentNode.appendChild(para_node)
        else:
            pass
            # NOTE: Can be legit (@embed)
            # context.parser.warning("Empty paragraph removed", context)

    def processText(self, context, text):
        assert text
        text = context.parser.expandTabs(text)
        text = context.parser.normaliseText(text)
        return text


# ------------------------------------------------------------------------------
#
# TAGGED BLOCK PARSER
#
# ------------------------------------------------------------------------------


class TaggedBlockParser(BlockParser):
    """Parses a tagged block. Notes are the common example of tagged
    block."""

    def __init__(self):
        BlockParser.__init__(self, "tagged-block")

    def recognises(self, context):
        lines = [l for l in context.currentFragment().split("\n") if l.strip()]
        if not lines:
            return
        return RE_TAGGED_BLOCK.match(lines[0])

    def _goToParent(self, parent):
        if not parent:
            return parent
        if parent.nodeName == "block":
            return parent.parentNode
        else:
            return parent

    def process(self, context, recogniseInfo):
        tagname = recogniseInfo.group(2)
        tagtitle = recogniseInfo.group(3)
        # This is an opening tag
        if tagname and tagname[0] != "_":
            # TODO: Asserts we are not already in a specific block
            block_depth = context.getBlockIndentation()
            block_node = context.document.createElementNS(None, "block")
            block_node.setAttributeNS(None, "type", tagname.strip().lower())
            block_node.setAttributeNS(None, "_indent", str(block_depth))
            if tagtitle:
                block_node.setAttributeNS(None, "title", tagtitle[1:].strip())
            # We get to a content node
            # Now we can process the document
            context.increaseOffset(len(recogniseInfo.group()))
            context.parser.parseBlock(context, block_node, self.processText)
            context.currentNode = self._goToParent(context.currentNode)
            context.currentNode.appendChild(block_node)
            context.currentNode = block_node
            assert context.currentNode
        # This is a closing tag
        elif tagname and tagname[0] == "_":
            while context.currentNode.nodeName != "block":
                context.currentNode = context.currentNode.parentNode
            context.currentNode = context.currentNode.parentNode


# ------------------------------------------------------------------------------
#
# COMMENT BLOCK PARSER
#
# ------------------------------------------------------------------------------


class CommentBlockParser(BlockParser):
    """Parses a comment markup block."""

    def __init__(self):
        BlockParser.__init__(self, "comment-block")

    def recognises(self, context):
        assert context and context.parser.commentParser
        lines = context.currentFragment().split("\n")
        comments = 0
        for line in lines:
            if (l := line.strip()) and not l.startswith("//"):
                return False
            elif l:
                comments += 1
        return comments > 0

    def process(self, context, recogniseInfo):
        context.currentNode.appendChild(
            context.document.createComment(
                " ".join(
                    RE_COMMENT.sub("", _).strip()
                    for _ in context.currentFragment().split("\n")
                ).strip()
            )
        )
        context.setOffset(context.blockEndOffset)


# ------------------------------------------------------------------------------
#
# MARKUP BLOCK PARSER
#
# ------------------------------------------------------------------------------


class MarkupBlockParser(BlockParser):
    """Parses a custom markup block."""

    def __init__(self):
        BlockParser.__init__(self, "markup")

    def recognises(self, context):
        assert context and context.parser.markupParser
        offset, match = context.parser.markupParser.recognises(context)
        # We make sure that the recognised markup is a block markup which has
        # only whitespaces at the beginning
        if (
            match
            and context.parser.markupParser.isStartTag(match)
            and len(context.currentFragment()[: match.start()].strip()) == 0
        ):
            # We parse the tag to see if it is a block tag and that it spans
            # the whole context current fragment.
            dummy_node = context.document.createElementNS(None, "dummy")
            match_end = context.parser.markupParser.parse(context, dummy_node, match)
            # The returned matched end MUST BE GREATER than the start tag match
            # end, and there MUST BE ONLY SPACES after the match end for this
            # tag to represent a standalone block, and not a block inlined into
            # a paragraph.
            if (
                match_end > match.end()
                and len(context.currentFragment()[match_end:].strip()) == 0
            ):
                # If there is a child node, we return it
                if len(dummy_node.childNodes) >= 1:
                    result_node = dummy_node.childNodes[0]
                    # We take care of the attributes
                    for key, value in list(
                        context.parseAttributes(match.group(2)).items()
                    ):
                        result_node.setAttributeNS(None, key, value)
                    return result_node
                # Otherwise this means that the block is empty
                else:
                    return True
            else:
                return False
        else:
            return False

    def process(self, context, recogniseInfo):
        if recogniseInfo != True:
            context.currentNode.appendChild(recogniseInfo)
        context.setOffset(context.blockEndOffset)


# ------------------------------------------------------------------------------
#
# TITLE BLOCK PARSER
#
# ------------------------------------------------------------------------------


class TitleBlockParser(BlockParser):
    """Parses a title object"""

    def __init__(self):
        BlockParser.__init__(self, "title")

    def recognises(self, context):
        matches = []
        if context.content.childNodes:
            return None
        while not context.blockEndReached():
            match = RE_TITLES.match(context.currentFragment())
            if match != None:
                context.increaseOffset(match.end())
                matches.append(match)
            else:
                return matches or False
        return matches

    def _processLine(self, line):
        pass

    def process(self, context, recogniseInfo):
        assert recogniseInfo
        for match in recogniseInfo:
            if match.group(1):
                self.processRegularTitle(context, match)
            elif match.group(3):
                self.processMetaTitle(context, match)
            else:
                raise Exception("We should not be here ! " + match.group())
        context.setOffset(context.blockEndOffset)

    def processRegularTitle(self, context, match):
        titleNode = context.ensureElement(context.header, "header")
        # We get the content of the title
        titleText = match.group(2) or match.group(4)
        # We prefix with 'sub' or 'subsub' depending on the number of
        # preceding titles
        titleType = "sub" * len(
            [n for n in titleNode.childNodes if n.nodeName.endswith("title")]
        )
        titleType += "title"
        # We add the node to the document tree
        resultNode = context.ensureElement(titleNode, titleType)
        titleNode.appendChild(resultNode)
        resultNode.appendChild(
            context.document.createTextNode(self.processText(context, titleText))
        )

    def processMetaTitle(self, context, match):
        metaNode = context.ensureElement(context.header, "meta")
        # We get the header name
        header_name = (match.group(4) or "").strip()
        header_text = (match.group(5) or "").strip()
        # We prepare the header node
        node = context.document.createElementNS(None, "meta")
        node.setAttributeNS(None, "name", header_name)
        node.appendChild(
            context.document.createTextNode(self.processText(context, header_text))
        )
        # And we add it to the document header
        metaNode.appendChild(node)

    def processText(self, context, text):
        return context.parser.normaliseText(text.strip())


# ------------------------------------------------------------------------------
#
# SEPARATED BLOCK PARSER
#
# ------------------------------------------------------------------------------


class SeparatedBlockParser(BlockParser):
    """Look for `-- block attr=value` and creates a new content block for it."""

    def __init__(self):
        super().__init__(name="content")

    def recognises(self, context):
        match = RE_BLOCK_SEPARATOR.match(context.currentFragment())
        return [match] if match else None

    def _processLine(self, line):
        pass

    def process(self, context, recogniseInfo):
        # This is a top level
        context.ensureParent(("document"))
        match = recogniseInfo[0]
        start = context.getOffset() + match.start()
        end = context.getOffset() + match.end()
        node = context.document.createElementNS(None, "content")
        node.setAttributeNS(None, "type", str(match.group("name")))
        node.setAttributeNS(None, "_start", str(start))
        node.setAttributeNS(None, "_end", str(end))
        node.setAttributeNS(None, "_indent", str(-1))
        node.setAttributeNS(None, "depth", str(0))
        for k, v in context.parseAttributes(match.group("attributes")).items():
            node.setAttributeNS(None, k, v)
        content_node = context.currentNode
        content_node.appendChild(node)
        context.currentNode = node
        context.setOffset(end)


# ------------------------------------------------------------------------------
#
# SECTION BLOCK PARSER
#
# ------------------------------------------------------------------------------


class SectionBlockParser(BlockParser):
    """Parses a section markup element."""

    def __init__(self):
        BlockParser.__init__(self, "section")

    def recognises(self, context):
        # We look for the number prefix
        match = RE_SECTION_HEADING.match(context.currentFragment())
        # We return directly if there are at least two section numbers (2.3)
        if match:
            match_underline = RE_SECTION_UNDERLINE.search(context.currentFragment())
            if match_underline:
                return (RE_SECTION_UNDERLINE, match_underline)
            else:
                return (RE_SECTION_HEADING, match)
        # We return directly for a section prefixed by '=='
        match_alt = RE_SECTION_HEADING_ALT.match(context.currentFragment())
        if match_alt:
            return (RE_SECTION_HEADING_ALT, match_alt)
        # Or a separator followed by blank space
        match = RE_SECTION_UNDERLINE.search(context.currentFragment())
        if match:
            # If we reached the end of the block, and that there is something
            # before, this OK
            if (
                match.end() == context.blockEndOffset
                and context.currentFragment()[: match.start()].strip()
            ):
                return (RE_SECTION_UNDERLINE, match)
            # Otherwise the rest must be blank
            else:
                blank_match = RE_BLANK.match(context.currentFragment()[match.end() :])
                # The rest is blank, it's OK
                if (
                    blank_match.end() + match.end() + context.getOffset()
                    == context.blockEndOffset
                ):
                    return (RE_SECTION_UNDERLINE, match)
                # Otherwise there is a trailing text
                else:
                    return None
        # Nothing matched
        else:
            return None

    def process(self, context, recogniseInfo):
        context.ensureParent(("content", "appendix", "chapter", "section"))
        matched_type, match = recogniseInfo
        section_indent = context.getBlockIndentation()
        trail = match.group().strip()
        # RULE:
        # A section underlined with '==' weights more than a section
        # underlined with '--', which weights more than a section
        # underline with nothing. This means that if you have
        #
        #  1. One
        #  ======
        #
        #  2. Two
        #  ------
        #
        #  3. Three
        #
        # These sections will all be children of the previous section
        section_weight = trail.endswith("==") and 2 or trail.endswith("--") and 1 or 0
        #
        # FIRST STEP - We detect section text bounds
        #
        block_start = context.blockStartOffset
        block_end = context.blockEndOffset
        section_type = "section"
        # We have an underlined section
        if matched_type == RE_SECTION_UNDERLINE:
            block_end = context.getOffset() + match.start()
        if matched_type == RE_SECTION_HEADING_ALT:
            block_start = context.getOffset() + match.start() + len(match.group(1))
            block_end = context.getOffset() + match.end()

        # We look for a number prefix
        heading_text = context.fragment(block_start, block_end)
        prefix_match = RE_SECTION_HEADING.match(heading_text)
        dots_count = 0
        if prefix_match:
            res = prefix_match.group()
            dots_count = len([x for x in res.split(".") if x])
            block_start = context.getOffset() + prefix_match.end()
        if matched_type == RE_SECTION_HEADING_ALT:
            dots_count += len(match.group(1))
        # We make sure that we end the section before the block delimiter
        delim_match = RE_SECTION_UNDERLINE.search(context.currentFragment())
        if delim_match:
            block_end = context.getOffset() + delim_match.start()
        context.currentNode = context.getParentSection(
            dots_count - section_weight, section_indent
        )
        section_depth = context.getDepthInSection(context.currentNode) + 1
        #
        # SECOND STEP - We create the section
        #
        section_node = context.document.createElementNS(None, section_type)
        section_node.setAttributeNS(None, "_indent", str(section_indent))
        section_node.setAttributeNS(None, "depth", str(section_depth))
        section_node.setAttributeNS(None, "_start", str(block_start))
        section_node.setAttributeNS(None, "_end", str(block_end))
        section_node.setAttributeNS(None, "_sstart", str(block_start))
        section_node.setAttributeNS(
            None, "id", str(context.asKey(heading_text, section_node))
        )
        heading_node = context.document.createElementNS(None, "title")
        section_node.appendChild(heading_node)
        offsets = context.saveOffsets()
        context.blockEndOffset = block_end
        context.setOffset(block_start)
        context.parser.parseBlock(context, heading_node, self.processText)
        context.restoreOffsets(offsets)
        # Now we create a Content node
        content_node = context.document.createElementNS(None, "content")
        content_node.setAttributeNS(None, "_indent", str(section_indent))
        section_node.appendChild(content_node)
        # We append the section node and assign it as current node
        context.currentNode.appendChild(section_node)
        context.currentNode = content_node
        context.declareSection(section_node, content_node, dots_count - section_weight)

    def processText(self, context, text):
        return context.parser.normaliseText(text.strip())


# ------------------------------------------------------------------------------
#
# DEFINITION BLOCK PARSER
#
# ------------------------------------------------------------------------------


class DefinitionBlockParser(BlockParser):
    """Parses a definition markup element."""

    def __init__(self):
        BlockParser.__init__(self, "definition-list")

    def recognises(self, context):
        return RE_DEFINITION_ITEM.match(context.currentFragment())

    def _getParentDefinition(self, node):
        while node and node.nodeName != "definition-list":
            node = node.parentNode
        return node

    def process(self, context, match):
        parent_node = self._getParentDefinition(context.currentNode)
        _indent = context.getBlockIndentation()
        # Ensures that the parent Definition node exists
        if not parent_node:
            parent_node = context.currentNode
            while True:
                if parent_node.parentNode == None:
                    break
                if parent_node.parentNode.nodeType == parent_node.DOCUMENT_NODE:
                    break
                if not parent_node.getAttributeNS(None, "_indent"):
                    break
                if int(parent_node.getAttributeNS(None, "_indent")) <= _indent:
                    break
                parent_node = parent_node.parentNode
                if parent_node.nodeName not in BLOCK_ELEMENTS:
                    continue
            context.currentNode = parent_node
            definition_node = context.document.createElementNS(None, "definition-list")
            definition_node.setAttributeNS(None, "_indent", str(_indent))
            context.currentNode.appendChild(definition_node)
            parent_node = definition_node
        # Creates the definition item
        definition_item = context.document.createElementNS(None, "definition-item")
        definition_item.setAttributeNS(None, "_indent", str(_indent + 1))
        definition_title = context.document.createElementNS(None, "title")
        definition_title.setAttributeNS(None, "_start", str(context.blockStartOffset))
        definition_title.setAttributeNS(
            None, "_end", str(context.blockStartOffset + len(match.group()))
        )
        # Parse the content of the definition title
        offsets = context.saveOffsets()
        context.setCurrentBlock(
            context.blockStartOffset, context.blockStartOffset + len(match.group(1))
        )
        context.parser.parseBlock(context, definition_title, self.processText)
        context.restoreOffsets(offsets)
        # And continue the processing
        definition_content = context.document.createElementNS(None, "content")
        definition_content.setAttributeNS(None, "_indent", str(_indent + 1))
        definition_content.setAttributeNS(
            None, "_start", str(context.blockStartOffset + match.end())
        )
        definition_content.setAttributeNS(None, "_end", str(context.blockEndOffset))
        definition_item.appendChild(definition_title)
        definition_item.appendChild(definition_content)
        parent_node.appendChild(definition_item)
        context.currentNode = definition_content
        # We check if there is a rest after the definition name
        rest = context.documentText[
            context.blockStartOffset + match.end() : context.blockEndOffset
        ]
        if not context.parser.normaliseText(rest).strip():
            rest = ""
        if rest:
            offsets = context.saveOffsets()
            context.setCurrentBlock(
                context.blockStartOffset + match.end(), context.blockEndOffset
            )
            context.parser.parseBlock(context, definition_content, self.processText)
            context.restoreOffsets(offsets)

    def processText(self, context, text):
        return context.parser.normaliseText(text)


# ------------------------------------------------------------------------------
#
# LIST ITEM BLOCK PARSER
#
# ------------------------------------------------------------------------------


class ListItemBlockParser(BlockParser):
    """Parses a list item. A list item is an element within a list."""

    def __init__(self):
        BlockParser.__init__(self, "list-item")

    def recognises(self, context):
        return RE_LIST_ITEM.match(context.currentFragment())

    def process(self, context, itemMatch):
        # These two lines will reuse a previous list item as the current node
        if context.lastBlockNode and context.lastBlockNode.nodeName == "list-item":
            context.currentNode = context.lastBlockNode
        context.ensureParent(("content", "appendix", "chapter", "section", "list"))
        start_offset = context.getOffset()

        # Step 1: Determine the range of the current line item in the current
        # block. There may be more than one line item as in the following:
        # "- blah blah\n - blah blah"
        # So we have to look for another line item in the current block

        # To do so, we move the offset after the recognised list item, ie.
        # after the leading "1)", "*)", etc
        context.increaseOffset(itemMatch.end())

        # Next item match will indicate where in the current fragment the next
        # item starts.
        next_item_match = None
        if context.blockEndReached():
            context.parser.warning(EMPTY_LIST_ITEM, context)
            return

        # We search a possible next list item after the first eol in the
        # current fragment, or at the beginning of the next fragment.
        next_eol = context.currentFragment().find("\n")
        if next_eol != -1:
            next_item_match = RE_LIST_ITEM.search(context.currentFragment(), next_eol)
        else:
            next_item_match = None

        # We assign to current_item_text the text of the current item
        current_item_text = context.currentFragment()
        if next_item_match:
            current_item_text = current_item_text[: next_item_match.start()]

        # We get the list item indentation, based on the indentation of the
        # item
        indent = context.parser.getIndentation(itemMatch.group(0))

        # We look for the optional list heading
        heading = RE_LIST_ITEM_HEADING.match(current_item_text)
        heading_offset = 0
        list_type = STANDARD_LIST
        item_type = STANDARD_ITEM
        if heading:
            # We remove the heading from the item text
            heading_offset = heading.end()
            # And update the heading variable with the heading text
            if heading.group(1):
                list_type = STANDARD_LIST
                heading_end = heading.group().rfind(":")
            else:
                list_type = DEFINITION_LIST
                heading_end = heading.group().rfind("/")

        head = itemMatch.group(2)
        if head:
            head = head.upper()
            if head == "[ ]":
                item_type = TODO_ITEM
                list_type = TODO_LIST
            elif head == "[X]":
                item_type = TODO_DONE_ITEM
                list_type = TODO_LIST
            elif RE_NUMBER.match(head):
                list_type = ORDERED_LIST

        # The current_item_text is no longer used in the following code

        # Step 2: Now that we have the item body, and that we know if there is
        # a next item (next_item_match), we can create the list item node. To
        # do so, we first have to look for a parent "list" node in which the
        # "list-item" node we wish to create will be inserted.

        # We want either a "list" with a LOWER OR EQUAL indent, or a "list-item"
        # with a STRICTLY LOWER indentation, or a node which is neither a List
        # or a ListItem.
        while (
            context.currentNode.nodeName == "list"
            and int(context.currentNode.getAttributeNS(None, "_indent")) > indent
            or context.currentNode.nodeName == "list-item"
            and int(context.currentNode.getAttributeNS(None, "_indent")) >= indent
        ):
            context.currentNode = context.currentNode.parentNode

        # If the current node is a list, then we have to create a nested list.
        # A List ALWAYS have at least one child ListItem. If the last ListItem
        # has the same indentation as our current list item, then it is a
        # sibling, otherwise it is a parent.
        if context.currentNode.nodeName == "list":
            # A List should always have a least one ListItem
            items = context._getElementsByTagName(context.currentNode, "list-item")
            assert len(items) > 0
            if int(items[-1].getAttributeNS(None, "_indent")) < indent:
                context.currentNode = items[-1]

        # We may need to create a new "list" node to hold our list items
        list_node = context.currentNode
        # If the current node is not a list, then we must create a new list
        if context.currentNode.nodeName != "list":
            list_node = context.document.createElementNS(None, "list")
            list_node.setAttributeNS(None, "_indent", str(indent))
            context.currentNode.appendChild(list_node)
            context.currentNode = list_node
        # We create the list item
        list_item_node = context.document.createElementNS(None, "list-item")
        list_item_node.setAttributeNS(None, "_indent", str(indent))
        if item_type == TODO_ITEM:
            list_item_node.setAttributeNS(None, "todo", "true")
        elif item_type == TODO_DONE_ITEM:
            list_item_node.setAttributeNS(None, "todo", "done")
        list_item_node.setAttributeNS(None, "_start", str(context.getOffset()))
        if next_item_match:
            list_item_node.setAttributeNS(
                None, "_end", str(context.getOffset() + next_item_match.start() - 1)
            )
        else:
            list_item_node.setAttributeNS(None, "_end", str(context.blockEndOffset))
        # and the optional heading
        if heading:
            offsets = context.saveOffsets()
            heading_node = context.document.createElementNS(None, "heading")
            context.setCurrentBlock(
                context.getOffset(), context.getOffset() + heading_end
            )
            context.parser.parseBlock(context, heading_node, self.processText)
            # heading_text = context.document.createTextNode(heading)
            # heading_node.appendChild(heading_text)
            list_item_node.appendChild(heading_node)
            context.restoreOffsets(offsets)
        # and the content
        offsets = context.saveOffsets()
        if next_item_match:
            context.setCurrentBlock(
                heading_offset + context.getOffset(),
                context.getOffset() + next_item_match.start(),
            )
        else:
            context.increaseOffset(heading_offset)
        # We parse the content of the list item
        old_node = context.currentNode
        # We temporarily set he list item node as the current node
        context.currentNode = list_item_node
        context.parser.parseBlock(context, list_item_node, self.processText)
        context.restoreOffsets(offsets)
        # We eventually append the created list item node to the parent list
        # node
        list_node.appendChild(list_item_node)
        # We set the type attribute of the list if necesseary
        if list_type == DEFINITION_LIST:
            list_node.setAttributeNS(None, "type", "definition")
        elif list_type == TODO_LIST:
            list_node.setAttributeNS(None, "type", "todo")
        elif list_type == ORDERED_LIST:
            list_node.setAttributeNS(None, "type", "ordered")

        # And recurse with other line items
        if next_item_match:
            # We set the offset in which the next_item Match object was
            # created, because match object start and end are relative
            # to the context offset at pattern matching time.
            context.lastBlockNode = context.currentNode
            list_item_node = self.process(context, next_item_match)
        # Or we have reached the block end
        else:
            context.setOffset(context.blockEndOffset)

        # We set the current node to be the list item node
        context.currentNode = list_item_node
        return list_item_node

    def processText(self, context, text):
        text = context.parser.expandTabs(text)
        text = context.parser.normaliseText(text)
        return text


# ------------------------------------------------------------------------------
#
# PRE BLOCK PARSER (ORIGINAL TEXTO)
#
# ------------------------------------------------------------------------------


class PreBlockParser(BlockParser):
    """Parses the content of a preformatted block, where every line is
    prefixed by '>   '."""

    def __init__(self):
        BlockParser.__init__(self, "pre")

    def recognises(self, context):
        for line in context.currentFragment().split("\n"):
            if line and not RE_PREFORMATTED.match(line):
                return False
        return True

    def process(self, context, recogniseInfo):
        text = ""
        for line in context.currentFragment().split("\n"):
            match = RE_PREFORMATTED.match(line)
            if match:
                text += match.group(3) + "\n"
            else:
                text += line + "\n"
        if text[-1] == "\n":
            text = text[:-1]
        pre_node = context.document.createElementNS(None, self.name)
        pre_node.appendChild(context.document.createTextNode(text))
        pre_node.setAttributeNS(None, "_start", str(context.getOffset()))
        pre_node.setAttributeNS(None, "_end", str(context.blockEndOffset))
        context.currentNode.appendChild(pre_node)


# ------------------------------------------------------------------------------
#
# PRE BLOCK PARSER (MARKDOWN)
#
# ------------------------------------------------------------------------------


class PreBlockParser2(BlockParser):
    """Parses the content of a preformatted block which is delimited with
    '```' and '```' characters."""

    START_PATTERN = PREFORMATTED_2_START
    END_PATTERN = PREFORMATTED_2_END

    def __init__(self):
        BlockParser.__init__(self, "pre")

    def recognises(self, context):
        head_lines = context.currentFragment().split("\n")
        while not head_lines[0].strip():
            head_lines = head_lines[1:]
        if not head_lines:
            return False
        match = self.isStartLine(context, head_lines[0])
        if match:
            return True, context.parser.getIndentation(head_lines[0]), match
        else:
            return False

    def isStartLine(self, context, line):
        return self.START_PATTERN.match(line)

    def isEndLine(self, context, line, indent):
        line_indent = context.parser.getIndentation(line)
        if line_indent != indent:
            return False
        return self.END_PATTERN.match(line)

    def findBlockEnd(self, context, indent):
        # FIXME: Issue a warning if no end is found
        cur_offset = context.blockEndOffset + 1
        block_end = context.blockEndOffset
        text = context.documentText
        # FIXME: THis should be rewritten
        # We look beyond the current block end, as  the preformatted block
        # may start with empty newlines
        # while block_end < len(text) and text[block_end] in "\n\t ":
        # 	block_end += 1
        fragment = text[context.blockStartOffset : block_end]
        lines = fragment.split("\n")
        if self.isEndLine(context, lines[-1], indent):
            return block_end
        # We look beyond the current block end, as  the preformatted block
        # may start with empty newlines
        while block_end < len(text) and text[block_end] in "\n\t ":
            block_end += 1
        fragment = text[context.blockStartOffset : block_end]
        lines = fragment.split("\n")
        if self.isEndLine(context, lines[-1], indent):
            return block_end
        while True:
            next_eol = context.documentText.find("\n", cur_offset)
            if next_eol == -1:
                break
            line = context.documentText[cur_offset:next_eol]
            if self.isEndLine(context, line, indent):
                block_end = next_eol + 1
                break
            if line.strip() and context.parser.getIndentation(line) < indent:
                break
            block_end = next_eol + 1
            cur_offset = block_end
        return block_end - 1

    def getLeadingSpaces(self, context, offset):
        e = offset
        o = e
        t = context.documentText
        while o > 0 and t[o] in " \t":
            o -= 1
        return t[o + 1 : e]

    def process(self, context, recognised):
        result = []
        _, indent, match = recognised
        # We extract the lang{range}|process structure.
        lang = match.group(3)
        # We find the block end
        context.setCurrentBlockEnd(self.findBlockEnd(context, indent))
        lines = context.currentFragment().split("\n")
        while not lines[0]:
            lines = lines[1:]
        lines = lines[1:-1]
        prefix = self.getLeadingSpaces(
            context, context.blockStartOffset - len(match.group(0)) - 1
        )
        if lines:
            for line in lines:
                line = line[len(prefix) :].replace("\t", TAB_VALUE)
                result.append(line)
        text = "\n".join(result)
        pre_node = context.document.createElementNS(None, self.name)
        pre_node.appendChild(context.document.createTextNode(text))
        if lang:
            pre_node.setAttributeNS(None, "data-lang", lang)
        pre_node.setAttributeNS(None, "_start", str(context.getOffset()))
        pre_node.setAttributeNS(None, "_end", str(context.blockEndOffset))
        context.currentNode.appendChild(pre_node)


# ------------------------------------------------------------------------------
#
# TABLE BLOCK PARSER
#
# ------------------------------------------------------------------------------


class Table:
    """The table class allows to easily create tables and then generate the
    XML objects from them."""

    def __init__(self):
        # Table is an array of array of (char, string) where char is either
        # 'H' for header, or 'T' for text.
        self._table = []
        self._rows = 0
        self._cols = 0
        self._title = None
        self._id = None

    def dimension(self):
        return len(self._table[0]), len(self._table)

    def getRow(self, y):
        return self._table[y]

    def _ensureCell(self, x, y):
        """Ensures that the cell at the given position exists and returns its
        pair value."""
        while y >= len(self._table):
            self._table.append([])
        row = self._table[y]
        while x >= len(row):
            row.append(["T", None])
        self._cols = max(self._cols, x + 1)
        self._rows = max(self._rows, y + 1)
        return row[x]

    def setTitle(self, title):
        """Sets the title for this table."""
        self._title = title.strip()

    def setID(self, id):
        """Sets the id for this table."""
        self._id = id.strip()

    def appendCellContent(self, x, y, text):
        cell_type, cell_text = self._ensureCell(x, y)
        if cell_text == None:
            self._table[y][x] = [cell_type, text]
        else:
            self._table[y][x] = [cell_type, cell_text + "\n" + text]

    def headerCell(self, x, y):
        self._table[y][x] = ["H", self._ensureCell(x, y)[1]]

    def dataCell(self, x, y):
        self._table[y][x] = ["T", self._ensureCell(x, y)[1]]

    def isHeader(self, x, y):
        if len(self._table) < y or len(self._table[y]) < x:
            return False
        row = self._table[y]
        if x >= len(row):
            return False
        return self._table[y][x][0] == "H"

    def getNode(self, context, processText):
        """Renders the table as a Texto XML document node."""
        table_node = context.document.createElementNS(None, "table")
        content_node = context.document.createElementNS(None, "content")
        # We set the id
        if self._id:
            table_node.setAttributeNS(None, "id", self._id)
        # We take care of the title
        if self._title:
            caption_node = context.document.createElementNS(None, "caption")
            caption_text = context.document.createTextNode(self._title)
            caption_node.appendChild(caption_text)
            table_node.appendChild(caption_node)
        # And now of the table
        for row in self._table:
            row_node = context.document.createElementNS(None, "row")
            i = 0
            for cell_type, cell_text in row:
                is_first = i == 0
                is_last = i == len(row) - 1
                cell_node = context.document.createElementNS(None, "cell")
                if cell_type == "H":
                    cell_node.setAttributeNS(None, "type", "header")
                # We create a temporary Content node that will stop the nodes
                # from seeking a parent content
                cell_content_node = context.document.createElementNS(None, "content")
                if is_last and len(row) != self._cols:
                    cell_node.setAttributeNS(None, "colspan", "%s" % (len(row) + 2 - i))
                new_context = context.clone()
                new_context.setDocumentText(cell_text)
                new_context.currentNode = cell_content_node
                new_context.parser.parseContext(new_context)
                # This is slightly hackish, but we simply move the nodes there
                for child in cell_content_node.childNodes:
                    cell_node.appendChild(child)
                row_node.appendChild(cell_node)
                i += 1
            content_node.appendChild(row_node)
        table_node.appendChild(content_node)
        return table_node

    def __repr__(self):
        s = ""
        i = 0
        for row in self._table:
            s += "%2d: %s\n" % (i, row)
            i += 1
        return s


class TableBlockParser(BlockParser):
    """Parses the content of a tables"""

    def __init__(self):
        BlockParser.__init__(self, "table")

    def recognises(self, context):
        lines = context.currentFragment().strip().split("\n")
        if not len(lines) > 1:
            return False
        title_match = RE_TITLE.match(lines[0])
        if title_match:
            if not len(lines) >= 3:
                return False
            start_match = RE_TABLE_ROW_SEPARATOR.match(lines[1])
        else:
            start_match = RE_TABLE_ROW_SEPARATOR.match(lines[0])
        end_match = RE_TABLE_ROW_SEPARATOR.match(lines[-1])
        return start_match and end_match

    def process(self, context, recogniseInfo):
        y = 0
        table = Table()
        # For each cell in a row
        rows = context.currentFragment().strip().split("\n")[:-1]
        # We take care of the title
        title_match = RE_TITLE.match(rows[0])
        if title_match:
            title_name = title_match.group(2).split("#", 1)
            title_id = None
            if len(title_name) == 2:
                title_name, title_id = title_name
                table.setTitle(title_name)
                table.setID(title_id)
            elif len(title_name) == 1:
                title_name = title_name[0]
                table.setTitle(title_name)
            rows = rows[2:]
        else:
            rows = rows[1:]
        # The cells are separated by pipes (||)
        for row in rows:
            cells = []
            x = 0
            # Empty rows are simply ignored
            if not row.strip():
                continue
            separator = RE_TABLE_ROW_SEPARATOR.match(row)
            # If we have not found a separator yet, we simply ensure that the
            # cell exists and appends content to it
            if not separator:
                # If the separator is not '||' it is '|'
                if row.find("||") == -1:
                    row = row.replace("|", "||")
                for cell in row.split("||"):
                    cells.append(cell)
                    # We remove leading or trailing borders (|)
                    if cell and cell[0] == "|":
                        cell = cell[1:]
                    if cell and cell[-1] == "|":
                        cell = cell[:-1]
                    table.appendCellContent(x, y, cell)
                    # FIXME: Weird rule
                    # The default cell type is the same as the above
                    # cell, if any.
                    # if y>0 and table.isHeader(x,y-1):
                    # 	table.headerCell(x,y)
                    x += 1
            # We move to the next row only when we encounter a separator. The
            # analysis of the separator will tell you if the above cell is a
            # header or a data cell
            else:
                # FIXME: This is wrong, see below
                if separator.group(1)[0] == "=":
                    row_count = table.dimension()[1]
                    if row_count > 0:
                        for cell in table.getRow(row_count - 1):
                            cell[0] = "H"
                if separator.group(1)[0] == "-":
                    row_count = table.dimension()[1]
                    if row_count > 0:
                        for cell in table.getRow(row_count - 1):
                            cell[0] = "T"
                # FIXME: Should handle vertical tables also
                # ==================================
                # HEADER || DATA
                # =======++-------------------------
                # ....
                offset = 0
                x = 0
                # FIXME: Here cells is always empty
                for cell in cells:
                    assert None, "Should not be here"
                    if separator.group(1)[offset] == "=":
                        table.headerCell(x, y)
                    else:
                        table.dataCell(x, y)
                    offset += len(cell)
                    x += 1
                y += 1
        context.currentNode.appendChild(table.getNode(context, self.processText))


# ------------------------------------------------------------------------------
#
# META BLOCK PARSER
#
# ------------------------------------------------------------------------------


class MetaBlockParser(BlockParser):
    """Parses the content of a Meta block"""

    START_PATTERN = RE_META_START
    END_PATTERN = RE_META_END

    def __init__(self):
        BlockParser.__init__(self, "meta")

    def recognises(self, context):
        head_lines = context.currentFragment().split("\n")
        while not head_lines[0].strip():
            head_lines = head_lines[1:]
        if not head_lines:
            return False
        match = self.START_PATTERN.match(head_lines[0])
        if match:
            return True, context.parser.getIndentation(head_lines[0]), match
        else:
            return False

    def process(self, context, recogniseInfo):
        text = ""
        _, indent, match = recogniseInfo
        lines = context.currentFragment().split("\n")[1:-1]
        rows = [
            context.node(
                "meta",
                name=line.split(":", 1)[0].strip(),
                value=line.split(":", 1)[-1].strip(),
            )
            for line in lines
            if line.strip()
        ]
        return context.addNode(
            "meta",
            *rows,
            _start=str(context.getOffset()),
            _end=str(context.blockEndOffset),
        )


# ------------------------------------------------------------------------------
#
# REFERENCE ENTRY BLOCK PARSER
#
# ------------------------------------------------------------------------------


class ReferenceEntryBlockParser(BlockParser):
    """Parses the content of a Reference entry"""

    def __init__(self):
        BlockParser.__init__(self, "entry")

    def recognises(self, context):
        assert context
        return RE_REFERENCE_ENTRY.match(context.currentFragment())

    def process(self, context, match):
        offsets = context.saveOffsets()
        ranges = []
        offset = 0
        # We get the start and end offsets of entry blocks
        while True:
            m = RE_REFERENCE_ENTRY.search(context.currentFragment(), offset)
            if not m:
                break
            ranges.append((m, m.start()))
            offset = m.end()
        ranges.append((None, len(context.currentFragment())))
        new_ranges = []
        for i in range(0, len(ranges) - 1):
            new_ranges.append((ranges[i][0], ranges[i][1], ranges[i + 1][1]))
        ranges = new_ranges
        # We loop for each found reference entry
        for match, start_offset, end_offset in ranges:
            entry_name = match.group(1)
            # We set the current block and process it
            sub_offsets = context.saveOffsets()
            context.setCurrentBlock(
                context.getOffset() + match.end(), context.getOffset() + end_offset
            )
            entry_node = context.document.createElementNS(None, "entry")
            entry_node.setAttributeNS(None, "id", entry_name)
            context.parser.parseBlock(context, entry_node, self.processText)
            context.references.appendChild(entry_node)
            context.restoreOffsets(sub_offsets)
        context.restoreOffsets(offsets)


# EOF
