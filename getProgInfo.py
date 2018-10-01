"""
"""

import os
import json
#import koa_db_conn as kdb
#import mysql_conn as msc
#import metrics_conn as metrics
import urllib.request as url
#import pymysql as pms
import time
import create_log as cl
from common import url_get
from dep_obtain import get_obtain_data


class ProgSplit:
    """
    Variables:
    @type engineering: dictionary
    @param engineering: different engineering directories
    @type fileList: list of dictionaries
    @param fileList: stores the files read from dep_obtain
    @type instrList: dictionary
    @param instrList: stores which instruments are on which telescope
    @type instrument: string
    @param instrument: Stores the current instrument being used
    @type numFiles: int
    @param numFiles: number of valid files found
    @type numSciencePI: int
    @param numSciencePI: Number of unique PIs found
    @type too: dictionary
    @param too: stores _ToO_ as a key for outdir
    @type observer: list
    @parma observer: Stores the observers for a project
    @type obsValues: list
    @param obsValues: stores various observation values
    @type outdir: string
    @param outdir: Directory where the original files are located
    @type programs: list of dictionaries
    @param programs: list of program information for the FITS files
    @type semester: string
    @param semester: Semester during which the observation occured in
    @type splitTime: float
    @param splitTime: the time in decimal hours when the programs switched
    @type stageDir: string
    @param stageDir: temporary storge location for files waiting to be sent
    @type sunset: float
    @param sunset: time in decimal hours when 12deg sunset occured
    @type sunrise: float
    @param sunrise: time in decimal hours when 12deg sunrise occured
    @type utDate: string (datetime in db)
    @param utDate: date in UT when observation occured
    @type sciFiles: list
    @param sciFiles: stores the valid science files
    @type api: string
    @param api: base url for querying the RESTful API

    Methods:
    __init__(self, ut_date, instr, stage_dir)
    get_semester(self)
    check_stage_dir(self)
    check_instrument(self)
    read_dep_obtain(self)
    read_file_list(self)
    assign_to_pi(self, num)
    assign_single_to_pi(self, filenum, num)
    get_schedule_value(self, col)
    get_sun_times(self)
    get_prog_title(self, progid)
    get_outdir(self)
    get_observer(self)
    split_by_observer(self)
    split_by_time(self)
    split_by_science(self)
    split_multi_by_science(self)
    fix_outdir(self, outdir)
    backup_program(self)
    get_program(self, num, progid, inst, pi)
    split_by_frameno(self)
    """
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
        self.engineering = {'kcwieng':'outdir', 'kcwirun':'outdir', 
                'hireseng':'outdir','nspeceng':'outdir', 
                'nirc2eng':'outdir', 'engineering':'observer',
                'dmoseng':'outdir', 'lriseng':'outdir', 'esieng':'outdir',
                'keck ipdm':'observer', 'nirspec':'observer',
                'nireseng':'outdir'}
        self.fileList = []
        self.instrList = {'DEIMOS':2, 'ESI':2, 'HIRES':1, 
                'KCWI':2, 'LRIS':1, 'MOSFIRE':1, 
                'NIRC2':2, 'NIRSPEC':2, 'OSIRIS':1, 'NIRES':2}
        self.instrument = instr
        self.numFiles = 0
        self.numSciencePI = 0
        self.too = {'_ToO_':'outdir'}
        self.observer = []
        self.obsValues = []
        self.outdir = []
        self.programs = []
        self.splitTime = 0.0
        self.stageDir = stage_dir
        self.sunset = 0.0
        self.sunrise = 0.0
        self.utDate = ut_date
        self.semester = self.get_semester()
        self.sciFiles = {}
        self.api = 'https://www.keck.hawaii.edu/software/db_api/'
        self.log = log
        self.rootDir = self.stageDir.split('/stage')[0]
        if not self.log:
            self.log = cl.create_log(self.rootDir, instr, ut_date)
    def get_semester(self):
        """
        This method determines the semester of the observation
        using the date in UTC
        """

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
            raise Exception("progInfo - stage directory doesn't exist!")
            return

    def check_instrument(self):
        """
        This method checks if the instrument is one of the existing
        instruments
        """
        if self.instrument not in self.instrList:
            print("Instrument must be one of: ")
            for item in self.instrList:
                print('\t', item)

    def read_dep_obtain(self):
        """
        This method reads the files from the dep_obtain output file
        """

        obFile = self.stageDir + '/dep_obtain' + self.instrument + '.txt'
        self.programs = get_obtain_data(obFile)

        for data in self.programs:
            if (data['progid'] != 'ENG'):
                self.numSciencePI += 1


    def read_file_list(self):
        """
        This method reads the list of files from the file list
        """
        colsToSave = ['file','utdate','utc','outdir','observer','frameno',
                'imagetyp','progid','progpi','proginst','progtitl','oa']
        colCount = len(colsToSave)
        fname = ''.join((self.stageDir, '/createprog.txt'))
        if not os.path.isfile(fname):
            raise Exception('This file does not exist!!!')
            return
        with open(fname, 'r') as flist:
            num = 0
            count = 0
            row = {}
            for line in flist:
                # Populate the dict with the information from file
                row[colsToSave[num]] = line.strip()
                num += 1
                if num == colCount:
                    self.fileList.append(row)
                    # Check to see if it is an engineering night
                    # Key = instrument, value = outdir/obs
                    for key, value in self.engineering.items():
                        if key in self.fileList[count][value].lower() or self.fileList[count]['progid'] == 'ENG':
                            self.fileList[count]['proginst'] = 'KECK'
                            self.fileList[count]['progid'] = 'ENG'
                            self.fileList[count]['progpi'] = ''.join((self.instrument.lower(), 'eng'))
                            self.fileList[count]['progtitl'] = ''.join((self.instrument.upper(), ' Engineering'))
                    # Check to see if it is a ToO observation
                    for key, value in self.too.items():
                        if key in self.fileList[count][value]:
                            #todo: why is this default section here?
                            self.fileList[count]['proginst'] = 'KECK'
                            self.fileList[count]['progid'] = 'ToO'
                            self.fileList[count]['progpi'] = 'ToO'
                            self.fileList[count]['progtitl'] = 'ToO'
                            garbage, progid = self.fileList[count][value].split('_ToO_')
                            progid, garbage = sem.split('/')
                            progpi = self.get_prog_pi(self.semester, progid)
                            progtitl = self.get_prog_title(self.semester, progid)
                            self.fileList[count]['proginst'] = 'KECK'
                            self.fileList[count]['progid'] = progid
                            self.fileList[count]['progpi'] = progpi
                            self.fileList[count]['progtitl'] = progtitl
                    # Reset for the next file
                    count += 1
                    num = 0
                    del row
                    row = {}
            # Number of files found
            self.numFiles = count

