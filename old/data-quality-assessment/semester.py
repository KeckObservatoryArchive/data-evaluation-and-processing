from verification import *

def semester(utDate):
	"""
	Returns the Keck observing semester for the supplied UT date

	semester('2017-08-01') --> 2017A
	semester('2017-08-02') --> 2017B

	A = Feb. 2 to Aug. 1 (UT)
	B = Aug. 2 to Feb. 1 (UT)
	"""

	# Verify date format
	
	verify_date(utDate)
	
	# In case /'s were used, replace with -'s

	utDate = utDate.replace('/', '-')

	# Get individual values and convert them to integers

	year, month, day = utDate.split('-')
	year = int(year)
	month = int(month)
	day = int(day)

	# Default semester

	semester = 'A'

	# All of January and February 1 are semester B of previous year

	if month == 1 or (month == 2 and day == 1):
		semester = 'B'
		year -= 1

	# August 2 onward is semester B

	if month >= 9 or (month == 8 and day >= 2): semester = 'B'

	return str(year) + semester
