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

''' 
 This function will search the data directories for data
 written in the last howold*24 hours.
 Pre-condition: Requires an instrument, a date to check in UTC time, and a staging directory
 Post-condition: Returns all the fits files within 24 hours of the date given
'''
def dep_locate(instr, utDate, stageDir):
    verify_instrument()
    verify_date(utDate)
    assert stageDir != '', 'stageDir value is blank'

    # Which sdata disk?
    locate.getDirList(instr)

    # Locate FITS files written in the last 24 hours
	
    # Verify FITS files and create stageDir/dep_locateINSTR.txt


#-----------------------END DEP LOCATE----------------------------------

'''
  This function will 
'''
def dep_locfiles(instr, utDate, endHour, stageDir, logFile):
    pass

#-------------------------END DEP LOCFILES------------------------------

def dep_rawfiles(instr, utDate, endHour,fileList, stageDir, ancDir, logFile):

    '''
    This function will look for non-raw images, duplicate KOAIDs, 
    or bad dates for each fits file. 
      
    Written by Jeff Mader
    
    Ported to Python3 by Matthew Brown
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
        logging.warning('rawfiles {}: KOAID not correct date for {}'.format(instr, fitsFile))
    else:
        logging.warning('rawfiles {}: {} found for {}'.format(instr, errorCode, fitsFile))
    logging.warning('rawfiles {}: Copying {} to {}/udf'.format(instr, fitsFile, ancDir))
    udfDir = ancDir + '/udf'
    if not sub.run(['cp', '-p', fitsFile, udfDir]):
        logging.warning('File was not copied')
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
