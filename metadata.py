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
    keyDefs = pandas.read_csv(keywordsDefFile, sep='\t')
    if log: log.info('read keywords definition file: {}'.format(keywordsDefFile))



    #create metadata table output file
    ymd = utDate.replace('-', '')
    metaFile =  lev0Dir + '/' + ymd + '.metadata.table'



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


    #put all keyword vals in a dictionary as we calculate them
    keywordVals = {}


    #get header object using astropy
    header = fits.getheader(fitsFile)


    #write all keywords vals for image to a line
    with open(metaFile, 'a') as out:

        for index, row in keyDefs.iterrows():

            keyword   = row['keyword']
            dataType  = row['dataType']
            colSize   = row['colSize']
            allowNull = row['allowNull']


            #todo: assert/log if non-null not found?
            if not (keyword in header): 
                val = 'null'
            else:
                val = header[keyword]


            #todo: check format using /tables/keywords.check
            val = check_keyword(keyword, val, row, log)


            #write out val padded to size
            out.write(' ')
            out.write(str(val).ljust(colSize))

        out.write("\n")
 


def check_keyword(keyword, val, fmt, log=None):

    #todo: assert/fail on any of these?


    #check null
    if (val == 'null'):
        if (fmt['allowNull'] == 'N'):
            if log: log.warning('metadata check fail: "null" value found for non-null keyword {}'.format(keyword))
            return val


    #check value type
    #todo: finish date check
    vtype = type(val).__name__
    if (fmt['dataType'] == 'char'):
        if (vtype != "str"):
            print (keyword, fmt['dataType'], val, 'type: ', vtype)
            if log: log.warning('metadata check fail: found var type of {}, expected {}.'.format(vtype, fmt['dataType']))

    elif (fmt['dataType'] == 'integer'):
        if (vtype != "int"):
            print (keyword, fmt['dataType'], val, 'type: ', vtype)
            if log: log.warning('metadata check fail: found var type of {}, expected {}.'.format(vtype, fmt['dataType']))

    elif (fmt['dataType'] == 'double'):
        if (vtype != "float"):
            print (keyword, fmt['dataType'], val, 'type: ', vtype)
            if log: log.warning('metadata check fail: found var type of {}, expected {}.'.format(vtype, fmt['dataType']))

    elif (fmt['dataType'] == 'date'):
        pass

        

    #check char length
    #TODO: remove truncate?
    length = len(str(val))
    if (length > fmt['colSize']):
            if log: log.warning('metadata check fail: char length of {} greater than column size of {} keyword {}.  TRUNCATING.'.format(length, fmt['colSize'], keyword))
            val = val[:fmt['colSize']]



    #todo: check value range
    


    #return val 
    return val