# ---------------- END READ FILE LIST--------------------------------------------------------

    def assign_to_pi(self, num):
        """
        This method assigns a PI to a program if
        the file does not already have a PI

        @type num: int
        @param num: number of programs to assign PIs to
        """
        num -= 1
        save = ('oa','proginst','progpi','progid')
        for i in range(self.numFiles):
            # If file already has PI, skip
            if self.fileList[i]['progpi'] != 'PROGPI':
                continue
            for col in save:
                self.fileList[i][col] = self.programs[num][col]
            if self.fileList[i]['progid'] == 'ENG':
                title = ''.join((self.instrument, ' Engineering'))
                self.fileList[i]['progtitl'] = title
            else:
                self.fileList[i]['progtitl'] = self.get_prog_title(
                        self.semester,
                        self.programs[num]['progid'])
            if (self.fileList[i]['progpi'] == 'PROGPI'
                    or self.fileList[i]['progpi'] == ''
                    or self.fileList[i]['progpi'] == 'NONE'):
                self.backup_program()

#--------------------------- END ASSIGN TO PI---------------------------------------------

    def assign_single_to_pi(self, filenum, num):
        """
        Assign a single file a PI

        @type filenum: int
        @param filenum: the index of the file to assign a PI
        @type num: int
        @param num: the index of the program to use to assign PI
        """
        # If file already has PI, skip
        if (self.fileList[filenum]['progpi'] != 'PROGPI'
                and self.fileList[filenum]['progpi'] != ''):
            return
        num -= 1
        save = ('oa', 'proginst', 'progpi', 'progid')
        if len(self.programs) == 1 and num == 1:
            num = 0
        for col in save:
            self.fileList[filenum][col] = self.programs[num][col]
        if self.fileList[filenum]['progid'] == 'ENG':
            title = ''.join((self.instrument, ' Engineering'))
            self.fileList[filenum]['progtitl'] = title
        else:
            self.fileList[filenum]['progtitl'] = self.get_prog_title(
                    self.semester,
                    self.programs[num]['progid'])

