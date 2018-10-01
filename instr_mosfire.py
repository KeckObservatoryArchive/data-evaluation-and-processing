'''
This is the class to handle all the MOSFIRE specific attributes
MOSFIRE specific DR techniques can be added to it in the future

12/14/2017 M. Brown - Created initial file
'''

import instrument
import datetime as dt
from common import *


class Mosfire(instrument.Instrument):
    
    def __init__(self, instr, utDate, rootDir, log=None):

        # Call the parent init to get all the shared variables
        super().__init__(instr, utDate, rootDir, log)


        # Set any unique keyword index values here
        self.ofName  = 'DATAFILE'        
        self.frameno = 'FRAMENUM'


        # Other vars that subclass can overwrite
        self.endTime = '20:00:00'   # 24 hour period start/end time (UT)


        # Generate the paths to the NIRES datadisk accounts
        self.sdataList = self.get_dir_list()


    def get_dir_list(self):
        '''
        Function to generate the paths to all the MOSFIRE accounts, including engineering
        Returns the list of paths
        '''
        dirs = []
        path = '/s/sdata1300'
        joinSeq = (path, '/mosfire')
        path2 = ''.join(joinSeq)
        dirs.append(path2)
        for i in range(1,10):
            joinSeq = (path, '/mosfire', str(i))
            path2 = ''.join(joinSeq)
            dirs.append(path2)
        joinSeq = (path, '/moseng')
        path2 = ''.join(joinSeq)
        dirs.append(path2)
        return dirs


    def set_prefix(self, keys):
        instr = self.set_instr(keys)
        if instr == 'mosfire':
            prefix = 'MF'
        else:
            prefix = ''
        return prefix


    def set_raw_fname(self, keys):
        """
        Overloaded method to construct the raw filename of the original file. 
        MOSFIRE stores the raw filename without the FITS extension in DATAFILE.

        @type keys: dictionary
        @param keys: FITS header file values
        """
        try:
            outfile = keys[self.ofName]
        except KeyError:
            return '', False
        else:
            filename = outfile
            if (filename.endsWith('.fits') == False) : filename += '.fits'
            return filename, True
