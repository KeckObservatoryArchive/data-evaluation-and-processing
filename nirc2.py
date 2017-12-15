'''
This is the class to handle all the NIRC2 specific attributes
NIRC2 specific DR techniques can be added to it in the future

12/14/2017 M. Brown - Created initial file
'''

class Nirc2(instrument.Instrument):
    def __init__(self):
        # Call the parent init to get all the shared variables
        super(Nirc2, self).__init__(self)

        # NIRC2 uses ROOTNAME instead of OUTDIR
        self.fileRoot = 'ROOTNAME'
        # Set the NIRC2 specific paths to anc and stage
        self.ancDir = '/net/koaserver2/koadata11/NIRC2/' + self.reducedDate + '/anc'
        self.stageDir = '/new/koaserver2/koadata11/stage'
        # Generate the paths to the NIRC2 datadisk accounts
        self.paths = self.getDirList()


    def getDirList(self):
        '''
        Function to generate the paths to all the NIRC2 accounts, including engineering
        Returns the list of paths
        '''
        dirs = []
        path = '/s/sdata90'
        for i in range(5):
            path2 = path + str(i) + '/nirc'
            for i in range(1,21):
                path3 = path2 + str(i)
                dirs.append(path3)
            dirs.append(path2 + '2eng')
        return dirs
