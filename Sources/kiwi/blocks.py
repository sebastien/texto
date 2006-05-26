#!/usr/bin/env python
# Encoding: iso-8859-1
# -----------------------------------------------------------------------------
# Project           :   Kiwi
# Module            :   Block parsers
# -----------------------------------------------------------------------------
# Author            :   Sébastien Pierre (SPE)           <sebastien@type-z.org>
# -----------------------------------------------------------------------------
# Creation date     :   19-Nov-2003
# Last mod.         :   10-Feb-2006
# History           :
#                       10-Feb-2006 Added Block creation in paragraphs to
#                       allowed "nested paragraphs" (a la Blockquote)
#                       08-Feb-2006 Changed title format, made paragraph go into
#                       list items if the list items have the same indentation
#                       as the paragraph.
#                       27-Dec-2004 Table parser implementation (SPE)
#                       26-Dec-2004 Fixed list item heading, section depth (SPE)
#                       01-Dec-2004 Added reference node. (SPE)
#                       05-Oct-2004 Enhanced meta block fields, attributes are
#                       handled in custom blocks. (SPE)
#                       27-Sep-2004 Added meta block parser (SPE)
#                       31-Mar-2004 Does not add empty paragraphs (SPE)
#                       23-Jan-2004 Implemented comment block (SPE)
#                       22-Jan-2004 Fixed list items parsing (SPE)
#                       20-Jan-2004 Implemented block parser (SPE)
#                       07-Jan-2004 Updated to use 4Suite DOM (SPE)
#                       13-Dec-2003 More list item block parser work (SPE)
#                       22-Nov-2003 Preliminary work on lists (SPE)
#                       19-Nov-2003 First (re-)implementation (SPE)
#
# Bugs              :
#                       -
# To do             :
#                       - Add a "moveToParentNode" method in Blocks
#                       - ListItem illustrates a case where the current node is
#                         not proper for parsing blocks
#                       - Enhance implementation of Meta which is a bit rough
#

import re, string
from kiwi.formatting import *

__doc__ = """Write module doc here"""
__pychecker__ = "unusednames=recogniseInfo,content"


EMPTY_LIST_ITEM = "Empty list item."

BLOCK_ELEMENTS = ("Block", "ListItem", "Content", "Chapter", "Section", "Appendix")

STANDARD_LIST    = 1
DEFINITION_LIST  = 2

#------------------------------------------------------------------------------
#
#  Regular expressions
#
#------------------------------------------------------------------------------

RE_BLANK          = re.compile(u"\s*", re.LOCALE|re.MULTILINE)

TITLE             = u"\s*(==)(.+)$"
RUNNING_TITLE     = u"\s*(--)(.+)$"
TITLES            = u"%s|%s" % (RUNNING_TITLE, TITLE)
RE_TITLES          = re.compile(TITLES, re.LOCALE|re.MULTILINE)

SECTION_HEADING   = u"^\s*((([0-9]+|[A-z])\.)+([0-9]+|[A-z])?\.?)"
RE_SECTION_HEADING= re.compile(SECTION_HEADING, re.LOCALE)
SECTION_UNDERLINE = u"^\s*[*-=#]+\s*$"
RE_SECTION_UNDERLINE = re.compile(SECTION_UNDERLINE, re.LOCALE|re.MULTILINE)

LIST_ITEM         = u"^(\s*)(-|\*\)|[0-9A-z][\)/\.])\s*"
RE_LIST_ITEM      = re.compile(LIST_ITEM, re.MULTILINE | re.LOCALE)
LIST_HEADING      = u"(^\s*[^:{().<]*:)"
RE_LIST_HEADING   = re.compile(LIST_HEADING, re.MULTILINE | re.LOCALE)
LIST_ITEM_HEADING = u"^([^:]+(:\s*\n\s*|::\s*))|([^/\\\]+[/\\\]\s*\n\s*)"
RE_LIST_ITEM_HEADING =  re.compile(LIST_ITEM_HEADING, re.MULTILINE|re.LOCALE)

PREFORMATTED      = u"^(\s*\>\t)(.*)$"
RE_PREFORMATTED   = re.compile(PREFORMATTED, re.LOCALE)

CUSTOM_MARKUP = u"\s*-\s*\"([^\"]+)\"\s*[=:]\s*([\w\-_]+)(\s*\(\s*(\w+)\s*\))?"
RE_CUSTOM_MARKUP = re.compile(CUSTOM_MARKUP, re.LOCALE|re.MULTILINE)

