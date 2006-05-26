# Kiwi makefile
# ---------------
#
#
# Revision 1.5.0 (22-Feb-2006)
#
# Distributed under BSD License
# See www.type-z.org/copyleft.html
# (c) S�bastien Pierre - http://www.type-z.org, 2003 - 2006


# Project variables___________________________________________________________
#
# Project name. Do not put spaces.
PROJECT         = Kiwi
PROJECT_VERSION = 0.7.8
PROJECT_STATUS  = BETA

DOCUMENTATION   = Documentation
SOURCES         = Sources
TESTS           = Tests
RESOURCES       = Resources
DISTRIBUTION    = Distribution
API             = $(DOCUMENTATION)/API
DISTROCONTENT   = $(DOCUMENTATION) $(SOURCES) $(TESTS) $(RESOURCES) \
                  Makefile

# Project files_______________________________________________________________

PROJECT_MODULES = \
	kiwi \
	kiwi.core \
	kiwi.blocks \
	kiwi.inlines

TEST_MAIN       = $(TESTS)/KiwiTest.py
SOURCE_FILES    = $(shell find $(SOURCES) -name "*.py")
TEST_FILES      = $(shell find $(TESTS) -name "*.py")

# The name of the folder in the PARENT_MODULE folder that corresponds to the
# projet main module
MAIN_MODULE     = kiwi
# The name of the parent folder of the MAIN_MODULE folder. The parent folder is
# relative to the SOURCES folder.
PARENT_MODULE   = 
# The name of the main python file, relative to the MAIN_MODULE
PROJECT_MAIN    = kiwi.py

# Tools_______________________________________________________________________

PYTHON          = $(shell which python)
PYTHONHOME      = $(shell $(PYTHON) -c \
 "import sys;print filter(lambda x:x[-13:]=='site-packages',sys.path)[0]")
EPYDOC          = $(shell which epydoc)
PYCHECKER       = $(shell which pychecker)
CTAGS           = $(shell which ctags)

# Useful variables____________________________________________________________

CURRENT_ARCHIVE = $(PROJECT)-$(PROJECT_VERSION).tar.gz
# This is the project name as lower case, used in the install rule
project_lower   = $(shell echo $(PROJECT) | tr "A-Z" "a-z")
# The installation prefix, used in the install rule
prefix          = /usr/local

# Rules_______________________________________________________________________

.PHONY: help info preparing-pre clean check dist doc tags install uninstall todo

help:
	@echo
	@echo " $(PROJECT) make rules:"
	@echo
	@echo "    doc     - generates the documentation"
	@echo "    install - installs $(PROJECT)"
	@echo
	@echo "   For developers:"
	@echo
	@echo "    info    - displays project information"
	@echo "    prepare - prepares the project, may require editing this file"
	@echo "    clean   - cleans up build files"
	@echo "    check   - executes pychecker"
	@echo "    run     - runs $(PROJECT)"
	@echo "    test    - executes the test suite"
	@echo "    dist    - generates distribution"
	@echo "    all     - makes everything"
	@echo "    tags    - generates ctags"
	@echo
	@echo "    Look at the makefile for overridable variables."

todo:
	@grep  -R --only-matching "TODO.*$$"  $(SOURCE_FILES)
	@grep  -R --only-matching "FIXME.*$$" $(SOURCE_FILES)


all: prepare clean check test doc dist install
	@echo "Making everything for $(PROJECT)"

info:
	@echo "$(PROJECT)-$(PROJECT_VERSION) ($(PROJECT_STATUS))"
	@echo Source file lines:
	@wc -l $(SOURCE_FILES)


prepare: $(PYTHONHOME)/$(PARENT_MODULE)/__init__.py prepare-pre
	@echo "Preparing done."

prepare-pre:
	@echo "WARNING : You may required root priviledges to execute this rule."
	@echo "Preparing python for $(PROJECT)"
	sudo ln -snf $(PWD)/$(SOURCES)/$(PARENT_MODULE)/$(MAIN_MODULE) \
		  $(PYTHONHOME)/$(PARENT_MODULE)/$(MAIN_MODULE)

$(PYTHONHOME)/$(PARENT_MODULE)/__init__.py:
	@echo "Preparing python site-packages directory"
	mkdir -p $(PYTHONHOME)/$(PARENT_MODULE)
	touch $(PYTHONHOME)/$(PARENT_MODULE)/__init__.py

