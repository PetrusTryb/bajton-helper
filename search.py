from configparser import ConfigParser
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import *
import requests
import threading
import sys,os,signal
from login import getSession,logOut
from strings import *
class SearchThread(QThread):
	results_ready = QtCore.pyqtSignal(object)
	def __init__(self, q,exclude="",pid=""):
		QThread.__init__(self)
		if(pid!=""):
			#need to find the placement node
			print("[INFO] Results will load in ref to resolved namespace")
		self.q=q
		self.row=0
		self.cNames=dict()
		self.results=list()
		self.states={"None":string_unsolved,"8":string_partial,"0":"OK","-1":string_wrong}
		self.exclude=exclude
		self.pid=pid
		print("[...]Starting thread")
	def run(self):
		if(len(self.q)>0):
			print("[...]Starting serach engine, query:",self.q)
			#list all contests
			lst=requests.get("http://bajton.vlo.gda.pl/api/contests?limit=99")
			self.allContests=lst.json()["data"]["results"]
			for i in (self.allContests):
				self.cNames[str(i["id"])]=i["title"]
				if(self.exclude!=""):
					#This means that search thread was started by auto-solver
					self.contestAnswersLookup(str(i["id"]))
				else:
					self.contestLookup(str(i["id"]))
			if(self.exclude!=""):
				#This means that search thread was started by auto-solver
				self.publicAnswersLookup()
			else:
				self.publicLookup()
		print(self.results)
		#emit completion event to search requester
		self.results_ready.emit(self.results)
	def checkContestAccess(self,cid):
		print("[...]Checking contest type: "+cid)
		parser = ConfigParser()
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
			#check contest access
			check=requests.get("http://bajton.vlo.gda.pl/api/contest/access?contest_id="+str(x["id"]),cookies=c)
			if("true" in check.text):
				return True
			else:
				try:
					#try to authenticate to the contest
					parser["PASSWORDS"][str(x["id"])]
					csrfget=requests.get("http://bajton.vlo.gda.pl/api/profile")
					h=dict()
					#obtain CSRF token
					h["X-CSRFToken"]=csrfget.cookies.get_dict()["csrftoken"]
					h["Content-Type"]="application/json;charset=UTF-8"
					c["csrftoken"]=csrfget.cookies.get_dict()["csrftoken"]
					test=requests.post("http://bajton.vlo.gda.pl/api/contest/password",headers=h,cookies=c,data='{"contest_id":"'+str(x["id"])+'","password":"'+parser["PASSWORDS"][str(x["id"])]+'"}')
					if('true' in test.text):
						return True
					else:
						print("[WARN]Authentication failed for "+str(x["title"])+":"+test.text)
				except:
					print("[WARN]No password found for "+str(x["title"]))
		return False
	def contestLookup(self,cid):
		if(self.checkContestAccess(cid)):
			c=dict()
			sessionId=getSession()
			c["sessionid"]=sessionId
			check=requests.get("http://bajton.vlo.gda.pl/api/contest/problem?contest_id="+cid,cookies=c)
			data=check.json()["data"]
			#find matching problem in contest
			for i in data:
				if(self.q in i["title"].lower() or self.q in i["_id"].lower()):
					self.results.append({"_id":i["_id"],"id":i["id"],"title":i["title"],"cName":self.cNames[cid],"cId":cid,"status":self.states[str(i["my_status"])]})
	def publicLookup(self):
		c=dict()
		sessionId=getSession()
		c["sessionid"]=sessionId
		check=requests.get("http://bajton.vlo.gda.pl/api/problem?limit=99",cookies=c)
		data=check.json()["data"]["results"]
		#find matching problem in public problems
		for i in data:
			if(self.q in i["title"].lower() or self.q in i["_id"].lower()):
				self.results.append({"_id":i["_id"],"id":i["id"],"title":i["title"],"cName":"Public problems","cId":"-1","status":self.states[str(i["my_status"])]})
	def publicAnswersLookup(self):
		c=dict()
		sessionId=getSession()
		c["sessionid"]=sessionId
		check=requests.get("http://bajton.vlo.gda.pl/api/submissions?myself=1&result=0&limit=250",cookies=c)
		data=check.json()["data"]["results"]
		#loop through job instances to get the latest success publish
		for i in data:
			if(self.q in i["problem"].lower()):
				self.results.append({"id":str(i["id"]),"cName":"Public problems","language":i["language"],"cId":"-1","target":self.exclude,"pid":self.pid})
	def contestAnswersLookup(self,cid):
		if(self.checkContestAccess(cid)):
			c=dict()
			sessionId=getSession()
			c["sessionid"]=sessionId
			check=requests.get("http://bajton.vlo.gda.pl/api/contest_submissions?myself=1&result=0&limit=250&contest_id="+cid,cookies=c)
			data=check.json()["data"]["results"]
			#loop through job instances to get the latest success publish
			for i in data:
				if(self.q in i["problem"].lower()):
					self.results.append({"id":str(i["id"]),"cName":self.cNames[cid],"language":i["language"],"cId":cid,"target":self.exclude,"pid":self.pid})
