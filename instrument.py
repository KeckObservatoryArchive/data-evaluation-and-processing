"""
The parent class for all the instruments to streamline big picture things
Contains basic keyword values common across all the instruments
Children will contain the instrument specific values

12/14/2017 M. Brown - Created initial file
"""

import datetime as dt

class Instrument:
    def __init__(self, endTime=dt.datetime.now()):
        """
        """

        # Keyword values to be used with a FITS file during runtime
        self.instr = 'INSTRUME'
        self.utc = 'UTC'
        self.dateObs = 'DATE'
        self.semester = 'SEMESTER'
        self.fileRoot = 'OUTFILE'        # Can be DATAFILE or ROOTNAME for specific instruments
        self.frameno = 'FRAMENO'     # Can be IMGNUM, FRAMENUM, FILENUM1, FILENUM2
        self.koaid = 'KOAID'
        self.outdir = 'OUTDIR'
        self.ftype = 'INSTR'         # For instruments with two file types
        try: # Let's see if endTime was passed as a string
            endTime = endTime.replace('-','')
            endTime = endTime.replace('/','')
            self.utDate = endTime[:8]
            self.endHour = endTime[9:]
            if self.endHour == '':
                self.endHour = '20:00:00'
        except TypeError: # It wasn't so it's a datetime object
            self.utDate = endTime.strftime('%Y%m%d')
            self.endHour = endTime.strftime('%H:%M:%S')

        # Values to be populated by subclass
        self.prefix = ''
        self.origFile = ''
        self.rootDir = ''
        self.stageDir = ''
        self.ancDir = ''
        self.paths = []
        self.keys = {}

    def koaid(self, keys):
        utc = keys[self.utc]
        dateobs = keys[self.dateObs]
        try:
            utc = datetime.strptime(utc, '%H:%M:%S.%f')
        except ValueError:
            raise ValueError

        hour = utc.hour
        minute = utc.minute
        second = utc.second

        totalSeconds = str((hour*3600) + (minute*60) + second)

        dateobs = dateobs.replace('-','')
        dateobs = dateobs.replace('/','')
        seq = (self.prefix, '.', dateobs, '.', totalseconds.zfill(5), '.fits')
        self.koaid = ''.join(seq)
        return True

    def set_instr(self, keys):
        instr = keys[self.instr].lower()
        instr = instr.split(' ')
        instr = instr[0].replace(':','')
        return instr