#---------------------------- END ASSIGN SINGLE TO PI-------------------------------------------

    def get_schedule_value(self, col):
        """
        Method to get a single value from the telescope schedule

        @type col: string
        @param col: the key for the value to extract from the database
        """
        telno = self.instrList[self.instrument]
        req = ''.join((self.api, 'telSchedule.php?cmd=getSchedule&date=',
                str(self.utDate), '&telnr=', str(telno),
                '&instr=', self.instrument, '&column=', col))
        val = url.urlopen(req).read().decode()
        val = json.loads(val)
        return val

#---------------------------------- END GET SCHEDULE VALUE------------------------------------

    def get_sun_times(self):
        req = url.urlopen(''.join((self.api, 'metrics.php?date=', self.utDate)))
        suntimes = req.read().decode()
        suntimes = json.loads(suntimes)
        rise = suntimes['dawn_12deg']
        sset = suntimes['dusk_12deg']
        risHr, risMin, risSec = rise.split(':')
        setHr, setMin, setSec = sset.split(':')
        self.sunrise = float(risHr)+float(risMin)/60.0+float(risSec)/3600.0
        self.sunset = float(setHr)+float(setMin)/60.0+float(setSec)/3600.0
        self.splitTime = (self.sunrise+self.sunset)/2.0

#------------------------------END GET SUN TIMES------------------------------------------------

    def get_prog_title(self, sem, progid):
        """
        Query the DB and get the program title

        @type sem: string
        @param sem: semester of the observation
        @type progid: string
        @param progid: ID of the observation program
        """

        semid = ''.join((sem, '_', progid))
        req = ''.join((self.api, 'koa.php?cmd=getTitle&semid=', semid))
        title = url_get(req, getOne=True)
        if (title == None or 'progtitl' not in title): 
            self.log.warning('get_prog_title: Could not find program title for semid "{}"'.format(semid))
            return 'NONE'
        else : return title['progtitl']

#--------------------- END GET PROG TITLE-----------------------------------------------

    def get_prog_pi(self, sem, progid):
        """
        Query the DB and get the prog PI last name

        @type sem: string
        @param sem: semester of the observation
        @type progid: string
        @param progid: ID of the observation program
        """

        semid = ''.join((sem, '_', progid))
        req = ''.join((self.api, 'koa.php?cmd=getPI&semid=', semid))
        pi = url_get(req, getOne=True)
        if (pi == None or 'pi_lastname' not in pi): 
            self.log.warning('get_prog_pi: Could not find program PI for semid "{}"'.format(semid))
            return 'NONE'
        else : return pi['pi_lastname']

#--------------------- END GET PROG TITLE-----------------------------------------------

    def get_outdir(self, times, num_splits):
        splitTimes = []
        for split in times:
            splitTimes.append((t.strptime(split['StartTime'], '%H:%M:%S').
                t.strptime(split['EndTime'], '%H:%M:%S')))
        for key, val in self.fileList:
            splits = list(range(1,num_splits+1))
            fdir = self.fix_outdir(val['outdir'])
            eng = 0
            for engname, name in self.engineering:
                if engname in fdir:
                    eng = 1

            # Add new outdirs to the outdir list
            if fdir not in self.outdir and eng != 0 and fdir != '0':
                if 'fcs' in fdir:
                    continue
                self.outdir.append([fdir, times['ProjCode']])
                self.sciFiles[fdir] = {}
                for index in splits:
                    self.sciFiles[fdir][index] = 0
            if val['imagetyp']=='object':
                for i in range(len(splitTimes)):
                    if (splitTimes[i][0] <= t.strptime(val['utc'], '%H:%M:%S')
                            < splitTimes[i][1]):
                        self.sciFiles[fdir][splits[i]] += 1
                        break

