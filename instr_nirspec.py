'''
This is the class to handle all the NIRSPEC specific attributes
NIRSPEC specific DR techniques can be added to it in the future

12/14/2017 M. Brown - Created initial file
'''

import instrument
import datetime as dt
from common import *

class Nirspec(instrument.Instrument):

    def __init__(self, instr, utDate, rootDir, log=None):

        #call the parent init to get all the shared variables
        super().__init__(instr, utDate, rootDir, log)

        #set any unique keyword index values here
        self.keywordMap['OFNAME'] = 'DATAFILE'
        self.keywordMap['FRAMENO'] = 'FRAMENUM'

        #other vars that subclass can overwrite
        self.endTime = '19:00:00'   # 24 hour period start/end time (UT)

        #generate the paths to the NIRSPEC datadisk accounts
        self.sdataList = self.get_dir_list()


    def run_dqa_checks(self, progData):
        '''
        Run all DQA checks unique to this instrument
        '''

        ok = True
        if ok: ok = self.set_instr()
        if ok: ok = self.set_dateObs()
        if ok: ok = self.set_elaptime()
        if ok: ok = self.set_koaimtyp()
        if ok: ok = self.set_koaid()
        if ok: ok = self.set_frameno()
        if ok: ok = self.set_ofName()
        if ok: ok = self.set_semester()
        if ok: ok = self.set_prog_info(progData)
        if ok: ok = self.set_propint(progData)
        if ok: ok = self.set_wavelengths()
#        if ok: ok = self.set_specres()
        if ok: ok = self.set_weather_keywords()
        if ok: ok = self.set_datlevel(0)
#        if ok: ok = self.set_filter()
#        if ok: ok = self.set_slit_dims()
#        if ok: ok = self.set_spatscal()
#        if ok: ok = self.set_dispscal()
#        if ok: ok = self.set_image_stats_keywords()
#        if ok: ok = self.set_npixsat()
        if ok: ok = self.set_oa()
        if ok: ok = self.set_dqa_date()
        if ok: ok = self.set_dqa_vers()

        return ok


    def get_dir_list(self):
        '''
        Function to generate the paths to all the NIRSPEC accounts, including engineering
        Returns the list of paths
        '''
        dirs = []
        path = '/s/sdata90'
        for i in range(4):
            joinSeq = (path, str(i))
            path2 = ''.join(joinSeq)
            for j in range(1,10):
                joinSeq = (path2, '/nspec', str(j))
                path3 = ''.join(joinSeq)
                dirs.append(path3)
            joinSeq = (path2, '/nspeceng')
            path3 = ''.join(joinSeq)
            dirs.append(path3)
            joinSeq = (path2, 'nirspec')
            path3 = ''.join(joinSeq)
            dirs.append(path3)
        return dirs


    def get_prefix(self, keys):

        # SCAM = NC, SPEC = NS
        instr = self.get_instr()
        if instr == 'nirspec' or instr == 'nirspao':
            try:
                outdir = self.get_keyword['OUTDIR']
            except KeyError:
                prefix = ''
            else:
                if '/scam' in outdir:
                    prefix = 'NC'
                elif '/spec' in outdir:
                    prefix = 'NS'
                else:
                    prefix = ''
        else:
            prefix = ''
       return prefix


    def set_elaptime(self):
        '''
        Fixes missing ELAPTIME keyword
        '''

        self.log.info('set_elaptime: determining ELAPTIME from TRUITIME')

        #skip it it exists
        if self.get_keyword('ELAPTIME', Flase) != None: return True

        #get necessary keywords
        itime  = self.get_keyword('TRUITIME')
        coadds = self.get_keyword('COADDS')
        if (itime == None or coadds == None):
            self.log.error('set_elaptime: TRUITIME and COADDS values needed to set ELAPTIME'
            return False

        #update val
        elaptime = itime * coadds
        self.set_keyword('ELAPTIME', elaptime, 'KOA: Total integration time')
        return True


    def set_ofName(self):
        """
        Adds OFNAME keyword to header
        """

        self.log.info('set_ofName: setting OFNAME keyword value')

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


    def set_koaimtyp(self):
        '''
        Fixes missing KOAIMTYP keyword.
        This is derived from OBSTYPE keyword.
        '''

        self.log.info('set_koaimtyp: setting KOAIMTYP keyword value from OBSTYPE')

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
            self.log.info('set_koaimtyp: Could not determine KOAIMTYP from OBSTYPE value of "' + obstype + '"')

        #update keyword
        self.set_keyword('KOAIMTYP', koaimtyp, 'KOA: Image type')
        return True

