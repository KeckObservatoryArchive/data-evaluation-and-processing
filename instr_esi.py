'''
This is the class to handle all the ESI specific attributes
ESI specific DR techniques can be added to it in the future

12/14/2017 M. Brown - Created initial file
'''

import instrument
import datetime as dt
from common import *
import numpy as np


class Esi(instrument.Instrument):

    def __init__(self, instr, utDate, rootDir, log=None):

        # Call the parent init to get all the shared variables
        super().__init__(instr, utDate, rootDir, log)


        # Set any unique keyword index values here
        self.keywordMap['UTC']       = 'UT'        


        # Other vars that subclass can overwrite
        #TODO: Ack! Looks like the old DEP has an hour difference between this value and the actual cron time!
        self.endTime = '20:00:00'   # 24 hour period start/end time (UT)


        # Generate the paths to the NIRES datadisk accounts
        self.sdataList = self.get_dir_list()


    def run_dqa_checks(self, progData):
        '''
        Run all DQA checks unique to this instrument.
        '''

        #todo: check that all of these do not need a subclass version if base class func was used.
        ok = True
        if ok: ok = self.set_instr()
        if ok: ok = self.set_dateObs()
        if ok: ok = self.set_utc()
        if ok: ok = self.set_koaimtyp()
        if ok: ok = self.set_koaid()
        if ok: ok = self.set_ut()
        if ok: ok = self.set_frameno()
        if ok: ok = self.set_ofName()
        if ok: ok = self.set_semester()
        if ok: ok = self.set_prog_info(progData)
        if ok: ok = self.set_propint(progData)
        if ok: ok = self.set_datlevel(0)
        if ok: ok = self.set_image_stats_keywords()
        if ok: ok = self.set_weather_keywords()
        if ok: ok = self.set_oa()
        if ok: ok = self.set_npixsat()

        # if ok: ok = self.set_wavelengths()
        # if ok: ok = self.set_specres()
        # if ok: ok = self.set_slit_dims()
        # if ok: ok = self.set_spatscal()
        # if ok: ok = self.set_dispscal()

        if ok: ok = self.set_dqa_vers()
        if ok: ok = self.set_dqa_date()
        return ok


    @staticmethod
    def get_dir_list():
        '''
        Function to generate the paths to all the ESI accounts, including engineering
        Returns the list of paths
        '''
        dirs = []
        path = '/s/sdata70'
        for i in range(8):
            if i != 5:
                path2 = path + str(i) + '/esi'
                for j in range(1,21):
                    path3 = path2 + str(j)
                    dirs.append(path3)
                path3 = path2 + 'eng'
                dirs.append(path3)
        return dirs


    def get_prefix(self):

        instr = self.get_instr()
        if instr == 'esi': prefix = 'EI'
        else             : prefix = ''
        return prefix


    def set_koaimtyp(self):
        """
        Uses get_koaimtyp to set KOAIMTYP
        """

        #self.log.info('set_koaimtyp: setting KOAIMTYP keyword value')

        koaimtyp = self.get_koaimtyp()

        # Warn if undefined
        if koaimtyp == 'undefined':
            self.log.info('set_koaimtyp: Could not determine KOAIMTYP value')

        # Update keyword
        self.set_keyword('KOAIMTYP', koaimtyp, 'KOA: Image type')

        return True


    def get_koaimtyp(self):
        """
        Determine iamge type based on instrument keyword configuration
        """

        # Default KOAIMTYP value
        koaimtyp = 'undefined'

        # Check OBSTYPE first
        obstype = self.get_keyword('OBSTYPE').lower()

        if obstype == 'bias': return 'bias'
        if obstype == 'dark': return 'dark'

        slmsknam = self.get_keyword('SLMSKNAM').lower()
        hatchpos = self.get_keyword('HATCHPOS').lower()
        lampqtz1 = self.get_keyword('LAMPQTZ1').lower()
        lampar1 = self.get_keyword('LAMPAR1').lower()
        lampcu1 = self.get_keyword('LAMPCU1').lower()
        lampne1 = self.get_keyword('LAMPNE1').lower()
        lampne2 = self.get_keyword('LAMPNE2').lower()
        prismnam = self.get_keyword('PRISMNAM').lower()
        imfltnam = self.get_keyword('IMFLTNAM').lower()
        axestat = self.get_keyword('AXESTAT').lower()
        domestat = self.get_keyword('DOMESTAT').lower()
        el = self.get_keyword('EL')
        dwfilnam = self.get_keyword('DWFILNAM').lower()

        # Hatch
        hatchOpen = 1
        if hatchpos == 'closed': hatchOpen = 0

        # Is flat lamp on?
        flat = 0
        if lampqtz1 == 'on': flat = 1

        # Is telescope pointed at flat screen?
        flatPos = 0
        if el >= 44.0 and el <= 46.01: flatPos = 1

        # Is an arc lamp on?
        arc = 0
        if lampar1 == 'on' or lampcu1 == 'on' or lampne1 == 'on' or lampne2 == 'on':
            arc = 1

        # Dome/Axes tracking
        axeTracking = domeTracking = 0
        if axestat == 'tracking': axeTracking = 1
        if domestat == 'tracking': domeTracking = 1

        # This is a trace or focus
        if 'hole' in slmsknam:
            if not hatchOpen:
                if flat and not arc and prismnam == 'in' and imfltnam == 'out': return 'trace'
                if flat and not arc and prismnam != 'in' and imfltnam != 'out': return 'focus'
                if not flat and arc and prismnam == 'in' and imfltnam == 'out': return 'focus'
            else:
                if prismnam == 'in' and imfltnam == 'out':
                    if obstype == 'dmflat' and not domeTracking and flatPos: return 'trace'
                    if not axeTracking and not domeTracking and flatPos: return 'trace'
                    if obstype == 'dmflat' and not axeTracking and not domeTracking and flatPos: return 'trace'
                    if obstype == 'dmflat' and not axeTracking and flatPos: return 'trace'
                else:
                    if obstype == 'dmflat' and not domeTracking and flatPos: return 'focus'
                    if not axeTracking and not domeTracking and flatPos: return 'focus'
                    if obstype == 'dmflat' and not axeTracking and not domeTracking and flatPos: return 'focus'
                    if obstype == 'dmflat' and not axeTracking and flatPos: return 'focus'
            idfltnam = self.get_keyword('IDFLTNAM').lower()
            if prismnam == 'out' and infltnam == 'in' and idfltnam == 'out': return 'focus'
            if prismnam == 'in' and infltnam == 'out' and dwfilnam == 'clear_s': return 'focus'
        else:
            if not hatchOpen:
                if flat and not arc: return 'flatlamp'
                if not flat and arc and prismnam == 'in' and imfltnam == 'out': return 'arclamp'
            else:
                if obstype == 'dmflat' and not domeTracking and flatPos: return 'flatlamp'
                if not axeTracking and not domeTracking and flatPos: return 'flatlamp'
                if obstype == 'dmflat' and not axeTracking and not domeTracking: return 'flatlamp'
                if obstype == 'dmflat' and not axeTracking and flatPos: return 'flatlamp'
                if not flat and not arc: return 'object'

        return 'undefined'
