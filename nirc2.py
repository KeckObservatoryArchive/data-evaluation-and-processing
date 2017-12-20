'''
This is the class to handle all the NIRC2 specific attributes
NIRC2 specific DR techniques can be added to it in the future

12/14/2017 M. Brown - Created initial file
'''

import instrument
import datetime as dt

class Nirc2(instrument.Instrument):
    def __init__(self, endTime=dt.datetime.now()):
        # Call the parent init to get all the shared variables
        super().__init__(endTime)

        # NIRC2 uses ROOTNAME instead of OUTDIR
        self.fileRoot = 'ROOTNAME'
        # Set the NIRC2 specific paths to anc and stage
        joinSeq = ('/net/koaserver2/koadata11/NIRC2/', self.utDate, '/anc')
        self.ancDir = ''.join(joinSeq)
        self.stageDir = '/new/koaserver2/koadata11/stage'
        # Generate the paths to the NIRC2 datadisk accounts
        self.paths = self.get_dir_list()
        self.prefix = 'N2'


    def get_dir_list(self):
        '''
        Function to generate the paths to all the NIRC2 accounts, including engineering
        Returns the list of paths
        '''
        dirs = []
        path = '/s/sdata90'
        for i in range(5):
            joinSeq = (path, str(i), '/nirc')
            path2 = ''.join(joinSeq)
            for j in range(1,21):
                joinSeq = (path2, str(j))
                path3 = ''.join(joinSeq)
                dirs.append(path3)
            joinSeq(path2, '2eng')
            path3 = ''.join(joinSeq)
            dirs.append(path3)
        return dirs

    def set_prefix(self, keys):
        instr = self.set_prefix(keys)
        if instr == 'nirc2':
            self.prefix = 'N2'
        else:
            self.prefix = ''
