"""
"""

import os
import koa_db_conn as kdb

class ProgSplit:
    def __init__(self, ut_date, instr, stage_diri, lg):
        engineering = {'kcwieng':'outdir', 'kcwirun':'outdir', 
                'hireseng':'outdir','nspeceng':'outdir', 
                'nirc2eng':'outdir', 'engineering':'observer',
                'dmoseng':'outdir', 'lriseng':'outdir', 'esieng':'outdir',
                'keck ipdm':'observer', 'nirspec':'observer'}
        fileList = [{}]
        instrList = {'DEIMOS':2, 'ESI':2, 'HIRES':1, 
                'KCWI':2, 'LRIS':1, 'MOSFIRE':1, 
                'NIRC2':2, 'NIRSPEC':2, 'OSIRIS':1}
        instrument = instr
        numFiles = 0
        numSciencePI = 0
        too = {'_ToO_':'outdir'}
        observer = ''
        obsValues = []
        outdir = ''
        programs = [{}]
        semester = this.get_semester()
        splitTime = ''
        stageDir = stage_dir
        sunset = ''
        sunrise = ''
        utDate = ut_date
        log = lg

    def get_semester(self):
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
        if not os.path.isdir(self.stageDir):
            self.log.warning("progInfo - stage directory doesn't exist!")

    def check_instrument(self):
        if instrument not in instrList:
            self.log.warning('progInfo - unknown instrument!')
            print("Instrument must be one of: ")
            for item in instrList:
                print('\t' + item)

    def read_dep_obtain(self):
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
                            with db.cursor() as cursor:
                                cursor.execute(query)
                                if cursor.rowcount == 1:
                                    res = cursor.fetchone()


                    # Reset for the next file
                    num = 0
                    del row
                    row = {}

def getProgInfo(utdate, instrument, stageDir):
    utdate = utdate.replace('/','-')
    instrument = instrument.upper()


