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
    switch(instr):
        case 'DEIMOS':
            subdir = '/s/sdata10*/d*mos*'
            break
        case 'ESI':
            subdir = '/s/sdata7*/esi*'
            break
        case 'HIRES':
            subdir = '/s/sdata12*/hires*'
            break
        case 'LRIS':
            subdir = '/s/sdata2*/lris*'
            break
        case 'MOSFIRE':
            subdir = '/s/sdata130*/m*'
            break
        case 'NIRC2':
            subdir = '/s/sdata9*/nirc*'
            break
        case 'NIRSPEC':
            subdir = '/s/sdata6*/n*'
            break
        case 'OSIRIS':
            subdir = '/s/sdata110*/os*'
            break
        case 'KCWI':
            subdir = '/s/sdata1400/kcwi*'
            break
        default:
            logging.basicConfig(filename='debug.log', level=logging.DEBUG)
            logging.warning('dep_locate %s: Could not find instrument %s', instr, instr)
            print('dep_locate %s: Could not find instrument %s', instr, instr)
            break

        

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
    data = []

    for line in dataFile:
        data.append(line)

    raw = []
    koa = []
    rootfile = []
    bad = []
    for i in range(len(data)):
        raw.append(0)
        header0 = fits.getheader(dataFile)
        root.append(data[i].split('/'))
        rootfile.append(root[len(root)-1])

    # Get filename from header
    #outfile = fits.(header0, 'OUTFILE')

'''
  This function will
'''
def deimos_find_fcs(logFile, stageDir):
    continue
