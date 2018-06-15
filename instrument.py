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


class Instrument:
    def __init__(self, instr, utDate, rootDir, log=None):
        """
        Base Instrument class to hold all the values common between
        instruments. Contains default values where possible
        but null values should be replaced in the init of the 
        subclasses.

        @param instr: instrument name
        @type instr: string
        @param utDate: UT date of observation
        @type utDate: string (YYYY-MM-DD)
        @param rootDir: root directory to write processed files
        @type rootDir: string
        @type log: Logger Object
        @param log: The log handler for the script. Writes to the logfile
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

        # Other values that can be overwritten in instr-*.py
        self.endHour = '20:00:00'	# 24 hour period start/end time (UT)


        # Values to be populated by subclass
        self.prefix = ''
        self.rawfile = ''
        self.koaid = ''
        self.sdataList = []
        self.extraMeta = {}


        #other helpful vars
        self.utDateDir = self.utDate.replace('/', '-').replace('-', '')


        # Verify input parameters
        verify_instrument(self.instr.upper())
        verify_date(self.utDate)
        assert os.path.isdir(self.rootDir), 'rootDir does not exist'



    def dep_init(self, config, fullRun=True):
        '''
        Perform specific initialization tasks for DEP processing.
        '''

        #TODO: exit if existence of output/stage dirs? Maybe put override in config?
        

        #store config
        self.config = config
        self.koaUrl = config['API']['KOAAPI']
        self.telUrl = config['API']['TELAPI']
        self.metadataTablesDir = config['MISC']['METADATA_TABLES_DIR']


        #create log if it does not exist
        if not self.log:
            self.log = cl.create_log(self.rootDir, self.instr, self.utDate, True)
            self.log.info('instrument.py: log created')


        #check and create dirs
        self.init_dirs(fullRun)


        #create README (output dir with everything before /koadata##/... stripped off)
        readmeFile = self.dirs['output'] + '/README';
        with open(readmeFile, 'w') as f:
            path = self.dirs['output']
            match = re.search( r'.*(/.*/.*/\d\d\d\d\d\d\d\d)$', path, re.M)
            if match: path = match.groups(0)[0]
            f.write(path + '\n')


    def init_dirs(self, fullRun=True):

        # get the various root dirs
        self.dirs = get_root_dirs(self.rootDir, self.instr, self.utDate)


        # Create the directories, if they don't already exist
        for key, dir in self.dirs.items():
            if key == 'process': continue # process dir should always exists
            self.log.info('instrument.py: {} directory {}'.format(key, dir))
            if os.path.isdir(dir):
                if (fullRun):
                    raise Exception('instrument.py: staging and/or output directories already exist')
            else:
                try:
                    os.makedirs(dir)
                except:
                    raise Exception('instrument.py: could not create {}'.format(dir))


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
        try:
            self.fitsHdu = fits.open(filename)
            self.fitsHeader = self.fitsHdu[0].header
            #self.fitsHeader = fits.getheader(filename)
            self.fitsFilepath = filename
        except:
            self.log.warning('set_fits_file: Could not read FITS file.  UDF!')
            return False

        self.koaid = '';
        self.rawfile = ''
        self.prefix = ''
        self.extraMeta = {}

        return True


    def set_koaid(self):
        '''
        Create and add KOAID to header if it does not already exist
        '''

        #skip if it exists
        if self.fitsHeader.get('KOAID') != None: return True

        #make it
        koaid, result = self.make_koaid(self.fitsHeader)
        if not result: 
            self.log.warning('set_koaid: Could not create KOAID.  UDF!')
            return False

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

        #TODO: see common.koaid() and make sure all logic is moved here or to instr_*.py


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
        totalSeconds = str((hour * 3600) + (minute * 60) + second)

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
        '''
        #todo:  go over idl file again and pull out logic for other instruments
        #todo: use class key vals instead

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
            self.log.warning('check_instr: Cannot determine if file is from ' + self.instr + '.  UDF!')

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
            keys.update({self.utc : (utc, 'KOA: Added missing keyword')})

        return True



    def set_ut(self):

        keys = self.fitsHeader

        #skip if it exists
        if keys.get('UT') != None: return True

        #get utc from header
        utc = keys.get(self.utc)
        if (not utc): 
            self.log.warning('set_ut: Could not get UTC value.  UDF!')
            return False

        #copy to UT
        keys.update({'UT' : (utc, 'KOA: Added missing keyword')})
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
            self.log.warning('set_prog_info: Could not get program info.  UDF!')
            return False

        #create keys
        keys = self.fitsHeader
        keys.update({'PROGID'  : (data['progid']  , 'KOA: Added keyword')})
        keys.update({'PROGINST': (data['proginst'], 'KOA: Added keyword')})
        keys.update({'PROGPI'  : (data['progpi']  , 'KOA: Added keyword')})

        #divide PROGTITL into length 70 chunks PROGTL1/2/3
        progtl1 = data['progtitl'][0:70]
        progtl2 = data['progtitl'][70:140]
        progtl3 = data['progtitl'][140:210]
        keys.update({'PROGTL1': (progtl1, '')})
        keys.update({'PROGTL2': (progtl2, '')})
        keys.update({'PROGTL3': (progtl3, '')})


        #NOTE: PROGTITL goes in metadata but not in header so we store in temp dict for later
        self.extraMeta['PROGTITL'] = data['progtitl']
        
        return True



    def set_semester(self):

        #TODO: move existing common.py semester() to Instrument?
        keys = self.fitsHeader        
        semester(keys)
        return True



    def set_propint(self, progData):
        '''
        Set proprietary period length.
        '''

        #create semid
        keys = self.fitsHeader
        semester = keys.get('SEMESTER')
        progid   = keys.get('PROGID')
        assert (semester != None and progid != None), 'set_propint: Could not find either SEMESTER or PROGID keyword.'
        semid = semester + '_' + progid

        # Default to 18 for ENG data (***verify with SAs***)
        if progid == 'ENG':
            propint = 18
        else:
            #create url and get data
            url = self.koaUrl + 'cmd=getPP&semid=' +  semid + '&utdate=' + self.utDate
            data = url_get(url, getOne=True)
            assert (data and  data['propint']), 'set_proprint: Unable to set PROPINT keyword.'
            propint = int(data['propint'])

        #NOTE: PROPINT goes in metadata but not in header so we store in temp dict for later
        self.extraMeta['PROPINT'] = propint

        return True


    def set_datlevel(self, datlevel):
        '''
        Adds "DATLEVEL" keyword to header
        '''
        keys = self.fitsHeader
        keys.update({'DATLEVEL' : (datlevel, 'KOA: Added keyword')})
        return True


    def set_dqa_date(self):
        """
        Adds date timestamp for when the DQA module was run
        """
        keys = self.fitsHeader
        dqa_date = dt.strftime(dt.now(), '%Y-%m-%dT%H:%M:%S')
        keys.update({'DQA_DATE' : (dqa_date, 'KOA: Added keyword')})
        return True


    def set_dqa_vers(self):
        '''
        Adds DQA version keyword to header
        '''
        keys = self.fitsHeader

        import configparser
        config = configparser.ConfigParser()
        config.read('config.live.ini')

        version = config['INFO']['DQA_VERSION']
        keys.update({'DQA_VERS' : (version, 'KOA: Added keyword')})
        return True


    def set_image_stats_keywords(self):
        '''
        Adds mean, median, std keywords to header
        '''
        keys = self.fitsHeader

        image = self.fitsHdu[0].data     
        imageMean   = round(np.mean(image)  , 2)
        imageStd    = round(np.std(image)   , 2)
        imageMedian = round(np.median(image), 2)

        keys.update({'IMAGEMN' : (imageMean,   'KOA: Added keyword')})
        keys.update({'IMAGESD' : (imageStd,    'KOA: Added keyword')})
        keys.update({'IMAGEMD' : (imageMedian, 'KOA: Added keyword')})

        return True


    def set_npixsat(self):
        '''
        Determines number of saturated pixels and adds NPIXSAT to header
        '''
        keys = self.fitsHeader
        satVal = keys.get('SATURATE')

        image = self.fitsHdu[0].data     
        pixSat = image[np.where(image >= satVal)]
        nPixSat = len(image[np.where(image >= satVal)])
        keys.update({'NPIXSAT' : (nPixSat, 'KOA: Added keyword')})

        return True


    def set_oa(self):
        '''
        Adds observing assistant name to header
        '''

        # Get OA from dep_obtain file
        dep_obtain = self.dirs['stage'] + '/dep_obtain' + self.instr + '.txt'
        oas = []
        oa = None
        with open(dep_obtain, 'r') as dob:
            for line in dob:
                items = line.strip().split(' ')
                if len(items)>1:
                    oas.append(items[1])
        if (len(oas) >= 1): oa = oas[0]

        keys = self.fitsHeader
        keys.update({'OA' : (oa, 'KOA: Added keyword')})

        return True




    def set_weather_keywords(self):
        '''
        Adds all weather related keywords to header.
        NOTE: DEP should not exit if weather files are not found
        '''

        #get input vars
        keys = self.fitsHeader
        dateobs = keys.get('DATE-OBS')
        utc = keys.get('UTC')
        telnr = self.get_telnr()


        #read envMet.arT and write to header
        logFile = self.dirs['anc'] + '/nightly/envMet.arT'
        data = envlog(logFile, 'envMet',   telnr, dateobs, utc)
        if type(data) is not dict: 
            self.log.warning("Could not read envMet.arT data")
            return True

        keys.update({'WXDOMHUM' : (data['wx_domhum'],    'KOA: Added keyword')})
        keys.update({'WXDOMTMP' : (data['wx_domtmp'],    'KOA: Added keyword')})
        keys.update({'WXDWPT'   : (data['wx_dewpoint'],  'KOA: Added keyword')})
        keys.update({'WXOUTHUM' : (data['wx_outhum'],    'KOA: Added keyword')})
        keys.update({'WXOUTTMP' : (data['wx_outtmp'],    'KOA: Added keyword')})
        keys.update({'WXPRESS'  : (data['wx_pressure'],  'KOA: Added keyword')})
        keys.update({'WXTIME'   : (data['time'],         'KOA: Added keyword')})
        keys.update({'WXWNDIR'  : (data['wx_winddir'],   'KOA: Added keyword')})
        keys.update({'WXWNDSP'  : (data['wx_windspeed'], 'KOA: Added keyword')})


        #read envFocus.arT and write to header
        logFile = self.dirs['anc'] + '/nightly/envFocus.arT'
        data = envlog(logFile, 'envFocus', telnr, dateobs, utc)
        if type(data) is not dict: 
            self.log.warning("Could not read envFocus.arT data")
            return True

        keys.update({'GUIDFWHM' : (data['guidfwhm'],     'KOA: Added keyword')})
        keys.update({'GUIDTIME' : (data['time'],         'KOA: Added keyword')})

        return True


    def get_telnr(self):
        '''
        Gets telescope number for instrument via API
        #todo: store this and skip api call if exists?  Would need to clear var on fits reload.
        #todo: Replace API call with hard-coded?
        '''

        url = self.telUrl + 'cmd=getTelnr&instr=' + self.instr.upper()
        data = url_get(url, getOne=True)
        telNr = int(data['TelNr'])
        assert telNr in [1, 2], 'telNr "' + telNr + '"" not allowed'
        return telNr


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

        #already exists?
        #todo: only allow skip if not fullRun
        # if os.path.isfile(outfile):
        #     self.log.warning('write_lev0_fits_file: file already exists. SKIPPING')
        #     return True

        #write out new fits file with altered header
        self.fitsHdu.writeto(outfile)
        return True


    def make_jpg(self):
        '''
        Converts a FITS file to JPG image
        '''

        import matplotlib as mpl
        mpl.use('Agg')
        import matplotlib.pyplot as plt
        from PIL import Image
        from astropy.visualization import ZScaleInterval, SinhStretch
        from astropy.visualization.mpl_normalize import ImageNormalize

        # file to convert is lev0Dir/KOAID

        path = self.dirs['lev0']
        koaid = self.fitsHeader.get('KOAID')
        filePath = ''.join((path, '/', koaid))
        self.log.info('make_jpg: converting {} to jpeg format'.format(filePath))

        #already exists?
        #todo: only allow skip if not fullRun

        jpgFile = filePath.replace('.fits', '.jpg')
        if os.path.isfile(jpgFile):
            self.log.warning('make_jpg: file already exists. SKIPPING')
            return True

        # verify file exists

        if os.path.isfile(filePath):
            # image data to convert
            image = self.fitsHdu[0].data
            interval = ZScaleInterval()
            vmin, vmax = interval.get_limits(image)
            norm = ImageNormalize(vmin=vmin, vmax=vmax, stretch=SinhStretch())
            plt.imshow(image, cmap='gray', origin='lower', norm=norm)
            plt.axis('off')
            # save as png, then convert to jpg
            pngFile = filePath.replace('.fits', '.png')
            jpgFile = pngFile.replace('.png', '.jpg')
            plt.savefig(pngFile)
            Image.open(pngFile).convert('RGB').save(jpgFile)
            os.remove(pngFile)
            self.log.info('make_jpg: file created {}'.format(jpgFile))
            return True
        else:
            #TODO: if this errors, should we remove .fits file added previously?
            self.log.error('make_jpg: file does not exist {}'.format(filePath))
            return False

