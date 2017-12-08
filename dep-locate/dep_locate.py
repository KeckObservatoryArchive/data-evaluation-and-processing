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

import logging
import subprocess as sub
import listInstrDirs as locate
from astropy.io import fits
from common import koaid

def dep_locate(instr, utDate, stageDir):
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
    verify_instrument()
    verify_date(utDate)
    assert stageDir != '', 'stageDir value is blank'

# Init of dep_locate. will come back to this later
'''
    if not sub.run(['mkdir','-p', ancDir+'/udf']):
        logging.warning("Unable to create udf directory!")
'''

    # Which sdata disk?
    subdir = locate.getDirList(instr)
    # locate did not return any dirs, so we exit
    if len(subdir) == 0:
        return

    # Locate FITS files written in the last 24 hours
    usedir = subdir
    # for loop was to detect alt_dir for files. remove
    for i in range(1,2):
        if i==1:
            log_file = stageDir + "/dep_locate1" + instr + ".txt"
        elif i==2:
            log_file = stageDir + "/dep_locate2" + instr + ".txt"
        file1 = stageDir + "/dep_locate" + instr + "1.txt"
        file2 = stageDir + "/dep_locate" + instr + "2.txt"
        file3 = stageDir + "/dep_locate" + instr + "3.txt"

        # Day 1, if not last night
        howold -= 1
        if howold >= 0:
            pyfind(usedir, howold, file1)

            # Write it to the log
            logger.info('dep_locate {}: /usr/bin/find {} -mtime {} -fprintf {}'.format(instr, usedir, howold, file1))
        else:
            sub.run(['touch', file1])

        # Day 2
        howold += 1
        pyfind(usedir, howold, file2)

        # Day 3
        howold += 1
        pyfind(usedir, howold, file3)
        howold -= 1

        # We only wants the .fits files
        logger.info('dep_locate {}: cat {} {} {} > {}'.format(instr, file1, file2, file3, log_file))
        sub.run(['grep', '-h', '.fits', file1, file2, file3, '|', 'grep', '-v', 'mira', '|', 'grep', '-v', 'savier-protected', '>>', log_file])
        sub.run(['grep', '-h', '.fits', file1, file2, file3, '|', 'grep', '-v', 'mira', '|', 'grep', '-v', 'savier-protected'])
        sub.run(['rm', '-r', file1, file2, file3])

        # Look for files within the requested 24 hour period
        logger.info('dep_locate {}: dep_locfiles {} dep_locfiles {} {} {} {} {}'.format(instr, instr, utDate, endHour, stageDir, log_file))
        dep_locfiles(instr, utDate, endHour, stageDir, log_file)
        logger.info('dep_locate {}: finished dep_locfiles {} {} {} {} {}'.format(instr, instr, utDate, endHour, stageDir, log_file))

        dep_rawfiles(instr, utDate, endHour, logFile, stageDir, ancDir)
        logger.info('dep_locate {}: finished rawfiles {} {} {} {} {}'.format(instr, instr, utDate, endHour, stageDir, ancDir))

        # 

#-----------------------END DEP LOCATE----------------------------------

def dep_locfiles(instr, utDate, endHour, stageDir, logFile):
    '''
    This function will locate all the files within 24 hours of the given utDate

    @type instr: string
    @param instr: The instrument used to make the fits files being looked at
    @type utDate: datetime
    @param utDate: The date in UT of the night that the fits tiles were taken
    @type endHour: datetime
    @param endHour: The hour that the observations ended
    @type stageDir: string
    @param stageDir: The staging area to store the files for transport to KOA
    @type logFile: string
    @param logFile: The file to send all the warnings and debug statements
    '''
    pass

#-------------------------END DEP LOCFILES------------------------------

