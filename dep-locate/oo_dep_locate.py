"""
  This script consolidates all the pieces of the KOA archival dep-locate
  function into one place. It mainly consists of dep_locate.csh,
  dep_locfiles.c, dep_rawfiles.csh, and deimos_find_fcs.csh.
  Upon completion, it should return a list of the fits files for a 
  given instrument within 24 hours of the supplied date.

  Usage dep_locate INSTRUMENT howhold

  Original scripts written by Jeff Mader and Jennifer Holt
  Ported to Python3 by Matthew Brown
"""

import list_instr_dirs as locate
import calendar as cal
import time as t
from astropy.io import fits
from common import koaid
import os
import verification
import shutil

def dep_locate(obj):
    """ 
    This function will search the data directories for 
    data  written in the last howold*24 hours.
    Pre-condition: Requires an instrument, a date to check in UTC time, 
        and a staging directory
    Post-condition: Returns all the fits files 
        within 24 hours of the date given
    
    @type instr: string
    @param instr: The instrument used to make the fits files being looked at
    @type utDate: datetime
    @param utDate: The date in UT of the night that the fits tiles were taken
    @type stageDir: string
    @param stageDir: The staging area to store the files for transport to KOA
    """
    # Verify instrument and date are in the correct format
    verification.verify_instrument(obj.instr)
    verification.verify_date(obj.utDate)

    # Create stage and anc directory strings
    obj.stageDir = ''.join((obj.rootDir, '/stage/', obj.utDate))
    obj.ancDir = ''.join((obj.rootDir, '/', obj.utDate, '/anc'))

    # Make sure the staging directory is not blank
    assert obj.stageDir != '', 'stageDir value is blank'

    # Create the udf directory in the anc_dir
    try:
        udfDir = ''.join((obj.ancDir, '/udf'))
        os.makedirs(udfDir)
    except FileExistsError:
        obj.log.warning('udf directory already exists!')
    except:
        obj.log.error('Unable to create udf directory!')
        return

    # Create the stage directory
    try:
        os.makedirs(obj.stageDir)
    except FileExistsError:
        obj.log.warning('stage directory already exists!')
    except:
        obj.log.error('Unable to create stage directory!')
        return

    # Which sdata disk?
    usedir = locate.get_dir_list(obj.instr, obj.log)

    # if locate did not return any dirs, we exit
    if len(usedir) == 0:
        obj.log.warning('did not find any directories')
        return

    # Create files to store the valid FITS files
    presort = ''.join((obj.stageDir, '/dep_locate', obj.instr, 'pre.text'))
    files = ''.join((obj.stageDir, '/dep_locate', obj.instr, '.txt'))

    # Find the files in the last 24 hours
    pyfind(usedir, obj.utDate, obj.endHour, presort, obj.log)

    # We only wants the .fits files
    with open(files, 'w') as f:
        with open(presort, 'r') as pre:
            fcsConfigs = []
            for line in pre:
                if ('.fits' in line 
                        and '/fcs' not in line 
                        and 'mira' not in line 
                        and 'savier-protected' not in line 
                        and 'idf' not in line):
                    # Copy the files to stageDir and update files 
                    # to use local copy file list
                    newFile = ''.join((obj.stageDir, line.strip()))
                    copy_file(line.strip(), newFile)

                    toFile = ''.join((newFile, '\n'))
                    f.write(toFile)
                    if 'DEIMOS' in obj.instr:
                        try:
                            fcs = fits.getheader(line.strip())['FCSIMGFI']
                            if fcs != '' and fcs not in fcsConfigs:
                                fcsConfigs.append(fcs)
                                if '/s/' not in fcs:
                                    fcs = '/s' + fcs
                                newFile = ''.join((obj.stageDir, fcs))
                                copy_file(fcs, newFile)

                                toFile = ''.join((newFile, '\n'))
                                f.write(toFile)
                        except:
                            pass
            del fcsConfigs

    # Remove temporary file
    os.remove(presort)
    obj.log.info(
            '{}: removed temporary presorted file {}'.format(obj.instr, presort))
    
    # Verify the files are valid - no corrupt headers, valid KOAID
    dep_rawfiles(obj.instr, obj.utDate, obj.endHour,
            files, obj.stageDir, obj.ancDir, obj.log)
    obj.log.info(
            '{0}: finished rawfiles {0} {1} {2} {3} {4}'.format(
                obj.instr, obj.utDate, obj.endHour, obj.stageDir, obj.ancDir))

    obj.log.info('{}: Using files found in {}'.format(obj.instr, usedir))
    obj.log.info('{}: dep_locate successful'.format(obj.instr))

