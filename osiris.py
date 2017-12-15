'''
This is the class to handle all the OSIRIS specific attributes
OSIRIS specific DR techniques can be added to it in the future

12/14/2017 M. Brown - Created initial file
'''

import instrument

class Osiris(instrument.Instrument):
    def __init__(self):
        # Call the parent init to get all the shared variables
        super().__init__()

        # OSIRIS has 'DATAFILE' instead of OUTFILE
        self.fileRoot = 'DATAFILE'
        # Set the OSIRIS specific paths to anc and stage
        self.ancDir = '/net/koaserver3/koadata23/OSIRIS/' + self.reducedDate + '/anc'
        self.stageDir = '/new/koaserver3/koadata23/stage'
        # Generate the paths to the OSIRIS datadisk accounts
        self.paths = self.getDirList()


    def getDirList(self):
        '''
        Function to generate the paths to all the OSIRIS accounts, including engineering
        Returns the list of paths
        '''
        dirs = []
        path = '/s/sdata110'
        for i in range (2):
            path2 = path + str(i)
            dirs.append(path2 + '/osiris')
            for i in range(1,21):
                path3 = path + '/osiris' + str(i)
                dirs.append(path3)
            dirs.append(path2 + '/osiriseng')
            dirs.append(path2 + '/osrseng')
        return dirs
