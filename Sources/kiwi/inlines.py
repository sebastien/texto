#!/usr/bin/env python
# Encoding: iso-8859-1
# -----------------------------------------------------------------------------
# Project           :   Kiwi
# Module            :   Inline parsers
# -----------------------------------------------------------------------------
# Author            :   Sebastien Pierre (SPE)           <sebastien@type-z.org>
# -----------------------------------------------------------------------------
# Creation date     :   19-Nov-2003
# Last mod.         :   05-Oct-2004
# History           :
#                       26-Dec-2004 Changed quotes syntax, added footnote (SPE)
#                       05-Oct-2004 Completed inline parsers (SPE)
#                       29-Sep-2004 Attributes parsing. (SPE)
#                       27-Sep-2004 Added support for custom markup, acronyms,
#                       citations (SPE)
#                       01-Apr-2004 Implemented reference parser
#                       31-Mar-2004 Fixed bug in escaped recognition.
#                       20-Jan-2004 MarkupParser recognises blocks properly
#                       (SPE)
#                       19-Jan-2004 Working on MarkupParser, added InlineParser
#                       `endOf' method (SPE)
#                       13-Jan-2004 Added EscapedParser, improved
#                       MarkupParser (SPE)
#                       07-Jan-2004 Added support for 4DOM (SPE)
#                       15-Dec-2003 Added preliminary comment node (SPE)
#                       23-Nov-2003 Added MarkupInlineParser (SPE)
#                       19-Nov-2003 First implementation (SPE)
#
# Bugs              :
#                       - Attributes in acronyms, citations and quotes should
#                         be normalised
# To do             :
#                       -
#

import re

__doc__ = """Write module doc here"""
__pychecker__ = "unusednames=y"

#------------------------------------------------------------------------------
#
#  Error messages
#
#------------------------------------------------------------------------------

END_WITHOUT_START = "Markup `%s' end found without previous markup start"
START_WITHOUT_END = "Markup `%s' start found without following markup end"
MUST_BE_START_OR_END = \
"Unrecognised markup specifier: 'start' or 'end' would be expected"

#------------------------------------------------------------------------------
#
#  Regular expressions
#
#------------------------------------------------------------------------------

#The regular expressions listed below are ordered conforming to their order
#of insertion into the parser.

# Kiwi core

COMMENT    = u"^\s*#.*$"
RE_COMMENT = re.compile(COMMENT, re.LOCALE | re.MULTILINE )

ESCAPED_START    = u"{\|"
RE_ESCAPED_START = re.compile(ESCAPED_START, re.LOCALE)
ESCAPED_END      = u"\|}"
RE_ESCAPED_END   = re.compile(ESCAPED_END, re.LOCALE)
ESCAPED_REPLACE  = u"\}"
RE_ESCAPED_REPLACE=re.compile(ESCAPED_REPLACE, re.LOCALE)

# Text style

LITTERAL         = u"`"
RE_LITTERAL      = re.compile(LITTERAL, re.LOCALE)
LITTERAL_REPLACE = u"\`"
RE_LITTERAL_REPLACE = re.compile(LITTERAL_REPLACE, re.LOCALE)
CODE     = u"`([^\']+)'"
RE_CODE  = re.compile(CODE, re.LOCALE|re.MULTILINE)
STRONG   = u"\*\*([^*]+)\*\*"
RE_STRONG= re.compile(STRONG, re.LOCALE|re.MULTILINE)
EMPHASIS = u"\*([^*]+)\*"
RE_EMPHASIS= re.compile(EMPHASIS, re.LOCALE|re.MULTILINE)
QUOTED    = u"''(.+)''"
RE_QUOTED = re.compile(QUOTED, re.LOCALE|re.MULTILINE)

# Special Characters

BREAK    = u"\s*\n\s*\|\s*\n()"
RE_BREAK= re.compile(BREAK)
NEWLINE  = u"\s*\\\\n\s*()"
RE_NEWLINE= re.compile(NEWLINE)
LONGDASH = u" -- ()"
RE_LONGDASH= re.compile(LONGDASH)
ARROW    = u"<-+>|-+->|<-+"
RE_ARROW = re.compile(ARROW,)
DOTS     = u" \.\.\.()"
RE_DOTS  = re.compile(DOTS,)

