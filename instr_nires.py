'''
This is the class to handle all the NIRES specific attributes
NIRES specific DR techniques can be added to it in the future

12/14/2017 M. Brown - Created initial file
'''

import instrument
import datetime as dt
from common import *

class Nires(instrument.Instrument):

    def __init__(self, instr, utDate, rootDir, log=None):

        # Call the parent init to get all the shared variables
        super().__init__(instr, utDate, rootDir, log)


        # Set any unique keyword index values here
        self.ofName = 'DATAFILE'        
        self.frameno = 'FRAMENUM'


        # Other vars that subclass can overwrite
        self.endTime = '19:00:00'   # 24 hour period start/end time (UT)


        # Generate the paths to the NIRES datadisk accounts
        self.sdataList = self.get_dir_list()


    def run_dqa_checks(self, progData):
        '''
        Run all DQA checks unique to this instrument.
        '''

        ok = True
        if ok: ok = self.check_instr()
        if ok: ok = self.set_dateObs()
        if ok: ok = self.set_utc()
        if ok: ok = self.set_elaptime()
        if ok: ok = self.set_koaimtyp()
        if ok: ok = self.set_koaid()
        if ok: ok = self.set_ut()
        if ok: ok = self.set_frameno()
        if ok: ok = self.set_ofName()
        if ok: ok = self.set_semester()
        if ok: ok = self.set_prog_info(progData)
        if ok: ok = self.set_propint()
        if ok: ok = self.set_wavelengths()
        if ok: ok = self.set_specres()
        if ok: ok = self.set_weather_keywords()
        if ok: ok = self.set_datlevel(0)
        if ok: ok = self.set_filter()
        if ok: ok = self.set_slit_dims()
        if ok: ok = self.set_spatscal()
        if ok: ok = self.set_dispscal()
        if ok: ok = self.set_image_stats_keywords()
        if ok: ok = self.set_npixsat()
        if ok: ok = self.set_oa()
        if ok: ok = self.set_dqa_date()
        if ok: ok = self.set_dqa_vers()
        return ok



    def get_dir_list(self):
        '''
        Function to generate generates all the storage locations including engineering
        Returns the list of paths
        '''
        dirs = []
        path = '/s/sdata150'
        for i in range(0,4):
            joinSeq = (path, str(i))
            path2 = ''.join(joinSeq)
            dirs.append(path2 + '/nireseng')
            for j in range(1, 10):
                path3 = ''.join((path2, '/nires', str(j)))
                dirs.append(path3)
        return dirs


    def set_prefix(self, keys):
        '''
        Sets the KOAID prefix
        Defaults to empty string
        '''
        #todo: why is this named 'set'?  It is not setting anything

        instr = self.set_instr(keys)
        if instr == 'nires':
            try:
                ftype = keys['INSTR']
            except KeyError:
                prefix = ''
            else:
                if ftype == 'imag':
                    prefix = 'NI'
                elif ftype == 'spec':
                    prefix = 'NR'
                else:
                    prefix = ''
        else:
            prefix = ''
        return prefix


    def set_raw_fname(self, keys):
        """
        Overloaded method to create the NIRES rawfile name
        NIRES uses DATAFILE to retrieve the filename without
        the FITS extension, so we have to add that back on

        @type keys: dictionary
        @param keys: FITS header keys for the given file
        """
        #todo: why is this named 'set'?  It is not setting anything

        try:
            outfile = keys[self.ofName]
        except KeyError:
            return '', False
        else:
            filename = outfile
            if (filename.endsWith('.fits') == False) : filename += '.fits'
            return filename, True


    def set_frameno(self):
        """
        Adds FRAMENO keyword to header if it doesn't exist
        #NOTE: keyword FRAMENUM added in Apr 2018
        """
 
        self.log.info('set_frameno: setting FRAMNO keyword value from FRAMENUM')

        #skip if it exists
        keys = self.fitsHeader
        if keys.get('FRAMENO') != None: return True

        # todo: derive from FRAMENUM first, then go on to DATAFILE

        #get value
        #NOTE: If FRAMENO doesn't exist, derive from DATAFILE
        frameno = keys.get(self.frameno)
        if (frameno == None): 

            datafile = keys.get('DATAFILE')
            if (datafile == None): 
                self.log.error('set_frameno: cannot find value for FRAMENO')
                return False

            frameno = datafile.replace('.fits', '')
            num = frameno.rfind('_') + 1
            frameno = frameno[num:]
            frameno = int(frameno)


        #update
        keys.update({'FRAMENO' : (frameno, 'KOA: Added keyword')})
        return True



    def set_ofName(self):
        """
        Adds OFNAME keyword to header (copy of DATAFILE)
        """

        self.log.info('set_ofName: setting OFNAME keyword value')

        #get value
        keys = self.fitsHeader
        ofName = keys.get(self.ofName)
        if (ofName == None): 
            self.log.error('set_ofName: cannot find value for OFNAME')
            return False

        #add *.fits to output if it does not exist (to fix old files)
        if (ofName.endswith('.fits') == False) : ofName += '.fits'

        #update
        keys.update({'OFNAME' : (ofName, 'KOA: Added keyword')})
        return True


    def set_elaptime(self):
        '''
        Fixes missing ELAPTIME keyword.
        '''

        self.log.info('set_elaptime: determining ELAPTIME from ITIME/COADDS')

        ekeys = self.fitsHeader

        #skip if it exists
        if keys.get('ELAPTIME') != None: return True

        #get necessary keywords
        itime  = keys.get('ITIME')
        coadds = keys.get('COADDS')
        if (itime == None or coadds == None):
            self.log.error('ITIME and COADDS values needed to set ELAPTIME')
            return False

        #update val
        elaptime = itime * coadds
        keys.update({'ELAPTIME' : (elaptime, 'KOA: Added keyword')})
        return True
        

    def set_wavelengths(self):
        '''
        Adds wavelength keywords.
        # https://www.keck.hawaii.edu/realpublic/inst/nires/genspecs.html
        # NOTE: kfilter is always on for imag
        '''

        self.log.info('set_wavelengths: setting wavelength keyword values')

        keys = self.fitsHeader
        instr = keys.get('INSTR')

        #imaging (K-filter always on):
        if (instr == 'imag'):
            keys.update({'WAVERED' : (19500, 'KOA: Added keyword')})
            keys.update({'WAVECNTR': (21230, 'KOA: Added keyword')})
            keys.update({'WAVEBLUE': (22950, 'KOA: Added keyword')})

        #spec:
        elif (instr == 'spec'):
            keys.update({'WAVERED' : (9400,  'KOA: Added keyword')})
            keys.update({'WAVECNTR': (16950, 'KOA: Added keyword')})
            keys.update({'WAVEBLUE': (24500, 'KOA: Added keyword')})

        return True


    def set_specres(self):
        '''
        Adds nominal spectral resolution keyword
        '''

        self.log.info('set_specres: setting SPECRES keyword values')

        keys = self.fitsHeader
        if (keys.get('INSTR') == 'spec'):
            specres = 2700.0
            keys.update({'SPECRES' : (specres,  'KOA: Added keyword')})
        return True


    def set_dispscal(self):
        '''
        Adds display scale keyword to header.
        '''

        keys = self.fitsHeader
        instr = keys.get('INSTR')
        if   (instr == 'imag'): dispscal = 0.12
        elif (instr == 'spec'): dispscal = 0.15
        keys.update({'DISPSCAL' : (dispscal, 'KOA: Added keyword')})
        return True


    def set_spatscal(self):
        '''
        Adds spatial scale keyword to header.
        '''

        keys = self.fitsHeader
        instr = keys.get('INSTR')
        if   (instr == 'imag'): spatscal = 0.12
        elif (instr == 'spec'): spatscal = 0.15
        keys.update({'SPATSCAL' : (spatscal, 'KOA: Added keyword')})
        return True


    def set_filter(self):
        '''
        Adds FILTER keyword to header.
        '''

        #add keyword for 'imag' only
        keys = self.fitsHeader
        if (keys.get('INSTR') == 'imag'):
            self.log.info('set_filter: setting FILTER keyword value')
            filt = 'Kp'
            keys.update({'FILTER' : (filt, 'KOA: Added keyword')})
        return True


    def set_slit_dims(self):
        '''
        Adds slit length and width keywords to header.
        '''

        #add keywords for 'spec' only
        keys = self.fitsHeader
        if (keys.get('INSTR') == 'spec'):
            self.log.info('set_slit_dims: setting slit keyword values')
            slitlen  = 18.1
            slitwidt = 0.5
            keys.update({'SLITLEN'  : (slitlen,  'KOA: Added keyword')})
            keys.update({'SLITWIDT' : (slitwidt, 'KOA: Added keyword')})
        return True


    def set_koaimtyp(self):
        '''
        Fixes missing KOAIMTYP keyword.
        This is derived from OBSTYPE keyword.
        '''

        self.log.info('set_koaimtyp: setting KOAIMTYP keyowrd value from OBSTYPE')

        #get obstype value
        keys = self.fitsHeader
        obstype = keys.get('OBSTYPE')

        #map to KOAIMTYP value
        koaimtyp = 'undefined'
        validValsMap = {
            'object'  : None,
            'standard': 'object',
            'bias'    : None, 
            'dark'    : None, 
            'domeflat': None, 
            'domearc' : None, 
            'astro'   : 'object',   #NOTE: old val
            'star'    : 'object',   #NOTE: old val
            'calib'   : 'undefined' #NOTE: old val
        }
        if (obstype != None and obstype in validValsMap): 
            koaimtyp = obstype
            if (validValsMap[obstype] != None): koaimtyp = validValsMap[obstype]

        #update keyword
        keys.update({'KOAIMTYP' : (koaimtyp,  'KOA: Added keyword')})
        return True


    def is_science(self):
        '''
        Returns true if header indicates science data was taken.
        (KOAIMTYP='object')
        '''

        keys = self.fitsHeader
        koaimtyp = keys.get('KOAIMTYP')
        if koaimtyp == 'object' : return True
        else                    : return False
    
