import pandas as pd

def envlog(logFile, logType, telnr, dateObs, utc):
	""" 
	Retrieve nearest env log data from envMet.arT or envFocus.arT 
	file that is closest to and within +-interval seconds of the input
	date and time.
	"""
	#
	# Defaults
	#
	telnr = str(telnr)
	#
	# Setup defaults and config based on logType
	#
	if logType == 'envMet':
		interval = 30
		values = {	'time'         : 'null',
					'wx_domtmp'    : 'null',
					'wx_outtmp'    : 'null',
					'wx_domhum'    : 'null',
					'wx_outhum'    : 'null',
					'wx_pressure'  : 'null',
					'wx_windspeed' : 'null',
					'wx_winddir'   : 'null',
					'wx_dewpoint'  : 'null'}
		output = [  'wx_dewpoint', 
					'wx_outhum', 
					'wx_outtmp', 
					'wx_domtmp', 
					'wx_domhum', 
					'wx_pressure', 
					'wx_windspeed', 
					'wx_winddir']
	elif logType == 'envFocus':
		interval = 2.5
		values = {	'time'     : 'null', 
					'guidfwhm' : 'null'}
		output = [	'time',
					'guidfwhm']
	else:
		return
	#
	# Read envlog file to determine if file and header exist
	# Skip first and third lines (interval and type lines)
	# Second line is header
	#
	try:
		data = pd.read_csv(logFile, skiprows=[0,2])
	except IOError as e:
		print('Unable to open', logFile)
	#
	# Setup if using header or index numbers
	#
	if 'UNIXDate' in data.keys():
		hstKeys = ['HSTdate', 'HSTtime']
		keys = [' "k0:met:dewpointRaw"', ' "k0:met:humidityRaw"', ' "k0:met:tempRaw"', ' "k'+telnr+':met:tempRaw"', ' "k'+telnr+':met:humidityRaw"', ' "k0:met:pressureRaw"', ' "k'+telnr+':met:windSpeedRaw"', ' "k'+telnr+':met:windAzRaw"']
		if logType == 'envFocus':
			keys = [' "k'+telnr+':dcs:pnt:cam0:fwhm"']
	else:
		hstKeys = [2, 3]
		keys = [5, 8, 10, 18, 20, 22, 24, 27]
		if logType == 'envFocus':
			keys = [26]
		data = pd.read_csv(logFile, skiprows=[0,1,2], header=None)
	#
	# Convert DATE-OBS/UT to HST
	#
	from datetime import datetime, timedelta
	utDatetime = datetime.strptime(dateObs + ' ' + utc, '%Y-%m-%d %H:%M:%S.%f')
	utDatetime += timedelta(hours=-10)
	#
	# Find envMet entry within +-interval seconds of this time
	#
	dt1 = utDatetime + timedelta(seconds=-interval)
	dt1 = dt1.strftime('%Y-%m-%d %H:%M:%S.%f')
	dt2 = utDatetime + timedelta(seconds=interval)
	dt2 = dt2.strftime('%Y-%m-%d %H:%M:%S.%f')
	envDatetime = data[hstKeys[0]][0:] + ' ' + data[hstKeys[1]][0:]
	envEntries = pd.to_datetime(envDatetime, format=' %d-%b-%Y %H:%M:%S.%f').between(dt1, dt2)
	envIndex = envEntries.index[envEntries]
	#
	# Timestamp of this entry in UT
	#
	mTime = data[hstKeys[0]][envIndex[0]] + ' ' + data[hstKeys[1]][envIndex[0]]
	mTime = datetime.strptime(mTime, ' %d-%b-%Y %H:%M:%S.%f')
	mTime += timedelta(hours=10)
	#todo: truncating microseconds b/c strftime does not support rounding overflow
	mTime = mTime.strftime('%H:%M:%S.%f')[:-4]


	values['time'] = mTime
	#
	# Set individual values for this entry
	#
	for index, key in enumerate(keys):
		try:
#			value = float(round(data[key][envIndex[0]], 2))
			value = float(data[key][envIndex[0]])
		except ValueError:
			value = 'null'
		values[output[index]] = value

	return values