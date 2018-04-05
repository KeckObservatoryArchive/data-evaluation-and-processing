"""
The parent class for all the instruments to streamline big picture things
Contains basic keyword values common across all the instruments
Children will contain the instrument specific values

12/14/2017 M. Brown - Created initial file
"""

#import datetime as dt
#import logging as lg
import os

class Instrument:
#    def __init__(self, endTime=dt.datetime.now(), rootDir):
    def __init__(self, rootDir):
        """
        Base Instrument class to hold all the values common between
        instruments. Contains default values where possible
        but null values should be replaced in the init of the 
        subclasses.

        @type endTime: string or datetime
        @param endTime: The date is a string if passed or datetime
            object if not passed
        @type rootDir: string
        @param rootDir: Working directory of the instrument
            Defaults to a null string
        """

        # Keyword values to be used with a FITS file during runtime
        self.rootDir = rootDir
        self.instrume = 'INSTRUME'
        self.utc = 'UTC'		# May be overwritten in instr_*.py
        self.dateObs = 'DATE-OBS'
        self.semester = 'SEMESTER'
        self.ofName = 'OUTFILE'		# May be overwritten in instr_*.py
        self.frameno = 'FRAMENO'	# May be overwritten in instr_*.py
        self.outdir = 'OUTDIR'
        self.ftype = 'INSTR'		# For instruments with two file types
        self.endTime = '20:00:00'	# 24 hour period start/end time (UT)
                                        # May be overwritten in instr_*.py

#        try: # Let's see if endTime was passed as a string
#            endTime = endTime.replace('-','')
#            endTime = endTime.replace('/','')
#            self.utDate = endTime[:8]
#            self.endHour = endTime[9:]
#            if self.endHour == '':
#                self.endHour = '20:00:00'
#        except TypeError: # It wasn't so it's a datetime object
#            self.utDate = endTime.strftime('%Y%m%d')
#            self.endHour = endTime.strftime('%H:%M:%S')

        # Values to be populated by subclass
        self.instr = ''
        self.prefix = ''
        self.rawfile = ''
        self.stageDir = ''
        self.ancDir = ''
        self.lev0 = ''
        self.lev1 = ''
        self.koaid = ''
        self.paths = []

        # Separate section for log init
#        self.log = set_logger()

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
            return '', False

        # Extract the UTC time and date observed from the header
        try:
            utc = keys[self.utc]
            dateobs = keys[self.dateObs]
        except KeyError:
            return '', False

        # Create a timedate object using the string from the header
        try:
            utc = datetime.strptime(utc, '%H:%M:%S.%f')
        except ValueError:
            return '', False

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
        koaid = ''.join(seq)
        return koaid, True

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

#    def set_logger(self):
#        """
#        Method to initialize the logger for each individual instrument. 
#        Log files will be created in their local directories 
#        as <instrument>Log.txt
#        """
#
#        # Get the user currently logged in
#        user = os.getlogin()
#        # Create a logger object with the user name
#        self.log = lg.getLogger(user)
#        self.log.setLevel(lg.INFO)
#        # Give the path to the log file. If directory exists but
#        # log does not, it will create the file. 
#        seq = (self.rootDir, '/', type(self).__name__, 'Log.txt')
#        fh = lg.FileHandler(''.join(seq))
#        fh.setLevel(lg.INFO)
#        # Create the format of the logged messages: 
#        # Time - Name - MessageLevel: Message
#        fmat = lg.Formatter('%(asctime)s - %(name)s - %(levelname)s: %(message)s')
#        fh.setFormatter(fmat)
#        self.log.addHandler(fh)

    def set_raw_fname(self, keys):
        """
        Determines the original filename from the keywords given

        @type keys: dictionary
        @param keys: contains the FITS file header information
        """
        # Get the root name of the file
        try:
            outfile = keys[self.ofName]
        except KeyError:
            return '', False
       
        # Get the frame number of the file
        try:
            frameno = keys[self.frameno]
        except KeyError:
            return '', False

        # Determine the necessary padding required
        zero = ''
        if float(frameno) < 10:
            zero = '000'
        elif 10 <= float(frameno) < 100:
            zero = '00'
        elif 100 <= float(frameno) < 1000:
            zero = '0'

        # Construct the original filename
        seq = (outfile.strip(), zero, str(frameno).strip(), '.fits')
        filename = ''.join(seq)
        return filename, True

