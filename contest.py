from configparser import ConfigParser
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import *
import requests
class Contests(QWidget):
	tableData=list()
	def initTable(self):
		#clear layout
		for i in reversed(range(self.layout.count())):
			self.layout.removeItem(self.layout.itemAt(i))
		self.tableData.clear()
		self.layout.addWidget(QLabel("If You want to use this app in password-protected contests, please enter passwords to this table.\nDouble-click on a password cell to edit."))
		self.tableWidget = QTableWidget()
		self.getList()
		self.tableWidget.setRowCount(len(self.tableData))
		self.tableWidget.setColumnCount(3)
		self.tableWidget.setHorizontalHeaderLabels(["Id","Name","Password"])
		header = self.tableWidget.horizontalHeader()       
		header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
		header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
		header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
		parser = ConfigParser()
		parser.read('props.ini')
		self.toExport=[]
		#Writing contests list with passwords to the table
		for i in range(len(self.tableData)):
			row=dict()
			row["title"]=self.tableData[i]["title"]
			row["id"]=str(self.tableData[i]["id"])
			titleItem=QTableWidgetItem(row["title"])
			titleItem.setFlags(QtCore.Qt.ItemIsEnabled)
			idItem=QTableWidgetItem(row["id"])
			idItem.setFlags(QtCore.Qt.ItemIsEnabled)
			self.tableWidget.setItem(i,0,idItem)
			self.tableWidget.setItem(i,1, titleItem)
			row["pass"]=""
			if(self.tableData[i]["contest_type"]=="Password Protected"):
				try:
					item=QTableWidgetItem()
					row["pass"]=parser["PASSWORDS"][str(self.tableData[i]["id"])]
					item.setText(row["pass"])
					self.tableWidget.setItem(i,2,item)
				except:
					self.tableWidget.setItem(i,2, QTableWidgetItem(""))
			else:
				notRequired=QTableWidgetItem("Not required")
				notRequired.setFlags(QtCore.Qt.ItemIsEnabled)
				self.tableWidget.setItem(i,2, notRequired)
			self.toExport.append(row)
		self.layout.addWidget(self.tableWidget)
		self.tableWidget.cellChanged.connect(self.setPassword)
		#import and export buttons
		options=QHBoxLayout()
		importBtn=QPushButton("Import")
		importBtn.clicked.connect(self.importPasswords)
		options.addWidget(importBtn)
		exportBtn=QPushButton("Export")
		exportBtn.clicked.connect(self.exportPasswords)
		options.addWidget(exportBtn)
		self.layout.addLayout(options)
	def __init__(self, parent):
		super(QWidget, self).__init__(parent)
		self.layout = QVBoxLayout()
		self.setLayout(self.layout)
		self.initTable()
		self.parent=parent
	def getList(self):
		lst=requests.get("http://bajton.vlo.gda.pl/api/contests?limit=100")
		data=lst.json()
		for i in data["data"]["results"]:
			self.tableData.append(i)
	def setPassword(self,row,col):
		parser = ConfigParser()
		parser.read('props.ini')
		#Adding or changing contest password in config file
		try:
			parser["PASSWORDS"][str(self.tableData[row]["id"])]=self.tableWidget.item(row,col).text()
		except:
			parser["PASSWORDS"]={self.tableData[row]["id"]:self.tableWidget.item(row,col).text()}
		with open('props.ini', 'w') as configfile:
			parser.write(configfile)
		print("[OK]Updated passwords data")
	######################
	def importPassword(self,id,passwd):
		parser = ConfigParser()
		parser.read('props.ini')
		#Adding or changing contest password in config file
		try:
			if(not (id.replace(" ","") in parser["PASSWORDS"])):
				print("[OK]Imported password for",id)
				parser["PASSWORDS"][id]=passwd
			else:
				print("[WARN]Skipped duplicate for",id)
		except KeyError:
			parser["PASSWORDS"]={id:passwd}
		with open('props.ini', 'w') as configfile:
			parser.write(configfile)
	def exportPasswords(self):
		fileName, _ = QFileDialog.getSaveFileName(self,"Export contests passwords","_judgeHelperExp","Plain text (*.txt)")
		if(fileName):
			print(fileName)
			with open(fileName,"w") as f:
				f.write('%-3s|%-50s|%-s\n' % ("ID", "Contest name", "Password"))
				for i in self.toExport:
					if(i["pass"]!=""):
						f.write('%-3s|%-50s|%-s\n' % (i["id"], i["title"], i["pass"]))
				f.write("Exported from Online Judge/Bajton helper app.")
	def importPasswords(self):
		fileName, _ = QFileDialog.getOpenFileName(self,"Import contests passwords","","Plain text (*.txt)")
		if(fileName):
			print(fileName)
			with open(fileName,"r") as f:
				for line in f.readlines():
					print(line)
					l=line.split("|")
					if(len(l)==3 and l[0]!="ID "):
						self.importPassword(l[0],l[2])
			self.initTable()
