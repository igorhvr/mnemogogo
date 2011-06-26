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

import mnemosyne.core
import mnemosyne.pyqt_ui
import sys
import os
import os.path
import shutil
import re
import itertools
import random
import traceback
from qt import *

interface_classes = []

read_log_file = False
max_config_size = 50

def phonejoin(paths):
    if len(paths) == 0: return ""

    r = paths[0]
    for p in paths[1:]:
	r = "/".join([r, p])
	if ((len(r) > 0) and ((r[-1] == '/') or r[-1] == '\\')):
	    r = r[0:-1]

    return r

class _RegisteredInterface(type):
    def __new__(meta, classname, bases, classdict):
	newClass = type.__new__(meta, classname, bases, classdict)

	if classname != "Interface":
	    interface_classes.append(newClass)

	return newClass

learning_data = [
    'grade',
    'easiness',
    'acq_reps',
    'ret_reps',
    'lapses',
    'acq_reps_since_lapse',
    'ret_reps_since_lapse',
    'last_rep',
    'next_rep',
    'unseen',
    ]

learning_data_len = {
    'grade'		    : 1,
    'easiness'		    : 4,
    'acq_reps'		    : 4,
    'ret_reps'		    : 4,
    'lapses'		    : 4,
    'acq_reps_since_lapse'  : 4,
    'ret_reps_since_lapse'  : 4,
    'last_rep'		    : 8,
    'next_rep'		    : 8,
    'unseen'		    : 1,
    }

easiness_accuracy = 1000

######################################################################
# Interfaces

class InterfaceError(Exception):
    pass

class Job:
    learning_data = learning_data
    learning_data_len = learning_data_len

    def __init__(self, interface, sync_path):
	self.interface = interface
	self.sync_path = sync_path
	self.percentage_complete = 0

    # implement in plugin
    def close(self):
	pass

    def error(self, msg):
	title = self.interface.description + ' interface: '
	raise InterfaceError(title + msg)

