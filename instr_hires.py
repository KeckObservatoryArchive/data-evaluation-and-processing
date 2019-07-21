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
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
from astropy.visualization import ZScaleInterval, AsinhStretch
from astropy.visualization.mpl_normalize import ImageNormalize

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
        Remove spaces from BINNING value and update self.get_keyword
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

        #set pixel and CCD size
        psize = 0.015
        npix = 3072.0

        #make sure stages are homed
        if not self.get_keyword('XDISPERS'):
            xdispers = 'RED'
        else:
            xdispers = self.get_keyword('XDISPERS').strip()

        keyflag=1
        keyvars = ['','','','','']
        for key_i,key_val in enumerate(['XDCAL','ECHCAL','XDSIGMAI','XDANGL','ECHANGL']):
            if not self.get_keyword(key_val) or self.get_keyword(key_val) == 0:
                keyflag = 0
            else:
                keyvars[key_i] = self.get_keyword(key_val)
            
        xdcal = keyvars[0]
        echcal = keyvars[1]
        xdsigmai = keyvars[2]
        xdangl = keyvars[3]
        echangl = keyvars[4]
            
        if keyflag == 1:
            #specifications, camera-collimator, blaze, cal offset angles
            camcol = 40.*np.pi/180.
            blaze = -4.38*np.pi/180.
            offset = 25.0-0.63 #0-order + 5deg for home

            #grating equation
            alpha = (xdangl+offset)*np.pi/180.
            d = 10.**7/xdsigmai #microns
            waveeq = lambda x,y,z: x*((1.+np.cos(y))*np.sin(z)-np.sin(y)*np.cos(z))
            wavecntr = waveeq(d,camcol,alpha)
            ccdangle = np.arctan2(npix*psize,(1.92*762.0)) #f = 762mm, psize u pix, 1.92 amag

            #blue end
            alphab = alpha - ccdangle
            waveblue = waveeq(d,camcol,alphab) 

            #red end
            alphar = alpha + ccdangle
            wavered = waveeq(d,camcol,alphar)

            #center, get non-decimal part of number
            wavecntr = np.fix(wavecntr)
            waveblue = np.fix(waveblue)
            wavered = np.fix(wavered)

            #get the correct equation constants
            if xdispers == 'RED':
                #order 62, 5748 A, order*wave = const
                const = 62.0 * 5748.0
                a = float(1.4088)
                b = float(-306.6910)
                c = float(16744.1946)
                
            if xdispers == 'UV':
                #order 97, 3677 A, order*wave = const
                const = 97.0 * 3677.0
                a = float(0.9496)
                b = float(-266.2792)
                c = float(19943.7496)
                
            if xdispers == '':
                return


            #correct wavelength values
            for i in [wavecntr,waveblue,wavered]:
                #find order for wavecntr
                wave = i
                order = np.floor(const/wave)
                trycount = 1
                okflag = 0
                while okflag == 0:
                    #find shift in Y: order 62 =npix with XD=ECH=0(red)
                    #                 order 97 =npix with XD=ECH=0(blue)
                    if i == wavecntr:
                        shift = a*order**2 + b*order + c
                        newy = npix - shift
                        newy = -newy
                        okflag = 1
                        
                    else:
                        shift2 = a*order**2 + b*order + c
                        
                        newy2 = shift2 - newy
                        if newy2 < 120:
                            order = order -1
                            trycount += 1
                            okflag=0
                            if trycount < 100:
                                continue
                        npix2 = 2*npix

                        if newy2 > npix2:
                            order = order + 1
                            trycount += 1
                            okflag=0
                            if trycount < 100:
                                continue
                        if trycount > 100 or newy2 > 120 or newy2 > npix2:
                            okflag=1
                            break

                #find delta wave for order
                dlamb = -0.1407*order + 18.005
                #new wavecenter = central wavelength for this order
                wave = const/order
                #correct for echangl
                wave = wave + (4*dlamb*echangl)
                #round to nearest 10 A
                wave2 = wave % 10 # round(wave,-1)
                if wave2 < 5:
                    wave = wave - wave2
                else:
                    wave = wave + (10-wave2)
                if wave < 2000 or wave > 20000:
                    wave = 'null'
                if i == wavecntr:
                    wavecntr = wave
                elif i == waveblue:
                    waveblue = wave
                elif i == wavered:
                    wavered = wave

            wavecntr = int(round(wavecntr,-1))
            waveblue = int(round(waveblue,-1))
            wavered = int(round(wavered,-1))
        else:
            wavecntr = 'null'
            waveblue = 'null'
            wavered = 'null'
            
        self.set_keyword('WAVECNTR',wavecntr,'Wave Center')
        self.set_keyword('WAVEBLUE',waveblue,'Wave Blue')
        self.set_keyword('WAVERED',wavered,'Wave Red')        

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
        '''
        Adds mean, median, std keywords to header
        '''

        # Can be up to 6 extensions
        for ext in range(1, 7):
            imageStd = imageMean = imageMedian = 'null'
            postStd = postMean = postMedian = 'null'
            precol  = self.get_keyword('PRECOL')
            postpix = self.get_keyword('POSTPIX')
            if ext < len(self.fitsHdu):
                image = self.fitsHdu[ext].data
                # postpix boundary
                x = len(image) - postpix
                # image area
                start = precol + int(x*0.10)
                end   = x - int(x*0.10)
                imageStd    = float("%0.2f" % np.std(image[start:end, :]))
                imageMean   = float("%0.2f" % np.mean(image[start:end, :]))
                imageMedian = float("%0.2f" % np.median(image[start:end, :]))
                if postpix != None:
                    # postscan area
                    start = x + int(postpix*0.10)
                    end   = -1 * int(postpix*0.10)
                    postStd    = float("%0.2f" % np.std(image[start:end, :]))
                    postMean   = float("%0.2f" % np.mean(image[start:end, :]))
                    postMedian = float("%0.2f" % np.median(image[start:end, :]))

            key = str(ext).zfill(2)
            key_mn = 'IM01MN' + key
            key_md = 'IM01MD' + key
            key_sd = 'IM01SD' + key
            self.set_keyword(key_mn,  imageMean,   'KOA: Image data mean')
            self.set_keyword(key_sd,  imageStd,    'KOA: Image data standard deviation')
            self.set_keyword(key_md,  imageMedian, 'KOA: Image data median')
            key_mn = 'PT01MN' + key
            key_md = 'PT01MD' + key
            key_sd = 'PT01SD' + key
            self.set_keyword(key_mn,  postMean,   'KOA: Postscan data mean')
            self.set_keyword(key_sd,  postStd,    'KOA: Postscan data standard deviation')
            self.set_keyword(key_md,  postMedian, 'KOA: Postscan data median')

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


    def make_jpg(self):
        '''
        Converts HIRES FITS file to JPG image
        Output filename = KOAID_CCD#_HDU##.jpg
            # = 1, 2, 3...
            ## = 01, 02, 03...
        '''

        # TODO: Can we merge this with instrument.make_jpg()?

        # file to convert is lev0Dir/KOAID

        koaid = self.get_keyword('KOAID')
        filePath = ''
        for root, dirs, files in os.walk(self.dirs['lev0']):
            if koaid in files:
                filePath = ''.join((root, '/', koaid))
        if not filePath:
            self.log.error('make_jpg: Could not find KOAID: ' + koaid)
            return False
        self.log.info('make_jpg: converting {} to jpeg format'.format(filePath))

        koaid = filePath.replace('.fits', '')

        if os.path.isfile(filePath):
            for ext in range(1, len(self.fitsHdu)):
                try:
                    ext2 = str(ext)
                    pngFile = koaid+'_CCD'+ext2+'_HDU'+ext2.zfill(2)+'.png'
                    jpgFile = pngFile.replace('.png', '.jpg')
                    # image data to convert
                    image = self.fitsHdu[ext].data
                    interval = ZScaleInterval()
                    vmin, vmax = interval.get_limits(image)
                    norm = ImageNormalize(vmin=vmin, vmax=vmax, stretch=AsinhStretch())
                    plt.imshow(image, cmap='gray', origin='lower', norm=norm)
                    plt.axis('off')
                    # save as png, then convert to jpg
                    plt.savefig(pngFile)
                    Image.open(pngFile).convert('RGB').rotate(-90).save(jpgFile)
                    os.remove(pngFile)
                    plt.close()
                except:
                    self.log.error('make_jpg: Could not create JPG: ' + jpgFile)
        else:
            self.log.error('make_jpg: file does not exist {}'.format(filePath))
            return False

        return True
