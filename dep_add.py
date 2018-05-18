import os
import shutil
import tarfile
import gzip
import hashlib

import common



def dep_add(instrObj):
    """
    Add the weather and focus log files to the ancillary directory.  
    Log files are copied from either /h/nightly#/yy/mm/dd or /s/nightly#/yy/mm/dd.

    @type instrObj: instrument
    @param instr: The instrument object
    """


    #Check anc dir exists
    assert os.path.isdir(instrObj.dirs['anc']), 'Ancillary dir does not exist.'


    #get telescope number and validate 
    telnr = instrObj.get_telnr()


    #log start
    instrObj.log.info('dep_add.py started for telnr {} {}'.format(telnr, instrObj.utDate))


    #get date vars
    year, month, day = instrObj.utDate.split('-')
    year = int(year) - 2000


    # Make ancDir/[nightly,udf]
    dirs = ['nightly', 'udf']
    for dir in dirs:
        ancDirNew = (instrObj.dirs['anc'], '/', dir)
        ancDirNew = ''.join(ancDirNew)
        if not os.path.isdir(ancDirNew):
            instrObj.log.info('dep_add.py creating {}'.format(ancDirNew))
            os.makedirs(ancDirNew)


    #check for valid nightly dir
    joinSeq = ('/h/nightly', str(telnr), '/', str(year), '/', month, '/', day)
    nightlyDir = ''.join(joinSeq)
    if not os.path.isdir(nightlyDir):
        nightlyDir.replace('/h/', '/s/')
        if not os.path.isdir(nightlyDir):
            instrObj.log.info('dep_add.py no nightly directory found')
            return


    # Copy nightly data to ancDir/nightly
    files = ['envMet.arT', 'envFocus.arT']
    for file in files:
        source = (nightlyDir, '/', file)
        source = ''.join(source)
        if os.path.exists(source):
            destination = (instrObj.dirs['anc'], '/nightly/', file)
            destination = ''.join(destination)
            instrObj.log.info('dep_add.py copying {} to {}'.format(source, destination))
            shutil.copyfile(source, destination)


