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
#   stage directory = rootDir/stage/instr/utDate
#   output directory = rootDir/instr/utDate/[anc,lev0,lev1]
#
#-------------------------------------------------------------------------------

import os
import sys
import importlib
import urllib.request
import json
import configparser
from dep_obtain import dep_obtain
from dep_locate import dep_locate
from dep_add import dep_add
from dep_dqa import dep_dqa
from dep_tar import dep_tar
from koaxfr import koaxfr
from send_email import send_email
from common import *
import re
import datetime as dt


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
        
        self.config = configparser.ConfigParser()
        self.config.read('config.live.ini')

        # Create instrument object
        moduleName = ''.join(('instr_', self.instr.lower()))
        className = self.instr.capitalize()
        module = importlib.import_module(moduleName)
        instrClass = getattr(module, className)
        self.instrObj = instrClass(self.instr, self.utDate, self.rootDir)
        
        
    def go(self, processStart=None, processStop=None):
        """
        Processing steps for DEP
        @param processStart: name of process to start at.  Default is 'obtain'
        @type instr: string
        @param processStop: name of process to stop after.  Default is 'koaxfr'
        @type instr: string
        """

        # Init DEP process (verify inputs, create the logger and create directories)
        # NOTE: A full run assert fails if dirs exist, otherwise assumes you know what you are doing.
        fullRun = True if (processStart == None and processStop == None) else False
        self.instrObj.dep_init(self.config, fullRun)


        #check koa for existing entry
        if self.tpx:
            if not self.check_koa_db_entry(): return False


        #write to tpx at dep start
        if self.tpx:
            utcTimestamp = dt.datetime.utcnow().strftime("%Y%m%d %H:%M")
            update_koatpx(self.instrObj.instr, self.instrObj.utDate, 'start_time', utcTimestamp, self.instrObj.log)


        #process steps control (pair down ordered list if requested)
        steps = ['obtain', 'locate', 'add', 'dqa', 'lev1', 'tar', 'koaxfr']
        if (processStart != None and processStart not in steps):
            raise Exception('Incorrect use of processStart: ' + processStart)
            return False
        if (processStop != None and processStop not in steps):
            raise Exception('Incorrect use of processStop: ' + processStop)
            return False
        if processStart != None: steps = steps[steps.index(processStart):]
        if processStop  != None: steps = steps[:(steps.index(processStop)+1)]


        #run each step in order
        for step in steps:
            self.instrObj.log.info('*** RUNNING DEP PROCESS STEP: ' + step + ' ***')

            if   step == 'obtain': dep_obtain(self.instrObj)
            elif step == 'locate': dep_locate(self.instrObj, self.tpx)
            elif step == 'add'   : dep_add(self.instrObj)
            elif step == 'dqa'   : dep_dqa(self.instrObj, self.tpx)
            #lev1
            elif step == 'tar'   : dep_tar(self.instrObj)
            #koaxfr
            elif step == 'koaxfr': koaxfr(self.instrObj, self.tpx)

            #check for expected output
            self.check_step_results(step)


        #email completion report
        if fullRun: self.do_process_report_email()


        #complete
        self.instrObj.log.info('*** DEP PROCESSSING COMPLETE! ***')
        return True


    def check_koa_db_entry(self):
        """
        Verify whether or not processing can proceed.  Processing cannot
        proceed if there is already an entry in koa.koatpx.
        """

        self.instrObj.log.info('dep: verifying if can proceed')
        # Verify that there is no entry in koa.koatpx
        try:
            url = ''.join((self.instrObj.koaUrl, 'cmd=isInKoatpx&instr=', self.instr, '&utdate=', self.utDate))
            data = url_get(url)
            if data[0]['num'] != '0':
                raise Exception('dep: entry already exists in database. EXITING!')
                return False
        except:
            raise Exception('dep: could not query koa database. EXITING!')
            return False

        return True



    def check_step_results(self, step):

        self.instrObj.log.info('*** VERIFYING OUTPUT FOR : ' + step + ' ***')

        #useful vars
        dirs = self.instrObj.dirs
        instr = self.instrObj.instr
        utDate = self.instrObj.utDate
        utDateDir = self.instrObj.utDateDir


        #get list of files to check for existence
        checkFiles = []
        if   step == 'obtain':
            checkFiles.append(dirs['stage'] + '/dep_obtain' + instr + '.txt')
        elif step == 'locate':
            checkFiles.append(dirs['stage'] + '/dep_locate' + instr + '.txt')
        elif step == 'add':
            #note: dep_add should not exit if weather files are not found
            pass
        elif step == 'dqa':
            checkFiles.append(dirs['stage'] + '/dep_dqa' + instr + '.txt')
            with open(checkFiles[0], 'r') as f:
                count = sum(1 for line in f)
            if count > 0:
                checkFiles.append(dirs['lev0'] + '/' + utDateDir + '.filelist.table')
                checkFiles.append(dirs['lev0'] + '/' + utDateDir + '.metadata.table')
                checkFiles.append(dirs['lev0'] + '/' + utDateDir + '.metadata.md5sum')
                checkFiles.append(dirs['lev0'] + '/' + utDateDir + '.FITS.md5sum.table')
                checkFiles.append(dirs['lev0'] + '/' + utDateDir + '.JPEG.md5sum.table')
        elif step == 'tar':
            checkFiles.append(dirs['anc'] + '/anc' + utDateDir + '.tar.gz')
            checkFiles.append(dirs['anc'] + '/anc' + utDateDir + '.md5sum')


        #check for file existence and fatal error if not found
        for file in checkFiles:
            if not os.path.exists(file):
                self.do_fatal_error(step, 'Process post-check: ' + file + " not found!")
                break


    def do_process_report_email(self):

        #read log file for errors and warnings
        logStr = ''
        count = 0
        errCount = 0
        warnCount = 0
        logOutFile = self.instrObj.log.handlers[0].baseFilename
        with open(logOutFile, 'r') as log:
            for line in log:
                count += 1
                if re.search('WARNING', line, re.IGNORECASE):
                    logStr += str(count) + ': ' + line + "\n"
                    warnCount += 1
                elif re.search('ERROR', line, re.IGNORECASE):
                    logStr += str(count) + ': ' + line + "\n"
                    errCount += 1


        #form subject
        subject = ''
        if (errCount  > 0): subject += '(ERR:'  + str(errCount) + ')'
        if (warnCount > 0): subject += '(WARN:' + str(warnCount) + ')'
        subject += ' DEP: ' + self.instrObj.instr + ' ' + self.instrObj.utDate


        #form msg
        #todo: clean this up a bit
        msg = ''
        msg += logStr + "\n"

        dirs = self.instrObj.dirs
        utDateDir = self.instrObj.utDateDir
        filelistOutFile = dirs['lev0'] + '/' + utDateDir + '.filelist.table'
        with open(filelistOutFile, 'r') as file:
            for line in file: 
                msg += line + "\n"


        #read config vars
        config = configparser.ConfigParser()
        config.read('config.live.ini')
        adminEmail = config['REPORT']['ADMIN_EMAIL']

        
        #if admin email then email
        if (adminEmail != ''):
            send_email(adminEmail, adminEmail, subject, msg)



    def do_fatal_error(self, step, msg):

        #call common.do_fatal_error
        do_fatal_error(msg, self.instrObj.instr, self.instrObj.utDate, step, self.instrObj.log)


        #update tpx
        #TODO: Note: we may not need/want to do this tpx update
        if self.tpx:
            self.instrObj.log.info('Updating KOA database with error status.')
            utcTimestamp = dt.datetime.utcnow().strftime("%Y%m%d %H:%M")
            update_koatpx(instr, utDate, 'arch_stat', "ERROR", log)
            update_koatpx(instr, utDate, 'arch_time', utcTimestamp, log)

        #exit program
        self.instrObj.log.info('EXITING DEP!')
        sys.exit()


#------- End dep class --------