#-----------------------END DEP LOCATE----------------------------------

def copy_file(source, destination):
    '''
    Copy source file to destination.  If destination directory does nott
    exist, then create it.

    @type source: string
    @param source: The source file path
    @type destination: string
    @param destination: The destination file path
    '''

    rDir = os.path.dirname(destination)
    if not os.path.exists(rDir):
        os.makedirs(rDir)
    if not os.path.exists(destination):
        shutil.copy2(source, destination)

#----------------------END COPY FILE----------------------------------

def dep_rawfiles(obj, fileList):
    """
    This function will look for non-raw images, duplicate KOAIDs, 
    or bad dates for each fits file. 
      
    Written by Jeff Mader
    
    Ported to Python3 by Matthew Brown

    @type instr: string
    @param instr: The instrument used to make the fits files being looked at
    @type utDate: datetime
    @param utDate: The date in UT of the night that the fits tiles were taken
    @type endHour: datetime
    @param endHour: The hour that the observations ended
    @type fileList: string
    @param fileList: Text file that contains the fits filenames 
            that occured within 24 hours of the given date
    @type stageDir: string
    @param stageDir: The staging area to store the files for transport to KOA
    @type ancDir: string
    @param ancDir: The anc directory to store the bad and corrupted fits files
    @type obj.log: Logger Object
    @param obj.log: The log handler for the script. Writes to the logfile
    """
    year = obj.utDate[:4]
    month = obj.utDate[4:6]
    day = obj.utDate[6:]

    # read input file list into an array
    fitsList = []

    # Loop through the file list and read in
    # the fits files found from within 24 hours
    # of the given date
    with open(fileList, 'r') as ffiles:
        for line in ffiles:
            fitsList.append(line.strip())

    # lsize = list size: get the size of the file list 
    lsize = len(fitsList)

    # Initialize lists with the number of fits files found
    raw = [0]*lsize
    koa = ['0']*lsize
    rootfile = ['0']*lsize

    # Each line in the file list is a fits file
    # We want to check the validity of each file
    for i in range(lsize):
        raw[i] = 0

        # Get the header of the current fits file
        header0 = fits.getheader(fitsList[i])

        # Break the file path into a list
        root = fitsList[i].split('/')

        # Grab the last element in the filepath list
        # This should be the filename *.fits
        rootfile[i] = root[-1]

        # Construct the original file name
        obj.rawfile, successful = obj.set_raw_fname(header0)
        if not successful:
            copy_bad_file(obj.instr, fitsList[i], 
                    obj.ancDir, 'Bad KOAID', obj.log)
            raw[i] = 2
            continue

        # Get KOAID
        obj.koaid, successful = obj.make_koaid(header0)
        if not successful:
            copy_bad_file(obj.instr, fitsList[i], obj.ancDir, 
                    'Bad KOAID', obj.log)
            raw[i] = 2
            continue
        koa[i] = obj.koaid

        # If filename is rootfile then file is a raw image
        if obj.rawfile == rootfile[i]:
            raw[i] = 1

    endtime = float(obj.endHour) * 3600.0

    for i in range(len(fitsList)-1):
        # Is this a duplicate KOAID?
        if raw[i] == 2:
            continue
        elif raw[i] == 0:
            for j in range(i+1,len(fitsList)):
                if koa[j]==koa[i]: # j should always be greater than i
                    copy_bad_file(
                            obj.instr, fitsList[i], obj.ancDir,
                            'Duplicate KOAID', obj.log)
                    break

        # Check the date
        prefix, fdate, ftime, postfix = koa[i].split('.')
        if fdate != obj.utDate and float(ftime) < endtime:
            copy_bad_file(obj.instr, fitsList[i],
                    obj.ancDir, 'KOADATE', obj.log)
            break

    # Need to remove "bad" files from dep_locateINSTR.txt in stageDir
    ffiles = open(fileList, 'r')
    lines = ffiles.readlines()
    ffiles.close()
    # Recreate the file with only the good lines
    with open(fileList, 'w') as ffiles:
        for line in lines:
            if line.strip() in fitsList:
                num = fitsList.index(line.strip())
                if raw[num] == 1:
                    ffiles.write(line)

