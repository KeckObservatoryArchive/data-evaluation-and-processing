"""
  This script consolidates all the pieces of the KOA data quality
  assessment into one place. Upon completion, it should populate the
  process directory with the final FITS files, in some cases adding 
  header keywords where necessary.

  Usage: dqa_run(instrObj, tpx)

  Original scripts written by Jeff Mader and Jennifer Holt
  Ported to Python3 by Matthew Brown and Josh Riley
"""
import get_header
import os
import logging as lg
import numpy as np
#import getProgInfo as gpi
import math
import shutil
from glob import glob
from common import *
from datetime import datetime as dt
from astropy.io import fits
from urllib.request import urlopen
#from imagetyp_instr import imagetyp_instr
from create_log import *
from create_prog import *
import metadata


def dqa_run(instrObj, tpx=0):
    """
    This function will analyze the FITS file to determine if they will be
    archived and if they need modifications or additions to their headers.

    @type instrObj: instrument
    @param instr: The instrument object
    """


    #shorthand
    instr  = instrObj.instr
    utDate = instrObj.utDate
    log    = instrObj.log
    dirs   = instrObj.dirs


    #Log start
    log.info('dqa_run.py started for {} {}'.format(instr, utDate))


    # Error if stageDir does not exist (required input files)
    if not os.path.isdir(dirs['stage']):
        print('dqa_run.py: stage dir does not exist.  EXITING.')
        exit()
        #todo: log, email, and return


    # Create the LOC file
    #todo: why do we create this?  should we exit if it exists?
    locFile = ''.join((dirs['lev0'], '/dqa.LOC'))
    with open(locFile, 'w') as fp:
        fp.write('DQA started')


    #determine program info
    create_prog(instrObj)
    #proginfo = gpi.ProgSplit()
    #progData = proginfo.getProgInfo()


    # dep_obtain file (list of programs)
    #todo: what are we doing with this?
    obtfile = ''.join((dirs['stage'], '/dep_obtain', instr, '.txt'))


    # Read the list of FITS files
    #todo: NOTE: current process copies 'dqa_locate<instr>.txt' output to 'dqa_<instr>.txt' and uses this
    #after searching and removing corrupted fits files.
    dqafile = ''.join((dirs['stage'], '/dqa_', instr, '.txt'))
    files = []
    with open(dqafile, 'r') as dqalist:
        for line in dqalist:
            files.append(line.strip())


    # How many files will be processed?
    numFiles = len(files)
    log.info('dqa_run.py there are {} files to process'.format(numFiles))


    #define vars to use throughout
    ymd = utDate.replace('-', '')


    # Create containers to hold infile and outfile
    inFiles = []
    outFiles = []


    # Catch for corrupted files
    try:

        # Loop through each entry in input_list
        for filename in files:

            log.info('dqa_run.py input file is {}'.format(filename))


            #set current file to work on
            instrObj.set_fits_file(filename)


            # do keyword checks.  if any of these steps return false then skip and copy to udf
            #todo: These checks may be unique per instrument so move this instrument.py function like do_dqa_checks()
            #todo: error checking, log, asserts?
            #todo: remaining tasks, extensions, etc?
            #todo: see dqa_lite.pro "Add DQA generated keywords" code
            #todo: check create_lev0_jpg for accuracy?
            ok = True
            if ok: ok = instrObj.check_instr()
            if ok: ok = instrObj.set_dateObs()
            if ok: ok = instrObj.set_utc()
            if ok: ok = instrObj.set_elaptime()
            if ok: ok = instrObj.set_koaimtyp()
            if ok: ok = instrObj.set_koaid()
            if ok: ok = instrObj.set_ut()
            if ok: ok = instrObj.set_frameno()
            if ok: ok = instrObj.set_ofName()
            if ok: ok = instrObj.set_semester()
            if ok: ok = instrObj.set_prog_info(progData)
            if ok: ok = instrObj.set_wavelengths()
            if ok: ok = instrObj.set_specres()
            if ok: ok = instrObj.write_lev0_fits_file()
            if ok: ok = instrObj.create_lev0_jpg()


            # checks failed?  copy to udf
            if (not ok): 
                log.info('copying {} to {}'.format(filename, dirs['udf']))
                shutil.copy2(filename, dirs['udf']);
                continue

            #keep list of good fits filenames
            else:
                inFiles.append(os.path.basename(instrObj.fitsFilepath))
                outFiles.append(instrObj.fitsHeader.get('KOAID'))


        #log num files passed DQA
        log.info('dqa_run.py: {} files passed DQA'.format(len(inFiles)))


        #Create yyyymmdd.filelist.table
        fltFile = dirs['lev0'] + '/' + ymd + '.filelist.table'
        with open(fltFile, 'w') as fp:
            for i in range(len(inFiles)):
                fp.write(inFiles[i] + ' ' + outFiles[i] + "\n")
            fp.write("    " + str(len(inFiles)) + ' Total FITS files\n')


        #create metadata file
        tablesDir = '/kroot/archive/tables'
        tablesDir = '/home/jriley/test/metadata_tables'
        metadata.make_metadata(instr, utDate, dirs['lev0'], tablesDir, log)


        #Create yyyymmdd.FITS.md5sum.table
        md5Outfile = dirs['lev0'] + '/' + ymd + '.FITS.md5sum.table'
        log.info('dqa_run.py creating {}'.format(md5Outfile))
        make_dir_md5_table(dirs['lev0'], ".fits", md5Outfile)


        #Create yyyymmdd.JPEG.md5sum.table
        md5Outfile = dirs['lev0'] + '/' + ymd + '.JPEG.md5sum.table'
        log.info('dqa_run.py creating {}'.format(md5Outfile))
        make_dir_md5_table(dirs['lev0'], ".jpg", md5Outfile)


        #gzip the fits files
        import gzip
        for file in os.listdir(dirs['lev0']):
            if file.endswith('.fits'): 
                in_path = dirs['lev0'] + '/' + file
                out_path = in_path + '.gz'
                with open(in_path, 'rb') as fIn:
                    with gzip.open(out_path, 'wb') as fOut:
                        shutil.copyfileobj(fIn, fOut)
                        os.remove(in_path)


        #update TPX: archive ready
        #todo: how to get pi, sdata, and sci_files (see commented old port code below)
        #todo: is arch_time utc or not?
        if tpx:
            utc_timestamp = dt.utcnow().strftime("%Y%m%d %H:%M")
            # update_koatpx(instr, utDate, 'pi', '???', log)
            # update_koatpx(instr, utDate, 'sdata', '???', log)
            # update_koatpx(instr, utDate, 'sci_files', '???', log)
            update_koatpx(instr, utDate, 'arch_state', 'DONE', log)
            update_koatpx(instr, utDate, 'arch_time', utc_timestamp, log)


        #Remove the LOC file
        locFile = ''.join((dirs['lev0'], '/dqa.LOC'))
        os.remove(locFile)



    #catch exceptions
    except Exception as err:
        log.error('dqa_run.py program crashed, exiting: {}'.format(str(err)))



    #log success
    log.info('dqa_run.py DQA Successful for {}'.format(instr))





