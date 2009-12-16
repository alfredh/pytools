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
# TODO:
#
#  - multiple (cross) compilers
#  - debian build gives some warnings/errors
#  - html-table output
#

import os, sys, platform, getpass, subprocess, shutil, time, re
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
UNAME    = os.uname()[3]
CC_VER   = subprocess.Popen([CC, "--version"], stdout=subprocess.PIPE).\
           communicate()[0].split('\n')[0]


def linecount(fname):
    f = open(fname, 'r')
    count = len(f.readlines())
    f.close()
    return count


class Build:
    # default flags
    do_svn = 1
    do_build = 1
    do_install = 0
    do_deb = 0
    do_rpm = 0
    do_ccheck = 1
    do_doxygen = 1
    do_splint = 1

    def __init__(self, root_dir, config):
        print "Build init: %s" % root_dir

        self.do_svn     = config.getboolean('tests', 'do_svn')
        self.do_build   = config.getboolean('tests', 'do_build')
        self.do_install = config.getboolean('tests', 'do_install')
        self.do_deb     = config.getboolean('tests', 'do_deb')
        self.do_rpm     = config.getboolean('tests', 'do_rpm')
        self.do_ccheck  = config.getboolean('tests', 'do_ccheck')
        self.do_doxygen = config.getboolean('tests', 'do_doxygen')
        self.do_splint  = config.getboolean('tests', 'do_splint')

        self.root_dir = root_dir
        self.log_dir = os.path.join(self.root_dir, 'log')
        self.svn_dir = os.path.join(self.root_dir, 'svn')

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


    def check_log(self, logfile, type, module, branch, pattern=None):
        if os.path.getsize(logfile):
            heading = False
            f = open(logfile, 'r')

            for line in f:
                if pattern is None:
                    output = True
                elif re.search(pattern, line):
                    output = True
                else:
                    output = False

                if output:
                    if not heading:
                        heading = True
                        print >> sys.stderr, '----- ' + type \
                              + ' failed for ' \
                              + module + '/' + branch + ' -----'
                    sys.stderr.write(line)

            f.close()


    def run_op(self, dir, op, lf):
        cmd = 'cd ' + dir + ' && ' + op + ' >> ' + lf + ' 2>&1'
        p = subprocess.Popen(cmd, shell=True)
        p.communicate()
        ret = p.returncode
        if ret != 0:
            cmd = 'echo \"Error: ' + dir + op + ' failed ('+str(ret)+')\" '\
                  '>> ' + lf + ' 2>&1'
            subprocess.Popen(cmd, shell=True).communicate()


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

        self.check_log(lf, 'ccheck', module, branch)


    def build_binaries(self, module, branch):
        print "building binaries [%s, %s]..." % (module, branch)

        path = os.path.join(self.svn_dir, branch, module)
        lf = self.logfile('binaries', module, branch)

        self.run_op(path, 'make CC=' + CC, lf)

        if self.do_install:
            self.run_op(path, 'make install CC=' + CC, lf)

        self.check_log(lf, 'binaries', module, branch, 'warning|error[ :]')


    def run_splint(self, module, branch):
        print "running splint [%s, %s]..." % (module, branch)

        lf = self.logfile('splint', module, branch)

        self.run_op(os.path.join(self.svn_dir, branch, module),
                    'make splint', lf)

        self.check_log(lf, 'splint', module, branch)


    def run_doxygen(self, module, branch):

        path = os.path.join(self.svn_dir, branch, module)
        lf = self.logfile('doxygen', module, branch)

        if os.path.isfile(path + '/mk/Doxyfile'):
            print "running doxygen [%s, %s]..." % (module, branch)

            self.run_op(path, 'make dox', lf)

            self.check_log(lf, 'doxygen', module, branch, 'warning |error ')


    # Make Debian package
    def make_deb(self, module, branch):
        print "make deb [%s, %s]..." % (module, branch)

        path = os.path.join(self.svn_dir, branch, module)
        lf = self.logfile('makedeb', module, branch)

        if os.path.exists(path + '/debian'):
            self.run_op(path, 'make deb', lf)

            self.check_log(lf, 'makedeb', module, branch, 'warning|error[ :]')


    # Make RPM package
    def make_rpm(self, module, branch):
        print "make rpm [%s, %s]..." % (module, branch)

        path = os.path.join(self.svn_dir, branch, module)
        lf = self.logfile('makerpm', module, branch)

        if os.path.exists(path + '/rpm'):
            self.run_op(path, 'make rpm', lf)

            self.check_log(lf, 'makerpm', module, branch, 'warning|error[ :]')


    def run_tests(self, svn_base, mods):
        for mod in mods:
            for b in mods[mod]:
                if self.do_svn: self.svn_update(svn_base, mod, b)
        for mod in mods:
            for b in mods[mod]:
                if self.do_ccheck:  self.run_ccheck(mod, b)
                if self.do_splint:  self.run_splint(mod, b)
                if self.do_doxygen: self.run_doxygen(mod, b)
                if self.do_build:   self.build_binaries(mod, b)
                if self.do_deb:     self.make_deb(mod, b)
                if self.do_rpm:     self.make_rpm(mod, b)


    def parse_svn(self, logfile):
        f = open(logfile, 'r')

        added = rev = 0
        for line in f:
            m = re.search('Checked out revision ([0-9]+)', line)
            if m:
                rev = m.group(1)

            if re.search('^A ', line, re.I):
                added += 1

        f.close()

        return '' + str(added) + ' files, revision ' + str(rev)


    def parse_log(self, logfile):
        f = open(logfile, 'r')

        loghtml = logfile.replace(self.root_dir, '', 1)

        (lines, err, warn) = (0, 0, 0)

        for line in f:
            lines += 1
            if re.search('error[ :]', line, re.I):
                err += 1
            if re.search('warning[ :]', line, re.I):
                warn += 1

        f.close()

        if err > 0:
            return '<font color=\"#ff6666\">[Failed]</font>' + \
                   ' with ' + str(err) + ' error(s) and ' \
                   + str(warn) + ' warning(s)' + \
                   '(<a href=\"' + loghtml + '\">logs</a>)'
        elif warn > 0:
            return '<font color=\"#999900\">[Failed]</font>' + \
                   ' with ' + str(warn) + ' warning(s)' + \
                   '(<a href=\"' + loghtml + '\">logs</a>)'
        elif lines == 0:
            return '<font color=\"#990000\">Fatal</font> - '\
                   + loghtml + ' is empty'
        else:
            return '<font color=\"#009900\">[Passed]</font>'


    def parse_ccheck(self, logfile):
        err = linecount(logfile)

        if err > 0:
            return '<font color=\"#ff6666\">[Failed]</font>' + \
                   ' with ' + str(err) + ' error(s) ' + \
                   '(<a href=\"log/' + logfile + '\">logs</a>)'
        else:
            return '<font color=\"#009900\">[Passed]</font>'


    def gen_status(self, mods):
        print "generating status page..."

        htmlfile = os.path.join(self.root_dir, 'index.html')
        title = "Daily builds"

        f = open(htmlfile, 'w')

        f.write('<html>\n')
        f.write('<head>\n')
        f.write('<title>' + title + '</title>\n')
        f.write('<link rel=\"stylesheet\" type=\"text/css\" '\
                'media=\"screen\" href=\"/css/std.css\" />\n')
        f.write('</head>\n')

        f.write('<body>\n')

        for mod in mods:
            for b in mods[mod]:

                f.write('<b>' + mod + ', branch ' + b + '</b>\n')
                f.write('<ul>\n')

                if self.do_svn:
                    lf = self.logfile('svn', mod, b)
                    f.write('<li>svn: ' \
                            + self.parse_svn(lf) + ' ' \
                            + self.parse_log(lf) \
                            + '</li>\n')

                if self.do_ccheck:
                    f.write('<li>ccheck: ' + \
                            self.parse_ccheck(self.logfile('ccheck', mod, b)) \
                            + '</li>\n')

                if self.do_splint:
                    f.write('<li>splint: ' + \
                            self.parse_ccheck(self.logfile('splint', mod, b)) \
                            + '</li>\n')

                if self.do_build:
                    f.write('<li>binaries: ' + \
                            self.parse_log(self.logfile('binaries', mod, b)) \
                            + '</li>\n')

                if self.do_deb:
                    lf = self.logfile('makedeb', mod, b)
                    if os.path.exists(lf):
                        f.write('<li>Debian: ' + \
                                self.parse_log(
                                    self.logfile('makedeb', mod, b)) \
                                + '</li>\n')

                if self.do_rpm:
                    lf = self.logfile('makedeb', mod, b)
                    if os.path.exists(lf):
                        f.write('<li>RPM: ' \
                                + self.parse_log(
                                    self.logfile('makerpm', mod, b)) \
                                + '</li>\n')

                if self.do_doxygen:
                    path = os.path.join(self.svn_dir, b, mod, 'mk/Doxyfile')
                    if os.path.exists(path):
                        f.write('<li>doxygen: ' \
                                + self.parse_log(
                                    self.logfile('doxygen', mod, b)))
                        f.write('<a href=\"' + \
                                'svn/' + b + '/' + mod + \
                                '-dox/html/index.html\">(html)</a>\n')

                f.write('</li>\n')
                f.write('</ul>\n')


        f.write('<hr>\n')
        f.write('Info:<br>' + CC_VER + '<br>' + UNAME + '<br>\n')

        f.write('<hr>\n')
        f.write('<i>Generated ' + time.ctime() + ' by ' \
                + USERNAME + '@' + HOSTNAME + ' using ' \
                + sys.argv[0] + ' version ' + VERSION + '</i><br><br>\n')

        f.write('</body></html>\n')

        f.close()


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

    if len (sys.argv) <= 1:
        usage()
        exit(2)

    config_file = sys.argv[1]

    print 'running ' + sys.argv[0] + ' v' + VERSION + \
          ' with config ' + config_file + ' on ' + HOSTNAME + '...'

    config = ConfigParser.ConfigParser()
    config.read(config_file)

    root_dir = config.get('core', 'root_dir')
    svn_base = config.get('core', 'svn_base')
    apps     = read_mods(config, 'apps')
    libs     = read_mods(config, 'libs')

    for a in apps:
        mods[a] = apps[a]
    for l in libs:
        mods[l] = libs[l]

    bld = Build(root_dir, config)

    bld.run_tests(svn_base, libs)
    bld.run_tests(svn_base, apps)

    bld.gen_status(mods)

    print 'build complete. logs at <http://' + HOSTNAME + '/build/>'
