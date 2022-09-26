#!/usr/bin/env python
# -----------------------------------------------------------------------------
# Project           : Texto
# -----------------------------------------------------------------------------
# Author            : Sebastien Pierre             <sebastien.pierre@gmail.com>
# -----------------------------------------------------------------------------
# Creation  date    : 2021-06-12
# Last mod.         : 2021-06-12
# -----------------------------------------------------------------------------
from texto.formats import Processor as BaseProcessor
import json


class Processor(BaseProcessor):

    def processElementNode(self, element, selector, isSelectorOptional=False):
        name = element.nodeName
        attr = dict((_.name, _.value) for _ in (element.attributes.item(_)
                                                for _ in range(len(element.attributes))))
        children = [self.processElement(_) for _ in element.childNodes]
        node = [name]
        if children:
            return [name, attr, children]
        elif attr:
            return [name, attr]
        else:
            return [name]

    def generate(self, xmlDocument, bodyOnly=False, variables={}):
        return json.dumps(super().generate(xmlDocument, bodyOnly, variables))


processor = Processor()
process = processor.process
# EOF
