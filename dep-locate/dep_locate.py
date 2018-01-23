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

import logging as lg                 ## Used for all the logging
import list_instr_dirs as locate     ## Used to create the directories of the instrument
import calendar as cal               ## Used to convert a time object into a number of seconds
import time as t                     ## Used to convert a string date into a time object
from astropy.io import fits          ## Used for everything with fits
from common import koaid             ## Used to determine the KOAID of a file for transport
import os
import verification
import shutil
from sys import argv

def dep_locate(instr, utDate, rootDir, endHour):
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

    # Create stage and anc directory strings
    dateDir = utDate.replace('-', '')
    dateDir = dateDir.replace('/', '')

    joinSeq = (rootDir, '/stage/', instr, '/', dateDir)
    stageDir = ''.join(joinSeq)

    joinSeq = (rootDir, '/', instr, '/', dateDir, '/anc')
    ancDir = ''.join(joinSeq)

    ### Set up logging ###
    user = os.getlogin()
    joinSeq = ('dep_locate <', user, '>')
    writerName = ''.join(joinSeq)
    log_writer = lg.getLogger(writerName)
    log_writer.setLevel(lg.INFO)
    
    # create a file handler
    joinSeq = (rootDir, '/', instr, '/', instr, '_', dateDir, '.log')
    log_file = ''.join(joinSeq)
    log_handler = lg.FileHandler(log_file)
    log_handler.setLevel(lg.INFO)
    
    # Create a logging format
    formatter = lg.Formatter('%(asctime)s - %(name)s - %(levelname)s: %(message)s')
    log_handler.setFormatter(formatter)
    
    # add handlers to the logger
    log_writer.addHandler(log_handler)

    # Verify instrument and date are in the correct format
    verification.verify_instrument(instr)
    verification.verify_date(utDate)

    # Make sure the staging directory is not blank
    assert stageDir != '', 'stageDir value is blank'

    # Create the udf directory in the anc_dir
    try:
        joinSeq = (ancDir, '/udf')
        udfDir = ''.join(joinSeq)
        os.makedirs(udfDir)
        log_writer.info('udf directory created')
    except FileExistsError:
        log_writer.warning('udf directory already exists!')
    except:
        log_writer.error('Unable to create udf directory!')
        return

    # Create the stage directory
    try:
        os.makedirs(stageDir)
        log_writer.info('stage directory created')
    except FileExistsError:
        log_writer.warning('stage directory already exists!')
    except:
        log_writer.error('Unable to create stage directory!')
        return

    # Which sdata disk?
    usedir = locate.getDirList(instr, log_writer)

    # if locate did not return any dirs, we exit
    if len(usedir) == 0:
        log_writer.warning('did not find any directories')
        return

    # Create files to store the valid FITS files
    joinSeq = (stageDir, '/dep_locate', instr, 'pre.text')
    presort = ''.join(joinSeq)

    joinSeq = (stageDir, '/dep_locate', instr, '.txt')
    files = ''.join(joinSeq)

    # Find the files in the last 24 hours
    log_writer.info('looking for FITS files')
    pyfind(usedir, utDate, endHour, presort, log_writer)

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
                    joinSeq = (stageDir, line.strip())
                    newFile = ''.join(joinSeq)
                    log_writer.info('copying file {} to {}'.format(line.strip(), newFile))
                    copy_file(line.strip(), newFile)

                    joinSeq = (newFile, '\n')
                    toFile = ''.join(joinSeq)
                    f.write(toFile)
                    if 'DEIMOS' in instr:
                        try:
                            fcs = fits.getheader(line.strip())['FCSIMGFI']
                            if fcs != '' and fcs not in fcsConfigs:
                                fcsConfigs.append(fcs)
                                if '/s/' not in fcs:
                                    fcs = '/s' + fcs
                                joinSeq = (stageDir, fcs)
                                newFile = ''.join(joinSeq)
                                copy_file(fcs, newFile)

                                joinSeq = (newFile, '\n')
                                toFile = ''.join(joinSeq)
                                f.write(toFile)
                        except:
                            pass
            del fcsConfigs

    # Remove temporary file
    os.remove(presort)
    log_writer.info(
            '{}: removed temporary presorted file {}'.format(instr, presort))
    
    # Verify the files are valid - no corrupt headers, valid KOAID
    dep_rawfiles(instr, utDate, endHour, files, stageDir, ancDir, log_writer)
    log_writer.info(
            '{0}: finished rawfiles {0} {1} {2} {3} {4}'.format(instr, utDate, endHour, stageDir, ancDir))

    num = sum(1 for line in open(files, 'r'))
    log_writer.info('{}: Using files found in {}'.format(instr, usedir))
    log_writer.info('{}: dep_locate successful - {} files found'.format(instr, num))

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

