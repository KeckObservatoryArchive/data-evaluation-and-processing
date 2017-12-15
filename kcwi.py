'''
This is the class to handle all the KCWI specific attributes
KCWI specific DR techniques can be added to it in the future

12/14/2017 M. Brown - Created initial file
'''

import instrument

class Kcwi(instrument.Instrument):
    def __init__(self):
        # Call the parent init to get all the shared variables
        super().__init__()

        # KCWI has the original file name
        self.origFile = 'OFNAME'
        # Set the KCWI specific paths to anc and stage
        self.ancDir = '/koadata28/KCWI/' + self.reducedDate + '/anc'
        self.stageDir = '/koadata28/stage'
        # Generate the paths to the KCWI datadisk accounts
        self.paths = self.getDirList()


    def getDirList(self):
        '''
        Function to generate the paths to all the KCWI accounts, including engineering
        Returns the list of paths
        '''
        dirs = []
        path = '/s/sdata1400/kcwi'
        for i in range(1,10):
            path2 = path + str(i)
            dirs.append(path2)
        dirs.append(path + 'dev')
        return dirs