#######################################################
######  OLD PORT (keeping for reference for now) ######
#######################################################

#    # Get the keys requires for the FITS files
#    keysMeta = get_keys_meta(instr, tablesDir)
#    num_keys = len(keysMeta)

#    # Store keyword values in the following arrays
#    kname = []
#    kvalue = []
#    nkw = []

#    #define vars to use throughout
#    sdata = ''
#    pi = ''
#    progid = ''
#    acct = ''
#    i = 0
#    i2 = 0
#    num_sci = 0

#    try:
#        for filename in files:
#            if log_writer:
#                log_writer.info('dqa_run.py input file is {}'.format(filename))
#            # Read the zero header
#            with fits.open(filename) as hdulist:
#                keys = hdulist[0].keys
#
#                # Temp fix for bad file times (NIRSPEC legacy)
#                fixdate = date
#                fixdatetime(fixdate, filename, keys)
#
#                # Is this a HIRES file?
#                test = filename.split('/')
#                goodfile = ''
#                log.info(instr,': check_instr')
#                check_instr(instr, filename, keys, udfDir, goodfile)
#                if goodfile == 'no':
#                    exit()
#                # Number of Extensions: nexten = numccds * numamps
#                log.info(instr, ': numamps')
#                numAmps = numamps(keys)
#                log.info(instr, ': numccds')
#                numCCDs = numccds(keys)
#                nexten = numAmps * numCCDs
#
#                # Need Semester to Fix DATE-OBS, if not ERROR or 0
#                if keys['DATE-OBS'] not in ['ERROR', 0]:
#                    semester(keys)
#
#                # Determine KOAID
#                log.info(instr, ': koaid')
#                koaid(keys)
#                if keys['KOAID'] == 'bad':
#                    log.warning(instr,
#                            ': KOAID could not be created for ', filename)
#                    exit()
#
#                # Add mosaic keywords to legacy data, UT from UTC
#                log.info(instr, ': add_keywords')
#                add_keywords(instr, keys, nexten)
#                skip = 'n'
#                j = 0
#                for j in range(key):
#                    if keycheck[j] eq 'Y':
#                        try:
#                            test = keys[keycheck2[j]]
#                        # If key does not exist, log it and skip
#                        except KeyError:
#                            log.warning(''.join((instr, ': ',
#                                    keycheck2[j], ' keyword missing')))
#                            exit()
#            # Read the header and image data from the input file
#            # Legacy data and NIRESPEC
#            if nexten == 0:
#                naxis1 = keys.get('NAXIS1')
#                naxis2 = keys.get('NAXIS2')
#                # Define image array
#                if instr in ['DEIMOS','ESI','HIRES','LRIS']:
#                    image = [1,int(naxis1),int(naxis2)]
#                elif instr in ['NIRC2','NIRSPEC']:
#                    image = [1,long(naxis1),long(naxis2)]
#                elif instr in ['OSIRIS']:
#                    image = [float(1),float(naxis1),float(naxis2)]
#                # Read image
#                data = hdulist[0].data
#
#                # Write to log (HIRES)
#                if instr == 'HIRES':
#                    log.info(''.join((instr, ': Legacy data')))
#
#                # Add BLANK (HIRES -32768), if missing
#                try:
#                    blank = keys['BLANK']
#                except KeyError:
#                    blank = -32768
#                    text = ' Keyword added by KOA software'
#                    keys.insert('BLANK'  , (blank, text))
#                    log.info(''.join((instr, ': BLANK added to header')))
#            else:
#            #Mosaic Data
#                ext = 0
#                # Define header, nkeywords, size_image arrays
#                header = []
#                image=[]
#                hdr = None
#                nkeywords = []
#                size_image = [0 for i in range(nexten+1)]
#                while ext < nexten:
#                    # Read extension header
#                    try:
#                        hdr = fits.getheader(filename, ext=ext+1)
#                    except Exception as e:
#                        log.error(''.join((instr, ': Error reading extension ', str(ext))))
#                        exit()
#                    try:
#                        blank = hdr['BLANK']
#                    except KeyError:
#                        blank = -32768
#                        text = ' Keyword added by KOA software'
#                        hdr.insert('BLANK', (blank, text))
#                        log.info(''.join((instr, ': BLANK added to image header for extension ', str(ext+1))))
#                    # Determine the number of keywords
#                    try:
#                        # This gets rid of the extra whitespace for some reason
#                        hdr.pop('')
#                    except:
#                        pass
#                    nkeywords.append(len(hdr))
#
#                    # Store extension header in array
#                    header.append(hdr)
#
#                    # Read image
#                    try:
#                        img = hdulist[ext+1].data
#                    except Exception as e:
#                        log.error(instr, ': Error reading image extension ', str(ext))
#                        exit()
#                    # Append the extension image to the list
#                    image.append(img)
#
#                    # Increment Extensions
#                    ext += 1
#                # End While loop
#            # End else
#
#            # First fix the BINNING keyword, if necessary
#            try:
#                binning = header['BINNING']
#                bin2 = binning.replace(' ','')
#                if binning not in bin2:
#                    text = ''.join((' Keyword changed from '. binning))
#                    keys.update('BINNING', (bin2, text))
#            except:
#                pass
#
#            # Get current list of KOAIDs in lev0_dir
#            koaid_found = []
#            for root, dirs, files in os.walk(lev0Dir):
#                for k_id in files:
#                    if '.fits' not in k_id:
#                        continue
#                    elif k_id not in koaid_found:
#                        koaid_found.append(''.join((root,'/',item)))
#                    else:
#                        log.warning(instr, ': KOAID ', k_id,
#                                ' exists for ' + filename)
#                        exit()
#
#            # Call SEMESTER
#            log.info(instr, ': semester')
#            semester(keys)
#
#            # Call IMAGETYP
#            log.info(instr, ': imagetyp')
#            imgtype = imagetyp_instr(instr, keys)
#            if imgtype == 'object':
#                num_sci += 1
#
#            # Add DQA generated keywords
#            log.info(instr, ': add_metakeywords')
#            pi, sdata, datlevel, progid, progtitl, acct = add_metakeywords(
#                    instr, date, filename, keys['KOAID'], imtype, keys, image, header,
#                    nexten, obtfile, ancDir)
#
#    except KeyError:
#        print('Invalid Key')
#        log.error('Invalid Key')
#    except Exception as err:
#        print('Program Crashed - Exiting: ', str(err))
#        log.error('Program Crashed - Exiting: ', str(err))