INCLUDE_SIMTEX    = u"\s*\[\s*\$\s*:([^\]]+)\]"
RE_INCLUDE_SIMTEX = re.compile(INCLUDE_SIMTEX, re.MULTILINE|re.LOCALE)

META_TYPE        = u"\s*(\w+)\s*(\((\w+)\))?"
RE_META_TYPE     = re.compile(META_TYPE, re.LOCALE|re.MULTILINE)

META_FIELD = u'(^|\n)\s*([\w\-]+)\s*:\s*'
RE_META_FIELD= re.compile(META_FIELD, re.LOCALE)
RE_META_AUTHOR_EMAIL = re.compile("\<([^>]+)\>", re.LOCALE)

BIBLIOGRAPHIC_ENTRY = u"\s*\.\.+\s+([\w_\-]+)\s*:"
RE_BIBLIOGRAPHIC_ENTRY = re.compile(BIBLIOGRAPHIC_ENTRY, re.LOCALE|re.MULTILINE)

TABLE_SEPARATOR    = "^\s*(-+|=+)\s*$"
RE_TABLE_SEPARATOR = re.compile(TABLE_SEPARATOR)

LANGUAGE_CODES = ("EN", "FR", "DE", "UK" )

#------------------------------------------------------------------------------
#
#  Error messages
#
#------------------------------------------------------------------------------

ERROR_TITLE_TOO_DEEPLY_NESTED = "Title too deeply nested"

#------------------------------------------------------------------------------
#
#  BlockParser
#
#------------------------------------------------------------------------------

class BlockParser:

	def __init__( self, name ):
		self.name = name

	def recognises( self, context ):
		"""Tells wether the given block is recognised or not. This returns
		this block recognition information, or False (or None) if the block was
		not recongised."""
		return False

	def process( self, context, recogniseInfo ):
		return None

	def processText( self, context, text ):
		assert context, text
		return text

#------------------------------------------------------------------------------
#
#  ParagraphBlockParser
#
#------------------------------------------------------------------------------

class ParagraphBlockParser(BlockParser):
	"""Parses a paragraph block. This parser always recognised the given block,
	so it should not appear in the block parsers."""

	def __init__( self ):
		BlockParser.__init__(self, "Paragraph")

	def recognises( self, context ):
		return True

	def process( self, context, recogniseInfo ):
		# We make sure that the current node is a block element
		paragraph_depth = context.getBlockIndentation()
		# Here we move to the first block element that has an indentation that
		# is lower or equal to this paragraph
		while context.currentNode.nodeName not in BLOCK_ELEMENTS \
		or context.currentNode.getAttribute("_indent") \
		and int(context.currentNode.getAttribute("_indent"))>paragraph_depth:
			context.currentNode = context.currentNode.parentNode
		# If the currentNode last element is a paragraph with a higher
		# indentation than the current one, then we create a block, and set it
		# as current node (this allows to create "indented paragraphs" - the
		# equivalent of blockquotes).
		if context.currentNode.childNodes \
		and context.currentNode.childNodes[-1].nodeName == "Paragraph" \
		and context.currentNode.childNodes[-1].getAttribute("_indent") \
		and int(context.currentNode.childNodes[-1].getAttribute("_indent"))<paragraph_depth:
			block_node = context.document.createElementNS(None, "Block")
			block_node.setAttributeNS(None, "_indent", str(paragraph_depth))
			context.currentNode.appendChild(block_node)
			context.currentNode = block_node
		# Now we can process the document
		para_node = context.document.createElementNS(None, self.name)
		para_node.setAttributeNS(None, "_indent", str(paragraph_depth))
		context.parser.parseBlock(context, para_node, self.processText)
		# Now we suppress leading and trailing whitespaces
		first_text_node = None
		last_text_node = None
		for child_node in para_node.childNodes:
			if child_node.nodeType == child_node.TEXT_NODE:
				if first_text_node == None:
					first_text_node = child_node
				else:
					last_text_node = child_node
		# Removed first and last text nodes if empty
		if first_text_node!=None and first_text_node.data.strip()=="":
			para_node.removeChild(first_text_node)
			first_text_node = None
		if last_text_node!=None and last_text_node.data.strip()=="":
			para_node.removeChild(last_text_node)
			last_text_node = None
		# We strip the leading whitespace
		if first_text_node!=None and len(first_text_node.data)>0 and \
			first_text_node.data[0] == " ":
			first_text_node.data = first_text_node.data[1:]
		if last_text_node!=None and len(last_text_node.data)>0 and \
			last_text_node.data[-1] == " ":
			last_text_node.data = last_text_node.data[:-1]
		# FIXME: Maybe the paragraph contains text nodes with only spaces ?
		if len(para_node.childNodes)>0:
			context.currentNode.appendChild(para_node)
		else:
			context.parser.warning("Empty paragraph removed", context)

	def processText( self, context, text ):
		assert text
		text = context.parser.expandTabs(text)
		text =  context.parser.normaliseText(text)
		return text