# Keywords and acronyms

ACRONYM  = u"_([^_]+)_(\s*\(:([^:)]+)(:([^)]+))?\))?"
RE_ACRONYM = re.compile(ACRONYM,re.LOCALE|re.MULTILINE)

KEYWORD  = u"!([^!]+)!"
RE_KEYWORD = re.compile(KEYWORD,re.LOCALE|re.MULTILINE)

TERM     = u"'\w+'|\|[^\|]+\|"
RE_TERM  = re.compile(TERM,re.LOCALE|re.MULTILINE)

CF  = ":([^:)]*)" ; OCF = "(:([^:)]*))?" ; ECF = "(:([^)]+))?"

CITATION = u"\>\>((\<[^<]|[^<])+)\<\<(\s*\(:([^:)]*)(:([^)]+))?\))?"
RE_CITATION = re.compile(CITATION,re.LOCALE|re.MULTILINE)

QUOTE = u"\<\<((\>[^>]|[^>])+)\>\>(\s*\(" + CF + OCF + OCF + ECF + "\))?"
RE_QUOTE = re.compile(QUOTE,re.LOCALE|re.MULTILINE)

DOCUMENT = u"``(('[^']|[^'])+)''(\s*\(" + CF + OCF + ECF + "\))?"
RE_DOCUMENT = re.compile(DOCUMENT,re.LOCALE|re.MULTILINE)

FOOTNOTE = u"\s*\.\.\(((\.[^\.]|[^\.])+)\)\.\."
RE_FOOTNOTE =  re.compile(FOOTNOTE,re.LOCALE|re.MULTILINE)


# Linking content

EMAIL    = u"\<([\w.\-_]+@[\w.\-_]+)\>"
RE_EMAIL = re.compile(EMAIL, re.LOCALE|re.MULTILINE)
URL      = u"\<([A-z]+://[^\>]+)\>"
RE_URL   = re.compile(URL, re.LOCALE|re.MULTILINE)

TAG       = u"{([\w_-]+)}"
RE_TAG    = re.compile(TAG, re.LOCALE|re.MULTILINE)

REFERENCE = u"\{([#$][\w_-]+|\<[A-z]+:/[^\>]+\>)\s*[:,;]([^\}]+)\}"
#FIXME: I came up with the following alternative
#REFERENCE    = u"{(#\w+|$\w+|<[^>]+>):[^}]+}"
RE_REFERENCE = re.compile(REFERENCE, re.LOCALE|re.MULTILINE)


# Custom markup

MARKUP   = u"\[([a-zA-Z]\w*)(\s*\w+)?\s*(:\s*([^\]]*))?\]"
RE_MARKUP= re.compile(MARKUP, re.LOCALE|re.MULTILINE)

# Specific elements

TARGET    = u"\[>\s*([^\]]+)\]"
RE_TARGET = re.compile(TARGET, re.LOCALE|re.MULTILINE)

INCLUDE_RAW = u"\[\s*#\s*:([^\]]+)\]"
RE_INCLUDE_RAW = re.compile(INCLUDE_RAW,re.LOCALE|re.MULTILINE)

START_TAGS = [u"start", u"debut", u"s"]
END_TAGS = [u"end", u"fin", u"e"]

#------------------------------------------------------------------------------
#
#  InlineParser
#
#------------------------------------------------------------------------------

