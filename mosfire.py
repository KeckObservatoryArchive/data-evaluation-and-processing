'''
This is the class to handle all the MOSFIRE specific attributes
MOSFIRE specific DR techniques can be added to it in the future

12/14/2017 M. Brown - Created initial file
'''

import instrument

class Mosfire(instrument.Instrument):
    def __init__(self):
        # Call the parent init to get all the shared variables
        super().__init__()

        # MOSFIRE has 'DATAFILE' instead of OUTFILE
        self.fileRoot = 'DATAFILE'
        # MOSFIRE has FRAMENUM instead of FRAMENO
        self.frameno = 'FRAMENUM'
        # Set the MOSFIRE specific paths to anc and stage
        self.ancDir = '/koadata21/MOSFIRE/' + self.reducedDate + '/anc'
        self.stageDir = '/koadata21/stage'
        # Generate the paths to the MOSFIRE datadisk accounts
        self.paths = self.getDirList()


    def getDirList(self):
        '''
        Function to generate the paths to all the MOSFIRE accounts, including engineering
        Returns the list of paths
        '''
        dirs = []
        path = '/s/sdata1300'
        dirs.append(path + '/mosfire')
        for i in range(1,10):
            path2 = path + '/mosfire' + str(i)
            dirs.append(path2)
        dirs.append(path + '/moseng')
        return dirs
