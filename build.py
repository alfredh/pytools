#!/usr/bin/env python
#
# build.py Build script
#
# Copyright 2005 - 2009 Alfred E. Heggestad. All rights reserved.
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License version 2 as
#    published by the Free Software Foundation.
#

import os, platform, getpass, subprocess, shutil
import ConfigParser

# constants
VERSION  = '0.8.0'
SVN_CMD  = 'svn'
LOGEXT   = 'txt'
CC       = 'gcc'
MAKE     = 'make'
CCHECK   = '/usr/local/bin/ccheck.py'
HOSTNAME = platform.node()
USERNAME = getpass.getuser()
UNAME    = os.uname()
CC_VER   = subprocess.Popen([CC, "--version"], stdout=subprocess.PIPE).\
           communicate()[0].split('\n')[0]


class Build:
    # flags - TODO move to config file
    do_svn = 1
    do_build = 1
    do_install = 0
    do_deb = 0
    do_rpm = 0
    do_ccheck = 1
    do_doxygen = 1
    do_splint = 1

    def __init__(self, root_dir):
        print "Build init: %s" % root_dir

        self.root_dir = root_dir
        self.log_dir = self.root_dir + '/log'
        self.svn_dir = self.root_dir + '/svn'

        self.clean_dir(self.log_dir)

        if self.do_svn:
            self.clean_dir(self.svn_dir)


    def clean_dir(self, dir):
        if os.path.exists(dir):
            shutil.rmtree(dir, ignore_errors=True)
        if not os.path.exists(dir):
            os.makedirs(dir)


    def logfile(self, prefix, module, branch):
        f = prefix + '-' + module + '-' + branch + '.' + LOGEXT
        return os.path.join(self.log_dir, f)


    def svn_update(self, svn_base, module, branch):
        print "subversion update [%s, %s]..." % (module, branch)

        if branch == 'trunk':
            url = os.path.join(svn_base, module, 'trunk')
        else:
            url = os.path.join(svn_base, module, 'branches', branch)

        path = os.path.join(self.svn_dir, branch, module)

        svn = 'svn co ' + url + ' ' + path + '>>' + \
              self.logfile('svn', module, branch) + ' 2>&1'

        subprocess.Popen(svn, shell=True).communicate()


    def run_ccheck(self, module, branch):
        print "running ccheck [%s, %s]..." % (module, branch)

        mod = os.path.join(self.svn_dir, branch, module)
        lf = self.logfile('ccheck', module, branch)

        cmd = 'cd ' + mod + '&&' + CCHECK + ' --quiet >>' + lf + ' 2>&1'

        subprocess.Popen(cmd, shell=True).communicate()

        # print warnings and errors to stdout
        subprocess.Popen('cat ' + lf, shell=True).communicate()


    def run_op(self, dir, op, lf):
        cmd = 'cd ' + dir + ' && ' + op + ' >> ' + lf + ' 2>&1'
        p = subprocess.Popen(cmd, shell=True)
        p.communicate()
        ret = p.returncode
        if ret != 0:
            cmd = 'echo \"Error: ' + dir + op + ' failed (' + ret + ')\" '\
                  '>> ' + lf + ' 2>&1'
            subprocess.Popen(cmd, shell=True).communicate()


    def build_binaries(self, module, branch):
        print "building binaries [%s, %s]..." % (module, branch)

        dir = os.path.join(self.svn_dir, branch, module)
        lf = self.logfile('binaries', module, branch)

        self.run_op(dir, 'make CC=' + CC, lf)

        if self.do_install:
            self.run_op(dir, 'make install CC=' + self.cc, lf)

        # print warnings and errors to stdout
        subprocess.Popen('grep -i \"warning[ :]\" ' + lf, \
                         shell=True).communicate()
        subprocess.Popen('grep -i \"error[ :]\" ' + lf, \
                         shell=True).communicate()


    def run_splint(self, module, branch):
        print "running splint [%s, %s]..." % (module, branch)

        dir = os.path.join(self.svn_dir, branch, module)
        lf = self.logfile('splint', module, branch)

        self.run_op(dir, 'make splint', lf)

        subprocess.Popen('cat ' + lf, shell=True).communicate()


    def run_tests(self, svn_base, mods):
        for mod in mods:
            for b in mods[mod]:
                if self.do_svn: self.svn_update(svn_base, mod, b)
                if self.do_ccheck: self.run_ccheck(mod, b)
                if self.do_splint: self.run_splint(mod, b)
            #run_doxygen $module, $module_hash{$module}->[$i] if $do_doxygen;
        for mod in mods:
            for b in mods[mod]:
                if self.do_build: self.build_binaries(mod, b)
                # deb
                # rpm


apps = {}
libs = {}

def read_mods(config, section):
    d = {}

    for item in config.items(section):
        module = item[0]
        branches = item[1].split(',')
        d[module] = [x.strip() for x in branches]

    return d


config_file = 'build.cfg'

config = ConfigParser.ConfigParser()
config.read(config_file)

svn_base = config.get('core', 'svn_base')
apps     = read_mods(config, 'apps')
libs     = read_mods(config, 'libs')


#print "apps = %s, libs = %s" % (apps, libs)


# ---------------------------------------------------

bld = Build('/Users/alfredh/tmp/build')

bld.run_tests(svn_base, libs)
bld.run_tests(svn_base, apps)