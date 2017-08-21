def koaid(instr, utDate, utc, instrume, outdir='', camera=''):
	"""
	Returns the KOAID for the input data

	KOAID = II.YYYYMMDD.######.fits
	   - II = instrument prefix
	   - YYYYMMDD = UT date of observation
	   - ###### = number of seconds into UT date

	koaid('HIRES', '2017-07-07', '01:00:00')

	Additional parameters are allowed for those instruments
	that have mulitple prefixes.  LRIS will use instrume,
	NIRSPEC and OSIRIS will use outdir, KCWI will use camera.
	"""

	# Verify the input parameters

	verify_instrument(instr)
	verify_date(utDate)
	verify_utc(utc)
	assert instrume != '', 'instrume value is blank'
	
	# Verify instrument and instrume values agree
	
	assert instr in instrume, 'instrument and instrume do not agree'
	
	# Covert to yyyy-mm-dd format
	
	utDate = utDate.replace('/', '-')

	# Split utc into individual elements and determine number of total seconds
	
	hour, minute, second = utc.split(':')
	total_seconds = str((int(hour) * 3600) + (int(minute) * 60) + float(second))
	total_seconds, _ = total_seconds.split('.')

	# Determine instrument prefix
	
	prefix = ''
	instrume = instrume.lower()
	easy_prefix = {'esi':'EI', 'hires':'HI', 'lris':'LR', 'lrisblue':'LB', 'mosfire':'MF', 'nirc2':'N2'}
	
	if instrume in easy_prefix:
		prefix = easy_prefix[instrume]
	else:
		
		# DEIMOS can also be FCS images
		
		if instrume == 'deimos':
			prefix = 'DE'
			if '/fcs' in outdir: prefix = 'DF'
		
		# KCWI prefix comes from the camera value
		
		elif instrume == 'kcwi':
			assert camera != '', 'camera value required for KCWI'
			if camera.lower() == 'blue': prefix = 'KB'
			elif camera.lower() == 'red': prefix = 'KR'
			elif camera.lower() == 'fpc': prefix = 'KF'
		
		# NIRSPEC prefix comes from the outdir value
		
		elif instrume == 'nirspec':
			assert outdir != '', 'outdir value required for NIRSPEC'
			if '/scam' in outdir: prefix = 'NC'
			elif '/spec' in outdir: prefix = 'NS'
		
		# OSIRIS prefix comes from the outdir value
		
		elif instrume == 'osiris':
			assert outdir != '', 'outdir value required for OSIRIS'
			if '/SCAM' in outdir: prefix = 'OI'
			elif '/SPEC' in outdir: prefix = 'OS'
		
	# KOAID prefix could not be determined
	
	assert prefix != '', 'cannot determine instrument prefix'

	# Construmct the KOAID
	
	koaid = prefix + '.' + utDate.replace('-', '') + '.' + total_seconds.zfill(5) + '.fits'

	return koaid