''' Old Stuff
    files = glob('*.fits*')
    for filename in files:
        header = get_header.HDU(filename)
        keywords = header.keywords
        data = header.data
        instr = keywords['INSTRUME'].lower()

        if instr in modules:
            module = importlib.import_module(instr)
            module.go(keywords, data, filename)
            # Write file to lev1 directory
            # header.hdu.writeto('')
        else:
            # Do something
            pass
'''

#-----------------------END DQA RUN-------------------------------------------



#def get_keys_meta(instrument, tablesDir):
#    # Get the critical keywords from from keyword.check
#    if instrument in ['DEIMOS', 'ESI', 'LRIS', 'OSIRIS']:
#        key_check = ''.join((tablesDir, '/keywordsMyKOA.check'))
#    elif instrument == 'HIRES':
#        key_check = ''.join((tablesDir, '/keywords.check'))
#    elif instrument == 'NIRC2':
#        key_check = ''.join((tablesDir, '/keywordsNirc2.check'))
#    elif instrument == 'NIRSPEC':
#        key_check = ''.join((tablesDir, '/NIRSPECkeywords.check'))
#    elif instrument == 'NIRES':
#        key_check = ''.join((tablesDir, '/keywords.format.NIRES'))
#
#    # Get the key meta data from the check file
#    keysMeta = []
#    with open(key_check, 'r') as fitskeys:
#        for line in fitskeys:
#            keysMeta.append(line.split(' '))
#    return keysMeta

