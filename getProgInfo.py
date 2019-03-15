"""
Assigns programs to FITS files.  

Uses the list of the night's programs (from dep_obtain) and the list of files (from create_prog) 
to assign a program (PROGID as well as PROGINST, PROGPI, PROGTITL) to each FITS file being processed by DQA.
Output is 'newproginfo.txt' with one line per FITS containing: 
    <file> <outdir> <proginst> <progid> <progpi> <progtitl>

This has traditionally been complicated to figure out.  In an attempt to streamline and simplify,
here is the new algorithym:

- If FITS header contains PROGNAME or PROGID, use that. BREAK.  (This is done in create_prog.py)
- If it is not a split night, then assign all files to that program.
- For split nights:
 -- For each unique (non-engineering) outdir, count how many science files are within each program time range.
    If any of those program counts are a majority (> 90%), then assign outdir files to that program.
 -- Also, check if any FITS outdirs match naming scheme and assign to program based on that (_A, _B, etc) 
    if need be.  If not needed, warn if this doesn't agree with sci file method.
 -- If we still don't have an outdir assignment for a file, use the FITS UTC time to assign to overlapping program.
 -- Else, ??? (call old DEP progInfo.php?) (split)
 -- NOTE: The sci files method looks at all dirs independently, including sub dirs and TOO dirs.  It does not compare
    their counts.

Q: Do we need a min file count check on sci files method?
Q: What to do when data shows up but not scheduled?
Q: Warn of data found in non confirming dirs?

"""

import os
import json
import urllib.request as url
import time
import create_log as cl
from common import get_api_data
from dep_obtain import get_obtain_data
from datetime import datetime, timedelta
import re


class ProgSplit:

    def __init__(self, ut_date, instr, stage_dir, log=None):
        """
        Initialization function for the ProgSplit class

        @type ut_date: string
        @param ut_date: Date of observaton in UT timezone
        @type instr: string
        @param instr: Instrument that is being observed
        @type stage_dir: string
        @param stage_dir: directory we are moving processed files to
        """

        #save inputs
        self.utDate = ut_date
        self.instrument = instr
        self.stageDir = stage_dir
        self.log = log

        #consts        
        self.instrList = {  'DEIMOS'    :2, 
                            'ESI'       :2, 
                            'HIRES'     :1, 
                            'KCWI'      :2, 
                            'LRIS'      :1, 
                            'MOSFIRE'   :1, 
                            'NIRC2'     :2, 
                            'NIRSPEC'   :2, 
                            'OSIRIS'    :1, 
                            'NIRES'     :2}
        self.engineering = {'kcwieng'       :'outdir', 
                            'kcwirun'       :'outdir', 
                            'hireseng'      :'outdir',
                            'nspeceng'      :'outdir', 
                            'nirc2eng'      :'outdir', 
                            'engineering'   :'observer',
                            'dmoseng'       :'outdir', 
                            'lriseng'       :'outdir', 
                            'esieng'        :'outdir',
                            'keck ipdm'     :'observer', 
                            'nirspec'       :'observer',
                            'nireseng'      :'outdir', 
                            'moseng'        :'outdir'}
        self.too = {'_ToO_':'outdir'}
        self.api = 'https://www.keck.hawaii.edu/software/db_api/'

        #var init
        self.fileList = []
        self.numFiles = 0
        self.observer = []
        self.obsValues = []
        self.outdirs = {}
        self.programs = []
        self.suntimes = None
        self.semester = self.get_semester()

        #log
        self.rootDir = self.stageDir.split('/stage')[0]
        if not self.log: self.log = cl.create_log(self.rootDir, instr, ut_date)

    def get_semester(self):
        """
        This method determines the semester of the observation
        using the date in UTC
        """

        #todo: move this to common (and change so that it subtracts a day and then does simple semester calc)

        # Split the date into its components
        yr, mo, dy = self.utDate.split('-')

        # convert the strings to ints
        iyr = int(yr)
        imo = int(mo)
        idy = int(dy)
        sem = 'A'

        # Determine which semester the data are from
        # Anything between August and Feb is semester B
        if imo > 8 or imo < 2:
            sem = 'B'
        # Aug 1 UT is still part of Jul 31 HST
        elif imo == 8 and idy > 1:
            sem = 'B'
        elif imo == 2 and idy < 1:
            sem = 'B'
        # Jan through Feb 1 are a part of the previous year's semester
        if imo == 1 or (imo ==2 and idy == 1):
            iyr -= 1
        # return the resulting semester
        return ''.join((str(iyr), sem))

    def check_stage_dir(self):
        """
        This method checks whether or not the stage dir exists
        """
        if not os.path.isdir(self.stageDir):
            raise Exception("progInfo: stage directory doesn't exist!")

    def check_instrument(self):
        """
        This method checks if the instrument is one of the existing
        instruments
        """
        if self.instrument not in self.instrList:
            raise Exception("progInfo - instrument name not valid: " + self.instrument)

    def read_file_list(self):
        """
        This method reads the list of files from the file list
        """

        #match up createprog.txt lines to column names
        colsToSave = ['file','utdate','utc','outdir','observer','frameno',
                      'imagetyp','progid','progpi','proginst','progtitl','oa']

        #check input file exists
        fname = self.stageDir +  '/createprog.txt'
        if not os.path.isfile(fname):
            raise Exception('This file does not exist!!!')
            return

        #loop thru all lines, creating one row record for each set of columns
        with open(fname, 'r') as flist:
            num = 0
            row = {}

            for line in flist:

                # Assign column to line
                row[colsToSave[num]] = line.strip()

                #check if we have reached last column to save
                num += 1
                if num == len(colsToSave):

                    # Check to see if it is an engineering night (Key = instrument, value = outdir/obs)
                    for key, value in self.engineering.items():
                        if key in row[value].lower() or row['progid'] == 'ENG':
                            row['proginst'] = 'KECK'
                            row['progid']   = 'ENG'
                            row['progpi']   = self.instrument.lower() + 'eng'
                            row['progtitl'] = self.instrument.upper() + ' Engineering'

                    # Check to see if it is a ToO observation (key=split, value=outdir)
                    for key, value in self.too.items():
                        if key in row[value]:
                            garbage, progid = row[value].split('_ToO_')
                            row['proginst'] = self.get_too_prog_inst(self.semester, progid)
                            row['progid']   = progid
                            row['progpi']   = self.get_prog_pi(self.semester, progid)
                            row['progtitl'] = self.get_prog_title(self.semester, progid)

                    #add row to list
                    self.fileList.append(row)

                    # Reset for the next file
                    num = 0
                    del row
                    row = {}

