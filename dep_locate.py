"""
  This script consolidates all the pieces of the KOA archival dep-locate
  function into one place. It mainly consists of dep_locate.csh,
  dep_locfiles.c, dep_rawfiles.csh, and deimos_find_fcs.csh.
  Finds all valid FITS files for a given instrument within 24 hours of 
  the supplied date.  Upon completion, it should have created a file 
  with the list of valid FITS files found, copied those FITS files to staging, 
  and put any bad files in the /anc/udf/ folder.

  Usage dep_locate(instrObj)

  Original scripts written by Jeff Mader and Jennifer Holt
  Ported to Python3 by Matthew Brown, Josh Riley
"""

import calendar as cal               ## Used to convert a time object into a number of seconds
import time as t                     ## Used to convert a string date into a time object
from astropy.io import fits          ## Used for everything with fits
from common import koaid             ## Used to determine the KOAID of a file for transport
import os
import shutil
from sys import argv
from datetime import datetime, timedelta
import configparser


def dep_locate(instrObj):
    """
    This function will search the data directories for FITS data written in the last 24hours.
    Copies FITS file to staging area. Creates the following files in stageDir:

      dep_locate<INSTR>.txt

    @param instrObj: the instrument object
    @type instrObj: instrument class
    """


    #shorthand
    instr  = instrObj.instr
    utDate = instrObj.utDate
    log    = instrObj.log
    ancDir   = instrObj.dirs['anc']
    stageDir = instrObj.dirs['stage']


    ##config for CIT
    config = configparser.ConfigParser()
    config.read('config.live.ini')


    #Find sdata dirs list. Return if none found.
    if ('LOCATE_DIR' in config['CIT']): useDirs = [config['CIT']['LOCATE_DIR']]
    else                              : useDirs = instrObj.get_dir_list()
    if len(useDirs) == 0:
        log.warning('Did not find any sdata directories')
        return


    # Create files to store the valid FITS files
    presort1File = ''.join((stageDir, '/dep_locate', instr, 'pre1.text'))
    presort2File = ''.join((stageDir, '/dep_locate', instr, 'pre2.text'))
    locateFile  = ''.join((stageDir, '/dep_locate', instr, '.txt'))


    # Find the files in the last 24 hours
    log.info('Looking for FITS files in {}'.format(useDirs))
    modtimeOverride = 0
    if ('LOCATE_MODTIME_OVERRIDE' in config['CIT']): modtimeOverride = int(config['CIT']['LOCATE_MODTIME_OVERRIDE'])
    filePaths = find_24hr_fits(useDirs, instrObj.utDate, instrObj.endTime, modtimeOverride)


    #write filepaths to outfile
    with open(presort1File, 'w') as f:
        for path in filePaths:
            f.write(path + '\n')
    log.info('Copied fits file names from {} to {}'.format(useDirs, presort1File))


    # Read presortFile list and do some more filtering before we do final copy to staging.
    with open(presort2File, 'w') as f:
        with open(presort1File, 'r') as pre:
            fcsConfigs = []
            for line in pre:
                if ('.fits' in line 
                        and '/fcs' not in line 
                        and 'mira' not in line 
                        and 'savier-protected' not in line 
                        and 'idf' not in line):

                    # Copy the files to stageDir and update files 
                    # to use local copy file list
                    newFile = ''.join((stageDir, line.strip()))
                    log.info('copying file {} to {}'.format(line.strip(), newFile))                    
                    copy_file(line.strip(), newFile)
                    toFile = ''.join((newFile, '\n'))
                    f.write(toFile)

                    #special DEIMOS step
                    #todo: move this to instr class?
                    if 'DEIMOS' in instr:
                        try:
                            fcs = fits.getheader(line.strip())['FCSIMGFI']
                            if fcs != '' and fcs not in fcsConfigs:
                                fcsConfigs.append(fcs)
                                if '/s/' not in fcs:
                                    fcs = '/s' + fcs
                                newFile = ''.join((stageDir, fcs))
                                copy_file(fcs, newFile)
                                toFile = ''.join((newFile, '\n'))
                                f.write(toFile)
                        except:
                            pass
            del fcsConfigs


    # Verify the files are valid - no corrupt headers, valid KOAID
    locateFile = stageDir +'/dep_locate' + instr + '.txt'
    dep_rawfiles(instr, utDate, instrObj.endTime, presort2File, locateFile, stageDir, ancDir, log)


    #log completion with count
    num = sum(1 for line in open(locateFile, 'r'))
    log.info('dep_locate: {} {} FITS files passed final checks.'.format(num, instr))

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


