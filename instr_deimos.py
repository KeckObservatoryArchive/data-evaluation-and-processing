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


        # Generate the paths to the NIRES datadisk accounts
        self.sdataList = self.get_dir_list()


        # """
        # Values not included in superclass, specific to DEIMOS
        # """
        # # add the FCSIMGFI config file for deimos
        # self.fcsimgfi = 'FCSIMGFI'


    def run_dqa_checks(self, progData):
        '''
        Run all DQA check unique to this instrument
        '''

        ok = True
        if ok: ok = self.set_instr()
        if ok: ok = self.set_dateObs()
        if ok: ok = self.set_ut()
        if ok: ok = self.set_koaimtyp()

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
        gratepos = self.get_keyword('GRATEPOS', default='').lower()

        # if obstype is 'bias' we have a bias
        if obstype == 'bias':
            return 'bias'

        # if obsmode is 'dark' we have a dark
        if obstype == 'dark':
            return 'dark'

        # if slmsknam contains 'goh' we have a focus image
        if slmsknam.startsWith('goh'):
            return 'focus'

        # if hatch is closed and lamps are quartz, then flat
        if hatchpos == 'closed' and 'qz' in lamps:
            return 'flatlamp'

        # if hatch is open and flimagin or flspectr are on, then flat
        if hatchpos == 'open' and (flimagin == 'on' or flspectr == 'on'):
            return 'flatlamp'

        # if lamps are not off/qz and grating position is 3 or 4, then arc
        if hatchpos == 'closed' and ('off' not in lamps and 'qz' not in lamps)\
           and (gratepos == '3' or gratepos == '4'):
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
