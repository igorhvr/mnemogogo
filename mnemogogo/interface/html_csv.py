# $Id$
#
# Copyright (c) 2009 Timothy Bourke
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the "BSD License" which is distributed with the
# software in the file ../LICENSE.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the BSD
# License for more details.

#
# Basic exporter:
#   * Questions and Answers to separate html files.
#   * Statistics to a csv file.
#   * Collect images into subdirectory.
#

import mnemogogo
from os.path import exists, join, splitext
from os import mkdir, listdir, remove
import codecs

class Export(mnemogogo.Export):
    def open(self, start_time, num_cards):
	self.card_path = join(self.sync_path, 'cards')
	self.img_path = join(self.card_path, 'img')

	if not exists(self.sync_path): mkdir(self.sync_path)
	if not exists(self.card_path): mkdir(self.card_path)
	if not exists(self.img_path): mkdir(self.img_path)

	sfile = open(join(self.sync_path, 'start_time'), 'w')
	sfile.write(str(start_time) + '\n')
	sfile.close()

	self.statfile = open(join(self.sync_path, 'stats.csv'), 'w')
	self.statfile.write(str(num_cards) + '\n')

	self.idfile = open(join(self.sync_path, 'ids'), 'w')
	self.serial_num = 0

	for stale_html in listdir(self.card_path):
	    (_, ext) = splitext(stale_html)
	    if ext == '.html':
		remove(join(self.card_path, stale_html))
	
	self.add_style_file(join(self.card_path, 'style.css'))

    def close(self):

	catfile = codecs.open(join(self.sync_path, 'categories'),
			      'w', encoding='utf-8')

	size_in_bytes = (sum([len(c.encode('utf-8')) for c in self.categories])
			 + len(self.categories))
	catfile.write("%d\n" % len(self.categories))
	catfile.write("%d\n" % size_in_bytes)

	for cat in self.categories:
	    catfile.write(cat + '\n')
	catfile.close()

	self.statfile.close()
	self.idfile.close()
	self.collect_images()
    
    def write_config(self, config):
	cfile = open(join(self.sync_path, 'config'), 'w')
	for c in config.iteritems():
	    cfile.write("%s=%s\n" % c)
	cfile.close()

    def write(self, id, q, a, cat, stats, inverse_ids):
	# Write stats
	for s in self.learning_data:
	    fmt = "%%0%dx," % self.learning_data_len[s]
	    self.statfile.write(fmt % stats[s])
	self.statfile.write("%04x," % self.category_id(cat))

	try:
	    self.statfile.write("%04x," %
		self.id_to_serial[inverse_ids.next()])
	except StopIteration:
	    self.statfile.write("ffff,")
	except KeyError:
	    self.statfile.write("ffff,")

	#self.statfile.write("%d", (self.is_overlay(q) or self.is_overlay(a)))
	self.statfile.write("\n");

	self.idfile.write(id + '\n')

	# Handle images
	self.extract_image_paths(q)
	q = self.map_image_paths(q)
	self.extract_image_paths(a)
	a = self.map_image_paths(a)

	# Write card data
	cfile = codecs.open(join(self.card_path, 'Q%04x.htm' % self.serial_num),
			    'w', encoding='utf-8')
	cfile.write('<html>\n')
	cfile.write('<head>')
	cfile.write('<link rel="stylesheet" href="style.css" type="text/css">')
	cfile.write('</head>\n')
	cfile.write('<body id="%s" class="single">\n' % cat)
	cfile.write('<div id="cat">%s</div>\n' % cat)
	cfile.write('<div id="q" style="display: block;">%s</div>\n' % q)
	cfile.write('</body></html>\n')
	cfile.close()

	cfile = codecs.open(join(self.card_path, 'A%04x.htm' % self.serial_num),
			    'w', encoding='utf-8')
	cfile.write('<html>\n')
	cfile.write('<head>')
	cfile.write('<link rel="stylesheet" href="style.css" type="text/css">')
	cfile.write('</head>\n')
	if self.is_overlay(q) or self.is_overlay(a):
	    cfile.write('<body id="%s" class="single">\n' % cat)
	    cfile.write('<div id="cat">%s</div>\n' % cat)
	else:
	    cfile.write('<body id="%s" class="double">\n' % cat)
	    cfile.write('<div id="cat">%s</div>\n' % cat)
	    cfile.write('<div id="q" style="display: block;">%s</div>\n' % q)
	cfile.write('<div id="a" style="display: none;">%s</div>\n' % a)
	cfile.write('</body></html>\n')
	cfile.close()

	self.serial_num += 1

class Import(mnemogogo.Import):
    def open(self):
	self.statfile = open(join(self.sync_path, 'stats.csv'), 'r')
	self.statfile.readline() # skip the number of entries
	self.idfile = open(join(self.sync_path, 'ids'), 'r')
	self.num_stats = len(self.learning_data)
	self.line = 0
	self.serial_num = 0

    def close(self):
	self.statfile.close()
	self.idfile.close()

	prelog_path = join(self.sync_path, 'prelog')
	postlog_path = join(self.sync_path, 'log')

	if not exists(prelog_path):
	    return

	prelog = open(prelog_path, 'r')
	postlog = open(postlog_path, 'w')

	serialtoid_re = re.compile(r'R <(?P<id>[0-9]+)>')
	line = prelog.readline()
	while line != '':
	    try:
		r = serialtoid_re.match(line)
		line = serialtoid_re.sub(
			'R ' + self.serial_to_id[r.groups('id')], line)

		postlog.write(line)
	    except e:
		print >> sys.stderr, "ignoring log line: " + line

	    line = prelog.readline()

	prelog.close()
	postlog.close()

    def read(self):
	line = self.statfile.readline()
	if line == '': return None

	id = self.idfile.readline()
	id = id.rstrip()
	self.serial_to_id[str(self.serial_num)] = id
	self.line += 1
	fields = line.rstrip().split(',')

	stats = map(lambda x: int (x, 16), fields[0:self.num_stats])
	if len(stats) != self.num_stats:
	    self.error("stats.csv:" + str(self.line) + ":too few fields")

	self.serial_num += 1
	return (id, dict(zip(self.learning_data, stats)))

    def get_start_time(self):
	sfile = open(join(self.sync_path, 'stats.csv'), 'r')
	timestr = sfile.readline().rstrip()
	sfile.close()
	return int(timestr)

class HtmlCsv(mnemogogo.Interface):

    description = 'HTML+CSV: Basic'
    version = '0.5.0'

    def start_export(self, sync_path):
	return Export(self, sync_path)

    def start_import(self, sync_path):
	return Import(self, sync_path)