class Search(QWidget):
	def __init__(self, parent):
		super(QWidget, self).__init__(parent)
		self.layout = QVBoxLayout()
		self.layout.addWidget(QLabel(string_search_desc))
		self.waitLabel=QLabel(string_searching)
		self.layout.addWidget(self.waitLabel)
		self.waitLabel.hide()
		self.query=QLineEdit(placeholderText=string_problem_name)
		#creating table
		self.layout.addWidget(self.query)
		self.tableWidget = QTableWidget()
		self.tableWidget.setRowCount(0)
		self.tableWidget.setColumnCount(5)
		self.tableWidget.setHorizontalHeaderLabels(["Id",string_name,string_contest_name,"Status",string_actions])
		header = self.tableWidget.horizontalHeader()
		header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
		header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
		header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
		header.setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)
		header.setSectionResizeMode(4, QtWidgets.QHeaderView.Stretch)
		self.layout.addWidget(self.tableWidget)
		self.setLayout(self.layout)
		self.query.returnPressed.connect(self.search)
		self.inProgress=False
	def search(self):
		if(not self.inProgress):
			#disable input box
			self.query.setDisabled(True)
			self.waitLabel.show()
			self.inProgress=True
			self.threads=[]
			#start search thread
			st=SearchThread(self.query.text().lower())
			st.results_ready.connect(self.showResults)
			self.threads.append(st)
			st.start()
	def showResults(self,data):
		#clear table
		self.tableWidget.setRowCount(0)
		self.row=0
		#process sequential verts
		for i in data:
			self.row+=1
			self.tableWidget.setRowCount(self.row)
			idItem=QTableWidgetItem(i["cId"]+"/"+i["_id"]+"/"+str(i["id"]))
			idItem.setFlags(QtCore.Qt.ItemIsEnabled)
			titleItem=QTableWidgetItem(i["title"])
			titleItem.setFlags(QtCore.Qt.ItemIsEnabled)
			cNameItem=QTableWidgetItem(i["cName"])
			cNameItem.setFlags(QtCore.Qt.ItemIsEnabled)
			statusItem=QTableWidgetItem(i["status"])
			statusItem.setFlags(QtCore.Qt.ItemIsEnabled)
			if(i["status"]=="OK"):
				solveBtn=QLabel(string_no_actions)
			else:
				solveBtn=QPushButton(string_auto_solve)
				solveBtn.clicked.connect(self.trySolve)
			self.tableWidget.setItem(self.row-1,0,idItem)
			self.tableWidget.setItem(self.row-1,1,titleItem)
			self.tableWidget.setItem(self.row-1,2,cNameItem)
			self.tableWidget.setItem(self.row-1,3,statusItem)
			self.tableWidget.setCellWidget(self.row-1,4,solveBtn)
		#enable input box and hide "please wait" status label
		self.inProgress=False
		self.query.setDisabled(False)
		self.waitLabel.hide()
	####################################################################
	'''
		cid - contest id (number)
		pn - problem name (short text id)
		id - problem id (number)
	'''
	def trySolve(self):
		#check wchich button was clicked
		buttonClicked = self.sender()
		index = self.tableWidget.indexAt(buttonClicked.pos())
		cid=(self.tableWidget.item(index.row(),0).text()).split("/")[0]
		pn=(self.tableWidget.item(index.row(),0).text()).split("/")[1]
		id=(self.tableWidget.item(index.row(),0).text()).split("/")[2]
		lst=requests.get("http://bajton.vlo.gda.pl/api/contest?id="+cid)
		if(lst.json()["data"]["status"]!="0"):
			self.error(string_contest_invalid)
			return
		print("[...]Looking up for Your submissions: "+id)
		self.threads=[]
		#start search thread
		st=SearchThread(pn.lower(),cid,id)
		st.results_ready.connect(self.finishAutoSolve)
		self.threads.append(st)
		st.start()
		self.showProgress(string_solving)
	def finishAutoSolve(self,data):
		self.prog.close()
		if(len(data)==0):
			print("[ERROR]Failed to find correct answer.")
			self.error(string_solve_failed)
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
	######################
	def error(self,text):
		msg = QMessageBox()
		msg.setIcon(QMessageBox.Critical)
		msg.setText(text)
		msg.setInformativeText(string_note)
		msg.setWindowTitle(string_solve_error)
		msg.exec_()
	def showProgress(self,text):
		self.prog = QProgressDialog()
		self.prog.setLabelText(text)
		self.prog.setValue(-1)
		self.prog.setMinimum(0)
		self.prog.setMaximum(0)
		self.prog.setWindowTitle(string_searching)
		self.prog.setCancelButton(None)
		self.prog.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)
		self.prog.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)
		self.prog.exec_()