class Export(Job):
    re_img_split = re.compile(r'(<img.*?>)')
    re_img = re.compile( r'(?P<all>(?P<before><img\s+[^>]?)'
			+ '((height|width)\s*=\s*"?[0-9]*"?\s*)*'
			+ 'src\s*=\s*"(?P<path>[^"]*)"'
			+ '((height|width)\s*=\s*"?[0-9]*"?)*'
			+ '(?P<after>[^>]*/?>))',
			re.IGNORECASE + re.MULTILINE + re.DOTALL)

    re_snd_split = re.compile(r'(<sound.*?>)')
    re_snd = re.compile( r'(?P<all>(?P<before><sound\s+[^>]?)'
			+ 'src\s*=\s*"(?P<path>[^"]*)"'
			+ '(?P<after>[^>]*/?>))',
			re.IGNORECASE + re.MULTILINE + re.DOTALL)

    def __init__(self, interface, sync_path):
	Job.__init__(self, interface, sync_path)

	self.categories = []
	self.imgs = {}
	self.img_cnt = 0
	self.snds = {}
	self.snd_cnt = 0
	self.name_with_numbers = True

	self.img_max_width = None
	self.img_max_height = None
	self.img_to_landscape = False
	self.img_to_ext = None

    # implement in plugin
    def open(self, start_date, num_days, num_cards, params):
	pass

    # implement in plugin
    def write(self, id, q, a, cat, stats, inverse_ids):
	pass

    def write_config(self, config):
	pass

    # # # Utility routines # # #

    def is_overlay(self, text):
	r = False
	abox = mnemosyne.pyqt_ui.card_prop.card_props(text).get('answerbox')
	return (abox == 'overlay')
    
    def remove_overlay(self, text):
	return mnemosyne.pyqt_ui.card_prop.re_card_props.sub('', text)

    def call_hooks(self, target, hook):
	if hook in mnemosyne.core.function_hooks:
	    for f in mnemosyne.core.function_hooks[hook]:
		f(target)

    def tidy_files(self, dst_subdir, list):
	dstpath = os.path.join(self.sync_path, dst_subdir)

	for file in os.listdir(dstpath):
	    if phonejoin([dst_subdir, file]) not in list:
		try:
		    os.remove(os.path.join(dstpath, file))
		except:
		    log_warning ("Could not remove: %s" % file)

    def tidy_images(self, dst_subdir):
	self.tidy_files(dst_subdir, self.imgs.values())

    def tidy_sounds(self, dst_subdir):
	self.tidy_files(dst_subdir, self.snds.values())
    
    def add_style_file(self, dstpath):
	shutil.copy(os.path.join(self.gogo_dir, 'style.css'), dstpath)

    def add_active_categories(self):
	mcats = mnemosyne.core.get_categories()
	cats = []
	for mc in mcats:
	    if mc.active:
		cats.append(mc.name)

	cats.sort()
	map(self.category_id, cats)

    def category_id(self, cat):
	try:
	    i = self.categories.index(cat)
	except ValueError:
	    i = len(self.categories)
	    self.categories.append(cat)
	return i

    def map_paths(self, reg, re_split, text, mapping):
	stext = re_split.split(text)
	ntext = []

	for ele in stext:
	    r = reg.match(ele)
	    if r:
		ele = (r.group('before')
		       + ' src="' + mapping[r.group('path')]
		       + '" ' + r.group('after'))
	    ntext.append(ele)

	return ''.join(ntext)

    def convert_img(self, src, dst_subdir, dst_name, dst_ext):
	dst_file = dst_name + '.' + dst_ext
	dst = os.path.join(self.sync_path, dst_subdir, dst_file)

	if not os.path.exists(src):
	    log_warning("image not found: %s" % src)
	    return (False, 'NOTFOUND.PNG')

	if (os.path.exists(dst) and
		(os.path.getmtime(src) < os.path.getmtime(dst))):
	    return (False, dst_file)

	im = QImage(src)
	(width, height) = (im.width(), im.height())

	if (self.img_to_landscape and self.img_max_width
		and float(width) > (height * 1.2)
		and width > self.img_max_width):
	    matrix = QWMatrix()
	    im = im.xForm(matrix.rotate(90))
	    (width, height) = (im.width(), im.height())
	
	(wratio, hratio) = (1.0, 1.0)
	if self.img_max_width and width > self.img_max_width:
	    wratio = width / float(self.img_max_width);
	
	if self.img_max_height and height > self.img_max_height:
	    hratio = height / float(self.img_max_height);
	
	ratio = max(wratio, hratio)
	if ratio != 1.0:
	    im = im.smoothScale(int(width / ratio), int(height / ratio))
	    (width, height) = (im.width(), im.height())
	
	if self.img_max_size:
	    tmpdstdir = os.tempnam()
	    os.mkdir(tmpdstdir)
	    tmpdst = os.path.join(tmpdstdir, '_gogo_scaling.png')

	    r = im.save(tmpdst, 'PNG')
	    if not r:
		log_warning('unable to export the image: %s' % src)
		return (True, dst_file)

	    (nwidth, nheight) = (width, height)
	    while (os.path.getsize(tmpdst) > self.img_max_size):
		(owidth, oheight) = (nwidth, nheight)
		scale = 0.9
		while ((nwidth == owidth or nheight == oheight)
		       and scale > 0.0):
		    (nwidth, nheight) = (int(nwidth * scale),
					 int(nheight * scale))
		    scale = scale - .1

		if nwidth > 0 and nheight > 0:
		    im = im.smoothScale(nwidth, nheight)
		    im.save(tmpdst, 'PNG')
		else:
		    break;
	    shutil.rmtree(tmpdstdir)

	im.save(dst, dst_ext.upper())
	return (True, dst_file)

    def handle_images(self, dst_subdir, text):
	for r in self.re_img.finditer(text):
	    src = r.group('path')

	    if not (src in self.imgs):
		(src_root, src_ext) = os.path.splitext(os.path.basename(src))
		if self.name_with_numbers:
		    name = '%08X' % self.img_cnt
		else:
		    name = src_root.encode('punycode').upper().replace(' ', '_')
		self.img_cnt += 1

		(moved, dst) = self.convert_img(src, dst_subdir, name,
			self.img_to_ext)
		if moved:
		    self.call_hooks(os.path.join(
			self.sync_path, dst_subdir, dst), 'gogo_img')

		self.imgs[src] = phonejoin([dst_subdir, dst])

	return self.map_paths(self.re_img, self.re_img_split, text, self.imgs)

    def handle_sounds(self, dst_subdir, text):
	ntext = []

	for r in self.re_snd.finditer(text):
	    src = r.group('path')

	    if src in self.snds:
		ntext.append('<sound src="%s" />' % self.snds[src])
	    else:
		(src_root, src_ext) = os.path.splitext(os.path.basename(src))
		if self.name_with_numbers:
		    name = '%08X' % self.snd_cnt
		else:
		    name = src_root.encode('punycode').upper().replace(' ', '_')
		self.snd_cnt += 1

		dst = name + src_ext
		dst_path = os.path.join(self.sync_path, dst_subdir, dst)
		try:
		    shutil.copy(src, dst_path)
		    self.snds[src] = phonejoin([dst_subdir, dst])
		    self.call_hooks(dst_path, 'gogo_snd')
		    ntext.append('<sound src="%s" />' % self.snds[src])

		except IOError:
		    log_warning("sound file not found: %s" % src)
	
	ntext.append(self.re_snd_split.sub('', text))
	return '\n'.join(ntext)

