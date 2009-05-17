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
from os import mkdir, listdir, remove, tempnam
from shutil import rmtree
from time import time
import codecs
import re

class BasicExport(mnemogogo.Export):

    single_cardfile = False

    extra_config = {}

    # abstract
    def write_data(self, card_path, serial_num, q, a, cat, is_overlay):
	pass

    def open(self, start_time, num_days, num_cards):
	if not exists(self.sync_path): mkdir(self.sync_path)
	self.card_path = join(self.sync_path, 'cards')

	if self.single_cardfile:
	    self.cardfile_path = join(self.sync_path, 'cards.db')
	    self.cardfile = open(self.cardfile_path, 'wb')
	else:
	    self.img_path = join(self.card_path, 'img')
	    self.snd_path = join(self.card_path, 'snd')

	    if not exists(self.card_path): mkdir(self.card_path)
	    if not exists(self.snd_path): mkdir(self.snd_path)

	    for stale_html in listdir(self.card_path):
		(_, ext) = splitext(stale_html)
		if (ext == '.htm' or ext == '.txt'):
		    remove(join(self.card_path, stale_html))
	    
	    self.add_style_file(join(self.card_path, 'style.css'))

	sfile = open(join(self.sync_path, 'start_time'), 'w')
	sfile.write(str(start_time) + '\n')
	sfile.close()
	self.extra_config['start_time'] = str(start_time);

	last_day = int(time() / 86400) + num_days;
	sfile = open(join(self.sync_path, 'last_day'), 'w')
	sfile.write(str(last_day) + '\n')
	sfile.close()
	self.extra_config['last_day'] = str(last_day);

	sfile = open(join(self.sync_path, 'prelog'), 'w')
	sfile.close()

	self.statfile = open(join(self.sync_path, 'stats.csv'), 'w')
	self.statfile.write(str(num_cards) + '\n')

	self.idfile = open(join(self.sync_path, 'ids'), 'w')
	self.serial_num = 0

    def close(self):

	catfile = codecs.open(join(self.sync_path, 'categories'),
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

	if self.single_cardfile:
	    tmpdir = tempnam()
	    mkdir(tmpdir)

	    self.collect_images(tmpdir)
	    for file in listdir(tmpdir):
		self.copy_to_cardfile(join('cards', 'img', file),
				      join(tmpdir, file))
	    rmtree(tmpdir)

	    mkdir(tmpdir)
	    self.collect_sounds(tmpdir)
	    for file in listdir(tmpdir):
		self.copy_to_cardfile(join('cards', 'snd', file),
				      join(tmpdir, file))

	    self.cardfile.close()
	else:
	    self.collect_images()
	    self.collect_sounds()
    
    def write_config(self, config):
	cfile = open(join(self.sync_path, 'config'), 'w')
	for c in config.iteritems():
	    cfile.write("%s=%s\n" % c)

	for c in self.extra_config.iteritems():
	    cfile.write("%s=%s\n" % c)

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

	#self.statfile.write("%d", (self.is_overlay(q) or self.is_overlay(a)))
	self.statfile.write("\n");

	self.idfile.write(id + '\n')

	# Handle images
	(q, a) = self.do_images(self.serial_num, q, a);
	(q, a) = self.do_sounds(self.serial_num, q, a);

	# Write card data
	self.write_data(self.card_path, self.serial_num, q, a, cat,
			 (self.is_overlay(q) or self.is_overlay(a)))

	self.serial_num += 1

    def write_to_cardfile(self, filename, data):
	self.cardfile.write(filename.encode('UTF-8') + '\n')
	dataenc = data.encode('UTF-8')
	self.cardfile.write('%d\n' % len(dataenc))
	self.cardfile.write(dataenc)
	self.cardfile.write('\n')

    def copy_to_cardfile(self, filename, srcpath):
	srcfile = open(srcpath, 'rb')
	data = srcfile.read()
	srcfile.close()

	self.cardfile.write(filename.encode('UTF-8') + '\n')
	self.cardfile.write('%d\n' % len(data))
	self.cardfile.write(data)
	self.cardfile.write('\n')

class Import(mnemogogo.Import):
    def open(self):
	self.statfile = open(join(self.sync_path, 'stats.csv'), 'r')
	self.statfile.readline() # skip the number of entries
	self.idfile = open(join(self.sync_path, 'ids'), 'r')
	self.num_stats = len(self.learning_data)
	self.line = 0
	self.serial_num = 0
	self.serial_to_id = {}

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
	sfile = open(join(self.sync_path, 'start_time'), 'r')
	timestr = sfile.readline().rstrip()
	sfile.close()
	return long(timestr)

# MnemoJoJo Exporter

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

class JoJoExport(BasicExport):
    raw_conversions = [
	    # ( regex ,	   replacement )
	    (r'(<br>)', r'<br/>'),
	    (r'</font>', r'</span>'),
	    (r'(<img[^>]*[^/])>', r'\1/>'),
	]
    conversions = []

    add_center_tag = False

    def convert(self, text):
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
	return text;

    def write_data(self, card_path, serial_num, q, a, cat, is_overlay):
	q = self.convert(q)
	a = self.convert(a)

	(ot, ct) = ('', '')
	if self.add_center_tag:
	    (ot, ct) = ('<center>', '</center>')

	qd = '<?xml version="1.0" encoding="UTF-8"?>\n'
	qd = qd + ('<body><p>%s%s%s</p></body>' % (ot, q, ct))

	ad = '<?xml version="1.0" encoding="UTF-8"?>\n<body>'
	if not is_overlay:
	    ad = ad + ('<p>%s%s%s</p><hr/>' % (ot, q, ct))
	ad = ad + ('<p>%s%s%s</p></body>' % (ot, a, ct))

	if self.single_cardfile:
	    self.write_to_cardfile(join('cards', 'Q%04x.htm' % serial_num), qd)
	    self.write_to_cardfile(join('cards', 'A%04x.htm' % serial_num), ad)
	else:
	    cfile = codecs.open(join(card_path, 'Q%04x.htm' % serial_num),
				'w', encoding='UTF-8')
	    cfile.write(qd);
	    cfile.close();
	    cfile = codecs.open(join(card_path, 'A%04x.htm' % serial_num),
				'w', encoding='UTF-8')
	    cfile.write(ad);
	    cfile.close();

    def do_images(self, serial_num, q, a):
	self.extract_image_paths(q)
	q = self.map_image_paths(q)
	self.extract_image_paths(a)
	a = self.map_image_paths(a)
	return (q, a)

    def do_sounds(self, serial_num, q, a):
	self.extract_sound_paths(q)
	q = self.map_sound_paths(q)
	self.extract_sound_paths(a)
	a = self.map_sound_paths(a)
	return (q, a)

class JoJoHexCsv(mnemogogo.Interface):
    max_width = 240
    max_height = 300
    max_size = 64
    ext = 'png'

    description = ('MnemoJoJo (%dx%d <%dk, %s)' %
		    (max_width, max_height, max_size, ext))
    version = '0.5.0'

    def start_export(self, sync_path):
	e = JoJoExport(self, sync_path)
	# e.single_cardfile = True
	e.img_max_width = self.max_width
	e.img_max_height = self.max_height - 43 
	e.img_to_landscape = True
	e.img_max_size = self.max_size * 1024;
	e.img_to_ext = self.ext
	return e

    def start_import(self, sync_path):
	return Import(self, sync_path)

# Plain Text Exporter

class TextExport(BasicExport):
    raw_conversions = [
	    # ( regex ,	   replacement )
	    (r'(<br/?>)', r'\n'),
	    (r'(<.*?>)', r''),
	    (r'&nbsp;', r' '),
	    (r'&lt;', r'<'),
	    (r'&gt;', r'>'),
	    (r'&amp;', r'&')
	]
    conversions = []

    def convert(self, text):
	if not self.conversions:
	    for (mat, rep) in self.raw_conversions:
		self.conversions.append((re.compile(mat, re.DOTALL), rep))

	for (mat, rep) in self.conversions:
	    text = mat.sub(rep, text)
	return text;

    def write_data(self, card_path, serial_num, q, a, cat, is_overlay):
	cfile = codecs.open(join(card_path, 'Q%04x.txt' % serial_num),
			    'w', encoding='UTF-8')
	if is_overlay:
	    cfile.write('answerbox: overlay;\n')
	else:
	    cfile.write('\n')
	cfile.write(self.convert(q))
	cfile.close()

	cfile = codecs.open(join(card_path, 'A%04x.txt' % serial_num),
			    'w', encoding='UTF-8')
	cfile.write(self.convert(a))
	cfile.close()

    def do_images(self, serial_num, q, a):
	return (q, a)

    def do_sounds(self, serial_num, q, a):
	return (q, a)

class TextCsv(mnemogogo.Interface):

    description = 'Text Only'
    version = '0.5.0'

    def start_export(self, sync_path):
	return TextExport(self, sync_path)

    def start_import(self, sync_path):
	return Import(self, sync_path)

