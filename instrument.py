"""
The parent class for all the instruments to streamline big picture things
Contains basic keyword values common across all the instruments
Children will contain the instrument specific values

12/14/2017 M. Brown - Created initial file
"""

import datetime as dt

class Instrument:
    def __init__(self, endhr):
        """
        Keyword values to be used with a FITS file during runtime
        """
        self.utc = 'UTC'
        self.dateObs = 'DATE'
        self.semester = 'SEMESTER'
        self.fileRoot = 'OUTFILE'        # Can be DATAFILE or ROOTNAME for specific instruments
        self.frameno = 'FRAMENO'     # Can be IMGNUM, FRAMENUM, FILENUM1, FILENUM2
        self.koaid = 'KOAID'
        self.outdir = 'OUTDIR'
        self.ftype = 'INSTR'         # For instruments with two file types
        self.endHour = endhr
        self.currDate = dt.datetime.now()
        self.reducedDate = self.currDate.strftime('%Y%m%d')

        """
        Values to be populated by subclass
        """
        self.instr = ''
        self.prefix = ''
        self.origFile = ''
        self.stageDir = ''
        self.ancDir = ''
        self.paths = []
