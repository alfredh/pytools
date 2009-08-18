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
#    Mal Minhas <mal@malm.co.uk>
#
#
# TODO:
# - optimize regex functions
# - count max y lines
#

import sys, os, re, fnmatch, getopt

PROGRAM = 'ccheck'
VERSION = '0.1.0'
AUTHOR  = 'Alfred E. Heggestad'


###
### Class definition
###

class ccheck:

    def __init__(self):
        self.errors = 0
        self.cur_filename = ''
        self.cur_lineno = 0
        self.empty_lines_count = 0
        self.files = {}
        self.extensions = ['c', 'cpp', 'h', 'mk', 'm4', 'py']

        self.operators = ["do", "if", "for", "while", "switch"]
        self.re_tab  = re.compile('(\w+\W*)\(')
        self.re_else = re.compile('\s*\}\s*else')
        self.re_inc  = re.compile('(^\s+\w+[+-]{2};)')
        self.re_hex  = re.compile('0x([0-9A-Fa-f]+)')

        # empty dict
        for e in self.extensions:
            self.files[e] = []

        # todo: global config
        self.common_checks = [self.check_whitespace, self.check_termination,
                              self.check_hex_lowercase, self.check_pre_incr,
                              self.check_file_unix]
        self.funcmap = {
            'c':    [self.check_brackets, self.check_c_preprocessor,
                     self.check_indent_tab],
            'h':    [self.check_brackets, self.check_indent_tab],
            'cpp':  [self.check_brackets, self.check_indent_tab],
            'mk':   [self.check_indent_tab],
            'm4':   [self.check_brackets, self.check_c_comments,
                     self.check_indent_tab],
            'py':   [self.check_brackets, self.check_indent_space],
            }
        self.extmap = {
            'c':    ['*.c'],
            'h':    ['*.h'],
            'cpp':  ['*.cpp', '*.cc'],
            'mk':   ['*Makefile', '*.mk'],
            'm4':   ['*.m4'],
            'py':   ['*.py'],
            }
        self.maxsize = {
            'c':  (79, 3000),
            'h':  (79, 1000),
            'mk': (79, 1000),
            'm4': (79, 3000),
            'py': (79, 3000),
            }


    def __del__(self):
        pass


    #
    # print an error message and increase error count
    #
    def error(self, msg):
        print >> sys.stderr, "%s:%d: %s" % \
              (self.cur_filename, self.cur_lineno, msg)
        self.errors += 1


    #
    # print statistics
    #
    def print_stats(self):
        print "Statistics:"
        print "~~~~~~~~~~~"
        print "Number of files processed:   ",
        for e in self.extensions:
            print " %s: %d" % (e, len(self.files[e])),
        print ""
        print "Number of lines with errors:   %d" % self.errors
        print ""


    #
    # check for strange white space
    #
    def check_whitespace(self, line, len):

        if len == 0:
            return

        # general trailing whitespace check
        if line[-1] == ' ':
            self.error("has trailing space(s)")

        if line[-1] == '\t':
            self.error("has trailing tab(s)")

        # check for empty lines count
        if len == 0:
            self.empty_lines_count += 1
        else:
            self.empty_lines_count = 0
        if self.empty_lines_count > 2:
            self.error("should have maximum two empty lines (%d)" % \
                       self.empty_lines_count)
            self.empty_lines_count = 0


    #
    # check for strange white space
    #
    def check_indent_tab(self, line, len):

        # make sure TAB is used for indentation
        for n in range(4, 17, 4):
            if len > n and line[0:n] == ' '*n and line[n] != ' ':
                self.error("starts with %d spaces, use tab instead" % n)


    def check_indent_space(self, line, len):

        if len > 1 and line[0] == '\t':
            self.error("starts with TAB, use 4 spaces instead")


    #
    # check for end of line termination issues
    #
    def check_termination(self, line, len):

        if len < 2:
            return

        if line[-2:] == ' ;':
            self.error("has spaces before terminator")

        if line[-2:] == ';;':
            self.error("has double semicolon")


    #
    # check for C++ comments
    #
    def check_c_preprocessor(self, line, len):

        index = line.find('//')
        if index != -1:
            if line[index-1] != ':':
                self.error("C++ comment, use C comments /* ... */ instead")


    #
    # check that C comments are not used
    #
    def check_c_comments(self, line, len):

        if line.find('/*') != -1 or line.find('*/') != -1:
            self.error("C comment, use Perl-style comments # ... instead");


    #
    # check max line length and number of lines
    #
    def check_xy_max(self, line, line_len, max_x):

        # expand TAB to 8 spaces
        l = len(line.expandtabs())

        if l > max_x:
            self.error("line is too wide (" + str(l) + " - max " \
                       + str(max_x) + ")");

        #    TODO:
        #    if ($line > $max_y) {
        #      self.error("is too big ($lines lines - max $max_y)\n");


    #
    # check that hexadecimal numbers are lowercase
    #
    def check_hex_lowercase(self, line, len):

        m = self.re_hex.search(line)
        if m:
            a = m.group(1)
            if re.search('[A-F]+', a):
                self.error("0x%s should be lowercase" % a)


    #
    # check for correct brackets usage in C/C++
    #
    # TODO: this is too slow, optimize
    #
    def check_brackets(self, line, len):

        m = self.re_tab.search(line)
        if m:
            keyword = m.group(1)

            if keyword.strip() in self.operators:
                if not re.search('[ ]{1}', keyword):
                    self.error("no single space after operator '%s()'" \
                               % keyword)

        # check that else statements do not have preceeding
        # end-bracket on the same line
        if self.re_else.search(line):
            self.error("else: ending if bracket should be on previous line")


    #
    # check that file is in Unix format
    #
    def check_file_unix(self, line, len):

        if len < 1:
            return

        if line[-1] == '\r':
            self.error("not in Unix format");


    #
    # check for post-increment/decrement
    #
    def check_pre_incr(self, line, len):

        m = self.re_inc.search(line)
        if m:
            op = m.group(1)
            if op.find('++') != -1:
                self.error("Use pre-increment: %s" % op);
            else:
                self.error("Use pre-decrement: %s" % op);


    def process_line(self, line, funcs, ext):

        line = line.rstrip('\n')
        line_len = len(line)

        for func in self.common_checks:
            func(line, line_len)

        for func in funcs:
            func(line, line_len)

        if ext in self.maxsize:
            (x, y) = self.maxsize[ext];
            self.check_xy_max(line, line_len, x)


    def parse_file(self, filename, ext):

        funcs = self.funcmap[ext]

        f = open(filename)

        self.cur_filename = filename

        while 1:
            lines = f.readlines(100000)
            if not lines:
                break
            self.cur_lineno = 0
            for line in lines:
                self.cur_lineno += 1
                self.process_line(line, funcs, ext)


    def parse_any_file(self, f):
        for e in self.extensions:
            em = self.extmap[e]
            for m in em:
                if fnmatch.fnmatch(f, m):
                    self.files[e].append(f)
                    self.parse_file(f, e)
                    return
        print "unknown extension: " + f


    def rec_quasiglob(self, top, patterns):
        for root, dirs, files in os.walk(top, topdown=False):
            for f in files:
                for pattern in patterns:
                    if fnmatch.fnmatch(f, pattern):
                        path = os.path.join(root, f)
                        self.parse_any_file(path)


    def build_file_list(self, top):
        for e in self.extensions:
            em = self.extmap[e]
            self.rec_quasiglob(top, em)


###
### END OF CLASS
###


def usage():
    print "%s version %s" % (PROGRAM, VERSION)
    print ""
    print "Usage:"
    print ""
    print "  %s [options] [file]... [dir]..." % PROGRAM
    print ""
    print "options:"
    print ""
    print "  -h --help     Display help"
    print "  -V --version  Show version info"


#
# main program
#


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hV', ['help', 'version'])
    except getopt.GetoptError, err:
        print str(err)
        usage()
        sys.exit(2)
    for o, a in opts:
        if o in ('-h', '--help'):
            usage()
            sys.exit()
        elif o in ('-V', '--version'):
            print "%s version %s, written by %s" % (PROGRAM, VERSION, AUTHOR)
            sys.exit()
        else:
            assert False, "unhandled option"

    cc = ccheck()

    if len(sys.argv) > 1:
        for f in sys.argv[1:]:
            print "checking: " + f
            if os.path.isdir(f):
                cc.build_file_list(f)
            elif os.path.isfile(f):
                cc.parse_any_file(f)
            else:
                print "unknown file type: " + f
    else:
        # scan all files recursively
        cc.build_file_list('.')

    # done - print stats
    cc.print_stats()

    exit(cc.errors != 0)


if __name__ == "__main__":
    main()