class Import(Job):
    def __iter__(self):
	self.open()
	return self

    def next(self):
	r = self.read()

	if r is None:
	    self.close()
	    raise StopIteration

	return r

    # implement in plugin
    def open(self):
	pass

    # implement in plugin
    def read(self):
	return None

    # implement in plugin
    def get_start_date(self):
	raise Exception('The plugin does not implement get_start_date!')

class Interface:
    __metaclass__ = _RegisteredInterface

    # # # Override # # #

    description = 'unknown'
    version = '0.0.0'

    def load(self):
	pass

    def unload(self):
	pass

    def start_export(self, sync_path):
	return Export(self, sync_path)

    def start_import(self, sync_path):
	return Import(self, sync_path)


######################################################################
# Implementation

class Mnemogogo(Exception):
    pass

interfaces = []

def register_interfaces():
    basedir = mnemosyne.core.get_basedir()
    interface_dir = unicode(os.path.join(basedir,
			    "plugins", "mnemogogo", "interface"))
    
    for file in os.listdir(interface_dir):
	if (not file.endswith(".py")) or file.startswith("_"):
	    continue
        
	try:
	    __import__("mnemogogo.interface." + file[:-3])
	except: raise Mnemogogo('Error initialising interface: ' + file
				+ '\n' + traceback.format_exc())

    for iface in interface_classes:
	try:
	    obj = iface()
	    name = iface.__name__
	    desc = obj.description
	except: raise Mnemogogo('Error registering interface: ' + file
				+ '\n' + traceback.format_exc())

	interfaces.append({ 'name' : name,
			    'description' : desc,
			    'object' : obj })

    return interfaces

def list_interfaces():
    return interfaces

# These generators were adapted from the rebuild_revision_queue
# function in the Mnemosyne 1.1.1 core module, which was written
# by <Peter.Bienstman@UGent.be>.
# NB: this function could try harder to avoid including inverses.
def extra_cards(items):

    wrong_cards_0 = (i for i in items if i.is_due_for_acquisition_rep() \
					 and i.lapses > 0
					 and i.grade == 0)

    wrong_cards_1 = (i for i in items if i.is_due_for_acquisition_rep() \
					 and i.lapses > 0
					 and i.grade == 1)

    not_committed_0 = (i for i in items if i.is_due_for_acquisition_rep() \
					   and i.lapses == 0
					   and i.unseen == False
					   and i.grade == 0)

    not_committed_1 = (i for i in items if i.is_due_for_acquisition_rep() \
					   and i.lapses == 0
					   and i.unseen == False
					   and i.grade == 1)

    unseen = (i for i in items if i.is_due_for_acquisition_rep() \
				   and i.lapses == 0
                                   and (i.unseen or i.grade not in [0, 1]))
    
    return itertools.chain(wrong_cards_0, wrong_cards_1, not_committed_0,
			   not_committed_1, unseen)

