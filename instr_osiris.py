'''
This is the class to handle all the OSIRIS specific attributes
OSIRIS specific DR techniques can be added to it in the future

12/14/2017 M. Brown - Created initial file
'''

import instrument
import datetime as dt
from common import *
from math import ceil

class Osiris(instrument.Instrument):

    def __init__(self, instr, utDate, rootDir, log=None):

        # Call the parent init to get all the shared variables
        super().__init__(instr, utDate, rootDir, log)

        # OSIRIS has 'DATAFILE' instead of OUTFILE
        self.ofName = 'DATAFILE'

        #other vars that subclass can overwrite
        self.endTime = '19:00:00'   # 24 hour period start/end time (UT)

        # Generate the paths to the OSIRIS datadisk accounts
        self.paths = self.get_dir_list()


    def run_dqa_checks(self, progData):
        '''
        Run all DQA checks unique to this instrument
        '''

        ok = True
        if ok: ok = self.set_dqa_date()
        if ok: ok = self.set_dqa_vers()
        if ok: ok = self.set_datlevel(0)
        if ok: ok = self.set_instr()
        if ok: ok = self.set_dateObs()
        if ok: ok = self.set_ut()
#        if ok: ok = self.set_elaptime()
#        if ok: ok = self.set_koaimtyp()
        if ok: ok = self.set_koaid()
        if ok: ok = self.set_frameno()
#        if ok: ok = self.set_ofName()
        if ok: ok = self.set_semester()
#        if ok: ok = self.set_isao()
#        if ok: ok = self.set_dispers()
#        if ok: ok = self.set_slit_values()
#        if ok: ok = self.set_wavelengths()
#        if ok: ok = self.set_weather_keywords()
#        if ok: ok = self.set_image_stats_keywords()
#        if ok: ok = self.set_gain_and_readnoise()
#        if ok: ok = self.set_npixsat(self.get_keyword('COADDS') * 25000)
        if ok: ok = self.set_oa()
        if ok: ok = self.set_prog_info(progData)
        if ok: ok = self.set_propint(progData)

        return ok


    def get_dir_list(self):
        '''
        Function to generate the paths to all the OSIRIS accounts, including engineering
        Returns the list of paths
        '''
        dirs = []
        path = '/s/sdata110'
        for i in range (2):
            seq = (path, str(i))
            path2 = ''.join(seq)
            seq = (path2, '/osiris')
            dirs.append(''.join(seq))
            for j in range(1,21):
                seq = (path, '/osiris', str(j))
                path3 = ''.join(seq)
                dirs.append(path3)
            seq = (path2, '/osiriseng')
            dirs.append(''.join(seq))
            seq = (path2, '/osrseng')
            dirs.append(''.join(seq))
        return dirs

    def get_prefix(self):
        try:
            instr = self.get_keyword('INSTR')
        except KeyError:
            prefix = ''
        else:
            if 'imag' in instr:
                prefix = 'OI'
            elif 'spec' in instr:
                prefix = 'OS'
            else:
                prefix = ''
        return prefix

    def set_elaptime(self):
        '''
        Fixes missing ELAPTIME keyword
        '''
        self.log.info('set_elaptime: determining ELAPTIME from TRUITIME')

        #skip it it exists
        if self.get_keyword('ELAPTIME', False) != None: return True

        #get necessary keywords
        itime  = self.get_keyword('TRUITIME')
        coadds = self.get_keyword('COADDS')
        #if exposure time or # of exposures doesn't exist, throw error
        if (itime == None or coadds == None):
            self.log.error('set_elaptime: TRUITIME and COADDS values needed to set ELAPTIME')
            return False

        #update elaptime val, convert from milleseconds to seconds
        elaptime = round(itime/1000 * coadds, 5)
        self.set_keyword('ELAPTIME', elaptime, 'KOA: Total integration time')
        
        return True
    
    def set_instr(self):
        #update instrument
        self.set_keyword('INSTRUME', 'OSIRIS', 'Instrument (added by KOA)') 
        
        return True
        

    def set_koaimtyp(self):
        '''
        Adds KOAIMTYP keyword
        '''

        self.log.info('set_koaimtyp: setting KOAIMTYP keyword from algorithm')

        koaimtyp = 'undefined'
        ifilter = self.get_keyword('IFILTER')
        sfilter = self.get_keyword('SFILTER')
        axestat = self.get_keyword('AXESTAT')
        domeposn = self.get_keyword('DOMEPOSN')
        az = self.get_keyword('AZ')
        el = self.get_keyword('EL')
        obsfname = self.get_keyword('OBSFNAME')
        obsfx = self.get_keyword('OBSFX')
        obsfy = self.get_keyword('OBSFY')
        obsfz = self.get_keyword('OBSFZ')
        instr = self.get_keyword('INSTR')
        datafile = self.get_keyword('DATAFILE')
        coadds = self.get_keyword('COADDS')

        # telescope at flat position
        flatpos = 0
        if (el < 45.11 and el > 44.89) and (domeposn - az > 80.0 and domeposn - az < 100.0):
            flatpos = 1

        if 'telescope' in obsfname.lower():
            koaimtyp = 'object'

        # recmat files
        if 'c' in datafile:
            koaimtyp = 'calib'

        # dark if ifilter/sfilter is dark
        if 'drk' in ifilter.lower() and instr.lower() == 'imag':
            koaimtyp = 'dark'
        elif 'drk' in sfilter.lower() and instr.lower() == 'spec':
            koaimtyp = 'dark'

        # uses dome lamps for instr=imag
        elif instr.lower() == 'imag':
            if 'telescope' in obsfname and 'not controlling' in axestat and flatpos:
                # divide image by coadds
                img = self.fitsHdu[0].data

                # median
                imgmed = np.median(img)

                if imgmed > 30.0:
                    koaimtyp = 'flatlamp'
                else:
                    koaimtyp = 'flatlampoff'

        if instr.lower == 'spec':
            if 'telsim' in obsfname or (obsfx > 30 and obsfy < 0.1 and obsfz < 0.1):
                koaimtyp = 'undefined'
            elif obsfz > 10:
                koaimtype = 'undefined'
        elif 'c' in datafile:
            koaimtyp = 'calib'

        #warn if undefined
        if (koaimtyp == 'undefined'):
            self.log.info('set_koaimtyp: Could not determine KOAIMTYP value')

        #update keyword
        self.set_keyword('KOAIMTYP', koaimtyp, 'KOA: Image type')
        return True

