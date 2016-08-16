#!/usr/bin/python
# Encoding: utf8
# -----------------------------------------------------------------------------
# Project           : Texto
# -----------------------------------------------------------------------------
# Author            : Sebastien Pierre             <sebastien.pierre@gmail.com>
# License           : Revised BSD License
# -----------------------------------------------------------------------------
# Creation date     : 07-Fev-2006
# Last mod.         : 16-Aug-2016
# -----------------------------------------------------------------------------

import sys
from   distutils.core import setup
sys.path.insert(0, "src") ; import texto

NAME        = "texto"
VERSION     = texto.__version__
WEBSITE     = "http://www.github.com/sebastien/texto"
SUMMARY     = "Intuitive, flexible structured text to markup processor"
DESCRIPTION = """\
Texto is a structured text (markup) to XML/HTML processor, designed with
embedding in mind. Very close in syntax to the Markdown markup, Texto
supports more elements and can be easily extended.
"""

# ------------------------------------------------------------------------------
#
# SETUP DECLARATION
#
# ------------------------------------------------------------------------------

setup(
	name        = NAME,
	version     = VERSION,
	author      = "Sébastien Pierre", author_email = "sebastien.pierre@gmail.com",
	description = SUMMARY, long_description = DESCRIPTION,
	license     = "Revised BSD License",
	keywords    = "text translation, markup, markdown, web",
	url         =  WEBSITE,
	download_url=  WEBSITE + "/%s-%s.tar.gz" % (NAME.lower(), VERSION) ,
	package_dir = { "": "src" },
	packages    = [
		"texto",
		"texto.formats",
		"texto.parser",
	],
	scripts     = ["bin/texto"],
	classifiers = [
	  "Development Status :: 4 - Beta",
	  "Environment :: Console",
	  "Intended Audience :: Developers",
	  "Intended Audience :: Information Technology",
	  "License :: OSI Approved :: BSD License",
	  "Natural Language :: English",
	  "Topic :: Documentation",
	  "Topic :: Software Development :: Documentation",
	  "Topic :: Text Processing",
	  "Topic :: Text Processing :: Markup",
	  "Topic :: Text Processing :: Markup :: HTML",
	  "Topic :: Text Processing :: Markup :: XML",
	  "Topic :: Utilities",
	  "Operating System :: POSIX",
	  "Operating System :: Microsoft :: Windows",
	  "Programming Language :: Python",
	]
)

# EOF - vim: tw=80 ts=4 sw=4 noet
