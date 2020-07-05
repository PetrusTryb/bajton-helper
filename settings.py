from configparser import ConfigParser
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5 import *
from login import logOut
import requests
import sys
class Settings(QWidget):
	def __init__(self, parent):
		super(QWidget, self).__init__(parent)
		layout = QVBoxLayout()
		account=QGroupBox("My data")
		accountLayout=QVBoxLayout()
		warn=QLabel("Do not share the props.ini file! It contains informations that may be used to steal Your account.")
		warn.setFont(QFont("Arial",12,5))
		accountLayout.addWidget(warn)
		clear=QCheckBox("Clear all data at logout (this will clear all settings and contests passwords)")
		accountLayout.addWidget(clear)
		logout=QPushButton("Logout and exit")
		logout.clicked.connect(lambda x:logOut(clear=clear.isChecked()))
		accountLayout.addWidget(logout)
		account.setLayout(accountLayout)
		layout.addWidget(account)
		ui=QGroupBox("Interface theme")
		uiLayout=QVBoxLayout()
		dark=QRadioButton("Dark")
		dark.clicked.connect(lambda x:self.changeTheme("dark"))
		uiLayout.addWidget(dark)
		light=QRadioButton("Light")
		light.clicked.connect(lambda x:self.changeTheme("light"))
		parser = ConfigParser()
		parser.read('props.ini')
		dark.setChecked(parser["GUI"]["theme"]=="dark")
		light.setChecked(parser["GUI"]["theme"]=="light")
		uiLayout.addWidget(light)
		ui.setLayout(uiLayout)
		layout.addWidget(ui)
		runOpts=QGroupBox("Start options")
		runLayout=QVBoxLayout()
		systemRun=QCheckBox("Run at system startup")
		runLayout.addWidget(systemRun)
		headless=QCheckBox("Start minimized")
		headless.setChecked(parser["GUI"]["headless"]=="True")
		headless.clicked.connect(lambda x:self.changeDisplay(headless.isChecked()))
		runLayout.addWidget(headless)
		runOpts.setLayout(runLayout)
		layout.addWidget(runOpts)
		verInfo=QLabel("Bajton helper by Piotr Trybisz")
		verInfo.setFont(QFont("Arial",25))
		layout.addWidget(verInfo)
		layout.addWidget(QLabel("This app is made for educational purposes. It is not for cheating or hacking Online Judge app."))
		fullExit=QPushButton("Full exit")
		fullExit.clicked.connect(sys.exit)
		layout.addWidget(fullExit)
		self.setLayout(layout)
	def changeTheme(self,what):
		parser = ConfigParser()
		parser.read('props.ini')
		parser["GUI"]["theme"]=what
		with open('props.ini', 'w') as configfile:
			parser.write(configfile)
		box = QMessageBox()
		box.setIcon(QMessageBox.Information)
		box.setWindowTitle("Theme changed")
		box.setText("Please restart the app to apply changes.")
		box.exec_()
	def changeDisplay(self,what):
		parser = ConfigParser()
		parser.read('props.ini')
		parser["GUI"]["headless"]=str(what)
		with open('props.ini', 'w') as configfile:
			parser.write(configfile)