#-------------------END GET KEYS META-------------------------------




# def add_metakeywords(instr, date, ifile, fkoaid, imagetyp, keys,
#         image, iheader, nexten, obtfile, ancDir, log):
#     """
#     """
#     log.info('Starting add_metakeywords')


#     # Get koaid keyword
#     fkoaid = koaid(keys)
#     if instr not in ['HIRES','NIRC2','NIRSPEC']:
#         keys.update('KOAID', (fkoaid, ' KOA data file name'))
#         stageDir = ancDir.replace(instr, ''.join(('stage/',instr)))
#         stageDir = stageDir.replace('/anc','')

#         # Get ProgID, ProgPI, ProgInst
#         req = ''.join(('https://www.keck.hawaii.edu/software/db_api/',
#                 'telSchedule.php?cmd=getSchedule&date=', date, '&instr=',
#                 instr, '&column=ProjCode,Principal,Institution'))
#         res = url.urlopen(req).read().decode()
#         dat = json.loads(res)

#         keys['progid'] = (dat['ProjCode'], 'WMKO Program ID')
#         keys['progpi'] = (dat['Principal'], 'Program Institution')
#         keys['proginst'] = (dat['Institution'], 'Program Principal Investigator')

#         # Get ProgTitl
#         req = ''.join(('https://www.keck.hawaii.edu/software/db_api/',
#                 'koa.php?cmd=getTitle&semid=', progid))
#         res = url.urlopen(req).read().decode()
#         dat = json.loads(res)
#         keys['progtitl '] = (dat['progtitl'], 'Program Title')

#         # Find the observing semester
#         log.info('add_metakeywords: semester')
#         sem = semester(keys)
#         keys['semester'] = (sem, 'WMKO Observing Scheudule Semester')

#     log.info('add_metakeywords: datlevel')
#     datlevel = data_level('raw')
#     dqa_date(keys)
#     dqa_vers(keys)

