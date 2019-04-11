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

    #todo: make dep_add smarter about finding misplaced files and deal with corrupted files

    #shorthand
    instr  = instrObj.instr
    utDate = instrObj.utDate
    log    = instrObj.log
    dirs   = instrObj.dirs


    #Log start
    log.info('dep_add.py started for {} {}'.format(instr, utDate))


    #get telescope number
    telnr = instrObj.get_telnr()
    instrObj.log.info('dep_add.py: using telnr {}'.format(telnr))


    #get date vars
    year, month, day = instrObj.utDate.split('-')
    year = int(year) - 2000


    # Make ancDir/[nightly,udf]
    dirs = ['nightly', 'udf']
    for dir in dirs:
        ancDirNew = ''.join((instrObj.dirs['anc'], '/', dir))
        if not os.path.isdir(ancDirNew):
            instrObj.log.info('dep_add.py creating {}'.format(ancDirNew))
            os.makedirs(ancDirNew)


    #check for valid nightly dir
    nightlyDir = ''.join(('/s/nightly', str(telnr), '/', str(year), '/', month, '/', day))
    if not os.path.isdir(nightlyDir):
        nightlyDir = nightlyDir.replace('/s/', '/h/')
        if not os.path.isdir(nightlyDir):
            instrObj.log.warning('dep_add.py no nightly directory found')
            return


    # Copy nightly data to ancDir/nightly
    files = ['envMet.arT', 'envFocus.arT']
    for file in files:
        source = ''.join((nightlyDir, '/', file))
        if os.path.exists(source):
            destination = ''.join((instrObj.dirs['anc'], '/nightly/', file))
            instrObj.log.info('dep_add.py copying {} to {}'.format(source, destination))
            shutil.copyfile(source, destination)
        else:
            destination = None
            instrObj.log.warning('dep_add.py: Could not find {}'.format(source))


        #re-open file and look for bad lines with NUL chars and remove those lines and resave.
        #(The bad characters are a result of copying a file that is being modified every few seconds)
        if destination and os.path.exists(destination):
            newLines = []
            with open(destination, 'r') as f:
                for line in f:
                    if '\0' in line: continue
                    newLines.append(line)
            with open(destination, 'w') as f:
                f.write("".join(newLines))

    