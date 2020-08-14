import locale
from configparser import ConfigParser
#detect system language
if("pl" in locale.getdefaultlocale()[0].lower()):
	from strings_pl import *
else:
	from strings_en import *
#version number
string_version="v0010"
#API endpoint
parser = ConfigParser()
parser.read('props.ini')
try:
	string_api=parser["ACCOUNT"]["api"]
except:
	string_api="http://bajton.vlo.gda.pl/api/"
print("[INFO] Using API endpoint:",string_api)