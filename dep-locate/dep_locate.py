'''
  This script consolidates all the pieces of the KOA archival dep-locate
  function into one place. It mainly consists of dep_locate.csh,
  dep_locfiles.c, dep_rawfiles.csh, and deimos_find_fcs.csh.
  Upon completion, it should return a list of the fits files for a 
  given instrument within 24 hours of the supplied date.

  Usage dep_locate INSTRUMENT howhold

  Original scripts written by Jeff Mader and Jennifer Holt
  Ported to Python3 by Matthew Brown
'''

import logging as lg                         ## Used for all the logging
import listInstrDirs as locate               ## Used to create the directories of the instrument
import calendar as cal                       ## Used to convert a time object into a number of seconds
import time as t                             ## Used to convert a string date into a time object
from astropy.io import fits                  ## Used for everything with fits
from common import koaid                     ## Used to determine the KOAID of a file for transport
import os
import verification
import shutil

def dep_locate(instr, utDate, rootDir, endHour):
    ''' 
    This function will search the data directories for data  written in the last howold*24 hours.
    Pre-condition: Requires an instrument, a date to check in UTC time, and a staging directory
    Post-condition: Returns all the fits files within 24 hours of the date given
    
    @type instr: string
    @param instr: The instrument used to make the fits files being looked at
    @type utDate: datetime
    @param utDate: The date in UT of the night that the fits tiles were taken
    @type stageDir: string
    @param stageDir: The staging area to store the files for transport to KOA
    '''

    # Create stage and anc directory strings
    dateDir = utDate.replace('-', '')
    dateDir = dateDir.replace('/', '')
    stageDir = rootDir + '/stage/' + dateDir
    ancDir = rootDir + '/' + dateDir + '/anc'

    ### Set up logging ###
    user = os.getlogin()
    log_writer = lg.getLogger('dep_locate <' + user +'>')
    log_writer.setLevel(lg.INFO)
    
    # create a file handler
    log_handler = lg.FileHandler('debug.log')
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
        os.makedirs(ancDir + '/udf')
    except FileExistsError:
        log_writer.warning('udf directory already exists!')
    except:
        log_writer.error('Unable to create udf directory!')
        return

    # Create the stage directory
    try:
        os.makedirs(stageDir)
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
    presort = stageDir + '/dep_locate' + instr + 'pre.txt'
    files = stageDir + "/dep_locate" + instr + ".txt"

    # Find the files in the last 24 hours
    pyfind(usedir, utDate, presort, log_writer)

    # We only wants the .fits files
    with open(files, 'w') as f:
        with open(presort, 'r') as pre:
            for line in pre:
                if '.fits' in line and '/fcs' not in line and 'mira' not in line and 'savier-protected' not in line:
                    # Copy the files to stageDir and update files to use local copy file list
                    rDir = os.path.dirname(line)
                    if not os.path.exists(rDir):
                        os.makedirs(rDir)
                    newFile = stageDir + line.strip()
                    if not os.path.exists(newFile):
                        shutil.copy2(line.strip(), newFile)
                    f.write(newFile+'\n')

    # Remove temporary file
    os.remove(presort)
    log_writer.info('{}: removed temporary presorted file {}'.format(instr, presort))
    
    # Verify the files are valid - no corrupt headers, valid KOAID
    dep_rawfiles(instr, utDate, endHour, files, stageDir, ancDir, log_writer)
    log_writer.info('{0}: finished rawfiles {0} {1} {2} {3} {4}'.format(instr, utDate, endHour, stageDir, ancDir))

    log_writer.info('{}: Using files found in {}'.format(instr, usedir))
    log_writer.info('{}: dep_locate successful'.format(instr))

#-----------------------END DEP LOCATE----------------------------------

