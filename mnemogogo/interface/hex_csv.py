#
# Copyright (C) 2009 Timothy Bourke
# 
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
# 
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
# 
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc., 59
# Temple Place, Suite 330, Boston, MA 02111-1307 USA
#

#
# Basic exporter:
#   * Questions and Answers to a single file.
#   * Statistics to a csv file.
#   * Collect images into subdirectory.
#

import mnemogogo
from os.path import exists, join, splitext
from os import mkdir, listdir, remove, tempnam
from shutil import rmtree
import time
import calendar
import datetime
import codecs
import re
import sys

class BasicExport(mnemogogo.Export):

    extra_config = {}
    title_height_pixels = 43

    # abstract
    def write_data(self, cardfile, serial_num, q, a, cat, is_overlay):
	pass

    def open(self, start_date, num_days, num_cards, params):
	if not exists(self.sync_path): mkdir(self.sync_path)
	self.num_cards = num_cards

	self.cardfile_path = join(self.sync_path, 'CARDS')
	try:
	    self.cardfile = open(self.cardfile_path, 'wb')
	except Exception, e:
	    self.error("Export failed!\n\n(" + str(e) + ")")
	self.cardfile.write(str(num_cards) + '\n')

	self.img_path = join(self.sync_path, 'IMG')
	if not exists(self.img_path):
	    mkdir(self.img_path)

	self.snd_path = join(self.sync_path, 'SND')
	if not exists(self.snd_path):
	    mkdir(self.snd_path)

	self.img_max_width = params['max_width']
	self.img_max_height = params['max_height'] - self.title_height_pixels
	self.img_max_size = params['max_size'] * 1024;

	# database time_of_start:
	#   start_date is used only for comparison on import
	#   start_days is used in Mnemojojo for calculations
	#	       (it is start_date in days since the epoch)
	self.extra_config['start_date'] = start_date.isoformat()
	self.extra_config['start_days'] = int(
	    calendar.timegm(start_date.timetuple()) / 86400)

	last_day = int(time.time() / 86400) + num_days;
	self.extra_config['last_day'] = str(last_day);

	sfile = open(join(self.sync_path, 'PRELOG'), 'wb')
	sfile.close()

	self.statfile = open(join(self.sync_path, 'STATS.CSV'), 'wb')
	self.statfile.write(str(num_cards) + '\n')

	self.idfile = open(join(self.sync_path, 'IDS'), 'wb')
	self.serial_num = 0

	self.add_active_categories()

    def close(self):

	catfile = codecs.open(join(self.sync_path, 'CATS'),
			      'w', encoding='UTF-8')

	size_in_bytes = (sum([len(c.encode('UTF-8')) for c in self.categories])
			 + len(self.categories))
	catfile.write("%d\n" % len(self.categories))
	catfile.write("%d\n" % size_in_bytes)

	for cat in self.categories:
	    catfile.write(cat + '\n')
	catfile.close()

	self.statfile.close()
	self.idfile.close()
	self.cardfile.close()

	self.tidy_images('IMG')
	self.tidy_sounds('SND')
    
    def write_config(self, config):
	cfile = open(join(self.sync_path, 'CONFIG'), 'wb')
	for (n, v) in config.iteritems():
	    cfile.write("%s=%s\n" % (str(n)[:30], str(v)[:50]))

	for (n, v) in self.extra_config.iteritems():
	    cfile.write("%s=%s\n" % (str(n)[:30], str(v)[:50]))

	cfile.close()

    def write(self, id, q, a, cat, stats, inverse_ids):
	# Write stats
	for s in self.learning_data:
	    fmt = "%%0%dx," % self.learning_data_len[s]
	    self.statfile.write(fmt % stats[s])
	cat_id = self.category_id(cat)
	self.statfile.write("%04x" % cat_id)

	try:
	    self.statfile.write(",%04x" %
		self.id_to_serial[inverse_ids.next()])
	except StopIteration:
	    self.statfile.write(",ffff")
	except KeyError:
	    self.statfile.write(",ffff")

	self.statfile.write("\n");

	self.idfile.write(id + '\n')

	# Handle images
	(q, a) = self.do_images(self.serial_num, q, a);
	(q, a) = self.do_sounds(self.serial_num, q, a);

	# Write card data
	self.write_data(self.cardfile, self.serial_num, q, a, cat,
			 (self.is_overlay(q) or self.is_overlay(a)))

	self.serial_num += 1
	self.percentage_complete = (self.serial_num * 80) / self.num_cards
	    # cludge: leave 20% for images/sounds

    def write_to_cardfile(self, data):
	dataenc = data.encode('UTF-8')
	self.cardfile.write('%d\n' % len(dataenc))
	self.cardfile.write(dataenc)
	self.cardfile.write('\n')