class InlineParser:

	def __init__( self, name, regexp, result=lambda x,y: x.group(1) ):
		"""Creates a new InlineParser.

		Name is the name of the parser, *regexp* is the string expression
		of the regular expression that will match the element that the
		InlineParser is looking for, or regexp can also be a precompiled
		regular expression object.

		Result is a lambda expression that will return the content of the
		Inline generated by the *parse* method. The lambda takes two
		arguments : the match object and the string in which the match object
		has been found."""
		self.name   = name
		#Checks if regexp is a string or a precompiled regular expression
		if type(regexp) in (type(u""), type("")):
			self.regexp = re.compile(regexp, re.LOCALE|re.MULTILINE)
		else:
			self.regexp = regexp
		self.result = result

	def recognises( self, context ):
		"""Recognises this inlines in the given context, within the current
		context block. It returns (None, None) when the inline was not recognised,
		otherwise it returns the offset of the matching element in the current
		context, plus information that will be given as argument to the parse
		method. This means that the returned offset is RELATIVE TO THE CURRENT
		CONTEXT OFFSET."""
		match = self.regexp.search(context.currentFragment())
		if match:
			return (match.start(), match)
		else:
			return (None, None)

	def endOf( self, recogniseInfo ):
		"""Returns the end of this inline using the given recogniseInfo."""
		return recogniseInfo.end()

	def parse( self, context, node, recogniseInfo  ):
		"""Parses the given context within the current block range, returning
		the new offset (relative to the block start offset, ie. the start of
		context.currentFragment). Note that the context offsets are the same
		as those given to the recognise method call which created
		recogniseInfo.

		The given context starts at the same offset as when recognises was
		called. Modifications are made to the given node."""
		match = recogniseInfo
		assert match!=None
		inline_node = context.document.createElementNS(None, self.name)
		text = self.result(match, context.documentText)
		if text:
			text_node   = context.document.createTextNode(text)
			inline_node.appendChild(text_node)
		node.appendChild(inline_node)
		return self.endOf(recogniseInfo)

#------------------------------------------------------------------------------
#
#  Arrow parsers
#
#------------------------------------------------------------------------------

class ArrowInlineParser( InlineParser ):

	def __init__( self ):
		InlineParser.__init__( self, "arrow", RE_ARROW )

	def parse( self, context, node, match ):
		assert match
		text = match.group()
		arrow_type = None
		if text[0] == "<":
			if text[-1] == ">": arrow_type = "double"
			else: arrow_type = "left"
		else:
			arrow_type = "right"
		arrow_node = context.document.createElementNS(None, "arrow")
		arrow_node.setAttributeNS(None, "type", arrow_type)
		node.appendChild(arrow_node)
		return match.end()

#------------------------------------------------------------------------------
#
#  CommentInlineParser
#
#------------------------------------------------------------------------------

class CommentInlineParser( InlineParser ):

	def __init__( self ):
		InlineParser.__init__( self, "comment", RE_COMMENT )

	def processText( self, text ):
		new_text = ""
		for line in text.split("\n"):
			line = line.strip()
			if len(line)>1:
				line = line[1:]
				new_text += line + "\n"
		if new_text: new_text = new_text[:-1]
		new_text = " "+new_text+" "
		return new_text

	def parse( self, context, node, recogniseInfo ):
		match = recogniseInfo
		assert match!=None
		node.appendChild(context.document.createComment(
			self.processText(match.group())))
		return match.end()

#------------------------------------------------------------------------------
#
#  Escape inline parser
#
#------------------------------------------------------------------------------

class EscapedInlineParser( InlineParser ):

	def __init__( self ):
		InlineParser.__init__( self, "escaped", None )

	def recognises( self, context ):
		start_match = RE_ESCAPED_START.search(context.currentFragment())
		if start_match:
			# And search the escape starting from the end of the escaped
			end_match = RE_ESCAPED_END.search(
				context.currentFragment(), start_match.end())
			if end_match:
				return (start_match.start(), (start_match, end_match))
			else:
				return (None, None)
		return (None, None)

	def endOf( self, recogniseInfo ):
		return recogniseInfo[1].end()

	def parse( self, context, node, recogniseInfo  ):
		# We get start and end match, end being relative to the start
		start_match, end_match = recogniseInfo
		assert start_match!=None and end_match!=None

		# Create a text node with the escaped text
		escaped_node = context.document.createTextNode(
			context.currentFragment()[start_match.end():end_match.start()])
		node.appendChild(escaped_node)
		# And increase the offset
		return self.endOf(recogniseInfo)

#------------------------------------------------------------------------------
#
#  Tag inline parser
#
#------------------------------------------------------------------------------