def dep_rawfiles(instr, utDate, endHour,fileList, stageDir, ancDir, log_writer):

    '''
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
    @param fileList: Text file that contains the fits filenames that occured within 24 hours of the given date
    @type stageDir: string
    @param stageDir: The staging area to store the files for transport to KOA
    @type ancDir: string
    @param ancDir: The anc directory to store the bad and corrupted fits files
    @type log_writer: Logger Object
    @param log_writer: The log handler for the script. Writes to the logfile
    '''
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
        rootfile.append(root[-1])  

        # Construct the original file name
        filename, successful = construct_filename(instr,fitsList[i], ancDir, header0, log_writer)
        if not successful:
            move_bad_file(instr, fitsList[i], ancDir, 'Bad KOAID', log_writer)
            raw[i] = 2
            continue

        # Get KOAID
        if not koaid(header0, utDate):
            print('yes')
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
                    move_bad_file(instr, fitsList[i], ancDir, 'Duplicate KOAID', log_writer)
                    break

        # Check the date
        prefix, fdate, ftime, postfix = koa[i].split('.')
        if fdate != date and float(ftime) < endtime:
            move_bad_file(instr, fitsList[i], ancDir, 'KOADATE', log_writer)
            break
#        print(fitsList[i])

# Need to remove "bad" files from dep_locateINSTR.txt in stageDir

    
#------------------END RAWFILES-----------------------------

def move_bad_file(instr, fitsFile, ancDir, errorCode, log_writer):
    """ 
    Log the error where the fits file failed and copy the fits file to the anc directory

    This function logs the type of error encountered and moves the bad fits file to anc_dir/udf
    
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
        log_writer.warning('rawfiles {}: KOAID not correct date for {}'.format(instr, fitsFile))
    else:
        log_writer.warning('rawfiles {}: {} found for {}'.format(instr, errorCode, fitsFile))
    log_writer.info('rawfiles {}: Copying {} to {}/udf'.format(instr, fitsFile, ancDir))
    udfDir = ancDir + '/udf/'
    try:
        # Use copy2 from shutil to copy the file with its metadata
        shutil.copy2(fitsFile, udfDir)
    except:
        log_writer.error('{}: {} file was not copied!!'.format(instr, fitsFile))

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
           filename = filename + '.fits'
       return filename, True
   elif instr == 'MOSFIRE':
       outfile = keywords['DATAFILE']
   else:
       try:
           outfile = keywords['OUTFILE']
       except KeyError:
           try:
               outfile = keywords['ROOTNAME']
           except KeyError:
               move_bad_file(instr, fitsFile, ancDir, 'Bad Outfile', log_writer)
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
                   move_bad_file(instr, fitsFile, ancDir, 'Bad Frameno', log_writer)
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
   filename = outfile.strip() + zero + str(frameno).strip() + '.fits'
   return filename, True

#---------------------End construct_filename-------------------------

def pyfind(usedir,utDate, outfile, log_writer):
    """
    Uses the subprocess run function to call the find command which searches the given directories for files ending in .fits

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
    dayMax = int(day) + 1

    # Create a string date and time to convert to seconds since epoch
    utMaxTime = str(year)+str(month)+str(dayMax) + ' 20:00:00' # default 20:00:00, change if necessary
    utMinTime = str(year)+str(month)+str(dayMin) + ' 20:00:00' # default 20:00:00, change if necessary
    
    # st_mtime records the time in seconds of the last file modification since Jan 1 1970 00:00:00 UTC
    # We need to create a time_construct object (using time.strptime())
    # to convert to seconds (using calendar.timegm())
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
                    full_path = root + '/' + item
                    # Check to see if the file is a fits file created/modified in the last day
                    # st_mtime needs to be greater than the minTimeSinceMod to be within the past 24 hours
                    modTime = os.stat(full_path).st_mtime
                    if '.fits' in item[-5:] and modTime < maxTimeSinceMod and modTime > minTimeSinceMod:
                        ofile.write(full_path+'\n')

    # Append the action to the log
    log_writer.info('Copied fits file names from {} to {}'.format(usedir, outfile))


#-----------------------End PyFind-----------------------------------


