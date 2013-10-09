#!/usr/bin/python
## -*- encoding: utf-8 -*- vim:shiftwidth=4
##
## Split mbox input into monthly mbox files
## Copyright (c) 2013 SATOH Fumiyasu @ OSS Technology Corp., Japan
##               <http://www.OSSTech.co.jp/>
##
## Date: 2013-10-09, since 2013-10-09
## License: GNU General Public License version 3
##

## NOTE: This script supports mbox in mboxo and mboxrd format only.
##       See http://en.wikipedia.org/wiki/Mbox for details.

import getopt
import sys
import re
import os

## From name@example.jp  Wed May 22 17:58:31 2013
from_re = r'^From \S+  ?\S{3} (\S{3})  ?(\d\d?) \d\d:\d\d:\d\d (\d{4})$'

month_by_name = {
    'Jan':  1,
    'Feb':  2,
    'Mar':  3,
    'Apr':  4,
    'May':  5,
    'Jun':  6,
    'Jul':  7,
    'Aug':  8,
    'Sep':  9,
    'Oct': 10,
    'Nov': 11,
    'Dec': 12,
}

out_flags = os.O_CREAT | os.O_WRONLY | os.O_TRUNC
out_mode = 0600

usage = """Usage: %(program_name)s OUTPUT_MBOX_PREFIX < INPUT_MBOX

Options:
 -m, --mode MODE
   File mode for output mbox files (default: 0%(out_mode)03o)
 -a, --append
   Append to output mbox files if exists (default: Overwrite existent files)
 -h, --help
   Show this message
""" % {
    'program_name':		sys.argv[0],
    'out_mode':			out_mode,
}


try:
    opts, args = getopt.getopt(sys.argv[1:],
	'hm:a',
	[
	    'help',
	    'mode=',
	    'append=',
	])
except getopt.error, msg:
    perr("%s", msg)
    sys.exit(code_on_usage_error)

for opt, arg in opts:
    if opt in ('-h', '--help'):
	print usage
	sys.exit(0)
    if opt in ('-m', '--mode'):
	out_mode = int(arg, 8)
    if opt in ('-a', '--append'):
	out_flags |= os.O_APPEND
	out_flags &= ~os.O_TRUNC

if len(args) != 1:
    print usage
    sys.exit(1)

out_prefix = args[0]

## ======================================================================

out_fds = {}

for line in sys.stdin:
    m = re.match(from_re, line)
    if m:
	year = int(m.group(3))
	month = month_by_name.get(m.group(1))
	mday = int(m.group(2))
	if year > 1970 and month and mday >= 1 and mday <= 31:
	    out_fname = '%s%d%02d' % (out_prefix, year, month)
	    try:
		out_fd = out_fds[out_fname]
	    except KeyError:
		out_fd = out_fds[out_fname] = os.open(out_fname, out_flags, out_mode)

    os.write(out_fd, line)

sys.exit(0)

