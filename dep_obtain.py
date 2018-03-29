from datetime import datetime, timedelta
from pytz import timezone
from verification import *
import os
import json
import urllib.request

def dep_obtain(instr, utDate, stageDir, log_writer=''):
	"""
	Queries the telescope schedule database and creates the following files
	in stageDir:

	dep_obtainINSTR.txt
	dep_notschedINSTR.txt (if no entries fouund in database)

	@param instr: instrument name
	@type instr: string
	@param utDate: UT date (yyyy-mm-dd)
	@type utDate: string
	@param stageDir: path to staging directory
	@type staageDir: string
	"""

	# Verify the supplied instrument and UT date are allowed values/formats

	verify_instrument(instr)
	verify_date(utDate)
	utDate = utDate.replace('/', '-')

	if log_writer:
		log_writer.info('dep_obtain.py started for {} {} UT'.format(instr.upper(), utDate))

	# Verify that the stage directory exists.  If not, then make it.

	assert stageDir != '', 'stageDir value is blank'
	if not os.path.isdir(stageDir):
		if log_writer:
			log_writer.info('dep_obtain.py making stage directory {}'.format(stageDir))
		os.makedirs(stageDir)

	# Get HST from utDate

	utDateObj = datetime.strptime(utDate, '%Y-%m-%d')
	hstDateObj = utDateObj - timedelta(days=1)
	hstDate = hstDateObj.strftime('%Y-%m-%d')

	# URL to query telescope schedule

	url = ('https://www.keck.hawaii.edu/software/db_api/telSchedule.php', '?')
	schedUrl = url + ('cmd=getSchedule', '&date=', hstDate, '&instr=', instr.upper())
	schedUrl = ''.join(schedUrl)


	# Output files

	notScheduledFile = (stageDir, '/dep_notsched', instr.upper(), '.txt')
	notScheduledFile = ''.join(notScheduledFile)
	obtainFile = (stageDir, '/dep_obtain', instr.upper(), '.txt')
	obtainFile = ''.join(obtainFile)

	try:
		if log_writer:
			log_writer.info('dep_obtain.py retrieving telescope schedule information for {}'.format(instr.upper()))

		# Read the input URL

		data = urllib.request.urlopen(schedUrl)
		data = data.read().decode('utf8')	# Convert from byte to ascii
		if len(data) > 0:
			data = json.loads(data)			# Convert to Python list
		if isinstance(data, dict):
			data = [data]

		# Get the telescope number

		sendUrl = url + ('cmd=getTelnr&instr=', instr.upper())
		sendUrl = ''.join(sendUrl)
		telGet = urllib.request.urlopen(sendUrl)
		telGet = telGet.read().decode('utf8')       # Convert from byte to ascii
		telGet = json.loads(telGet)                 # Convert to Python list
		telnr = telGet['TelNr']

		# Get OA

		oaUrl = url + ('cmd=getNightStaff', '&date=', hstDate)
		oaUrl = oaUrl + ('&telnr=', str(telnr), '&type=oa')
		oaUrl = ''.join(oaUrl)
		oaGet = urllib.request.urlopen(oaUrl)
		oaGet = oaGet.read().decode('utf8')
		oa = 'None'
		if len(oaGet) > 0:
			oaGet = json.loads(oaGet)
			if isinstance(oaGet, dict):
				oa = oaGet['Alias']
			else:
				for entry in oaGet:
					if entry['Type'] == 'oa':
						oa = entry['Alias']

		# No entries found
		# Create stageDir/dep_notschedINSTR.txt and dep_obtainINSTR.txt

		if len(data) == 0:
			if log_writer:
				log_writer.info('dep_obtain.py no information found for {}'.format(instr.upper()))

			with open(notScheduledFile, 'w') as fp:
				fp.write('{} not scheduled'.format(instr.upper()))

			with open(obtainFile, 'w') as fp:
				fp.write('{} {} NONE NONE NONE NONE NONE'.format(hstDate, oa))

		# Entries found
		# Create stageDir/dep_obtainINSTR.txt

		else:
			with open(obtainFile, 'w') as fp:
				num = 0
				for entry in data:

					# Get observer list from URL

					obsUrl = url + ('cmd=getObservers', '&schedid=', entry['SchedId'])
					obsUrl = ''.join(obsUrl)
					observer = urllib.request.urlopen(obsUrl)
					observer = observer.read().decode('utf8')
					observer = json.loads(observer)
					observers = 'None'
					if len(observer) > 0:
						observers = observer['Observers']

					if num > 0:
						fp.write('\n')

					fp.write('{} {} {} {} {} {} {}'.format(hstDate, oa, entry['Account'], entry['Institution'], entry['Principal'], entry['ProjCode'], observers))

					if log_writer:
						log_writer.info('dep_obtain.php {} {} {} {} {} {} {}'.format(hstDate, oa, entry['Account'], entry['Institution'], entry['Principal'], entry['ProjCode'], observers))

					num += 1

	except:
		if log_writer:
			log_writer.info('dep_obtain.php {} error reading telescope schedule'.format(instr.upper()))
#		exit()

