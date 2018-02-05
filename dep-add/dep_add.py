from verification import *
import os
import shutil
import tarfile
import gzip
import hashlib

def dep_add(telNr, utDate, ancDir):
	"""
	"""
	
	verify_date(utDate)
	utDate = utDate.replace('/', '-')
	year, month, day = utDate.split('-')
	year = int(year) - 2000

	assert ancDir != '', 'ancDir value is blank'
	tel = [1, 2]
	assert telNr not in tel, 'telNr not allowed'

	# Make ancDir/[nightly,udf]

	dirs = ['nightly', 'udf']
	for dir in dirs:
		ancDirNew = (ancDir, '/', dir)
		ancDirNew = ''.join(ancDirNew)
		if not os.path.isdir(ancDirNew):
			os.makedirs(ancDirNew)

	# Copy nightly data to ancDir/nightly

	joinSeq = ('/h/nightly', str(telNr), '/', str(year), '/', month, '/', day)
	nightlyDir = ''.join(joinSeq)
	if not os.path.isdir(nightlyDir):
		nightlyDir.replace('/h/', '/s/')
		if not os.path.isdir(nightlyDir):
			return

	files = ['envMet.arT', 'envFocus.arT']
	for file in files:
		source = (nightlyDir, '/', file)
		source = ''.join(source)
		if os.path.exists(source):
			destination = (ancDir, '/nightly/', file)
			destination = ''.join(destination)
			shutil.copyfile(source, destination)

def dep_tar(utDate, ancDir):
	"""
	"""
	
	verify_date(utDate)
	utDate = utDate.replace('/', '-')
	utDate = utDate.replace('-', '')

	assert ancDir != '', 'ancDir value is blank'
	
	if os.path.isdir(ancDir):

		# Tarball name
	
		tarFileName = ('anc', utDate, '.tar')
		tarFileName = ''.join(tarFileName)

	
		# Go to directory and create tarball

		os.chdir(ancDir)
		with tarfile.open(tarFileName, 'w:gz') as tar:
			tar.add('./')

		# gzip the tarball

		gzipTarFile = (tarFileName, '.gz')
		gzipTarFile = ''.join(gzipTarFile)
		with open(tarFileName, 'rb') as fIn:
			with gzip.open(gzipTarFile, 'wb') as fOut:
				shutil.copyfileobj(fIn, fOut)

		# Remove the original tar file

		os.remove(tarFileName)
	
		# Create md5sum of the tarball

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
			shutil.rmtree(delDir)
