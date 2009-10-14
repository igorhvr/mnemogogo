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

import types

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
    obj.setEnabled = types.MethodType(_setEnabledWithLocking, obj)
    obj.disableAndLock = types.MethodType(_disableAndLock, obj)
    obj.unlockAndRestore = types.MethodType(_unlockAndRestore, obj)
    obj.removeLocking = types.MethodType(_removeLocking, obj)

