"""
"""

import os
import json
import koa_db_conn as kdb
import mysql_conn as msc
import metrics_conn as metrics
import urllib.request as url
import pymysql as pms

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
    @type log: Logger object
    @param log: log handler that writes messages to a log
    @type sciFiles: list
    @param sciFiles: stores the valid science files
    @type api: string
    @param api: base url for querying the RESTful API

    Methods:
    __init__(self, ut_date, instr, stage_dir, lg)
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
    def __init__(self, ut_date, instr, stage_dir, lg):
        """
        Initialization function for the ProgSplit class

        @type ut_date: string
        @param ut_date: Date of observaton in UT timezone
        @type instr: string
        @param instr: Instrument that is being observed
        @type stage_dir: string
        @param stage_dir: directory we are moving processed files to
        @type lg: Logger object
        @param lg: Logger object that handles information, warning, and error logging
        """
        self.engineering = {'kcwieng':'outdir', 'kcwirun':'outdir', 
                'hireseng':'outdir','nspeceng':'outdir', 
                'nirc2eng':'outdir', 'engineering':'observer',
                'dmoseng':'outdir', 'lriseng':'outdir', 'esieng':'outdir',
                'keck ipdm':'observer', 'nirspec':'observer'}
        self.fileList = []
        self.instrList = {'DEIMOS':2, 'ESI':2, 'HIRES':1, 
                'KCWI':2, 'LRIS':1, 'MOSFIRE':1, 
                'NIRC2':2, 'NIRSPEC':2, 'OSIRIS':1}
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
        self.log = lg
        self.sciFiles = []
        self.api = 'https://www.keck.hawaii.edu/software/db_api/'

    def get_semester(self):
        """
        This method determines the semester of the observation
        using the date in UTC
        """
        yr, mo, dy = self.utDate.split('-')
        iyr = int(yr)
        imo = int(mo)
        idy = int(dy)
        sem = 'A'

        if imo > 8 or imo < 2:
            sem = 'B'
        elif imo == 8 and idy > 1:
            sem = 'B'
        elif imo == 2 and idy < 1:
            sem = 'B'
        if imo == 1 or (imo ==2 and idy == 1):
            iyr -= 1
        return str(iyr) + sem

    def check_stage_dir(self):
        """
        This method checks whether or not the stage dir exists
        """
        if not os.path.isdir(self.stageDir):
            self.log.warning("progInfo - stage directory doesn't exist!")

    def check_instrument(self):
        """
        This method checks if the instrument is one of the existing
        instruments
        """
        if self.instrument not in self.instrList:
            self.log.warning('progInfo - unknown instrument!')
            print("Instrument must be one of: ")
            for item in self.instrList:
                print('\t', item)

    def read_dep_obtain(self):
        """
        This method reads the files from the dep_obtain output file
        """
        seq = (self.stageDir, '/dep_obtain', self.instrument, '.txt')
        readfile = ''.join(seq)
        if not os.path.exists(readfile):
            self.log.warning('progInfo - file does not exist!!')
            exit()

        save = ['utdate', 'oa','account', 'proginst', 'progpi', 'progid', 'observer']
        with open(readfile, 'r') as rfile:
            for line in rfile:
                vals = line.strip().split(' ')
                if vals[5] != 'ENG': # vals[5] is progid
                    self.numSciencePI += 1
                row = {}
                for i in range(1, len(save)):
                    row[save[i]] = vals[i]
                self.programs.append(row)
                del row

    def read_file_list(self):
        """
        This method reads the list of files from the file list
        """
        colsToSave = ['file','utdate','utc','outdir','observer','frameno',
                'imagetyp','progid','progpi','proginst','progtitl','oa']
        colCount = len(colsToSave)
        seq = (self.stageDir, '/createprog.txt')
        fname = ''.join(seq)
        if not os.path.isfile(fname):
            self.log.warning('This file does not exist!!!')
            exit()
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
                    for key, value in self.engineering.items():
                        if key in self.fileList[count][value].lower():
                            self.fileList[count]['proginst'] = 'KECK'
                            self.fileList[count]['progid'] = 'ENG'
                            seq = (self.instrument.lower(), 'eng')
                            self.fileList[count]['progpi'] = ''.join(seq)
                            seq = (self.instrument.lower(), ' Engineering')
                            self.fileList[count]['progtitl'] = ''.join(seq)
                    # Check to see if it is a ToO observation
                    for key, value in self.too.items():
                        if key in self.fileList[count][value]:
                            self.fileList[count]['proginst'] = 'KECK'
                            self.fileList[count]['progid'] = 'ToO'
                            self.fileList[count]['progpi'] = 'ToO'
                            self.fileList[count]['progtitl'] = 'ToO'
                            # Get semid
                            garbage, sem = self.fileList[count][value].split('_ToO_')
                            sem, garbage = sem.split('/')
                            # Get program information
                            semid = ''.join((self.semester, '-', sem))
                            req = ''.join((self.api, 'koa.php?cmd=getPI&semid=', 
                                    semid))
                            pid = url.urlopen(req).read().decode()['progpi']
                            req = ''.join((self.api, 'koa.php?cmd=getTitle&semid=', 
                                    semid))
                            titl = url.urlopen(req).read().decode()['progtitl']
                            self.fileList[count]['proginst'] = 'KECK'
                            self.fileList[count]['progid'] = sem
                            self.fileList[count]['progpi'] = pid
                            self.fileList[count]['progtitl'] = titl
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
                seq = (self.instrument, ' Engineering')
                self.fileList[i]['progtitl'] = ''.join(seq)
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
            seq = (self.instrument, ' Engineering')
            self.fileList[filenum]['progtitl'] = ''.join(seq)
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
                self.utDate, '&telnr=', telno, '&column=', col))
        val = url.urlopen(req).read().decode()
        val = json.loads(val)[0][col]
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
        req = url.urlopen(req)
        title = req.read().decode()
        title = json.loads(title)['progtitl']
        return title

