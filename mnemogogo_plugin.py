##############################################################################
#
# mnemogogo.py <timbob@bigpond.com>
#
# Mnemogogo: making mnemosyne mobile
#
##############################################################################

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

from mnemosyne.core import *
from mnemosyne.pyqt_ui.plugin import get_main_widget
from qt import *
import sys, copy
from os.path import exists, join

try:
    import mnemogogo
    mnemogogo_imported = True
except Exception, e:
    mnemogogo_imported = False
    mnemogogo_imported_error = str(e)

class MnemogogoPlugin(Plugin):
    version = "1.1.4"
    is_locked = False
    old_overlay = None
    config_key = "mnemogogo"

    default_settings = {
	'sync_path'	: '',
	'interface'	: None,
	'n_days'	: 7,
	'mode'		: 'local',
	'extra_factor'	: 1.00,
	'max_width'	: 240,
	'max_height'	: 300,
	'max_size'	: 64,
    }

    def description(self):
	return ("Making mnemosyne mobile (v" + version + ")")

    def load_config(self):
	self.config_key = mnemogogo.get_config_key()

	try:
	    config = get_config(self.config_key)
	except KeyError:
	    config = {}
	    set_config(self.config_key, {})
	
	self.settings = copy.copy(self.default_settings)
	for k in self.settings.keys():
	    if config.has_key(k): self.settings[k] = config[k]
	
    def save_config(self):
	set_config(self.config_key, copy.copy(self.settings))

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

    def show_error(self, msg):
	QMessageBox.critical(None, 
	    self.main_dlg.trUtf8("Mnemogogo"),
	    self.main_dlg.trUtf8(msg),
	    self.main_dlg.trUtf8("&OK"), "", "", 0, -1)

    def load(self):
	basedir = get_basedir()
	self.main_dlg = get_main_widget()

	if not exists(join(basedir, "plugins", "mnemogogo")):
	    self.show_error("Incorrect installation. Missing "
	        + join(basedir, "plugins", "mnemogogo")
	        + " directory")
	    return

	if not mnemogogo_imported:
	    self.show_error("Incorrect installation."
		+ " The mnemogogo module could not be imported.\n\n("
		+ mnemogogo_imported_error + ")")
	    return
	
	try:
	    time_of_start = mnemosyne.core.get_time_of_start()
	except AttributeError:
	    self.show_error(
		"Mnemogogo requires Mnemosyne version 1.2.2 or above.")
	    return

	mnemogogo.log_info('version %s' % self.version)

	if not mnemogogo.htmltounicode_working:
	    mnemogogo.log_warning(
		'Neither html.entities nor htmlentitydefs could be imported.')
	
	self.interfaces = mnemogogo.register_interfaces()

	self.gogo_dlg = mnemogogo.GogoDlg(self.main_dlg)
	self.gogo_dlg.setInterfaceList(self.interfaces)

	# Add Menu Item
	self.menu = self.main_dlg.Deck

        self.menu_item = QAction(self.main_dlg, "menuMnemogogo")
	self.menu_item.addTo(self.menu)
        self.main_dlg.connect(self.menu_item, SIGNAL("activated()"),
			      self.open_dialog)
        self.menu_item.setText(QString.null)
        self.menu_item.setMenuText(self.main_dlg.trUtf8("&Mnemogogo"))
        self.menu_item.setToolTip(QString.null)
        self.menu_item.setStatusTip(self.main_dlg.trUtf8("."))
        self.menu_item.setAccel(self.main_dlg.trUtf8("Ctrl+M"))

	# Implement locking
	self.lock_msg_main = self.main_dlg.trUtf8(
	    "Mobile reviewing is enabled.")
	self.lock_msg_info = self.main_dlg.trUtf8(
	    "Choose Mnemogogo from the Deck menu for options.")

	mnemogogo.lock_enabling.add(self.main_dlg.show_button)
	mnemogogo.lock_enabling.add(self.main_dlg.grades)

	register_function_hook("filter_q", self.check_lock)
	register_function_hook("filter_a", self.check_lock)
	register_function_hook("after_load", self.after_load)

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
	try:
	    self.main_dlg.style['answerbox'] = self.old_overlay
	except: pass
	self.main_dlg.question.show()
	self.main_dlg.question_label.show()
	self.main_dlg.answer.show()
	self.main_dlg.answer_label.show()

    def unload(self):
	self.menu_item.removeFrom(self.menu)
	self.unlock()
	unregister_function_hook("filter_q", self.check_lock)
	unregister_function_hook("filter_a", self.check_lock)
	unregister_function_hook("after_load", self.after_load)
	self.main_dlg.show_button.removeLocking()
	self.main_dlg.grades.removeLocking()

    def check_lock(self, text, card):
	try: dlg_name = sys._getframe(2).f_locals['self'].__class__.__name__
	except: dlg_name = 'MainDlg'

	if (not self.is_locked) or (dlg_name == 'PreviewItemDlg'):
	    return text

	text = "<b><font color=\"red\">%s</font></b>" % self.lock_msg_main
	text += "<br><br><img src=\"plugins/mnemogogo/locked.png\">"
	text += "<br><br><i>%s</i>" % self.lock_msg_info
	text += "<card style=\"answerbox: overlay\"/>"

	return mnemosyne.core.preprocess(text)

    def after_load(self):
	self.load_config()
	if self.settings['mode'] == 'mobile':
	    self.lock()
	else:
	    self.unlock()

p = MnemogogoPlugin()
p.load()

