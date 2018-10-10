'''
This is the class to handle all the MOSFIRE specific attributes
MOSFIRE specific DR techniques can be added to it in the future

12/14/2017 M. Brown - Created initial file
'''

import instrument
import datetime as dt
from common import *


class Mosfire(instrument.Instrument):

    def __init__(self, instr, utDate, rootDir, log=None):

        # Call the parent init to get all the shared variables
        super().__init__(instr, utDate, rootDir, log)


        # Set any unique keyword index values here
        self.keywordMap['OFNAME']       = 'DATAFILE'        
        self.keywordMap['FRAMENO']      = 'FRAMENUM'


        # Other vars that subclass can overwrite
        self.endTime = '20:00:00'   # 24 hour period start/end time (UT)


        # Generate the paths to the NIRES datadisk accounts
        self.sdataList = self.get_dir_list()



    def run_dqa_checks(self, progData):
        '''
        Run all DQA checks unique to this instrument.
        '''

        #todo: finish this
        #todo: check that all of these do not need a subclass version if base class func was used.
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
        if ok: ok = self.set_propint(progData)
        if ok: ok = self.set_wavelengths()
        # if ok: ok = self.set_specres()
        if ok: ok = self.set_weather_keywords()
        if ok: ok = self.set_datlevel(0)
        # if ok: ok = self.set_filter()
        # if ok: ok = self.set_slit_dims()
        # if ok: ok = self.set_spatscal()
        # if ok: ok = self.set_dispscal()
        if ok: ok = self.set_image_stats_keywords()
        if ok: ok = self.set_npixsat()
        if ok: ok = self.set_oa()
        if ok: ok = self.set_dqa_date()
        if ok: ok = self.set_dqa_vers()
        return ok



    def get_dir_list(self):
        '''
        Function to generate the paths to all the MOSFIRE accounts, including engineering
        Returns the list of paths
        '''
        dirs = []
        path = '/s/sdata1300'
        joinSeq = (path, '/mosfire')
        path2 = ''.join(joinSeq)
        dirs.append(path2)
        for i in range(1,10):
            joinSeq = (path, '/mosfire', str(i))
            path2 = ''.join(joinSeq)
            dirs.append(path2)
        joinSeq = (path, '/moseng')
        path2 = ''.join(joinSeq)
        dirs.append(path2)
        return dirs


    def get_prefix(self):

        instr = self.get_instr()
        if instr == 'mosfire': prefix = 'MF'
        else                 : prefix = ''
        return prefix


    def set_elaptime(self):
        '''
        Fixes missing ELAPTIME keyword.
        '''

        self.log.info('set_elaptime: determining ELAPTIME from ITIME/COADDS')

        #skip if it exists
        if self.get_keyword('ELAPTIME', False) != None: return True

        #get necessary keywords
        itime  = self.get_keyword('TRUITIME')
        coadds = self.get_keyword('COADDS')
        if (itime == None or coadds == None):
            self.log.error('set_elaptime: TRUITIME and COADDS values needed to set ELAPTIME')
            return False

        #update val
        elaptime = itime * coadds
        self.set_keyword('ELAPTIME', elaptime, 'KOA: Total integration time')
        return True


    def is_science(self):
        '''
        Returns true if header indicates science data was taken.
        '''

        #todo: is this right?

        koaimtyp = self.get_keyword('KOAIMTYP')
        if koaimtyp == 'object' : return True
        else                    : return False


    def set_frameno(self):
        """
        Adds FRAMENO keyword to header if it doesn't exist
        """
        # todo: Is all this needed for MOSFIRE too like NIRES?  If so, make commo?

        self.log.info('set_frameno: setting FRAMNO keyword value from FRAMENUM')

        #skip if it exists
        if self.get_keyword('FRAMENO', False) != None: return True

        #get value
        #NOTE: If FRAMENO doesn't exist, derive from DATAFILE
        frameno = self.get_keyword('FRAMENUM')
        if (frameno == None): 

            datafile = self.get_keyword('DATAFILE')
            if (datafile == None): 
                self.log.error('set_frameno: cannot find value for FRAMENO')
                return False

            frameno = datafile.replace('.fits', '')
            num = frameno.rfind('_') + 1
            frameno = frameno[num:]
            frameno = int(frameno)

        #update
        self.set_keyword('FRAMENO', frameno, 'KOA: Image frame number')
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
        """
        Determine image type based on instrument keyword configuration
        """

        self.log.info('set_koaimtyp: setting KOAIMTYP keyword value')

        # Default KOAIMTYPE value
        koaimtyp = 'undefined'

        # Telescope and dome keyword values
        el = self.get_keyword('EL')
        domestat = self.get_keyword('DOMESTAT')
        axestat = self.get_keyword('AXESTAT')

        # MOSFIRE keyword values
        obsmode = self.get_keyword('OBSMODE')
        maskname = self.get_keyword('MASKNAME')
        mdcmech = self.get_keyword('MDCMECH')
        mdcstat = self.get_keyword('MDCSTAT')
        mdcname = self.get_keyword('MDCNAME')

        # Dome lamp keyword values
        flatspec = self.get_keyword('FLATSPEC')
        flimagin = self.get_keyword('FLIMAGIN')
        flspectr = self.get_keyword('FLSPECTR')
        flatOn = 0
        if flatspec == 1 or flimagin == 'on' or flspectr == 'on':
            flatOn = 1

        # Arc lamp keyword values
        pwstata7 = self.get_keyword('PWSTATA7')
        pwstata8 = self.get_keyword('PWSTATA8')
        power = 0
        if pwstata7 == 1 and pwstata8 == 1:
            power = 1

        # Is telescope in flatlamp position
        flatlampPos = 0
        if el >= 44.99 and el <= 45.01 and 'tracking' not in [domestat, axestat]:
            flatlampPos = 1

        # Is the dust cover open
        dustCover = ''
        if  mdcmech == 'Dust Cover' and mdcstat == 'OK':
            dustCover = mdcname.lower()

        # Dark frame
        if obsmode.lower() == 'dark' and not power:
            koaimtyp = 'dark'
        else:
            # Setup for arclamp
            if dustCover == 'closed':
                if 'spectroscopy' in obsmode and power:
                    koaimtyp = 'arclamp'
            elif dustCover == 'open':
                # This is an object unless a flatlamp is on
                koaimtyp = 'object'
                if flatOn:
                    koaimtyp = 'flatlmp'
                else:
                    if flatlampPos:
                        koaimtyp = 'flatlampoff'

        # Still undefined? Use image statistics
        if koaimtyp == 'undefined':
            # Is the telescope in dome flat position?
            if flatlampPos:
                image = self.fitsHdu[0].data
                imageMean = np.mean(image)
                koaimtyp = 'flatlampoff'
                if (imageMean > 500):
                    koaimtyp = 'flatlamp'

        # Warn if undefined
        if koaimtyp == 'undefined':
            self.log.warning('set_koaimtyp: Could not determine KOAIMTYP value')

        # Update keyword
        self.set_keyword('KOAIMTYP', koaimtyp, 'KOA: Image type')
        return True


    def set_wavelengths(self):
        """
        Adds wavelength keywords.
        # https://www.keck.hawaii.edu/realpublic/inst/mosfire/genspecs.html
        """

