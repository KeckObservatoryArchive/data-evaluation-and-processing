'''
This is the class to handle all the NIRSPEC specific attributes
NIRSPEC specific DR techniques can be added to it in the future

12/14/2017 M. Brown - Created initial file
'''

import instrument

class Nirspec(instrument.Instrument):
    def __init__(self):
        # Call the parent init to get all the shared variables
        super().__init__()

        # NIRSPEC uses ROOTNAME instead of OUTDIR
        self.fileRoot = 'ROOTNAME'
        # NIRSPEC uses FILENUM2 instead of FRAMENO
        self.frameno = 'FILENUM2'
        # Set the NIRSPEC specific paths to anc and stage
        self.ancDir = '/net/koaserver/koadata7/NIRSPEC/' + self.reducedDate + '/anc'
        self.stageDir = '/new/koaserver/koadata7/stage'
        # Generate the paths to the NIRSPEC datadisk accounts
        self.paths = self.getDirList()


    def getDirList(self):
        '''
        Function to generate the paths to all the NIRSPEC accounts, including engineering
        Returns the list of paths
        '''
        dirs = []
        path = '/s/sdata90'
        for i in range(4):
            path2 = path + str(i)
            for i in range(1,21):
                path3 = path2 + '/nspec' + str(i)
                dirs.append(path3)
            dirs.append(path2 + '/nspeceng')
            dirs.append(path2 + '/nirspec')
        return dirs