#------------------END RAWFILES-----------------------------

def copy_bad_file(instr, fitsFile, ancDir, errorCode, log):
    """ 
    Log the error where the fits file failed 
    and copy the fits file to the anc directory

    This function logs the type of error encountered 
    and moves the bad fits file to anc_dir/udf
    
    @type instr: string
    @param instr: The keyword for the instrument being searched
    @type fitsFile: string
    @param fitsFile: The filename of the fits file being observed
    @type ancDir: string
    @param ancDir: The path to the anc directory
    @type errorCode: string
    @param errorCode: How the fits file failed. Used in the logging
    @type obj.log: Logger Object
    @param obj.log: The log handler for the script. Writes to the logfile
    """
    if errorCode == 'KOADATE':
        log.warning(
                'rawfiles {}: KOAID not correct date for {}'.format(instr, fitsFile))
    else:
        log.warning(
                'rawfiles {}: {} found for {}'.format(instr, errorCode, fitsFile))
    log.info(
            'rawfiles {}: Copying {} to {}/udf'.format(instr, fitsFile, ancDir))
    udfDir = ''.join((ancDir,'/udf/'))
    try:
        # Use copy2 from shutil to copy the file with its metadata
        shutil.copy2(fitsFile, udfDir)
    except:
        log.error('{}: {} file was not copied!'.format(instr, fitsFile))

#-------------End copy-bad-file()---------------------------

def pyfind(usedir, utDate, endHour, outfile, log):
    """
    Uses the os.walk function to recurse through a given directory
    and return all the leaf files which are checked to be
    fits files.

    @type usedir: string
    @param usedir: The directory that we want to search in
    @type utDate: datetime
    @param utDate: The date of observation of the files we want to search for
    @type outfile: string
    @param outfile: Where we want to store the output
    @type log: Logger Object
    @param log: The log handler for the script. Writes to the logfile
    """
    # Break utDate into its pieces
    year = utDate[:4]
    month = utDate[4:6]
    day = utDate[6:]
    # Set up our +/-24 hour boundary
    dayMin = int(day) - 1
    dayMax = int(day)# + 1

    # Create a string date and time to convert to seconds since epoch
    utMaxTime = ''.join((str(year), str(month), 
            str(dayMax), ' ', str(endHour), ':00:00'))
    utMinTime = ''.join((str(year), str(month), 
            str(dayMin), ' ', str(endHour), ':00:00'))

    # st_mtime records the time in seconds of the last file modification since 
    # Jan 1 1970 00:00:00 UTC We need to create a time_construct object 
    # (using time.strptime()) to convert to seconds (using calendar.timegm())
    # All valid files should fall within these boundaries
    maxTimeSinceMod = cal.timegm(t.strptime(utMaxTime, '%Y%m%d %H:%M:%S'))
    minTimeSinceMod = cal.timegm(t.strptime(utMinTime, '%Y%m%d %H:%M:%S'))

    # Open the destination file to write to
    with open(outfile, 'w') as ofile:
        # Iterate through the list of directories from the locate script
        for fitsDir in usedir:
            # Do a walk through the given directory
            for root, dirs, files in os.walk(fitsDir):
                # Iterate through the leaf files in the directory
                for item in files:
                    # Create the path to the current file we want to check
                    full_path = ''.join((root, '/', item))
                    # Check to see if the file is a fits file created/modified
                    # in the last day. st_mtime needs to be greater than the
                    # minTimeSinceMod to be within the past 24 hours
                    modTime = os.stat(full_path).st_mtime
                    if ('.fits' in item[-5:] 
                            and modTime <= maxTimeSinceMod 
                            and modTime > minTimeSinceMod):
                        toFile = ''.join((full_path, '\n'))
                        ofile.write(toFile)

    # Append the action to the log
    log.info(
            'Copied fits file names from {} to {}'.format(usedir, outfile))


#-----------------------End PyFind-----------------------------------


