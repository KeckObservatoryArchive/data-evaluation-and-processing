'''
This is the class to handle all the MOSFIRE specific attributes
MOSFIRE specific DR techniques can be added to it in the future

12/14/2017 M. Brown - Created initial file
'''

import instrument
import datetime as dt

class Mosfire(instrument.Instrument):
    def __init__(self, endTime=dt.datetime.now()):
        # Call the parent init to get all the shared variables
        super().__init__(endTime)

        # MOSFIRE has 'DATAFILE' instead of OUTFILE
        self.fileRoot = 'DATAFILE'
        # MOSFIRE has FRAMENUM instead of FRAMENO
        self.frameno = 'FRAMENUM'
        # Set the MOSFIRE specific paths to anc and stage
        joinSeq = ('/koadata21/MOSFIRE/', self.utDate, '/anc')
        self.ancDir = ''.join(joinSeq)
        self.stageDir = '/koadata21/stage'
        # Generate the paths to the MOSFIRE datadisk accounts
        self.paths = self.get_dir_list()


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
