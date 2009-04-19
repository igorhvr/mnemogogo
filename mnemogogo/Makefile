MAKE=make

gogo_frm.py: gogo_frm.ui
	pyuic gogo_frm.ui > gogo_frm.py

clean:
	$(MAKE) -C ./mobile/htmlcsv clean
	-@rm *.pyc *.pyo gogo_frm.py
	-@rm ../mnemogogo_plugin.pyc
	-@rm ../mnemogogo_plugin.pyo
	-@rm interface/*.pyc interface/*.pyo

