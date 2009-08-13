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

import sys, os, re
import fileinput

# config
version = '0.1.0'

# global variables
errors = 0
empty_lines_count = 0


#
# helper functions
#

#
# print an error message and increase error count
#
def error(msg):
    global errors
    print "%s:%d: %s" % (fileinput.filename(), fileinput.filelineno(), msg)
    errors += 1


#
# print statistics
#
def print_stats():
    print "Statistics:"
    print "~~~~~~~~~~~"
    print "Number of files processed:    "
#    foreach (@extension) {
#      print " $_: $stats{$_} "
#    }
    print ""
    print "Number of lines with errors:   %d" % errors
    print ""


#
# functions checking code
#


#
# check for strange white space
#
def check_whitespace(line):

    # chomp
    line = line.rstrip('\n')
    line_len = len(line)

#    print "scanning line {%d} [%s]" % (line_len, line)

    # general trailing whitespace check
    if re.search(' $', line):
        error("has trailing space(s)")
    if re.search('\t$', line):
        error("has trailing tab(s)")

    # make sure TAB is used for indentation
    for n in range(4, 17, 4):
        if re.match('^ {%d}\S+' % n, line):
            error("starts with %d spaces, use tab instead" % n)

    # check for empty lines count
    global empty_lines_count
    if 1 == fileinput.lineno():
        empty_lines_count = 0
    if line_len == 0:
        empty_lines_count += 1
    else:
        empty_lines_count = 0
    if empty_lines_count > 2:
        error("should have maximum two empty lines (%d)" % empty_lines_count)
        empty_lines_count = 0

    return


#
# main program
#


#
# map of extensions, and which checks to perform
#


#
# scan all files of extensions .xyz
# parse all files
#
  

# check program arguments
if len(sys.argv) > 0:
    for line in fileinput.input():
        check_whitespace(line)
else:
    # scan recurs
    pass


#
# done - print stats
#
print_stats()