#------------------------------------------------------------------------------
#
#  CommentBlockParser
#
#------------------------------------------------------------------------------

class CommentBlockParser(BlockParser):
	"""Parses a comment markup block."""

	def __init__( self ):
		BlockParser.__init__(self, "CommentBlock")

	def recognises( self, context ):
		assert context and context.parser.commentParser
		lines = context.currentFragment().split("\n")
		for line in lines:
			line = line.strip()
			if line and line.strip()[0]!= "#": return False
		return True

	def process( self, context, recogniseInfo ):
		context.currentNode.appendChild( context.document.createComment(
		self.processText(context, context.currentFragment())))
		context.setOffset(context.blockEndOffset)


#------------------------------------------------------------------------------
#
#  MarkupBlockParser
#
#------------------------------------------------------------------------------

class MarkupBlockParser(BlockParser):
	"""Parses a custom markup block."""

	def __init__( self ):
		BlockParser.__init__(self, "MarkupBlock")

	def recognises( self, context ):
		assert context and context.parser.markupParser
		offset, match = context.parser.markupParser.recognises(context)
		# We make sure that the recognised markup is a block markup which has
		# only whitespaces at the beginning
		if match and match.group(1) in context.parser.markupParser.START_TAGS\
		and match.group(2)!=None \
		and len(context.currentFragment()[:match.start()].strip())==0:
			# We parse the tag to see if it is a block tag and that it spans
			# the whole context current fragment.
			dummy_node = context.document.createElementNS(None, "Dummy")
			match_end = context.parser.markupParser.parse(context, dummy_node, match)
			# The returned matched end MUST BE GREATER than the start tag match
			# end, and there MUST BE ONLY SPACES after the match end for this
			# tag to represent a standalone block, and not a block inlined into
			# a paragraph.
			if match_end > match.end() and \
			len(context.currentFragment()[match_end:].strip())==0:
				# If there is a child node, we return it
				if len(dummy_node.childNodes)>=1:
					result_node = dummy_node.childNodes[0]
					# We take care of the attributes
					for key, value in \
					    context.parseAttributes(match.group(4)).items():
						result_node.setAttributeNS(None, key, value)
					return result_node
				# Otherwise this means that the block is empty
				else: return True
			else:
				return False
		else:
			return False

	def process( self, context, recogniseInfo ):
		if recogniseInfo!=True:
			context.currentNode.appendChild(recogniseInfo)
		context.setOffset(context.blockEndOffset)


#------------------------------------------------------------------------------
#
#  TitleBlockParser
#
#------------------------------------------------------------------------------

class TitleBlockParser(BlockParser):
	"""Parses a title object.

	A title object is a text surrounded by two '~'."""

	def __init__( self ):
		BlockParser.__init__(self, "title")

	def recognises( self, context ):
		matches = []
		while not context.blockEndReached():
			match = RE_TITLES.match(context.currentFragment())
			if match!=None:
				context.increaseOffset(match.end())
				matches.append(match)
			else:
				return False
		return matches

	def process( self, context, recogniseInfo ):
		assert recogniseInfo
		titleNode = context.ensureElement( context.header, "Title" )
		for match in recogniseInfo:
			#We get the content of the title
			titleText = Upper(match.group(2) or match.group(4))
			# We prefix with 'sub' or 'subsub' depending on the number of
			# preceding titles
			titleType  = u"sub" * len(filter(lambda n:n.nodeName.endswith("title"), titleNode.childNodes))
			titleType += u"title"
			#We add the node to the document tree
			resultNode = context.ensureElement(titleNode, titleType)
			titleNode.appendChild(resultNode)
			resultNode.appendChild(context.document.createTextNode(self.processText(context, titleText)))
			#We parse the next title
		context.setOffset(context.blockEndOffset)

	def processText( self, context, text ):
		return context.parser.normaliseText(text.strip())

