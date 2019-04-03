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
        self.keywordMap['OFNAME']       = 'DATAFILE'        
        self.keywordMap['FRAMENO']      = 'FRAMENUM'


        # Other vars that subclass can overwrite
        self.endTime = '19:00:00'   # 24 hour period start/end time (UT)


        # Generate the paths to the NIRES datadisk accounts
        self.sdataList = self.get_dir_list()


    def run_dqa_checks(self, progData):
        '''
        Run all DQA checks unique to this instrument.
        '''

        ok = True
        if ok: ok = self.set_instr()
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
        if ok: ok = self.set_propint(progData)
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


    def get_prefix(self):
        '''
        Sets the KOAID prefix. Defaults to empty string
        '''

        instr = self.get_instr()
        if instr == 'nires':
            ftype = self.get_keyword('FTYPE')
            if   ftype == 'imag': prefix = 'NI'
            elif ftype == 'spec': prefix = 'NR'
            else                : prefix = ''
        else:
            prefix = ''
        return prefix



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


    def set_elaptime(self):
        '''
        Fixes missing ELAPTIME keyword.
        '''

        # self.log.info('set_elaptime: determining ELAPTIME from ITIME/COADDS')

        #skip if it exists
        if self.get_keyword('ELAPTIME', False) != None: return True

        #get necessary keywords
        itime  = self.get_keyword('ITIME')
        coadds = self.get_keyword('COADDS')
        if (itime == None or coadds == None):
            self.log.error('set_elaptime: ITIME and COADDS values needed to set ELAPTIME')
            return False

        #update val
        elaptime = itime * coadds
        self.set_keyword('ELAPTIME', elaptime, 'KOA: Total integration time')
        return True
        

    def set_wavelengths(self):
        '''
        Adds wavelength keywords.
        # https://www.keck.hawaii.edu/realpublic/inst/nires/genspecs.html
        # NOTE: kfilter is always on for imag
        '''

        # self.log.info('set_wavelengths: setting wavelength keyword values')

        instr = self.get_keyword('FTYPE')

        #imaging (K-filter always on):
        if (instr == 'imag'):
            self.set_keyword('WAVERED' , 22950, 'KOA: Red end wavelength')
            self.set_keyword('WAVECNTR', 21225, 'KOA: Center wavelength')
            self.set_keyword('WAVEBLUE', 19500, 'KOA: Blue end wavelength')

        #spec:
        elif (instr == 'spec'):
            self.set_keyword('WAVERED' , 24500, 'KOA: Red end wavelength')
            self.set_keyword('WAVECNTR', 16950, 'KOA: Center wavelength')
            self.set_keyword('WAVEBLUE',  9400, 'KOA: Blue end wavelength')

        return True


    def set_specres(self):
        '''
        Adds nominal spectral resolution keyword
        '''

        # self.log.info('set_specres: setting SPECRES keyword values')

        instr = self.get_keyword('FTYPE')
        if (instr == 'spec'):
            specres = 2700.0
            self.set_keyword('SPECRES' , specres,  'KOA: Nominal spectral resolution')
        return True


    def set_dispscal(self):
        '''
        Adds CCD pixel scale, dispersion (arcsec/pixel) keyword to header.
        '''

        instr = self.get_keyword('FTYPE')
        if   (instr == 'imag'): dispscal = 0.12
        elif (instr == 'spec'): dispscal = 0.15
        self.set_keyword('DISPSCAL' , dispscal, 'KOA: CCD pixel scale, dispersion')
        return True


    def set_spatscal(self):
        '''
        Adds spatial scale keyword to header.
        '''

        instr = self.get_keyword('FTYPE')
        if   (instr == 'imag'): spatscal = 0.12
        elif (instr == 'spec'): spatscal = 0.15
        self.set_keyword('SPATSCAL' , spatscal, 'KOA: CCD pixel scale, spatial')
        return True


    def set_filter(self):
        '''
        Adds FILTER keyword to header.
        '''

        #add keyword for 'imag' only
        instr = self.get_keyword('FTYPE')
        if (instr == 'imag'):
            # self.log.info('set_filter: setting FILTER keyword value')
            filt = 'Kp'
            self.set_keyword('FILTER' , filt, 'KOA: Filter')
        return True


    def set_slit_dims(self):
        '''
        Adds slit length and width keywords to header.
        '''

        #add keywords for 'spec' only
        instr = self.get_keyword('FTYPE')
        if (instr == 'spec'):
            # self.log.info('set_slit_dims: setting slit keyword values')
            slitlen  = 18.1
            slitwidt = 0.5
            self.set_keyword('SLITLEN'  , slitlen,  'KOA: Slit length projected on sky')
            self.set_keyword('SLITWIDT' , slitwidt, 'KOA: Slit width projected on sky')
        return True


    def set_koaimtyp(self):
        '''
        Fixes missing KOAIMTYP keyword.
        This is derived from OBSTYPE keyword.
        '''

        # self.log.info('set_koaimtyp: setting KOAIMTYP keyword value from OBSTYPE')

        #get obstype value
        obstype = self.get_keyword('OBSTYPE')

        #map to KOAIMTYP value 
        koaimtyp = 'undefined'
        validValsMap = {
            'object'  : 'object',
            'standard': 'object',   #NOTE: old val
            'telluric': 'object',
            'bias'    : 'bias', 
            'dark'    : 'dark', 
            'domeflat': 'domeflat', 
            'domearc' : 'domearc', 
            'astro'   : 'object',   #NOTE: old val
            'star'    : 'object',   #NOTE: old val
            'calib'   : 'undefined' #NOTE: old val
        }
        if (obstype != None and obstype.lower() in validValsMap): 
            koaimtyp = validValsMap[obstype.lower()]

        #warn if undefined
        if (koaimtyp == 'undefined'):
            self.log.info('set_koaimtyp: Could not determine KOAIMTYP from OBSTYPE value of "' + str(obstype) + '"')

        #update keyword
        self.set_keyword('KOAIMTYP', koaimtyp, 'KOA: Image type')
        return True

