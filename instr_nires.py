'''
This is the class to handle all the NIRES specific attributes
NIRES specific DR techniques can be added to it in the future

12/14/2017 M. Brown - Created initial file
'''

import instrument
import datetime as dt
from common import *

class Nires(instrument.Instrument):
    def __init__(self, rootDir, utDate, log_writer):

        # Input parameters

        self.rootDir = rootDir
        self.utDate = utDate

        # Call the parent init to get all the shared variables

        super().__init__(rootDir)

        # Logging

        self.log_writer = log_writer

        # Set the NIRES specific paths to lev0 and anc

        self.dirs = get_root_dirs(self.rootDir, 'NIRES', self.utDate)

        # NIRES uses DATAFILE instead of OUTFILE

        self.ofName = 'DATAFILE'

#        # NIRES does not have a frameno keyword, use datafile
#
#        self.frameno = self.get_frameno()

        # Generate the paths to the NIRES datadisk accounts
        self.sdataList = self.get_dir_list()

    def get_dir_list(self):
        '''
        Function to generate the paths to all the DEIMOS accounts, including engineering
        Returns the list of paths
        '''
        dirs = []
        path = '/s/sdata150'
        for i in range(1,4):
            joinSeq = (path, str(i))
            path2 = ''.join(joinSeq)
            dirs.append(path2 + '/nireseng')
            for j in range(1, 10):
                path3 = ''.join((path2, '/nires', str(j)))
                dirs.append(path3)
        return dirs

    def set_prefix(self, keys):
        '''
        Sets the KOAID prefix
        Defaults to nullstr
        '''

        # Will there be a single keyword for this?

        instr = self.set_instr(keys)
        if instr == 'nires':
            try:
                ftype = keys['INSTR']
            except KeyError:
                prefix = ''
            else:
                if ftype == 'imag':
                    prefix = 'NI'
                elif ftype == 'spec':
                    prefix = 'NR'
                else:
                    prefix = ''
        else:
            prefix = ''
        return prefix

    def set_raw_fname(self, keys):
        """
        Overloaded method to create the NIRES rawfile name
        NIRES uses DATAFILE to retrieve the filename without
        the FITS extension, so we have to add that back on

        @type keys: dictionary
        @param keys: FITS header keys for th given file
        """
        try:
            outfile = keys[self.ofName]
        except KeyError:
            return '', False
        else:
            seq = (outfile, '.fits')
            filename = ''.join(seq)
            return filename, True

    def get_frameno(self):
        """
        Determines the frame number from the FITS file name stored
        in the DATAFIILE keyword
        """

        test = 's180404_0002.fits'
        test = test.replace('.fits', '')
        num = test.rfind('_') + 1
        return int(test[num:])
