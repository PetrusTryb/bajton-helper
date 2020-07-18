import locale
#detect system language
if("pl" in locale.getdefaultlocale()[0].lower()):
	from strings_pl import *
else:
	from strings_en import *