# ---------------- END READ FILE LIST--------------------------------------------------------

    def assign_to_pi(self, num):
        """
        This method assigns program info to any file that does not already have assignment

        @type num: int
        @param num: index of program to assign files to
        """

        prog = self.programs[num]

        for i in range(self.numFiles):

            # If file already has PI, skip
            if self.fileList[i]['progpi'] != 'PROGPI':
                continue

            #update col values to those in program
            self.fileList[i]['proginst'] = prog['Institution']
            self.fileList[i]['progpi']   = prog['Principal']
            self.fileList[i]['progid']   = prog['ProjCode']

            #assign title
            if self.fileList[i]['progid'] == 'ENG':
                self.fileList[i]['progtitl'] = self.instrument + ' Engineering'
            else:
                self.fileList[i]['progtitl'] = self.get_prog_title(self.semester, prog['ProjCode'])

#--------------------------- END ASSIGN TO PI---------------------------------------------

    def assign_single_to_pi(self, filenum, num):
        """
        Assign a single file to a program

        @type filenum: int
        @param filenum: the index of the file to assign a PI
        @type num: int
        @param num: the index of the program to use to assign PI
        """

        # If file already has PI, skip
        if (self.fileList[filenum]['progpi'] != 'PROGPI' and self.fileList[filenum]['progpi'] != ''):
            return

        #todo: is this unnecessary (should we do a greater than check instead)?
        if len(self.programs) == 1 and num == 1:
            num = 0

        #get prog
        prog = self.programs[num]
        self.log.info('assigning ' + self.fileList[filenum]['file'] + ' to progIndex: ' + str(num) + '('+prog['ProjCode']+').')

        #update col values to those in program
        self.fileList[filenum]['proginst'] = prog['Institution']
        self.fileList[filenum]['progpi']   = prog['Principal']
        self.fileList[filenum]['progid']   = prog['ProjCode']

        #assign title
        if self.fileList[filenum]['progid'] == 'ENG':
            self.fileList[filenum]['progtitl'] = self.instrument +' Engineering'
        else:
            self.fileList[filenum]['progtitl'] = self.get_prog_title(self.semester, prog['ProjCode'])