#--------------------------------END GET OUTDIR-----------------------------

    def get_observer(self):
        repchar = [' ','_','/','&','.',',,']
        count = []
        temp = []
        for key, val in self.fileList:
            obs = val['observer']
            if obs != 'Keck Engineering':
                outdir = self.fix_outdir(val['outdir'])
            for char in repchar:
                obs = obs.replace(char, ',')
            if obs not in temp:
                temp.append(obs)
            obs = ''.join((obs, '_', outdir))
            if obs not in self.observer:
                self.observer.append(obs)
        self.obsValues = len(temp)

#----------------------END GET OBSERVER------------------------------------

    def split_multi_by_science(self):
        """
        """
        # Default, bad values
        assign = [-2]*len(self.programs)

        # Loop through the OUTDIRs and assume yyyyMMMdd, yyyyMMMdd_B...
        num =  cycle = 0
        diff1 = diff2 = 0
        for i in range(len(self.outdir)):
            if '/_A/' in self.outdir[i]:
                assign[i] = 1
            elif '/_B/' in self.outdir[i]:
                assign[i] = 2
            elif '/_C/' in self.outdir[i]:
                assign[i] = 3
            elif '/_D' in self.outdir[i]:
                assign[i] = 4
            elif '/_E' in self.outdir[i]:
                assign[i] = 5
            else:
                assign[i] = 1
            print(''.join(
                ('Assigning', self.outdir[i], 'to', assign[i])))

        # Split by OUTDIR
        for key, val in self.fileList:
            for i in range(len(self.outdir)):
                if self.fix_outdir(val['outdir']) == self.outdir[i]:
                    self.assign_single_to_pi(key, assign[i])

#---------------------END SPLIT MULTI BY SCIENCE---------------------------

    def fix_outdir(self, outdir):
        """
        Function to remove unwanted subdirectories from outdir

        @type outdir: string
        @param outdir: path to be have subdirs removed
        """
        if '/fcs' in outdir:
            outdir.replace('/fcs', '')
        rep = ['/s/', '//', '/scam/', '/spec/', '/scam', '/spec']
        for subdir in rep:
            oudir = outdir.replace(subdir, '/')
        return outdir

#-----------------------------END FIX SUBDIR--------------------------------

    def backup_program(self):
        """
        """
        if self.instrument not in ['NIRC2', 'NIRSPEC']:
            return

        for key, val in self.fileList:
            if (self.fileList[key]['progpi'] != 'PROGPI'
                    and self.fileList[key]['progpi'] != 'NONE'
                    and self.fileList['progpi'] != ''):
                continue

        # Begin isntrBackup.php code
            # URL to query the database for ProjCode, Institution, and Principal
            req = ''.join((self.api, 'telSchedule.php?cmd=getSchedule&date=',
                    self.utDate, '&telnr=2&column=ProjCode,Institution,Principal,StartTime, EndTime'))

            # Then we get the results returned by the query
            res = url.urlopen(req).read().decode()
            dat = json.loads(res)

            if type(dat) == type(dict()): # Single entries return as dict
                #  Unpack the value into the variables
                progid = dat['ProjCode']
                inst = dat['Institution']
                pi = dat['Principal']
                title = get_program(-1, progid, institution, pi)
            else: # Multiple Entries return as a list, so split night
                for i in range(len(dat)):
                    if (t.strptime(dat[i]['StartTime'], '%H:%M:%S')
                            <= t.strptime(self.fileList[key]['utc'], '%H:%M:%S')
                            < t.strptime(dat[i]['EndTime'], '%H:%M:%S')):
                        num = i
                        break
                progid = dat[num]['ProjCode']
                inst = dat[num]['Institution']
                pi = dat[num]['Principal']
                title = get_program(num, progid, inst, pi)
                title = ''.join(title.split(' ')[3:])

            self.fileList[key]['proginst'] = inst
            self.fileList[key]['progid'] = progid
            self.fileList[key]['progpi'] = pi
            self.fileList[key]['progtitl'] = title

#--------------------------------------END BACKUP PROGRAM---------------------------------

    def get_program(self, num, progid, inst, pi):
        """
        Method to determine which program to use
        """
        instr = ''
        if 'N2' in progid[-3:]:
            instr = 'NIRC2'
        elif 'O' in progid[-2:]:
            instr = 'OSIRIS'
        elif 'AK' in progid[-2:]:
            instr = 'KCAM'
        if instr != '':
            return (''.join((progid, ' ', inst, ' ',
                    pi, ' ', instr, ' backup program')))
        else:
            return 'ENG KECK Engineering Engineering'

