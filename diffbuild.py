#! /usr/bin/env python
#
# diffbuild.py -- Written by Alfred E. Heggestad 2012
#

import os, sys, subprocess, re

objdump = 'gobjdump'


def run_command(cmd):
    p = subprocess.Popen(cmd, shell=True)
    p.communicate()
    if p.returncode != 0:
        print 'error' + str(p.returncode)


def analyze(file):

    sect = {}

    p = subprocess.Popen(objdump + ' -h ' + file, shell=True,
                         stdout=subprocess.PIPE)
    (out, err) = p.communicate()

    lines = out.splitlines()

    for line in lines:
        m = re.match('[ \t]*[0-9]+[ \t]+.([a-z_\.]+)\s+([0-9a-f]+)', line)
        if m:
            name = m.group(1)
            size = m.group(2)
            sect[name] = int(size, 16)

    return sect


def diff_sect(a, b):

    c = {}

    for k,v in a.items():
        c[k] = a[k] - b[k]

    return c


def print_all(binary, sect, diff):

    print "#"
    print "# codesize changes for `%s'" % binary
    print "#"

    total = 0
    totalx = 0

    for k in sorted(sect.keys()):

        total += sect[k]
        totalx += diff[k]

        print("%-26s %7d bytes" % (k, sect[k])),

        x = diff[k]
        if x != 0:
            print(" (%+d bytes)" % (x) ),

        print("")

    print "----------------------------------------"
    print("total:                      %d bytes" % (total)),

    if totalx != 0:
        print(" (%+d bytes)" % (totalx) ),
    print ""
    print "----------------------------------------"


if __name__ == '__main__':

    if len (sys.argv) <= 1:
        print "usage: %s <binary>" % sys.argv[0]
        exit(2)

    f = sys.argv[1]
    c = " ".join(sys.argv[1:])

    a = analyze(f)

    run_command('make ' + c)

    b = analyze(f)

    x = diff_sect(b, a)

    print_all(f, b, x)