#     # Instrument Specific Keyword Additions
#     if instr == 'HIRES':
#         # Wavelengths
#         log.info('add_metakeywords: lambda_xd')
#         filname = keys.get('FILNAME')
#         wavecntr, waveblue, wavered = lambda_xd(nexten, keys)
#     elif instr == 'NIRSPEC':
#         # DETGAIN, MODE, & RN
#         if 'NS' in fkoaid:
#             detmode = 'spec'
#             detgain = 5
#             detrn = 10
#         elif 'NC' in fkoaid:
#             detmode = 'scam'
#             detgain = 4
#             detrn = 25
#         else:
#             detmode = 'null'
#             detgain = 'null'
#             detrn = 'null'

#         # Dispersion
#         log.info('add_metakeywords: nirspec_disp')
#         dispersion, dispscal = nirspec_disp(keys)

#         # Get differential tracking
#         log.info('add_metakeywords: get_dtrack')
#         dra, ddec, dtrack, update = get_dtrack(keys, ancDir)

#         # Get image statistics
#         log.info('add_metakeyworsd; nirspec_imagestat')
#         imgmean, imgstdv, imgmed = nirspec_imagestat(keys, image, dispersion)

#         # Server Crash?
#         log.info('add_metakeywords: nirspec_crash')
#         crash = nirspec_crash(keys, ifile)

# def data_level(ftype):
#     datalevel = None

#     # Raw - level 0
#     if ftype == 'raw':
#         datalevel = 0
#     elif ftype == 'reduced':
#         datalevel = 1
#     return datalevel

# def dqa_date(keys):
#     """
#     Determines the date timestamp for when the DQA module was run
#     """
#     dqa_date = dt.now()
#     keys['dqa_date'] = dt.strftime(dqa_date, '%Y-%m-%s %H:%M:%S')
#     return

# def dqa_vers(keys):
#     path = '/kroot/archive/dep/dqa/default'
#     keys['dqa_vers'] = (os.readlink(path), 'Live build version')
#     return

# def lambda_xd(nexten, keys):
#     # Default to null
#     waveblue = 'null'
#     wavecntr = 'null'
#     wavered = 'null'

#     # Set pixel and CCD size
#     psize = 0.015
#     npix = 3072.0
#     if nexten == 0:
#         psize = 0.024
#         npix = 1024.0

#     # Make sure stages are homed
#     try:
#         xdispers = keys['XDISPERS'].strip()
#     except KeyError:
#         xdispers = 'RED'
#     try:
#         xdcal = keys['XDCAL'].strip()
#         exhcal = keys['ECHCAL'].strip()
#     except KeyError:
#         return wavecntr, waveblue, wavered
#     if xdcal == 0 or exhcal == 0:
#         return wavecntr, waveblue, wavered

#     # Determine XD groove spacing and HIRES angle setting
#     try:
#         xdsigmai = keys['XDSIGMAI']
#         xdangl = keys['XDANGL']
#         echangl = keys['ECHANGL']
#     except KeyError:
#         return wavecntr, waveblue, wavered

#     # Specifications camera-collimator, blaze, cal offset angles
#     camcol = 40.*math.pi/180.
#     blaze = -4.38*math.pi/180.
#     offset = 25.0 - 0.63        # 0-order + 5 deg for home

#     # Grating Equation
#     alpha = (xdangl+offset)*math.pi/180.
#     d = 10**7/xdsigmai                    # microns
#     wavecntr = d*((1.+math.cos(camcol))*math.sin(alpha)
#             - math.sin(camcol)*math.cos(alpha))
#     ccdangle = math.atan(npix*psize/1.92/762.0)    # f = 762mm, psize u pix, 1.92 amag

#     # Blue end
#     alphab = alpha - ccdangle
#     waveblue = d*((1.+math.cos(camcol))*math.sin(alphab)
#             - math.sin(camcol)*math.cos(alphab))

#     # Red end
#     alphar = alpha + ccdangle
#     wavered =  d*((1.+math.cos(camcol))*math.sin(alphar)
#             - math.sin(camcol)*math.cos(alphar))

#     # Center
#     wavecntr = int(wavecntr)
#     waveblue = int(waveblue)
#     wavered  = int(wavered)

