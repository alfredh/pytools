#!/usr/bin/env python
#
# build.py Build script
#
# Copyright 2005 - 2014 Alfred E. Heggestad. All rights reserved.
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License version 2 as
#    published by the Free Software Foundation.
#
# TODO:
#
#  - debian build gives some warnings/errors
#
#
# normal messages are written to STDOUT
# error messages are written to STDERR
#

import os, sys, platform, getpass, subprocess, shutil, time, re
import ConfigParser

# constants
VERSION  = '0.8.2'
LOGEXT   = 'txt'
CCHECK   = '/usr/local/bin/ccheck.py'
HOSTNAME = platform.node()
USERNAME = getpass.getuser()
UNAME    = os.uname()[3]


def linecount(fname):
    f = open(fname, 'r')
    count = len(f.readlines())
    f.close()
    return count


class Build:
    # default flags
    do_svn = 1
    do_git = 1
    do_build = 1
    do_deb = 0
    do_rpm = 0
    do_ccheck = 1
    do_doxygen = 1
    do_splint = 1

    cxx = 'g++'

    def __init__(self, root_dir, config):
        print "Build init: %s" % root_dir

        self.do_svn     = config.getboolean('tests', 'do_svn')
        self.do_git     = config.getboolean('tests', 'do_git')
        self.do_build   = config.getboolean('tests', 'do_build')
        self.do_deb     = config.getboolean('tests', 'do_deb')
        self.do_rpm     = config.getboolean('tests', 'do_rpm')
        self.do_ccheck  = config.getboolean('tests', 'do_ccheck')
        self.do_doxygen = config.getboolean('tests', 'do_doxygen')
        self.do_splint  = config.getboolean('tests', 'do_splint')

        self.make = config.get('core', 'make')
        self.cc = config.get('core', 'cc')
        self.cxx = config.get('core', 'cxx')
        self.svn = config.get('core', 'svn')
        self.git = config.get('core', 'git')

        self.cc_ver = subprocess.Popen([self.cc, "--version"], \
                                       stdout=subprocess.PIPE).\
                                       communicate()[0].split('\n')[0]

        self.root_dir = root_dir
        self.log_dir = os.path.join(self.root_dir, 'log')
        self.src_dir = os.path.join(self.root_dir, 'src')

        self.clean_dir(self.log_dir)

        if self.do_svn or self.do_git:
            self.clean_dir(self.src_dir)


    def clean_dir(self, dir):
        if os.path.exists(dir):
            shutil.rmtree(dir, ignore_errors=True)
        if not os.path.exists(dir):
            os.makedirs(dir)


    def logfile(self, prefix, module):
        f = prefix + '-' + module + '.' + LOGEXT
        return os.path.join(self.log_dir, f)


    def check_log(self, logfile, type, module, pattern=None):
        if os.path.getsize(logfile):
            heading = False
            f = open(logfile, 'r')

            for line in f:
                if pattern is None:
                    output = True
                elif re.search(pattern, line, re.I):
                    output = True
                else:
                    output = False

                if output:
                    if not heading:
                        heading = True
                        print >> sys.stderr, '----- ' + type \
                              + ' failed for ' \
                              + module + ' -----'
                    sys.stderr.write(line)

            f.close()


    def run_op(self, dir, op, lf):
        if dir and not os.path.exists(dir):
            os.makedirs(dir)
        cmd = 'cd ' + dir + ' && ' + op + ' >> ' + lf + ' 2>&1'
        p = subprocess.Popen(cmd, shell=True)
        p.communicate()
        ret = p.returncode
        if ret != 0:
            cmd = 'echo \"Error: ' + dir + ' ' + op + ' failed (' \
                  + str(ret) + ')\" ' '>> ' + lf + ' 2>&1'
            subprocess.Popen(cmd, shell=True).communicate()


    def svn_update(self, name, url):
        print "subversion update [%s, %s]..." % (name, url)

        path = os.path.join(self.src_dir, name)

        lf = self.logfile('svn', name)
        self.run_op(path, self.svn + ' co ' + url + ' ' + path, lf)


    def git_clone(self, name, url):
        print "git clone [%s, %s]..." % (name, url)

        path = os.path.join(self.src_dir, name)

        lf = self.logfile('git', name)
        self.run_op(path, self.git + ' clone ' + url + ' ' + path, lf)


    def run_ccheck(self, module):
        print "running ccheck [%s]..." % (module)

        mod = os.path.join(self.src_dir, module)
        lf = self.logfile('ccheck', module)

        cmd = 'cd ' + mod + '&&' + CCHECK + ' --quiet >>' + lf + ' 2>&1'
        subprocess.Popen(cmd, shell=True).communicate()

        self.check_log(lf, 'ccheck', module)


    def build_binaries(self, module):
        print "building binaries [%s]..." % (module)

        path = os.path.join(self.src_dir, module)
        lf = self.logfile('binaries', module)

        self.run_op(path, self.make + ' CC=' + self.cc + ' CXX=' + self.cxx, lf)

        self.check_log(lf, 'binaries', module, 'warning|error[ :]')


    def run_splint(self, module):
        print "running splint [%s]..." % (module)

        lf = self.logfile('splint', module)

        self.run_op(os.path.join(self.src_dir, module),
                    self.make + ' splint', lf)

        self.check_log(lf, 'splint', module)


    def run_doxygen(self, module):

        path = os.path.join(self.src_dir, module)
        lf = self.logfile('doxygen', module)

        if os.path.isfile(path + '/mk/Doxyfile'):
            print "running doxygen [%s]..." % (module)

            self.run_op(path, self.make + ' dox', lf)

            self.check_log(lf, 'doxygen', module, 'warning |error ')


    # Make Debian package
    def make_deb(self, module):
        print "make deb [%s]..." % (module)

        path = os.path.join(self.src_dir, module)
        lf = self.logfile('makedeb', module)

        if os.path.exists(path + '/debian'):
            self.run_op(path, self.make + ' deb', lf)
            self.check_log(lf, 'makedeb', module, 'warning|error[ :]')


    # Make RPM package
    def make_rpm(self, module):
        print "make rpm [%s]..." % (module)

        path = os.path.join(self.src_dir, module)
        lf = self.logfile('makerpm', module)

        if os.path.exists(path + '/rpm'):
            self.run_op(path, self.make + ' rpm', lf)

            self.check_log(lf, 'makerpm', module, 'warning|error[ :]')


    def run_tests(self, mods):
        for mod in mods:
            if self.do_ccheck:  self.run_ccheck(mod)
            if self.do_splint:  self.run_splint(mod)
            if self.do_doxygen: self.run_doxygen(mod)
            if self.do_deb:     self.make_deb(mod)
            if self.do_rpm:     self.make_rpm(mod)




