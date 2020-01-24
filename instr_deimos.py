"""
This is the class to handle all the DEIMOS specific attributes
DEIMOS specific DR techniques can be added to it in the future

12/14/2017 M. Brown - Created initial file
"""

import instrument
import datetime as dt
from common import *
import numpy as np

class Deimos(instrument.Instrument):

    def __init__(self, instr, utDate, rootDir, log=None):

        # Call the parent init to get all the shared variables
        super().__init__(instr, utDate, rootDir, log)


        # Set any unique keyword index values here
        self.keywordMap['OFNAME']       = 'DATAFILE'        
        self.keywordMap['FRAMENO']      = ''


        # Other vars that subclass can overwrite
        self.endTime = '19:00:00'   # 24 hour period start/end time (UT)


        # Generate the paths to the DEIMOS datadisk accounts
        self.sdataList = self.get_dir_list()


        # """
        # Values not included in superclass, specific to DEIMOS
        # """
        # # add the FCSIMGFI config file for deimos
        # self.fcsimgfi = 'FCSIMGFI'
        self.gratingList = {}
        self.gratingList['600ZD'] = {'wave':7500, 'dispersion':0.65, 'length':5300}
        self.gratingList['830G']  = {'wave':8640, 'dispersion':0.47, 'length':3840}
        self.gratingList['900ZD'] = {'wave':5500, 'dispersion':0.44, 'length':3530}
        self.gratingList['1200G'] = {'wave':7760, 'dispersion':0.33, 'length':2630}
        self.gratingList['1200B'] = {'wave':4500, 'dispersion':0.33, 'length':2630}
        # Filter list for imaging wavelengths
        self.filterList = {}
        self.filterList['B']      = {'blue':4200, 'cntr':4400, 'red':4600}
        self.filterList['V']      = {'blue':5150, 'cntr':5450, 'red':5750}
        self.filterList['R']      = {'blue':6100, 'cntr':6500, 'red':6900}
        self.filterList['I']      = {'blue':7600, 'cntr':8400, 'red':9200}
        self.filterList['Z']      = {'blue':8600, 'cntr':9100, 'red':9600}
        self.filterList['GG400']  = {'blue':4000, 'cntr':7250, 'red':10500}
        self.filterList['GG455']  = {'blue':4550, 'cntr':7525, 'red':10500}
        self.filterList['GG495']  = {'blue':4950, 'cntr':7725, 'red':10500}
        self.filterList['OG550']  = {'blue':5500, 'cntr':8000, 'red':10500}
        self.filterList['NG8560'] = {'blue':8400, 'cntr':8550, 'red':8700}
        self.filterList['NG8580'] = {'blue':8550, 'cntr':8600, 'red':8650}


    def run_dqa_checks(self, progData):
        '''
        Run all DQA check unique to this instrument
        '''

        ok = True
        if ok: ok = self.set_instr()
        if ok: ok = self.set_dateObs()
        if ok: ok = self.set_ut()
        if ok: ok = self.set_koaimtyp()
        if ok: ok = self.set_koaid()
        if ok: ok = self.set_ofName()
        if ok: ok = self.set_semester()
        if ok: ok = self.set_prog_info(progData)
        if ok: ok = self.set_propint(progData)
        if ok: ok = self.set_datlevel(0)
        if ok: ok = self.set_weather_keywords()
        if ok: ok = self.set_oa()
        if ok: ok = self.set_dqa_vers()
        if ok: ok = self.set_dqa_date()
        if ok: ok = self.set_camera()
        if ok: ok = self.set_filter()
        if ok: ok = self.set_mjd()
        if ok: ok = self.set_obsmode()
        if ok: ok = self.set_nexten()
        if ok: ok = self.set_detsec()
        if ok: ok = self.set_npixsat(satVal=65535.0)
        if ok: ok = self.set_wavelengths()
        if ok: ok = self.set_spatscal()
        if ok: ok = self.set_specres()

        return ok


    def get_dir_list(self):
        """
        Function to generate the paths to all the DEIMOS accounts, including engineering
        Returns the list of paths
        """
        dirs = []
        path = '/s/sdata100'
        for i in range(1,6):
            path2 = path + str(i)
            for j in range(1,21):
                path3 = path2 + '/deimos' + str(j)
                dirs.append(path3)
            path3 = path2 + '/dmoseng'
            dirs.append(path3)
        return dirs


    def get_prefix(self):
        '''
        Returns the KOAID prefix to use, either DE for a DEIMOS science/calibration
        exposure or DF for an FCS image.
        '''

        instr = self.get_instr()
        outdir = self.get_keyword('OUTDIR')
        
        if '/fcs' in outdir:
            prefix = 'DF'
        elif instr == 'deimos':
            prefix = 'DE'
        else:
            prefix = ''
        return prefix


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


    def set_koaimtyp(self):
        '''
        Calls get_koaimtyp to determine image type. 
        Creates KOAIMTYP keyword.
        '''

        koaimtyp = self.get_koaimtyp()

        # Warn if undefined
        if koaimtyp == 'undefined':
            self.log.info('set_koaimtyp: Could not determine KOAIMTYP value')

        # Create the keyword
        self.set_keyword('KOAIMTYP', koaimtyp, 'KOA: Image type')

        return True


    def get_koaimtyp(self):
        '''
        Return image type based on the algorithm provided by SA
        '''

        # Get relevant keywords from header
        obstype  = self.get_keyword('OBSTYPE', default='').lower()
        slmsknam = self.get_keyword('SLMSKNAM', default='').lower()
        hatchpos = self.get_keyword('HATCHPOS', default='').lower()
        flimagin = self.get_keyword('FLIMAGIN', default='').lower()
        flspectr = self.get_keyword('FLSPECTR', default='').lower()
        lamps    = self.get_keyword('LAMPS', default='').lower()
        gratepos = self.get_keyword('GRATEPOS')

        # if obstype is 'bias' we have a bias
        if obstype == 'bias':
            return 'bias'

        # if obsmode is 'dark' we have a dark
        if obstype == 'dark':
            return 'dark'

        # if slmsknam contains 'goh' we have a focus image
        if slmsknam.startswith('goh'):
            return 'focus'

        # if hatch is closed and lamps are quartz, then flat
        if hatchpos == 'closed' and 'qz' in lamps:
            return 'flatlamp'

        # if hatch is open and flimagin or flspectr are on, then flat
        if hatchpos == 'open' and (flimagin == 'on' or flspectr == 'on'):
            return 'flatlamp'

        # if lamps are not off/qz and grating position is 3 or 4, then arc
        if hatchpos == 'closed' and ('off' not in lamps and 'qz' not in lamps)\
           and (gratepos == 3 or gratepos == 4):
            return 'arclamp'

        # if tracking then we must have an object science image
        # otherwise, don't know what it is
        if hatchpos == 'open':
            return 'object'

        # check for fcs image
        outdir = self.get_keyword('OUTDIR', default='')
        if 'fcs' in outdir:
            return 'fcscal'

        return 'undefined'


    def set_camera(self):
        '''
        Adds the keyword CAMERA to the header and sets its value to DEIMOS
        '''
        
        camera = self.get_keyword('CAMERA', False)
        if camera == None:
            self.log.info('set_camera: Adding CAMERA keyword')
            self.set_keyword('CAMERA', 'DEIMOS', 'KOA: Camera name')

        return True


    def set_filter(self):
        '''
        Adds the keyword FILTER to the header and sets its value to be the 
        same as the DWFILNAM keyword.
        '''

        filter = self.get_keyword('DWFILNAM', False)
        if filter == None:
            self.log.info('set_filter: Could not set filter, no DWFILNAM value')
        else:
            self.log.info('set_filter: Adding FILTER keyword')
            self.set_keyword('FILTER', filter, 'KOA: Filter name')
        
        return True


    def set_mjd(self):
        '''
        Adds the keyword MJD to the header and sets its value equal to the 
        MJD-OBS keyword.  MJD is the numeric respresentation of MJD-OBS.
        '''

        mjd = self.get_keyword('MJD-OBS', False)
        if mjd == None:
            self.log.info('set_mjd: Could not set MJD, no MJD-OBS value')
        else:
            self.log.info('set_mjd: Adding MJD keyword')
            self.set_keyword('MJD', float(mjd), 'KOA: Modified julian day')
        
        return True


    def set_obsmode(self):
        '''
        Adds the keyword OBSMODE to the header.
        
        UNKNOWN if:  GRATENAM = "Unknown", "None", or (blank)
        IMAGING if:  GRATENAM = "Mirror"
                     OR
                     ( GRATEPOS = 3 and G3TLTNAM = "Zeroth_Order"
                       OR
                       GRATEPOS = 4 and G4TLTNAM = "Zeroth_Order"
                     )
        LONGSLIT if: GRATENAM != ["Mirror", "Unknown", "None", (blank)]
                     AND
                     SLMSKNAM contains "LVM*" or "Long*"
        MOS if:      GRATENAM != ["Mirror", "Unknown", "None", (blank)]
                     AND
                     SLMSKNAM != ["LVM*", "Long*"]
        '''

        self.log.info('set_obsmode: Adding OBSMODE keyword')
        
        gratname = self.get_keyword('GRATENAM', default='').lower()
        if gratname in ['', 'unknown', 'none']:
            obsmode = 'UNKNOWN'
        elif gratname == 'mirror':
            gratepos = self.get_keyword('GRATEPOS', default=0)
            if int(gratepos) == 3 or int(gratepos) == 4:
                key = f'G{int(gratepos)}TLTNAM'
                tilt = self.get_keyword(key, default='').lower()
                if tilt == 'zeroth_order':
                    obsmode = 'IMAGING'
        else:
            slmsknam = self.get_keyword('SLMSKNAM', default='')
            if slmsknam.startswith('LVM') or slmsknam.startswith('Long'):
                obsmode = 'LONGSLIT'
            else:
                obsmode = 'MOS'

        self.set_keyword('OBSMOD', obsmode, 'KOA: Observing mode')

        return True


    def set_nexten(self):
        '''
        Adds the NEXTEN keyword and sets its value to the number of
        imaging extensions for this file.
        '''

        self.log.info('set_nexten: Adding NEXTEN keyword')
        self.set_keyword('NEXTEN', int(len(self.fitsHdu))-1, 'KOA: Number of image extensions')

        return True


    def set_detsec(self):
        '''
        Adds the DETSEC## keywords to the primary header.  Value of the
        keyword is set equal to the DETSEC keyword value from the image
        headers.  ## = 01 to 16.
        '''

        self.log.info('set_detsec: Adding DETSEC## keywords')

        maxExtensions = 16
        for i in range(1, maxExtensions+1):
            key = f'DETSEC{str(i).zfill(2)}'
            detsec = 'null'
            if i < len(self.fitsHdu):
                try:
                    detsec = self.fitsHdu[i].header['DETSEC']
                except:
                    pass
            comment = f'KOA: Mosaic detector section for HDU{str(i).zfill(2)}'
            self.set_keyword(key, detsec, comment)

        return True


    def set_npixsat(self, satVal=None):
        '''
        Determines number of saturated pixels and adds NPIXSAT to header
        NPIXSAT is the sum of all image extensions.
        '''

        self.log.info('set_npixsat: setting pixel saturation keyword value')

        if satVal == None:
            satVal = self.get_keyword('SATURATE')

        if satVal == None:
            self.log.warning("set_npixsat: Could not find SATURATE keyword")
        else:
            nPixSat = 0
            for ext in range(1, len(self.fitsHdu)):
                image = self.fitsHdu[ext].data
                pixSat = image[np.where(image >= satVal)]
                nPixSat += len(image[np.where(image >= satVal)])

            self.set_keyword('NPIXSAT', nPixSat, 'KOA: Number of saturated pixels')

        return True


    def set_wavelengths(self):
        '''
        Adds wavelength keywords.
        '''

        waveblue = wavecntr = wavered = 'null'

        # Is this an image or spectrum?
        obsmode = self.get_keyword('OBSMODE')
        if obsmode == 'image':
            filter = self.get_keyword('FILTER', defult='').strip()
            if filter in filter.keys():
                waveblue = self.filterList[filter]['blue']
                wavecntr = self.filterList[filter]['cntr']
                wavered  = self.filterList[filter]['red']

        elif obsmode in ['longslit', 'mos']:
            gratepos = self.get_keyword('GRATEPOS')
            waveKey = f'G{gratepos}TLTWAV'
            grating = self.get_keyword('GRATENAM')
            if grating in self.gratingList.keys():
                wavecntr = int(round(self.get_keyword(waveKey), -1))
                delta = self.gratingList[grating]['length']/2
                waveblue = wavecntr - delta
                wavered = wavecntr + delta

        else:
            pass

        self.set_keyword('WAVEBLUE', waveblue, 'KOA: Blue end wavelength')
        self.set_keyword('WAVECNTR', wavecntr, 'KOA: Center wavelength')
        self.set_keyword('WAVERED' , wavered, 'KOA: Red end wavelength')

        return True


    def set_spatscal(self):
        '''
        Populates SPATSCAL
        '''
        
        self.set_keyword('SPATSCAL', 0.1185, 'KOA: CCD spatial pixel scale')
        return True


    def set_dispscal(self):
        '''
        Populates DISPSCAL
        '''

        dispscal = 'null'

        obsmode = self.get_keyword('OBSMODE')
        spatscal = self.get_keyword('SPATSCAL')
        if obsmode == 'image':
            dispscal = spatscal
        elif obsmode in ['longslit', 'mos']:
            grating = self.get_keyword('GRATENAM')
            if grating in self.gratingList.keys():
                dispscal = self.gratingList[grating]['dispersion']

        self.set_keyword('DISPSCAL', dispscal, 'KOA: CCD dispersion pixel scale')
        return True


    def set_specres(self):
        '''
        Calculates the spectral resolution and add SPECRES to header
        '''

        specres = 'null'

        spatscal = self.get_keyword('SPATSCAL')
        grating = self.get_keyword('GRATENAM')

        if grating in self.gratingList.keys():
            specres = (self.gratingList[grating]['wave']*spatscal)/self.gratingList[grating]['dispersion']
            specres = round(specres, -1)

        self.set_keyword('SPECRES', specres, 'KOA: nominal spectral resolution')

        return True
