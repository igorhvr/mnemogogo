#!/usr/local/bin/python2.5

# Derived from the mnemosyne startup script by <Peter.Bienstman@UGent.be>

import sys, os, locale

from qt import *
from mnemosyne.core import basedir, get_config, set_config, \
                           initialise, finalise, get_items, load_database
from mnemosyne.pyqt_ui.main_dlg import MainDlg, install_tooltip_strings, prefix
from mnemosyne.pyqt_ui.message_boxes import messagebox_errors
from mnemosyne.pyqt_ui.plugin import * # To be picked up by py2exe.
from mnemosyne.core.exceptions import *
from optparse import OptionParser

# Manipulate stats

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

def card_to_stats(card):
    stats = {}
    for f in learning_data:
	if f == 'easiness':
	    stats[f] = int(round(getattr(card, f) * easiness_accuracy))
	else:
	    stats[f] = int(getattr(card, f))
    return stats

def write_stats(id, cat, stats):
    for s in learning_data:
	fmt = "%%0%dx," % learning_data_len[s]
	print (fmt % stats[s]),
    print ("%s " % id),
    print ("(%s)" % cat)

# Parse options.

parser = OptionParser()
parser.usage = "%prog [<database.mem>]"
parser.add_option("-d", "--datadir", dest="datadir",
                  help="data directory", default=None)
(options, args) = parser.parse_args()

# Check if we have to override the basedir determined in mnemosyne.core,
# either because we explicitly specified a datadir on the command line,
# or because there is a .mnemosyne directory present in the current directory.
# The latter is handy when Mnemosyne is run from a USB key, so that there
# is no need to refer to a drive letter which can change from computer to
# computer.
    
if options.datadir != None:
    basedir = os.path.abspath(options.datadir)
elif os.path.exists(os.path.join(os.getcwdu(), ".mnemosyne")):
    basedir = os.path.abspath(os.path.join(os.getcwdu(), ".mnemosyne"))

# Filename argument.

if len(args) > 0:
    filename = os.path.abspath(args[0])
else:
    filename = None

# Create main widget.

a = QApplication(sys.argv)

# Under Windows, move out of library.zip to get the true prefix.

if sys.platform == "win32":
    prefix = os.path.split(prefix)[0]
    prefix = os.path.split(prefix)[0]
    prefix = os.path.split(prefix)[0]

# Get the locale from the user's config.py, to install the translator as
# soon as possible.

loc = str(QLocale().name()) # Default to system locale.

sys.path.insert(0, basedir)

config_file_c = os.path.join(basedir, "config.pyc")
if os.path.exists(config_file_c):
    os.remove(config_file_c)

try:
    import config as _config
    if _config.locale != None:
        loc = _config.locale      
except:
    pass

# Install translator.

translator = QTranslator(a)
translator.load("mnemosyne_"+loc+".qm", os.path.join(prefix,'locale'))
a.installTranslator(translator)

translator = QTranslator(a)
translator.load("qt_"+loc+".qm", os.path.join(prefix,'locale'))
a.installTranslator(translator)

# Check if there is another instance of Mnemosyne running.

if os.path.exists(os.path.join(basedir,"MNEMOSYNE_LOCK")):
    status = QMessageBox.warning(None,
             a.trUtf8("Mnemosyne"),
             a.trUtf8("Either Mnemosyne didn't shut down properly,\n" +
                      "or another copy of Mnemosyne is still running.\n" +
                      "Continuing in the latter case could lead to data " +
                      "loss!\n"),
             a.trUtf8("&Exit"), a.trUtf8("&Continue"),
             QString(), 0, -1)
    if status == 0 or status == -1:
        sys.exit()

try:
    initialise(basedir)
except MnemosyneError, e:
    messagebox_errors(a, e)

# Start program.

filename = get_config("path")
load_database(filename)
items = get_items()
for item in items:
    stats = card_to_stats(item)
    write_stats(item.id, item.cat.name, stats)

finalise()
