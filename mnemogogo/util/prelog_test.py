#!/usr/bin/python

import sys, re
from os.path import exists

# load serial numbers
ids_path = 'IDS'

if not exists(ids_path):
    print >> sys.stderr, "could not find " + prelog_path
    sys.exit(1)

idfile = open(ids_path, 'rb')
serial_num = 0
serial_to_id = {}

id = idfile.readline()
while id != '':
    id = id.rstrip()
    serial_to_id[str(serial_num)] = id
    serial_num += 1
    id = idfile.readline()

idfile.close()

# process prelog file

prelog_path = 'PRELOG'

if not exists(prelog_path):
    print >> sys.stderr, "could not find " + prelog_path
    sys.exit(1)

prelog = open(prelog_path, 'r')

serialtoid_re = re.compile(r'R <(?P<id>[0-9]+)>')
line = prelog.readline()
while line != '':
    try:
	r = serialtoid_re.match(line)
	line = serialtoid_re.sub(
		'R ' + serial_to_id[r.group('id')], line)
	print >> sys.stdout, line
    except:
	print >> sys.stderr, "! ignoring log line: " + line

    line = prelog.readline()

prelog.close()

