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
# Contributors:
#
#    Haavard Wik Thorkildssen <havard.thorkildssen@telio.ch>
#
#
# TODO:
# - benchmark against ccheck.pl
# - add mapping for file ext to types of test
# - object oriented: make a class ccheck
#

import sys, os, re
import os, fnmatch

# config
version = '0.1.0'
extensions = ['c', 'h', 'mk', 'cpp']

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
# check for end of line termination issues
#
def check_termination(line, len):

    if len < 2:
        return

#    print "scanning len=%d line=%s" % (len, line)

    if line[-1] == ';':
        if line[-2] == ' ':
            error("has spaces before terminator")

    if line[-2:] == ';;':
        error("has double semicolon")


#
# check for C++ comments
#
def check_c_preprocessor(line, len):

    index = line.find('//')
    if index != -1:
        if line[index-1] != ':':
            error("C++ comment, use C comments /* ... */ instead")


#
# check that hexadecimal numbers are lowercase
#
def check_hex_lowercase(line, len):

    m = re.search('0x([0-9A-Fa-f]+)', line)
    if m:
        a = m.group(1)
        if re.search('[A-F]+', a):
            error("0x%s should be lowercase" % a)
        

#
# check for correct brackets usage in C/C++
#
# TODO: this is too slow, optimize
#
def check_brackets(line, len):

    operators = ["do", "if", "for", "while", "switch"]

#    return if (m/^\#if/); # skip macros

    m = re.search('\W*(\w+\W*)\(', line)
    if m:
        keyword = m.group(1)

#      return if ($keyword =~ m/\(/)

        if keyword.strip() in operators:
            if not re.search('[ ]{1}', keyword):
                error("no single space after operator '%s()'" % keyword)

    # check that else statements do not have preceeding
    # end-bracket on the same line
    if re.search('\s*\}\s*else', line):
        error("else: ending if bracket should be on previous line")


#
# map of extensions, and which checks to perform
#


"""
Function that does a simplified recursive globbing,
and returns a list of matches.
"""
def rec_quasiglob(top, patterns):
    for root, dirs, files in os.walk(top, topdown=False):
        for file in files:
            for pattern in patterns:
                if fnmatch.fnmatch(file, pattern):
                    path = os.path.join(root, file)
                    parse_any_file(path)


#
# scan all files of extensions .xyz
# parse all files
#
def build_file_list(top):
    for e in extensions:
        rec_quasiglob(top, ['*.' + e])


# mapping:
#
#   C-files:        .c
#   Header files:   .h  .hh
#   C++ files:      .cpp .cc
#   Makefiles:      Makefile, mk, mak
#
#

common_checks = [check_whitespace, check_whitespace2,
                 check_termination, check_hex_lowercase]

mapping = {
    'c':    [check_brackets, check_c_preprocessor],
    'cpp':  [check_brackets],
    'h':    [check_brackets],
    'mk':   [],
    }


for k, v in mapping.iteritems():
    print "mapping of *." + k + ":",  v


def process(line, funcs):
    # chomp
    line = line.rstrip('\n')
    line_len = len(line)

    for func in common_checks:
        func(line, line_len)

    for func in funcs:
        func(line, line_len)
    
    

def parse_file(filename, ext):
    #print "parsing " + filename

    funcs = mapping[e]
    
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
            process(line, funcs)


def parse_any_file(f):
#    print "parse_any_file: " + f
    for e in extensions:
        if fnmatch.fnmatch(f, '*.' + e):
            files[e].append(f)
            parse_file(f, e)
            return
    print "unknown extension: " + f


#
# print usage
#
def usage():
    print "ccheck version " + version
    print ""
    print "Usage:"
    print ""
    print "  ccheck [options]"
    print ""
    print "options:"
    print ""
    print "  --help     Display help"
    print "  --verbose  Verbose output"
    print "  --quiet    Only print warnings"
    print "  --exclude  Exclude pattern(s)"


#
# main program
#


# empty dict
for e in extensions:
    files[e] = []




if len(sys.argv) > 1:
    if sys.argv[1] == '--help':
        usage()
        exit(2)
    for f in sys.argv[1:]:
        print "checking: " + f
        if os.path.isdir(f):
            print "is a dir: + " + f
            build_file_list(f)
        elif os.path.isfile(f):
            parse_any_file(f)
        else:
            print "unknown file type: " + f
else:
    # scan all files recursively
    print "building file list.."
    build_file_list('.')    



#
# done - print stats
#
print_stats()


exit(errors != 0)
