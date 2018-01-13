"""
"""

import os

class ProgSplit:
    def __init__(self, ut_date, instr, stage_diri, lg):
        engineering = {'kcwieng':'outdir', 'kcwirun':'outdir', 
                'hireseng':'outdir','nspeceng':'outdir', 
                'nirc2eng':'outdir', 'engineering':'observer',
                'dmoseng':'outdir', 'lriseng':'outdir', 'esieng':'outdir',
                'keck ipdm':'observer', 'nirspec':'observer'}
        fileList = []
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
            return

        save = ['utdate', 'oa','account', 'proginst', 'progpi', 'progid', 'observer']
        with open(readfile, 'r') as rfile:
            for line in rfile:
                vals = line.strip().split(' ')
                # check if progid is 'ENG'
                if vals[5] != 'ENG':
                    self.numSciencePI += 1
                row = {}
                for i in range(1, len(save)):
                    row[save[i]] = vals[i]
                programs.append(row)
                    

def getProgInfo(utdate, instrument, stageDir):
    utdate = utdate.replace('/','-')
    instrument = instrument.upper()