def dep_rawfiles(instr, utDate, endHour,fileList, stageDir, ancDir, logFile):

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
    @type logFile: string
    @param logFile: The file to send all the warnings and debug statements
    '''
    # Change yyyy/mm/dd to yyyymmdd
    year, month, day = utDate.split('/')
    date = year + month + day

    # date = utDate.replace('/','') # This will also work

    # read input file list into an array
    fitsList = []

    # Loop through the file list and read in
    # the fits files found from within 24 hours
    # of the given date
    files = open(fileList, 'r')
    for line in files:
        fitsList.append(line)

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
        filename, successful = construct_filename(instr,fitsFile[i], ancDir, header0)
        if not successful:
            raw[i] = 2
            continue

        # Get KOAID
        if not koaid(header0, utDate):
            move_bad_file(instr, fitsFile[i], ancDir, 'Bad KOAID')
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

    for i in range(len(fitsList)):
        # Is this a duplicate KOAID?
        if raw[i] == 2:
            continue
        elif raw[i] == 0:
            for j in range(i+1,len(fitsList)):
                if koa[j]==koa[i]: # j will always be greater than i
                    move_bad_file(instr, fitsFile[i], ancDir, 'Duplicate KOAID')
                    break

        # Check the date
        prefix, fdate, ftime, postfix = koa[i].split('.')
        if fdate != date and float(ftime) < endtime:
            move_bad_file(instr, fitsFile[i], ancDir, 'KOADATE')
            break
        print(fitsFile[i])

    
#------------------END RAWFILES-----------------------------

def deimos_find_fcs(logFile, stageDir):
    '''
    This function will
    '''
    pass

#------------------END DEIMOS FIND FCS---------------------

def move_bad_file(instr, fitsFile, ancDir, errorCode):
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
    """
    if errorCode == 'KOADATE':
        logger.warning('rawfiles {}: KOAID not correct date for {}'.format(instr, fitsFile))
    else:
        logger.warning('rawfiles {}: {} found for {}'.format(instr, errorCode, fitsFile))
    logger.warning('rawfiles {}: Copying {} to {}/udf'.format(instr, fitsFile, ancDir))
    udfDir = ancDir + '/udf'
    if not sub.run(['cp', '-p', fitsFile, udfDir]):
        logger.warning('File was not copied')
        print('File was not copied')

#-------------End move-bad-file()---------------------------

def construct_filename(instr, fitsFile, ancDir, keywords):
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
    """
   if instr == 'OSIRIS': # Osiris already has the raw filename under DATAFILE
       filename = keywords['DATAFILE']
       # but the i file needs .fits added to it
       if filename[0] == 'i':
           filename = filename + '.fits'
   elif instr == 'MOSFIRE':
       outfile = keywords['DATAFILE']
   else:
       try:
           outfile = keywords['OUTFILE']
       except KeyError:
           try:
               outfile = keywords['ROOTNAME']
           except KeyError:
               move_bad_file(instr, fitsFile, ancDir, 'Bad Outfile')
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
                   move_bad_file(instr, fitsFile, ancDir, 'Bad Frameno')
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
   filename = outfile.strip() + zero + frameno.strip() + '.fits'
   return filename, True

#---------------------End construct_filename-------------------------

def pyfind(usedir, howold, outfile):
    """
    Uses the subprocess run function to call the find command which searches the given directories for files ending in .fits

    @type usedir: string
    @param usedir: The directory that we want to search in
    @type howold: string
    @param howold: How old the file can be
    @type outfile: string
    @param outfile: Where we want to store the output
    """
    # The format which we want to output text into the log as
    oformat = "%p %CT %CZ %CY/%Cm/%Cd\n"

    # Run the command
    sub.run(['find', usedir, '-mtime', howold, '-name', '*.fits', '!', '-name', 'fcs*.fits', '-fprintf', outfile, oformat])
    
    # Append the action to the log
    logger.warning('dep_locate {}: /usr/bin/find {} -mtime {} -fprintf {}'.format(instr, usedir, howold, file1))

#-----------------------End PyFind-----------------------------------


### Set up logging ###
# We need 1 file handler per log and 1 logger per thing we want to track
logger = logging.getLogger(__main__)
logger.setLevel(logging.WARNING)

# create a file handler
debugger = logging.FileHandler('debug.log')
debugger.setLevel(logging.WARNING)

# Create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# add handlers to the logger
logger.addHandler(handler)
