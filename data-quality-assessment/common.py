from datetime import datetime

def semester(utDate):
	"""
	Returns the Keck observing semester for the supplied UT date

	semester('2017-08-01') --> 2017A
	semester('2017-08-02') --> 2017B

	A = Feb. 2 to Aug. 1 (UT)
	B = Aug. 2 to Feb. 1 (UT)
	"""

	utDate = utDate.replace('-', '')
	utDate = utDate.replace('/', '')

	try:
		utDate = datetime.strptime(utDate, '%Y%m%d')
	except ValueError:
		raise ValueError("Incorrect date format, should be YYYYMMDD")

	year = utDate.year
	month = utDate.month
	day = utDate.day

	# All of January and February 1 are semester B of previous year
	if month == 1 or (month == 2 and day == 1):
		semester = 'B'
		year -= 1
	# August 2 onward is semester B
	elif month >= 9 or (month == 8 and day >= 2):
		semester = 'B'
	else:
		semester = 'A'

	return str(year) + semester