'''
This is the class to handle all the HIRES specific attributes
HIRES specific DR techniques can be added to it in the future

12/14/2017 M. Brown - Created initial file
'''

import instrument
import datetime as dt

class Hires(instrument.Instrument):
    def __init__(self, endTime=dt.datetime.now(), rDir=''):
        # Call the parent init to get all the shared variables
        super().__init__(endTime, rDir)

        '''
        Values to be overwritten from superclass
        '''
        # Set the hires specific paths to anc and stage
        seq = (self.rootDir,'/HIRES/', self.utDate, '/anc')
        self.ancDir = ''.join(seq)
        seq = (self.rootDir, '/stage')
        self.stageDir = ''.join(seq)
        # Generate the paths to the HIRES datadisk accounts
        self.paths = self.get_dir_list()

        '''
        Values not included in superclass
        '''


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
            for j in range(1,21):
                joinSeq = (path2, str(j))
                path3 = ''.join(joinSeq)
                dirs.append(path3)
            joinSeq = (path2, 'eng')
            path3 = ''.join(joinSeq)
            dirs.append(path2 + 'eng')
        return dirs

    def get_prefix(self, keys):
        instr = self.get_instr(keys)
        if instr == 'hires':
            prefix = 'HI'
        else:
            prefix = ''
        return prefix