#---------------------------- END ASSIGN SINGLE TO PI-------------------------------------------

    def assign_single_by_time(self, filenum):

        file = self.fileList[filenum]
        fileTime = datetime.strptime(file['utc'],'%H:%M:%S.%f')
        self.log.warning('getProgInfo: assigning ' + file['file'] + ' by time')

        #look for program that file time falls within
        for idx in range(len(self.programs)):
            prog = self.programs[idx]
            if not prog['StartTime'] or not prog['EndTime']:
                continue
            progStartTime = datetime.strptime(prog['StartTime'],'%H:%M')
            progEndTime   = datetime.strptime(prog['EndTime'],'%H:%M')
            if (progStartTime <= fileTime <= progEndTime):
                self.assign_single_to_pi(filenum, idx)
                break

#---------------------------- END ASSIGN SINGLE BY TIME -------------------------------------------

    def get_programs(self):

        """
        This method obtains the data from the dep_obtain output file
        """

        obFile = self.stageDir + '/dep_obtain' + self.instrument + '.txt'
        self.programs = get_obtain_data(obFile)

#---------------------------------- END GET SCHEDULE VALUE------------------------------------

    def get_sun_times(self):
        '''
        Gets the sunrise and sunset times and calculates the two halves of the night
        NOTE: We only bother with this because for legacy data, we did not have the start/end
        times of the programs so we try to see which has the most data in either half.
        This doesn't work in the rare case that there is a same instrument 3-way or more 
        split because we couldn't predict if it was a 1/3,1/3,1/3 or a 1/2,1/4,1/4 etc.
        '''

        url = self.api + 'metrics.php?date=' + self.utDate
        self.suntimes = get_api_data(url, getOne=True)
        if not self.suntimes:
            self.log.error('getProgInfo: Could not get sun times via API call: ', url)
            return

#------------------------------END GET SUN TIMES------------------------------------------------

    def get_too_prog_inst(self, sem, progid):
        """
        Query the proposalsAPI and get the ToO program institution

        @type sem: string
        @param sem: semester of the observation
        @type progid: string
        @param progid: ID of the observation program
        """
        semid = sem + '_' + progid
        req = self.api + 'proposalsAPI.php?cmd=getAllocInst&ktn=' + semid
        data = url.urlopen(req)
        inst = data.read().decode('utf8')
        if (inst == None or inst == '' or inst == 'error'): 
            self.log.warning('getProgInfo: Could not find ToO program institution for semid "{}"'.format(semid))
            return 'NONE'
        else : 
            return inst

#--------------------- END GET PROG TITLE-----------------------------------------------

    def get_prog_title(self, sem, progid):
        """
        Query the DB and get the program title

        @type sem: string
        @param sem: semester of the observation
        @type progid: string
        @param progid: ID of the observation program
        """

        semid = sem + '_' + progid
        req = self.api + 'koa.php?cmd=getTitle&semid=' + semid
        title = get_api_data(req, getOne=True)
        if (title == None or 'progtitl' not in title): 
            self.log.warning('get_prog_title: Could not find program title for semid "{}"'.format(semid))
            return 'NONE'
        else : 
            return title['progtitl']

#--------------------- END GET PROG TITLE-----------------------------------------------

    def get_prog_pi(self, sem, progid):
        """
        Query the DB and get the prog PI last name

        @type sem: string
        @param sem: semester of the observation
        @type progid: string
        @param progid: ID of the observation program
        """

        semid = sem + '_' +progid
        req = self.api + 'koa.php?cmd=getPI&semid=' + semid
        pi = get_api_data(req, getOne=True)
        if (pi == None or 'pi_lastname' not in pi): 
            self.log.warning('get_prog_pi: Could not find program PI for semid "{}"'.format(semid))
            return 'NONE'
        else : 
            return pi['pi_lastname']

