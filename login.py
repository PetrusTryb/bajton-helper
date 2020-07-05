from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import *
from configparser import SafeConfigParser
import requests
import sys
import time
import os
def getSession():
	parser = SafeConfigParser()
	parser.read('props.ini')
	#Getting session id from config
	return parser["ACCOUNT"]["session"]
def isLoggedIn():
	print("[...]Checking session")
	parser = SafeConfigParser()
	parser.read('props.ini')
	c=dict()
	#Getting session id from config and checking it
	c["sessionid"]=parser["ACCOUNT"]["session"]
	try:
		r=requests.get("http://bajton.vlo.gda.pl/api/profile",cookies=c)
		if "id" in r.text:
			print(c)
			return c["sessionid"]
		else:
			print()
			return ' '
	except:
		hardError("Cannot connect to Online Judge. Server may be down.")
def logOut(forced=False,clear=False):
	#ask for permission to logout and exit
	if(not forced):
		box = QMessageBox()
		box.setIcon(QMessageBox.Question)
		box.setWindowTitle("Sign out and close?")
		box.setText("Are You sure that You want to log out and exit the app?")
		if(clear):
			box.setInformativeText("WARNING: Bajton Helper app data WILL BE PERMANENTLY REMOVED!")
		box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
		box.setDefaultButton(QMessageBox.No)
		buttonYes = box.button(QMessageBox.Yes)
		buttonYes.setText("Logout and exit")
		buttonNo = box.button(QMessageBox.No)
		buttonNo.setText("Cancel")
		box.exec_()
	else:
		hardError("You are not logged in. Please restart the app and sign in.")
	if(box.clickedButton() == buttonYes or forced):
		print("[...]Logging out")
		s = requests.Session()
		sessionId=getSession()
		cookie_obj = requests.cookies.create_cookie(domain='bajton.vlo.gda.pl',name='sessionid',value=sessionId)
		s.cookies.set_cookie(cookie_obj)
		#Closing session
		r = s.get(url = "http://bajton.vlo.gda.pl/api/logout")
		data = r.text
		print(data)
		parser = SafeConfigParser()
		parser.read('props.ini')
		parser["ACCOUNT"]={"session":""}
		with open('props.ini', 'w') as configfile:
			if(not clear):
				parser.write(configfile)
			else:
				configfile.write("")
		sys.exit()
def hardError(message):
	box = QMessageBox()
	box.setIcon(QMessageBox.Critical)
	box.setWindowTitle("Shit Outta Luck")
	box.setText("Bajton helper has stopped because of hard error:")
	box.setInformativeText(message)
	box.exec_()
	print("[CRITICAL ERROR]Killing app in 3 seconds")
	time.sleep(3)
	os.kill(os.getppid(),1)
class loginForm():
	def __init__(self,app):
		#Initializing form
		self.window = QWidget(windowTitle="Bajton helper")
		self.window.setWindowFlag(QtCore.Qt.WindowMaximizeButtonHint, False)
		self.window.closeEvent=self.fullExit
		layout = QVBoxLayout()
		loginLabel=QLabel('Please log-in using Bajton account. App will store only session id (not password).')
		loginBtn=QPushButton('Login')
		loginBtn.clicked.connect(lambda result:self.tryLogIn(app,login.text(),passwd.text()))
		cancelBtn=QPushButton('Cancel')
		cancelBtn.clicked.connect(self.fullExit)
		login=QLineEdit(placeholderText="Login")
		passwd=QLineEdit(placeholderText="Password")
		passwd.setEchoMode(QLineEdit.Password)
		layout.addWidget(loginLabel)
		layout.addWidget(login)
		layout.addWidget(passwd)
		layout.addWidget(loginBtn)
		layout.addWidget(cancelBtn)
		self.window.setLayout(layout)
		self.window.show()
		self.window.setFixedSize(layout.sizeHint())
		app.exec_()
	def closeForm(self,evnt):
		pass
	def fullExit(self,evnt):
		print("[INFO]Login cancelled, exiting")
		sys.exit(0)
	def tryLogIn(self,app,login,passwd):
		print("[...]Logging in as:",login)
		#Getting valid CSRF token
		s = requests.Session()
		csrfget=requests.get("http://bajton.vlo.gda.pl/api/profile")
		print("[OK]Obtained valid CSRF token:",csrfget.cookies.get_dict()["csrftoken"])
		h=dict()
		h["X-CSRFToken"]=csrfget.cookies.get_dict()["csrftoken"]
		h["Content-Type"]="application/json;charset=UTF-8"
		#Posting login form
		r = s.post(url = "http://bajton.vlo.gda.pl/api/login", data='{"username": "'+login+'", "password": "'+passwd+'"}',cookies=csrfget.cookies.get_dict(),headers=h)
		data = r.json()
		if "Succeeded" in data["data"]:
			sessid=s.cookies.get_dict()
			print("[OK]You are in! Session id: ",sessid["sessionid"])
			#Writing session id to config file
			parser = SafeConfigParser()
			parser.read('props.ini')
			parser["ACCOUNT"]={"session":sessid["sessionid"]}
			with open('props.ini', 'w') as configfile:
				parser.write(configfile)
			self.window.closeEvent=self.closeForm
			self.window.close()
		else:
			print("[ERROR]"+data["data"])
			#Displaying error dialog
			msg = QMessageBox()
			msg.setIcon(QMessageBox.Critical)
			msg.setText(data["data"])
			msg.setWindowTitle("Error")
			msg.exec_()