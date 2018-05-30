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

def make_metadata(keywordsDefFile, metaOutFile, lev0Dir, extraData=None, log=None):
    """
    Creates the archiving metadata file as part of the DQA process.

    @param keywordsDefFile: keywords format definition input file path
    @type keywordsDefFile: string
    @param metaOutFile: metadata output file path
    @type metaOutFile: string
    @param lev0Dir: directory for finding FITS files and writing output files
    @type lev0Dir: string
    @param lev0Dir: dictionary of any extra key val pairs not in header
    @type lev0Dir: dictionary
    """


    #open keywords format file and read data
    #NOTE: changed this file to tab-delimited
    if log: log.info('metadata.py reading keywords definition file: {}'.format(keywordsDefFile))
    keyDefs = pandas.read_csv(keywordsDefFile, sep='\t')


    #add header to output file
    #NOTE: alignment assumes the col width is at least as big is the keyword name
    if log: log.info('metadata.py writing to metadata table file: {}'.format(metaOutFile))
    with open(metaOutFile, 'w+') as out:

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
    if log: log.info('metadata.py searching fits files in dir: {}'.format(lev0Dir))
    for root, directories, files in os.walk(lev0Dir):
        for filename in files:
            if filename.endswith('.fits'):
                fitsFile = os.path.join(root, filename)

                extra = {}
                if filename in extraData: extra = extraData[filename]

                add_fits_metadata_line(fitsFile, metaOutFile, keyDefs, extra, log)


    #create md5 sum
    md5Outfile = metaOutFile.replace('.table', '.md5sum')
    if log: log.info('metadata.py creating {}'.format(md5Outfile))
    make_dir_md5_table(lev0Dir, ".metadata.table", md5Outfile)



def add_fits_metadata_line(fitsFile, metaOutFile, keyDefs, extra, log):
    """
    Adds a line to metadata file for one FITS file.
    """

    #get header object using astropy
    header = fits.getheader(fitsFile)


    #write all keywords vals for image to a line
    with open(metaOutFile, 'a') as out:

        for index, row in keyDefs.iterrows():

            keyword   = row['keyword']
            dataType  = row['dataType']
            colSize   = row['colSize']
            allowNull = row['allowNull']


            #get value from header, set to null if not found
            if   (keyword in header) : val = header[keyword]
            elif (keyword in extra)  : val = extra[keyword]
            else                     : val = 'null';


            #check keyword val and format
            val = check_keyword_val(keyword, val, row, log)


            #write out val padded to size
            out.write(' ')
            out.write(str(val).ljust(colSize))

        out.write("\n")
 


def check_keyword_val(keyword, val, fmt, log=None):
    '''
    Checks keyword for correct type and proper value.
    '''

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