#--------------------- END GET PROG TITLE-----------------------------------------------

    def get_outdirs(self, programs):

        #make array for easy time comparison
        splitTimes = {}
        isMissingTimes = False
        for key, prog in enumerate(programs):

            if not prog['StartTime'] or not prog['EndTime']:
                isMissingTimes = True
                sunset   = datetime.strptime(self.suntimes['sunset'], '%H:%M')
                midpoint = datetime.strptime(self.suntimes['midpoint'], '%H:%M')
                sunrise  = datetime.strptime(self.suntimes['sunrise'], '%H:%M')
                t1 = sunset   if key == 0 else midpoint
                t2 = midpoint if key == 0 else sunrise
            else:
                t1 = datetime.strptime(prog['StartTime'], '%H:%M')
                t2 = datetime.strptime(prog['EndTime']  , '%H:%M')

            splitTimes[key] = [t1, t2]
        self.log.info('get_prog_pi: Split times: ' + str(splitTimes))


        #throw an error if there are 3-way or more split and we don't have Start/End times
        if len(programs) > 2 and isMissingTimes:
            self.log.error('get_prog_pi: Three or more programs found this night but no Start/End time info found!!!')


        #Get list of unique outdirs from file list and keep count of where the science files are
        self.outdirs = {}
        for file in self.fileList:
            fdir = self.fix_outdir(file['outdir'])
            eng = 0
            for engname, name in self.engineering.items():
                if engname in fdir: eng = 1

            #skip certain dirs/files
            if eng or fdir == '0' or 'fcs' in fdir: continue

            # Add new outdirs to the outdir list and init sci file counts
            if fdir not in self.outdirs:
                data = {'assign': -1, 'sciCounts': {}, 'sciTotal': 0}
                for i in range(len(splitTimes)):
                    data['sciCounts'][i] = 0
                self.outdirs[fdir] = data 

            #if image type is object, increment count for which program time range it falls within
            if file['imagetyp'] == 'object' or True:
                thistime = datetime.strptime(file['utc'], '%H:%M:%S.%f')
                for i in range(len(splitTimes)):
                    if splitTimes[i][0] <= thistime and splitTimes[i][1] > thistime:
                        self.outdirs[fdir]['sciCounts'][i] += 1
                        self.outdirs[fdir]['sciTotal']     += 1
                        break


#--------------------------------END GET OUTDIR-----------------------------

    def get_observer(self):
        repchar = [' ','_','/','&','.',',,']
        count = []
        temp = []
        for key, file in self.fileList:
            obs = file['observer']
            if obs != 'Keck Engineering':
                outdir = self.fix_outdir(file['outdir'])
            for char in repchar:
                obs = obs.replace(char, ',')
            if obs not in temp:
                temp.append(obs)
            obs = ''.join((obs, '_', outdir))
            if obs not in self.observer:
                self.observer.append(obs)
        self.obsValues = len(temp)

#----------------------END GET OBSERVER------------------------------------

    def assign_outdirs_to_programs(self):

        self.log.info('getProgInfo: starting assign_outdirs_to_programs()')

        # Try different methods
        self.assign_outdirs_by_sci_count()
        self.assign_outdirs_by_dir_name()


    def assign_outdirs_by_sci_count(self):

        #The idea here is: given some outdirs, count up how many science files each outdir has in each 
        #program time range. If an outdir has a high % of one program time range like > 80%, 
        # then that outdir must belong to that program.  
        #NOTE: Sometimes programs take data during other program times.
        self.log.info('getProgInfo: ' + str(len(self.outdirs)) + ' OUTDIRs found')
        for outdir, data in self.outdirs.items():
            self.log.info('outdir sci counts for : ' + outdir)
            for i, count in data['sciCounts'].items():
                perc = count / data['sciTotal'] if data['sciTotal'] > 0 else 0
                self.log.info('--- prog' + str(i) + ': ' + str(count) + ' ('+str(round(perc*100,0))+'%)')
                if perc > 0.8: 
                    self.outdirs[outdir]['assign'] = i
                    progid = self.programs[i]['ProjCode']
                    self.log.info('Mapping (by sci) outdir ' + outdir + " to progIndex: " + str(i) + ' ('+progid+').')

            #no assignment?
            if self.outdirs[outdir]['assign'] < 0:
                self.log.warning("Could not map outdir by sci counts for: " + outdir)


    def assign_outdirs_by_dir_name(self):

        # Loop through the OUTDIRs and assign them to program indexes based on naming convention
        # (assume yyyyMMMdd, yyyyMMMdd_B...)
        for outdir, data in self.outdirs.items():

            assign = -1
            if   re.search('/\d{4}\D{3}\d{2}_A', outdir): assign = 0
            elif re.search('/\d{4}\D{3}\d{2}_B', outdir): assign = 1
            elif re.search('/\d{4}\D{3}\d{2}_C', outdir): assign = 2
            elif re.search('/\d{4}\D{3}\d{2}_D', outdir): assign = 3
            elif re.search('/\d{4}\D{3}\d{2}_E', outdir): assign = 4
            elif re.search('/\d{4}\D{3}\d{2}'  , outdir): assign = 0

            #if previously assigned, make sure this jives
            if data['assign'] >= 0:
                if data['assign'] != assign and assign >= 0:
                    self.log.error("getProgInfo: Outdir assigned to program " + str(data['assign']) + ', but outdir naming convention suggests ' + str(assign) + ' ('+outdir+')')
                continue

            if assign >= len(self.programs) : 
                self.log.error('getProgInfo: Program assignment index ' + str(assign) + ' > number of programs.')
                assign = -1

            if assign < 0:
                self.log.warning('getProgInfo: Could not map ' + outdir + " to a program by dir naming convention.")
            else:
                progid = self.programs[assign]['ProjCode']
                self.log.info('getProgInfo: Mapping (by name) outdir ' + outdir + " to progIndex: " + str(assign) + ' ('+progid+').')

            self.outdirs[outdir]['assign'] = assign


    def split_multi(self):

        #TODO: is this correct for eng data?

        # Loop thru all files and if we find an outdir match, assign to program
        for key, file in enumerate(self.fileList):
            fileOutdir = self.fix_outdir(file['outdir'])
            if fileOutdir in self.outdirs:
                progIndex = self.outdirs[fileOutdir]['assign']
                if progIndex >= 0: 
                    self.assign_single_to_pi(key, progIndex)
                else: 
                    self.assign_single_by_time(key)
            else:
                self.log.error("getProgInfo: Could not find outdir match for: " + fileOutdir)

            #final check to see if assigned
            if self.fileList[key]['progpi'] in ('PROGPI', '', 'NONE'):
                self.log.error("getProgInfo: Could not assign program for file: " + self.fileList[key]['file'])

