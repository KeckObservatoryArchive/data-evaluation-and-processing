'''
This is the class to handle all the KCWI specific attributes
KCWI specific DR techniques can be added to it in the future

01/31/2020 E. Lucas - Updated functions
12/14/2017 M. Brown - Created initial file
'''

import instrument
import datetime as dt
import numpy as np

class Kcwi(instrument.Instrument):
    def __init__(self, instr, utDate, rootDir, log=None):
        # Call the parent init to get all the shared variables
        super().__init__(instr, utDate, rootDir, log)
        # Other vars that subclass can overwrite
        self.endTime = '19:00:00'   # 24 hour period start/end time (UT)
        self.sdataList = self.get_dir_list()

    def get_dir_list(self):
        '''
        Function to generate the paths to all the KCWI accounts, including engineering
        Returns the list of paths
        '''
        dirs = []
        path = '/s/sdata1400/kcwi'
        for i in range(1,10):
            joinSeq = (path, str(i))
            path2 = ''.join(joinSeq)
            dirs.append(path2)
        joinSeq = (path, 'dev')
        path2 = ''.join(joinSeq)
        dirs.append(path2)
        return dirs

    def get_prefix(self):
        instr = self.get_instr()
        if instr == 'kcwi':
            try:
                camera = self.get_keyword('CAMERA').lower()
                if camera == 'blue':
                    prefix = 'KB'
                elif camera == 'red':
                    prefix = 'KR'
                elif camera == 'fpc':
                    prefix = 'KF'
                else:
                    prefix = ''
            except:
                prefix = ''
        else:
            prefix = ''
        return prefix

    def run_dqa_checks(self, progData):
        '''
        Run all DQA checks unique to this instrument.
        '''

        #todo: check that all of these do not need a subclass version if base class func was used.
        ok = True
        self.log.info(self.get_keyword('OFNAME'))
        if ok: ok = self.set_instr()
        if ok: ok = self.set_telescope()
        if ok: ok = self.set_filename()
        if ok: ok = self.set_elaptime()
        if ok: ok = self.set_dateObs()
        if ok: ok = self.set_utc()
        if ok: ok = self.set_koaid()
        if ok: ok = self.set_koaimtyp()
        
        # if ok: ok = self.set_ut()
        if ok: ok = self.set_frameno()
        if ok: ok = self.set_semester()
        if ok: ok = self.set_prog_info(progData)
        if ok: ok = self.set_propint(progData)
        if ok: ok = self.set_datlevel(0)
        if ok: ok = self.set_image_stats_keywords()
        if ok: ok = self.set_weather_keywords()
        if ok: ok = self.set_oa()
        if ok: ok = self.set_npixsat(satVal=65535)
        if ok: ok = self.set_slit_dims()
        if ok: ok = self.set_wcs()
        if ok: ok = self.set_dqa_vers()
        if ok: ok = self.set_dqa_date()
        return ok
    
    def set_filename(self):
        self.keywordMap['OFNAME'] = 'OFNAME'
        return True

    def set_telescope(self):
        self.set_keyword('TELESCOP','Keck II','KOA: Telescope name')
        return True

    def set_utc(self):
        try:
            self.set_keyword('UTC',self.get_keyword('UT'),'KOA: Coordinated Universal Time')
        except:
            self.log.info('set_utc (KCWI): Could not set UTC from UT')
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
        self.set_keyword('IMAGETYP', koaimtyp, 'KOA: Image type')
        self.set_keyword('KOAIMTYP', koaimtyp, 'KOA: Image type')
        
        return True

        
    def get_koaimtyp(self):
        '''
        Sets koaimtyp based on keyword values
        '''
        koaimtyp = 'undefined'
        try:
            camera = self.get_keyword('CAMERA').lower()
        except:
            camera = ''
        if camera == 'fpc':
            koaimtyp = 'fpc'
        elif self.get_keyword('XPOSURE') == 0.0:
            koaimtyp = 'bias'
        elif self.get_keyword('IMTYPE'):
            koaimtyp = self.get_keyword('IMTYPE').lower()
        
        # self.log.info(self.get_keyword('FILENAME'))
        # self.log.info(self.get_keyword('KOAID'))
        # self.log.info(f"XPOS {self.get_keyword('XPOSURE')} CAM {self.get_keyword('CAMERA')} IMTYPE {self.get_keyword('IMTYPE')} >>>>>> KOAIMTYP {koaimtyp}")
        return koaimtyp

    def set_elaptime(self):
        '''
        Fixes missing ELAPTIME keyword.
        '''

        itime  = self.get_keyword('ITIME')
        coadds = self.get_keyword('COADDS')
        #use elaptime if set, otherwise check other keywords
        if self.get_keyword('ELAPTIME') is not None:
            elaptime = self.get_keyword('ELAPTIME')
        elif self.get_keyword('EXPTIME') is not None:
            elaptime = self.get_keyword('EXPTIME')
            self.log.info('set_elaptime: Setting ELAPTIME from EXPTIME')
        elif self.get_keyword('XPOSURE') is not None:
            elaptime = self.get_keyword('XPOSURE')
            self.log.info('set_elaptime: Setting ELAPTIME from XPOSURE')
        elif itime != None and coadds != None:
            elaptime = round(itime*coadds,4)
            self.log.info('set_elaptime: Setting ELAPTIME from ITIME*COADDS')
        else:
            elaptime = ''
            self.log.warning('set_elaptime: no methods possible for setting elaptime')
        self.set_keyword('ELAPTIME', elaptime, 'KOA: Total integration time')
        return True

    def set_slit_dims(self):
        waveblue = 'null'
        wavecntr = 'null'
        wavered  = 'null'
        specres  = 'null'
        dispscal = 'null'
        slitwidt = 'null'
        slitlen  = 'null'
        spatscal = 'null'

        slicer = self.get_keyword('IFUNAM').lower()
        camera = self.get_keyword('CAMERA')
        try:
            camera = camera.lower()
        except:
            pass
        binning = self.get_keyword('BINNING')
        gratname = self.get_keyword('BGRATNAM').lower()
        nodmask = self.get_keyword('BNASNAM').lower()
        # print(gratname,slicer,camera)
        # Configuration for KB
        #
        configurations = {'bl' : {'waves':(3500, 4550, 5600), 'large':900, 'medium':1800, 'small':3600},
                  'bm' : {'waves':(3500, 4500, 5500), 'large':2000, 'medium':4000, 'small':8000},
                  'bh3' : {'waves':(4700, 5150, 5600), 'large':4500, 'medium':9000, 'small':18000},
                  'bh2' : {'waves':(4000, 4400, 4800), 'large':4500, 'medium':9000, 'small':18000},
                  'bh1' : {'waves':(3500, 3800, 4100), 'large':4500, 'medium':9000, 'small':18000}
                 }
        #
        # Slit width by slicer, slit length is always 20.4"
        #
        slits = {'large':'1.35', 'medium':'0.69', 'small':'0.35'}
        if slicer in slits.keys():
            slitwidt = slits[slicer]
            slitlen = 20.4

        if gratname in configurations.keys() and slicer in slits.keys():
            waveblue = configurations.get(gratname)['waves'][0]
            wavecntr = configurations.get(gratname)['waves'][1]
            wavered = configurations.get(gratname)['waves'][2]
            specres = configurations.get(gratname)[slicer]
            if nodmask == "mask":
                diff = int((wavered - waveblue)/3)
                diff = int(math.ceil(diff/100.0)*100)
                waveblue = wavecntr - diff
                wavered = wavecntr + diff
        #
        # Camera plate scale, arcsec/pixel unbinned
        #
        pscale = {'fpc':0.0075, 'blue':0.147}
        if camera in pscale.keys():
            # print(pscale.get(camera),binning)
            try:
                dispscal = pscale.get(camera) * binning
            except:
                dispscal = pscale.get(camera) * int(binning.split(',')[0])
            spatscal = dispscal
            if camera == 'fpc':
                waveblue = 3700
                wavecntr = 6850
                wavered = 10000

        self.set_keyword('WAVEBLUE',waveblue,'KOA: Blue end wavelength')
        self.set_keyword('WAVECNTR',wavecntr,'KOA: Central wavelength')
        self.set_keyword('WAVERED',wavered,'KOA: Red end wavelength')
        self.set_keyword('SPECRES',specres,'KOA: Nominal spectral resolution')
        self.set_keyword('SPATSCAL',spatscal,'KOA: CCD pixel scale, spatial')
        self.set_keyword('DISPSCAL',dispscal,'KOA: CCD pixel scale, dispersion')
        self.set_keyword('SLITWIDT',slitwidt,'KOA: Slit width on sky')
        self.set_keyword('SLITLEN',slitlen,'KOA: Slit length on sky')

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
            if ((key_val != 'ECHANGL' and key_val != 'XDANGL') and 
                (not self.get_keyword(key_val) or self.get_keyword(key_val) == 0)):
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
                self.log.error('set_wavelengths: could not determine xdispers')
                return False


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

    def set_wcs(self):
        #---------------------------
        # extract values from header
        #---------------------------
        camera = self.get_keyword('CAMERA')
        if camera != 'fpc':
            self.log.info(f'set_wcs: WCS keywords not set for camera type: {camera}')
            return True
        rakey = (self.get_keyword('RA')).split(':')
        rakey = 15.0*(float(rakey[0])+(float(rakey[1])/60.0)+(float(rakey[2])/3600.0))
        deckey = (self.get_keyword('DEC')).split(':')
        if float(deckey[0]) < 0:
            deckey = float(deckey[0])-(float(deckey[1])/60.0)-(float(deckey[2])/3600.0)
        else:
            deckey = float(deckey[0])+(float(deckey[1])/60.0)+(float(deckey[2])/3600.0)
        equinox = self.get_keyword('EQUINOX')
        naxis1 = self.get_keyword('NAXIS1')
        naxis2 = self.get_keyword('NAXIS2')
        pa = self.get_keyword('ROTPOSN')
        rotmode = self.get_keyword('ROTMODE')
        parantel = self.get_keyword('PARANTEL')
        parang = self.get_keyword('PARANG')
        el = self.get_keyword('EL')
        binning = self.get_keyword('BINNING')
        
        #---------------------------------------------
        # special PA calculation determined by rotmode
        # pa = rotposn + parantel - el
        #---------------------------------------------
        mode = rotmode[0:4]
        if parantel == '' or parantel == None:
            parantel = parang
        if mode == 'posi':
            pa1 = float(pa)
        elif mode == 'vert':
            pa1 = float(pa)+float(parantel)
        elif mode == 'stat':
            pa1 = float(pa)+float(parantel)-float(el)
        else:
            self.log.warning(f'set_wcs: indeterminate mode {mode}')
            return False

        #---------------------------
        # extract values from header
        #---------------------------
        raindeg = 1
        pixscale = 0.0075 * float(binning)
        pa0 = 0.7
        crval1 = rakey
        crval2 = deckey

        pa = -(pa1 - pa0)*np.pi/180.0
        cd1_1 = -pixscale*np.cos(pa)/3600.0
        cd2_2 = pixscale*np.cos(pa)/3600.0
        cd1_2 = -pixscale*np.sin(pa)/3600.0
        cd2_1 = -pixscale*np.sin(pa)/3600.0

        cd1_1 = '%18.7e' % cd1_1
        cd2_2 = '%18.7e' % cd2_2
        cd1_2 = '%18.7e' % cd1_2
        cd2_1 = '%18.7e' % cd2_1

        pixscale = '%8.6f' % pixscale
        crpix1 = (float(naxis1)+1.0)/2.0
        crpix2 = (float(naxis2)+1.0)/2.0
        crpix1 = '%8.2f' % crpix1
        crpix2 = '%8.2f' % crpix2
        #--------------
        # check equinox
        #--------------
        if float(equinox) == 2000.0:
            radecsys = 'FK5'
        else:
            radecsys = 'FK4'
        
        self.set_keyword('CD1_1',cd1_1,'KOA: WCS coordinate transformation matrix')
        self.set_keyword('CD1_2',cd1_2,'KOA: WCS coordinate transformation matrix')
        self.set_keyword('CD2_1',cd2_1,'KOA: WCS coordinate transformation matrix')
        self.set_keyword('CD2_2',cd2_2,'KOA: WCS coordinate transformation matrix')
        self.set_keyword('CRPIX1',crpix1,'KOA: Reference pixel')
        self.set_keyword('CRPIX2',crpix2,'KOA: Reference pixel')
        self.set_keyword('CRVAL1',crval1,'KOA: Reference pixel value')
        self.set_keyword('CRVAL2',crval2,'KOA: Reference pixel value')
        self.set_keyword('RADECSYS',radecsys,'KOA: WCS coordinate system')
        self.set_keyword('CTYPE1','RA---TAN','KOA: WCS type of the horizontal coordinate')
        self.set_keyword('CTYPE2','DEC--TAN','KOA: WCS type of the vertical coordinate')
        
        return True