class TagInlineParser( InlineParser ):
	"""A tag is the equivalent of an anchor in HTML, it is used to be
	references later."""

	def __init__( self ):
		InlineParser.__init__( self, "tag", RE_TAG )

	def parse( self, context, node, recogniseInfo  ):
		match = recogniseInfo
		assert match!=None
		if node.getAttributeNS(None, "tag"):
			context.parser.warning("Duplicate tag for block element: " +
			match.group(1), context)
		node.setAttributeNS(None, "tag", match.group(1))
		return self.endOf(recogniseInfo)

#------------------------------------------------------------------------------
#
#  Reference identifier
#
#------------------------------------------------------------------------------

def identifyReference( reference, node ):
	"""Identifies a reference from the given string, resuling from a
	RE_REFERENCE match, sets the type and target attributes of the given
	node to the proper value and return the value of the type attribute."""
	# It is an internal reference
	if reference[0] == "#":
		node.setAttributeNS(None, u"type", "internal")
		node.setAttributeNS(None, u"target", reference[1:])
		return "internal"
	# It is a bibliographic
	elif reference[0] == "$":
		node.setAttributeNS(None, u"type", "bibliographic")
		node.setAttributeNS(None, u"target", reference[1:])
		return "bibliographic"
	# Otherwise it is an URI
	else:
		assert reference[0] == "<"
		node.setAttributeNS(None, u"type", "uri")
		node.setAttributeNS(None, u"target", reference[1:-1])
		return "uri"

#------------------------------------------------------------------------------
#
#  Acronym inline parser
#
#------------------------------------------------------------------------------

def _processText( text, context ):
	"""Common operation for expanding tabs and normalising text. Use by
	acronyms, citations and quotes."""
	if not text: return text
	text = context.parser.expandTabs(text)
	text = context.parser.normaliseText(text)
	return text

class AcronymInlineParser( InlineParser ):

	def __init__( self ):
		InlineParser.__init__( self, "acronym", RE_ACRONYM )

	def parse( self, context, node, match  ):

		acronym     = _processText(match.group(1), context)
		description = _processText(match.group(3), context)
		links       = _processText(match.group(4), context)

		# In case the acronym is a reverse acronym...
		if description and (acronym.split(" ")) > 1 and len(description.split(" ")) == 1:
			temp = acronym
			acronym = description
			description = temp

		# We create the text node
		acr_node = context.document.createElementNS(None, self.name)
		acr_node.appendChild(
			context.document.createTextNode(acronym.upper().strip()))
		# Add the attributes if necessary
		if description:
			acr_node.setAttributeNS(None, "description", description.strip())
		if links:
			# We skip the first character (always a colon)
			identifyReference(links[1:], acr_node)

		# And append it
		node.appendChild(acr_node)

		# And increase the offset
		return self.endOf(match)

#------------------------------------------------------------------------------
#
#  Citation inline parser
#
#------------------------------------------------------------------------------

class CitationInlineParser( InlineParser ):

	def __init__( self ):
		InlineParser.__init__( self, "citation", RE_CITATION )

	def parse( self, context, node, match  ):
		assert match
		citation     = _processText(match.group(1), context)
		authors      = _processText(match.group(4), context)
		links        = _processText(match.group(5), context)
		# We create the text node
		cit_node = context.document.createElementNS(None, self.name)
		cit_node.appendChild(context.document.createTextNode(citation.strip()))
		# Add the authors, if any
		if authors:
			cit_node.setAttributeNS(None, "authors", authors.strip())
		if links:
			# We skip the first character (always a colon)
			identifyReference(links[1:], cit_node)
		# And append it
		node.appendChild(cit_node)
		# And increase the offset
		return self.endOf(match)

#------------------------------------------------------------------------------
#
#  Quote inline parser
#
#------------------------------------------------------------------------------

class QuoteInlineParser( InlineParser ):

	def __init__( self ):
		InlineParser.__init__( self, "quote", RE_QUOTE )

	def parse( self, context, node, match  ):
		assert match
		quote     = _processText(match.group(1), context)
		title     = _processText(match.group(4), context)
		authors   = _processText(match.group(6), context)
		year      = _processText(match.group(8), context)
		links     = _processText(match.group(10), context)

		# We create the text node
		quote_node = context.document.createElementNS(None, self.name)
		quote_node.appendChild(context.document.createTextNode(quote.strip()))

		if title: quote_node.setAttributeNS(None, "title", title.strip())
		if authors: quote_node.setAttributeNS(None, "authors", authors.strip())
		if year: quote_node.setAttributeNS(None, "year", year.strip())
		if links: identifyReference(links, quote_node)

		# And append it
		node.appendChild(quote_node)
		# And increase the offset
		return self.endOf(match)

