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
from subprocess import *

# config
version = '0.1.0'
extensions = ['c', 'h']

# global variables
files = {}
errors = 0
empty_lines_count = 0
cur_filename = ''
cur_lineno = 0


#
# helper functions
#

#
# print an error message and increase error count
#
def error(msg):
    global errors
    print "%s:%d: %s" % (cur_filename, cur_lineno, msg)
    errors += 1


#
# print statistics
#
def print_stats():
    print "Statistics:"
    print "~~~~~~~~~~~"
    print "Number of files processed:   ",
    for e in extensions:
        print " .%s: %d" % (e, len(files[e])),
    print ""
    print "Number of lines with errors:   %d" % errors
    print ""


#
# functions checking code
#


#
# check for strange white space
#
def check_whitespace(line, len):

    if len == 0:
        return

    # general trailing whitespace check
    if line[-1] == ' ':
        error("has trailing space(s)")

    if line[-1] == '\t':
        error("has trailing tab(s)")

    # make sure TAB is used for indentation
    for n in range(4, 9, 4):
        if len > n and line[0:n] == ' '*n and line[n] != ' ':
            error("starts with %d spaces, use tab instead" % n)


def check_whitespace2(line, len):
    
    # check for empty lines count
    global empty_lines_count
    if len == 0:
        empty_lines_count += 1
    else:
        empty_lines_count = 0
    if empty_lines_count > 2:
        error("should have maximum two empty lines (%d)" % empty_lines_count)
        empty_lines_count = 0

#
# map of extensions, and which checks to perform
#


#
# scan all files of extensions .xyz
# parse all files
#
def build_file_list():
    for e in extensions:
        cmd = "find . -type f -name \"*." + e + "\""
        out = Popen(cmd, stdout=PIPE, shell=True).communicate()[0]
        files[e] = out.split()


def process(line):
    # chomp
    line = line.rstrip('\n')
    line_len = len(line)

    check_whitespace(line, line_len)
    check_whitespace2(line, line_len)


def parse_file(filename):
    print "parsing " + filename
    file = open(filename)

    global cur_filename, cur_lineno
    cur_filename = filename
    
    while 1:
        lines = file.readlines(100000)
        if not lines:
            break
        cur_lineno = 0
        for line in lines:
            cur_lineno += 1
            process(line)


#
# main program
#


if len(sys.argv) > 1:
    for line in fileinput.input():
        if fileinput.isfirstline():
            print "scanning " + fileinput.filename()
        process(line)
else:
    # scan recurs
    print "building file list.."
    build_file_list()    

    print "scanning .."
    for e in extensions:
        for f in files[e]:
            pass
            parse_file(f)

    

#
# done - print stats
#
print_stats()
