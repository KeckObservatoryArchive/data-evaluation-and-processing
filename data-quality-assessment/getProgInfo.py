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
    def __init__(self, ut_date, instr, stage_diri, lg):
        self.engineering = {'kcwieng':'outdir', 'kcwirun':'outdir', 
                'hireseng':'outdir','nspeceng':'outdir', 
                'nirc2eng':'outdir', 'engineering':'observer',
                'dmoseng':'outdir', 'lriseng':'outdir', 'esieng':'outdir',
                'keck ipdm':'observer', 'nirspec':'observer'}
        self.fileList = [{}]
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
        self.programs = [{}]
        self.semester = this.get_semester()
        self.splitTime = 0.0
        self.stageDir = stage_dir
        self.sunset = 0.0
        self.sunrise = 0.0
        self.utDate = ut_date
        self.log = lg
        self.sciFiles = []

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
        if instrument not in instrList:
            self.log.warning('progInfo - unknown instrument!')
            print("Instrument must be one of: ")
            for item in instrList:
                print('\t' + item)

    def read_dep_obtain(self):
        """
        This method reads the files from the dep_obtain output file
        """
        seq = (self.stageDir, '/dep_obtain', instrument, '.txt')
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
        seq = (self.stageDir, 'createprog.txt')
        fname = ''.join(seq)
        if not os.path.isFile(fname):
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
                    count += 1
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
                            db = kdb.get_connection()
                            query = 'SELECT koa_pi.*, koa_program.* FROM koa_pi LEFT JOIN koa_program '
                            query += 'ON koa_pi.piID=koa_program.piID WHERE koa_program.semid='
                            query += self.semester + '_' + sem + 'and koa_program.type="ToO"'
                            with db.cursor(pymysql.cursors.DictCursor) as cursor:
                                cursor.execute(query)
                                res = cursor.fetchone()
                                sem, prog = res[7].split('_')
                                self.fileList[count]['proginst'] = 'KECK'
                                self.fileList[count]['progid'] = prog
                                self.fileList[count]['progpi'] = res[1].replace(' ','')
                                self.fileList[count]['progtitl'] = res[9]
                    # Reset for the next file
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
                self.fileList[i]['progtitl'] = self.get_prog_title(self.programs[num]['progid'])
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
            self.fileList[filenum]['progtitl'] = self.get_prog_title(self.programs[num]['progid'])

#---------------------------- END ASSIGN SINGLE TO PI-------------------------------------------

    def get_schedule_value(self, col):
        """
        Method to get a single value from the telescope schedule

        @type col: string
        @param col: the key for the value to extract from the database
        """
        seq = ('vm-koaserver5:50001/sched_api?cmd=getSchedule&date=', 
                self.utDate, '&col=', col)
        qry = ''.join(seq)
        req = url.urlopen(qry).read().decode()
        # single json dicts won't allow [] so remove them
        if '},' not in req and req[0] == '[':
            req = req[1:-1]
        data = json.loads(req)
        return data[col]

#---------------------------------- END GET SCHEDULE VALUE------------------------------------

    def get_sun_times(self):
        seq = ('http://vm-koaserver5:50001/metrics_api?date=', self.utDate)
        res = url.urlopen(''.join(seq))
        suntimes = res.read().decode()
        suntimes = json.loads(res)
        rise = suntimes['dawn_12deg']
        sset = suntimes['dusk_12deg']
        risHr, risMin, risSec = rise.split(':')
        setHr, setMin, setSec = sset.split(':')
        self.sunrise = float(risHr)+float(risMin)/60.0+float(risSec)/3600.0
        self.sunset = float(setHr)+float(setMin)/60.0+float(setSec)/3600.0
        self.splitTime = (self.sunrise+self.sunset)/2.0

#------------------------------END GET SUN TIMES------------------------------------------------

    def get_prog_title(self, progid):
        seq = ('http://vm-koaserver5:50001/koa_api?cmd=getTitle&semid=', progid)
        res = url.urlopen(''.join(seq))
        title = res.read().decode()
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
        seq = (yr, '/', mo, '/', str(int(dy)-1))
        date = ''.join(seq)
        for key, val in self.fileList:
            if (self.fileList[key]['progpi'] != 'PROGPI'
                    and self.fileList[key]['progpi'] != 'NONE'
                    and self.fileList['progpi'] != ''):
                continue
            qry  = 'SELECT * FROM telsched WHERE Date="' + date + '" AND TelNr=2'
            crs = msc.mysql_conn().cursor(pms.cursors.DictCursor)
            crs.execute(qry)
            backup = crs.fetchone()

            if len(backup) != 1:
                return

            program = row['ProjCode'].split('/')

            if len(program) == 1:
                title = get_program(-1, program[0], row['Institution'], row['Principal'])
            else: # split night
                # Get sun times
                self.get_sun_times()
                nightLen = self.sunrise - self.sunset
                midNight = self.sunset + nightLen/2.0
                hr, mn, sc = self.utc.split(':')
                time = float(hr) + float(mn)/60.0 + float(sc)/3600.0
                if time < midNight:
                    num = 0
                else:
                    num = 1
                progid = program[num]
                title = get_program(num, progid, row['Institution'], row['Principal'])

            progid = backup['ProjCode'].strip()
            inst = backup['Institution'].strip()
            pi = backup['Principal'].strip()
            title = 

#--------------------------------------END BACKUP PROGRAM---------------------------------

    def get_program(self, num, progid, inst, pi):
        """
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
        pi = pi.replace(" ", '')

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

    def getProgInfo(utdate, instrument, stageDir):
        utdate = utdate.replace('/','-')
        instrument = instrument.upper()


