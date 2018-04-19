#-------------------------------------------------------------------------------
# dep.py instr utDate rootDir [tpx]
#
# This is the backbone process for KOA operations at WMKO.
#
# instr = Instrument name (e.g. HIRES)
# utDate = UT date of observation (YYYY-MM-DD)
# rootDir = Root directory for output and staging files (e.g. /koadata99)
#
# Directories created:
#	stage directory = rootDir/stage/instr/utDate
#	output directory = rootDir/instr/utDate/[anc,lev0,lev1]
#
#-------------------------------------------------------------------------------

from sys import argv
from verification import *
import argparse
import logging as lg
import os
import urllib.request
import json
import hashlib
#from update_koatpx import *
from datetime import datetime
from common import get_root_dirs


# Input parameters
parser = argparse.ArgumentParser(description='DEP input parameters')
parser.add_argument('instr', type=str, help='Instrument name')
parser.add_argument('utDate', type=str, help='UT date of observation (yyyy-mm-dd)')
parser.add_argument('rootDir', type=str, help='Directory to use for output (/koadata32)')
parser.add_argument('tpx', type=str, nargs='?', default='', help='Update koatpx (optional)')

args = parser.parse_args()
instr   = args.instr.upper()
utDate  = args.utDate.replace('/', '-')
rootDir = args.rootDir
tpx = 1 if (args.tpx == 'tpx') else 0




# Verify input parameters
verify_instrument(instr)
verify_date(utDate)
assert rootDir != '', 'rootDir value is blank'



# get root dirs
dirs = get_root_dirs(rootDir, instr, utDate)



# endHour for NIRES
endHour = 19



# Setup logging
import create_log
log = create_log.create_log(rootDir, instr, utDate)

log.info('dep.py started for {} {}'.format(instr.upper(), utDate))
log.info('dep.py process directory is {}'.format(dirs['output']))
log.info('dep.py stage directory is {}'.format(dirs['stage']))



# Skip if entry in database
if tpx:
	koaUrl = 'https://www.keck.hawaii.edu/software/db_api/koa.php?'
	sendUrl = ''.join((koaUrl, 'cmd=isInKoatpx&instr=', instr.upper(), '&utdate=', utDate))
	data = urllib.request.urlopen(sendUrl)
	data = data.read().decode('utf8')       # Convert from byte to ascii
	data = json.loads(data)                 # Convert to Python list

	if data[0]['num'] != '0':
		print('Entry already exists in database - remove and start again')
		log.info('dep.py entry already exists in database - exiting')
		exit()



# Skip if directories already exist
dirList = [dirs['stage'], dirs['output']]
for dir in dirList:
	if os.path.isdir(dir):
		print('Directory exists {} - remove and start again'.format(dir))
		log.info('dep.py directory ({}) already exists - exiting'.format(dir))
		exit()



# Add entry to database
now = datetime.now().strftime('%Y%m%d %H:%M')
if tpx:
	update_koatpx(instr, utDate, 'start_time', now, log)



# Create the directories
dirList = [dirs['lev0'], dirs['lev1'], dirs['anc'], dirs['stage']]
try:
	log.info('dep.py creating directory structure')
	for dir in dirList:
		os.makedirs(dir)
except:
	print('Error creating directory {}'.format(dir))
	log.info('Error creating directory {}'.format(dir))



# Create README
readmeFile = ''.join((dirs['output'], '/README'))
with open(readmeFile, 'w') as fp:
	fp.write(dirs['output'])



# dep_obtain
import dep_obtain
log.info('dep.py starting dep_obtain.py')
dep_obtain.dep_obtain(instr, utDate, dirs['stage'], log)
file = ''.join((dirs['stage'], '/dep_obtain', instr.upper(), '.txt'))
if not os.path.isfile(file):
	print('{} file missing'.format(file))
	exit()



# dep_locate/transfer
import dep_locate
dep_locate.dep_locate(instr, utDate, rootDir, endHour, log)

file = ''.join((dirs['stage'], '/dep_locate', instr.upper(), '.txt'))
num = sum(1 for line in open(file, 'r'))
if tpx:
	update_koatpx(instr, utDate, 'files', str(num), log)



# No FITS files found
if num == 0:

	#todo: do cleanup?
	log.info('Cleaning up')
	print('Removing {}'.format(dirs['output']))
	log.info('Removing {}'.format(dirs['output']))

	if tpx:
		update_koatpx(instr, utDate, 'sci_files', '0', log)
		update_koatpx(instr, utDate, 'ondisk_stat', 'N/A', log)
		update_koatpx(instr, utDate, 'arch_stat', 'N/A', log)
		update_koatpx(instr, utDate, 'metadata_stat', 'N/A', log)
		update_koatpx(instr, utDate, 'dvdwrit_stat', 'N/A', log)
		update_koatpx(instr, utDate, 'dvdsent_stat', 'N/A', log)
		update_koatpx(instr, utDate, 'dvdstor_stat', 'N/A', log)
		update_koatpx(instr, utDate, 'tpx_stat', 'N/A', log)

	#todo: send email?
	print('Send email')

	exit()

if tpx:
	now = datetime.now().strftime('%Y%m%d %H:%M')
	update_koatpx(instr, utDate, 'ondisk_stat', 'DONE', log)
	update_koatpx(instr, utDate, 'ondisk_time', now, log)



#get telescope number
schedUrl = 'https://www.keck.hawaii.edu/software/db_api/telSchedule.php?'
sendUrl = ''.join((schedUrl, 'cmd=getTelnr&instr=', instr.upper()))
data = urllib.request.urlopen(sendUrl)
data = data.read().decode('utf8')       # Convert from byte to ascii
data = json.loads(data)                 # Convert to Python list

telNr = None
if len(data) > 0: telNr = int(data[0]['TelNr'])
if (telNr == None): 
	log.error('Unable to get telNr for instrument: ' + instr)
	exit()



# dep_add
import dep_add
log.info('dep.py starting dep_add.py')
dep_add = dep_add.dep_add(telNr, instr, utDate, rootDir, log)
dep_add.dep_add()



# dqa_run
import dqa_run
log.info('dep.py starting dqa_run.py')
dqa_run(instr, utDate, rootDir, tpx=tpx, log)
# level 1? (OSIRIS, NIRC2)



# dep_tar
log.info('dep.py starting dep_add.dep_tar()')
dep_add.dep_tar()



#todo: cleanup



#todo: transfer data
##--koaxfr(instr, utDate, dirs['output'], tpx=tpx)



# Temporary tar for PI
# import test_tar
# test_tar.test_tar(dirs['stage'])
