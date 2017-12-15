'''
This is the class to handle all the ESI specific attributes
ESI specific DR techniques can be added to it in the future

12/14/2017 M. Brown - Created initial file
'''

class Esi(instrument.Instrument):
    def __init__(self):
        # Call the parent init to get all the shared variables
        super(Esi, self).__init__(self)

        # Set the esi specific paths to anc and stage
        self.ancDir = '/koadata29/ESI/' + self.reducedDate + '/anc'
        self.stageDir = '/koadata29/stage'
        # Generate the paths to the ESI datadisk accounts
        self.paths = self.getDirList()


    def getDirList(self):
        '''
        Function to generate the paths to all the ESI accounts, including engineering
        Returns the list of paths
        '''
        dirs = []
        path = '/s/sdata70'
        for i in range(8):
            if i != 5:
                path2 = path + str(i) = '/esi'
                for j in range(1,21):
                    path3 = path2 + str(j)
                    dirs.append(path3)
                dirs.append(path2 + 'eng')
        return dirs