# Return enough cards for rebuild_revision_queue on the mobile device to
# work with for the given number of days.
def cards_for_ndays(days = 0, extra = 1.00):
            
    items = mnemosyne.core.get_items()
    random.shuffle(items)
    revision_queue = []

    if len(items) == 0:
        return revision_queue

    limit = (mnemosyne.core.get_config("grade_0_items_at_once")
	     * (days + 1) * extra)

    time_of_start = mnemosyne.core.get_time_of_start()
    time_of_start.update_days_since()
    scheduled_cards = (i for i in items if i.is_due_for_retention_rep(days))

    return itertools.chain(scheduled_cards,
			   itertools.islice(extra_cards(items), limit))

num_suffix_re = re.compile(r'^(.*?)([0-9]*)$')
def get_fresh_id(cardid, used_ids):
    r = num_suffix_re.match(cardid)
    prefix = r.group(1)
    suffix_str = r.group(2)
    if suffix_str == '': suffix_str = "0"

    suffix = int(suffix_str) + 1
    while used_ids.has_key(prefix + str(suffix)):
	suffix += 1

    return prefix + str(suffix)

def eliminate_duplicate_ids():
    items = mnemosyne.core.get_items()

    checked = {}
    for item in items:
	checked[item.id] = False

    for item in items:
	if type(item.id) not in [str, unicode]:
	    log_info ("Converting id to string: %s" % item.id)
	    item.id = unicode(item.id)

	if checked[item.id]:
	    newid = get_fresh_id(item.id, checked)
	    log_info ("Fixing duplicate id: %s -> %s" % (item.id, newid))
	    item.id = newid
	checked[item.id] = True

def card_to_stats(card):
    stats = {}
    for f in learning_data:
	if f == 'easiness':
	    stats[f] = int(round(getattr(card, f) * easiness_accuracy))
	else:
	    stats[f] = int(getattr(card, f))
    return stats

def stats_to_card(stats, card):
    for f in learning_data:
	if f == 'easiness':
	    setattr(card, f, float(stats[f]) / easiness_accuracy)
	elif f == 'unseen':
	    setattr(card, f, bool(stats[f]))
	else:
	    setattr(card, f, int(stats[f]))

def process(card, which):
    hook = "gogo_" + which
    text = mnemosyne.core.preprocess(getattr(card, which))
    if hook in mnemosyne.core.function_hooks:
	for f in mnemosyne.core.function_hooks[hook]:
	    text = f(text, card)
    return text

def do_export(interface, num_days, sync_path, progress_bar=None,
	      extra = 1.00, max_width = 240, max_height = 300, max_size = 64):
    basedir = mnemosyne.core.get_basedir()

    eliminate_duplicate_ids()
    exporter = interface.start_export(sync_path)
    exporter.gogo_dir = unicode(os.path.join(basedir, "plugins", "mnemogogo"))
    exporter.progress_bar = progress_bar

    config = {
	    'grade_0_items_at_once'
		: mnemosyne.core.get_config('grade_0_items_at_once'),
	    'logging'
		: "%d" % mnemosyne.core.get_config('upload_logs'),
	    'database'
		: get_database().encode('punycode')[-max_config_size:],
	}

    params = {
	    'max_width' : max_width,
	    'max_height' : max_height,
	    'max_size' : max_size,
	}

    cards = list(cards_for_ndays(num_days, extra))
    cards.sort(key=mnemosyne.core.Item.sort_key_interval)
    time_of_start = mnemosyne.core.get_time_of_start()
    items = mnemosyne.core.get_items()

    total = len(cards)
    current = 0

    exporter.open(time_of_start.date, num_days, len(cards), params)
    exporter.id_to_serial = dict(zip((i.id for i in cards),
				 range(0, len(cards))))
    exporter.write_config(config)
    for card in cards:
	stats = card_to_stats(card)
	q = process(card, "q")
	a = process(card, "a")
	inverses = (i.id for i in cards
		    if mnemosyne.core.items_are_inverses(card, i))
	exporter.write(card.id, q, a, card.cat.name, stats, inverses)

	if progress_bar:
	    progress_bar.setProgress(exporter.percentage_complete)

    exporter.close()

