PROJECT = texto
TEST_FILES = $(wildcard tests/*.txto)
TEST_PRODUCT = $(TEST_FILES:%.txto=%.html)
include lib/mk/python-module.mk

tests: $(TEST_PRODUCT)

%.html: %.txto
	texto $< $@
#EOF
