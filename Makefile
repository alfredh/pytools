#
# Makefile
#
# Copyright (C) 2005 - 2009 Alfred E. Heggestad
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License version 2 as
#    published by the Free Software Foundation.
#

TOOLS	:= build.py ccheck.py
DEST	:= /usr/local/bin

default:
	@echo "run 'make install'"

install:
	@mkdir -p $(DEST)
	@install -m 755 $(TOOLS) $(DEST)