#------------------------------------------------------------------------------
#
#  SectionBlockParser
#
#------------------------------------------------------------------------------

class SectionBlockParser(BlockParser):
	"""Parses a section markup element."""

	def __init__( self ):
		BlockParser.__init__(self, "Section")

	def recognises( self, context ):
		# We look for the number prefix
		match = RE_SECTION_HEADING.match(context.currentFragment())
		# We return directly if there are at least two section numbers (2.3)
		if match and match.group(4):
			return (RE_SECTION_HEADING, match)
		# Or a separator followed by blank space
		match = RE_SECTION_UNDERLINE.search(context.currentFragment())
		if  match:
			# If we reached the end of the block, this OK
			if match.end() == context.blockEndOffset:
				return (RE_SECTION_UNDERLINE, match)
			# Otherwise the rest must be blank
			else:
				blank_match = RE_BLANK.match(context.currentFragment()[match.end():])
				# The rest is blank, it's OK
				if blank_match.end()+match.end()+context.getOffset()\
					==context.blockEndOffset:
					return (RE_SECTION_UNDERLINE, match)
				# Otherwise there is a trailing text
				else:
					return None
		# Nothing matched
		else:
			return None

	def getHeadingDepth( self, heading ):
		return len(filter(lambda x:x, heading.split(".")))

	def process( self, context, recogniseInfo ):
		context.ensureParent( ("Content", "Appendix", "Chapter", "Section") )
		matched_type, match = recogniseInfo
		section_depth = context.getBlockIndentation()
		# FIRST STEP - We detect section text bounds
		block_start = context.blockStartOffset
		block_end = context.blockEndOffset
		section_type = "Section"
		# We have a numbered section
		if matched_type == RE_SECTION_HEADING:
			# The depth is the number of dot-separated symbols
			section_depth += self.getHeadingDepth(match.group(1))
			# Is a chapter or appendix ?
			first_char = match.group(1)[0]
			if first_char in ( u'I', u'V', u'V', u'X'):
				section_type = "Chapter"
			elif first_char.upper() == "A":
				section_type = "Appendix"
			block_start = context.getOffset() + match.end()
			# We make sure that we end the section before the block delimiter
			delim_match = RE_SECTION_UNDERLINE.search(context.currentFragment())
			if delim_match: block_end = context.getOffset() + delim_match.start()
		# We have an unnumbered section
		else:
			block_end = context.getOffset() + match.start()
		# SECOND STEP - We look for a parent node, which would have a depth
		# smaller than the current one or that would not be a section node
		while context.currentNode.nodeName == "Content" \
		and context.currentNode.parentNode.nodeName == "Section" \
		and int(context.currentNode.parentNode.getAttributeNS(None, "_depth")) >= section_depth:
			context.currentNode = context.currentNode.parentNode.parentNode
		# THIRD STEP - We create the section
		section_node = context.document.createElementNS(None, section_type)
		section_node.setAttributeNS(None, "_depth", str(section_depth))
		heading_node = context.document.createElementNS(None, "Heading")
		section_node.appendChild(heading_node)
		offsets = context.saveOffsets()
		context.blockEndOffset = block_end
		context.setOffset(block_start)
		context.parser.parseBlock(context, heading_node, self.processText)
		context.restoreOffsets(offsets)
		# Now we create a Content node
		content_node = context.document.createElementNS(None, "Content")
		section_node.appendChild(content_node)
		# We append the section node and assign it as current node
		context.currentNode.appendChild(section_node)
		context.currentNode = content_node

	def processText( self, context, text ):
		return context.parser.normaliseText(text.strip())

#------------------------------------------------------------------------------
#
#  ListItemBlockParser
#
#------------------------------------------------------------------------------

