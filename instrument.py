"""
The parent class for all the instruments to streamline big picture things
Contains basic keyword values common across all the instruments
Children will contain the instrument specific values

12/14/2017 M. Brown - Created initial file
"""

import datetime as dt
import logging as lg
import os

class Instrument:
    def __init__(self, endTime=dt.datetime.now(), rDir=''):
        """
        Base Instrument class to hold all the values common between
        instruments. Contains default values where possible
        but null values should be replaced in the init of the 
        subclasses.
        """

        # Keyword values to be used with a FITS file during runtime
        self.rootDir = rDir
        self.instrume = 'INSTRUME'
        self.utc = 'UTC'
        self.dateObs = 'DATE'
        self.semester = 'SEMESTER'
        self.fileRoot = 'OUTFILE'        # Can be DATAFILE or ROOTNAME for specific instruments
        self.frameno = 'FRAMENO'     # Can be IMGNUM, FRAMENUM, FILENUM1, FILENUM2
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
        self.instr = ''
        self.prefix = ''
        self.origFile = ''
        self.stageDir = ''
        self.ancDir = ''
        self.koaid = ''
        self.paths = []
        self.keys = {}

        # Separate section for log init
        user = os.getlogin()
        self.log = lg.getLogger(user)
        self.log.setLevel(lg.INFO)
        fh = lg.FileHandler(self.rootDir + type(self).__name__ + 'Log.txt')
        fh.setLevel(lg.INFO)
        fmat = lg.Formatter('%(asctime)s - %(name)s - %(levelname)s: %(message)s')
        fh.setFormatter(fmat)
        self.log.addHandler(fh)

    def make_koaid(self, keys):
        """
        Function to create the KOAID for a given FITS file
        Returns the TRUE if the KOAID is successfully created
        and stored in the KOAID member variable

        @type keys: dictionary
        @param keys: The header for the given FITS file
        """
        # Get the prefix for the correct instrument and configuration
        # Note: set_prefix() is a subclass method
        self.prefix = self.set_prefix(keys)
        if self.prefix == '':
            return False

        # Extract the UTC time and date observed from the header
        try:
            utc = keys[self.utc]
            dateobs = keys[self.dateObs]
        except KeyError:
            return False

        # Create a timedate object using the string from the header
        try:
            utc = datetime.strptime(utc, '%H:%M:%S.%f')
        except ValueError:
            return False

        # Extract the hour, minute, and seconds from the UTC time
        hour = utc.hour
        minute = utc.minute
        second = utc.second

        # Calculate the total number of seconds since Midnight
        seq = (str(hour*3600), str(minute*60), str(second))
        totalSeconds = ''.join(seq)

        # Remove any date separators from the date
        dateobs = dateobs.replace('-','')
        dateobs = dateobs.replace('/','')

        # Create the KOAID from the parts
        seq = (self.prefix, '.', dateobs, '.', totalseconds.zfill(5), '.fits')
        self.koaid = ''.join(seq)
        return True

    def set_instr(self, keys):
        """
        Method to extract the name of the instrument from the INSTRUME keyword value
        """
        # Extract the Instrume value from the header as lowercase
        instr = keys[self.instrume].lower()

        # Split the value up into an array 
        instr = instr.split(' ')

        # The instrument name should always be the first value
        instr = instr[0].replace(':','')
        return instr
