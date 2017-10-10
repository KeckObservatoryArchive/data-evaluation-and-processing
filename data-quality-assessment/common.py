from datetime import datetime

def semester(keywords, utDate):
	"""
	Determines the Keck observing semester for the supplied UT date

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

	keywords['SEMESTER'] = semester

def koaid(keywords, utDate):
	'''
	Determines the KOAID

	KOAID = II.YYYYMMDD.######.fits
	   - II = instrument prefix
	   - YYYYMMDD = UT date of observation
	   - ###### = number of seconds into UT date
	 '''

	utc = keywords['UTC']
	try:
		utc = datetime.strptime(utc, '%H:%M:%S')
	except ValueError:
		raise ValueError

	hour = utc.hour
	minute = utc.minute
	second = utc.second

	totalSeconds = str((hour * 3600) + (minute * 60) + second)

	instr_prefix = {'esi':'EI', 'hires':'HI', 'lris':'LR', 'lrisblue':'LB', 'mosfire':'MF', 'nirc2':'N2'}

	instr = keywords['INSTRUME'].lower()
	outdir = keywords['OUTDIR']
	camera = keywords['CAMERA'].lower()

	if instr in instr_prefix:
		prefix = instr_prefix[instr]
	elif instr == 'deimos':
		if '/fcs' in outdir:
			prefix = 'DF'
		else:
			prefix = 'DE'
	elif instr == 'kcwi':
		if camera == 'blue':
			prefix = 'KB'
		elif camera == 'red':
			prefix = 'KR'
		elif camera == 'fpc':
			prefix = 'KF'
	elif instr == 'nirspec':
		if '/scam' in outdir:
			prefix = 'NC'
		elif '/spec' in outdir:
			prefix = 'NC'
	elif instr == 'osiris':
		if '/SCAM' in outdir:
			prefix = 'OI'
		elif '/SPEC' in 'osiris':
			prefix = 'OS'
	else:
		raise Exception('Cannot determine prefix')

	# Will utDate be a string, int, or datetime object?
	koaid = prefix + '.' + utDate + '.' + totalSeconds.zfill(5) + '.fits'
	keywords['KOAID'] = koaid
