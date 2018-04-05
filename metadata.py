"""
  This script creates the archiving metadata file as part of the DQA process.

  Original scripts written in IDL by Jeff Mader
  Ported to python by Josh Riley

#TODO: add more code documentation
#TODO: move this code into instrument.py

"""



#imports
import sys
import os
from astropy.io import fits
import pandas
from common import get_root_dirs


def make_metadata(instr, utDate, rootDir, tablesDir, log=None):
    """
    Creates the archiving metadata file as part of the DQA process.

    @param instr: instrument name
    @type instr: string
    @param rootDir: root directory for data processing
    @type rootDir: string
    @param utDate: UT date (yyyy-mm-dd)
    @type utDate: string
    @param tablesDir: directory containing metadata keyword definition files
    @type rootDir: string
    """


    if log: log.info('make_metadata.py started for {} {} UT'.format(instr.upper(), utDate))


    #get various dirs
    dirs = get_root_dirs(rootDir, instr, utDate)


    #open keywords format file and read data
    #NOTE: changed this file to tab-delimited
    keywordsDefFile = tablesDir + '/keywords.format.' + instr
    keyDefs = pandas.read_csv(keywordsDefFile, sep='\t')



    #create metadata table output file
    #todo: creating dir if it does not exist, but prob don't need that.
    #(example: /koadata21/MOSFIRE/20180403/lev0/20180403.metadata.table)
    if not os.path.exists(dirs['lev0']): os.makedirs(dirs['lev0'])
    ymd = utDate.replace('-', '')
    metaFile =  dirs['lev0'] + '/' + ymd + '.metadata.table'



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
    for root, dirs, files in os.walk(dirs['lev0']):
        for filename in files:
            if filename.endswith('.fits'):
                fitsFile = os.path.join(root, filename)
                add_fits_metadata_line(fitsFile, metaFile, keyDefs)




def add_fits_metadata_line(fitsFile, metaFile, keyDefs):
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
                if allowNull == 'N':
                    print ("WARNING: NON-NULL KEYWORD NOT FOUND: ", keyword)
                val = 'null'
            else:
                val = header[keyword]


            #todo: check format using /tables/keywords.check


            #write out val padded to size
            out.write(' ')
            out.write(str(val).ljust(colSize))

        out.write("\n")
 

