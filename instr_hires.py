'''
This is the class to handle all the HIRES specific attributes
HIRES specific DR techniques can be added to it in the future

12/14/2017 M. Brown - Created initial file
'''

import instrument
import datetime as dt
from common import *
from math import ceil, floor
import numpy as np

class Hires(instrument.Instrument):
    def __init__(self, instr, utDate, rootDir, log=None):

        # Call the parent init to get all the shared variables
        super().__init__(instr, utDate, rootDir, log)

        # Set any unique keyword index values here
        self.keywordMap['OFNAME'] = ''
        self.keywordMap['FRAMENO'] = ''

        # Other vars that subclass can overwrite
        self.endTime = '20:00:00'  # 24 hour period start/end time (UT)

        # Generate the paths to the HIRES datadisk accounts
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
        if ok: ok = self.set_ut() # may need to delete duplicate UTC?
#        if ok: ok = self.set_numamps()
#        if ok: ok = self.set_numccds() # needed?
#        if ok: ok = self.set_elaptime()
        if ok: ok = self.set_koaimtyp() # imagetyp
        if ok: ok = self.set_koaid()
        if ok: ok = self.set_blank()
        if ok: ok = self.fix_binning()
        if ok: ok = self.set_frameno()
        if ok: ok = self.set_ofName()
        if ok: ok = self.set_semester()
        if ok: ok = self.set_wavelengths() # lambda_xd
        if ok: ok = self.set_instrument_status() # inststat
        if ok: ok = self.set_weather_keywords()
        if ok: ok = self.set_image_stats_keywords() # IM* and PST*, imagestat
