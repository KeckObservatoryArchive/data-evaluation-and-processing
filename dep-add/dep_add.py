from verification import *
import os
import shutil
import tarfile
import gzip
import hashlib

def dep_add(telNr, utDate, ancDir, log_writer=''):
	"""
	This function will add the weather and focus log files to 
	the ancillary directory.  Log files are copied from either
	/h/nightly#/yy/mm/dd or /s/nightly#/yy/mm/dd.

	@param telNr: Telescope number
	@type telnr: string
	@param utDate: UT date (yyyy-mm-dd)
	@type utDate: string
	@param ancDir: ancillary directry
	@type ancDir: string
	"""
	
	verify_date(utDate)
	utDate = utDate.replace('/', '-')
	year, month, day = utDate.split('-')
	year = int(year) - 2000

	assert ancDir != '', 'ancDir value is blank'
	tel = [1, 2]
	assert telNr not in tel, 'telNr not allowed'

	if log_writer:
		log_writer.info('dep_add.py started for telnr {} {}'.format(telNr, utDate))

	# Make ancDir/[nightly,udf]

	dirs = ['nightly', 'udf']
	for dir in dirs:
		ancDirNew = (ancDir, '/', dir)
		ancDirNew = ''.join(ancDirNew)
		if not os.path.isdir(ancDirNew):
			if log_writer:
				log_writer.info('dep_add.py creating {}'.format(ancDirNew))
			os.makedirs(ancDirNew)

	# Copy nightly data to ancDir/nightly

	joinSeq = ('/h/nightly', str(telNr), '/', str(year), '/', month, '/', day)
	nightlyDir = ''.join(joinSeq)
	if not os.path.isdir(nightlyDir):
		nightlyDir.replace('/h/', '/s/')
		if not os.path.isdir(nightlyDir):
			if log_writer:
				log_writer.info('dep_add.py no nightly directory found')
			return

	files = ['envMet.arT', 'envFocus.arT']
	for file in files:
		source = (nightlyDir, '/', file)
		source = ''.join(source)
		if os.path.exists(source):
			destination = (ancDir, '/nightly/', file)
			destination = ''.join(destination)
			if log_writer:
				log_writer.info('dep_add.py copying {} to {}'.format(source, destination))
			shutil.copyfile(source, destination)

def dep_tar(utDate, ancDir):
	"""
	This function will tar the ancillary directory, gzip that
	tarball and remove the original contents of the directory.

	@param utDate: UT date (yyyy-mm-dd)
	@type utDate: string
	@param ancDir: ancillary directry
	@type ancDir: string
	"""
	
	verify_date(utDate)
	utDate = utDate.replace('/', '-')
	utDate = utDate.replace('-', '')

	assert ancDir != '', 'ancDir value is blank'
	
	if log_writer:
		log_writer.info('dep_tar.py started for {}'.format(ancDir))

	if os.path.isdir(ancDir):

		# Tarball name
	
		tarFileName = ('anc', utDate, '.tar')
		tarFileName = ''.join(tarFileName)

	
		# Go to directory and create tarball

		if log_writer:
			log_writer.info('dep_tar.py creating {}'.format(tarFileName))
		os.chdir(ancDir)
		with tarfile.open(tarFileName, 'w:gz') as tar:
			tar.add('./')

		# gzip the tarball

		if log_writer:
			log_writer.info('dep_tar.py gzipping {}'.format(tarFileName))
		gzipTarFile = (tarFileName, '.gz')
		gzipTarFile = ''.join(gzipTarFile)
		with open(tarFileName, 'rb') as fIn:
			with gzip.open(gzipTarFile, 'wb') as fOut:
				shutil.copyfileobj(fIn, fOut)

		# Remove the original tar file

		os.remove(tarFileName)
	
		# Create md5sum of the tarball

		if log_writer:
			log_writer.info('dep_tar.py creating {}'.format(md5sumFile))

		md5sumFile = gzipTarFile.replace('tar.gz', 'md5sum')
		md5 = hashlib.md5(open(gzipTarFile, 'rb').read()).hexdigest()

		with open(md5sumFile, 'w') as f:
			md5 = (md5, '  ', gzipTarFile)
			md5 = ''.join(md5)
			f.write(md5)

		dirs = ['nightly', 'udf']
		for dir in dirs:
			delDir = (ancDir, '/', dir)
			delDir = ''.join(delDir)
			if log_writer:
				log_writer.info('dep_tar.py removing {}'.format(delDir))
			shutil.rmtree(delDir)
