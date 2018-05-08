'''
This is the class to handle all the NIRES specific attributes
NIRES specific DR techniques can be added to it in the future

12/14/2017 M. Brown - Created initial file
'''

import instrument
import datetime as dt
from common import *

class Nires(instrument.Instrument):

    def __init__(self, instr, utDate, rootDir, log=None):

        # Call the parent init to get all the shared variables
        super().__init__(instr, utDate, rootDir, log)


        # Set any unique keyword index values here
        self.ofName = 'DATAFILE'        
        self.frameno = 'FRAMENUM'


        # Other vars that subclass can overwrite
        self.endTime = '19:00:00'   # 24 hour period start/end time (UT)



        # Generate the paths to the NIRES datadisk accounts
        self.sdataList = self.get_dir_list()


    def run_dqa_checks(self, progData):
        '''
        Run all DQA checks unique to this instrument.
        '''

        ok = True
        if ok: ok = self.check_instr()
        if ok: ok = self.set_dateObs()
        if ok: ok = self.set_utc()
        if ok: ok = self.set_elaptime()
        if ok: ok = self.set_koaimtyp()
        if ok: ok = self.set_koaid()
        if ok: ok = self.set_ut()
        if ok: ok = self.set_frameno()
        if ok: ok = self.set_ofName()
        if ok: ok = self.set_semester()
        if ok: ok = self.set_prog_info(progData)
        if ok: ok = self.set_propint()
        if ok: ok = self.set_wavelengths()
        if ok: ok = self.set_specres()

        #todo: finish setting remaining non-critical KOA-calculated keywords
        # DATLEVEL
        # DISPSCAL
        # DQA_DATE
        # DQA_VERS
        # GUIDFWHM
        # GUIDTIME
        # IMAGEMD
        # IMAGEMN
        # IMAGESD
        # NPIXSAT
        # OA
        # SLITLEN
        # SLITWIDT
        # SPATSCAL
        # WXDOMHUM
        # WXDOMTMP
        # WXDWPT
        # WXOUTHUM
        # WXOUTTMP
        # WXPRESS
        # WXTIME
        # WXWNDIR
        # WXWNDSP


        return ok



    def get_dir_list(self):
        '''
        Function to generate generates all the storage locations including engineering
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
        Adds FRAMENO keyword to header if it doesn't exist
        #NOTE: keyword FRAMENUM added in Apr 2018
        """
 
         #skip if it exists
        keys = self.fitsHeader
        if keys.get('FRAMENO') != None: return True


        #get value
        #NOTE: If FRAMENO doesn't exist, derive from DATAFILE
        frameno = keys.get(self.frameno)
        if (frameno == None): 

            datafile = keys.get('DATAFILE')
            if (datafile == None): 
                self.log.error('set_frameno: cannot find value for FRAMENO')
                return False

            frameno = datafile.replace('.fits', '')
            num = frameno.rfind('_') + 1
            frameno = frameno[num:]
            frameno = int(frameno)


        #update
        keys.update({'FRAMENO' : (frameno, 'KOA: Added keyword')})
        return True



    def set_ofName(self):
        """
        Adds OFNAME keyword to header if it doesn't exist
        #todo: Percy still needs to add ".fits" to end of DATAFILE keyword
        #todo: add *.fits to output if it does not exist? (to fix old files?)
        """

        #skip if it exists
        keys = self.fitsHeader
        if keys.get('OFNAME') != None: return True

        #get value
        ofName = keys.get(self.ofName)
        if (ofName == None): 
            self.log.error('set_ofName: cannot find value for OFNAME')
            return False

        #update
        keys.update({'OFNAME' : (ofName, 'KOA: Added keyword')})
        return True


    def set_elaptime(self):
        '''
        Fixes missing ELAPTIME keyword.
        '''

        keys = self.fitsHeader

        #skip if it exists
        if keys.get('ELAPTIME') != None: return True

        #get necessary keywords
        itime  = keys.get('ITIME')
        coadds = keys.get('COADDS')
        if (itime == None or coadds == None):
            self.log.error('ITIME and COADDS values needed to set ELAPTIME')
            return False

        #update val
        elaptime = itime * coadds
        keys.update({'ELAPTIME' : (elaptime, 'KOA: Added keyword')})
        return True
        

    def set_wavelengths(self):
        '''
        Adds wavelength keywords.
        # https://www.keck.hawaii.edu/realpublic/inst/nires/genspecs.html
        # NOTE: kfilter is always on
        '''

        keys = self.fitsHeader
        kfilter = True

        #with K-filter:
        if kfilter:
            keys.update({'WAVERED' : (19500, 'KOA: Added keyword')})
            keys.update({'WAVECNTR': (21230, 'KOA: Added keyword')})
            keys.update({'WAVEBLUE': (22950, 'KOA: Added keyword')})

        #no filter:
        else:
            keys.update({'WAVERED' : (9400,  'KOA: Added keyword')})
            keys.update({'WAVECNTR': (16950, 'KOA: Added keyword')})
            keys.update({'WAVEBLUE': (24500, 'KOA: Added keyword')})

        return True


    def set_specres(self):
        '''
        Adds nominal spectral resolution keyword
        '''
        keys = self.fitsHeader
        keys.update({'SPECRES' : (2700.0,  'KOA: Added keyword')})
        return True



    def set_koaimtyp(self):
        '''
        Fixes missing KOAIMTYP keyword.
        todo: This will come from OBSTYPE keyword.
        '''
        return True



    def is_science(self):
        '''
        Returns true if header indicates it was a science data was taken.
        '''

        #todo: finish this.  Based on KOAIMTYP='object'?
        return True