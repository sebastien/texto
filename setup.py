#!/usr/bin/python
# Encoding: ISO-8859-1
# vim: tw=80 ts=4 sw=4 noet 
# -----------------------------------------------------------------------------
# Project           :   Kiwi
# -----------------------------------------------------------------------------
# Author            :   Sebastien Pierre                 <sebastien@type-z.org>
# License           :   Revised BSD License
# -----------------------------------------------------------------------------
# Creation date     :   07-Fev-2006
# Last mod.         :   17-Jul-2007
# -----------------------------------------------------------------------------

import sys
from distutils.core import setup

NAME        = "Kiwi"
VERSION     = "0.8.6"
WEBSITE     = "http://www.ivy.fr/" + NAME.lower()
SUMMARY     = "Intuitive, flexible structured text to markup processor"
DESCRIPTION = """\
Kiwi is a structured text (markup) to XML/HTML processor, designed with
embedding in mind. Very close in syntax to the Markdown markup, Kiwi however
supports more elements (including tables), and has a more advanced XML/HTML
integration.

When using Kiwi, you can still write XML or HTML tags within your text, and use
the markup syntax whenever you want. Kiwi is integrated into the Tahchee
<http://www.ivy.fr/tahchee> static web site build system.
"""

# ------------------------------------------------------------------------------
#
# SETUP DECLARATION
#
# ------------------------------------------------------------------------------

setup(
    name        = NAME,
    version     = VERSION,
    author      = "Sebastien Pierre", author_email = "sebastien@type-z.org",
    description = SUMMARY, long_description = DESCRIPTION,
    license     = "Revised BSD License",
    keywords    = "text translation, markup, markdown, web",
    url         =  WEBSITE,
    download_url=  WEBSITE + "/%s-%s.tar.gz" % (NAME.lower(), VERSION) ,
    package_dir = { "": "Sources" },
    package_data= { "kiwi": ["*.css"] },
    packages    = ["kiwi"],
    scripts     = ["Scripts/kiwi"],
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

# EOF
