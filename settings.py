from configparser import ConfigParser
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5 import *
from login import logOut
import requests
import os
import sys
import win32com.client
from strings import *
class Settings(QWidget):
	def __init__(self, parent, wnd):
		super(QWidget, self).__init__(parent)
		self.wnd=wnd
		layout = QVBoxLayout()
		account=QGroupBox(string_my_data)
		accountLayout=QVBoxLayout()
		warn=QLabel(string_props_warning)
		warn.setFont(QFont("Arial",12,5))
		accountLayout.addWidget(warn)
		clear=QCheckBox(string_clear_data)
		accountLayout.addWidget(clear)
		logout=QPushButton(string_logout)
		logout.clicked.connect(lambda x:logOut(clear=clear.isChecked()))
		accountLayout.addWidget(logout)
		account.setLayout(accountLayout)
		layout.addWidget(account)
		ui=QGroupBox(string_theme)
		uiLayout=QVBoxLayout()
		dark=QRadioButton(string_dark)
		dark.clicked.connect(lambda x:self.changeTheme("dark"))
		uiLayout.addWidget(dark)
		light=QRadioButton(string_light)
		light.clicked.connect(lambda x:self.changeTheme("light"))
		parser = ConfigParser()
		parser.read('props.ini')
		dark.setChecked(parser["GUI"]["theme"]=="dark")
		light.setChecked(parser["GUI"]["theme"]=="light")
		uiLayout.addWidget(light)
		ui.setLayout(uiLayout)
		layout.addWidget(ui)
		runOpts=QGroupBox(string_start_options)
		runLayout=QVBoxLayout()
		systemRun=QCheckBox(string_autorun)
		autorunEnabled="bajton.lnk" in os.listdir(os.getenv("appdata")+"\\Microsoft\\Windows\\Start Menu\\Programs\\Startup")
		systemRun.setChecked(autorunEnabled)
		systemRun.clicked.connect(self.toggleAutostart)
		runLayout.addWidget(systemRun)
		headless=QCheckBox(string_minimize)
		try:
			headless.setChecked(parser["GUI"]["headless"]=="True")
		except KeyError:
			parser["GUI"]["headless"]="False"
			with open('props.ini', 'w') as configfile:
				parser.write(configfile)
		headless.clicked.connect(lambda x:self.changeDisplay(headless.isChecked()))
		runLayout.addWidget(headless)
		runOpts.setLayout(runLayout)
		layout.addWidget(runOpts)
		verInfo=QLabel("<a href='https://github.com/PetrusTryb/bajton-helper' style='color:red'>Bajton helper by Piotr Trybisz</a>")
		verInfo.setOpenExternalLinks(True)
		verInfo.setFont(QFont("Arial",25))
		layout.addWidget(verInfo)
		layout.addWidget(QLabel(string_legal))
		fullExit=QPushButton(string_exit)
		fullExit.clicked.connect(sys.exit)
		layout.addWidget(fullExit)
		self.setLayout(layout)
	def changeTheme(self,what):
		parser = ConfigParser()
		parser.read('props.ini')
		parser["GUI"]["theme"]=what
		with open('props.ini', 'w') as configfile:
			parser.write(configfile)
		self.wnd.setDarkMode()
	def changeDisplay(self,what):
		parser = ConfigParser()
		parser.read('props.ini')
		parser["GUI"]["headless"]=str(what)
		with open('props.ini', 'w') as configfile:
			parser.write(configfile)
	def toggleAutostart(self):
		autorunEnabled="bajton.lnk" in os.listdir(os.getenv("appdata")+"\\Microsoft\\Windows\\Start Menu\\Programs\\Startup")
		if(autorunEnabled):
			os.remove(os.getenv("appdata")+"\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\bajton.lnk")
		else:
			shell = win32com.client.Dispatch("WScript.Shell")
			shortcut = shell.CreateShortCut(os.getenv("appdata")+"\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\bajton.lnk")
			shortcut.Targetpath = "pythonw3"
			shortcut.Arguments = os.path.realpath("main.py")
			shortcut.IconLocation = os.path.realpath("icon.ico")
			shortcut.Description = "Bajton Helper by Piotr Trybisz"
			shortcut.WorkingDirectory = os.path.realpath(".")
			shortcut.save()