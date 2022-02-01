"""
The parent class for all the instruments to streamline big picture things
Contains basic keyword values common across all the instruments
Children will contain the instrument specific values

12/14/2017 M. Brown - Created initial file
"""

#import datetime as dt
import os
from common import *
from astropy.io import fits
from datetime import timedelta, datetime as dt
from envlog import *
import shutil
import create_log as cl
from verification import *
import urllib.request
import json
import numpy as np
import re
from dep_obtain import get_obtain_data
import math
import db_conn

import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
from astropy.visualization import ZScaleInterval, AsinhStretch
from astropy.visualization.mpl_normalize import ImageNormalize


class Instrument:
    def __init__(self, instr, utDate, config, log=None):
        """
        Base Instrument class to hold all the values common between
        instruments. Contains default values where possible
        but null values should be replaced in the init of the 
        subclasses.

        @param instr: instrument name
        @type instr: string
        @param utDate: UT date of observation
        @type utDate: string (YYYY-MM-DD)
        @param config: config object containing configration variables
        @type config: config object
        @type log: Logger Object
        @param log: The log handler for the script. Writes to the logfile
        """

        #class inputs
        self.instr    = instr
        self.utDate   = utDate
        self.config   = config
        self.log      = log


        # Keyword values to be used with a FITS file during runtime
        # NOTE: array may be used to denote an ordered list of possible keywords to look for.
        # NOTE: these may be overwritten by instr_*.py
        self.keywordMap = {}
        self.keywordMap['INSTRUME']     = 'INSTRUME'
        self.keywordMap['UTC']          = 'UTC'
        self.keywordMap['DATE-OBS']     = 'DATE-OBS'
        self.keywordMap['SEMESTER']     = 'SEMESTER'
        self.keywordMap['OFNAME']       = 'OUTFILE'
        self.keywordMap['FRAMENO']      = 'FRAMENO'
        self.keywordMap['OUTDIR']       = 'OUTDIR'
        self.keywordMap['FTYPE']        = 'INSTR'       # For instruments with two file types


        # Other values that can be overwritten in instr-*.py
        self.endHour = '20:00:00'   # 24 hour period start/end time (UT)


        # Values to be populated by subclass
        self.prefix         = ''
        self.rawfile        = ''
        self.koaid          = ''
        self.sdataList      = []
        self.extraMeta      = {}
        self.keywordSkips   = []

        #init fits specific vars
        self.fitsHdu        = None
        self.fitsHeader     = None
        self.fitsFilepath   = None


        #other helpful vars
        self.rootDir = self.config[self.instr]['ROOTDIR']
        if self.rootDir.endswith('/'): self.rootDir = self.rootDir[:-1]
        self.utDateDir = self.utDate.replace('/', '-').replace('-', '')


        # Verify input parameters
        verify_instrument(self.instr.upper())
        verify_date(self.utDate)
        assert os.path.isdir(self.rootDir), 'rootDir does not exist'

        #create db conn obj
        self.db = db_conn.db_conn('config.live.ini', configKey='DATABASE', persist=True)


    def __del__(self):
        """
        Close the database connection, if it is open
        """
        if self.db:
            self.db.close()


    #abstract methods that must be implemented by inheriting classes
    def get_dir_list(self) : raise NotImplementedError("Abstract method not implemented!")
    def get_prefix(self)   : raise NotImplementedError("Abstract method not implemented!")
    def set_koaimtyp(self) : raise NotImplementedError("Abstract method not implemented!")


    def dep_init(self, fullRun=True):
        '''
        Perform specific initialization tasks for DEP processing.
        '''

        #TODO: exit if existence of output/stage dirs? Maybe put override in config?
        

        #store config
        self.telUrl = self.config['API']['TELAPI']
        self.metadataTablesDir = self.config['MISC']['METADATA_TABLES_DIR']


        #check and create dirs
        self.init_dirs(fullRun)


        #create log if it does not exist
        if not self.log:
            self.log = cl.create_log(self.rootDir, self.instr, self.utDate, True)
            self.log.info('instrument.py: log created')


        #create README (output dir with everything before /koadata##/... stripped off)
        readmeFile = self.dirs['output'] + '/README';
        with open(readmeFile, 'w') as f:
            path = self.dirs['output']
            # match = re.search( r'.*(/.*/.*/\d\d\d\d\d\d\d\d)$', path, re.M)
            # if match: path = match.groups(0)[0]
            f.write(path + '\n')


    def init_dirs(self, fullRun=True):

        # get the various root dirs
        self.dirs = get_root_dirs(self.rootDir, self.instr, self.utDate)


        # Create the output directories, if they don't already exist.
        # Unless this is a full pyDEP run, in which case we exit with warning
        for key, dir in self.dirs.items():
            if os.path.isdir(dir):
                if fullRun and key != 'process':
                    raise Exception('instrument.py: Full pyDEP run, but staging and/or output directories already exist')
            else:
                try:
                    os.makedirs(dir)
                except:
                    raise Exception('instrument.py: could not create directory: {}'.format(dir))


        # Additions for NIRSPEC
        # TODO: move this to instr_nirspec.py?
        if self.instr == 'NIRSPEC':
            for dir in ['scam', 'spec']:
                newdir = self.dirs['lev0'] + '/' + dir
                if not os.path.isdir(newdir):
                    os.mkdir(newdir)



    def set_fits_file(self, filename):
        '''
        Sets the current FITS file we are working on.  Clears out temp fits variables.
        '''

        #todo: should we have option to just read the header for performance if that is all that is needed?
        try:
            self.fitsHdu = fits.open(filename, ignore_missing_end=True)
            self.fitsHeader = self.fitsHdu[0].header
            # print('hdu0',type(self.fitsHeader
            # print('hdu1',type(self.fitsHdu[1]))
            #self.fitsHeader = fits.getheader(filename)
            self.fitsFilepath = filename
        except:
            self.log.warning('set_fits_file: Could not read FITS file "' + filename + '"!')
            return False

        self.koaid = '';
        self.rawfile = ''
        self.prefix = ''
        self.extraMeta = {}

        return True

    def get_keyword(self, keyword, useMap=True, default=None, ext=None):
        '''
        Gets keyword value from the FITS header as defined in keywordMap class variable.  
        NOTE: FITS file must be loaded first with self.set_fits_file

        @param keyword: keyword value or ordered list of keyword values to search for
        @type instr: string or list
        '''
        # check for loaded fitsHeader
        if ext == None:
            if not self.fitsHeader:
                 raise Exception('get_keyword: ERROR: no FITS header loaded')
                 return default
        else:
             if not self.fitsHdu[ext].header:
                 raise Exception('get_keyword: ERROR: no FITS header loaded')
                 return default
        #use keyword mapping?
        if useMap:
    
            #if keyword is mapped, then use mapped value(s)        
            if isinstance(keyword, str) and keyword in self.keywordMap:
                keyword = self.keywordMap[keyword]

        #We allow an array of mapped keys, so if keyword is still a string then put in array
        mappedKeys = keyword
        if isinstance(mappedKeys, str):
            mappedKeys = [mappedKeys]

        #loop
        if ext == None:
            fitshead = self.fitsHeader
        else:
            fitshead = self.fitsHdu[ext]

        for mappedKey in mappedKeys:
            try:
                val = fitshead.get(mappedKey)
                if self._chk_valid(val):
                    return val
            except fits.verify.VerifyError:
                continue

        return default

    @staticmethod
    def _chk_valid(val):
        if val == 0:
            return True

        if (not val or isinstance(val, fits.Undefined) or
                str(val).strip().lower() in ('nan', '-nan')):
            return False

        return True


    def set_keyword(self, keyword, value, comment='', useMap=False, ext=None):
        '''
        Sets keyword value in FITS header.
        NOTE: Mapped values are only used if "useMap" is set to True, otherwise keyword name is as provided.
        NOTE: FITS file must be loaded first with self.set_fits_file
        '''

        # check for loaded fitsHeader
        if not self.fitsHeader:
             raise Exception('get_keyword: ERROR: no FITS header loaded')
             return None

        #use keyword mapping?
        if useMap:
            #NOTE: We allow an array of mapped keys, so if keyword is array, then use first value
            if keyword in self.keywordMap:
                keyword = self.keywordMap[keyword]

        #NOTE: If keyword is mapped to an array of key values, the first value will be used.
        if isinstance(keyword, list):
            keyword = keyword[0]

        #handle infinite value
        if value == math.inf:
            self.log.error(f'set_keyword: ERROR: keyword {keyword} value is infinite.  Setting to null.')
            return None

        #ok now we can update
        if ext == None:
            self.fitsHeader.update({keyword : (value, comment)})
        else:
            (self.fitsHdu[ext].header).update({keyword : (value, comment)})


    def is_fits_valid(self):
        '''
        Basic checks that the fits file is valid.
        '''

        #check no data
        if len(self.fitsHdu) == 0:
            self.log.error('is_fits_valid: No HDUs.')
            return False

        #any corrupted HDUs?
        for hdu in self.fitsHdu:
            hdu_type = str(type(hdu))
            if 'CorruptedHDU' in hdu_type:
                self.log.error('is_fits_valid: Corrupted HDU found.')
                return False

        return True


    def set_koaid(self):
        '''
        Create and add KOAID to header if it does not already exist
        '''

        # self.log.info('set_koaid: setting KOAID keyword value')

        #skip if it exists
        if self.get_keyword('KOAID', False) != None: return True

        #make it
        koaid, result = self.make_koaid()
        if not result: 
            self.log.warning('set_koaid: Could not create KOAID.  UDF!')
            return False

        #save it
        self.set_keyword('KOAID', koaid, 'KOA: Data file name')
        return True



    def make_koaid(self):
        """
        Function to create the KOAID for the current loaded FITS file
        Returns the koaid and TRUE if the KOAID is successfully created
        """

        #TODO: see old/common.koaid() and make sure all logic is moved here or to instr_*.py

        # Get the prefix for the correct instrument and configuration
        self.prefix = self.get_prefix()
        if self.prefix == '':
            return '', False

        # Extract the UTC time and date observed from the header
        utc = self.get_keyword('UTC', False)
        if utc == None: return '', False

        dateobs = self.get_keyword('DATE-OBS')
        if dateobs == None: return '', False

        # Create a timedate object using the string from the header
        try:
            utc = dt.strptime(utc, '%H:%M:%S.%f')
        except:
            return '', False

        # Extract the hour, minute, and seconds from the UTC time
        hour   = utc.hour
        minute = utc.minute
        second = utc.second

        # Calculate the total number of seconds since Midnight
        totalSeconds = str((hour * 3600) + (minute * 60) + second)

        # Remove any date separators from the date
        dateobs = dateobs.replace('-','')
        dateobs = dateobs.replace('/','')

        # Create the KOAID from the parts
        koaid = self.prefix + '.' + dateobs + '.' + totalSeconds.zfill(5) + '.fits'
        return koaid, True


    def get_instr(self):
        """
        Method to extract the name of the instrument from the INSTRUME keyword value
        """

        # Extract the Instrume value from the header as lowercase
        instr = self.get_keyword('INSTRUME')
        if (instr == None) : return ''
        instr = instr.lower()

        # Split the value up into an array 
        instr = instr.split(' ')

        # The instrument name should always be the first value
        instr = instr[0].replace(':','')
        return instr


    def get_raw_fname(self):
        """
        Determines the original filename
        """

        #todo: is this function needed?

        # Get the root name of the file
        outfile = self.get_keyword('OFNAME')
        if outfile == None: return '', False

        # Get the frame number of the file
        frameno = self.get_keyword('FRAMENO')
        if frameno == None: return '', False

        # Determine the necessary padding required
        zero = ''
        if         float(frameno) < 10:   zero = '000'
        elif 10 <= float(frameno) < 100:  zero = '00'
        elif 100 <= float(frameno)< 1000: zero = '0'

        # Construct the original filename
        filename = outfile.strip() + zero + str(frameno).strip() + '.fits'
        return filename, True

 
    def set_instr(self):
        '''
        Check that value(s) in header indicates this is valid instrument and fixes if needed.
        (ported to python from check_instr.pro)
        '''
        #todo:  go over idl file again and pull out logic for other instruments

        #self.log.info('set_instr: verifying this is a ' + self.instr + ' FITS file')

        ok = False

        #direct match (or starts with match)?
        instrume = self.get_keyword('INSTRUME')
        if instrume and instrume.startswith(self.instr):
            if instrume != self.instr:
                self.set_keyword('INSTRUME', self.instr, 'KOA: Instrument')
            ok = True

        #mira not ok
        outdir = self.get_keyword('OUTDIR')
        if (outdir and '/mira' in outdir) : ok = False

        #No DCS keywords, check others
        if (not ok):
            filname = self.get_keyword('FILNAME')
            if (filname and self.instr in filname): ok = True

            outdir = self.get_keyword('OUTDIR')
            if (outdir and self.instr in outdir.upper()): ok = True
            if (outdir and 'sdata100' in outdir and outdir.endswith('fcs')): ok = True
            currinst = self.get_keyword('CURRINST')
            if (currinst and self.instr == currinst): ok = True

            #if fixed, then update 'INSTRUME' in header
            if ok:
                self.set_keyword('INSTRUME', self.instr, 'KOA: Fixing INSTRUME keyword')
                self.log.info('set_instr: fixing INSTRUME value')

        #log err
        if (not ok):
            self.log.warning('set_instr: cannot determine if file is from ' + self.instr + '.  UDF!')

        return ok



    def set_dateObs(self):
        '''
        Checks to see if we have a DATE-OBS keyword, and if it needs to be fixed or created.
        '''

        #try to get from header (unmapped or mapped)
        dateObs = self.get_keyword('DATE-OBS', False)
        if dateObs == None: dateObs = self.get_keyword('DATE-OBS')

        #validate
        valid = False
        if dateObs: 
            dateObs = str(dateObs) #NOTE: sometimes we can get a number
            dateObs = dateObs.strip()
            valid = re.search('^\d\d\d\d[-]\d\d[-]\d\d', dateObs)

            #fix slashes?
            if not valid and '/' in dateObs:
                orig = dateObs
                day, month, year = dateObs.split('/')
                if int(year)<50: year = '20' + year
                else:            year = '19' + year
                dateObs = year + '-' + month + '-' + day
                self.set_keyword('DATE-OBS', dateObs, 'KOA: Value corrected (' + orig + ')')
                self.log.warning('set_dateObs: fixed DATE-OBS format (orig: ' + orig + ')')
                valid = True

        #if we couldn't match valid pattern, then build from file last mod time
        #note: converting to universal time (+10 hours)
        if not valid:
            filename = self.fitsFilepath
            lastMod = os.stat(filename).st_mtime
            dateObs = dt.fromtimestamp(lastMod) + timedelta(hours=10)
            dateObs = dateObs.strftime('%Y-%m-%d')
            self.set_keyword('DATE-OBS', dateObs, 'KOA: Observing date')
            self.log.warning('set_dateObs: set DATE-OBS value from FITS file time')

        # If good match, just take first 10 chars (some dates have 'T' format and extra time)
        if len(dateObs) > 10:
            orig = dateObs
            dateObs = dateObs[0:10]
            self.set_keyword('DATE-OBS', dateObs, 'KOA: Value corrected (' + orig + ')')
            self.log.warning('set_dateObs: fixed DATE-OBS format (orig: ' + orig + ')')

        return True
       


    def set_utc(self):
        '''
        Checks to see if we have a UTC time keyword, and if it needs to be fixed or created.
        '''

        #try to get from header unmapped and mark if update needed
        update = False
        utc = self.get_keyword('UTC', False)
        if utc == None: update = True

        #try to get from header mapped
        if utc == None:
            utc = self.get_keyword('UTC')
        #validate
        valid = False
        if utc: 
            utc = str(utc) #NOTE: sometimes we can get a number
            utc = utc.strip()
            valid = re.search('^\d\d:\d\d:\d\d.\d\d', utc)

        #if we couldn't match valid pattern, then build from file last mod time
        #note: converting to universal time (+10 hours)
        if not valid:
            filename = self.fitsFilepath
            lastMod = os.stat(filename).st_mtime
            utc = dt.fromtimestamp(lastMod) + timedelta(hours=10)
            utc = utc.strftime('%H:%M:%S.00')
            update = True
            self.log.warning(f'set_utc: set UTC value from FITS file time ({utc})')
        #update/add if need be
        if update:
            self.set_keyword('UTC', utc, 'KOA: UTC keyword corrected')
        return True



    def set_ut(self):

        #skip if it exists
        if self.get_keyword('UT', False) != None: return True

        #get utc from header
        utc = self.get_keyword('UTC', False)
        if utc == None: 
            self.log.warning('set_ut: Could not get UTC value.  UDF!')
            return False

        #copy to UT
        self.set_keyword('UT', utc, 'KOA: Observing time')
        return True



    def get_outdir(self):
        '''
        Returns outdir if keyword exists, else derive from filename
        '''

        #return by keyword index if it exists
        outdir = self.get_keyword('OUTDIR')
        if (outdir != None) : return outdir

        #Returns the OUTDIR associated with the filename, else returns None.
        #OUTDIR = [/s]/sdata####/account/YYYYmmmDD
        #todo: should we look for '/s/' and subtract one from index?
        #NOTE: for reprocessing old data that doesn't have OUTDIR keyword, this matches
        #on /stage/ or /storageserver/ instead of /s/, which still gets the job done.  not ideal.
        try:
            filename = self.fitsFilepath
            start = filename.find('/s')
            end = filename.rfind('/')
            return filename[start:end]
        except:
            #todo: really return "None"?
            return "None"



    def get_fileno(self):

        #todo: do we need this function instead of using keyword mapping?  see subclass set_frameno
        keys = self.fitsHeader

        fileno = keys.get('FILENUM')
        if (fileno == None): fileno = keys.get('FILENUM2')
        if (fileno == None): fileno = keys.get('FRAMENO')
        if (fileno == None): fileno = keys.get('IMGNUM')
        if (fileno == None): fileno = keys.get('FRAMENUM')

        return fileno


    def set_prog_info(self, progData):
        
        # self.log.info('set_prog_info: setting program information keywords')

        #note: progData is also stored in newproginfo.txt output from getProgInfo.py

        #find matching filename in array 
        dataKey = None
        data = None
        for key, progFile in enumerate(progData):
            filepath = progFile['file']
            if filepath in self.fitsFilepath:
                dataKey = key
                data = progFile
                break
        if data == None: 
            self.log.error('set_prog_info: Could not get program info.  UDF!')
            return False

        #create keywords, deal with blank/undefined vals
        assert 'progid'   in data and data['progid'],   'PROGID not found.'
        assert 'progpi'   in data and data['progpi'],   'PROGPI not found.'
        assert 'proginst' in data and data['proginst'], 'PROGINST not found.'
        assert 'progtitl' in data and data['progtitl'], 'PROGTITL not found.'

        if data['progid']   == 'PROGID'  : data['progid']   = 'NONE'
        if data['progpi']   == 'PROGPI'  : data['progpi']   = 'NONE'
        if data['proginst'] == 'PROGINST': data['proginst'] = 'NONE'
        if data['progtitl'] in ('PROGTITL', 'NONE'): data['progtitl'] = ''

        self.set_keyword('PROGID'  , data['progid']  , 'KOA: Program ID')
        self.set_keyword('PROGPI'  , data['progpi']  , 'KOA: Program principal investigator')
        self.set_keyword('PROGINST', data['proginst'], 'KOA: Program institution')

        #extra warning for log
        if data['progid'] == 'NONE':
            time = self.get_keyword('DATE-OBS') + ' ' + self.get_keyword('UTC')
            self.log.info(f"set_prog_info: PROGID is NONE for {os.path.basename(self.fitsFilepath)} (@{time})")

        #enocde unicode chars in progtitl
        title = data['progtitl']
        title = title.encode('ascii', errors='xmlcharrefreplace').decode('utf8')
        #divide PROGTITL into length 50 (+20 for comments) chunks PROGTL1/2/3
        progtl1 = title[0:50]
        progtl2 = title[50:100]
        progtl3 = title[100:150]
        self.set_keyword('PROGTL1',  progtl1, 'Program title 1')
        self.set_keyword('PROGTL2',  progtl2, 'Program title 2')
        self.set_keyword('PROGTL3',  progtl3, 'Program title 3')


        #NOTE: PROGTITL goes in metadata but not in header so we store in temp dict for later
        self.extraMeta['PROGTITL'] = title
        
        return True



    def set_semester(self):
        """
        Determines the Keck observing semester from the DATE-OBS keyword in header
        and updates the SEMESTER keyword in header.

        semester('2017-08-01') --> 2017A
        semester('2017-08-02') --> 2017B

        A = Feb. 2 to Aug. 1 (UT)
        B = Aug. 2 to Feb. 1 (UT)
        """

        #special override via command line option
        assign_progname = self.config.get('MISC', {}).get('ASSIGN_PROGNAME')
        if assign_progname:
            utc = self.get_keyword('UTC', False)
            progname = get_progid_assign(assign_progname, utc)
            if '_' in progname and is_progid_valid(progname):
                semester, progid = progname.split('_')
                self.set_keyword('SEMESTER', semester, 'Calculated SEMESTER from PROGNAME')
                self.log.info(f"set_semester: Set SEMESTER to '{semester}' from ASSIGN_PROGNAME '{progname}'")
                return True

        #special override assign using PROGNAME
        progname = self.get_keyword('PROGNAME', default='')
        if '_' in progname and is_progid_valid(progname):
            semester, progid = progname.split('_')
            self.set_keyword('SEMESTER', semester, 'Calculated SEMESTER from PROGNAME')
            self.log.info(f"set_semester: Set SEMESTER to '{semester}' from PROGNAME '{progname}'")
            return True

        #normal assign using DATE-OBS and UTC
        else:
            dateObs = self.get_keyword('DATE-OBS', False)
            utc     = self.get_keyword('UTC', False)
            if not dateObs or not utc:
                self.log.error('set_semester: Could not parse DATE-OBS and UTC')
                return False

            #Slightly unintuitive, but get utc datetime obj and subtract 10 hours to convert to HST
            #and another 10 for 10 am cutoff as considered next days observing.
            d = dt.strptime(dateObs+' '+utc, "%Y-%m-%d %H:%M:%S.%f")
            d = d - timedelta(hours=20)

            #define cutoffs and see where it lands
            #NOTE: d.year is wrong when date is Jan 1 and < 20:00:00, 
            #but it doesn't matter since we assume 'B' which is correct for Jan1 
            semA = dt.strptime(f'{d.year}-02-01 00:00:00.00', "%Y-%m-%d %H:%M:%S.%f")
            semB = dt.strptime(f'{d.year}-08-01 00:00:00.00', "%Y-%m-%d %H:%M:%S.%f")
            sem = 'B'
            if d >= semA and d < semB: sem = 'A'

            #adjust year if january
            year = d.year
            if d.month == 1: year -= 1

            semester = f'{year}{sem}'
            self.set_keyword('SEMESTER', semester, 'Calculated SEMESTER from DATE-OBS')

            return True



    def set_propint(self, progData):
        '''
        Set proprietary period length.
        NOTE: This must come after set_semester() is called
        '''

        # self.log.info('set_propint: determining PROPINT value')

        #create semid
        semid = self.get_semid()
        assert (semid != None), 'set_propint: Could not create SEMID.'


        # Default to 18 for ENG data (***verify with SAs***)
        progid = self.fitsHeader.get('PROGID').upper()
        if progid == 'ENG':
            propint = 18
        else:
            #create url and get data
