"""
The parent class for all the instruments to streamline big picture things
Contains basic keyword values common across all the instruments
Children will contain the instrument specific values

12/14/2017 M. Brown - Created initial file
"""

#import datetime as dt
import os
from common import get_root_dirs, semester
from astropy.io import fits
from datetime import timedelta, datetime as dt
import shutil
import makejpg
import create_log as cl
from verification import *
import urllib.request
import json


class Instrument:
#    def __init__(self, endTime=dt.datetime.now(), rootDir):
    def __init__(self, instr, utDate, rootDir, log=None):
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

        #class inputs
        self.rootDir = rootDir
        self.instr = instr
        self.utDate = utDate
        self.log = log


        # Keyword values to be used with a FITS file during runtime
        #(NOTE: may be overwritten by instr-*.py)
        self.instrume = 'INSTRUME'
        self.utc = 'UTC'		# May be overwritten in instr_*.py
        self.dateObs = 'DATE-OBS'
        self.semester = 'SEMESTER'
        self.ofName = 'OUTFILE'		# May be overwritten in instr_*.py
        self.frameno = 'FRAMENO'	# May be overwritten in instr_*.py
        self.outdir = 'OUTDIR'
        self.ftype = 'INSTR'		# For instruments with two file types

        # Other values that be overwritten in instr-*.py
        self.endTime = '20:00:00'	# 24 hour period start/end time (UT)


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
        self.prefix = ''
        self.rawfile = ''
        self.koaid = ''
        self.sdataList = []


        #other helpful vars
        self.utDateDir = self.utDate.replace('/', '-').replace('-', '')


        # Verify input parameters
        verify_instrument(self.instr.upper())
        verify_date(self.utDate)
        assert os.path.isdir(self.rootDir), 'rootDir does not exist'



    def dep_init(self):
        '''
        Perform specific initialization tasks for DEP processing.
        '''

        #create log if it does nto exist
        if not self.log:
            self.log = cl.create_log(self.rootDir, self.instr, self.utDate, True)
            self.log.info('instrument.py: log created')


        #check and create dirs
        self.init_dirs()

       

    def init_dirs(self):

        # get the various root dirs
        self.dirs = get_root_dirs(self.rootDir, self.instr, self.utDate)


        # Create the directories, if they don't already exist
        for key, dir in self.dirs.items():
            self.log.info('instrument.py: using directory {}'.format(dir))
            if not os.path.isdir(dir):
                try:
                    os.makedirs(dir)
                except:
                    print('instrument.py: Could not create {}'.format(dir))


        # Additions for NIRSPEC
        # TODO: move this to instr_nirspec.py?
        if self.instr == 'NIRSPEC':
            os.mkdir(self.dirs['lev0'] + '/scam')
            os.mkdir(self.dirs['lev0'] + '/spec')




    def set_fits_file(self, filename):
        '''
        Sets the current FITS file we are working on.  Clears out temp fits variables.
        '''

        #todo: should we have option to just read the header for performance if that is all that is needed?
        self.fitsHdu = fits.open(filename)
        self.fitsHeader = self.fitsHdu[0].header
        #self.fitsHeader = fits.getheader(filename)
        self.fitsFilepath = filename


        self.koaid = '';
        self.rawfile = ''
        self.prefix = ''



    def set_koaid(self):
        '''
        Create and add KOAID to header if it does not already exist
        '''

        #skip if it exists
        if self.fitsHeader.get('KOAID') != None: return True

        #make it
        koaid, result = self.make_koaid(self.fitsHeader)
        if not result: return False

        #save it
        self.fitsHeader.update({'KOAID' : (koaid, 'KOA: Added missing keyword')})
        return True



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
            utc = dt.strptime(utc, '%H:%M:%S.%f')
        except ValueError:
            return '', False

        # Extract the hour, minute, and seconds from the UTC time
        hour = utc.hour
        minute = utc.minute
        second = utc.second

        # Calculate the total number of seconds since Midnight
        totalSeconds = ''.join((str(hour*3600), str(minute*60), str(second)))

        # Remove any date separators from the date
        dateobs = dateobs.replace('-','')
        dateobs = dateobs.replace('/','')

        # Create the KOAID from the parts
        koaid = ''.join((self.prefix, '.', dateobs, '.', totalSeconds.zfill(5), '.fits'))
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

 
    def check_instr(self):
        '''
        Check that value(s) in header indicates this is valid instrument and matches what we expect.
        (ported to python from check_instr.pro)
        #todo:  go over idl file again and pull out logic for other instruments
        #todo: use class key vals instead
        '''
        self.log.info('dqa: running check_instr for {}')


        ok = False
        keys = self.fitsHeader


        #get val
        #instrume = keys[self.instrume]
        instrume = keys.get('INSTRUME')
        if (instrume == None): instrume = keys.get('CURRINST')


        #direct match?
        if instrume:
            if (self.instr == instrume.strip()): ok = True


        #mira not ok
        outdir = keys.get('OUTDIR')
        if (outdir and '/mira' in outdir) : ok = False


        #No DCS keywords, check others
        if (not ok):
            filname = keys.get('FILNAME')
            if (filname and self.instr in filname): ok = True

            instrVal = self.instr.lower()
            outdir = keys.get(self.outdir)
            if (outdir and instrVal in outdir): ok = True


        #log err
        if (not ok):
            self.log.info('check_instr: Cannot determine if file is from ' + self.instr)


        return ok



    def set_dateObs(self):
        '''
        Checks to see if we have a date obsv keyword, and if it needs to be fixed or created.
        '''

        keys = self.fitsHeader
        filename = self.fitsFilepath


        #try to get from header
        dateObs = keys.get(self.dateObs)
        if dateObs: dateObs = dateObs.strip()


        #if empty or bad values then build from file last mod time
        #note: converting to universal time (+10 hours)
        if dateObs == None or 'Error' in dateObs or dateObs == '':
            lastMod = os.stat(filename).st_mtime
            dateObs = dt.fromtimestamp(lastMod) + timedelta(hours=10)
            dateObs = dateObs.strftime('%Y-%m-%d')
            keys.update({self.dateObs : (dateObs, 'KOA: Added missing keyword')})

        # Fix yy/mm/dd to yyyy-mm-dd
        if '-' not in dateObs:
            orig = dateObs
            yr, mo, dy = dateObs.split('/')
            dateObs = ''.join(('20', yr, '-', mo, '-', dy))
            keys.update({self.dateObs : (dateObs, 'KOA: value corrected (' + orig + ')')})


        #todo: can this check fail?
        return True
       


    def set_utc(self):
        '''
        Checks to see if we have a utc time keyword, and if it needs to be fixed or created.
        '''

        keys = self.fitsHeader
        filename = self.fitsFilepath
 
        #if empty or bad values then build from file last mod time
        #todo: make sure this is universal time
        utc = keys.get(self.utc)
        if utc == None or 'Error' in utc or utc == '':
            lastMod = os.stat(filename).st_mtime
            utc = dt.fromtimestamp(lastMod) + timedelta(hours=10)
            utc = utc.strftime('%H:%M:%S')
            keys.update({self.utc : (utc, 'KOA: Added missing keyword "UTC"')})

        return True



    def set_ut(self):

        keys = self.fitsHeader

        #skip if it exists
        if keys.get('UT') != None: return True

        #get utc from header
        utc = keys.get(self.utc)
        if (not utc): 
            self.log.error('Could not get UTC value.')
            return False

        #copy to UT
        keys.update({'UT' : (utc, 'KOA: Added missing keyword "UT"')})
        return True



    def get_outdir(self):
        '''
        Returns outdir if keyword exists, else derive from filename
        '''

        #return by keyword index if it exists
        keys = self.fitsHeader
        outdir = keys.get(self.outdir)
        if (outdir != None) : return outdir


        #Returns the OUTDIR associated with the filename, else returns None.
        #OUTDIR = [/s]/sdata####/account/YYYYmmmDD
        try:
            filename = self.fitsFilepath
            start = filename.find('/s')
            end = filename.rfind('/')
            return filename[start:end]
        except:
            #todo: really return "None"?
            return "None"



    def get_fileno(self):

        #todo: do we need this function instead of using keyword index?
        keys = self.fitsHeader

        fileno = keys.get('FILENUM')
        if (fileno == None): fileno = keys.get('FILENUM2')
        if (fileno == None): fileno = keys.get('FRAMENO')
        if (fileno == None): fileno = keys.get('IMGNUM')
        if (fileno == None): fileno = keys.get('FRAMENUM')

        return fileno


    def set_prog_info(self, progData):
        
        #note: progData is also stored in newproginfo.txt output from getProgInfo.py

        #find matching filename in array column 0
        baseFilename = os.path.basename(self.fitsFilepath)
        data = None
        for progFile in progData:
            filepath = progFile['file']
            if baseFilename in filepath:
                data = progFile
                break

        #return false if not found
        if not data: 
            return False

        #create keys
        keys = self.fitsHeader
        keys.update({'PROGID'  : (data['progid']  , 'KOA: Added keyword PROGID')})
        keys.update({'PROGINST': (data['proginst'], 'KOA: Added keyword PROGINST')})
        keys.update({'PROGPI'  : (data['progpi']  , 'KOA: Added keyword PROGPI')})
        keys.update({'PROGTITL': (data['progtitl'], 'KOA: Added keyword PROGTITL')})
        return True



    def set_semester(self):

        #TODO: move existing common.py semester() to Instrument?
        keys = self.fitsHeader        
        semester(keys)
        return True



    def set_propint(self):

        #create semid
        keys = self.fitsHeader
        semester = keys.get('SEMESTER')
        progid   = keys.get('PROGID')
        assert (semester != None and progid != None), 'set_propint: Could not find either SEMESTER or PROGID keyword.'
        semid = semester + '_' + progid


        #create url and get data
        url = self.koaUrl + 'cmd=getPP&semid=' +  semid + '&utdate=' + self.utDate
        data = urllib.request.urlopen(url).read().decode('utf8')
        data = json.loads(data)
        assert (data and len(data) > 0 and data[0]['propint']), 'set_proprint: Unable to set PROPINT keyword.'
        propint = int(data[0]['propint'])


        #update
        keys.update({'PROPINT' : (propint, 'KOA: Added missing keyword "PROPINT"')})
        return True



    def write_lev0_fits_file(self):

        #make sure we have a koaid
        keys = self.fitsHeader
        koaid = keys.get('KOAID')
        if (not koaid):
            self.log.error('write_lev0_fits_file: Could not find KOAID for output filename.')
            return False

        #build outfile path
        outfile = self.dirs['lev0']
        if   (koaid.startswith('NC')): outfile += '/scam'
        elif (koaid.startswith('NS')): outfile += '/spec'
        outfile += '/' + koaid


        #write out new fits file with altered header
        self.fitsHdu.writeto(outfile)
        return True



    def create_lev0_jpg(self):
    
        #make sure we have a koaid
        keys = self.fitsHeader
        koaid = keys.get('KOAID')
        if (not koaid):
            self.log.error('create_lev0_jpg: Could not find KOAID for output filename.')
            return False

        #build path to final fits file
        fitsfile = self.dirs['lev0']
        if   (koaid.startswith('NC')): fitsfile += '/scam'
        elif (koaid.startswith('NS')): fitsfile += '/spec'
        fitsfile += '/' + koaid

        #create jpg
        #todo: why does the old IDL code create jpgs to a tempdir first?
        makejpg.main(fitsfile, self.instr, self.dirs['lev0'] + '/')
        return True

