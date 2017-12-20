'''
This is the class to handle all the ESI specific attributes
ESI specific DR techniques can be added to it in the future

12/14/2017 M. Brown - Created initial file
'''

import instrument

class Esi(instrument.Instrument):
    def __init__(self, endTime=dt.datetime.now()):
        # Call the parent init to get all the shared variables
        super().__init__(endTime)

        # Set the esi specific paths to anc and stage
        joinSeq = ('/koadata29/ESI/', self.utDate, '/anc')
        self.ancDir = ''.join(joinSeq)
        self.stageDir = '/koadata29/stage'
        # Generate the paths to the ESI datadisk accounts
        self.paths = self.get_dir_list()


    def get_dir_list(self):
        '''
        Function to generate the paths to all the ESI accounts, including engineering
        Returns the list of paths
        '''
        dirs = []
        path = '/s/sdata70'
        for i in range(8):
            if i != 5:
                joinSeq = (path, str(i), '/esi')
                path2 = ''.join(joinSeq)
                for j in range(1,21):
                    joinSeq = (path2, str(j))
                    path3 = ''.join(joinSeq)
                    dirs.append(path3)
                joinSeq = (path2, 'eng')
                path3 = ''.join(joinSeq)
                dirs.append(path3)
        return dirs

    def set_prefix(self, keys):
        instr = self.set_prefix(keys)
        if instr == 'esi':
            self.prefix = 'EI'
        else:
            self.prefix = ''