class ListItemBlockParser(BlockParser):
	"""Parses a list item. A list item is an element within a list."""

	def __init__( self ):
		BlockParser.__init__(self, "ListItem")

	def recognises( self, context ):
		return RE_LIST_ITEM.match(context.currentFragment())

	def process( self, context, itemMatch ):

		context.ensureParent( ("Content", "Appendix", "Chapter", "Section", "List") )

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

		# We search a possible next list item after the first eol
		next_eol = context.currentFragment().find("\n")
		if next_eol!=-1:
			next_item_match = RE_LIST_ITEM.search(
				context.currentFragment(), next_eol)
		else:
			next_item_match = None

		# We assign to current_item_text the text of the current item
		current_item_text = context.currentFragment()
		if next_item_match:
			current_item_text = current_item_text[:next_item_match.start()]

		# We get the list item identation
		indent = context.parser.getIndentation(
			context.parser.charactersToSpaces(itemMatch.group(1)))
		
		# We look for the optional list heading
		heading = RE_LIST_ITEM_HEADING.match(current_item_text)
		heading_offset = 0
		list_type   = STANDARD_LIST
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
			
		# The current_item_text is no longer used in the following code

		# Step 2: Now that we have the item body, and that we know if there is
		# a next item (next_item_match), we can create the list item node. To
		# do so, we first have to look for a parent "List" node in which the
		# "ListItem" node we wish to create will be inserted.

		# We want either a "List" with a LOWER OR EQUAL indent, or a "ListItem"
		# with a STRICLY LOWER indentation, or a node which is neither a List
		# or a ListItem.
		while context.currentNode.nodeName == "List" and \
		int(context.currentNode.getAttributeNS(None, "_indent"))>indent or \
		context.currentNode.nodeName == "ListItem" and \
		int(context.currentNode.getAttributeNS(None, "_indent"))>=indent:
			context.currentNode = context.currentNode.parentNode

		# If the current node is a list, then we have to create a nested list.
		# A List ALWAYS have at least one child ListItem. If the last ListItem
		# has the same indentation as our current list item, then it is a
		# sibling, otherwise it is a parent.
		if context.currentNode.nodeName == "List":
			# A List should always have a least one ListItem
			items = context._getElementsByTagName( context.currentNode, "ListItem")
			assert len(items)>0
			if int(items[-1].getAttributeNS(None, "_indent")) < indent:
				context.currentNode = items[-1]

		# We may need to create a new "List" node to hold our list items
		list_node = context.currentNode
		# If the current node is not a list, then we must create a new list
		if context.currentNode.nodeName != "List":
			list_node = context.document.createElementNS(None, "List")
			list_node.setAttributeNS(None, "_indent", str(indent))
			context.currentNode.appendChild(list_node)
			context.currentNode = list_node

		# We create the list item
		list_item_node = context.document.createElementNS(None, "ListItem")
		list_item_node.setAttributeNS(None, "_indent", str(indent))
		# and the optional heading
		if heading:
			offsets = context.saveOffsets()
			heading_node = context.document.createElementNS(None, "heading")
			context.setCurrentBlock(context.getOffset(), context.getOffset()+heading_end)
			context.parser.parseBlock(context, heading_node, self.processText)
			# heading_text = context.document.createTextNode(heading)
			# heading_node.appendChild(heading_text)
			list_item_node.appendChild(heading_node)
			context.restoreOffsets(offsets)
		# and the content
		offsets = context.saveOffsets()
		if next_item_match:
			context.setCurrentBlock(heading_offset+context.getOffset() ,
				context.getOffset()+next_item_match.start())
		else:
			context.increaseOffset(heading_offset)
		# We parse the content of the list item
		old_node = context.currentNode
		# FIXME: This is necessary to assign the current node, but I do not
		# quite understand why... this needs some code review.
		context.currentNode = list_item_node
		context.parser.parseBlock(context, list_item_node, self.processText)
		context.currentNode = old_node
		context.restoreOffsets(offsets)
		# We eventually append the created list item node to the parent list
		# node
		list_node.appendChild(list_item_node)
		# We set the type attribute of the list if necesseary
		if list_type == DEFINITION_LIST:
			list_node.setAttributeNS(None, "type", "definition")

		# And recurse with other line items
		if next_item_match:
			# We set the offset in which the next_item Match object was
			# created, because match object start and end are relative
			# to the context offset at pattern matching time.
			list_item_node = self.process(context, next_item_match)
		# Or we have reached the block end
		else:
			context.setOffset(context.blockEndOffset)

		# We set the current node to be the list item node
		context.currentNode = list_item_node
		return list_item_node

	def processText( self, context, text ):
		text = context.parser.expandTabs(text)
		text = context.parser.normaliseText(text)
		return text

#------------------------------------------------------------------------------
#
#  PreBlockParser
#
#------------------------------------------------------------------------------