def usage():
  print sys.argv[0] + " version " + VERSION
  print ""
  print "Usage:"
  print ""
  print "  " + sys.argv[0] + " [options] <config file>"
  print ""
  print "options:"
  print "  --help     Display help"


def read_mods(config, section):
    d = {}

    for item in config.items(section):
        module = item[0]
        branches = item[1].split(',')
        d[module] = [x.strip() for x in branches]

    return d


# ---------------------------------------------------

if __name__ == '__main__':

    apps = {}
    libs = {}
    mods = {}
    gits = {}
    
    if len (sys.argv) <= 1:
        usage()
        exit(2)

    config_file = sys.argv[1]

    print 'running ' + sys.argv[0] + ' v' + VERSION + \
          ' with config ' + config_file + ' on ' + HOSTNAME + '...'

    config = ConfigParser.ConfigParser()
    config.read(config_file)

    root_dir = config.get('core', 'root_dir')
    apps     = read_mods(config, 'apps')
    libs     = read_mods(config, 'libs')
    gits     = read_mods(config, 'gits')

    for a in apps:
        mods[a] = apps[a]
    for l in libs:
        mods[l] = libs[l]
    for g in gits:
        mods[g] = gits[g]

    bld = Build(root_dir, config)

    if bld.do_svn:
        print "checkout subversion projects ..."
        for name in libs:
            url = libs[name][0]
            bld.svn_update(name, url)
        for name in apps:
            url = apps[name][0]
            bld.svn_update(name, url)

    if bld.do_git:
        print "clone GIT projects ..."
        for name in gits:
            url = gits[name][0]
            bld.git_clone(name, url)

    # Build step: libs must be built first
    if bld.do_build:
        print "building all projects ..."
        for l in libs:
            bld.build_binaries(l)
        for a in apps:
            bld.build_binaries(a)
        for g in gits:
            bld.build_binaries(g)

    bld.run_tests(mods)

    print 'build complete.'
