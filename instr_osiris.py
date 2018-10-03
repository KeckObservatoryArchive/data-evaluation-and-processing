'''
This is the class to handle all the OSIRIS specific attributes
OSIRIS specific DR techniques can be added to it in the future

12/14/2017 M. Brown - Created initial file
'''

import instrument
import datetime as dt

class Osiris(instrument.Instrument):
    def __init__(self, endTime=dt.datetime.now(), rDir=''):
        # Call the parent init to get all the shared variables
        super().__init__(endTime, rDir)

        # OSIRIS has 'DATAFILE' instead of OUTFILE
        self.ofName = 'DATAFILE'
        # Set the OSIRIS specific paths to anc and stage
        seq = (self.rootDir, '/OSIRIS/', self.utDate, '/anc')
        self.ancDir = ''.join(seq)
        seq = (self.rootDir, '/stage')
        self.stageDir = ''.join(seq)
        # Generate the paths to the OSIRIS datadisk accounts
        self.paths = self.get_dir_list()

    def get_dir_list(self):
        '''
        Function to generate the paths to all the OSIRIS accounts, including engineering
        Returns the list of paths
        '''
        dirs = []
        path = '/s/sdata110'
        for i in range (2):
            seq = (path, str(i))
            path2 = ''.join(seq)
            seq = (path2, '/osiris')
            dirs.append(''.join(seq))
            for j in range(1,21):
                seq = (path, '/osiris', str(j))
                path3 = ''.join(seq)
                dirs.append(path3)
            seq = (path2, '/osiriseng')
            dirs.append(''.join(seq))
            seq = (path2, '/osrseng')
            dirs.append(''.join(seq))
        return dirs

    def get_prefix(self, keys):
        instr = self.get_instr(keys)
        if instr == 'osiris':
            try:
                outdir = keys[self.outdir]
            except KeyError:
                prefix = ''
            else:
                if '/scam' in outdir:
                    prefix = 'OI'
                elif '/spec' in outdir:
                    prefix = 'OS'
                else:
                    prefix = ''
        else:
           prefix = ''
        return prefix