#------------------------------------------------------------------------------
#
#  Document inline parser
#
#------------------------------------------------------------------------------

class DocumentInlineParser( InlineParser ):

	def __init__( self ):
		InlineParser.__init__( self, "document", RE_DOCUMENT )

	def parse( self, context, node, match  ):
		assert match
		document = _processText(match.group(1), context)
		type     = _processText(match.group(4), context)
		comment  = _processText(match.group(6), context)
		year     = _processText(match.group(8), context)

		# We create the text node
		doc_node = context.document.createElementNS(None, self.name)
		doc_node.appendChild(context.document.createTextNode(document.strip()))

		if type:    doc_node.setAttributeNS(None, "type", type.strip().lower())
		if comment: doc_node.setAttributeNS(None, "comment", comment.strip())
		if year:    doc_node.setAttributeNS(None, "year", year.strip())

		# And append it
		node.appendChild(doc_node)
		# And increase the offset
		return self.endOf(match)

#------------------------------------------------------------------------------
#
#  Footnote inline parser
#
#------------------------------------------------------------------------------

class FootnoteInlineParser( InlineParser ):

	def __init__( self ):
		InlineParser.__init__( self, "footnote", RE_FOOTNOTE )

	def parse( self, context, node, match  ):
		assert match
		content  = _processText(match.group(1), context)

		# We create the text node
		note_node = context.document.createElementNS(None, self.name)
		note_node.appendChild(context.document.createTextNode(content.strip()))

		# And append it
		node.appendChild(note_node)
		# And increase the offset
		return self.endOf(match)
		
#------------------------------------------------------------------------------
#
#  Reference inline parser
#
#------------------------------------------------------------------------------

class ReferenceInlineParser( InlineParser ):
	"""A reference refers to a tag, a bibliographic entry, or an URI."""

	def __init__( self ):
		InlineParser.__init__( self, "reference", RE_REFERENCE )

	def parse( self, context, node, recogniseInfo  ):
		match = recogniseInfo
		assert match!=None
		# Creates the node and assign the type and target attribute
		refnode = context.document.createElementNS(None, self.name)
		reftype = identifyReference(match.group(1), refnode)
		# Then we set the content of the node
		if reftype == "uri":
			refnode.appendChild(context.document.createTextNode(match.group(2)))
		else:
			self._createContent(context, refnode, match.group(2))
		node.appendChild(refnode)
		return self.endOf(recogniseInfo)

	def _createContent( self, context, node, text ):
		"""Creates child nodes and appends them to the given node, where occurences
		of `p#' and `#' in text are replaced by pageNumber and number elements
		in the child nodes, while other characters are appended as text nodes."""
		offset = 0
		while offset < len(text):
			pnum = text.find("p#", offset)
			num  = text.find("#",  offset)
			if ( pnum < num or num<0 ) and pnum>=0:
				if pnum>0:
					node.appendChild(context.document.createTextNode(
					text[offset:pnum]))
				node.appendChild(context.document.createElementNS(None, "pageNumber"))
				offset = pnum + len("p#")
			elif ( num < pnum or pnum<0 ) and num>=0:
				if num>0:
					node.appendChild(context.document.createTextNode(
					text[offset:num]))
				node.appendChild(context.document.createElementNS(None, "number"))
				offset = num + len("#")
			else:
				node.appendChild(context.document.createTextNode(
					text[offset:]))
				offset = len(text)

#------------------------------------------------------------------------------
#
#  MarkupInlineParser
#
#------------------------------------------------------------------------------