#todo: test this
            query = f'select propmin from koa_ppp where semid="{semid}" and utdate="{self.utDate}"'
            data = self.db.query('koa', query, getOne=True)
            if not data:
                self.log.info('set_propint: PROPINT not found for ' + semid + ' and ' + self.utDate + ', defaulting to 18 months')
                propint = 18
            else:
                propint = int(data['propmin'])

        #NOTE: PROPINT goes in metadata but not in header so we store in temp dict for later
        self.extraMeta['PROPINT'] = propint

        return True


    def set_datlevel(self, datlevel):
        '''
        Adds "DATLEVEL" keyword to header
        '''
        self.set_keyword('DATLEVEL' , datlevel, 'KOA: Data reduction level')
        return True


    def set_dqa_date(self):
        """
        Adds date timestamp for when the DQA module was run
        """
        dqa_date = dt.strftime(dt.now(), '%Y-%m-%dT%H:%M:%S')
        self.set_keyword('DQA_DATE', dqa_date, 'KOA: Data quality assess time')
        return True


    def set_dqa_vers(self):
        '''
        Adds DQA version keyword to header
        '''
        version = self.config['INFO']['DEP_VERSION']
        self.set_keyword('DQA_VERS', version, 'KOA: Data quality assess code version')
        return True


    def set_image_stats_keywords(self):
        '''
        Adds mean, median, std keywords to header
        '''

        # self.log.info('set_image_stats_keywords: setting image statistics keyword values')

        image = self.fitsHdu[0].data     
        imageStd    = float("%0.2f" % np.std(image))
        imageMean   = float("%0.2f" % np.mean(image))
        imageMedian = float("%0.2f" % np.median(image))

        self.set_keyword('IMAGEMN' ,  imageMean,   'KOA: Image data mean')
        self.set_keyword('IMAGESD' ,  imageStd,    'KOA: Image data standard deviation')
        self.set_keyword('IMAGEMD' ,  imageMedian, 'KOA: Image data median')

        return True


    def set_npixsat(self, satVal=None, ext=0):
        '''
        Determines number of saturated pixels and adds NPIXSAT to header
        '''

        # self.log.info('set_npixsat: setting pixel saturation keyword value')

        if satVal == None:
            satVal = self.get_keyword('SATURATE')
            
        if satVal == None:
            self.log.warning("set_npixsat: Could not find SATURATE keyword")
        else:
            image = self.fitsHdu[ext].data     
            pixSat = image[np.where(image >= satVal)]
            nPixSat = len(image[np.where(image >= satVal)])
            self.set_keyword('NPIXSAT', nPixSat, 'KOA: Number of saturated pixels',ext=ext)

        return True


    def set_oa(self):
        '''
        Adds observing assistant name to header
        '''

        # Get OA from dep_obtain file
        obFile = self.dirs['stage'] + '/dep_obtain' + self.instr + '.txt'
        obData = get_obtain_data(obFile)
        oa = None
        if len(obData) >= 1: oa = obData[0]['OA']

        if oa == None:
            self.log.warning("set_oa: Could not find OA data")
        else:
            self.set_keyword('OA', oa, 'KOA: Observing Assistant name')

        return True


    def set_ofName(self):
        """
        Adds OFNAME keyword to header 
        """

        # self.log.info('set_ofName: setting OFNAME keyword value')

        #get value
        ofName = self.get_keyword('OFNAME')
        if (ofName == None): 
            self.log.error('set_ofName: cannot find value for OFNAME')
            return False

        #add *.fits to output if it does not exist (to fix old files)
        if (ofName.endswith('.fits') == False) : ofName += '.fits'

        #update
        self.set_keyword('OFNAME', ofName, 'KOA: Original file name')
        return True


    def set_weather_keywords(self):
        '''
        Adds all weather related keywords to header.
        NOTE: DEP should not exit if weather files are not found
        '''

        # self.log.info('set_weather_keywords: setting weather keyword values')

        #get input vars
        dateobs = self.get_keyword('DATE-OBS')
        utc     = self.get_keyword('UTC', False)
        telnr   = self.get_telnr()

        #get data but continue even if there were errors for certain keywords
        data, errors, warns = envlog(telnr, dateobs, utc)
        if type(data) is not dict: 
            self.log.error(f"Could not get weather data for {dateobs} {utc}")
            return True
        if len(errors) > 0:
            self.log.error(f"EPICS archiver error for {dateobs} {utc}: {str(errors)}")
        if len(warns) > 0:
            self.log.info(f"EPICS archiver warn {dateobs} {utc}: {str(warns)}")

        #set keywords
        self.set_keyword('WXDOMHUM' , data['wx_domhum'],    'KOA: Weather dome humidity')
        self.set_keyword('WXDOMTMP' , data['wx_domtmp'],    'KOA: Weather dome temperature')
        self.set_keyword('WXDWPT'   , data['wx_dewpoint'],  'KOA: Weather dewpoint')
        self.set_keyword('WXOUTHUM' , data['wx_outhum'],    'KOA: Weather outside humidity')
        self.set_keyword('WXOUTTMP' , data['wx_outtmp'],    'KOA: Weather outside temperature')
        self.set_keyword('WXPRESS'  , data['wx_pressure'],  'KOA: Weather pressure')
        self.set_keyword('WXWNDIR'  , data['wx_winddir'],   'KOA: Weather wind direction')
        self.set_keyword('WXWNDSP'  , data['wx_windspeed'], 'KOA: Weather wind speed')
        self.set_keyword('WXTIME'   , data['wx_time'],      'KOA: Weather measurement time')
        self.set_keyword('GUIDFWHM' , data['guidfwhm'],     'KOA: Guide star FWHM value')
        self.set_keyword('GUIDTIME' , data['fwhm_time'],    'KOA: Guide star FWHM measure time')
        return True


    def get_telnr(self):
        '''
        Gets telescope number for instrument via API
        #todo: store this and skip api call if exists?  Would need to clear var on fits reload.
        #todo: Replace API call with hard-coded?
        '''

        url = self.telUrl + 'cmd=getTelnr&instr=' + self.instr.upper()
        data = get_api_data(url, getOne=True)
        telNr = int(data['TelNr'])
        assert telNr in [1, 2], 'telNr "' + telNr + '"" not allowed'
        return telNr


    def write_lev0_fits_file(self):

        #make sure we have a koaid
        koaid = self.get_keyword('KOAID')
        if (not koaid):
            self.log.error('write_lev0_fits_file: Could not find KOAID for output filename.')
            return False

        #build outfile path
        outfile = self.dirs['lev0']
        if   (koaid.startswith('NC')): outfile += '/scam'
        elif (koaid.startswith('NS')): outfile += '/spec'
        outfile += '/' + koaid

        # already exists?
        if os.path.isfile(outfile):
            self.log.error('write_lev0_fits_file: file already exists.  Duplicate KOAID?')
            return False

        #write out new fits file with altered header
        try:
            self.fitsHdu.writeto(outfile)
            self.log.info('write_lev0_fits_file: output file is ' + outfile)
        except:
            try:
                self.fitsHdu.writeto(outfile, output_verify='ignore')
                self.log.info('write_lev0_fits_file: Forced to write FITS using output_verify="ignore". May want to inspect:' + outfile)                
            except Exception as e:
                self.log.error('write_lev0_fits_file: Could not write out lev0 FITS file to ' + outfile)
                self.log.info(str(e))
                #If it someone still wrote something out, remove it
                if os.path.isfile(outfile):
                    os.remove(outfile)
                return False

        self.set_filesize(outfile)

        return True


    def make_jpg(self):
        '''
        Make the jpg(s) for current fits file
        '''

        # Find fits file in lev0 dir to convert based on koaid
        koaid = self.fitsHeader.get('KOAID')
        fits_filepath = ''
        for root, dirs, files in os.walk(self.dirs['lev0']):
            if koaid in files:
                fits_filepath = f'{root}/{koaid}'
        if not fits_filepath:
            self.log.error(f'make_jpg: Could not find KOAID: {koaid}')
            return False
        outdir = os.path.dirname(fits_filepath)

        #call instrument specific create_jpg function
        try:
            self.log.info(f'make_jpg: Creating jpg from: {fits_filepath}')
            self.create_jpg_from_fits(fits_filepath, outdir)
        except Exception as e:
            self.log.error(f'make_jpg: Could not create JPG from: {fits_filepath}')
            self.log.error(e)
            return False

        return True


    def create_jpg_from_fits(self, fits_filepath, outdir):
        '''
        Basic convert fits primary data to jpg.  Instrument subclasses can override this function.
        '''

        #get image data
        hdu = fits.open(fits_filepath, ignore_missing_end=True)
        data = hdu[0].data
        hdr  = hdu[0].header

        #form filepaths
        basename = os.path.basename(fits_filepath).replace('.fits', '')
        jpg_filepath = f'{outdir}/{basename}.jpg'

        #create jpg
        interval = ZScaleInterval()
        vmin, vmax = interval.get_limits(data)
        norm = ImageNormalize(vmin=vmin, vmax=vmax, stretch=AsinhStretch())
        dpi = 100
        width_inches  = hdr['NAXIS1'] / dpi
        height_inches = hdr['NAXIS2'] / dpi
        fig = plt.figure(figsize=(width_inches, height_inches), frameon=False, dpi=dpi)
        ax = fig.add_axes([0, 0, 1, 1]) #this forces no border padding
        plt.axis('off')
        plt.imshow(data, cmap='gray', origin='lower', norm=norm)
        plt.savefig(jpg_filepath, quality=92)
        plt.close()


    def get_semid(self):

        semester = self.get_keyword('SEMESTER')
        progid   = self.get_keyword('PROGID')

        if (semester == None or progid == None): 
            return None

        semid = semester + '_' + progid
        return semid


    def fix_datetime(self, fname):

        # Temp fix for bad file times (NIRSPEC legacy)
        #todo: test this
        #todo: is this needed?

        datefile = ''.join(('/home/koaadmin/fixdatetime/', self.utDateDir, '.txt'))
        datefile = '/home/koaadmin/fixdatetime/20101128.txt'
        if os.path.isfile(datefile) is False:
            return

        fileroot = fname.split('/')
        fileroot = fileroot[-1]
        output = ''

        with open(datefile, 'r') as df:
            for line in df:
                if fileroot in line:
                    output = line
                    break

        if output != '':
            dateobs = self.get_keyword('DATE-OBS')
            if 'Error' not in dateobs and dateobs.strip() != '':
                return
            vals = output.split(' ')
            self.set_keyword('DATE-OBS', vals[1], ' Original value missing - added by KOA')
            self.set_keyword('UTC',      vals[2], 'Original value missing - added by KOA')


    def set_frameno(self):
        """
        Adds FRAMENO keyword to header if it doesn't exist
        """

        # self.log.info('set_frameno: setting FRAMNO keyword value from FRAMENUM')

        #skip if it exists
        if self.get_keyword('FRAMENO', False) != None: return True

        #get value
        #NOTE: If FRAMENO doesn't exist, derive from DATAFILE
        frameno = self.get_keyword('FRAMENUM')
        if (frameno == None): 

            datafile = self.get_keyword('DATAFILE')
            if (datafile == None):
                datafile = self.fitsHeader.get('OFNAME')
            if (datafile == None): 
                self.log.error('set_frameno: cannot find value for FRAMENO')
                return False

            frameno = datafile.replace('.fits', '')
            num = frameno.rfind('_') + 1
            # this is needed for new lris red 20210422 on (sometimes)
            # rfoc_00007.fits and rfoc00008.fits
            if num == 0:
                num = re.search(r'\d', frameno).start()
            frameno = frameno[num:]
            frameno = int(frameno)

            self.set_keyword('FRAMENUM', frameno, 'KOA: Image frame number (derived from filename)')

        #update
        self.set_keyword('FRAMENO', frameno, 'KOA: Image frame number')
        return True


    def is_science(self):
        '''
        Returns true if header indicates science data was taken.
        '''

        koaimtyp = self.get_keyword('KOAIMTYP')
        if koaimtyp == 'object' : return True
        else                    : return False


    def run_drp(self):
        '''
        This will be overwritten by method in instrument specific module.
        For those instruments without a DRP, just note that in the log.
        '''

        self.log.info('run_drp: no DRP defined for {}'.format(self.instr))
        return True

    def run_psfr(self):
        '''
        This will be overwritten by method in instrument specific module.
        For those instruments without PSFR, just note that in the log.
        '''

        self.log.info('run_psfr: no PSFR defined for {}'.format(self.instr))
        return True

    def set_numccds(self):
        try:
            panelist = self.get_keyword('PANELIST')
        except:
            self.set_keyword('NUMCCDS',0,'KOA: Number of CCDs')
            return True
        if panelist == '0':
            numccds = 0
        #mosaic data
        elif panelist == 'PANE':
            pane = self.get_keyword('PANE')
            plist = pane.split(',')
            dx = float(plist[2])
            if dx < 8192:
                numccds = 4
            elif dx < 6144:
                numccds = 3
            elif dx < 4096:
                numccds = 2
            elif dx < 2048:
                numccds = 1
            if 'LRISBLUE' in self.get_keyword('INSTRUME'):
                numccds = 1
                amplist = (self.get_keyword('AMPLIST')).split(',')
                if float(amplist[1]) > 2:
                    numccds = 2
        else:
            plist = panelist.split(',')
            numccds = 0
            for i,val in enumerate(plist):
                kywrd = f'PANE{str(val)}'
                pane = self.get_keyword(kywrd)
                plist2 = pane.split(',')
                dx = float(plist2[2])
                if dx < 2048:
                    numccds += 1
                else:
                    if dx < 4096:
                        numccds += 2
                    else:
                        numccds += 3

        self.set_keyword('NUMCCDS',numccds,'KOA: Number of CCDs')
        return True


    def dqa_loc(self, delete=0):
        '''
        Creates or deletes the dqa.LOC file.
        This file is needed for the PSF/TRS process.
        '''

        dqaLoc = f"{self.dirs['lev0']}/dqa.LOC"

        if delete == 0:
            if not os.path.isfile(dqaLoc):
                self.log.info(f'dqa_loc: creating {dqaLoc}')
                open(dqaLoc, 'w').close()
        elif delete == 1:
            if os.path.isfile(dqaLoc):
                self.log.info(f'dqa_loc: removing {dqaLoc}')
                os.remove(dqaLoc)
        else:
            self.log.info('dqa_loc: invalid input parameter')

        return True

    def set_filesize(self, filename):
        '''
        Add file size to the metadata table
        '''
        self.extraMeta['FILESIZE_MB'] = 0.0 
        
        if os.path.isfile(filename):
            filesize = round(os.path.getsize(filename) / 1000000, 2)
            self.extraMeta['FILESIZE_MB'] = filesize
            
        return True

    def check_filetime_vs_window(self, filename):
        '''
        Used to avoid adding duplicate FCS files re-used from previous days.
        Override in instr_<instrument> class to use.

        :return: (bool) True if file is within 24 hrs.
        '''
        return True

    @staticmethod
    def check_type_str(chk_list, dfault):
        for i, val in enumerate(chk_list):
            if type(val) != str:
                continue
            try:
                chk_list[i] = float(val)
            except ValueError:
                chk_list[i] = dfault

        return chk_list