#--------------------- END GET PROG TITLE-----------------------------------------------

    def get_outdir(self):
        utdate = ''
        for key, val in self.fileList:
            ttype = 'firsthalf'
            utdate = val['utdate']
            uhr, umin, usec = val['utc'].split(':')
            time = float(uhr) + float(umin)/60.0 + float(usec)/3600.0
            if time > self.splitTime:
                ttype = 'secondhalf'
            if utdate != self.utDate:
                ttype = 'firsthalf'
            fdir = self.fix_outdir(val['outdir'])
            eng = 0
            for engname, name in self.engineering:
                if engname in fdir:
                    eng = 1
            if fdir not in self.outdir and eng != 0 and fdir != '0':
                if fcs in fdir:
                    continue
                self.outdir.push(fdir)
                self.sciFiles[fdir]['firsthalf'] = 0
                self.sciFiles[fdir]['secondhalf'] = 0
            if val['imagetyp']=='object':
                self.sciFiles[fdir][ttype] += 1

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
            seq = (obs, '_', outdir)
            obs = ''.join(seq)
            if obs not in self.observer:
                self.observer.append(obs)
        self.obsValues = len(temp)

#----------------------END GET OBSERVER------------------------------------

    def split_by_observer(self):
        """
        """
        # Get observers value from telescope schedule
        obs = self.get_schedule_value('observers')
        obs = obs.split('/')
        rep = [' ', '_', '/', '&', '.', ',,', ',and,']

        for key, val in self.fileList:
            found = ''
            observer = ''
            for char in rep:
                observer = val['observer'].replace(char, ',')
            split = observer.split(',')
            for name in split:
                if len(name) > 2:
                    for num, obsval in obs:
                        if name.lower() in obsval.lower():
                            found += num + 1
            if found%11 == 0 or found < 5:
                if found > 5:
                    found /= 11
                self.assign_single_to_pi(key, found)

#--------------------END SPLIT BY OBSERVER----------------------------------

    def split_by_time(self):
        seq = (' -- Splitting at ', self.splitTime)
        self.log.info(''.join(seq))

        for key, val in self.fileList:
            utdate = val['utdate']
            hr, mn, sc = val['utc'].split(':')
            utc = float(hr) + float(mn)/60.0 + float(sc)/3600.0
            num = 1

            # Second half
            if utc >= self.splitTime:
                num = 2
            # First half
            if utdate != self.utDate:
                num = 1
            self.assign_single_to_pi(key, num)

#---------------------END SPLIT BY TIME---------------------------------------

    def split_by_science(self):
        """
        """
        # Default, bad values
        first = -2
        second = -2

        # How many halves have science files? Must be > 1
        numHalf = 0

        # Loop through outdirs and determine which has most sci
        num = cycle = 0
        diff1 = diff2 = 0
        for key, val in self.outdir:
            # Must get through this if twice
            if (self.sciFiles[val]['firsthalf'] > 0
                    or self.sciFiles[val]['secondhalf'] > 0):
                numHalf+=1
            # Same number of sciFiles - bad
            if self.sciFiles[val]['firsthalf'] == num and cycle != 0:
                first = -1
            # Least number of sci is second half
            if self.sciFiles[val]['firsthalf'] < num:
                second = key
            # Less than 4 files - bad
            if self.sciFiles[val]['firsthalf'] + self.sciFiles[val]['secondhalf'] < 10:
                second = -1
            # Higher sci number is first half
            if (self.sciFiles[val]['firsthalf'] > num
                    and (first != -1 and second != -1)):
                second = first
                first = key
                num = self.sciFiles[val]['firsthalf']
            cycle += 1

        # Do nothing if same number of science files for each half
        if first == -1:
            self.log.info('progInfo.php - Same number of science files in each half')
            return

        # Do nothing if one outdir has most data
        if second == -1:
            self.log.info('progInfo.php - not enough data in one OUTDIR, treating as one')
            return

        # Do nothing if only one half had science
        #if numHalf <= 1:
        #    self.log.info(' -- Science frames in half' + first + 'only')
        #    return

        # Split by OUTDIR
        if second < 0:
            second = 0
        self.log.info('First half being assigned to ' + first)
        self.log.info('Second half being assigned to ' + second)
        for key, val in self.fileList:
            if self.fix_outdir(val['outdir']) == self.outdir[first]:
                self.assign_single_to_pi(key, 1)
            else:
                self.assign_single_to_pi(key, 2)

