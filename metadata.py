"""
  This script creates the archiving metadata file as part of the DQA process.

  Original scripts written in IDL by Jeff Mader
  Ported to python by Josh Riley

#TODO: add more code documentation
#TODO: add more asserts/logging

"""



#imports
import sys
import os
from astropy.io import fits
import pandas
from common import make_dir_md5_table
import datetime

def make_metadata(instr, utDate, lev0Dir, tablesDir, log=None):
    """
    Creates the archiving metadata file as part of the DQA process.

    @param instr: instrument name
    @type instr: string
    @param lev0Dir: directory for finding FITS files and writing output files
    @type lev0Dir: string
    @param utDate: UT date (yyyy-mm-dd)
    @type utDate: string
    @param tablesDir: directory containing metadata keyword definition files
    @type tablesDir: string
    """


    if log: log.info('make_metadata.py started for {} {} UT'.format(instr.upper(), utDate))


    #open keywords format file and read data
    #NOTE: changed this file to tab-delimited
    keywordsDefFile = tablesDir + '/keywords.format.' + instr
    if log: log.info('metadata.py reading keywords definition file: {}'.format(keywordsDefFile))
    keyDefs = pandas.read_csv(keywordsDefFile, sep='\t')


    #create metadata table output file
    ymd = utDate.replace('-', '')
    metaFile =  lev0Dir + '/' + ymd + '.metadata.table'
    if log: log.info('metadata.py writing to metadata table file: {}'.format(metaFile))


    #add header to output file
    #NOTE: alignment assumes the col width is at least as big is the keyword name
    with open(metaFile, 'w+') as out:

        for index, row in keyDefs.iterrows():
            out.write('|' + row['keyword'].ljust(row['colSize']))
        out.write("|\n")

        for index, row in keyDefs.iterrows():
            out.write('|' + row['dataType'].ljust(row['colSize']))
        out.write("|\n")

        #todo: add units?
        for index, row in keyDefs.iterrows():
            out.write('|' + ''.ljust(row['colSize']))
        out.write("|\n")

        for index, row in keyDefs.iterrows():
            nullStr = '' if (row['allowNull'] == "N") else "null"
            out.write('|' + nullStr.ljust(row['colSize']))
        out.write("|\n")


    #walk lev0Dir to find all final fits files
    for root, directories, files in os.walk(lev0Dir):
        for filename in files:
            if filename.endswith('.fits'):
                fitsFile = os.path.join(root, filename)
                add_fits_metadata_line(fitsFile, metaFile, keyDefs, log)


    #create md5 sum
    md5Outfile = metaFile.replace('.table', '.md5sum')
    if log: log.info('metadata.py creating {}'.format(md5Outfile))
    make_dir_md5_table(lev0Dir, ".metadata.table", md5Outfile)



def add_fits_metadata_line(fitsFile, metaFile, keyDefs, log):
    """
    Adds a line to metadata file for one FITS file.
    """

    #get header object using astropy
    header = fits.getheader(fitsFile)


    #write all keywords vals for image to a line
    with open(metaFile, 'a') as out:

        for index, row in keyDefs.iterrows():

            keyword   = row['keyword']
            dataType  = row['dataType']
            colSize   = row['colSize']
            allowNull = row['allowNull']


            #get value from header, set to null if not found
            if not (keyword in header): val = 'null'
            else:                       val = header[keyword]


            #check keyword val and format
            val = check_keyword_val(keyword, val, row, log)


            #write out val padded to size
            out.write(' ')
            out.write(str(val).ljust(colSize))

        out.write("\n")
 


def check_keyword_val(keyword, val, fmt, log=None):

    #todo: assert/fail on any of these?


    #check null
    if (val == 'null'):
        if (fmt['allowNull'] == 'N'):
            if log: log.error('metadata check: incorrect "null" value found for non-null keyword {}'.format(keyword))
        return val


    #check value type
    vtype = type(val).__name__
    if (fmt['dataType'] == 'char'):
        if (vtype == 'bool'):
            if   (val == True):  val = 'T'
            elif (val == False): val = 'F'
        elif (vtype != "str"):
            if log: log.warning('metadata check: var type {}, expected {} ({}={}).'.format(vtype, fmt['dataType'], keyword, val))

    elif (fmt['dataType'] == 'integer'):
        if (vtype != "int"):
            if log: log.warning('metadata check: var type of {}, expected {} ({}={}).'.format(vtype, fmt['dataType'], keyword, val))

    elif (fmt['dataType'] == 'double'):
        if (vtype != "float"):
            if log: log.warning('metadata check: var type of {}, expected {} ({}={}).'.format(vtype, fmt['dataType'], keyword, val))

    elif (fmt['dataType'] == 'date'):
        try:
            datetime.datetime.strptime(val, '%Y-%m-%d')
        except ValueError:
            if log: log.warning('metadata check: expected date format YYYY-mm-dd ({}={}).'.format(keyword, val))

    elif (fmt['dataType'] == 'datetime'):
        try:
            datetime.datetime.strptime(val, '%Y-%m-%d %H:%i:%s')
        except ValueError:
            if log: log.warning('metadata check: expected date format YYYY-mm-dd HH:ii:ss ({}={}).'.format(keyword, val))
     

    #check char length
    #TODO: round instead of truncate for type double?
    length = len(str(val))
    if (length > fmt['colSize']):
            if log: log.warning('metadata check: char length of {} greater than column size of {} ({}={}).  TRUNCATING.'.format(length, fmt['colSize'], keyword, val))
            val = str(val)[:fmt['colSize']]


    #todo: check value range, discrete values?


    return val