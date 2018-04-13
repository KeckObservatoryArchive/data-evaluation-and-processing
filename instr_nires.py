'''
This is the class to handle all the NIRES specific attributes
NIRES specific DR techniques can be added to it in the future

12/14/2017 M. Brown - Created initial file
'''

import instrument
import datetime as dt
from common import *

class Nires(instrument.Instrument):

    def __init__(self, instr, utDate, rootDir, log):

        # Call the parent init to get all the shared variables
        super().__init__(instr, utDate, rootDir, log)


        # Set any unique keyword index values here
        self.ofName = 'DATAFILE'        # NIRES uses DATAFILE instead of OUTFILE


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
        #todo: Will there be a single keyword for this?

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
        @param keys: FITS header keys for the given file
        """
        try:
            outfile = keys[self.ofName]
        except KeyError:
            return '', False
        else:
            seq = (outfile, '.fits')
            filename = ''.join(seq)
            return filename, True


    def set_frameno(self):
        """
        If FRAMENO doesn't exist, this will determine the frame number from        
        the DATAFIILE keyword (eg DATAFILE = 's180404_0002.fits') 
        and update the keyword.
 
        #todo: did we get new keyword in header?
        """
 
        keys = self.fits_header
        frameno = keys.get(self.frameno)

        if (frameno == None):

            datafile = keys.get('DATAFILE')
            if (datafile == None): return False

            frameno = datafile.replace('.fits', '')
            num = frameno.rfind('_') + 1
            frameno = frameno[num:]
            keys.update({self.frameno : (frameno, 'KOA: Added missing keyword')})

        return True


    def set_ofName(self):
        """
        If OUTFILE doesn't exist, this will determine the name from 
        the DATAFIILE keyword (eg DATAFILE = 's180404_0002.fits') 
        and update the keyword.
 
        #todo: did we get new keyword in header?
        """
 
        keys = self.fits_header
        ofName = keys.get(self.ofName)

        if (ofName == None):

            datafile = keys.get('DATAFILE')
            if (datafile == None): return False

            ofName = datafile.replace('.fits', '')
            keys.update({self.ofName : (ofName, 'KOA: Added missing keyword')})

        return True


    def get_outdir(self):
        """
        Returns the OUTDIR associated with the filename, else returns None.
        OUTDIR = [/s]/sdata####/account/YYYYmmmDD
 
        #todo: did we get new keyword in header?
        """

        filename = self.fits_filename

        try:
            # Find the first /s for /s/sdata... or /sdata...
            start = filename.find('/s')
            # Find the last / before FITS file name
            end = filename.rfind('/')
            return filename[start:end]
        except:
            #todo: really return "None"?
            return "None"


    def get_fileno(self):

        #todo: determine NIRES fileno
        fileno = None
        return fileno
    
