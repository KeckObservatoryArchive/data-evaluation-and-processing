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
import importlib
import urllib.request
import json
import configparser
from dep_obtain import dep_obtain
from dep_locate import dep_locate
from dep_add import dep_add
from dep_dqa import dep_dqa
from dep_tar import dep_tar
from send_email import send_email
from common import *


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
        # This will also verify inputs, create the logger and create all directories
        moduleName = ''.join(('instr_', self.instr.lower()))
        className = self.instr.capitalize()
        module = importlib.import_module(moduleName)
        instrClass = getattr(module, className)
        self.instrObj = instrClass(self.instr, self.utDate, self.rootDir)
        self.instrObj.koaUrl = self.config['API']['KOAAPI']
        self.instrObj.telUrl = self.config['API']['TELAPI']
        self.instrObj.metadataTablesDir = self.config['MISC']['METADATA_TABLES_DIR']
        self.instrObj.dep_init()
        
        
    def go(self, processStart=None, processStop=None):
        """
        Processing steps for DEP
        @param processStart: name of process to start at.  Default is 'obtain'
        @type instr: string
        @param processStop: name of process to stop after.  Default is 'koaxfr'
        @type instr: string
        """

        #verify
        if self.tpx:
            if not self.verify_can_proceed(): return


        #todo: write to tpx at dep start


        #process steps control (pair down ordered list if requested)
        steps = ['obtain', 'locate', 'add', 'dqa', 'lev1', 'tar', 'koaxfr']
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


        #run each step in order
        for step in steps:
            self.instrObj.log.info('*** RUNNING DEP PROCESS STEP: ' + step + ' ***')

            if   step == 'obtain': dep_obtain(self.instrObj)
            elif step == 'locate': dep_locate(self.instrObj)
            elif step == 'add'   : dep_add(self.instrObj)
            elif step == 'dqa'   : dep_dqa(self.instrObj)
            #lev1
            elif step == 'tar'   : dep_tar(self.instrObj)
            #koaxfr

            #check for expected output
            self.check_step_results(step)


        self.instrObj.log.info('*** DEP PROCESSSING COMPLETE! ***')


    def verify_can_proceed(self):
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
                self.instrObj.log.error('dep: entry already exists in database, exiting')
                return False
        except:
            self.instrObj.log.error('dep: could not query koa database')
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
                self.do_fatal_error(step, file + " not found!")
                break



    def do_fatal_error(self, step, msg):

        summary = "DEP ERROR: [" + self.instrObj.instr + ', ' + self.instrObj.utDate + ', ' + step + ']'

        #log message
        log_msg = summary + ' (' + msg + ')'
        self.instrObj.log.error(log_msg)

        #send email to admin
        self.instrObj.log.info('Emailing koaadmin about fatal error.')
        emailTo   = self.config['REPORT']['ADMIN_EMAIL']
        emailFrom = self.config['REPORT']['ADMIN_EMAIL']
        subject = summary
        message = subject + "\n\n" + msg
        send_email(emailTo, emailFrom, subject, message)

        #update tpx
        #TODO: Note: we may not need/want to do this tpx update
        if self.tpx:
            self.instrObj.log.info('Updating KOA database with error status.')
            utcTimestamp = dt.utcnow().strftime("%Y%m%d %H:%M")
            update_koatpx(instr, utDate, 'arch_state', "ERROR", log)
            update_koatpx(instr, utDate, 'arch_time', utcTimestamp, log)

        #exit program
        self.instrObj.log.info('EXITING DEP!')
        sys.exit()


#------- End dep class --------