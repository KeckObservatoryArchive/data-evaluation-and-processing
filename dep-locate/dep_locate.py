def dep_locate(instr, utDate, stageDir):
	"""
	"""
	
	verify_instrument()
	verify_date(utDate)
	assert stageDir != '', 'stageDir value is blank'

	# Which sdata disk?
	
	# Locate FITS files written in the last 24 hours
	
	# Verify FITS files and create stageDir/dep_locateINSTR.txt
	
