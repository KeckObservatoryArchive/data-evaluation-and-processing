'''
This is the class to handle all the NIRES specific attributes
NIRES specific DR techniques can be added to it in the future

12/14/2017 M. Brown - Created initial file
'''

import instrument
import datetime as dt

class Nires(instrument.Instrument):
    def __init__(self, endTime=dt.datetime.now()):
        # Call the parent init to get all the shared variables
        super().__init__(endTime)

        # NIRES uses DATAFILE instead of OUTFILE
        self.root = 'DATAFILE'
        # NIRES frame numbers are a part of their data file
        self.frameno = ''
        # Date observed is stored as DATE-OBS for NIRES
        self.dateObs = 'DATE-OBS'
        # Set the NIRES specific paths to anc and stage
        joinSeq = ('/koadataXX/NIRES/', self.utDate, '/anc')
        self.ancDir = ''.join(joinSeq)
        self.stageDir = '/koadataXX/stage'

        # Generate the paths to the NIRES datadisk accounts
        self.paths = self.get_dir_list()


    def get_dir_list(self):
        '''
        Function to generate the paths to all the DEIMOS accounts, including engineering
        Returns the list of paths
        '''
        dirs = []
        path = '/s/sdata150'
        for i in range(1,4):
            joinSeq = (path, str(i), '/nireseng')
            path2 = ''.join(joinSeq)
            dirs.append(path2)
        return dirs

    def set_prefix(self, keys):
        '''
        Sets the KOAID prefix
        Defaults to nullstr
        '''
        instr = self.set_instr(keys)
        if instr == 'nires':
            try:
                ftype = keys['INSTR']
            except KeyError:
                prefix = ''
            else:
                if ftype == 'imag':
                    prefix = 'NI'
                elif ftype == 'spec':
                    prefix = 'NR'
                else:
                    prefix = ''
        else:
            prefix = ''
        return prefix