class Import(mnemogogo.Import):
    def open(self):
	try:
	    statpath = join(self.sync_path, 'STATS.CSV')
	    try:
		self.statfile = open(statpath, 'r')
	    except IOError, e:
		self.error("Cannot open '%s'!\n\n(%s)" %
			   (self.statpath, str(e)))
	except IOError:
	    self.error('Could not find: ' + statpath)

	self.num_cards = int(self.statfile.readline())
	try:
	    self.idfile = open(join(self.sync_path, 'IDS'), 'r')
	except IOError, e:
	    self.error("Cannot open '%sIDS'!\n\n(%s)" %
		       (self.sync_path, str(e)))
	self.num_stats = len(self.learning_data)
	self.line = 0
	self.serial_num = 0
	self.serial_to_id = {}

    def close(self):
	self.statfile.close()
	self.idfile.close()

	prelog_path = join(self.sync_path, 'PRELOG')
	postlog_path = join(self.sync_path, 'LOG')

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
			'R ' + self.serial_to_id[r.group('id')], line)
		postlog.write(line)
	    except:
		mnemogogo.log_warning("ignoring log line: " + line)

	    line = prelog.readline()

	prelog.close()
	remove(prelog_path)

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
	self.percentage_complete = (self.serial_num * 100) / self.num_cards

	return (id, dict(zip(self.learning_data, stats)))

    def read_config(self):
	config = {}

	try:
	    cfile = open(join(self.sync_path, 'CONFIG'), 'rb')
	except IOError, e:
	    self.error("Cannot open '%sCONFIG'!\n\n(%s)" %
		       (self.sync_path, str(e)))

	configline_re = re.compile(r'(?P<name>[^=]+)=(?P<value>.*)')

	line = cfile.readline()
	while line != '':
	    r = configline_re.match(line.rstrip())
	    config[r.group('name')] = r.group('value')

	    line = cfile.readline()

	cfile.close()
	return config

    def get_start_date(self, config=None):
	if (config is None):
	    config = self.read_config()
	[year, month, day] = config['start_date'].split('-')
	return datetime.date(int(year), int(month), int(day))

# Mnemojojo Exporter

def make_map_color_re(name, rgb):
    return ((r'<font\s+color\s*=\s*"%s"\s*/?>' % name),
	    (r'<span style="color: %s;">' % rgb))

color_map = [
    ("pink",	    "#ffc0cb"),
    ("magenta",	    "#ff00ff"),
    ("purple",	    "#800080"),
    ("indigo",	    "#4b0082"),
    ("blue",	    "#0000ff"),
    ("darkblue",    "#00008b"),
    ("navy",	    "#000080"),
    ("lightblue",   "#add8e6"),
    ("lightcyan",   "#e0ffff"),
    ("cyan",	    "#00ffff"),
    ("darkcyan",    "#008b8b"),
    ("lightgreen",  "#90ee90"),
    ("green",	    "#008000"),
    ("darkgreen",   "#006400"),
    ("lightyellow", "#ffffe0"),
    ("yellow",	    "#ffff00"),
    ("orange",	    "#ffa500"),
    ("red",	    "#ff0000"),
    ("brown",	    "#a52a2a"),
    ("darkred",	    "#8b0000"),
    ("white",	    "#ffffff"),
    ("lightgrey",   "#d3d3d3"),
    ("silver",	    "#c0c0c0"),
    ("darkgray",    "#a9a9a9"),
    ("gray",	    "#808080"),
    ("black",	    "#000000"),
]

class JojoExport(BasicExport):
    raw_conversions = [
	    # ( regex ,	   replacement )
	    (r'(<br>)', r'<br/>'),
	    (r'(</?\s*(table|td|tr)\s*>)( *<br/>)+', r'\1'),
	    (r'</font>', r'</span>'),
	    (r'(<img[^>]*[^/])>', r'\1/>'),
	]
    conversions = []

    add_center_tag = False

    def convert(self, text):
	text = self.remove_overlay(text)

	if not self.conversions:
	    for (name, rgb) in color_map:
		self.raw_conversions.append(make_map_color_re(name, rgb))

	    self.raw_conversions.append(
		(r'<font\s+color\s*=\s*"([^"]*)"\s*/?>',
		 r'<span style="color: \1;">'))

	    for (mat, rep) in self.raw_conversions:
		self.conversions.append(
		    (re.compile(mat, re.DOTALL | re.IGNORECASE), rep))

	for (mat, rep) in self.conversions:
	    text = mat.sub(rep, text)

	return mnemogogo.htmltounicode(text);

    def write_data(self, cardfile, serial_num, q, a, cat, is_overlay):
	q = self.convert(q)
	a = self.convert(a)

	(ot, ct) = ('', '')
	if self.add_center_tag:
	    (ot, ct) = ('<center>', '</center>')

	if is_overlay:
	    self.cardfile.write('1\n')
	else:
	    self.cardfile.write('0\n')

	self.write_to_cardfile(('%s%s%s' % (ot, q, ct)))
	self.write_to_cardfile(('%s%s%s' % (ot, a, ct)))

    def do_images(self, serial_num, q, a):
	q = self.handle_images('IMG', q)
	a = self.handle_images('IMG', a)
	return (q, a)

    def do_sounds(self, serial_num, q, a):
	q = self.handle_sounds('SND', q)
	a = self.handle_sounds('SND', a)
	return (q, a)

class JojoHexCsv(mnemogogo.Interface):
    ext = 'PNG'

    description = ('Mnemojojo (J2ME)')
    version = '1.0.0'

    def start_export(self, sync_path):
	e = JojoExport(self, sync_path)
	e.img_to_landscape = False
	e.img_to_ext = self.ext
	e.name_with_numbers = False
	return e

    def start_import(self, sync_path):
	return Import(self, sync_path)

class DodoHexCsv(mnemogogo.Interface):
    ext = 'PNG'

    description = ('Mnemododo (Android)')
    version = '1.0.0'

    def start_export(self, sync_path):
	e = JojoExport(self, sync_path)
	e.img_to_landscape = False
	e.img_to_ext = self.ext
	e.name_with_numbers = False
	return e

    def start_import(self, sync_path):
	return Import(self, sync_path)

