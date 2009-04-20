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

from qt import *
from gogo_frm import *
from core import do_export, do_import, MnemoGoGo, InterfaceError
from mnemosyne.core import *
import traceback

class GoGoDlg(GoGoFrm):
    settings = {
	    'extra_factor' : 1.00,
	}

    def showWarning(self, msg):
	status = QMessageBox.warning(None,
	   self.trUtf8("MnemoGoGo"),
	   msg,
	   self.trUtf8("&OK"))

    def showError(self, msg):
	status = QMessageBox.critical(None,
	   self.trUtf8("MnemoGoGo"), msg, self.trUtf8("&OK"))

    def markInactive(self, frame, label):
	frame.setPaletteBackgroundColor(QColor(124,124,124))
        label.setPaletteBackgroundColor(QColor(124,124,124))
        label.setPaletteForegroundColor(QColor(192,192,192))

    def markActive(self, frame, label):
	frame.setPaletteBackgroundColor(QColor(0,170,0))
	label.setPaletteBackgroundColor(QColor(0,170,0))
        label.setPaletteForegroundColor(QColor(255,255,255))

    def setLocal(self):
	self.mode = "local"
	self.markInactive(self.mobileFrame, self.mobileLabel)
	self.markActive(self.localFrame, self.localLabel)
	self.exportButton.setEnabled(1)
	self.importButton.setEnabled(0)
	self.forceMobileButton.setEnabled(1)
	self.forceLocalButton.setEnabled(0)

    def setMobile(self):
	self.mode = "mobile"
	self.markActive(self.mobileFrame, self.mobileLabel)
	self.markInactive(self.localFrame, self.localLabel)
	self.exportButton.setEnabled(0)
	self.importButton.setEnabled(1)
	self.forceMobileButton.setEnabled(0)
	self.forceLocalButton.setEnabled(1)

    def setInterfaceList(self, interfaces):
	self.name_to_desc = {}
	self.desc_to_name = {}
	self.name_to_object = {}
	for iface in interfaces:
	    self.name_to_desc[iface['name']] = iface['description']
	    self.desc_to_name[iface['description']] = iface['name']
	    self.name_to_object[iface['name']] = iface['object']
	    self.interfaceList.insertItem(iface['description'])

    def getInterface(self):
	return self.desc_to_name[unicode(self.interfaceList.currentText())]

    def writeSettings(self):
	self.settings['mode'] = self.mode
	self.settings['interface'] = self.getInterface()
	self.settings['n_days'] = self.daysToExport.value()
	self.settings['sync_path'] = unicode(self.syncPath.text())

    def __init__(self, parent=None, name=None, modal=0, fl=0):
	GoGoFrm.__init__(self, parent, name, modal, fl)

	self.main_dlg = parent

	self.setLocal()

	self.connect(self.exportButton, SIGNAL("clicked()"), self.doExport)
	self.connect(self.importButton, SIGNAL("clicked()"), self.doImport)
	self.connect(self.browseButton, SIGNAL("clicked()"), self.browse)
	self.connect(self.doneButton, SIGNAL("clicked()"), self.apply)
	self.connect(self.forceMobileButton, SIGNAL("clicked()"),
		     self.forceMobile)
	self.connect(self.forceLocalButton, SIGNAL("clicked()"),
		     self.forceLocal)

    def doExport(self):
	self.writeSettings()
	try:
	    do_export(
		self.name_to_object[self.settings['interface']],
		self.settings['n_days'],
		self.settings['sync_path'],
		self.settings['extra_factor'])
	    self.setMobile()
	except InterfaceError, e:
	    self.showError(unicode(e))
	except MnemoGoGo, e:
	    self.showError(unicode(e))
	except Exception:
	    self.showError(traceback.format_exc())

    def doImport(self):
	self.writeSettings()
	try:
	    do_import(
		self.name_to_object[self.settings['interface']],
		self.settings['sync_path'])
	    self.setLocal()
	    rebuild_revision_queue(False)
	    self.main_dlg.newQuestion()
	    self.main_dlg.updateDialog()

	except InterfaceError, e:
	    self.showError(unicode(e))
	except MnemoGoGo, e:
	    self.showError(unicode(e))
	except Exception:
	    self.showError(traceback.format_exc())

    def forceMobile(self):
	self.setMobile()

    def forceLocal(self):
	self.setLocal()

    def browse(self):
        dir = unicode(QFileDialog.getExistingDirectory(
		self.syncPath.text(),
		self,
		"blah",
		self.trUtf8("Select synchronization path"),
		False))
	# wrap path in expand_path
		
        if dir != "":
            self.syncPath.setText(dir)
    
    def configure(self, settings):
	if settings.has_key('mode'):
	    self.mode = settings['mode']
	
	if self.mode == 'mobile':
	    self.setMobile()
	else:
	    self.setLocal()

	if settings.get('interface'):
	    try:
		if not settings['interface'] is None:
		    self.interfaceList.setCurrentText(
			self.name_to_desc[settings['interface']])
	    except KeyError:
		self.showWarning(
			self.trUtf8("The interface '")
			+ settings['interface']
			+ self.trUtf8("' is not currently available. ")
			+ self.trUtf8("Please select another."))

	if settings.has_key('n_days'):
	    self.daysToExport.setValue(settings['n_days'])

	if settings.has_key('sync_path'):
	    self.syncPath.setText(settings['sync_path'])
	
	if settings.has_key('extra_factor'):
	    self.settings['extra_factor'] = settings['extra_factor']

    def apply(self):
	self.writeSettings()
	self.close()

