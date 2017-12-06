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

'''
  This function will 
'''
def dep_locfiles(instr, utDate, endHour, stageDir, logFile):
    pass

'''
  This function will look for non-raw images, duplicate KOAIDs, 
  or bad dates for each fits file. 
  
  Written by Jeff Mader

  Ported to Python3 by Matthew Brown
'''
def dep_rawfiles(instr, utDate, endHour,fileList, stageDir, ancDir, logFile):
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
    bad = [0]*lsize

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

        # Construct the filename from the header
        # STOPPING HERE WORK ON ERROR STAT
        if instr == 'MOSFIRE':
            outfile = header0['DATAFILE']
        else:
            try:
                outfile = header0['OUTFILE']
            except KeyError:
                try:
                    outfile = header0['ROOTNAME']
                except KeyError:
                    move_bad_file(instr, fitsFile[i], ancDir, 'outfile')
                    continue

        # Get the frame number of the file
        if outfile[:2] == 'kf':
            frameno = header0['IMGNUM']
        elif instr == 'MOSFIRE':
            frameno = header0['FRAMENUM']
        else:
            try:
                frameno = header0['FRAMENO']
            except KeyError:
                try:
                    frameno = header0['FILENUM']
                except KeyError:
                    move_bad_file(instr, fitsFile[i], ancDir, 'frameno')
                    continue
        if float(frameno) < 10:
            zero = '000'
        if float(frameno) >= 10 and (double)frameno < 100:
            zero = '00'
        if float(frameno) >= 100 and (double)frameno < 1000:
            zero = '0'
        filename = outfile.strip() + zero + frameno.strip() + '.fits'

        # Get KOAID
        if not koaid(header0, utDate):
            move_bad_file(instr, fitsFile[i], ancDir, 'KOAID')
            continue
        try:
            koa[i] = header0['KOAID']
        except KeyError:
            koa[i] = ''

        # If filename is rootfile then file is a raw image
        if filename == rootfile[i]:
            raw[i] = 1

    endtime = float(endHour) * 3600.0
    

'''
  This function will
'''
def deimos_find_fcs(logFile, stageDir):
    pass

'''
  This function logs the type of error encountered and moves the bad fits file to anc_dir/udf
'''
def move_bad_file(instr, fitsFile, ancDir, errorCode):
    logging.warning('rawfiles {}: Bad {} found for {}'.format(instr, errorCode, fitsFile))
    logging.warning('rawfiles {}: Copying {} to {}/udf'.format(instr, fitsFile, ancDir))
    udfDir = ancDir + '/udf'
    sp.run(['cp', '-p', fitsFile, udfDir])
