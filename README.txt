Mnemogogo: Making Mnemosyne Mobile
Timothy Bourke <timbob@bigpond.com>

THIS IS EXPERIMENTAL SOFTWARE. USE AT YOUR OWN RISK. BACKUP YOUR FILES.

Please report bugs, preferably with patches to the author or the Mnemosyne
development mailing list.

Installation
------------
1. Patch the mnemosyne_core.py file. Either manually, or with:
    cd /usr/lib/python2.x/site-packages/Mnemosyne-1.x.x-py2.x.egg/
    patch < ~/mnemogogo/mnemosyne-1.x.patch

2. Copy the mnemogogo_plugin.py file and mnemogogo directory to your
   Mnemosyne plugins directory.

Development
-----------
To implement a mobile platform using the htmlcvs interface and library,
see the file:
    mnemogogo/mobile/htmlcsv/template.c

Please submit your applications to the Mnemosyne site!

The suggested naming is:
    Mnemogogo-S60
    Mnemogogo-iPhone
    Mnemogogo-D2
    Mnemogogo-Maemo
or similar.