#----------------------------------END GET PROGRAM-----------------------------------

    def sort_by_time(self, vals):
        """
        Simple Bubble Sort algorithm to reorder multiple nights by StartTime
        """
        cont = True
        while(cont):
            # Set continue to false so that if it is sorted it is done
            cont = False
            for i in range(len(vals)-1):
                if (time.strptime(vals[i]['StartTime'],'%H:%M:%S')
                        > time.strptime(vals[i+1]['StartTime'],'%H:%M:%S')):
                    temp = vals[i]
                    vals[i] = vals[i+1]
                    vals[i+1] = temp
                    del temp
                    cont = True

#----------------------------------END SORT BY TIME----------------------------------

def getProgInfo(utdate, instrument, stageDir, log=None):
    utdate = utdate.replace('/','-')
    instrument = instrument.upper()
    progSplit = ProgSplit(utdate, instrument, stageDir, log)
    progSplit.check_stage_dir()
    progSplit.check_instrument()
    progSplit.read_dep_obtain()
    progSplit.read_file_list()

    splitNight = 0
    codeStartEnd = progSplit.get_schedule_value('ProjCode,StartTime,EndTime')

    # Check if a Dict or a List was returned
    if type(codeStartEnd) == type(list()) and len(progSplit.programs) != 1:
        splitNight = len(codeStartEnd)
    else:
        splitNight = 1

    if splitNight == 1: # No split
        msg = ''.join(('getProgInfo: ', utdate, ' is not a split night'))
        progSplit.log.info(msg)
        if len(progSplit.programs) == 1:
            msg = ''.join(('getProgInfo: Assigning to ', progSplit.instrument, ' PI'))
            progSplit.log.info(msg)
            progSplit.assign_to_pi(1)
        elif instrument == 'NIRSPEC':
            # Check for NIRSPEC backup
            progSplit.log.info('getProgInfo: NIRSPEC backup program')
            progSplit.backup_program()
        elif instrument == 'NIRC2':
            # check for NIRC2 backup
            progSplit.log.info('getProgInfo: NIRC2 backup program')
            progSplit.backup_program()
    elif splitNight > 1: # Split night
        msg = ''.join(('getProgInfo: ', utdate, ' is a split night with ',
                str(len(progSplit.programs)), ' programs'))
        progSplit.log.info(msg)
        progSplit.sort_by_time(codeStartEnd)
        progSplit.get_sun_times()
        progSplit.get_outdir(codeStartEnd, splitNight)
        msg = ''.join(('getProgInfo: ', len(progSplit.outdir), ' OUTDIRs found'))
        progSplit.log.info(msg)

        # Split the stuff
        # setNum is the number of the program from dep_obtain
        for setNum in range(len(codeStartEnd)):
            # fileNum is the number of the file from createprog
            for fileNum in range(len(progSplit.fileList)):
                try:
                    if progSplit.fileList[fileNum]['outdir'] == progSplit.outdir[setNum][0]:
                        progSplit.assign_single_to_pi(fileNum, setNum)
                except KeyError:
                    if (t.strptime(codeStartEnd[setNum]['StartTime'],'%H:%M:%S')
                            <= t.strptime(progSplit.fileList[fileNum]['utc'],'%H:%M:%S')
                            <= t.strptime(codeStartEnd[setNum]['EndTime'],'%H:%M:%S')):
                        progSplit.assign_single_to_pi(fileNum,setNum)
    else:
        print('No project code was found!!!')
        progSplit.log.warning('No project code was found!!!')

    fname = ''.join((stageDir, '/newproginfo.txt'))
    with open(fname, 'w') as ofile:
        for progfile in progSplit.fileList:
            line = ''.join((progfile['file'], ' ',
                            progfile['outdir'], ' ',
                            progfile['proginst'],' ',
                            progfile['progid'], ' ',
                            progfile['progpi'], ' ',
                            progfile['progtitl'], '\n'))
            ofile.writelines(line)

    msg = ''.join(('Assigning to ', progSplit.instrument, ' PI'))
    progSplit.log.info('getProgInfo: finished, {} created'.format(fname))


    #return data written for convenience
    return progSplit.fileList
