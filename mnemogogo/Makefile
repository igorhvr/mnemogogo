MAKE=make

gogo_frm.py: gogo_frm.ui
	pyuic gogo_frm.ui > gogo_frm.py

clean:
	-@rm *.pyc *.pyo 2>/dev/null
	-@rm ../mnemogogo_plugin.pyc 2>/dev/null
	-@rm ../mnemogogo_plugin.pyo 2>/dev/null
	-@rm interface/*.pyc interface/*.pyo 2>/dev/null

cleanall:
	-@rm *.jar 2>/dev/null
	-@rm *-src.tar.gz 2>/dev/null

