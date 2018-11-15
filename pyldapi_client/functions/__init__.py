# -*- coding: utf-8 -*-
#
"""
Utility functions shared between the py27 and py35 versions of ldapi-client
In theory all of these should be compatible with _all_ versions of python
"""
import re

reg_Register = "http://purl.org/linked-data/registry#Register"
reg_register = "http://purl.org/linked-data/registry#register"
reg_cic = "http://purl.org/linked-data/registry#containedItemClass"
ldp_Page = "http://www.w3.org/ns/ldp#Page"
vocab_first = "https://www.w3.org/1999/xhtml/vocab#first"
vocab_last = "https://www.w3.org/1999/xhtml/vocab#last"

per_page_matcher = re.compile(r"[\&|\?]per_page=([0-9]+)")
page_matcher = re.compile(r"[\&|\?]page=([0-9]+)")


def extract_page_from_string(page_string):
    page_matches = page_matcher.search(page_string)
    if page_matches:
        page = int(page_matches.group(1))
    else:
        page = None
    return page


def extract_per_page_from_string(page_string):
    per_page_matches = per_page_matcher.search(page_string)
    if per_page_matches:
        per_page = int(per_page_matches.group(1))
    else:
        per_page = None
    return per_page


def find_registers_from_ld_payload(uri, json_payload, container):
    assert isinstance(json_payload, list), "The json payload must be a list of objects."
    registers = {}
    for r in json_payload:
        if "@id" not in r:
            continue
        if '@type' in r and reg_Register in r['@type']:
            identifier = r['@id']
            reg = container(identifier, item_classes=[], payload=None)
            if reg_cic in r:
                cics = r[reg_cic]
                for cic in cics:
                    if "@id" in cic:
                        reg.item_classes.append(cic["@id"])
            if identifier == uri:
                reg.payload = json_payload
            registers[identifier] = reg
    return registers