def adjust_start_date(import_start_date):

    time_of_start = mnemosyne.core.get_time_of_start()
    db_start_date = time_of_start.date
    offset = (import_start_date - db_start_date).days

    if offset < 0:
	log_error(
	    "database time_of_start is later than import time_of_start!")

	# The database time_of_start should only ever be pushed back earlier
	# into time (by an import with learning data).
	#
	# The reason we can't have:
	#	t = time.mktime(import_start_date.timetuple())
	#	new_time_of_start = mnemosyne.core.StartTime(t)
	#	mnemosyne.core.set_time_of_start(new_time_of_start)
	#	items = mnemosyne.core.get_items()
	#	offset = abs(offset)
	#	for item in items:
	#	    item.last_rep += offset
	#	    item.next_rep += offset
	#	return 0
	#
	# is because there is no mnemosyne.core.set_time_of_start() function.

    return offset

def do_import(interface, sync_path, progress_bar=None):
    importer = interface.start_import(sync_path)
    importer.progress_bar = progress_bar

    import_config = importer.read_config()
    if (import_config.has_key('database')):
	curr_database = get_database().encode('punycode')[-max_config_size:]
	load_database = import_config['database']
	if load_database != curr_database:
	    raise Mnemogogo("These cards were exported from '"
		    + load_database
		    + "', but the current database is '"
		    + curr_database
		    + "'!")
 
    offset = adjust_start_date(importer.get_start_date(import_config))

    new_stats = []
    for (id, stats) in importer:
	card = mnemosyne.core.get_item_by_id(id)
	if card is not None:
	    if offset != 0:
		stats['last_rep'] += offset
		stats['next_rep'] += offset
	    new_stats.append((card, stats))
	else:
	    log_error("Quietly ignoring card with missing id: %s" % id)

	if (progress_bar):
	    progress_bar.setProgress(importer.percentage_complete)

    # Only update the database if the entire read is successful
    for (card, stats) in new_stats:
	stats_to_card(stats, card)

    shutil.move(os.path.join(sync_path, 'STATS.CSV'),
		os.path.join(sync_path, 'OLDSTATS.CSV'))

    # Import logging details
    logpath = os.path.join(sync_path, 'LOG')
    if os.path.exists(logpath):
	log = open(logpath)

	mnemosyne.core.logger.info('mnemogogo: starting log import')
	line = log.readline()
	while line != '':
	    mnemosyne.core.logger.info(line.rstrip('\n'))
	    line = log.readline()
	mnemosyne.core.logger.info('mnemogogo: finished log import')

	log.close()
	os.remove(logpath)

def get_database():
    try:
	mempath =  mnemosyne.core.get_config("path")
    except KeyError:
	mempath = "default.mem"

    return mempath[:-4]

def get_config_key():
    mempath = get_database()

    if mempath == "default":
	config_key = "mnemogogo"
    else:
	config_key = "mnemogogo:" + mempath

    return config_key

def log_info(msg):
    mnemosyne.core.logger.info("mnemogogo: " + msg)

def log_warning(msg):
    mnemosyne.core.logger.warning("mnemogogo: " + msg)

def log_error(msg):
    global read_log_file
    read_log_file = True
    mnemosyne.core.logger.error("mnemogogo: " + msg)

def check_log_status():
    global read_log_file
    return read_log_file

def clear_log_status():
    global read_log_file
    read_log_file = False