#     # Get the correct equation constants
#     if xdispers == 'RED':
#         # Order 62, 5748 A, order*wave= const
#         const = 62.0 * 5748.0
#         a = 1.4088
#         b = -306.6910
#         c = 16744.1946
#         if nexten == 0:
#             a = 1.1986
#             b = -226.6224
#             c = 10472.6948
#     elif xdispers == 'UV':
#         # Order 97, 3677 A, order*wave = const
#         const = 97.0*3677.0
#         a = 0.9496
#         b = -266.2792
#         c = 19943.7496
#         if nexten == 0:
#             a = 0.5020
#             b = -148.3824
#             c = 10743.1746
#     elif xdispers == '':
#         return wavecntr, waveblue, wavered

#     # Correct wavelength values
#     i = 1
#     while i <= 3:
#         if i == 1:
#             wave = wavecenter
#         elif i == 2:
#             wave = waveblue
#         elif i == 3:
#             wave = wavered
#         # Find order
#         order = math.floor(const/wave)

#         # Find shift in Y: order 62 = npix with XD=ECH=0 (RED)
#         # Find shift in Y: order 97 = npix with XD=ECH=0 (BLUE)
#         tryit = 1
#         while nexten != 0 and tryit < 100:
#             if i == 1:
#                 shift = a*order*order + b*order + c
#                 newy = npix - shift
#                 newy = -newy
#             else:
#                 shift2 = a*order*order + b*order + c
#                 if nexten == 0:
#                     if i == 1:
#                         shift2 = shift2 + npix
#                     elif i == 3:
#                         shift2 = shift2 + 2*npix
#                 newy2 = shift2 - newy
#                 if newy2 < 120:
#                     order = order - 1
#                     tryit += 1
#                     if nexten != 0 and tryit < 100:
#                         continue
#                 npix2 = 2*npix
#                 if nexten == 0:
#                     npix2 = npix2/2
#                 if newy2 > npix2:
#                     order += 1
#                     tryit += 1
#                     if nexten != 0 and tryit < 100:
#                         continue

#         # Find delta wave for order
#         dlamb = -0.1407*order + 18.005

#         # New wavecntr = central wavelength for this order
#         wave = const/order

#         # Correct for echangl
#         wave += (4 * dlamb * echangl)

#         # round to nearest 10 angstroms
#         wave2 = wave % 10
#         if wave2 < 5:
#             wave -= wave2
#         else:
#             wave += (10 - wave2)

#         # cleanup
#         if wave < 2000 or wave > 20000:
#             wave = 'null'
#         if i == 1:
#             wavecntr =  wave
#         elif i == 2:
#             waveblue = wave
#         elif i == 3:
#             wavered = wave
#         i += 1
#     return wavecntr, waveblue, wavered

# def nirspec_disp(keys):
#     dispersion = 'null'
#     dispscal = 'null'
#     k_id = keys['KOAID']
#     if'NC' not in k_id:
#         return dispersion, dispscal
#     dispersion = 'unknown'
#     try:
#         echelle = keys['ECHLPOS']
#     except KeyError:
#         dispersion = 'unknown'
#         return dispersion, dispscal
#     if echelle > 100:
#         dispersion = 'low'
#         dispscal = 0.190
#     elif echelle <= 100:
#         dispersion = 'high'
#         dispscal = 0.144
#     return disperion, dispscal

# def get_dtrack(keys, ancDir):
#     # If DTRACK exists in header, return
#     update = 'no'
#     dtrack = keys['DTRACK']
# #    if dtrack not None:
# #        return dra, ddec, dtrack, update
#     update = 'yes'

#     # Get RA, DEC, TARGETNAME
#     ra = keys['RA']              # ra = 49.509
#     dec = keys['DEC']            # dec = 7.466
#     targname = keys['TARGNAME']  # targname = '2001PT13 05UT'

#     # Default values
#     dra    = 'null'
#     ddec   = 'null'
#     dtrack = 'null'

#     # Read DCSlog
#     if not targname or not ra or not dec or not ancDir:
#         return dra, ddec, dtrack, update

#     # Does dcsinfo file exist
#     dcsfile = ''.join((ancDir, '/nightly/dcsinfo'))
#     if not os.path.exists(dcsfile):
#         return 'null', 'null', 'null', 'no'

