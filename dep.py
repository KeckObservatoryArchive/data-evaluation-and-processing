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

#import os
import importlib
import urllib.request
import json
import configparser
from dep_obtain import dep_obtain
from dep_locate import dep_locate
from dep_add import *
from dqa_run import dqa_run


class Dep:
	"""
	This is the backbone class for KOA operations at WMKO.

	@param instr: instrument name
	@type instr: string
	@param utDate: UT date of observation
	@type utDate: string (YYYY-MM-DD)
	@param rootDir: root directory to write processed files
	@type rootDir: string
	"""
	def __init__(self, instr, utDate, rootDir, tpx=0):
		"""
		Setup initial parameters.
		Create instrument object.
		"""
		self.instr = instr.upper()
		self.utDate = utDate
		self.rootDir = rootDir
		self.tpx = tpx
		if self.tpx != 1: self.tpx = 0
		
		config = configparser.ConfigParser()
		config.read('config.live.ini')

		# Create instrument object
		# This will also verify inputs, create the logger and create all directories
		moduleName = ''.join(('instr_', self.instr.lower()))
		className = self.instr.capitalize()
		print(moduleName, className)
		module = importlib.import_module(moduleName)
		instrClass = getattr(module, className)
		self.instrObj = instrClass(self.instr, self.utDate, self.rootDir)
		self.instrObj.koaUrl = config['API']['KOAAPI']
		self.instrObj.telUrl = config['API']['TELAPI']
		
	def go(self, processStart=None, processStop=None):
		"""
		Processing steps for DEP
		@param processStart: name of process to start at.  Default is 'obtain'
		@type instr: string
		@param processStop: name of process to stop after.  Default is 'koaxfr'
		@type instr: string
		"""

		#verify
		if not self.verify_can_proceed(): return


		#process steps control (pair down ordered list if requested)
		steps = ['obtain', 'locate', 'transfer', 'add', 'dqa', 'lev1', 'tar', 'koaxfr']
		if (processStart != None and processStart not in steps):
			self.instrObj.log.error('Incorrect use of processStart')
			return False
		if (processStop != None and processStop not in steps):
			self.instrObj.log.error('Incorrect use of processStop')
			return False
		if processStart != None:
			steps = steps[steps.index(processStart):]
		if processStop  != None:
			steps = steps[:(steps.index(processStop)+1)]
		print ('Running process steps: ', steps)


		#run each step in order
		for step in steps:
			if   step == 'obtain': dep_obtain(self.instrObj)
			elif step == 'locate': dep_locate(self.instrObj)
			elif step == 'add'   : dep_add(self.instrObj)
			elif step == 'dqa'   : dqa_run(self.instrObj)
			#lev1
			#dep_tar
			#koaxfr



	def verify_can_proceed(self):
		"""
		Verify whether or not processing can proceed.  Processing cannot
		proceed if there is already an entry in koa.koatpx.
		"""

		#return True
		self.instrObj.log.info('dep: verifying if can proceed')
		# Verify that there is no entry in koa.koatpx
		try:
			url = ''.join((self.instrObj.koaUrl, 'cmd=isInKoatpx&instr=', self.instr, '&utdate=', self.utDate))
			data = urllib.request.urlopen(url)
			data = data.read().decode('utf8')
			data = json.loads(data)
			if data[0]['num'] != '0':
				self.instrObj.log.error('dep: entry already exists in database, exiting')
				return False
		except:
			self.instrObj.log.error('dep: could not query koa database')
			return False
		return True

#------- End dep class --------