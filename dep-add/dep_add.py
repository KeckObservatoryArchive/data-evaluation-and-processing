def dep_add(instr, utDate, ancDir):
	"""
	"""
	
	verify_instrument()
	verify_date(utDate)
	assert ancDir != '', 'ancDir value is blank'

	# Make ancDir/[nightly,udf]
	
	# Copy nightly data to ancDir/nightly
	
def dep_tar(instr, utDate, ancDir):
	"""
	"""
	
	verify_instrument()
	verify_date(utDate)
	assert ancDir != '', 'ancDir value is blank'
	
	# Go to ancDir and create a tarball of its contents
	
	date = utDate.replace('/', '-')
	date = date.replace('-', '')
	tarFile = 'anc' + date + '.tar'
	
	cd ancDir
	tar cvf tarFile ./
	gzip tarFile
	
	# Create md5sum of the tarball
	
	md5sum tarFile > tarFile.replace('.tar', '.md5sum')
	
