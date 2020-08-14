from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import *
from configparser import ConfigParser
import requests
import sys
import time
import os
from strings import *
def getSession():
	parser = ConfigParser()
	parser.read('props.ini')
	#Getting session id from config
	return parser["ACCOUNT"]["session"]
def isLoggedIn():
	print("[...]Checking session")
	parser = ConfigParser()
	parser.read('props.ini')
	c=dict()
	#Getting session id from config and checking it
	try:
		c["sessionid"]=parser["ACCOUNT"]["session"]
	except KeyError:
		parser["ACCOUNT"]=dict()
		return ' '
	try:
		r=requests.get(string_api+"profile",cookies=c)
		if "id" in r.text:
			print(c)
			return c["sessionid"]
		else:
			print()
			return ' '
	except:
		hardError(string_connect_error)
def logOut(forced=False,clear=False):
	#ask for permission to logout and exit
	if(not forced):
		box = QMessageBox()
		box.setIcon(QMessageBox.Question)
		box.setWindowTitle(string_logout)
		box.setText(string_logout_question)
		if(clear):
			box.setInformativeText(string_data_warning)
		box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
		box.setDefaultButton(QMessageBox.No)
		buttonYes = box.button(QMessageBox.Yes)
		buttonNo = box.button(QMessageBox.No)
		box.exec_()
	else:
		hardError(string_unauthorized)
	if(box.clickedButton() == buttonYes or forced):
		print("[...]Logging out")
		s = requests.Session()
		sessionId=getSession()
		cookie_obj = requests.cookies.create_cookie(domain='bajton.vlo.gda.pl',name='sessionid',value=sessionId)
		s.cookies.set_cookie(cookie_obj)
		#Closing session
		r = s.get(url = string_api+"logout")
		data = r.text
		print(data)
		parser = ConfigParser()
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
	box.setText(string_hard_error)
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
		api=QLineEdit(string_api+"",placeholderText="API")
		loginLabel=QLabel(string_login_desc)
		loginBtn=QPushButton('Ok')
		loginBtn.clicked.connect(lambda result:self.tryLogIn(app,login.text(),passwd.text(),api.text()))
		cancelBtn=QPushButton(string_exit)
		cancelBtn.clicked.connect(self.fullExit)
		login=QLineEdit(placeholderText="Nick")
		passwd=QLineEdit(placeholderText=string_password)
		passwd.setEchoMode(QLineEdit.Password)
		layout.addWidget(loginLabel)
		layout.addWidget(api)
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
	def tryLogIn(self,app,login,passwd,api):
		string_api=api
		print("[...]Logging in as:",login)
		#Getting valid CSRF token
		s = requests.Session()
		csrfget=requests.get(string_api+"profile")
		print("[OK]Obtained valid CSRF token:",csrfget.cookies.get_dict()["csrftoken"])
		h=dict()
		h["X-CSRFToken"]=csrfget.cookies.get_dict()["csrftoken"]
		h["Content-Type"]="application/json;charset=UTF-8"
		#Posting login form
		r = s.post(url = string_api+"login", data='{"username": "'+login+'", "password": "'+passwd+'"}',cookies=csrfget.cookies.get_dict(),headers=h)
		data = r.json()
		if "Succeeded" in data["data"]:
			sessid=s.cookies.get_dict()
			print("[OK]You are in! Session id: ",sessid["sessionid"])
			#Writing session id to config file
			parser = ConfigParser()
			parser.read('props.ini')
			parser["ACCOUNT"]={"session":sessid["sessionid"],"api":api}
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
			msg.setWindowTitle(string_login_error)
			msg.exec_()