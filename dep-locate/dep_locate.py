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
    locate.getInstrDirs(instr)

    # Locate FITS files written in the last 24 hours
	
    # Verify FITS files and create stageDir/dep_locateINSTR.txt

'''
  This function will 
'''
def dep_locfiles(instr, utDate, endHour, stageDir, logFile):
    continue

'''
  This function will look for non-raw images, duplicate KOAIDs, 
  or bad dates for each fits file. 
'''
def dep_rawfiles(instr, utDate, endHour,dataFile, stageDir, ancDir, logFile):
    # Change yyyy/mm/dd to yyyymmdd
    date = utDate.replace('/','')

    # read input file data into an array
    inputList = []

    # Loop through the data file and read in
    for line in dataFile:
        inputList.append(line)

    raw = []
    koa = []
    rootfile = []
    bad = []
    for i in range(len(data)):
        raw.append(0)
        header0 = fits.getheader(dataFile)
        root.append(inputList[i].split('/'))
        rootfile.append(root[len(root)-1])

    # Get filename from header
    #outfile = fits.(header0, 'OUTFILE')

'''
  This function will
'''
def deimos_find_fcs(logFile, stageDir):
    continue