def dep_rawfiles(
        instr, utDate, endHour, fileList, stageDir, ancDir, log_writer):
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
    @type log_writer: Logger Object
    @param log_writer: The log handler for the script. Writes to the logfile
    """
    # Change yyyy/mm/dd to yyyymmdd
    if '/' in utDate:
        year, month, day = utDate.split('/')
    elif '-' in utDate:
        year, month, day = utDate.split('-')
    date = year + month + day

    # read input file list into an array
    fitsList = []

    # Loop through the file list and read in
    # the fits files found from within 24 hours
    # of the given date
    print(fileList)
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
        if instr == 'NIRC2':
            header0 = fits.getheader(fitsList[i], ignore_missing_end=True)
            header0['INSTRUME'] = 'NIRC2'
        else:
            header0 = fits.getheader(fitsList[i])

        # Break the file path into a list
        root = fitsList[i].split('/')

        # Grab the last element in the filepath list
        # This should be the filename *.fits
        rootfile[i] = root[-1]

        # Construct the original file name
        filename, successful = construct_filename(instr,fitsList[i], 
                ancDir, header0, log_writer)
        if not successful:
            move_bad_file(instr, fitsList[i], ancDir, 'Bad Header', log_writer)
            raw[i] = 2
            continue

        # Get KOAID
        if not koaid(header0, utDate):
            move_bad_file(instr, fitsList[i], ancDir, 'Bad KOAID', log_writer)
            raw[i] = 2
            continue
        try:
            koa[i] = header0['KOAID']
        except KeyError:
            koa[i] = ''

        # If filename is rootfile then file is a raw image
        if filename == rootfile[i]:
            raw[i] = 1

    endtime = float(endHour) * 3600.0

    for i in range(len(fitsList)-1):
        # Is this a duplicate KOAID?
        if raw[i] == 2:
            continue
        elif raw[i] == 0:
            for j in range(i+1,len(fitsList)):
                if koa[j]==koa[i]: # j will always be greater than i
                    move_bad_file(
                            instr, fitsList[i], ancDir, 
                            'Duplicate KOAID', log_writer)
                    break

        # Check the date
        prefix, fdate, ftime, postfix = koa[i].split('.')
        if fdate != date and float(ftime) < endtime:
            move_bad_file(instr, fitsList[i], ancDir, 'KOADATE', log_writer)
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

def move_bad_file(instr, fitsFile, ancDir, errorCode, log_writer):
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
    @type log_writer: Logger Object
    @param log_writer: The log handler for the script. Writes to the logfile
    """
    if errorCode == 'KOADATE':
        log_writer.warning(
                'rawfiles {}: KOAID not correct date for {}'.format(instr, fitsFile))
    else:
        log_writer.warning(
                'rawfiles {}: {} found for {}'.format(instr, errorCode, fitsFile))
    log_writer.info(
            'rawfiles {}: Copying {} to {}/udf'.format(instr, fitsFile, ancDir))
    udfDir = ancDir + '/udf/'
    try:
        # Use copy2 from shutil to copy the file with its metadata
        shutil.copy2(fitsFile, udfDir)
    except:
        log_writer.error('{}: {} file was not copied!'.format(instr, fitsFile))

#-------------End move-bad-file()---------------------------

