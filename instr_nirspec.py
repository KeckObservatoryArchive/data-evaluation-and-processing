'''
This is the class to handle all the NIRSPEC specific attributes
NIRSPEC specific DR techniques can be added to it in the future

12/14/2017 M. Brown - Created initial file
'''

import instrument
import datetime as dt

class Nirspec(instrument.Instrument):
    def __init__(self, endTime=dt.datetime.now(), rDir=''):
        # Call the parent init to get all the shared variables
        super().__init__(endTime, rDir)

        # NIRSPEC uses ROOTNAME instead of OUTDIR
        self.ofName = 'FILENAME'
        # NIRSPEC uses FILENUM and FILENUM2 so we'll
        # just use DATAFILE to get the name instead
        self.frameno = ''
        # Set the NIRSPEC specific paths to anc and stage
        seq = (self.rootDir, '/NIRSPEC/', self.utDate, '/anc')
        self.ancDir = ''.join(seq)
        seq = (self.rootDir, '/stage')
        self.stageDir = ''.join(seq)
        # Generate the paths to the NIRSPEC datadisk accounts
        self.paths = self.get_dir_list()


    def get_dir_list(self):
        '''
        Function to generate the paths to all the NIRSPEC accounts, including engineering
        Returns the list of paths
        '''
        dirs = []
        path = '/s/sdata90'
        for i in range(4):
            joinSeq = (path, str(i))
            path2 = ''.join(joinSeq)
            for j in range(1,21):
                joinSeq = (path2, '/nspec', str(j))
                path3 = ''.join(joinSeq)
                dirs.append(path3)
            joinSeq = (path2, '/nspeceng')
            path3 = ''.join(joinSeq)
            dirs.append(path3)
            joinSeq = (path2, 'nirspec')
            path3 = ''.join(joinSeq)
            dirs.append(path3)
        return dirs

    def set_prefix(self, keys):
        instr = self.set_instr(keys)
        if instr == 'nirspec':
            try:
                outdir = keys[self.outdir]
            except KeyError:
                prefix = ''
            else:
                if '/scam' in outdir:
                    prefix = 'NC'
                elif '/spec' in outdir:
                    prefix = 'NS'
                else:
                    prefix = ''
        else:
            prefix = ''
       return prefix

   def set_raw_fname(self, keys):
       """
       Overloaded method to retrieve the raw filename for
       the given FITS file. NIRSPEC uses two different keys
       for the frameno so we'll save a lot of headaches by
       using DATAFILE where it stores the raw filename.

       @type keys: dictionary
       @param keys: the header keys from a given FITS file
       """
       try:
           filename = keys[self.ofName]
       except KeyError:
           return '', False
       else:
           return filename, True