#     # Read the file
#     savevals = {'targname':'', 'targra':'', 'targdec':'', 'dtrack':'', 'dra':'', 'ddec':''}
#     with open(dcsfile, 'r') as dcslog:
#         for line in dcslog:
#             use = 'no'
#             targname = targra = targdec = dtrack = dra= ddec = ''
#             for val in savevals:
#                 if val in line:
#                     tmp = line.split('=')
#                     savevals[val] = tmp[1].strip()
#                     use = 'yes'
#             # If target found then...
#             if use == 'yes' and targname == name:
#                 hr, mn, sc = targra.split(':')
#                 thisRA = (hr + mn/60.0 + sc/3600.0) * 1500
#                 dg, mn, sc = targdec.split(':')
#                 sign = 1
#                 if dg < 0:
#                     deg = -deg
#                     sign = -1
#                 thisDEC = dg + mn/60.0 + sc/3600.0
#                 thisDEC *= sign
#                 dra = abs(thisRA - ra)
#                 ddec = abs(thisDEC - dec)
#                 if dra < 0.01 and ddec < 0.01:
#                     return dra, ddec, dtrack, update
#     return dra, ddec, dtrack, update

# def nirspec_imagestat(keys, image, dispersion):
#     if not keys and not image and not dispersion:
#         log.info('Syntax: nirspec_imagestat: header, image, dispersion')
#         return 'null', 'null', 'null'

#     # Defaults
#     imgmean = 'null'
#     imgstdv = 'null'
#     imgmed  = 'null'

#     # Determine image format
#     naxis1 = keys['NAXIS1']
#     naxis2 = keys['NAXIS2']
#     x = naxis1/2
#     y = naxis2/2

#     # For low dispersion, spectrum is to the right of center
#     # Make sure NOT scam
#     try:
#         outdir2 = keys['OUTDIR2']
#     except KeyError:
#         if dispersion == 'low':
#             x = 715.0
#     if outdir2:
#         y -= 20

#     # Sampling Box
#     img = image[0][x-15:x+15,y-15:y+15]
#     imgmean = numpy.mean(img)
#     imgstdv = numpy.std(img)
#     imgmed  = numpy.median(img)

#     return imgmean, imgstdv, imgmed

# def nirspec_crash(keys, ifile, log):
#     # Add CRASH keyword, default is CRASH = No
#     crash = 'No'
#     keys['CRASH'] = ('No', 'NIRSPEC server crash detected?')

#     # Crash if FILNAME is UNKNOWN
#     filname = keys['FILNAME']
#     slitname = keys['SLITNAME']
#     if filname != 'UNKNOWN' and slitname != 'UNKNOWN':
#         return 'No'

#     # Crash detected
#     crash = 'Yes'
#     log.warning('nirspec_crash: Crash detected')
#     keys['CRASH'] = 'Yes'

#     # Get the file number and root name of this file
#     try:
#         filenum = keys['FILENUM']
#     except KeyError:
#         filenum = keys['FILENUM2']
#     rootname = keys['ROOTNAME'].strip()

#     # Starting with the previous file, loop through until
#     # file is found that was written before the crash.
#     filenum -= 1
#     while filenum >= 0:
#         # Construct the filename to previous file
#         num2 = int(filenum.strip())
#         if 100 <= num2 < 1000:
#             num2 = ''.join(('0', string(num2)))
#         if 10 <= num2 < 100:
#             num2 = ''.join(('00', string(num2)))
#         if num2 < 10:
#             num2 = ''.join(('000', string(num2)))
#         prefile = ''.join((rootname, num2.strip(), '.fits'))

#         # Directory to look in
#         rdir = ifile.split(rootname)[0]

#         # Find the file
#         for root, dirs, files in os.walk(rdir):
#             prevfile = ''.join((root,files))

#         # If file found, continue
#         if prevfile == '':
#             filenum -= 1
#             continue

#         # Read this header
#         prevhead = fits.getheader(prevfile)

#         # Good header if FILNAME not UNKNOWN
#         filname = prevhead['FILNAME'].strip()
#         slitname = prevhead['SLITNAME'].strip()
#         if filname != 'UNKNOWN' and slitname != 'UNKNOWN':
#             # loop through all the keywords and fix those
#             # That are bogus
#             for key in prevhead:
#                 if key != 'COMMENT':
#                     comment = prevhead[key].split('/')

