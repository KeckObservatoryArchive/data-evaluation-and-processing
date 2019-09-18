'''
This is the class to handle all the KCWI specific attributes
KCWI specific DR techniques can be added to it in the future

12/14/2017 M. Brown - Created initial file
'''

import instrument
import datetime as dt
from common import *

class Kcwi(instrument.Instrument):

    def __init__(self, instr, utDate, rootDir, log=None):

        # Call the parent init to get all the shared variables
        super().__init__(instr, utDate, rootDir, log)


        # Set any unique keyword index values here
        # self.keywordMap['OFNAME']       = 'OFNAME'        
        # self.keywordMap['FRAMENO']      = 'FRAMENUM'


        # Other vars that subclass can overwrite
        self.endTime = '20:00:00'   # 24 hour period start/end time (UT)


        # Generate the paths to the NIRES datadisk accounts
        self.sdataList = self.get_dir_list()


    def run_dqa_checks(self, progData):
        '''
        Run all DQA checks unique to this instrument.
        '''

        # todo: check that all of these do not need a subclass version if base class func was used.
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
        if ok: ok = self.set_npixsat(65535)

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
        Function to generate the paths to all the KCWI accounts, including engineering
        Returns the list of paths
        '''

        #TODO: verify that /sdata1401/ is not used
        #todo: verify that /kcwidev/ is not used
        dirs = []
        path = '/s/sdata140'
        for i in range(0,1):
            path2 = path + str(i) + '/kcwi'
            for j in range(1,10):
                path3 = path2 + str(j)
                dirs.append(path3)
            dirs.append(path2 + 'dev')
            dirs.append(path2 + 'eng')
        return dirs


    def get_prefix(self):

        instr = self.get_instr()
        if instr == 'kcwi':
            camera = self.get_keyword('CAMERA', default='')
            camera = camera.lower()
            if   camera == 'blue': prefix = 'KB'
            elif camera == 'red' : prefix = 'KR'
            elif camera == 'fpc' : prefix = 'KF'
            else                 : prefix = ''
        else:
            prefix = ''
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
        Determine image type based on instrument keyword configuration
        """

        # Default KOAIMTYP value
        koaimtyp = 'undefined'


        #todo


        return koaimtyp


    def get_dispmode(self, update=False):
        """
        """

        dispmode = ''

        #todo: 

        return dispmode


