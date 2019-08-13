'''
This is the class to handle all the NIRC2 specific attributes
NIRC2 specific DR techniques can be added to it in the future

12/14/2017 M. Brown - Created initial file
08/07/2019 E. Lucas - updated to conform to new class standards
'''

import instrument
import datetime as dt
import numpy as np

class Nirc2(instrument.Instrument):
    def __init__(self, instr, utDate, rootDir, log=None):

        # Call parent init to get all the shared variables
        super().__init__(instr, utDate, rootDir, log)

        # NIRC2 uses ROOTNAME instead of OUTDIR
        self.ofName = 'FILENAME'

        # set endtime to 9AM
        self.endTime = '19:00:00' #UT

    def run_dqa_checks(self, progData):
        '''
        Run all DQA checks unique to this instrument
        '''
        ok=True
        if ok: ok = self.set_dqa_date()
        if ok: ok = self.set_dqa_vers()
        if ok: ok = self.set_datlevel(0)
        if ok: ok = self.set_instr()
        if ok: ok = self.set_dateObs()
        if ok: ok = self.set_ut() # may need to delete duplicate UTC?
#        if ok: ok = self.set_utend()
#        if ok: ok = self.set_numamps()
#        if ok: ok = self.set_numccds() # needed?
        if ok: ok = self.set_koaimtyp() # imagetyp
        if ok: ok = self.set_koaid()
#        if ok: ok = self.set_blank()
#        if ok: ok = self.fix_binning()
#        if ok: ok = self.set_ofName()
        if ok: ok = self.set_semester()
#        if ok: ok = self.set_wavelengths()
#        if ok: ok = self.set_instrument_status() # inststat
        if ok: ok = self.set_weather_keywords()
#        if ok: ok = self.set_image_stats_keywords() # IM* and PST*, imagestat
#        if ok: ok = self.set_npixsat(satVal=65535.0) # npixsat
#        if ok: ok = self.set_sig2nois()
#        if ok: ok = self.set_slit_values()
#        if ok: ok = self.set_gain_and_readnoise() # ccdtype
#        if ok: ok = self.set_skypa() # skypa
#        if ok: ok = self.set_subexp()
#        if ok: ok = self.set_roqual()
        if ok: ok = self.set_oa()
        if ok: ok = self.set_prog_info(progData)
        if ok: ok = self.set_propint(progData)
#        if ok: ok = self.fix_propint()
        return ok

    def get_dir_list(self):
        '''
        Function to generate the paths to all the NIRC2 accounts, including engineering
        Returns the list of paths
        '''
        dirs = []
        path = '/s/sdata90'
        for i in range(5):
            joinSeq = (path, str(i), '/nirc')
            path2 = ''.join(joinSeq)
            for j in range(1,11):
                joinSeq = (path2, str(j))
                path3 = ''.join(joinSeq)
                dirs.append(path3)
            joinSeq = (path2, '2eng')
            path3 = ''.join(joinSeq)
            dirs.append(path3)
        return dirs

    def get_prefix(self):
        if self.get_keyword('INSTRUME') == self.instr:
            prefix = 'N2'
        else:
            prefix = ''
        return prefix

    def set_instr(self):
        '''
        Check OUTDIR to verify NIRC2 and add INSTRUME
        '''

        self.log.info('set_instr: setting INSTRUME to NIRC2')
        if 'nirc' in self.get_keyword('OUTDIR'):
            #update instrument
            self.set_keyword('INSTRUME', 'NIRC2', 'KOA: Instrument')

        return True

    def set_koaimtyp(self):
        '''
        Add KOAIMTYP based on algorithm
        Calls get_koaimtyp for algorithm
        '''

        koaimtyp = self.get_koaimtyp()
        
        #warn if undefined
        if (koaimtyp == 'undefined'):
            self.log.info('set_koaimtyp: Could not determine KOAIMTYP value')

        #update keyword
        self.set_keyword('KOAIMTYP', koaimtyp, 'KOA: Image type')
        
        return True

        
    def get_koaimtyp(self):
        '''
        Sets koaimtyp based on keyword values
        '''
        #define python replica of IDL strtrim
        strtrim = lambda x: x.replace(' ','')

        grsname = strtrim(self.get_keyword('GRSNAME'))
        shrname = strtrim(self.get_keyword('SHRNAME'))
        obsfname = strtrim(self.get_keyword('OBSFNAME'))
        domestat = strtrim(self.get_keyword('DOMESTAT'))
        axestat = strtrim(self.get_keyword('AXESTAT'))

        imagetyp = 'undefined'
        #shutter open
        if shrname == 'open':
            if obsfname == 'telescope':
                imagetyp = 'object'
            if (obsfname == 'telescope') and (domestat != 'tracking') and (axestat != 'tracking'):
                if grsname != 'clear':
                    imagetyp = 'telTBD'
                    return imagetyp
                #if domelamps keyword exists
                if (strtrim(self.get_keyword('FLIMAGIN'))):
                    flspectr = strtrim(self.get_keyword('FLSPECTR'))
                    flimagin = strtrim(self.get_keyword('FLIMAGIN'))
                    if flimagin == 'on' or flspectr == 'on':
                        imagetyp = 'flatlamp'
                    else:
                        imagetyp = 'flatlampoff'
                #else check EL, AXESTAT, and DOMESTAT instead
                else:
                    el = float(self.get_keyword('EL'))
                    if (el > 44.99 and el < 45.01) and (domestat != 'tracking' and axestat != 'tracking'):
                        imagetyp = 'flatTBD'
            #arclamp
            elif obsfname == 'telsim':
                if self.get_keyword('ARGONPWR'):
                    #get element power boolean
                    argonpwr = strtrim(self.get_keyword('ARGONPWR'))
                    xenonpwr = strtrim(self.get_keyword('XENONPWR'))
                    kryptpwr = strtrim(self.get_keyword('KRYPTPWR'))
                    neonpwr = strtrim(self.get_keyword('NEONPWR'))
                    lamppwr = strtrim(self.get_keyword('LAMPPWR'))
                    #compare dates for special logic after 2011-10-10
                    dateobs = strtrim(self.get_keyword('DATE-OBS'))
                    date = dateobs.split('-')
                    dateval = dt.date(date[0],date[1],date[2])
                    dlmpvalid = dt.date(2011,10,10)
                    if dateval > dlmpvalid:
                        if lamppwr == 1:
                            imagetyp = 'flatlamp'
                        elif 1 in [argonpwr,xenonpwr,kryptpwr,neonpwr]:
                            imagetyp = 'arclamp'
                        else:
                            imagetyp = 'specTBD'

                        print('Image Type: ',imagetyp)
                        print('Lamp Power: ',lamppwr)
                        print('Ne: ',neonpwr)
                        print('Ar: ',argonpwr)
                        print('Kr: ',kryptpwr)
                        print('Xe: ',xenonpwr)
            #use grsname keyword instead
            else:
                if grsname in ['lowres','medres','GRS1','GRS2']:
                    imagetyp = 'specTBD'
        #dark or bias
        elif shrname == 'closed':
            itime = strtrim(self.get_keyword('ITIME'))
            if itime == 0.0:
                imagetyp = 'bias'
            else:
                imagetyp = 'dark'
            print('Image Type: ',imagetyp)
        
        return imagetyp