#---------------------------------END SPLIT BY SCIENCE-----------------------------------

    def split_multi_by_science(self):
        """
        """
        # Default, bad values
        assign = [-2]*len(self.programs)

        # Loop through the OUTDIRs and assume yyyyMMMdd, yyyyMMMdd_B...
        num =  cycle = 0
        diff1 = diff2 = 0
        for key, val in self.outdir:
            if '/_A/' in val:
                assign[key] = 1
            elif '/_B/' in val:
                assign[key] = 2
            elif '/_C/' in val:
                assign[key] = 3
            elif '/_D' in val:
                assign[key] = 4
            elif '/_E' in val:
                assign[key] = 5
            else:
                assign[key] = 1
            seq = ('Assigning ', val, ' to ', assign[key])
            self.log.info(''.join(seq))

        # Split by OUTDIR
        for key, val in self.fileList:
            for key2, val2 in self.outdir:
                if self.fix_outdir(val['outdir']) == val2:
                    self.assign_single_to_pi(key, assign[key2])

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

        yr, mo, dy = self.utDate.split('-')
        date = ''.join((yr, '/', mo, '/', str(int(dy)-1)))
        for key, val in self.fileList:
            if (self.fileList[key]['progpi'] != 'PROGPI'
                    and self.fileList[key]['progpi'] != 'NONE'
                    and self.fileList['progpi'] != ''):
                continue

            # Base url request for DB query
            req = ''.join((self.api, 'telSchedule.php?cmd=getScheduleColumn&date=',
                    self.utDate, '&telnr=2&column='))

            # Get the Project Code, Institution and Principal from TelSched
            # First we create the url to query the db
            projcode = ''.join((req, 'ProjCode'))
            inst = ''.join((req, 'Institution'))
            pi = ''.join((req, 'Principal'))

            # Then we get the results returned by the query
            projcode = url.urlopen(projcode).read().decode()
            inst = url.urlopen(inst).read().decode()
            pi = url.urlopen(pi).read().decode()

            #  Finally we load the JSON into a dict and access the value
            projcode = json.loads(projcode)['ProjCode']
            inst = json.loads(inst)['Institution']
            pi = json.loads(pi)['Principal']

            if len(program) == 1:
                title = get_program(-1, program, institution, pi)
            else: # split night
                # Get sun times
                self.get_sun_times()
                nightLen = self.sunrise - self.sunset
                midNight = self.sunset + nightLen/2.0
                hr, mn, sc = self.utc.split(':')
                time = float(hr) + float(mn)/60.0 + float(sc)/3600.0
                if time <= midNight:
                    num = 0
                else:
                    num = 1
                progid = program[num]
                title = get_program(num, progid, inst, pi)

            progid = backup['ProjCode'].strip()
            inst = backup['Institution'].strip()
            pi = backup['Principal'].strip()
            title = ''

#--------------------------------------END BACKUP PROGRAM---------------------------------

    def get_program(self, num, progid, inst, pi):
        """
        Method to determine which program to use
        """
        if num != -1:
            split1 = inst.split('/')
            if len(split1 == 1):
                split1.append(split1[0])
            split2 = pi.split('/')
            if len(split2 == 1):
                split2.append(split2[0])
            if len(split1) >= num:
                inst = split1[num]
            else:
                inst = split[0]
            if count(split2) >= num:
                pi = split2[num]
            else:
                pi = split2[0]
        pi = pi.replace(' ', '')

        instr = ''
        if '/N2' in progid:
            instr = 'NIRC2'
        elif '/O' in progid:
            instr = 'OSIRIS'
        elif '/AK' in progid:
            instr = 'KCAM'
        if instr != '':
            seq = (progid, ' ', inst, ' ', pi, ' ', instr, ' backup program')
            return ''.join(seq)
        else:
            return 'ENG KECK Engineering Engineering'

