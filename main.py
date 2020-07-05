from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import *
from login import *
from contest import *
from search import *
from notifier import *
from settings import *
from configparser import ConfigParser
import sys
class Tabs(QWidget):
	def __init__(self, parent):
		super(QWidget, self).__init__(parent)
		self.layout = QVBoxLayout(self)
		#Initializing tab screen
		self.tabs = QTabWidget()
		self.tab1 = Contests(self)
		self.tab2 = Search(self)
		self.tab3 = Notifier(self)
		self.tab4 = Settings(self)
		self.tabs.resize(1000,700)
		#Adding tabs
		self.tabs.addTab(self.tab1,"Contests")
		self.tabs.addTab(self.tab2,"Search")
		self.tabs.addTab(self.tab3,"Notifications")
		self.tabs.addTab(self.tab4,"Settings")
		self.layout.addWidget(self.tabs)
		self.setLayout(self.layout)

class App(QMainWindow):
	def setDarkMode(self):
		palette = QtGui.QPalette()
		parser = ConfigParser()
		parser.read('props.ini')
		try:
			enabled = (parser["GUI"]["theme"]=="dark")
		except:
			enabled=True
			parser["GUI"]=dict()
			parser["GUI"]["theme"]="dark"
			with open('props.ini', 'w') as configfile:
				parser.write(configfile)
		if enabled:
			palette.setColor(QtGui.QPalette.Window, QtGui.QColor(53,53,53))
			palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor(250,250,250))
			palette.setColor(QtGui.QPalette.Base, QtGui.QColor(13,13,13))
			palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(53,53,53))
			palette.setColor(QtGui.QPalette.ToolTipBase, QtCore.Qt.white)
			palette.setColor(QtGui.QPalette.ToolTipText, QtCore.Qt.white)
			palette.setColor(QtGui.QPalette.Text, QtCore.Qt.white)
			palette.setColor(QtGui.QPalette.Button, QtGui.QColor(53,53,53))
			palette.setColor(QtGui.QPalette.ButtonText, QtCore.Qt.white)
			palette.setColor(QtGui.QPalette.BrightText, QtCore.Qt.red)
			palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(120,120,120).lighter())
			palette.setColor(QtGui.QPalette.HighlightedText, QtCore.Qt.black)
		self.setPalette(palette)
		print("[OK]Dark mode setting was set to",enabled)
	def __init__(self):
		super().__init__()
		#Initializing window
		#self.closeEvent=self.dontExit
		self.setDarkMode()
		self.left = 0
		self.top = 0
		self.title = 'Bajton helper'
		self.width = 1000
		self.height = 700
		self.setWindowTitle(self.title)
		self.setGeometry(self.left, self.top, self.width, self.height)
		#Checking user login
		if(isLoggedIn()==" "):
			loginForm(app)
		else:
			print("[OK]Last known login is valid")
		self.tabs_widget = Tabs(self)
		self.setCentralWidget(self.tabs_widget)
		parser = ConfigParser()
		parser.read('props.ini')
		if(parser["GUI"]["headless"]=="True"):
			self.setWindowState(Qt.WindowMinimized)
		self.show()
	def closeEvent(self,event):
		event.ignore()
		self.setWindowState(Qt.WindowMinimized)
if __name__ == '__main__':
	#Starting app, setting icon and style
	app = QApplication(sys.argv)
	app.setWindowIcon(QtGui.QIcon('icon.ico'))
	app.setStyle("Fusion")
	ex=App()
	sys.exit(app.exec_())