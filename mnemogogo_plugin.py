##############################################################################
#
# mnemogogo.py <timbob@bigpond.com>
#
# MnemoGoGo: making mnemosyne mobile
#
##############################################################################

#
# Copyright (c) 2009 Timothy Bourke
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the "BSD License" which is distributed with the
# software in the file mnemogogo/LICENSE.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the BSD
# License for more details.
#

from mnemosyne.core import *
from mnemosyne.pyqt_ui.plugin import get_main_widget
from qt import *
import sys
from os.path import exists, join

import mnemogogo

debug = True
def log_info(msg):
    if debug:
	print >> sys.stderr, msg

class MnemoGoGoPlugin(Plugin):
    version = "0.9.3"
    is_locked = False
    old_overlay = None

    settings = {
	'sync_path'	: '',
	'interface'	: None,
	'n_days'	: 7,
	'mode'		: 'local',
	'extra_factor'	: 1.00,
    }

    def description(self):
	return ("Making mnemosyne mobile (v" + version + ")")

    def load_config(self):
	try: config = get_config("mnemogogo")
	except KeyError:
	    config = {}
	    set_config("mnemogogo", {})
	
	for k in self.settings.keys():
	    if config.has_key(k): self.settings[k] = config[k]
	
    def save_config(self):
	set_config("mnemogogo", self.settings)

    def open_dialog(self):
	self.gogo_dlg.configure(self.settings)
	self.gogo_dlg.exec_loop()
	self.settings = self.gogo_dlg.settings

	if self.settings['mode'] == 'mobile':
	    self.lock()
	else:
	    self.unlock()

	self.main_dlg.updateDialog()
	self.save_config()

    def load(self):
	basedir = get_basedir()

	if not exists(join(basedir, "plugins", "mnemogogo")):
	    raise mnemogogo.MnemoGoGo(
		     "Incorrect installation. Missing "
		   + join(basedir, "plugins", "mnemogogo")
		   + " directory")
	
	# Load configuration
	self.load_config()
	
	self.interfaces = mnemogogo.register_interfaces()

	self.main_dlg = get_main_widget()
	self.gogo_dlg = mnemogogo.GoGoDlg(self.main_dlg)
	self.gogo_dlg.setInterfaceList(self.interfaces)

	# Add Menu Item
	self.menu = self.main_dlg.Deck

        self.menu_item = QAction(self.main_dlg, "menuMnemoGoGo")
	self.menu_item.addTo(self.menu)
        self.main_dlg.connect(self.menu_item, SIGNAL("activated()"),
			      self.open_dialog)
        self.menu_item.setText(QString.null)
        self.menu_item.setMenuText(self.main_dlg.trUtf8("MnemoGoGo"))
        self.menu_item.setToolTip(QString.null)
        self.menu_item.setStatusTip(self.main_dlg.trUtf8("."))

	# Implement locking
	self.lock_msg_main = self.main_dlg.trUtf8(
	    "Mobile reviewing is enabled.")
	self.lock_msg_info = self.main_dlg.trUtf8(
	    "Choose MnemoGoGo from the Deck menu for options.")

	mnemogogo.lock_enabling.add(self.main_dlg.show_button)
	mnemogogo.lock_enabling.add(self.main_dlg.grades)

	register_function_hook("filter_q", self.check_lock)
	register_function_hook("filter_a", self.check_lock)

	if self.settings['mode'] == 'mobile':
	    self.lock()

    def lock(self):
	self.is_locked = True
	self.main_dlg.show_button.disableAndLock()
	self.main_dlg.grades.disableAndLock()

	try:
	    self.old_overlay = self.main_dlg.style['answerbox']
	    self.main_dlg.style["answerbox"] = "overlay"
	except: self.old_overlay = None

	self.main_dlg.answer.hide()
	self.main_dlg.answer_label.hide()

    def unlock(self):
	self.is_locked = False
	self.main_dlg.show_button.unlockAndRestore()
	self.main_dlg.grades.unlockAndRestore()
	self.main_dlg.style['answerbox'] = self.old_overlay
	self.main_dlg.question.show()
	self.main_dlg.question_label.show()
	self.main_dlg.answer.show()
	self.main_dlg.answer_label.show()

    def unload(self):
	self.menu_item.removeFrom(self.menu)
	self.unlock()
	unregister_function_hook("filter_q", self.check_lock)
	unregister_function_hook("filter_a", self.check_lock)
	self.main_dlg.show_button.removeLocking()
	self.main_dlg.grades.removeLocking()

    def check_lock(self, text, card):
	if not self.is_locked: return text

	text = "<b><font color=\"red\">%s</font></b>" % self.lock_msg_main
	text += "<br><br><img src=\"plugins/mnemogogo/locked.png\">"
	text += "<br><br><i>%s</i>" % self.lock_msg_info
	text += "<card style=\"answerbox: overlay\"/>"

	return mnemosyne.core.preprocess(text)

p = MnemoGoGoPlugin()
p.load()