#        if ok: ok = self.set_npixsat(satVal=65535.0) # npixsat
        if ok: ok = self.set_sig2nois() # still needed?
        if ok: ok = self.set_slit_values() # slitsize
        if ok: ok = self.set_gain_and_readnoise() # ccdtype
        if ok: ok = self.set_skypa() # skypa
        if ok: ok = self.set_subexp() # subexp
        if ok: ok = self.set_oa()
        if ok: ok = self.set_prog_info(progData)
        if ok: ok = self.set_propint(progData)
        if ok: ok = self.fix_propint()

        return ok


    def get_dir_list(self):
        '''
        Function to generate the paths to all the HIRES accounts, including engineering
        Returns the list of paths
        '''
        dirs = []
        path = '/s/sdata12'
        for i in range(5,8):
            joinSeq = (path, str(i), '/hires')
            path2 = ''.join(joinSeq)
            for j in range(1,10):
                joinSeq = (path2, str(j))
                path3 = ''.join(joinSeq)
                dirs.append(path3)
            joinSeq = (path2, 'eng')
            path3 = ''.join(joinSeq)
            dirs.append(path3)
        return dirs

    def get_prefix(self):
        '''
        Set prefix to HI if this is a HIRES file
        '''

        instr = self.get_keyword('INSTRUME')
        if 'hires' in instr.lower():
            prefix = 'HI'
        else:
            prefix = ''
        return prefix


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
        self.set_keyword('IMAGETYP', koaimtyp, 'KOA: Image type')
        self.set_keyword('KOAIMTYP', koaimtyp, 'KOA: Image type')
        
        return True

        
    def get_koaimtyp(self):
        '''
        Sets koaimtyp based on keyword values
        '''
        
        koaimtyp = 'undefined'
        if self.get_keyword('AUTOSHUT', False) == None: return koaimtyp
        if self.get_keyword('LAMPNAME', False) == None: return koaimtyp
        if self.get_keyword('LMIRRIN', False) == None:  return koaimtyp
        if self.get_keyword('DARKCLOS', False) == None: return koaimtyp
        if self.get_keyword('TTIME', False) == None:    return koaimtyp

        lampname = self.get_keyword('LAMPNAME', False)
        ttime = self.get_keyword('TTIME', False)
        
        if self.get_keyword('AUTOSHUT', False) == 0:
            lampOn = ''
            if lampname != 'none' and (lmirrin != 0 or darkclos != 1):
                lampOn = '_lamp_on'
            if ttime == 0: koaimtyp = ''.join(('bias', lampOn))
            else:          koaimtyp = ''.join(('dark', lampOn))
            return koaimtyp

        deckname = self.get_keyword('DECKNAME', False)
        catcur1 = self.get_keyword('CATCUR1', False)
        catcur2 = self.get_keyword('CATCUR2', False)
        hatclos = self.get_keyword('HATCLOS', False)

        if deckname == None or catcur1 == None or catcur2 == None or hatclos == None:
            return koaimtyp

        lmirrin = self.get_keyword('LMIRRIN', False)
        xcovclos = self.get_keyword('XCOVCLOS', False)
        ecovclos = self.get_keyword('ECOVCLOS', False)

        if 'quartz' in lampname:
            if deckname == 'D5':              koaimtyp = 'trace'
            else:                             koaimtyp = 'flatlamp'
            if lmirrin == 0 and hatclos == 0: koaimtyp = 'object_lamp_on'
            if lmirrin == 0 and hatclos == 1: koaimtyp = 'undefined'
            return koaimtyp
        elif 'ThAr' in lampname:
            if catcur1 >= 5.0:
                koaimtyp = 'arclamp'
                if deckname == 'D5': koaimtyp = 'focus'
            else: koaimtyp = 'undefined'
            if lmirrin == 0 and hatclos == 0:   koaimtyp = 'object_lamp_on'
            if lmirrin == 0 and hatclos == 1:   koaimtyp = 'undefined'
            if xcovclos == 1 and ecovclos == 1: koaimtyp = 'undefined'
            return koaimtyp
        elif 'undefined' in lampname:
            return 'undefined'

        if hatclos == 1:
            koaimtyp = 'dark'
            if ttime == 0: koaimtyp = 'bias'
            return koaimtyp
        
        if ttime == 0: return 'bias'
        
        return 'object'


    def set_blank(self):
        '''
        If BLANK keyword does not exist, create and set to -32768
        '''
        
        if self.get_keyword('Blank', False) != None: return True

        self.log.info('set_blank: Creating BLANK keyword with value -32768')

        #add keyword
        self.set_keyword('BLANK', -32768, 'KOA: ')
        
        return True


    def fix_binning(self):
        '''
        Remove spaces from BINNING value and update header
        '''

        binning = self.get_keyword('BINNING', False)

        if ' ' not in binning: return True

        self.log.info('fix_binning: BINNING value updated')
        comment = ' '.join*(('KOA: Keyword value changed from', binning))
        binning = binning.replace(' ', '')
        self.set_keyword('BINNING', binning, comment)

        return True


    def set_ofName(self):
        '''
        Sets OFNAME keyword from OUTFILE and FRAMENO
        '''

        outfile = self.get_keyword('OUTFILE', False)
        frameno = self.get_keyword('FRAMENO', False)
        if outfile == None or frameno == None:
            self.log.info('set_ofName: Could not detrermine OFNAME')
            ofname = ''
            return False
        
        frameno = str(frameno).zfill(4)
        ofName = ''.join((outfile, frameno, '.fits'))
        self.log.info('set_ofName: OFNAME = {}'.format(ofName))
        self.set_keyword('OFNAME', ofName, 'KOA: Original file name')

        return True


    def set_wavelengths(self):
        '''
        Determine and set wavelength range of spectum
        '''


        return True



        waveblue = wavecntr = wavered = 'null'

        psize = 0.015 # pixel size
        npix = 3072.0 # ccd size
        
        # Make sure stages are homed
        xdcal = self.get_keyword('XDCAL', False)
        echcal = self.get_keyword('ECHCAL', False)
        xdsigmai = self.get_keyword('XDSIGMAI', False)
        xdangl = self.get_keyword('XDANGL', False)
        echangl = self.get_keyword('ECHANGL', False)
        xdispers = self.get_keyword('XDISPERS', default='')

        if xdcal != None and echcal != None and xdsigmai != None and xdangl != None and \
           echangl != None and xdcal != 0 and echcal != 0:

            # Determine XD groove spacing and HIRES angle setting
            camcol = 40.0 * np.pi() / 180.0 # camera-collimater angle
            blaze = -4.38 * np.pi() / 180.0 # blaze angle
            offset = 25.0 - 0.63            # 0-order + 5 deg for home
            # Grating equation
            alpha = (xdangl + offset) * np.pi() / 180.0
            d = 10000000.0 / xdsigmai # microns
            wavecntr = d * (( 1.0 + np.cos(camcol)) * np.sin(alpha) - np.sin(camcol) * np.cos(alpha))
            ccdangle = np.arctan(npix * psize / 1.92 / 762.0) # f = 762 mm, psize u pix, 1.92 amag
            alphab = alpha - ccdangle
            waveblue = d * ((1.0 + np.cos(camcol)) * np.sin(alphab) - np.sin(camcol) * np.cos(alphab))
            alphar = alpha + ccdangle
            wavered = d * ((1.0 + np.cos(camcol)) * np.sin(alphar) - np.sin(camcol) * np.cos(alphar))
            # Get equation constants
            if xdispers == 'RED':
                # Order 62, 5748 A, order * wave = const
                const = 62.0 * 5748.0
                a = 1.4088
                b = -306.6910
                c = 16744.1946
            elif xdispers == 'UV':
                # ORder 97, 3677A, order * wave = const
                const = 97.0 * 3677.0
                a = 0.9496
                b = -266.2792
                c = 19943.7496
            # Correct wavelengths
            order = floor((const / wavecntr))








            # Cast to integers
            waveblue = int(waveblue)
            wavecntr = int(wavecntr)
            wavered = int(wavered)

        return True


    def set_instrument_status(self):
        '''
        Determine instrument status from instrument configuration

        inststat = 1 (good)
        inststat = 0 (abnormal)
        inststat = -1 (missing keywords)
        '''

        self.log.info('set_instrument_status: Setting ...')

        inststat = 1
        koaimtyp = self.get_keyword('IMAGETYP', default='')
        
        # Is this a bias/dark?
        dark = 0
        if koaimtyp == 'bias' or koaimtyp == 'dark': dark = 1
        
        keyList = ['CAFCAL', 'COFCAL', 'DECKCAL', 'ECHCAL', 'FIL1CAL', 'FILE2CAL',
                   'LFILCAL', 'LSELCAL', 'SLITCAL', 'TVACAL', 'TVFCAL', 'TVF1CAL',
                   'TVF2CAL', 'XDCAL', 'TEMPDET']
        
        # All keywords have to exist
        for key in keyList:
            if self.get_keyword(key) == None:
                inststat = -1
                self.set_keyword('INSTSTAT', inststat, 'KOA: HIRES instrument status')
                return True

        # Any with value of 0 is abnormal
        for key in keyList:
            if self.get_keyword(key, default='') == '0':
                inststat = 0
                self.set_keyword('INSTSTAT', inststat, 'KOA: HIRES instrument status')
                return True

        # Check detector temperature
        tempdet = self.get_keyword('TEMPDET')
        if (tempdet < -135 or tempdet > -115) and (tempdet < 32 and tempdet > 33):
            inststat = 0

        # Check the optics covers
        keyList1 = ['C1CVOPEN', 'C2CVOPEN', 'ECOVOPEN', 'XCOVOPEN']
        keyList2 = ['C1CVCLOS', 'C2CVCLOS', 'ECOVCLOS', 'XCOVCLOS']
        
        for i in range(0, 3):
            if self.get_keyword(keyList1[i]) == None or self.get_keyword(keyList2[i]) == None:
                inststat = -1
                self.set_keyword('INSTSTAT', inststat, 'KOA: HIRES instrument status')
                return True

        for i in range(0, 3):
            open = 0
            if self.get_keyword(keyList1[i]) == 1 and self.get_keyword(keyList2[i]) == 0:
                open = 1
            if not open and not dark: inststat = 0

        # Collimator
        keyList = ['XDISPERS', 'BCCVOPEN', 'BCCVCLOS', 'RCCVOPEN', 'RCCVCLOS']
        for key in keyList:
            if self.get_keyword(key) == None:
                inststat = -1
                self.set_keyword('INSTSTAT', inststat, 'KOA: HIRES instrument status')
                return True
        xdispers = self.get_keyword('XDISPERS')
        
        xd = {'RED':['RCCVOPEN', 'RCCVCLOS'], 'BLUE':['BCCVOPEN', 'BCCVCLOS']}

        open = 0
        if xdispers == 'RED':
            if self.get_keyword(xd[xdispers][0]) == 1 and self.get_keyword(xd[xdispers][1]) == 0:
                open = 1
            if not open and not dark: inststat = 0

            # Hatch
            hatopen = self.get_keyword('HATOPEN')
            hatclos = self.get_keyword('HATCLOS')
            if hatopen == None or hatclos == None:
                inststat = -1
        else:
            open = 0
            if hatopen == 1 and hatclos == 0: open = 1
            if not open and koaimtyp == 'object': inststat = 0

        self.set_keyword('INSTSTAT', inststat, 'KOA: HIRES instrument status')
        return True

    
    def set_slit_values(self):
        '''
        Determine slit scales from decker name
        '''
        self.log.info('set_slit_values: Setting slit scale keywords')

        slitlen = slitwidt = spatscal = specres = 'null'
        f15PlateScale = 0.7235 # mm/arcsec
        lambdaRes     = 5019.5 # A, res blaze order 71
        ccdSpaScale   = 0.1194 # arcsec/pixel - legacy 0.191
        ccdDispScale  = 0.1794 # arcsec/pixel - legacy 0.287
        dispRes       = 0.0219 # A/pixel, res blaze order 71 - legacy 0.035
        deckname = self.get_keyword('DECKNAME', default='')
        binning = self.get_keyword('BINNING', default='')
        xbin, ybin = binning.split(',')
        slitwid = self.get_keyword('SLITWID', default='')
        slitwid /= f15PlateScale
        spatscal = ccdSpaScale * int(xbin)
        dispscal = ccdDispScale * int(ybin)

        # Decker names
        decker = {}
        decker['A1'] =  [0.300, slitwid]
        decker['A2'] =  [0.500, slitwid]
        decker['A3'] =  [0.750, slitwid]
        decker['A4'] =  [1.000, slitwid]
        decker['A5'] =  [1.360, slitwid]
        decker['A6'] =  [1.500, slitwid]
        decker['A7'] =  [2.000, slitwid]
        decker['A8'] =  [2.500, slitwid]
        decker['A9'] =  [3.000, slitwid]
        decker['A10'] = [4.000, slitwid]
        decker['A11'] = [5.000, slitwid]
        decker['A12'] = [10.00, slitwid]
        decker['A13'] = [20.00, slitwid]
        decker['A14'] = [40.00, slitwid]
        decker['A15'] = [80.00, slitwid]
        decker['B1'] =  [3.500, 0.574]
        decker['B2'] =  [7.000, 0.574]
        decker['B3'] =  [14.00, 0.574]
        decker['B4'] =  [28.00, 0.574]
        decker['B5'] =  [3.500, 0.861]
        decker['C1'] =  [7.000, 0.861]
        decker['C2'] =  [14.00, 0.861]
        decker['C3'] =  [28.00, 0.861]
        decker['C4'] =  [3.500, 1.148]
        decker['C5'] =  [7.000, 1.148]
        decker['D1'] =  [14.00, 1.148]
        decker['D2'] =  [28.00, 1.148]
        decker['D3'] =  [7.000, 1.722]
        decker['D4'] =  [14.00, 1.722]
        decker['D5'] =  [0.119, 0.179]
        decker['E1'] =  [1.000, 0.400]
        decker['E2'] =  [3.000, 0.400]
        decker['E3'] =  [5.000, 0.400]
        decker['E4'] =  [7.000, 0.400]
        decker['E5'] =  [1.000, 0.400]

        # If decker exists, determine slit values
        if deckname in decker.items():
            slitwidt = decker[deckname][1]
            slitlen = decker[deckname][0]
            prslwid = slitwidt / dispscal
            res = lambdaRes / (prslwid * dispRes * ybin)
            specres = res - (res % 100)
        else:
            self.log.info('set_slit_values: Unable to set slit scale keywords')

        self.set_keyword('SLITLEN', slitlen, 'KOA: Slit length projected on sky (arcsec)')
        self.set_keyword('SLITWIDT', slitlen, 'KOA: Slit width projected on sky (arcsec)')
        self.set_keyword('SPATSCAL', slitlen, 'KOA: CCD pixel scale (arcsec/pixel)')
        self.set_keyword('SPECRES', slitlen, 'KOA: Nominal spectral resolution')

        return True
    
    
    def set_gain_and_readnoise(self): # ccdtype
        '''
        Assign values for CCD gain and read noise
        '''
        self.log.info('set_gain: Setting ...')

        gain = {'low':[], 'high':[]}
        readnoise = {'low':[], 'high':[]}

        return True
    
    
    def set_skypa(self): # skypa
        '''
        Calculate the HIRES slit sky position angle
        '''

        # Detemine rotator, parallactic and elevation angles
        offset = 270.0
        irot2ang = self.get_keyword('IROT2ANG', False)
        parang = self.get_keyword('PARANG', False)
        el = self.get_keyword('EL', False)

        # Skip if one or more values not found
        if irot2ang == None or parang == None or el == None:
            self.log.info('set_skypa: Could not set skypa')
            return True

        skypa = (2.0 * float(irot2ang) + float(parang) + float(el) + offset) % (360.0)

        self.log.info('set_skypa: Setting skypa')
        self.set_keyword('SKYPA', round(skypa, 4), 'KOA: Position angle on sky (deg)')

        return True
    
    
    def set_subexp(self): # subexp
        '''
        Determine if file is part of a subexposure sequence
        '''
        self.log.info('set_subexp: Setting ...')

        return True

 
    def set_image_stats_keywords(self):
        return True


    def set_sig2nois(self):
        return True


    def fix_propint(self):
        '''
        HIRES needs PROPINT1, 2, 3 and PROPMIN
        '''

        if self.extraMeta['PROPINT']:
            self.log.info('fix_propint: Adding PROPINT1, PROPINT2 and PROPINT3')
            self.extraMeta['PROPINT1'] = self.extraMeta['PROPINT']
            self.extraMeta['PROPINT2'] = self.extraMeta['PROPINT']
            self.extraMeta['PROPINT3'] = self.extraMeta['PROPINT']
            self.extraMeta['PROPMIN'] = self.extraMeta['PROPINT']

        return True