def construct_filename(instr, fitsFile, ancDir, keywords, log_writer):
   """
    Constructs the original filename from the fits header keywords

    @type instr: string
    @param instr: The keyword for the instrument
    @type fitsFile: string
    @param fitsFile: The current fits file being observed
    @type ancDir: str
    @param ancDir: The anc directory to move bad files
    @type keywords: dictionary
    @param keywords: The pairing of all the fits keywords with their values
    @type log_writer: Logger Object
    @param log_writer: The log handler for the script. Writes to the logfile
   """
   if instr == 'OSIRIS': # Osiris already has the raw filename under DATAFILE
       filename = keywords['DATAFILE']
       # but the i file needs .fits added to it
       if filename[0] == 'i':
           joinSeq = (filename, '.fits')
           filename = ''.join(joinSeq)
       return filename, True
   elif instr == 'MOSFIRE':
       try:
           outfile = keywords['DATAFILE']
           if '.fits' not in outfile:
               joinSeq = (outfile, '.fits')
               outfile = ''.join(joinSeq)
           return outfile, True
       except KeyError:
           move_bad_file(
                   instr, fitsFile, ancDir, 'Bad Outfile', log_writer)
           return '', False
   elif instr == 'KCWI':
       try:
           outfile = keywords['OFNAME']
           return outfile, True
       except KeyError:
           move_bad_file(
                   instr, fitsFile, ancDir, 'Bad Outfile', log_writer)
           return '', False
   else:
       try:
           outfile = keywords['OUTFILE']
       except KeyError:
           try:
               outfile = keywords['ROOTNAME']
           except KeyError:
               try:
                   outfile = keywords['FILENAME']
               except KeyError:
                   move_bad_file(
                           instr, fitsFile, ancDir, 'Bad Outfile', log_writer)
                   return '', False

   # Get the frame number of the file
   if outfile[:2] == 'kf':
       frameno = keywords['IMGNUM']
   elif instr == 'MOSFIRE':
       frameno = keywords['FRAMENUM']
   else:
       try:
           frameno = keywords['FRAMENO']
       except KeyError:
           try:
               frameno = keywords['FILENUM']
           except KeyError:
               try:
                   frameno = keywords['FILENUM2']
               except KeyError:
                   move_bad_file(
                           instr, fitsFile, ancDir, 'Bad Frameno', log_writer)
                   return '', False

   # Determine the amount of 0 padding that must be done
   zero = ''
   if float(frameno) < 10:
       zero = '000'
   elif float(frameno) >= 10 and float(frameno) < 100:
       zero = '00'
   elif float(frameno) >= 100 and float(frameno) < 1000:
       zero = '0'
   
   # Construct the original file name from the previous parts
   joinSeq = (outfile.strip(), zero, str(frameno).strip(), '.fits')
   filename = ''.join(joinSeq)
   return filename, True

#---------------------End construct_filename-------------------------

def pyfind(usedir, utDate, endHour, outfile, log_writer):
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
    @type log_writer: Logger Object
    @param log_writer: The log handler for the script. Writes to the logfile
    """
    # Break utDate into its pieces
    if '/' in utDate:
        year, month, day = utDate.split('/')
    elif '-' in utDate:
        year, month, day = utDate.split('-')
    # Set up our +/-24 hour boundary
    dayMin = int(day) - 1
    dayMax = int(day)# + 1

    # Create a string date and time to convert to seconds since epoch
    joinSeq = (str(year), str(month), str(dayMax), ' ', str(endHour), ':00:00')
    utMaxTime = ''.join(joinSeq)

    joinSeq = (str(year), str(month), str(dayMin), ' ', str(endHour), ':00:00')
    utMinTime = ''.join(joinSeq)
    
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
                    if not '.fits' in item:
                        continue
                    # Create the path to the current file we want to check
                    joinSeq = (root, '/', item)
                    full_path = ''.join(joinSeq)
                    # Check to see if the file is a fits file created/modified
                    # in the last day. st_mtime needs to be greater than the m
                    # inTimeSinceMod to be within the past 24 hours
                    modTime = os.stat(full_path).st_mtime
                    if ('.fits' in item[-5:] 
                            and modTime <= maxTimeSinceMod 
                            and modTime > minTimeSinceMod):
                        joinSeq = (full_path, '\n')
                        toFile = ''.join(joinSeq)
                        ofile.write(toFile)

    # Append the action to the log
    log_writer.info(
            'Copied fits file names from {} to {}'.format(usedir, outfile))


#-----------------------End PyFind-----------------------------------



print(len(argv))
if len(argv) == 5:
    print(argv[1])
    print(argv[2])
    print(argv[3])
    print(argv[4])
    dep_locate(argv[1], argv[2], argv[3], argv[4])
