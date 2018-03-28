import pandas as pd

def envlog(log_type, telnr, date_obs, utc):
	""" Retrieve nearest env log data from envMet.arT or envFocus.arT 
	    file that is closest to and within +-interval seconds of the input
	    date and time """
	#
	# Defaults
	#
	telnr = str(telnr)
	#
	# Allowed log files
	#
	if log_type == 'envMet':
		log_file = 'envMet.arT'
		interval = 30
		values = {'time' : 'null',
				'wx_domtmp' : 'null',
				'wx_outtmp' : 'null',
				'wx_domhum' : 'null',
				'wx_outhum' : 'null',
				'wx_pressure' : 'null',
				'wx_windspeed' : 'null',
				'wx_winddir' : 'null',
				'wx_dewpoint' : 'null'}
		output = ['wx_dewpoint', 
				'wx_outhum', 
				'wx_outtmp', 
				'wx_domtmp', 
				'wx_domhum', 
				'wx_pressure', 
				'wx_windspeed', 
				'wx_winddir']
	elif log_type == 'envFocus':
		log_file = 'envFocus.arT'
		interval = 2.5
		values = {'time' : 'null', 'guidfwhm' : 'null'}
		output = ['guidfwhm']
	else:
		return
	#
	# Read envlog file to determine if file and header exist
	# Skip first and third lines (interval and type lines)
	# Second line is header
	#
	try:
		data = pd.read_csv(log_file, skiprows=[0,2])
	except IOError as e:
		print('Unable to open', log_file)
	#
	# Setup if using header or index numbers
	#
	if 'UNIXDate' in data.keys():
		hst_keys = ['HSTdate', 'HSTtime']
		keys = [' "k0:met:dewpointRaw"', ' "k0:met:humidityRaw"', ' "k0:met:tempRaw"', ' "k'+telnr+':met:tempRaw"', ' "k'+telnr+':met:humidityRaw"', ' "k0:met:pressureRaw"', ' "k'+telnr+':met:windSpeedRaw"', ' "k'+telnr+':met:windAzRaw"']
		if log_type == 'envFocus':
			keys = [' "k'+telnr+':dcs:pnt:cam0:fwhm"']
	else:
		hst_keys = [2, 3]
		keys = [5, 8, 10, 18, 20, 22, 24, 27]
		if log_type == 'envFocus':
			keys = [26]
		data = pd.read_csv(log_file, skiprows=[0,1,2], header=None)
	#
	# Convert DATE-OBS/UT to HST
	#
	from datetime import datetime, timedelta
	ut_datetime = datetime.strptime(date_obs + ' ' + utc, '%Y-%m-%d %H:%M:%S.%f')
	ut_datetime += timedelta(hours=-10)
	print(ut_datetime.strftime('%Y-%m-%d %H:%M:%S.%f'))
	#
	# Find envMet entry within +-interval seconds of this time
	#
	dt1 = ut_datetime + timedelta(seconds=-interval)
	dt1 = dt1.strftime('%Y-%m-%d %H:%M:%S.%f')
	dt2 = ut_datetime + timedelta(seconds=interval)
	dt2 = dt2.strftime('%Y-%m-%d %H:%M:%S.%f')
	env_datetime = data[hst_keys[0]][0:] + ' ' + data[hst_keys[1]][0:]
	env_entries = pd.to_datetime(env_datetime, format=' %d-%b-%Y %H:%M:%S.%f').between(dt1, dt2)
	env_index = env_entries.index[env_entries]
	#
	# Timestamp of this entry in UT
	#
	m_time = data[hst_keys[0]][env_index[0]] + ' ' + data[hst_keys[1]][env_index[0]]
	m_time = datetime.strptime(m_time, ' %d-%b-%Y %H:%M:%S.%f')
	m_time += timedelta(hours=10)
	m_time = m_time.strftime('%H:%M:%S.%f')
	values['time'] = m_time
	#
	# Set individual values for this entry
	#
	for index, key in enumerate(keys):
		try:
#			value = float(round(data[key][env_index[0]], 2))
			value = float(data[key][env_index[0]])
		except ValueError:
			value = 'null'
		values[output[index]] = value
	print(values)
