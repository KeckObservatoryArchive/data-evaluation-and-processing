from verification import *
import os
import shutil
import tarfile
import gzip
import hashlib
from create_log import create_log

class dep_add:
    """
    Class to create ancillary directory, copy log files to it and tar
    the contents.
    """

    def __init__(self, telNr, instr, utDate, rootDir, log_writer=''):
        """
        Verify input, create directory and setup log_writer, if needed

        @param telNr: Telescope number
        @type telnr: string
        @param instr: Instrument name
        @type instr: string
        @param utDate: UT date (yyyy-mm-dd)
        @type utDate: string
        @param rootDir: Root directory for data output
        @type rootDir: string
        """

        # Verify UT date

        verify_date(utDate)
        self.utDate = utDate.replace('/', '-')
        self.utDateDir = self.utDate.replace('-', '')

        # Verify telescope

        tel = [1, 2]
        assert telNr not in tel, 'telNr not allowed'
        self.telNr = telNr

        # Set and create log_writer

        if not log_writer:
            self.log_writer = create_log(rootDir, instr, utDate)
        else:
            self.log_writer = log_writer

        # Set and create ancillary directory

        assert rootDir != '', 'rootDir value is blank'
        joinSeq = (rootDir, '/', instr.upper(), '/', self.utDate.replace('-', ''), '/anc')
        self.ancDir = ''.join(joinSeq)
        if not os.path.isdir(self.ancDir):
            if log_writer:
                log_writer.info('dep_add.py creating {}'.format(self.ancDir))
            os.makedirs(self.ancDir)

    #-------

    def dep_add(self):
        """
        This function will add the weather and focus log files to 
        the ancillary directory.  Log files are copied from either
        /h/nightly#/yy/mm/dd or /s/nightly#/yy/mm/dd.
        """
        
        year, month, day = self.utDate.split('-')
        year = int(year) - 2000

        if self.log_writer:
            self.log_writer.info('dep_add.py started for telnr {} {}'.format(self.telNr, self.utDate))

        # Make ancDir/[nightly,udf]

        dirs = ['nightly', 'udf']
        for dir in dirs:
            ancDirNew = (self.ancDir, '/', dir)
            ancDirNew = ''.join(ancDirNew)
            if not os.path.isdir(ancDirNew):
                if self.log_writer:
                    self.log_writer.info('dep_add.py creating {}'.format(ancDirNew))
                os.makedirs(ancDirNew)

        # Copy nightly data to ancDir/nightly

        joinSeq = ('/h/nightly', str(self.telNr), '/', str(year), '/', month, '/', day)
        nightlyDir = ''.join(joinSeq)
        if not os.path.isdir(nightlyDir):
            nightlyDir.replace('/h/', '/s/')
            if not os.path.isdir(nightlyDir):
                if self.log_writer:
                    self.log_writer.info('dep_add.py no nightly directory found')
                return

        files = ['envMet.arT', 'envFocus.arT']
        for file in files:
            source = (nightlyDir, '/', file)
            source = ''.join(source)
            if os.path.exists(source):
                destination = (self.ancDir, '/nightly/', file)
                destination = ''.join(destination)
                if self.log_writer:
                    self.log_writer.info('dep_add.py copying {} to {}'.format(source, destination))
                shutil.copyfile(source, destination)

    #-------

    def dep_tar(self):
        """
        This function will tar the ancillary directory, gzip that
        tarball and remove the original contents of the directory.
        """
    
        if self.log_writer:
            self.log_writer.info('dep_tar.py started for {}'.format(self.ancDir))

        if os.path.isdir(self.ancDir):

            # Tarball name
    
            tarFileName = ('anc', self.utDateDir, '.tar')
            tarFileName = ''.join(tarFileName)
    
            # Go to directory and create tarball

            if self.log_writer:
                self.log_writer.info('dep_tar.py creating {}'.format(tarFileName))
            os.chdir(self.ancDir)
            with tarfile.open(tarFileName, 'w:gz') as tar:
                tar.add('./')

            # gzip the tarball

            if self.log_writer:
                self.log_writer.info('dep_tar.py gzipping {}'.format(tarFileName))
            gzipTarFile = (tarFileName, '.gz')
            gzipTarFile = ''.join(gzipTarFile)
            with open(tarFileName, 'rb') as fIn:
                with gzip.open(gzipTarFile, 'wb') as fOut:
                    shutil.copyfileobj(fIn, fOut)

            # Remove the original tar file

            os.remove(tarFileName)
    
            # Create md5sum of the tarball

            md5sumFile = gzipTarFile.replace('tar.gz', 'md5sum')

            if self.log_writer:
                self.log_writer.info('dep_tar.py creating {}'.format(md5sumFile))

            md5 = hashlib.md5(open(gzipTarFile, 'rb').read()).hexdigest()

            with open(md5sumFile, 'w') as f:
                md5 = (md5, '  ', gzipTarFile)
                md5 = ''.join(md5)
                f.write(md5)

            dirs = ['nightly', 'udf']
            for dir in dirs:
                delDir = (self.ancDir, '/', dir)
                delDir = ''.join(delDir)
                if not os.path.isdir(delDir): continue
                if self.log_writer:
                    self.log_writer.info('dep_tar.py removing {}'.format(delDir))
                shutil.rmtree(delDir)

    #-------