#---------------------END SPLIT MULTI BY SCIENCE---------------------------

    def fix_outdir(self, outdir):
        """
        Function to remove unwanted subdirectories from outdir

        @type outdir: string
        @param outdir: path to be have subdirs removed
        """
        if '/fcs' in outdir:
            outdir = outdir.replace('/fcs', '')
        rep = ['/s/', '//', '/scam/', '/spec/', '/scam', '/spec']
        for subdir in rep:
            outdir = outdir.replace(subdir, '/')
        return outdir

#-----------------------------END FIX SUBDIR--------------------------------

    def sort_by_time(self, progs):
        """
        Simple Bubble Sort algorithm to reorder multiple nights by StartTime
        """
        cont = True
        while(cont):
            cont = False
            for i in range(len(progs)-1):
                if not progs[i]['StartTime']:
                    cont = False
                    break
                if (time.strptime(progs[i]['StartTime'],'%H:%M') > time.strptime(progs[i+1]['StartTime'],'%H:%M')):
                    temp = progs[i]
                    progs[i] = progs[i+1]
                    progs[i+1] = temp
                    del temp
                    cont = True




#----------------------------------END SORT BY TIME----------------------------------

def getProgInfo(utdate, instrument, stageDir, log=None, test=False):

    if test: 
        rootDir = stageDir.split('/stage')[0]
        log = cl.create_log(rootDir, instrument, utdate+'_TEST')

    #input var compat
    utdate = utdate.replace('/','-')
    instrument = instrument.upper()

    #gather info
    progSplit = ProgSplit(utdate, instrument, stageDir, log)
    progSplit.check_stage_dir()
    progSplit.check_instrument()
    progSplit.read_file_list()

    #get list of programs and determine if instrument split night
    progSplit.get_programs()
    numSplits = len(progSplit.programs) if progSplit.programs else 0

    #No split
    if numSplits == 1: 
        progSplit.log.info('getProgInfo: ' + utdate + ' is not a split night')
        progSplit.log.info('getProgInfo: Assigning to ' + progSplit.instrument + ' PI')
        progSplit.assign_to_pi(0)

    # Split night
    elif numSplits > 1: 
        progSplit.log.info('getProgInfo: ' + utdate + ' is a split night with ' + str(len(progSplit.programs)) + ' programs')
        progSplit.sort_by_time(progSplit.programs)
        progSplit.get_sun_times()
        progSplit.get_outdirs(progSplit.programs)
        progSplit.assign_outdirs_to_programs()
        progSplit.split_multi()

    #no proj codes
    # TODO: in this case, do we use old progInfo.php?
    # TODO: only throw error if there was some science files (ie this could be engineering)
    else:
        progSplit.log.warning('No ' + instrument + ' programs found this night.')

    #write out result
    fname = stageDir + '/newproginfo.txt'
    if test: fname += '.TEST'
    with open(fname, 'w') as ofile:
        for progfile in progSplit.fileList:
            line =         progfile['file']
            line += "\t" + progfile['outdir']
            line += "\t" + progfile['proginst']
            line += "\t" + progfile['progid']
            line += "\t" + progfile['progpi']
            line += "\t" + progfile['progtitl']
            line += "\n"
            ofile.writelines(line)

    #return data written for convenience
    progSplit.log.info('getProgInfo: finished, {} created'.format(fname))
    return progSplit.fileList
