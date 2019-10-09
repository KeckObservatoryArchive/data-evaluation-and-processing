'''
This is the class to handle all the LRIS specific attributes
LRIS specific DR techniques can be added to it in the future

12/14/2017 M. Brown - Created initial file
'''

import instrument
import datetime as dt
import numpy as np

class Lris(instrument.Instrument):
    def __init__(self, instr, utDate, rootDir, log=None):
        # Call the parent init to get all the shared variables
        super().__init__(instr, utDate, rootDir, log)

        # Set the lris specific paths to anc and stage
        seq =(self.rootDir, '/LRIS/', self.utDate, '/anc')
        self.ancDir = ''.join(seq)
        seq = (self.rootDir, '/stage')
        self.stageDir = ''.join(seq)
        # Generate the paths to the LRIS datadisk accounts
        # self.paths = self.get_dir_list()


        # Other vars that subclass can overwrite
        #TODO: Ack! Looks like the old DEP has an hour difference between this value and the actual cron time!
        self.endTime = '20:00:00'   # 24 hour period start/end time (UT)


        # Generate the paths to the LRIS datadisk accounts
        self.sdataList = self.get_dir_list()

    def run_dqa_checks(self, progData):
        '''
        Run all DQA checks unique to this instrument.
        '''
        print('Running DQA checks')
        #todo: check that all of these do not need a subclass version if base class func was used.
        ok = True
        if ok: ok = self.set_instr()
        if ok: ok = self.set_dateObs()
        if ok: ok = self.set_utc()
        # self.get_dispmode(update=True)
        # self.get_camera(update=True)
        if ok: ok = self.set_koaimtyp()
        if ok: ok = self.set_koaid()
        if ok: ok = self.set_ut()
        if ok: ok = self.set_ofname()
        if ok: ok = self.set_frameno()
        if ok: ok = self.set_semester()
        if ok: ok = self.set_prog_info(progData)
        if ok: ok = self.set_propint(progData)
        if ok: ok = self.set_datlevel(0)
        # if ok: ok = self.set_image_stats_keywords()
        if ok: ok = self.set_weather_keywords()
        if ok: ok = self.set_oa()

        if ok: ok = self.set_numccds()
        if ok: ok = self.set_numamps()
        if ok: ok = self.get_nexten()
        for i in range(1,self.nexten+1):
            print(f'EXTENSION {i}')
            if ok: ok = self.set_npixsat(32768,ext=i)
        if ok: ok = self.set_obsmode()
        if ok: ok = self.set_wavelengths()

        # if ok: ok = self.set_ccdtype()
        if ok: ok = self.set_slit_dims()
        print('SLIT DIMS SUCCESSFUL')
        # if ok: ok = self.set_spatscal()
        # if ok: ok = self.set_dispscal()
        # if ok: ok = self.set_specres()
        if ok: ok = self.set_dqa_vers()
        if ok: ok = self.set_dqa_date()
        print('DQA SUCCESSFUL?')
        return ok

    def get_dir_list(self):
        '''
        Function to generate the paths to all the LRIS accounts, including engineering
        Returns the list of paths
        '''
        dirs = []
        path = '/s/sdata24'
        for i in range(1,4):
            path2 = path + str(i) + '/lris'
            for i in range(1,10):
                path3 = path2 + str(i)
                dirs.append(path3)
            dirs.append(path2 + 'eng')
        return dirs

    def get_prefix(self):
        instr = self.get_instr()
        if instr == 'lrisblue':
            prefix = 'LB'
        elif instr == 'lris':
            prefix = 'LR'
        else:
            prefix = ''
        return prefix

    def set_ofname(self):
        '''
        Sets OFNAME keyword from OUTFILE and FRAMENO
        '''

        outfile = self.get_keyword('OUTFILE', False)
        frameno = self.get_keyword('FRAMENO', False)
        if outfile == None or frameno == None:
            print('could not determine ofname')
            self.log.info('set_ofName: Could not detrermine OFNAME')
            ofname = ''
            return False
        
        frameno = str(frameno).zfill(4)
        ofName = ''.join((outfile, frameno, '.fits'))
        self.log.info('set_ofName: OFNAME = {}'.format(ofName))
        self.set_keyword('OFNAME', ofName, 'KOA: Original file name')

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
        imagetyp = 'undefined'
        try:
            instrume = self.get_keyword('INSTRUME')
        except:
            return 'undefined'
        #focus
        slitname = self.get_keyword('SLITNAME')
        outfile = self.get_keyword('OUTFILE')
        if (slitname == 'GOH_LRIS') or (outfile == 'rfoc') or (outfile == 'bfoc'):
            return 'focus'
        #bias
        elaptime = self.get_keyword('ELAPTIME')
        if elaptime == 0:
            return 'bias'
        #flat, dark, wave, object
        try:
            trapdoor = self.get_keyword('TRAPDOOR')
        except:
            return 'undefined'
        graname = self.get_keyword('GRANAME')
        grisname = self.get_keyword('GRISNAME')
        if trapdoor == 'open':
            #is lamp on?
            flimagin = self.get_keyword('FLIMAGIN')
            flspectr = self.get_keyword('FLSPECTR')
            flat1 = self.get_keyword('FLAMP1')
            flat2 = self.get_keyword('FLAMP2')
            #a lamp is on
            if 'on' in [flimagin,flspectr,flat1,flat2]:
                return 'flatlamp'
            else:
                #no lamp on
                if self.get_keyword('AUTOSHUT'):
                    calname = self.get_keyword('CALNAME')
                    if calname in ['ir','hnpb','uv']:
                        return 'polcal'
                    else:
                        return 'object'
                else:
                    return 'undefined'
        elif trapdoor == 'closed':
            #is lamp on?
            lamps = self.get_keyword('LAMPS')
            if lamps not in ['','0',None]:
                if '1' in lamps:
                    if lamps == '0,0,0,0,0,1':
                        return 'flatlamp'
                    else:
                        if instrume == 'LRIS':
                            if graname != 'mirror':
                                return 'arclamp'
                        elif instrume == 'LRISBLUE':
                            if grisname != 'clear':
                                return 'arclamp'
                else:
                    if lamps == '0,0,0,0,0,0':
                        return 'dark'
            else:
                mercury = self.get_keyword('MERCURY')
                neon = self.get_keyword('NEON')
                argon = self.get_keyword('ARGON')
                cadmium = self.get_keyword('CADMIUM')
                zinc = self.get_keyword('ZINC')
                halogen = self.get_keyword('HALOGEN')
                krypton = self.get_keyword('KRYPTON')
                xenon = self.get_keyword('XENON')
                feargon = self.get_keyword('FEARGON')
                deuterium = self.get_keyword('DEUTERI')

                if halogen == 'on':
                    return 'flatlamp'
                elif 'on' in [neon,argon,cadmium,zinc,krypton,xenon,feargon,deuterium]:
                    if instrume == 'LRIS':
                        if graname != 'mirror':
                            return 'arclamp'
                    elif instrume == 'LRISBLUE':
                        if grisname != 'clear':
                            return 'arclamp'
                elif all(element == 'off' for element in [neon,argon,cadmium,zinc,halogen,krypton,xenon,feargon,deuterium]):
                    return 'dark'

    def set_obsmode(self):
        grism = self.get_keyword('GRISNAME')
        grating = self.get_keyword('GRANAME')
        angle = self.get_keyword('GRANGLE')
        instr = self.get_keyword('INSTRUME')

        if instr == 'LRISBLUE':
            if ('cl' in grism) or ('NB' in grism):
                obsmode = 'IMAGING'
            else:
                obsmode = 'SPEC'
        elif instr == 'LRIS':
            if (grating == 'mirror'):
                obsmode = 'IMAGING'
            else:
                obsmode = 'SPEC'

        self.set_keyword('OBSMODE',obsmode,'KOA: Observation Mode (Imaging or Spec)')
        return True

    def set_wavelengths(self):
        instr = self.get_keyword('INSTRUME')
        # IMAGING #
        slitname = self.get_keyword('SLITNAME')
        obsmode = self.get_keyword('OBSMODE')
        print('obs',self.get_keyword('OBSMODE'))
        if obsmode == 'IMAGING':
            print('IMAGING',instr)
            if instr == 'LRIS':
                flt = self.get_keyword('REDFILT')
                wavearr = dict({'clear':[3500,9000],
                                'B':[3800,5300],
                                'V':[4800,6600],
                                'R':[5500,8200],
                                'Rs':[6000,7500],
                                'I':[6800,8400],
                                'GG495':[4800,4950],
                                'OG570':[5500,5700],
                                'RG850':[8200,8500],
                                'NB4000':[3800,4200],
                                'NB5390':[5350,5400],
                                'NB6741':[6700,6800],
                                'NB8185':[8150,8250],
                                'NB8560':[8500,8650],
                                'NB9135':[9100,9200],
                                'NB9148':[9050,9250],
                                'NB4325':[9050,9520]})
            elif instr == 'LRISBLUE':
                flt = self.get_keyword('BLUFILT')
                wavearr = dict({'clear':[3000,6500],
                                'U':[3050,4000],
                                'B':[3900,4900],
                                'V':[5800,6600],
                                'G':[4100,5300],
                                'SP580':[0,0],
                                'NB4170':[0,0]})
            if flt == 'Clear':
                flt = 'clear'
        else: #if spectroscopy mode
            print('SPECTROSCOPY',instr)
            if instr == 'LRIS':
                wlen = self.get_keyword('WAVELEN')
                grating = self.get_keyword('GRANAME')
                print('GRATING',grating)
                wavearr = dict({'150/7500':[wlen-12288/2,wlen+12288/2],
                                '300/5000':[wlen-6525/2,wlen+6525/2],
                                '400/8500':[wlen-4762/2,wlen+4762/2],
                                '600/5000':[wlen-3275/2,wlen+3275/2],
                                '600/7500':[wlen-3275/2,wlen+3275/2],
                                '600/10000':[wlen-3275/2,wlen+3275/2],
                                '831/8200':[wlen-2375/2,wlen+2375/2],
                                '900/5500':[wlen-2175/2,wlen+2175/2],
                                '1200/7500':[wlen-1638/2,wlen+1638/2],
                                '1200/9000':[wlen-1638/2,wlen+1638/2]})
                dateobs = self.get_keyword('DATE-OBS')
                date = dt.datetime.strptime(dateobs,'%Y-%M-%d')
                newthreshold = dt.datetime(2015,5,14)

                if date < newthreshold:
                    wavearr = dict({'150/7500':[wlen-9830/2,wlen+9830/2],
                                    '158/8500':[wlen-9830/2,wlen+9830/2],
                                    '300/5000':[wlen-5220/2,wlen+5220/2],
                                    '400/8500':[wlen-3810/2,wlen+3810/2],
                                    '600/5000':[wlen-2620/2,wlen+2620/2],
                                    '600/7500':[wlen-2620/2,wlen+2620/2],
                                    '600/10000':[wlen-2620/2,wlen+2620/2],
                                    '831/8200':[wlen-1900/2,wlen+1900/2],
                                    '900/5500':[wlen-1740/2,wlen+1740/2],
                                    '1200/7500':[wlen-1310/2,wlen+1310/2]})
            elif instr == 'LRISBLUE':
                grism = self.get_keyword('GRISNAME')
                print('GRISM',grism)
                slitmask = str(self.get_keyword('SLITMASK'))
                print(slitmask)
                #longslit
                if 'long_' in slitmask or 'pol_' in slitmask:
                    print('longslit')
                    wavearr = dict({'300/5000':[1570,7420],
                                    '400/3400':[1270,5740],
                                    '600/4000':[3010,5600],
                                    '1200/3400':[2910,3890]})
                else:
                    print('slitmask is int')
                    wavearr = dict({'300/5000':[2210,8060],
                                    '400/3400':[1760,6220],
                                    '600/4000':[3300,5880],
                                    '1200/3400':[3010,4000]})
            else:
                return False

        #dichroic cutoff
        dichname = self.get_keyword('DICHNAME')
        print('DICHROIC',dichname)
        if dichname == '460':
            minmax = 4874
        elif dichname == '500':
            minmax = 5091
        elif dichname == '560':
            minmax = 5696
        elif dichname == '680':
            minmax = 6800
        else:
            minmax = 0
        print('MINMAX',minmax)
        #determine wavelength range
        print(wavearr)
        if obsmode == 'IMAGING':
            print(flt)
            waveblue,wavered = wavearr.get(flt)
        elif obsmode == 'SPEC':
            try:
                print(grating)
                waveblue,wavered = wavearr.get(grating)
            except:
                print(grism)
                waveblue,wavered = wavearr.get(grism)
        if instr == 'LRIS':
            if waveblue < minmax:
                waveblue = minmax
        elif instr == 'LRISBLUE':
            if wavered > minmax:
                wavered = minmax
        wavered = np.round(wavered,-1)
        waveblue = np.round(waveblue,-1)
        wavecntr = (waveblue + wavered)/2
        print('R,C,B',wavered,wavecntr,waveblue)
        self.set_keyword('WAVERED',round(wavered,0),'KOA: Red wavelength')
        self.set_keyword('WAVEBLUE',round(waveblue,0),'KOA: Blue wavelength')
        self.set_keyword('WAVECNTR',round(wavecntr,0),'KOA: Center wavelength')

        return True

    def set_ccdtype(self):
        ccdgain = 'null'
        rdnoise = 'null'
        #gain
        gainblue = [1.55,1.56,1.63,1.70]
        rnblue = [3.9,4.2,3.6,3.6]
        gainred = [1.255,1.180,1.191,1.162]
        rnred = [4.64,4.76,4.54,4.62]
        #red or blue?
        instr = self.get_keyword('INSTRUME')
        if instr == 'LRISBLUE':
            gain = gainblue
            rn = rnblue
        elif instr == 'LRIS':
            gain = gainred
            rn = rnred
        print('AMPLOC',self.get_keyword('AMPLOC'))
        print(gain,rn)
        ccdgain = self.get_keyword('CCDGAIN')
        for ext in range(1, len(self.fitsHdu)):
            ccdgain = ccdgain.strip()
            print(ccdgain)
            amploc  = self.fitsHdu[ext].header['AMPLOC']
            if amploc != None and ccdgain != None:
                amploc = int(amploc.strip()) - 1

                ccdgn[ext] = gain[ccdgain][amploc]
                ccdrn[ext] = readnoise[ccdgain][amploc]
        print('ccdgn',ccdgn)
        print('ccdrn',ccdrn)
        #determine amp to use
        # EXT? #
        return True

    def set_sig2nois(self):
        '''
        Calculates S/N for middle CCD image
        '''

        self.log.info('set_sig2nois: Adding SIG2NOIS')

        numamps = self.get_numamps()

        # Middle extension
        ext = floor(len(self.fitsHdu)/2.0)
        image = self.fitsHdu[ext].data

        naxis1 = self.fitsHdu[ext].header['NAXIS1']
        naxis2 = self.fitsHdu[ext].header['NAXIS2']
        postpix = self.get_keyword('POSTPIX', default=0)
        precol = self.get_keyword('PRECOL', default=0)

        nx = (naxis2 - numamps * (precol + postpix))
        c = [naxis1 / 2, 1.17 * nx / 2]

        wsize = 10
        spaflux = []
        for i in range(wsize, int(naxis1)-wsize):
            spaflux.append(np.median(image[int(c[1])-wsize:int(c[1])+wsize, i]))

        maxflux = np.max(spaflux)
        minflux = np.min(spaflux)

        sig2nois = np.fix(np.sqrt(np.abs(maxflux - minflux)))

        self.set_keyword('SIG2NOIS', sig2nois, 'KOA: S/N estimate near image spectral center')

        return True

    def set_numamps(self):
        '''
        Determine number of amplifiers
        '''

        ampmode = self.get_keyword('AMPMODE', default='')
        if 'DUAL:A+B' in ampmode: numamps = 2
        elif ampmode == '':       numamps = 0
        else:                     numamps = 1

        self.set_keyword('NUMAMPS',numamps,'KOA: Number of amplifiers')
        return True

    def get_nexten(self):
        '''
        Determine number of FITS HDU extensions
        '''
        # numamps = self.get_keyword('NUMAMPS')
        # numccds = self.get_keyword('NUMCCDS')
        # try:
        #     self.nexten = numamps * numccds
        # except:
        #     self.nexten = 'undefined'
        self.nexten = len(self.fitsHdu)-1
        return True

    def set_imagestat(self):
        pass
        return True

    def set_wcs(self):
        pixelscale = 0.135 #arcsec
        hdu = self.fitsHdu.header
        rotposn = self.get_keyword('ROTPOSN')
        ra = self.get_keywrord('RA')
        dec = self.get_keyword('DEC')
        poname = self.get_keyword('PONAME')
        pixcorrect = lambda x: (x/pixelscale) + 1024

        #dictionary of xim and yim only
        podict = dict({'REF':[380.865,71.44],
                       'REFO':[-377.22,72.52],
                       'LRIS':[3.97,-309.82],
                       'slitb':[-14.41,-263.74],
                       'slitc':[31.85,-262.58],
                       'POL':[3.91,-273.12],
                       'LRISB':[-53.11,-310.54],
                       'PICKOFF':[27.95,-260.63],
                       'MIRA':[3.67,-300.34],
                       'BEDGE':[20.25,-260.68],
                       'TEDGE':[-0.65,-263.68],
                       'UNDEFINED':[-53.11,-320.54]})
        if poname not in podict.keys():
            poname = 'UNDEFINED'
        xim,yim = podict.get(poname)
        xcen = pixcorrect(yim+308.1)
        ycen = pixcorrect(3.4-xim)

        crpix1_arr = []
        crpix2_arr = []
        cdelt1_arr = []
        cdelt2_arr = []
        #for each FITS header extension, calculate CRPIX1/2 and CDELT1/2
        for i in range(1,len(self.nexten)):
            crpix1 = self.get_keyword('CRPIX1')
            crpix2 = self.get_keyword('CRPIX2')
            crval1 = self.get_keyword('CRVAL1')
            crval2 = self.get_keyword('CRVAL2')
            cd11 = self.get_keyword('CD1_1')
            cd22 = self.get_keyword('CD2_2')
            naxis1 = self.get_keyword('NAXIS1')
            naxis2 = self.get_keyword('NAXIS2')

            crpix1_arr[i] = crpix1 + ((xcen - crval1)/cd11)
            crpix2_arr[i] = crpix2 + ((ycen - crval2)/cd22)
            cdelt1_arr[i] = cd11 * pixelscale
            cdelt2_arr[i] = cd22 * pixelscale

        return True

    def set_skypa(self):
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

    def set_imagestats(self):
        #running into more extension issues
        return True

    def set_slit_dims(self):
        slitname = self.get_keyword('SLITNAME')
        if slitname in ['GOH_LRIS','direct']:
            return True
        spatscal = 0.135
        wavelen = self.get_keyword('WAVECNTR')
        slitdict = dict({'long_0.7':[175,0.7],
                         'long_1.0':[175,1.0],
                         'long_1.5':[175,1.5],
                         'long_8.7':[175,8.7],
                         'pol_1.0':[25,1.0],
                         'pol_1.5':[25,1.5]})
        try:
            [slitlen,slitwidt] = slitdict.get(slitname)
        except:
            slitlen,slitwidt = 'null','null'

        dispersion = 0
        fwhm = 0
        instr = self.get_keyword('INSTRUME')
        if instr ==  'LRIS':
            grating = self.get_keyword('GRANAME')
            gratdict = dict({'150/7500':[3.00,0],
                             '300/5000':[0,9.18],
                             '400/8500':[1.16,6.90],
                             '600/5000':[0.80,4.70],
                             '600/7500':[0.80,4.70],
                             '600/10000':[0.80,4.70],
                             '831/8200':[0.58,0],
                             '900/5500':[0.53,0],
                             '1200/7500':[0.40,0],
                             '1200/9000':[0.40,0]})
            try:
                [dispersion,fwhm] = gratdict.get(grating)
            except:
                dispersion,fwhm = 0,0
        elif instr == 'LRISBLUE':
            grism = self.get_keyword('GRISNAME')
            grismdict = dict({'300/5000':[1.43,8.80],
                              '400/3400':[1.09,6.80],
                              '600/4000':[0.63,3.95],
                              '1200/3400':[0.24,1.56]})
            [dispersion,fwhm] = grismdict.get(grism)
        specres = 'null'
        slit = 1.0
        if slitwidt != 'null':
            slit = slitwidt
        slitpix = slit/spatscal
        deltalam = dispersion * slitpix
        if dispersion != 0:
            specres = round(wavelen/deltalam,-1)
        if fwhm != 0:
            specres = round((wavelen/fwhm)/slit,-2)
        self.set_keyword('SLITLEN',slitlen,'KOA: Slit length')
        self.set_keyword('SLITWIDT',slitwidt,'KOA: Slit width')
        self.set_keyword('SPECRES',specres,'KOA: Spectral resolution')
        self.set_keyword('SPATSCAL',spatscal,'KOA: Spatial resolution')

        return True
