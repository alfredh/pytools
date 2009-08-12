#! /usr/bin/env python
#
# ccheck.py  Code Checker
#
# Copyright (C) 2005 - 2009 Alfred E. Heggestad
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License version 2 as
#    published by the Free Software Foundation.
#

import fileinput

version = '0.2.0'

# config


# functions checking code


# main program

# map of extensions, and which checks to perform

# scan all files of extensions .xyz
# parse all files

# print stats

for line in fileinput.input():
    print "== %s:%d: %s" % (fileinput.filename(), fileinput.filelineno(), line.rstrip())