def dep_rawfiles(instr, utDate, endTime, inFile, outFile, stageDir, ancDir, log):
    """
    This function will look for non-raw images, duplicate KOAIDs,
    or bad dates for each fits file.

    Written by Jeff Mader

    Ported to Python3 by Matthew Brown

    @type instr: string
    @param instr: The instrument used to make the fits files being looked at
    @type utDate: datetime
    @param utDate: The date in UT of the night that the fits tiles were taken
    @type endTime: datetime
    @param endTime: The hour that the observations ended
    @type inFile: string
    @param inFile: Filepath of text file with list of all FITS files within 24 hours of the given date
    @type outFile: string
    @param outFile: Filepath for final output file for all valid FITS passing checks.
    @type stageDir: string
    @param stageDir: The staging area to store the files for transport to KOA
    @type ancDir: string
    @param ancDir: The anc directory to store the bad and corrupted fits files
    @type log: Logger Object
    @param log: The log handler for the script. Writes to the logfile
    """
    log.info('dep_locate: starting rawfiles check: {0} {1} {2} {3} {4}'.format(instr, utDate, endTime, stageDir, ancDir))

    # Change yyyy/mm/dd to yyyymmdd
    if   '/' in utDate: year, month, day = utDate.split('/')
    elif '-' in utDate: year, month, day = utDate.split('-')
    date = year + month + day

    # read input file list into an array
    fitsList = []

    # Loop through the file list and read in
    # the fits files found from within 24 hours
    # of the given date
    with open(inFile, 'r') as ffiles:
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

        # check for empty file
        if (os.path.getsize(fitsList[i]) == 0):
            move_bad_file(instr, fitsList[i], ancDir, 'Empty File', log_writer)
            continue

        # Get the header of the current fits file
        try:
            if instr == 'NIRC2':
                header0 = fits.getheader(fitsList[i], ignore_missing_end=True)
                header0['INSTRUME'] = 'NIRC2'
            else:
                header0 = fits.getheader(fitsList[i])
        except:
            move_bad_file(instr, fitsList[i], ancDir, 'Unreadable Header', log_writer)
            continue

        # Break the file path into a list
        root = fitsList[i].split('/')

        # Grab the last element in the filepath list
        # This should be the filename *.fits
        rootfile[i] = root[-1]

        # Construct the original file name
        filename, successful = construct_filename(instr,fitsList[i], ancDir, header0, log)
        if not successful:
            copy_bad_file(instr, fitsList[i], ancDir, 'Bad Header', log)
            raw[i] = 2
            continue

        # Get KOAID
        if not koaid(header0, utDate):
            copy_bad_file(instr, fitsList[i], ancDir, 'Bad KOAID', log)
            raw[i] = 2
            continue
        try:
            koa[i] = header0['KOAID']
        except KeyError:
            koa[i] = ''

        # If filename is rootfile then file is a raw image
        if filename == rootfile[i]:
            raw[i] = 1

    #get endtime in seconds
    #endTimeSec = float(endTime) * 3600.0
    hours, minutes, seconds = endTime.split(":") 
    endTimeSec = float(hours) * 3600.0 + float(minutes)*60.0 + float(seconds)


    #check for duplicate KOA ID
    for i in range(len(fitsList)-1):
        if   raw[i] == 2: continue
        elif raw[i] == 0:
            for j in range(i+1,len(fitsList)):
                if koa[j]==koa[i]: # j will always be greater than i
                    copy_bad_file(instr, fitsList[i], ancDir, 'Duplicate KOAID', log)
                    raw[i] = 2
                    break

    # Check for bad date
    for i in range(len(fitsList)):
        if raw[i] == 2: continue
        prefix, fdate, ftime, postfix = koa[i].split('.')
        if fdate != date and float(ftime) < endTimeSec:
            copy_bad_file(instr, fitsList[i], ancDir, 'KOADATE', log)
            raw[i] = 2


    # Create final dqa_<instr>.txt file with only the good lines from dep_locateINSTR.txt
    with open(inFile, 'r') as fhIn:
      lines = fhIn.readlines()
    with open(outFile, 'w') as fhOut:
        for line in lines:
            if line.strip() in fitsList:
                num = fitsList.index(line.strip())
                if raw[num] == 1:
                    fhOut.write(line)


#------------------END RAWFILES-----------------------------


def copy_bad_file(instr, fitsFile, ancDir, errorCode, log):
    """
    This function logs the type of error encountered
    and copies the bad fits file to anc_dir/udf

    @type instr: string
    @param instr: The keyword for the instrument being searched
    @type fitsFile: string
    @param fitsFile: The filename of the fits file being observed
    @type ancDir: string
    @param ancDir: The path to the anc directory
    @type errorCode: string
    @param errorCode: How the fits file failed. Used in the logging
    @type log: Logger Object
    @param log: The log handler for the script. Writes to the logfile
    """
    if errorCode == 'KOADATE':
        log.warning('rawfiles {}: KOAID not correct date for {}'.format(instr, fitsFile))
    else:
        log.warning('rawfiles {}: {} found for {}'.format(instr, errorCode, fitsFile))
    log.info('rawfiles {}: Copying {} to {}/udf'.format(instr, fitsFile, ancDir))
    udfDir = ancDir + '/udf/'
    try:
        # Use copy2 from shutil to copy the file with its metadata
        shutil.copy2(fitsFile, udfDir)
    except:
        log.error('{}: {} file was not copied!'.format(instr, fitsFile))