#----------------------------------END GET PROGRAM-----------------------------------

    def split_by_frameno(self):
        numSplits = 0
        count =1
        ftype = ''
        prev = 0
        tsplit = 24
        for i in range(len(self.fileList)):
            outdir = self.fileList[i]['outdir'].strip().replace('//','/')
            outdir = outdir.replace('/', ' ')
            type2 = outdir.strip().split(' ')
            type2 = type2[-1]
            if type2 != ftype:
                count = 1
            if prev != 0 and count >= 8:
                diff = self.fileList[i]['frameno'] - prev
                if diff > 25 and ftype == type2:
                    hr, mn, sc = self.fileList[i]['utc'].split(':')
                    temp = float(hr) + float(mn)/60.0 + float(sc)/3600.0
                    if self.sunset < temp < tsplit:
                        tsplit = temp
                    numSplits += 1
            if self.fileList[i]['frameno'] != 1:
                prev = self.fileList[i]['frameno']
            ttype = type2
            count += 1
        if tsplit != 24 and numSplits < 4:
            self.splitTime = tsplit
            return 1
        return 0

#--------------------------END SPLIT BY FRAMENO------------------------------------

def getProgInfo(utdate, instrument, stageDir, log):
    utdate = utdate.replace('/','-')
    instrument = instrument.upper()
    progSplit = ProgSplit(utdate, instrument, stageDir, log)
    progSplit.check_stage_dir()
    progSplit.check_instrument()
    progSplit.read_dep_obtain()
    progSplit.read_file_list()

    splitNight = 0
    code = progSplit.get_schedule_value('ProjCode')
    if '/' in code:
        splitNight = 1
    if splitNight == 0:
        progSplit.log.warning(utdate + ' is not a split night')
        if len(progSplit.programs) == 1:
            msg = ('Assigning to ', progsplit.instrument, ' PI')
            msg = ''.join(msg)
            print(msg)
            progSplit.log.info(msg)
            progSplit.assign_single_to_pi(1)
        elif instrument == 'NIRSPEC':
            # Check for NIRSPEC backup
            print('NIRSPEC backup program')
            progSplit.log.info('NIRSPEC backup program')
            progSplit.backup_program()
        elif instrument == 'NIRC2':
            # check for NIRC2 backup
            print('NIRC2 backup program')
            progSplit.log.info('NIRC2 backup program')
            progSplit.backup_program()
    else:
        msg = (utdate, ' is a split night with ', str(len(progSplit.programs)), ' programs')
        msg = ''.join(msg)
        print(msg)
        progSplit.log.info(msg)
        progSplit.get_sun_times()
        progSplit.get_outdir()
        msg = (len(progSplit.outdir), 'OUTDIRs found')
        msg = ''.join(msg)
        print(msg)
        progSplit.log.info(msg)

        for key, val in progSplit.outdir:
            temp = (key, ' -- ', val, ': first half of sci = ', 
                    progSplit.sciFiles[val]['firsthalf'], 
                    '  second half of sci = ', 
                    progSplit.sciFiles[val]['secondhalf'])
            msg = ''.join(temp)
            print(msg)
            progSplit.log.info(msg)

        if len(progSplit.outdir) == 1:
            print('Checking FRAMENO')
            progSplit.log.info('Checking FRAMENO')
            return_val = progSplit.split_by_frameno()
            if return_val > 0:
                progSplit.split_by_time()
            else:
                progSplit.get_observer()
                if progSplit.obsValues > 1 or progSplit.numSciencePI == 1:
                    print('Splitting by observer')
                    progSplit.log.info('Splitting by Observer')
                    progSplit.split_by_observer()
        elif len(progSplit.outdir) == 2:
            # Split by OUTDIR
            print('Checking FRAMENO')
            progSplit.log.info('Checking FRAMENO')
            return_val = progSplit.split_by_frameno()
            if len(progSplit.programs) == len(progSplit.outdir):
                sci1 = progSplit.sciFiles[progSplit.outdir[0]]['firsthalf']
                sci2 = progSplit.sciFiles[progSplit.outdir[1]]['firsthalf']
                if sci1 != sci2:
                    print('Splitting by OUTDIR/Science Files')
                    progSplit.log.info('Splitting by OUTDIR/Science Files')
                    progSplit.split_by_science()
            elif return_val > 0:
                progSplit.split_by_time()
            else: # Split by observer
                print('Splitting by observer')
                progSplit.log.info('Splitting by Observer')
                progSplit.split_by_observer()
        else:
            sci1 = progSplit.sciFiles[progSplit.outdir[0]]['firsthalf']
            sci2 = progSplit.sciFiles[progSplit.outdir[1]]['firsthalf']
            if sci1 != sci2:
                print('Splitting by OUTDIR/Science files')
                splitProg.log.info('Splitting by OUTDIR/Science files')
                progSplit.split_multi_by_science()
            # Observers
            else:
                print('Splitting by Observer')
                splitProg.log.info('Splitting by Observer')
                progSplit.split_by_observer()

