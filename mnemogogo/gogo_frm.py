# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'gogo_frm.ui'
#
# Created: Tue Jan 19 20:13:25 2010
#      by: The PyQt User Interface Compiler (pyuic) 3.18.1
#
# WARNING! All changes made in this file will be lost!


from qt import *


class GogoFrm(QDialog):
    def __init__(self,parent = None,name = None,modal = 0,fl = 0):
        QDialog.__init__(self,parent,name,modal,fl)

        if not name:
            self.setName("GogoFrm")

        self.setSizeGripEnabled(1)


        LayoutWidget = QWidget(self,"Layout1")
        LayoutWidget.setGeometry(QRect(11,326,546,31))
        Layout1 = QHBoxLayout(LayoutWidget,0,6,"Layout1")
        Horizontal_Spacing2 = QSpacerItem(20,20,QSizePolicy.Expanding,QSizePolicy.Minimum)
        Layout1.addItem(Horizontal_Spacing2)

        self.doneButton = QPushButton(LayoutWidget,"doneButton")
        self.doneButton.setAutoDefault(1)
        self.doneButton.setDefault(1)
        Layout1.addWidget(self.doneButton)

        self.tabWidget = QTabWidget(self,"tabWidget")
        self.tabWidget.setGeometry(QRect(10,10,550,310))

        self.synchronizeTab = QWidget(self.tabWidget,"synchronizeTab")

        self.localFrame = QFrame(self.synchronizeTab,"localFrame")
        self.localFrame.setGeometry(QRect(24,11,176,261))
        self.localFrame.setPaletteBackgroundColor(QColor(0,170,0))
        self.localFrame.setFrameShape(QFrame.StyledPanel)
        self.localFrame.setFrameShadow(QFrame.Sunken)
        localFrameLayout = QGridLayout(self.localFrame,1,1,11,6,"localFrameLayout")
        spacer4 = QSpacerItem(20,40,QSizePolicy.Minimum,QSizePolicy.Expanding)
        localFrameLayout.addItem(spacer4,0,1)
        spacer4_2 = QSpacerItem(20,40,QSizePolicy.Minimum,QSizePolicy.Expanding)
        localFrameLayout.addItem(spacer4_2,2,1)
        spacer15 = QSpacerItem(40,20,QSizePolicy.Expanding,QSizePolicy.Minimum)
        localFrameLayout.addItem(spacer15,1,0)
        spacer15_2 = QSpacerItem(40,20,QSizePolicy.Expanding,QSizePolicy.Minimum)
        localFrameLayout.addItem(spacer15_2,1,2)

        self.localLabel = QLabel(self.localFrame,"localLabel")
        self.localLabel.setPaletteForegroundColor(QColor(255,255,255))

        localFrameLayout.addWidget(self.localLabel,1,1)

        self.mobileFrame = QFrame(self.synchronizeTab,"mobileFrame")
        self.mobileFrame.setGeometry(QRect(330,11,192,261))
        self.mobileFrame.setFrameShape(QFrame.StyledPanel)
        self.mobileFrame.setFrameShadow(QFrame.Sunken)
        mobileFrameLayout = QGridLayout(self.mobileFrame,1,1,11,6,"mobileFrameLayout")
        spacer4_3 = QSpacerItem(20,40,QSizePolicy.Minimum,QSizePolicy.Expanding)
        mobileFrameLayout.addItem(spacer4_3,0,1)
        spacer4_2_2 = QSpacerItem(20,40,QSizePolicy.Minimum,QSizePolicy.Expanding)
        mobileFrameLayout.addItem(spacer4_2_2,2,1)
        spacer17 = QSpacerItem(40,20,QSizePolicy.Expanding,QSizePolicy.Minimum)
        mobileFrameLayout.addItem(spacer17,1,0)
        spacer17_2 = QSpacerItem(40,20,QSizePolicy.Expanding,QSizePolicy.Minimum)
        mobileFrameLayout.addItem(spacer17_2,1,2)

        self.mobileLabel = QLabel(self.mobileFrame,"mobileLabel")
        self.mobileLabel.setPaletteForegroundColor(QColor(124,124,124))

        mobileFrameLayout.addWidget(self.mobileLabel,1,1)

        self.buttonGroup1 = QButtonGroup(self.synchronizeTab,"buttonGroup1")
        self.buttonGroup1.setGeometry(QRect(210,10,109,257))
        self.buttonGroup1.setFrameShape(QButtonGroup.NoFrame)
        self.buttonGroup1.setFrameShadow(QButtonGroup.Plain)
        self.buttonGroup1.setColumnLayout(0,Qt.Vertical)
        self.buttonGroup1.layout().setSpacing(6)
        self.buttonGroup1.layout().setMargin(11)
        buttonGroup1Layout = QVBoxLayout(self.buttonGroup1.layout())
        buttonGroup1Layout.setAlignment(Qt.AlignTop)
        spacer11 = QSpacerItem(20,40,QSizePolicy.Minimum,QSizePolicy.Expanding)
        buttonGroup1Layout.addItem(spacer11)

        self.exportButton = QPushButton(self.buttonGroup1,"exportButton")
        buttonGroup1Layout.addWidget(self.exportButton)
        spacer11_2 = QSpacerItem(20,20,QSizePolicy.Minimum,QSizePolicy.Expanding)
        buttonGroup1Layout.addItem(spacer11_2)

        self.progressBar = QProgressBar(self.buttonGroup1,"progressBar")
        self.progressBar.setPaletteForegroundColor(QColor(0,170,0))
        self.progressBar.setProgress(0)
        self.progressBar.setCenterIndicator(1)
        self.progressBar.setPercentageVisible(0)
        buttonGroup1Layout.addWidget(self.progressBar)
        spacer11_2_2 = QSpacerItem(20,20,QSizePolicy.Minimum,QSizePolicy.Expanding)
        buttonGroup1Layout.addItem(spacer11_2_2)

        self.importButton = QPushButton(self.buttonGroup1,"importButton")
        self.importButton.setEnabled(0)
        buttonGroup1Layout.addWidget(self.importButton)
        spacer11_2_2_2 = QSpacerItem(20,40,QSizePolicy.Minimum,QSizePolicy.Expanding)
        buttonGroup1Layout.addItem(spacer11_2_2_2)
        self.tabWidget.insertTab(self.synchronizeTab,QString.fromLatin1(""))

        self.optionsTab = QWidget(self.tabWidget,"optionsTab")

        self.textLabel2 = QLabel(self.optionsTab,"textLabel2")
        self.textLabel2.setGeometry(QRect(11,11,175,24))

        self.textLabel4 = QLabel(self.optionsTab,"textLabel4")
        self.textLabel4.setGeometry(QRect(11,80,175,24))

        self.interfaceList = QComboBox(0,self.optionsTab,"interfaceList")
        self.interfaceList.setGeometry(QRect(192,80,343,24))

        self.browseButton = QPushButton(self.optionsTab,"browseButton")
        self.browseButton.setGeometry(QRect(449,41,86,33))

        self.forceLocalButton = QPushButton(self.optionsTab,"forceLocalButton")
        self.forceLocalButton.setGeometry(QRect(11,235,119,33))

        self.forceMobileButton = QPushButton(self.optionsTab,"forceMobileButton")
        self.forceMobileButton.setGeometry(QRect(11,196,119,33))

        self.syncPath = QLineEdit(self.optionsTab,"syncPath")
        self.syncPath.setGeometry(QRect(192,45,251,24))

        self.daysToExport = QSpinBox(self.optionsTab,"daysToExport")
        self.daysToExport.setGeometry(QRect(192,11,46,24))

        self.textLabel3 = QLabel(self.optionsTab,"textLabel3")
        self.textLabel3.setGeometry(QRect(11,41,175,33))

        self.imageProperties = QButtonGroup(self.optionsTab,"imageProperties")
        self.imageProperties.setGeometry(QRect(270,130,176,118))
        self.imageProperties.setColumnLayout(0,Qt.Vertical)
        self.imageProperties.layout().setSpacing(6)
        self.imageProperties.layout().setMargin(11)
        imagePropertiesLayout = QGridLayout(self.imageProperties.layout())
        imagePropertiesLayout.setAlignment(Qt.AlignTop)

        self.maxWidth = QSpinBox(self.imageProperties,"maxWidth")
        self.maxWidth.setMaxValue(1024)
        self.maxWidth.setMinValue(32)
        self.maxWidth.setValue(240)

        imagePropertiesLayout.addWidget(self.maxWidth,0,1)

        self.maxHeight = QSpinBox(self.imageProperties,"maxHeight")
        self.maxHeight.setMaxValue(1024)
        self.maxHeight.setMinValue(32)
        self.maxHeight.setValue(300)

        imagePropertiesLayout.addWidget(self.maxHeight,1,1)

        self.maxSize = QSpinBox(self.imageProperties,"maxSize")
        self.maxSize.setMaxValue(256)
        self.maxSize.setMinValue(16)
        self.maxSize.setValue(64)

        imagePropertiesLayout.addWidget(self.maxSize,2,1)

        self.maxSize_label = QLabel(self.imageProperties,"maxSize_label")

        imagePropertiesLayout.addWidget(self.maxSize_label,2,0)

        self.maxHeight_label = QLabel(self.imageProperties,"maxHeight_label")

        imagePropertiesLayout.addWidget(self.maxHeight_label,1,0)

        self.maxWidth_label = QLabel(self.imageProperties,"maxWidth_label")

        imagePropertiesLayout.addWidget(self.maxWidth_label,0,0)
        self.tabWidget.insertTab(self.optionsTab,QString.fromLatin1(""))

        self.languageChange()

        self.resize(QSize(572,365).expandedTo(self.minimumSizeHint()))
        self.clearWState(Qt.WState_Polished)

        self.setTabOrder(self.doneButton,self.tabWidget)
        self.setTabOrder(self.tabWidget,self.exportButton)
        self.setTabOrder(self.exportButton,self.importButton)
        self.setTabOrder(self.importButton,self.daysToExport)
        self.setTabOrder(self.daysToExport,self.syncPath)
        self.setTabOrder(self.syncPath,self.browseButton)
        self.setTabOrder(self.browseButton,self.interfaceList)
        self.setTabOrder(self.interfaceList,self.forceMobileButton)
        self.setTabOrder(self.forceMobileButton,self.forceLocalButton)


    def languageChange(self):
        self.setCaption(self.__tr("Mnemogogo"))
        self.doneButton.setText(self.__tr("&Done"))
        self.doneButton.setAccel(QKeySequence(self.__tr("Alt+D")))
        self.localLabel.setText(self.__tr("<p align=\"center\"><font size=\"+3\"><b>Local</b></font></p>"))
        self.mobileLabel.setText(self.__tr("<p align=\"center\"><font size=\"+3\"><b>Mobile</b></font></p>"))
        self.buttonGroup1.setTitle(QString.null)
        self.exportButton.setText(self.__tr("&Export >>"))
        self.exportButton.setAccel(QKeySequence(self.__tr("Alt+E")))
        self.importButton.setText(self.__tr("<< &Import"))
        self.importButton.setAccel(QKeySequence(self.__tr("Alt+I")))
        self.tabWidget.changeTab(self.synchronizeTab,self.__tr("Synchronize"))
        self.textLabel2.setText(self.__tr("Number of days to export:"))
        self.textLabel4.setText(self.__tr("Interface:"))
        self.browseButton.setText(self.__tr("&Browse"))
        self.browseButton.setAccel(QKeySequence(self.__tr("Alt+B")))
        self.forceLocalButton.setText(self.__tr("Force to Local"))
        self.forceMobileButton.setText(self.__tr("Force to Mobile"))
        self.textLabel3.setText(self.__tr("Synchronization path:"))
        self.imageProperties.setTitle(self.__tr("Exported image limits"))
        self.maxSize_label.setText(self.__tr("Size (Kb):"))
        self.maxHeight_label.setText(self.__tr("Height:"))
        self.maxWidth_label.setText(self.__tr("Width:"))
        self.tabWidget.changeTab(self.optionsTab,self.__tr("Options"))


    def __tr(self,s,c = None):
        return qApp.translate("GogoFrm",s,c)