clean:
	@echo "Cleaning $(PROJECT)."
	@find . -name "*.pyc" -or -name "*.sw?" -or -name ".DS_Store" -or -name "*.bak" -or -name "*~" | xargs rm
	@rm -rf $(API)

check:
	@echo "Checking $(PROJECT) sources :"
ifeq ($(shell basename spam/$(PYCHECKER)),pychecker)
	@$(PYCHECKER) $(SOURCE_FILES)
	@echo "Checking $(PROJECT) tests :"
	@$(PYCHECKER) $(TEST_FILES)
else
	@echo "You need Pychecker to check $(PROJECT)."
	@echo "See <http://pychecker.sf.net>"
endif
	@echo "done."

test: $(SOURCE_FILES) $(TEST_FILES)
	@echo "Testing $(PROJECT)."
	@$(PYTHON) $(TEST_MAIN)

dist:
	@echo "Creating archive $(DISTRIBUTION)/$(PROJECT)-$(PROJECT_VERSION).tar.gz"
	@mkdir -p $(DISTRIBUTION)/$(PROJECT)-$(PROJECT_VERSION)
	@cp -r $(DISTROCONTENT) $(DISTRIBUTION)/$(PROJECT)-$(PROJECT_VERSION)
	@make -C $(DISTRIBUTION)/$(PROJECT)-$(PROJECT_VERSION) clean
	@make -C $(DISTRIBUTION)/$(PROJECT)-$(PROJECT_VERSION) doc
	@tar cfz $(DISTRIBUTION)/$(PROJECT)-$(PROJECT_VERSION).tar.gz \
	-C $(DISTRIBUTION) $(PROJECT)-$(PROJECT_VERSION)
	@rm -rf $(DISTRIBUTION)/$(PROJECT)-$(PROJECT_VERSION)

doc:
	@echo "Generating $(PROJECT) documentation"
ifeq ($(shell basename spam/$(EPYDOC)),epydoc)
	@mkdir -p $(API)
	@$(EPYDOC) --css $(RESOURCES)/epydoc.css --html -o $(API) -n "$(PROJECT) v.$(PROJECT_VERSION)" $(PROJECT_MODULES)
else
	@echo "Epydoc is required to generate $(PROJECT) documentation."
	@echo "Please see <http://epydoc.sf.net>"
endif

tags:
	@echo "Generating $(PROJECT) tags"
ifeq ($(shell basename spam/$(CTAGS)),ctags)
	@$(CTAGS) -R
else
	@echo "Ctags is required to generate $(PROJECT) tags."
	@echo "Please see <http://ctags.sf.net>"
endif

install: $(PYTHONHOME)/$(PARENT_MODULE)/__init__.py
	@echo "Installing $(PROJECT) in $(prefix)"

	@echo " - creating $(prefix)/share/$(project_lower)"
	@mkdir -p $(prefix)/share/$(project_lower)

	@echo " - copying files to $(prefix)/share/$(project_lower)"
	@tar cf $(PROJECT).tar -C $(SOURCES) \
	     $(filter-out $(SOURCES)/__init__.py $(SOURCES)/$(PARENT_MODULE)/__init__.py, \
	     $(subst $(SOURCES)/,,$(SOURCE_FILES)))
	@tar xf $(PROJECT).tar -C $(prefix)/share/$(project_lower)
	@rm $(PROJECT).tar

	@echo " - creating link in python home $(PYTHONHOME)/$(PARENT_MODULE)/$(MAIN_MODULE)"
	@ln -snf $(prefix)/share/$(project_lower)/$(PROJECT_MAIN) \
		  $(PYTHONHOME)

	@echo " - creating script $(prefix)/bin/$(project_lower)"
	@echo "#!/bin/sh" > $(prefix)/bin/$(project_lower)
	@echo '$(PYTHON) $(PYTHONHOME)/$(PROJECT_MAIN) $$@' >> \
	       $(prefix)/bin/$(project_lower)
	@chmod +x $(prefix)/bin/$(project_lower)


uninstall:
	@echo "Uninstalling $(PROJECT)."
	@rm -rf $(prefix)/share/$(project_lower)
	@rm $(prefix)/bin/$(project_lower)

#EOF
