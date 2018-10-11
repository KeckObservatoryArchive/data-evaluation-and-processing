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
import re

def make_metadata(keywordsDefFile, metaOutFile, lev0Dir, extraData=None, log=None):
    """
    Creates the archiving metadata file as part of the DQA process.

    @param keywordsDefFile: keywords format definition input file path
    @type keywordsDefFile: string
    @param metaOutFile: metadata output file path
    @type metaOutFile: string
    @param lev0Dir: directory for finding FITS files and writing output files
    @type lev0Dir: string
    @param extraData: dictionary of any extra key val pairs not in header
    @type extraData: dictionary
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


    #track warning counts
    warns = {'type': 0, 'truncate': 0}


    #walk lev0Dir to find all final fits files
    if log: log.info('metadata.py searching fits files in dir: {}'.format(lev0Dir))
    for root, directories, files in os.walk(lev0Dir):
        for filename in sorted(files):
            if filename.endswith('.fits'):
                fitsFile = os.path.join(root, filename)

                extra = {}
                if filename in extraData: extra = extraData[filename]

                log.info("Creating metadata record for: " + fitsFile)
                add_fits_metadata_line(fitsFile, metaOutFile, keyDefs, extra, warns, log)


    #create md5 sum
    md5Outfile = metaOutFile.replace('.table', '.md5sum')
    if log: log.info('metadata.py creating {}'.format(md5Outfile))
    make_dir_md5_table(lev0Dir, ".metadata.table", md5Outfile)


    #warn only if counts
    if (warns['type'] > 0):
        if log: log.warning('metadata.py: Found {} data type warnings (search "metadata check" in log).'.format(warns['type']))
    if (warns['truncate'] > 0):
        if log: log.warning('metadata.py: Found {} truncation warnings (search "metadata check" in log).'.format(warns['truncate']))



def add_fits_metadata_line(fitsFile, metaOutFile, keyDefs, extra, warns, log):
    """
    Adds a line to metadata file for one FITS file.
    """

    #get header object using astropy
    header = fits.getheader(fitsFile)

    #check keywords
    check_keyword_existance(header, keyDefs, log)

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
            val = check_keyword_val(keyword, val, row, warns, log)

            #write out val padded to size
            out.write(' ')
            out.write(str(val).ljust(colSize))

        out.write("\n")
 


def check_keyword_existance(header, keyDefs, log):

    #get simple list of keywords
    keyDefList = []
    for index, row in keyDefs.iterrows():
        keyDefList.append(row['keyword'])        

    #find all keywords in header that are not in metadata file
    skips = ['SIMPLE', 'COMMENT', 'PROGTL1', 'PROGTL2', 'PROGTL3']
    for keywordHdr in header:
        if keywordHdr not in keyDefList and keywordHdr not in skips:
            if log: log.warning('metadata.py: header keyword "{}" not found in metadata definition file.'.format(keywordHdr))

    #find all keywords in metadata def file that are not in header
    skips = ['PROGTITL', 'PROPINT']
    for keywordDef in keyDefList:
        if keywordDef not in header and keywordDef not in skips:
            if log: log.warning('metadata.py: metadata keyword "{}" not found in header.'.format(keywordDef))



def check_keyword_val(keyword, val, fmt, warns, log=None):
    '''
    Checks keyword for correct type and proper value.
    '''

    #specific ERROR, UDF values that we should convert to "null"
    errVals = ['#### Error ###']
    if (val in errVals):
        val = 'null'


    #check null
    if (val == 'null'):
        if (fmt['allowNull'] == 'N'):
            raise Exception('metadata check: incorrect "null" value found for non-null keyword {}'.format(keyword))            
        return val


    #check value type
    vtype = type(val).__name__
    if (fmt['dataType'] == 'char'):
        if (vtype == 'bool'):
            if   (val == True):  val = 'T'
            elif (val == False): val = 'F'
        elif (vtype == 'int' and val == 0):
            val = ''
            if log: log.warning('metadata check: found integer 0, expected {}. KNOWN ISSUE. SETTING TO BLANK!'.format(fmt['dataType']))
        elif (vtype != "str"):
            if log: log.warning('metadata check: var type {}, expected {} ({}={}).'.format(vtype, fmt['dataType'], keyword, val))
            warns['type'] += 1
    elif (fmt['dataType'] == 'integer'):
        if (vtype != "int"):
            if log: log.warning('metadata check: var type of {}, expected {} ({}={}).'.format(vtype, fmt['dataType'], keyword, val))
            warns['type'] += 1

    elif (fmt['dataType'] == 'double'):
        if (vtype != "float" and vtype != "int"):
            if log: log.warning('metadata check: var type of {}, expected {} ({}={}).'.format(vtype, fmt['dataType'], keyword, val))
            warns['type'] += 1

    elif (fmt['dataType'] == 'date'):
        try:
            datetime.datetime.strptime(val, '%Y-%m-%d')
        except ValueError:
            if log: log.warning('metadata check: expected date format YYYY-mm-dd ({}={}).'.format(keyword, val))
            warns['type'] += 1

    elif (fmt['dataType'] == 'datetime'):
        try:
            datetime.datetime.strptime(val, '%Y-%m-%d %H:%i:%s')
        except ValueError:
            if log: log.warning('metadata check: expected date format YYYY-mm-dd HH:ii:ss ({}={}).'.format(keyword, val))
            warns['type'] += 1
     

    #check char length
    length = len(str(val))
    if (length > fmt['colSize']):
        if (fmt['dataType'] == 'double'): 
            #todo: change this back to warning once this is fixed for good?
            if log: log.info('metadata check: char length of {} greater than column size of {} ({}={}).  TRUNCATING.'.format(length, fmt['colSize'], keyword, val))
            warns['truncate'] += 1
            val = truncate_float(val, fmt['colSize'])
        else: 
            if log: log.info('metadata check: char length of {} greater than column size of {} ({}={}).  TRUNCATING.'.format(length, fmt['colSize'], keyword, val))
            warns['truncate'] += 1
            val = str(val)[:fmt['colSize']]


    #todo: check value range, discrete values?


    return val



def truncate_float(f, n):
    s = '{}'.format(f)
    exp = ''
    if 'e' in s or 'E' in s:
        parts = re.split('e', s, flags=re.IGNORECASE)
        s = parts[0]
        exp = 'e' + parts[1]

    n -= len(exp)
    return s[:n] + exp



