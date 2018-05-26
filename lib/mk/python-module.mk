# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PYTHON MODULE MAKEFILE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Updated: 2016-08-16
# Created: 2016-08-16
# License: MIT License
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
VERSION        = `grep __version__ src/$(MODULE)/*.py | cut -d '=' -f2  | xargs echo`

SOURCES_PY     = $(wildcard src/*.py) $(wildcard src/*/*.py) $(wildcard src/*/*/*.py)
SOURCES_TXTO   = $(wildcard doc/*.txto)
MANIFEST       = $(SOURCES_PY) $(wildcard *.py api/*.* AUTHORS* README* LICENSE*)
OS             = `uname -s | tr A-Z a-z`

PRODUCT        = MANIFEST

YELLOW =`tput setaf 11`
GREEN  =`tput setaf 10`
CYAN   =`tput setaf 14`
RED    =`tput setaf 1`
GRAY   =`tput setaf 7`
RESET  =`tput sgr0`

.PHONY: all doc clean check test

# ─────────────────────────────────────────────────────────────────────────────
#
# MAIN RULES
# 
# ─────────────────────────────────────────────────────────────────────────────

all: $(PRODUCT)

release: $(PRODUCT)
	git commit -a -m "Release $(VERSION)" ; true
	git tag $(VERSION) ; true
	git push --all ; true
	python setup.py clean sdist register upload

clean:
	@rm -f $(PRODUCT) ; true

check:
	pychecker -100 $(SOURCES)

test:
	PYTHONPATH=src:$(PYTHONPATH) python tests/run.py

# ─────────────────────────────────────────────────────────────────────────────
#
# BUILD FILES
# 
# ─────────────────────────────────────────────────────────────────────────────

MANIFEST: $(MANIFEST)
	echo $(MANIFEST) | xargs -n1 | sort | uniq > $@

# ─────────────────────────────────────────────────────────────────────────────
#
# HELPERS
# 
# ─────────────────────────────────────────────────────────────────────────────

print-%:
	@echo $*=$($*) | xargs -n1 echo

FORCE:

#EOF
