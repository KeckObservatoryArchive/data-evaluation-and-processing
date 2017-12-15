'''
This is the class to handle all the NIRES specific attributes
NIRES specific DR techniques can be added to it in the future

12/14/2017 M. Brown - Created initial file
'''

import instrument

class Nires(instrument.Instrument):
    def __init__(self):
        # Call the parent init to get all the shared variables
        super().__init__()

        # NIRES uses DATAFILE instead of OUTFILE
        self.root = 'DATAFILE'
        # NIRES frame numbers are a part of their data file
        self.frameno = ''
        # Set the NIRES specific paths to anc and stage
        self.ancDir = '/koadataXX/NIRES/' + self.reducedDate + '/anc'
        self.stageDir = '/koadataXX/stage'
        # Generate the paths to the NIRES datadisk accounts
        self.paths = self.getDirList()
        self.dataType = 'INSTR'


    def getDirList(self):
        '''
        Function to generate the paths to all the DEIMOS accounts, including engineering
        Returns the list of paths
        '''
        dirs = []
        path = '/s/sdata150'
        for i in range(1,4):
            path2 = path + str(i) + '/nireseng'
            dirs.append(path2)
        return dirs
