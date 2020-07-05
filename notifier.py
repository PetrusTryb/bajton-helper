from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import *
from configparser import SafeConfigParser
from login import getSession
from search import SearchThread
import datetime
import requests
import threading
import schedule
import time
import sys
class SystemTrayIcon(QSystemTrayIcon):
	def __init__(self, icon, parent=None):
		#init tray icon
		QSystemTrayIcon.__init__(self, icon, parent)
		#init context menu
		menu = QMenu(parent)
		exitAction = menu.addAction("Exit")
		exitAction.triggered.connect(sys.exit)
		self.setContextMenu(menu)
class BackgroundService(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.trayIcon = SystemTrayIcon(QtGui.QIcon("icon.ico"))
		self.trayIcon.setToolTip("Bajton helper")
		self.trayIcon.show()
		self.threads=[]
	def tick(self):
		if(self.config["publicMode"]!="None"):
			self.checkPublic()
		if(self.config["contestMode"]!="None"):
			self.checkContests()
		if(self.config["contestAlert"]!="None"):
			self.checkContestsDeadlines()
		print("_____________________________________")
	def run(self):
		while(1):
			schedule.run_pending()
			time.sleep(1)
	def pushConfig(self,fullConfig):
		self.config=fullConfig["NOTIFICATIONS"]
		self.parser=fullConfig
		schedule.clear()
		mult={"minutes":60,"hours":60*60,"seconds":1}
		schedule.every(int(self.config["interval"])*mult[self.config["intervalType"]]).seconds.do(self.tick)
	def checkPublic(self):
		try:
			last=int(self.parser["CACHE"]["publicCount"])
		except KeyError:
			self.parser["CACHE"]=dict()
			last=-1
		print("[...]Checking public problems updates")
		print(last)
		c=dict()
		sessionId=getSession()
		c["sessionid"]=sessionId
		check=requests.get("http://bajton.vlo.gda.pl/api/problem?limit=99",cookies=c)
		data=check.json()["data"]["results"]
		print(len(data))
		autoFilled=0
		for i in range(last,len(data)):
			#notify only when problem is not already solved
			if(data[i]["my_status"]!=0):
				self.trayIcon.showMessage("New public problem",data[i]["title"])
				if(self.config["publicMode"]=="Auto"):
					if(self.trySolve("-1",data[i]["_id"],str(data[i]["id"]))):
						autoFilled+=1
		if(autoFilled>0):
			self.trayIcon.showMessage(str(autoFilled)+" problems auto-filled!","We have copied Your previous answers so You don't have to solve these problems again.")
		self.parser["CACHE"]["publicCount"]=str(len(data))
		with open('props.ini', 'w') as configfile:
			self.parser.write(configfile)
	def checkContestsDeadlines(self):
		print("[...]Checking contests deadlines")
		#list all contests
		lst=requests.get("http://bajton.vlo.gda.pl/api/contests?limit=99&status=0")
		self.allContests=lst.json()["data"]["results"]
		for i in (self.allContests):
			deadlineTime=datetime.datetime.fromisoformat(i["end_time"][:-1])
			now=datetime.datetime.utcnow()
			delta=deadlineTime-now
			currency=self.config["contestAlert"].split()[1]
			offset=int(self.config["contestAlert"].split()[0])
			if((currency=="days" and delta.days<offset) or (currency=="hours" and delta.days==0 and delta.seconds//60//60<offset) or (currency=="minutes" and delta.days==0 and delta.seconds//60<offset)):
				self.trayIcon.showMessage("Contest alert",i["title"]+" is ending in less than "+self.config["contestAlert"])
	def checkContests(self):
		print("[...]Checking contests updates")
		#list all contests
		lst=requests.get("http://bajton.vlo.gda.pl/api/contests?limit=99&status=0")
		self.allContests=lst.json()["data"]["results"]
		self.cNames=dict()
		for i in (self.allContests):
			self.cNames[str(i["id"])]=i["title"]
			self.contestLookup(str(i["id"]))
	def contestLookup(self,cid):
		if(self.checkContestAccess(cid)):
			c=dict()
			sessionId=getSession()
			c["sessionid"]=sessionId
			check=requests.get("http://bajton.vlo.gda.pl/api/contest/problem?contest_id="+cid,cookies=c)
			data=check.json()["data"]
			try:
				if(str(cid) not in self.parser["CACHE"]):
					self.parser["CACHE"][str(cid)]=""
			except KeyError:
				self.parser["CACHE"]=dict()
				self.parser["CACHE"][str(cid)]=""
			autoFilled=0
			for p in data:
				if(str(p["id"]) not in self.parser["CACHE"][str(cid)].split(";") and p["my_status"]!=0):
					self.trayIcon.showMessage(self.cNames[cid],"New problem: "+p["title"])
					if(self.config["contestMode"]=="Auto"):
						if(self.trySolve(cid,p["_id"],str(p["id"]))):
							autoFilled+=1
					self.parser["CACHE"][str(cid)]+=str(p["id"])+";"
			if(autoFilled>0):
				self.trayIcon.showMessage(str(autoFilled)+" problems auto-filled!","We have copied Your previous answers so You don't have to solve these problems again.")
			with open('props.ini', 'w') as configfile:
				self.parser.write(configfile)
	def checkContestAccess(self,cid):
		print("[...]Checking contest type: "+cid)
		parser = SafeConfigParser()
		parser.read('props.ini')
		c=dict()
		#getting session id
		sessionId=getSession()
		c["sessionid"]=sessionId
		r=requests.get("http://bajton.vlo.gda.pl/api/contest?id="+cid,cookies=c)
		print(r)
		x=r.json()["data"]
		#print(cid,x)
		if(x["contest_type"]!="Password Protected"):
				return True
		else:
			csrfget=requests.get("http://bajton.vlo.gda.pl/api/profile")
			h=dict()
			#obtain CSRF token
			h["X-CSRFToken"]=csrfget.cookies.get_dict()["csrftoken"]
			h["Content-Type"]="application/json;charset=UTF-8"
			c["csrftoken"]=csrfget.cookies.get_dict()["csrftoken"]
			#check contest access
			check=requests.get("http://bajton.vlo.gda.pl/api/contest/access?contest_id="+str(x["id"]),cookies=c)
			if("true" in check.text):
				return True
			else:
				try:
					#try to authenticate to the contest
					parser["PASSWORDS"][str(x["id"])]
					test=requests.post("http://bajton.vlo.gda.pl/api/contest/password",headers=h,cookies=c,data='{"contest_id":"'+str(x["id"])+'","password":"'+parser["PASSWORDS"][str(x["id"])]+'"}')
					if('true' in test.text):
						return True
					else:
						print("[WARN]Authentication failed for "+str(x["title"])+":"+test.text)
				except:
					print("[WARN]No password found for "+str(x["title"]))
		return False
	######
	def trySolve(self,cid="",pn="",id=""):
		print("[...]Looking up for Your submissions: "+id)
		#start search thread
		st=SearchThread(pn.lower(),cid,id)
		st.results_ready.connect(self.finishAutoSolve)
		self.threads.append(st)
		st.start()
	def finishAutoSolve(self,data):
		if(len(data)==0):
			print("[ERROR]Failed to find correct answer.")
			return False
		else:
			print("[...]Copying answer")
			code=self.getCode(data[0]["id"])
			self.pushCode(code,data[0]["language"],data[0]["pid"],data[0]["target"])
			return True
	def getCode(self,id):
		c=dict()
		sessionId=getSession()
		c["sessionid"]=sessionId
		check=requests.get("http://bajton.vlo.gda.pl/api/submission?id="+id,cookies=c)
		data=check.json()["data"]["code"]
		return data.replace("\n","\\n").replace("\t","\\t").replace("\"",'\\"')
	def pushCode(self,code,lang,id,cid):
		sessionId=getSession()
		s = requests.Session()
		cookie_obj = requests.cookies.create_cookie(domain='bajton.vlo.gda.pl',name='sessionid',value=sessionId)
		s.cookies.set_cookie(cookie_obj)
		csrfget=requests.get("http://bajton.vlo.gda.pl/api/profile")
		print("[OK]Obtained valid CSRF token:",csrfget.cookies.get_dict()["csrftoken"])
		h=dict()
		h["X-CSRFToken"]=csrfget.cookies.get_dict()["csrftoken"]
		h["Content-Type"]="application/json;charset=UTF-8"
		#Posting submission form
		if(cid==-1):
			#Push to public problems
			r = s.post(url = "http://bajton.vlo.gda.pl/api/submission", data='{"code": "'+code+'", "language": "'+lang+'", "problem_id": "'+id+'"}',cookies=csrfget.cookies.get_dict(),headers=h)
		else:
			#Push to contest
			r = s.post(url = "http://bajton.vlo.gda.pl/api/submission", data='{"code": "'+code+'", "language": "'+lang+'", "contest_id": "'+cid+'", "problem_id": "'+id+'"}',cookies=csrfget.cookies.get_dict(),headers=h)
		data = r.json()
		print(data)
class Notifier(QWidget):
	def readConfig(self):
		self.parser.read('props.ini')
		try:
			self.config=self.parser["NOTIFICATIONS"]
		except:
			print("[WARN]Notification config is empty or corrupted, applying defaults")
			self.config={"interval":"160",
			"intervalType":"minutes",
			"publicMode":"None",
			"contestMode":"None",
			"contestAlert":"None"}
			self.parser["NOTIFICATIONS"]=self.config
	def updateConfig(self):
		self.parser["NOTIFICATIONS"]=self.config
		with open('props.ini', 'w') as configfile:
			self.parser.write(configfile)
		self.initControls()
	def initControls(self):
		self.readConfig()
		self.publicNotify.setChecked(self.config["publicMode"]!="None")
		self.publicAuto.setChecked(self.config["publicMode"]=="Auto")
		self.publicAuto.setDisabled(self.config["publicMode"]=="None")
		
		self.contestNotify.setChecked(self.config["contestMode"]!="None")
		self.contestAuto.setChecked(self.config["contestMode"]=="Auto")
		self.contestAuto.setDisabled(self.config["contestMode"]=="None")

		self.lazyNotify.setChecked(self.config["contestAlert"]!="None")
		self.lazyDays.setDisabled(self.config["contestAlert"]=="None")
		self.cb.setDisabled(self.config["contestAlert"]=="None")
		if(self.config["contestAlert"]!="None"):
			self.lazyDays.setValue(int(self.config["contestAlert"].split()[0]))
			opts=["days","hours","minutes"]
			self.cb.setCurrentIndex(opts.index(self.config["contestAlert"].split()[1]))
		opts=["hours","minutes","seconds"]
		self.checkTime.setValue(int(self.config["interval"]))
		self.checkTimeCombo.setCurrentIndex(opts.index(self.config["intervalType"]))

		self.svc.pushConfig(self.parser)
	def calcSleepTime(self):
		sTime=int(self.config["interval"])
		if(self.config["intervalType"]=="minutes"):
			sTime*=60
		elif(self.config["intervalType"]=="hours"):
			sTime*=3600
		return sTime
	def publicToggle(self):
		if(self.publicNotify.isChecked()):
			if(self.publicAuto.isChecked()):
				self.config["publicMode"]="Auto"
			else:
				self.config["publicMode"]="Notify"
		else:
			self.config["publicMode"]="None"
		#print("[...]Applying new public problems settings")
		self.updateConfig()
	def contestToggle(self):
		if(self.contestNotify.isChecked()):
			if(self.contestAuto.isChecked()):
				self.config["contestMode"]="Auto"
			else:
				self.config["contestMode"]="Notify"
		else:
			self.config["contestMode"]="None"
		#print("[...]Applying new contests settings")
		self.updateConfig()
	def alertToggle(self):
		if(self.lazyNotify.isChecked()):
			self.config["contestAlert"]=str(self.lazyDays.value())+" "+self.cb.currentText()
		else:
			self.config["contestAlert"]="None"
		#print("[...]Applying new contest alert settings")
		self.updateConfig()
	def intervalChange(self):
		self.config["interval"]=str(self.checkTime.value())
		self.config["intervalType"]=self.checkTimeCombo.currentText()
		#print("[...]Applying new fetch interval settings")
		self.updateConfig()
	def __init__(self, parent):
		super(QWidget, self).__init__(parent)
		self.parser = SafeConfigParser()
		self.svc=BackgroundService()
		self.svc.daemon=True
		self.svc.start()
		self.layout = QVBoxLayout()
		self.layout.addWidget(QLabel("Here You can manage notifications service.\nPlease note that this function is experimental.\nIt will work only when the app is running - please check autostart options in Settings."))
		groupBox1 = QGroupBox("Public problems")
		self.publicNotify = QCheckBox("Notify about new problems")
		self.publicNotify.clicked.connect(self.publicToggle)
		self.publicAuto = QCheckBox("Fill automatically if previously solved")
		self.publicAuto.clicked.connect(self.publicToggle)
		vbox = QVBoxLayout()
		vbox.addWidget(self.publicNotify)
		vbox.addWidget(self.publicAuto)
		groupBox1.setLayout(vbox)
		self.layout.addWidget(groupBox1)
		groupBox2 = QGroupBox("Contests")
		self.contestNotify = QCheckBox("Notify about new problems")
		self.contestNotify.clicked.connect(self.contestToggle)
		self.contestAuto = QCheckBox("Fill automatically if previously solved")
		self.contestAuto.clicked.connect(self.contestToggle)
		self.lazyNotify = QCheckBox("Notify about ending contests when deadline is closer than:")
		self.lazyNotify.clicked.connect(self.alertToggle)
		self.lazyDays = QSpinBox()
		self.lazyDays.setMinimum(1)
		self.lazyDays.valueChanged.connect(self.alertToggle)
		vbox2 = QVBoxLayout()
		vbox2.addWidget(self.contestNotify)
		vbox2.addWidget(self.contestAuto)
		vbox2.addWidget(self.lazyNotify)
		vbox2.addWidget(self.lazyDays)
		self.cb = QComboBox()
		self.cb.addItems(["days", "hours", "minutes"])
		self.cb.currentIndexChanged.connect(self.alertToggle)
		vbox2.addWidget(self.cb)
		groupBox2.setLayout(vbox2)
		self.layout.addWidget(groupBox2)
		groupBox3=QGroupBox("Check interval")
		vbox3 = QVBoxLayout()
		self.checkTime = QSpinBox()
		self.checkTime.setMinimum(1)
		self.checkTime.editingFinished.connect(self.intervalChange)
		self.checkTimeCombo = QComboBox()
		self.checkTimeCombo.addItems(["hours","minutes","seconds"])
		self.checkTimeCombo.currentIndexChanged.connect(self.intervalChange)
		vbox3.addWidget(self.checkTime)
		vbox3.addWidget(self.checkTimeCombo)
		forceCheckbtn=QPushButton("Check now")
		forceCheckbtn.clicked.connect(self.svc.tick)
		vbox3.addWidget(forceCheckbtn)
		groupBox3.setLayout(vbox3)
		self.layout.addWidget(groupBox3)
		self.initControls()
		self.setLayout(self.layout)