class PreBlockParser( BlockParser ):
	"""Parses the content of a preformatted block"""

	def __init__( self ):
		BlockParser.__init__(self, "pre")

	def recognises( self, context ):
		for line in context.currentFragment().split("\n"):
			if line and not RE_PREFORMATTED.match(line):
				return False
		return True
		
	def process( self, context, recogniseInfo ):
		text = ""
		for line in context.currentFragment().split("\n"):
			match = RE_PREFORMATTED.match(line)
			if match:
				text += match.group(2) + "\n"
			else:
				text += line + "\n"
		if text[-1] == "\n": text = text[:-1]
		pre_node = context.document.createElementNS(None, self.name)
		pre_node.appendChild(context.document.createTextNode(text))
		context.currentNode.appendChild(pre_node)


#------------------------------------------------------------------------------
#
#  TableBlockParser
#
#------------------------------------------------------------------------------

class Table:
	"""The table class allows to easily create tables and then generate the
	XML objects from them."""
	
	def __init__( self ):
		# Table is an array of array of (char, string) where char is either
		# 'H' for header, or 'T' for text.
		self._table = []
	
	def _ensureCell( self, x, y ):
		"""Ensures that the cell at the given position exists and returns its
		pair value."""
		while y >= len(self._table): self._table.append([])
		row = self._table[y]
		while x >= len(row): row.append(["T", None])
		return row[x]
		
	def appendCellContent( self, x, y, text ):
		cell_type, cell_text = self._ensureCell(x,y)
		if not text: return
		if cell_text == None:
			self._table[y][x] = [cell_type, text]
		else:
			self._table[y][x] = [cell_type, cell_text + " " + text]
	
	def headerCell( self, x, y ):
		self._table[y][x] = ["H", self._ensureCell(x,y)[1]]
		
	def dataCell( self, x, y ):
		self._table[y][x] = ["T", self._ensureCell(x,y)[1]]
	
	def isHeader( self, x, y ):
		if len(self._table) < y or len(self._table[y]) < x: return False
		return self._table[y][x][0] == "H"
	
	def getNode( self, context, processText ):
		table_node = context.document.createElementNS(None, "Table")
		for row in self._table:
			row_node = context.document.createElementNS(None, "Row")
			for cell_type, cell_text in row:
				cell_node = context.document.createElementNS(None, "Cell")
				if cell_type == "H":
					cell_node.setAttributeNS(None, "type", "header")
				new_context = context.clone()
				new_context.setDocumentText(cell_text)
				new_context.setCurrentBlock(0,0)
				new_context.parser.parseBlock(new_context, cell_node, processText)
				row_node.appendChild(cell_node)
			table_node.appendChild(row_node)
		return table_node
				
class TableBlockParser( BlockParser ):
	"""Parses the content of a tables"""

	def __init__( self ):
		BlockParser.__init__(self, "table")

	def recognises( self, context ):
		lines = context.currentFragment().strip().split("\n")
		return RE_TABLE_SEPARATOR.match(lines[0]) \
		and RE_TABLE_SEPARATOR.match(lines[-1])

	def process( self, context, recogniseInfo ):
		y = 0
		table = Table()
		# For each cell in a row
		# The cells are separated by piped (||)
		for row in context.currentFragment().strip().split("\n")[1:-1]:
			x = 0
			# The separator variable indicates wether we encountered a
			# separator during the parsing of the line. If it is not the
			# case, then the row spans more than one line.
			separator = False
			# Empty rows are simply ignored
			if not row.strip(): continue
			# Otherwise we split the cells in the row
			for cell in map(string.strip, row.split("||")):
				# We remove leading or trailing borders (|)
				if cell and cell[0]  == "|": cell = cell[1:]
				if cell and cell[-1] == "|": cell = cell[:-1]
				cell = cell.strip()
				# Is the cell a separation ?
				if RE_TABLE_SEPARATOR.match(cell):
					# If the previous cell was a header
					if cell[0] == "=":
						table.headerCell(x, y)
					else:
						table.dataCell(x, y)
					separator = True
				# Otherwise the cell is data
				else:
					table.appendCellContent(x,y,cell)
					# The default cell type is the same as the above
					# cell, if any.
					if y>0 and table.isHeader(x,y-1):
						table.headerCell(x,y)
				x += 1
			# If there was at least one separator, then we are on a new
			# row
			if separator: y+=1
		context.currentNode.appendChild(table.getNode(context, self. processText))
		
#------------------------------------------------------------------------------
#
#  MetaBlockParser
#
#------------------------------------------------------------------------------


