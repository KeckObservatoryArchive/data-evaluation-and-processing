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
    date = utDate.replace('/','')

    # read input file list into an array
    fitsList = []

    # Loop through the file list and read in
    # the fits files found from within 24 hours
    # of the given date
    for line in fileList:
        fitsList.append(line)

    # get the size of the inputList 
    isize = len(fitsList)

    # Initialize lists with the number of fits files found
    raw = [0]*isize
    koa = ['0']*isize
    rootfile = ['0']*isize
    bad = [0]*isize

    # Each line in the file list is a fits file
    # We want to check the validity of each file
    for i in range(len(fitsList)):
        raw[i] = 0
        header0 = fits.getheader(fitsList[i])
        root = fitsList[i].split('/')
        rootfile.append(root[len(root)-1])

        # Get filename from header
        # STOPPING HERE WORK ON ERROR STATE
        outfile = header0['OUTFILE']
        if outfile == "":
            outfile = header0['ROOTNAME']
            if instr == 'MOSFIRE':
                frameno = header0['DATAFILE']
            if ERROR:
                bad[i]=1
                break
        frameno = header0['FRAMENO']
        if outfile[:2] == 'kf':
            frameno = header0['IMGNUM']
        if instr == 'MOSFIRE':
            frameno = header0['FRAMENUM']
        if ERROR:
            frameno = header0['FILENUM']
            if ERROR:
                bad[i] = 1
                break
        if float(frameno) < 10:
            zero = '000'
        if float(frameno) >= 10 and (double)frameno < 100:
            zero = '00'
        if float(frameno) >= 100 and (double)frameno < 1000:
            zero = '0'
        filename = outfile.strip() + zero + frameno.strip() + '.fits'

        # Get KOAID
        if not koaid.koaid(header0, utDate):
            logging.warning('rawfiles %s: Bad KOAID', instr)
            logging.warning('rawfiles %s: Copying ' + fitsList[i] + ' to ' + ancDir + '/udf', instr)

    endtime = float(endHour) * 3600.0

'''
  This function will
'''
def deimos_find_fcs(logFile, stageDir):
    pass

