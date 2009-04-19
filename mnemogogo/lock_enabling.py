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

#
# Wrapper to lock enabled status of QWidget instances
#
# To add locking to a widget:
#   add(widget)
#
# To remove locking from a widget:
#   widget.removeLocking()
#
# When locking is available:
#   To lock in the disabled state:	widget.disableAndLock()
#   To unlock and restore the state:	widget.unlockAndRestore()
#

import new

def _setEnabledWithLocking(self, status=True):
    self._status = status
    if not self._locked:
	self._setEnabled(status)

def _disableAndLock(self):
    self._locked = True
    self._setEnabled(False)

def _unlockAndRestore(self):
    self._locked = False
    self._setEnabled(self._status)

def _removeLocking(self):
    self.unlockAndRestore()

    self.setEnabled = self._setEnabled
    del self.__dict__['_status']
    del self.__dict__['_locked']
    del self.__dict__['_setEnabled']
    del self.__dict__['disableAndLock']
    del self.__dict__['unlockAndRestore']
    del self.__dict__['removeLocking']

def add(obj):
    dict = obj.__class__.__dict__

    obj._status = obj.isEnabled()
    obj._locked = False

    obj._setEnabled = obj.setEnabled
    obj.setEnabled = new.instancemethod(_setEnabledWithLocking,
					obj, obj.__class__)
    obj.disableAndLock = new.instancemethod(_disableAndLock,
					    obj, obj.__class__)
    obj.unlockAndRestore = new.instancemethod(_unlockAndRestore,
					   obj, obj.__class__)
    obj.removeLocking = new.instancemethod(_removeLocking,
					   obj, obj.__class__)