#        self.log.info('set_wavelengths: setting wavelength keyword values')

        # Filter lookup (filter: [central, fwhm])

        wave = {}
        wave['Y'] = [1.048, 0.152]
        wave['J'] = [1.253, 0.200]
        wave['H'] = [1.637, 0.341]
        wave['K'] = [2.162, 0.483]
        wave['Ks'] = [2.147, 0.314]
        wave['J2'] = [1.181, 0.129]
        wave['J3'] = [1.288, 0.122]
        wave['H1'] = [1.556, 0.165]
        wave['H2'] = [1.709, 0.167]

        # Default null values
        wavered = wavecntr = waveblue = 'null'

        filter = self.get_keyword('FILTER')

        if filter in wave.keys():
            fwhm = wave[filter][1] / 2.0
            wavecntr = wave[filter][0]
            waveblue = wavecntr - fwhm
            wavered = wavecntr + fwhm
            waveblue = float('%.3f' % waveblue)
            wavecntr = float('%.3f' % wavecntr)
            wavered = float('%.3f' % wavered)

        self.set_keyword('WAVERED' , wavered, 'KOA: Red end wavelength')
        self.set_keyword('WAVECNTR', wavecntr, 'KOA: Center wavelength')
        self.set_keyword('WAVEBLUE', waveblue, 'KOA: Blue end wavelength')

        return True

