'''
This is the class to handle all the HIRES specific attributes
HIRES specific DR techniques can be added to it in the future

12/14/2017 M. Brown - Created initial file
'''

import instrument

class Hires(instrument.Instrument):
    def __init__(self):
        # Call the parent init to get all the shared variables
        super().__init__()

        
        # Set the hires specific paths to anc and stage
        self.ancDir = '/net/koaserver2/koadata13/HIRES/' + self.reducedDate + '/anc'
        self.stageDir = '/net/koaserver2/koadata13/stage'
        # Generate the paths to the HIRES datadisk accounts
        self.paths = self.getDirList()


    def getDirList(self):
        '''
        Function to generate the paths to all the HIRES accounts, including engineering
        Returns the list of paths
        '''
        dirs = []
        path = '/s/sdata12'
        for i in range(5,8):
            path2 = path + str(i) + '/hires'
            for i in range(1,21):
                path3 = path2 + str(i)
                dirs.append(path3)
            dirs.append(path2 + 'eng')
        return dirs
