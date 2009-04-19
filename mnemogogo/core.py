#
# Copyright (c) 2009 Timothy Bourke
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the "BSD License" which is distributed with the
# software in the file LICENSE.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the BSD
# License for more details.
#

import mnemosyne.core
import mnemosyne.pyqt_ui
import sys
import os
import os.path
import shutil
import re
import itertools
from sets import Set
import traceback

interface_classes = []

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
    'last_rep'		    : 4,
    'next_rep'		    : 4,
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

    # implement in plugin
    def open(self, start_time, num_cards):
	pass

    # implement in plugin
    def close(self):
	pass

    def error(self, msg):
	title = self.interface.description + ' interface: '
	raise InterfaceError(title + msg)

class Export(Job):
    categories = []
    imgs = []

    re_img_split = re.compile(r'(<img.*?>)')
    re_img = re.compile( r'(?P<all>(?P<before><img\s+[^>]?)'
			+ 'src\s*=\s*"(?P<path>[^"]*)"'
			+ '(?P<after>[^>]*/?>))',
			re.IGNORECASE + re.MULTILINE + re.DOTALL)

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
	mnemosyne.pyqt_ui.card_prop.re_card_props.sub('', text)
	return text

    def extract_image_paths(self, text):
	for r in self.re_img.finditer(text):
	    self.imgs.append(r.group('path'))

    def map_image_paths(self, text,
			f=(lambda x: os.path.join('img', os.path.basename(x)))):
	stext = self.re_img_split.split(text)
	ntext = []

	for ele in stext:
	    r = self.re_img.match(ele)
	    if r:
		ele = (r.group('before')
		       + ' src="' + f(r.group('path'))
		       + '" ' + r.group('after'))
	    ntext.append(ele)

	return ''.join(ntext)

    def call_hooks(self, target, hook):
	if hook in mnemosyne.core.function_hooks:
	    for f in mnemosyne.core.function_hooks[hook]:
		f(target)

    def collect_images(self, dst_subdir=os.path.join('cards', 'img'),
		       fcopy=shutil.copy):

	dstpath = os.path.join(self.sync_path, dst_subdir)
	if not os.path.exists(dstpath):
	    os.mkdir(dstpath)

	moved = Set()
	for srcimg in self.imgs:
	    moved.add(os.path.basename(srcimg))
	    dstimg = os.path.join(dstpath, os.path.basename(srcimg))
	    if (not os.path.exists(dstimg)
		or (os.path.getmtime(dstimg) < os.path.getmtime(srcimg))):
		try:
		    fcopy(srcimg, dstimg)
		    self.call_hooks(dstimg, 'gogo_img')
		except Exception, e:
		    print >> sys.stderr, "Error copying image: %s" % e


	for file in os.listdir(dstpath):
	    if file not in moved:
		os.remove(os.path.join(dstpath, file))
    
    def add_style_file(self, dstpath):
	shutil.copy(os.path.join(self.gogo_dir, 'style.css'), dstpath)

    def category_id(self, cat):
	try:
	    i = self.categories.index(cat)
	except ValueError:
	    i = len(self.categories)
	    self.categories.append(cat)
	return i

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
    def read(self):
	return None

    # implement in plugin
    def get_start_time(self):
	return 0

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

    # # # Utility routines # # #

######################################################################
# Implementation

class MnemoGoGo(Exception):
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
	except: raise MnemoGoGo('Error initialising interface: ' + file
				+ '\n' + traceback.format_exc())

    for iface in interface_classes:
	try:
	    obj = iface()
	    name = iface.__name__
	    desc = obj.description
	except: raise MnemoGoGo('Error registering interface: ' + file
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
def get_fresh_id(id, used_ids):
    r = num_suffix_re.match(id)
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
	if checked[item.id]:
	    newid = get_fresh_id(item.id, checked)
	    print >> sys.stderr, ("Fixing duplicate id: %s -> %s",
				  item.id, newid)
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

def do_export(interface, num_days, sync_path, extra = 1.00):
    basedir = mnemosyne.core.get_basedir()

    eliminate_duplicate_ids()
    exporter = interface.start_export(sync_path)
    exporter.gogo_dir = unicode(os.path.join(basedir, "plugins", "mnemogogo"))

    config = {
	    'grade_0_items_at_once'
		: mnemosyne.core.get_config('grade_0_items_at_once'),
	    'logging'
		: mnemosyne.core.get_config('upload_logs'),
	}

    cards = list(cards_for_ndays(num_days, extra))
    cards.sort(key=mnemosyne.core.Item.sort_key_interval)
    time_of_start = mnemosyne.core.get_time_of_start()
    items = mnemosyne.core.get_items()

    exporter.open(long(time_of_start.time), len(cards))
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

    exporter.close()

def adjust_start_date(import_start_date):
    time_of_start = mnemosyne.core.get_time_of_start()
    cur_start_date = time_of_start.time
    imp_time_of_start = mnemosyne.core.StartTime(import_start_date)
    imp_start_date = imp_time_of_start.time

    offset = abs(long(round((cur_start_date - imp_start_date)
			    / 60. / 60. / 24.)))

    if cur_start_date > imp_start_date:
	time_of_start = mnemosyne.core.StartTime(imp_start_date)
	items = mnemosyne.core.get_items()
	for item in items:
	    item.last_rep += offset
	    item.next_rep += offset
	return None

    return offset

def do_import(interface, sync_path):
    importer = interface.start_import(sync_path)

    offset = adjust_start_date(importer.get_start_time())

    new_stats = []
    for (id, stats) in importer:
	card = mnemosyne.core.get_item_by_id(id)
	if card is not None:
	    if offset is not None:
		stats['last_rep'] += offset
		stats['next_rep'] += offset
	    new_stats.append((card, stats))
	else:
	    print >> sys.stderr, (
		"Quietly ignoring card with missing id: %s" % id)

    # Only update the database if the entire read is successful
    for (card, stats) in new_stats:
	stats_to_card(stats, card)

    # Import logging details
    logpath = os.path.join(sync_path, 'log')
    if os.path.exists(logpath):
	log = open(logpath)

	line = self.statfile.readline()
	while line != ''
	    mnemosyne.core.logger.info(line)
	    line = self.statfile.readline()

	close(log)
	os.remove(logpath)