#-------------End copy-bad-file()---------------------------


def construct_filename(instr, fitsFile, ancDir, keywords, log):
   """
    Constructs the original filename from the fits header keywords

    @type instr: string
    @param instr: The keyword for the instrument
    @type fitsFile: string
    @param fitsFile: The current fits file being observed
    @type ancDir: str
    @param ancDir: The anc directory to copy bad files
    @type keywords: dictionary
    @param keywords: The pairing of all the fits keywords with their values
    @type log: Logger Object
    @param log: The log handler for the script. Writes to the logfile
   """

   #TODO: move this to instrument classes

   if instr == 'OSIRIS': # Osiris already has the raw filename under DATAFILE
       filename = keywords['DATAFILE']
       # but the i file needs .fits added to it
       if filename[0] == 'i':
           filename = ''.join((filename, '.fits'))
       return filename, True
   elif instr in ['MOSFIRE', 'NIRES']:
       try:
           outfile = keywords['DATAFILE']
           if '.fits' not in outfile:
               outfile = ''.join((outfile, '.fits'))
           return outfile, True
       except KeyError:
           copy_bad_file(
                   instr, fitsFile, ancDir, 'Bad Outfile', log)
           return '', False
   elif instr == 'KCWI':
       try:
           outfile = keywords['OFNAME']
           return outfile, True
       except KeyError:
           copy_bad_file(
                   instr, fitsFile, ancDir, 'Bad Outfile', log)
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
                   copy_bad_file(
                           instr, fitsFile, ancDir, 'Bad Outfile', log)
                   return '', False

   # Get the frame number of the file
   if outfile[:2] == 'kf':
       frameno = keywords['IMGNUM']
   elif instr == 'MOSFIRE':
       frameno = keywords['FRAMENUM']
   # NIRES currently does not have a FRAMENO keyword, use datafile
   elif instr == 'NIRES':
       garbage, frameno = keywords['DATAFILE'].split('_')
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
                   copy_bad_file(
                           instr, fitsFile, ancDir, 'Bad Frameno', log)
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
   filename = ''.join((outfile.strip(), zero, str(frameno).strip(), '.fits'))
   return filename, True

#---------------------End construct_filename-------------------------


def find_24hr_fits(useDirs, utDate, endTime, modtimeOverride=0):
    """
    Uses the os.walk function to recurse through a given directory
    and return all the leaf files which are checked to be
    fits files.

    @type useDirs: string
    @param useDirs: The directory that we want to search in
    @type utDate: datetime
    @param utDate: The date of observation of the files we want to search for
    @type outfile: string
    @param outfile: Where we want to store the output
    @type log: Logger Object
    @param log: The log handler for the script. Writes to the logfile
    """

    # Break utDate into its pieces
    utDate = utDate.replace('/', '-')

    # Set up our +/-24 hour boundary
    utDate2 = datetime.strptime(utDate, '%Y-%m-%d')
    utDate2 -= timedelta(days=1)
    utDate2 = utDate2.strftime('%Y-%m-%d')

    # Create a string date and time to convert to seconds since epoch
    year, month, day = utDate.split('-')
    utMaxTime = ''.join((str(year), str(month), str(day).zfill(2), ' ', str(endTime)))
    year, month, day = utDate2.split('-')
    utMinTime = ''.join((str(year), str(month), str(day).zfill(2), ' ', str(endTime)))

    # st_mtime records the time in seconds of the last file modification since 
    # Jan 1 1970 00:00:00 UTC We need to create a time_construct object 
    # (using time.strptime()) to convert to seconds (using calendar.timegm())
    # All valid files should fall within these boundaries
    maxTimeSinceMod = cal.timegm(t.strptime(utMaxTime, '%Y%m%d %H:%M:%S'))
    minTimeSinceMod = cal.timegm(t.strptime(utMinTime, '%Y%m%d %H:%M:%S'))

    # Iterate through the list of directories from the locate script to look for fits files
    filePaths = []
    for fitsDir in useDirs:
        for root, dirs, files in os.walk(fitsDir):
            for item in sorted(files):

                if not '.fits' in item: continue

                # Create the path to the current file we want to check
                fullPath = ''.join((root, '/', item))

                # Check to see if the file is a fits file created/modified in the last day. 
                # st_mtime needs to be greater than the minTimeSinceMod to be within the past 24 hours
                modTime = os.stat(fullPath).st_mtime
                if ( (modTime <= maxTimeSinceMod and modTime > minTimeSinceMod)
                     or modtimeOverride == 1):
                    filePaths.append(fullPath)

    return filePaths


#-----------------------End find_24hr_fits-----------------------------------

