dep_transfer(instr, utDate, stageDir, tpx=tpx):
	"""
	"""
	
	verify_instrument()
	verify_date(utDate)
	assert stageDir != '', 'stageDir value is blank'

	# Copy files listed in stageDir/dep_locateINSTR.txt to stageDir/summitDisk...
	
	# Update database (ondisk_stat, ondisk_time)
	
