'''
This is the class to handle all the KCWI specific attributes
KCWI specific DR techniques can be added to it in the future

12/14/2017 M. Brown - Created initial file
'''

import instrument
import datetime as dt

class Kcwi(instrument.Instrument):
    def __init__(self, endTime=dt.datetime.now(), rDir=''):
        # Call the parent init to get all the shared variables
        super().__init__(endTime, rDir)

        # KCWI has the original file name
        self.ofName = 'OFNAME'
        self.camera = 'CAMERA'
        self.endHour = 'DATE-END'
        # Set the KCWI specific paths to anc and stage
        seq = (self.rootDir, '/KCWI/', self.utDate, '/anc')
        self.ancDir = ''.join(seq)
        seq = (self.rootDir, '/stage')
        self.stageDir = ''.join(seq)
        # Generate the paths to the KCWI datadisk accounts
        self.paths = self.get_dir_list()

        def run_dqa_checks(self, progData):
            '''
            Run all DQA checks unique to this instrument.
            '''

            # todo: check that all of these do not need a subclass version if base class func was used.
            ok = True
            if ok: ok = self.set_instr()
            if ok: ok = self.set_dateObs()
            if ok: ok = self.set_utc()
            self.get_dispmode(update=True)
            self.get_camera(update=True)
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

            if ok: ok = self.set_wavelengths()
            if ok: ok = self.set_specres()
            if ok: ok = self.set_slit_dims()
            if ok: ok = self.set_spatscal()
            if ok: ok = self.set_dispscal()

            if ok: ok = self.set_dqa_vers()
            if ok: ok = self.set_dqa_date()
            return ok


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

    def get_prefix(self, keys):
        instr = self.get_instr(keys)
        if instr == 'kcwi':
            try:
                camera = keys['CAMERA'].lower()
            except KeyError:
                prefix = ''
            if camera == 'blue':
                prefix = 'KB'
            elif camera == 'red':
                prefix = 'KR'
            elif camera == 'fpc':
                prefix = 'KF'
            else:
                prefix = ''
        else:
            prefix = ''
        return prefix