class MetaBlockParser( BlockParser ):
	"""Parses the content of a Meta block"""

	def __init__( self ):
		BlockParser.__init__(self, "Meta")
		#This is a binding from meta block section names to meta content
		#parsers
		self.field_parsers = {
			u'abstract':		self.p_abstract,
			u'acknowledgements':	self.p_ack,
			u'author':		self.p_author,
			u'authors':		self.p_author,
			u'creation':		self.p_creation,
			u'keywords':		self.p_keywords,
			u'language':		self.p_language,
			u'last-mod':		self.p_last_mod,
			u'markup':		self.p_markup,
			u'organisation':	self.p_organisation,
			u'organization':	self.p_organisation,
			u'revision':		self.p_revision,
			u'type':		self.p_type,
			u'reference':		self.p_reference
		}

	def process( self, context, recogniseInfo ):
		# Parses a particular field, with the given content
		def parse_field( field ):
			field = field.lower()
			if self.field_parsers.get(field):
				self.field_parsers.get(field)(context, context.currentFragment())
			else:
				context.parser.warning("Unknown Meta field: " + last_field,
				context)

		match  = True
		offset = 0
		last_field = None
		# Iterates through the fields
		while match != None:
			match = RE_META_FIELD.search(context.currentFragment(), offset)
			if match:
				if last_field != None:
					offsets = context.saveOffsets()
					# We set the current fragment to be the field value
					context.setCurrentBlock( context.getOffset() + offset,
					context.getOffset() + match.start() )
					parse_field(last_field)
					context.restoreOffsets(offsets)
				last_field = match.group(2)
				offset = match.end()

		# And parse the last field
		if last_field != None:
			offsets = context.saveOffsets()
			context.setCurrentBlock( context.getOffset() + offset,
			context.blockEndOffset )
			parse_field(last_field)
			context.restoreOffsets(offsets)
		else:
			context.parser.warning("Empty Meta block.", context)

	# Field parsers __________________________________________________________

	def p_abstract( self, context, content ):
		old_node = context.currentNode 
		abstract_node = context.document.createElementNS(None, "Abstract")
		context.currentNode = abstract_node
		context.parser.parseBlock(context, abstract_node, self.processText)
		context.currentNode  = old_node
		context.header.appendChild(abstract_node)

	def p_ack( self, context, content ):
		old_node = context.currentNode 
		ack_node = context.document.createElementNS(None, "Acknowledgement")
		context.currentNode = ack_node
		context.parser.parseBlock(context, ack_node, self.processText)
		context.currentNode  = old_node
		context.header.appendChild(ack_node)

	def p_author( self, context, content ):
		authors_node = context.document.createElementNS(None, "Authors")
		text = self._flatify(content).strip()
		# Cuts the trailing dot if present
		if text[-1]==u'.': text=text[:-1]
		for author in text.split(','):
			author_node = context.document.createElementNS(None, "person")
			# We take care of email
			email_match = RE_META_AUTHOR_EMAIL.search(author)
			if email_match:
				author = author[:email_match.start()]
				author_node.setAttributeNS(None, "email", email_match.group(1))
			text_node   = context.document.createTextNode(author.strip())
			author_node.appendChild(text_node)
			authors_node.appendChild(author_node)
		context.header.appendChild(authors_node)
	
	def p_creation( self, context, content ):
		creation_node = context.document.createElementNS(None, "creation")
		if self._parseDateToNode( context, content, creation_node ):
			context.header.appendChild(creation_node)
	
	def _parseDateToNode( self, context, content, node ):
		content = content.strip()
		date = content.split("-")
		for elem in date:
			format = None
			try:
				format = "%0" + str(len(elem)) + "d"
				format = format % (int(elem))
			except:
				pass
			if len(date)!=3 or format != elem:
				context.parser.error("Malformed date meta field: " + content,
				context)
				context.parser.tip("Should be YYYY-MM-DD", context)
				return False
		date = map(lambda x:int(x), date)
		if date[1] < 1 or date[1] > 12:
			context.parser.warning("Bad month number: " + str(date[1]),
			context)
		if date[2] < 1 or date[2] > 31:
			context.parser.warning("Bad day number: " + str(date[2]),
			context)
		node.setAttributeNS(None, "year",  str(date[0]))
		node.setAttributeNS(None, "month", str(date[1]))
		node.setAttributeNS(None, "day",   str(date[2]))
		return True

	def p_keywords( self, context, content ):
		keywords_node = context.document.createElementNS(None, "Keywords")
		text = self._flatify(content).strip()
		# Cuts the trailing dot if present
		if text[-1]==u'.': text=text[:-1]
		for keyword in text.split(','):
			keyword_node = context.document.createElementNS(None, "keyword")
			text_node   = context.document.createTextNode(keyword.strip())
			keyword_node.appendChild(text_node)
			keywords_node.appendChild(keyword_node)
		context.header.appendChild(keywords_node)

	def p_last_mod( self, context, content ):
		lastmod_node = context.document.createElementNS(None, "modification")
		if self._parseDateToNode( context, content, lastmod_node ):
			context.header.appendChild(lastmod_node)

	def p_revision( self, context, content ):
		revision_node = context.document.createElementNS(None, "revision")
		text_node   = context.document.createTextNode(content.strip())
		revision_node.appendChild(text_node)
		context.header.appendChild(revision_node)

	def p_type( self, context, content ):
		match = RE_META_TYPE.match(content)
		if match:
			style_node = context.document.createElementNS(None, "type")
			style_node.setAttributeNS(None, "name", match.group(1).lower())
			if match.group(3):
				style_node.setAttributeNS(None, "style", match.group(3).lower())
			context.header.appendChild(style_node)
		else:
			context.parser.warning("Malformed meta type field: " + content,
			context)

	def p_reference( self, context, content ):
		ref_node = context.document.createElementNS(None, "reference")
		ref_node.setAttributeNS(None, "id", content)
		context.header.appendChild(ref_node)

	def p_language( self, context, content ):
		lang = content.strip()[0:2].upper()
		lang_node = context.document.createElementNS(None, "language")
		#We assign the language code
		if len(lang)>=2 and lang.upper()[0:2] in LANGUAGE_CODES:
			lang_code = unicode(lang.upper()[0:2])
		else:
			lang_code = "UK"
		lang_node.setAttributeNS(None, "code", lang_code)
		context.header.appendChild(lang_node)

	def p_organisation( self, context, content ):
		old_node = context.currentNode 
		org_node = context.document.createElementNS(None, "Organisation")
		context.currentNode = org_node
		context.parser.parseBlock(context, org_node, self.processText)
		context.currentNode  = old_node
		context.header.appendChild(org_node)

	def p_markup( self, context, content ):
		"""Parses custom markup and registers the new parsers in the current
		Kiwi parser"""
		# TODO
		match = 1
		start = 0
		end   = len(content)
		custom_markup = RE_CUSTOM_MARKUP
		while match!=None and start<end:
			match = custom_markup.search(content,start)
			if match:
				regexp  = match.group(1)
				element = match.group(2)
				option  = match.group(4)
				if option == None:
					self.parser.txt_parsers.append(InlineParser(self.parser,
					element, regexp))
				elif option.lower() == u"empty":
					self.parser.txt_parsers.append(EmptyInlineParser(self.parser,
					element, regexp))
				else:
					#FIXME: OUTPUT ERROR FOR UNKNOWN OPTION
					pass
				start = match.end()

	def _flatify( self, text ):
		new_text = u""
		for line in text.split(): new_text += line+u" "
		return new_text

	def processText( self, context, text ):
		assert text
		text = context.parser.expandTabs(text)
		text =  context.parser.normaliseText(text)
		return text

#------------------------------------------------------------------------------
#
#  BibliographicEntryBlockParser
#
#------------------------------------------------------------------------------


class BibliographicEntryBlockParser( BlockParser ):
	"""Parses the content of a Bibliographic entries"""

	def __init__( self ):
		BlockParser.__init__(self, "Entry")

	def recognises( self, context ):
		assert context
		return RE_BIBLIOGRAPHIC_ENTRY.match(context.currentFragment())

	def process( self, context, match ):
		entry_name = match.group(1)
		entry = context.currentFragment()[match.end():]
		attributes = context.parseAttributes(entry)
		entry_node = context.document.createElementNS(None, "Entry")
		entry_node.setAttributeNS(None, "id", entry_name)
		for key, value in attributes.items():
			if key.lower() == "type": value = value.lower()
			entry_node.setAttributeNS(None, key.lower(), value)
		context.references.appendChild(entry_node)
		
# EOF-Linux/ASCII-----------------------------------@RisingSun//Python//1.0//EN
