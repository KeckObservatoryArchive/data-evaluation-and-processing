'''
This is the class to handle all the LRIS specific attributes
LRIS specific DR techniques can be added to it in the future

12/14/2017 M. Brown - Created initial file
'''

import instrument

class Lris(instrument.Instrument):
    def __init__(self):
        # Call the parent init to get all the shared variables
        super().__init__()

        # Set the lris specific paths to anc and stage
        self.ancDir = '/koadata27/LRIS/' + self.reducedDate + '/anc'
        self.stageDir = '/koadata27/stage'
        # Generate the paths to the LRIS datadisk accounts
        self.paths = self.getDirList()


    def getDirList(self):
        '''
        Function to generate the paths to all the LRIS accounts, including engineering
        Returns the list of paths
        '''
        dirs = []
        path = '/s/sdata24'
        for i in range(1,4):
            path2 = path + str(i) + '/lris'
            for i in range(1,21):
                path3 = path2 + str(i)
                dirs.append(path3)
            dirs.append(path2 + 'eng')
        return dirs