class MarkupInlineParser( InlineParser ):
	"""Parses Kiwi generic markup elements."""

	def __init__( self ):
		InlineParser.__init__(self, None, RE_MARKUP)
		self.START_TAGS = START_TAGS

	def parse( self, context, node, recogniseInfo  ):
		"""Parses the given tag, and returns the offset where the parsed tag
		ends. If the tag is an "inline block" tag, then its content is also
		parsed."""
		match = recogniseInfo
		# Is it an inline ?
		if match.group(2) == None:
			# TODO: Check if element name is recognised or not
			markup_node = context.document.createElementNS(None, match.group(1).strip())
			for key, value in context.parseAttributes(match.group(4)).items():
				markup_node.setAttributeNS(None, key, value)
			node.appendChild(markup_node)
			return match.end()
		# Or is it a block ?
		elif match.group(1) in START_TAGS:
			# We search for an end, taking care of setting the offset after the
			# recognised inline.
			markup_name  = match.group(2).strip()
			markup_range = self.findEnd( markup_name, context, match.end())
			if not markup_range:
				context.parser.error( START_WITHOUT_END % (markup_name), context )
				return match.end()
			else:
				# We do not want the context to be altered by block parsing
				offsets = context.saveOffsets()
				context.setCurrentBlock(context.getOffset()+match.end(),
					context.getOffset()+markup_range[0])
				# We check if there is a specific block parser for this markup
				custom_parser = context.parser.customParsers.get(markup_name)
				# Here we have found a custom parser, which is in charge for
				# creating nodes
				if custom_parser:
					custom_parser.process(context, None)
				# Otherwise we create the node for the markup and continue
				# parsing
				else:
					markup_node = context.document.createElementNS(None, markup_name)
					node.appendChild(markup_node)
					# FIXME: This should not be necessary
					old_node = context.currentNode
					context.currentNode = markup_node
					context.parser.parseBlock(context, markup_node, self.processText)
					context.currentNode = old_node
				context.restoreOffsets(offsets)
				return markup_range[1]
		elif match.group(1) in END_TAGS:
			context.parser.error( END_WITHOUT_START % (match.group(2).strip()),
			context )
			return match.end()
		else:
			context.parser.error( MUST_BE_START_OR_END, context )
			return match.end()

	def _searchMarkup( self, context ):
		"""Looks for the next markup inline in the current context. This also
		takes care of markups that are contained into an escaped text tag.

		WARNING : this operation mutates the context offsets, so this should
		always be enclosed in offset store and restore. The context offset is
		set BEFORE the searched markup, so that the returned recognition info
		is relative to the context offset.

		Returns the result of this parser `recognise' method, or null."""
		inline_parsers = ( context.parser.escapedParser, self )
		# We look for a block inline
		while not context.blockEndReached():
			result = context.findNextInline(inline_parsers)
			if result:
				if result[2] == self:
					return result[1]
				else:
					context.increaseOffset(result[2].endOf(result[1]))
			else:
				break
		return None

	def findEnd( self, blockName, context, offsetIncr=0 ):
		"""Finds the end of the given markup end in the current block. Returns
		a coupe (start, end) indicating the start and end offsets of the found
		end block, relative to the context offset. The given offsetInc
		parameter tells the number of characters to skip before searching for
		the end markup. This has no impact on the result.

		The context offsets are left unchanged."""
		depth = markup_match =  1
		block_name = None
		offsets = context.saveOffsets()
		original_offset = context.getOffset()
		context.increaseOffset(offsetIncr)
		# We look for start and end markups
		while depth>0 and markup_match and not context.blockEndReached():
			markup_match = self._searchMarkup(context)
			if markup_match:
				if markup_match.group(1).lower() in START_TAGS:
					depth += 1
				elif markup_match.group(1).lower() in END_TAGS:
					depth -= 1
					block_name = markup_match.group(2).strip()
				if depth > 0:
					context.increaseOffset(markup_match.end())
		# We have found at least one matching block
		end_markup_range = None
		if depth==0 and block_name and block_name==blockName:
			# The match is relative to the current context offset
			match_start = context.getOffset() - original_offset + markup_match.start()
			match_end   = context.getOffset() - original_offset + markup_match.end()
			end_markup_range = ( match_start, match_end )
		context.restoreOffsets(offsets)
		return end_markup_range

	def processText( self, context, text ):
		return context.parser.normaliseText(text)


# EOF-Linux/ASCII-----------------------------------@RisingSun//Python//1.0//EN
