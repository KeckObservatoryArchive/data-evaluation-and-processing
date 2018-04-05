import get_header
import importlib
import os
import logging as lg
import numpy as np
#import getProgInfo as gpi
import math
from glob import glob
from common import koaid
from datetime import datetime as dt
from astropy.io import fits
from urllib.request import urlopen
#from imagetyp_instr import imagetyp_instr
from create_log import *
from verification import *

#modules = ['nirspec', 'kcwi']

def dqa_run(instr, utDate, rootDir, tpxlog=0, log_writer=''):
    """
    """

    # Verify input parameters

    instr = instr.upper()
    verify_instrument(instr)
    verify_date(utDate)
    assert os.path.isdir(rootDir), 'rootDir does not exist'

    # Setup log_writer, if it doesn't exist already

    if not log_writer:
        log_writer = create_log(rootDir, instr, utDate)

    if log_writer:
        log_writer.info('dqa_run.py started for {} {}'.format(instr, utDate))

    # Set up default directories

    tablesDir = '/kroot/archive/tables'
    dirList = get_root_dirs(rootDir, instr, utDate)
    udfDir = ''.join((dirList['anc'], '/udf/'))

    return

    # Error if stageDir does not exist (required input files)

    if not os.path.isdir(stageDir):
        log_writer
        email
        return

    # Create the directories, if they don't already exist

    for dir in [lev0Dir, lev1Dir, udfDir]:
        if log_writer:
            log_writer.info('dqa_run.py using directory {}'.format(dir))
        if not os.path.isdir(dir):
            os.mkdir(dir)

    # Additions for NIRSPEC

    if instr == 'NIRSPEC':
        os.mkdir(lev0Dir + '/scam')
        os.mkdir(lev0Dir + '/spec')

    # Create the LOC file

    locFile = lev0Dir + '/dqa.LOC'

    udate = date
    createprog(instr, udate, stageDir, log)
#    proginfo = gpi.ProgSplit()
#    proginfo.getProgInfo()

    # Input file for dqa_run (list of FITS files)

    dqafile = ''.join((stageDir, '/dqa_', instr, '.txt'))

    # dep_obtain file (list of programs)

    obtfile = ''.join((stageDir, '/dep_obtain', instr, '.txt'))

    # Read the input file and store it in a something
    files = []
    with open(dqafile, 'r') as dqalist:
        for line in dqalist:
            files.append(line)

    # How many files will be processed?

    numFiles = len(files)
    if log_writer:
        log_writer.info('dqa_run.py there are {} files to process'.format(num_Files))

#    # Get the keys requires for the FITS files
#    keysMeta = get_keys_meta(instr, tablesDir)
#    num_keys = len(keysMeta)

#    # Create containers to hold infile and outfile
#    infile = []
#    outfile = []

#    # Store keyword values in the following arrays
#    kname = []
#    kvalue = []
#    nkw = []

    # Instanciate the instrument class

    moduleName = ''.join(('instr_', instr.lower()))
    module = importlib.import_module(moduleName)
    module.go()

    # Loop through each entry in input_list
    sdata = ''
    pi = ''
    progid = ''
    acct = ''
    i = 0
    i2 = 0
    num_sci = 0

    # Catch for corrupted files

    try:
        for filename in files:

            # Read the FITS header

            module.header = ''

            # Is this actually an instrument FITS file?

            check = module.check_instr()...

            ...

    except Exception as err:
        print('Program Crashed - Exiting: ', str(err))
        log_writer.error('dqa_run.py program crashed, exiting: {}'.format(str(err)))

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

def create_prog(instr, utdate, stageDir, log):
    log.info('create_prog: Getting FITS file information')

    dep_obtain = stageDir + '/dep_obtain' + instr + '.txt'

    oa = []
    fileList = []

    # Get OA
    with open(dep_obtain, 'r') as dob:
        for line in dob:
            items = line.strip().split(' ')
            if len(items)>1:
                oa.append(items[1])

    if len(oa) >= 1:
        oa = oa[0]

    # Get all files
    ''' This part was commented out in the idl file
    for root, dirs, files in os.walk(stageDir):
        for item in files:
            if '.fits' in item:
                seq = (root, item)
                fileName = ''.join(seq)
                fileList.append(fileName)
    '''
    seq = (stageDir, '/dqa_', instr, '.txt')
    dqa_instr = ''.join(seq)
    with open(dqa_instr, 'r') as dqa:
        for item in dqa:
            fileList.append(item.strip())

    # Open output file
    seq = (stageDir, '/createprog.txt')
    outfile = ''.join(seq)

    with open(outfile, 'w') as ofile:
        for item in fileList:
            if item.strip() != '':
                if instr == 'OSIRIS':
                    if item[-1] == 'x':
                        log.info(item + ': file ends with x')
                        continue
                header = fits.getheader(item)

                # Temp fix for bad file times(NIRSPEC legacy)
                fixdate = utdate
                fixdatetime(fixdate, item, header)
                imagetyp = imagetyp_instr(instr, header)
                udate = header.get('DATE-OBS').strip()
                if 'Error' in udate or udate == '':
                    lastMod = os.stat(item).st_mtime
                    udate = dt.fromtimestamp(lastMod).strftime('%Y-%m-%d')

                # Fix yy/mm/dd to yyyy-mm-dd
                if '-' not in udate:
                    yr, mo, dy = udate.split('/')
                    seq = ('20', yr, '-', mo, '-', dy)
                    udate = ''.join(seq)
                try:
                    utc = header['UT'].strip()
                except KeyError:
                    try:
                        utc = header['UTC'].strip()
                    except KeyError:
                        utc = dt.fromtimestamp(lastMod).strftime('%H:%M:%S')
                observer = header.get('OBSERVER').strip()
                try:
                    fileno = header['FILENUM']
                except KeyError:
                    try:
                        fileno = header['FILENUM2']
                    except KeyError:
                        try:
                            fileno = header['FRAMENO']
                        except KeyError:
                            try:
                                fileno = header['IMGNUM']
                            except KeyError:
                                try:
                                    fileno = header['FRAMENUM']
                                except KeyError:
                                    pass
                try:
                    outdir = header['OUTDIR']
                except KeyError:
                    try:
                        outdir = header['OUTDIR2']
                    except KeyError:
                        pass
                fileparts = item.split('/sdata')
                if len(fileparts) > 1:
                    newFile = '/sdata' + fileparts[-1]
                else:
                    newFile = item
                newFile = newFile.replace('//','/')
                ofile.write(newFile+'\n')
                ofile.write(udate+'\n')
                ofile.write(utc+'\n')
                ofile.write(outdir+'\n')
                ofile.write(observer+'\n')
                ofile.write(str(fileno)+'\n')
                ofile.write(imagetyp+'\n')

                try:
                    progname = header.get('PROGNAME')
                    if progname == None:
                        progname = header['PROGID']
                except KeyError:
                    ofile.write('PROGNAME\n')
                    ofile.write('PROGPI\n')
                    ofile.write('PROGINST\n')
                    ofile.write('PROGTITL\n')
                else:
                    progname = progname.strip()
                    ofile.write(progname + '\n')

                    # Get the viewing semester from obs-date
                    semester(header)
                    sem = header['SEMESTER'].strip()

                    # Get the program ID
                    seq = (sem, '_', progname)
                    ktn = ''.join(seq)

                    # Get the program information from the program ID
                    progpi,proginst, progtitl = get_prog_info(ktn)                   
                    if 'Usage' in progpi:
                        ofile.write('PROGPI\n')
                    else:
                        ofile.write(progpi+'\n')
                    if 'Usage' in proginst:
                        ofile.write('PROGINST\n')
                    else:
                        ofile.write(proginst+'\n')
                    if 'Usage' in progtitl:
                        ofile.write('PROGTITL\n')
                    else:
                        ofile.write(progtitl+'\n')
                ofile.write(oa + '\n')

#-------------------- END CREATEPROG--------------------------------------------------

def fixdatetime(utdate, fname, keys):
    utdate = utdate.replace('-','')
    utdate = utdate.replace('/','')

    seq = ('/home/koaadmin/fixdatetime/', utdate, '.txt')
    datefile = '' .join(seq)

    if os.path.isfile(datefile) is False:
        return

    fileroot = fname.split('/')
    fileroot = [-1]

    output = ''

    with open(datefile, 'r') as df:
        for line in df:
            if rootfile in line:
                output = line
                break
    if output != '':
        dateobs = keys.get('DATE-OBS')
        if 'Error' not in dateobs and dateobs.strip() != '':
            return
        vals = output.split(' ')
        keys.update({'DATE-OBS':(vals[1], ' Original value missing - added by KOA')})
        keys.update({'UTC':(vals[2], 'Original value missing - added by KOA')})

#---------------------------------- End fixdatetime ----------------------------

def semester(keys):
    try:
        dateobs = keys['DATE-OBS']
    except KeyError:
        try:
            dateobs = keys.get('DATE').strip()[0:10]
        except:
            dateobs = keys.get('DQA_DATE').strip()[0:10]
        keys.update({'DATE-OBS':(dateobs, 'Added missing DATE-OBS keyword')})
    if '-' not in dateobs:
        day, month, year = dateobs.split('/')
        if int(year)<50:
            year = '20' + year
        else:
            year = '19' + year
        dateval = year + '-' + month + '-' + day
        note = " DATE-OBS corrected (" + dateobs + ")"
        keys.update({'DATE-OBS':(dateval, note)})
    else:
        year, month, day = dateobs.split('-')
        iyear = int(year)
        imonth = int(month)
        iday = int(day)

    # Determine SEMESTER from DATE-OBS
    semester = ''
    sem = 'A'
    if imonth >8 or imonth < 2:
        sem = 'B'
    elif imonth == 8 and iday > 1:
        sem = 'B'
    elif imonth == 2 and iday == 1:
        sem = 'B'
    if imonth == 1 or (imonth == 2 and iday == 1):
        year = str(iyear-1)

    semester = ''.join((year, sem)).strip()
    keys.update({'SEMESTER':(semester, 'Calculated SEMESTER from DATE-OBS')})

#------------------ END SEMESTER ---------------------------------------------

def get_prog_info(ktn):
    """
    Retrives the program PI, allocating institution,
    and title from the proposals database web API

    @type ktn: string
    @param ktn: the program ID - consists of semester and progname (ie 2017B_U428)
    """
    url = 'http://www.keck.hawaii.edu/software/db_api/proposalsAPI.php?ktn='+ktn+'&cmd='
    progpi = urlopen(url+'getPI').read().decode('utf8')
    proginst = urlopen(url+'getAllocInst').read().decode('utf8')
    progtitl = urlopen(url+'getTitle').read().decode('utf8')
    return progpi, proginst, progtitl

#--------------- END GET PROG INFO-----------------------------------------

def add_metakeywords(instr, date, ifile, fkoaid, imagetyp, keys,
        image, iheader, nexten, obtfile, ancDir, log):
    """
    """
    log.info('Starting add_metakeywords')


    # Get koaid keyword
    fkoaid = koaid(keys)
    if instr not in ['HIRES','NIRC2','NIRSPEC']:
        keys.update('KOAID', (fkoaid, ' KOA data file name'))
        stageDir = ancDir.replace(instr, ''.join(('stage/',instr)))
        stageDir = stageDir.replace('/anc','')

        # Get ProgID, ProgPI, ProgInst
        req = ''.join(('https://www.keck.hawaii.edu/software/db_api/',
                'telSchedule.php?cmd=getSchedule&date=', date, '&instr=',
                instr, '&column=ProjCode,Principal,Institution'))
        res = url.urlopen(req).read().decode()
        dat = json.loads(res)

        keys['progid'] = (dat['ProjCode'], 'WMKO Program ID')
        keys['progpi'] = (dat['Principal'], 'Program Institution')
        keys['proginst'] = (dat['Institution'], 'Program Principal Investigator')

        # Get ProgTitl
        req = ''.join(('https://www.keck.hawaii.edu/software/db_api/',
                'koa.php?cmd=getTitle&semid=', progid))
        res = url.urlopen(req).read().decode()
        dat = json.loads(res)
        keys['progtitl '] = (dat['progtitl'], 'Program Title')

        # Find the observing semester
        log.info('add_metakeywords: semester')
        sem = semester(keys)
        keys['semester'] = (sem, 'WMKO Observing Scheudule Semester')

    log.info('add_metakeywords: datlevel')
    datlevel = data_level('raw')
    dqa_date(keys)
    dqa_vers(keys)

    # Instrument Specific Keyword Additions
    if instr == 'HIRES':
        # Wavelengths
        log.info('add_metakeywords: lambda_xd')
        filname = keys.get('FILNAME')
        wavecntr, waveblue, wavered = lambda_xd(nexten, keys)
    elif instr == 'NIRSPEC':
        # DETGAIN, MODE, & RN
        if 'NS' in fkoaid:
            detmode = 'spec'
            detgain = 5
            detrn = 10
        elif 'NC' in fkoaid:
            detmode = 'scam'
            detgain = 4
            detrn = 25
        else:
            detmode = 'null'
            detgain = 'null'
            detrn = 'null'

        # Dispersion
        log.info('add_metakeywords: nirspec_disp')
        dispersion, dispscal = nirspec_disp(keys)

        # Get differential tracking
        log.info('add_metakeywords: get_dtrack')
        dra, ddec, dtrack, update = get_dtrack(keys, ancDir)

        # Get image statistics
        log.info('add_metakeyworsd; nirspec_imagestat')
        imgmean, imgstdv, imgmed = nirspec_imagestat(keys, image, dispersion)

        # Server Crash?
        log.info('add_metakeywords: nirspec_crash')
        crash = nirspec_crash(keys, ifile)

def data_level(ftype):
    datalevel = None

    # Raw - level 0
    if ftype == 'raw':
        datalevel = 0
    elif ftype == 'reduced':
        datalevel = 1
    return datalevel

def dqa_date(keys):
    """
    Determines the date timestamp for when the DQA module was run
    """
    dqa_date = dt.now()
    keys['dqa_date'] = dt.strftime(dqa_date, '%Y-%m-%s %H:%M:%S')
    return

def dqa_vers(keys):
    path = '/kroot/archive/dep/dqa/default'
    keys['dqa_vers'] = (os.readlink(path), 'Live build version')
    return

def lambda_xd(nexten, keys):
    # Default to null
    waveblue = 'null'
    wavecntr = 'null'
    wavered = 'null'

    # Set pixel and CCD size
    psize = 0.015
    npix = 3072.0
    if nexten == 0:
        psize = 0.024
        npix = 1024.0

    # Make sure stages are homed
    try:
        xdispers = keys['XDISPERS'].strip()
    except KeyError:
        xdispers = 'RED'
    try:
        xdcal = keys['XDCAL'].strip()
        exhcal = keys['ECHCAL'].strip()
    except KeyError:
        return wavecntr, waveblue, wavered
    if xdcal == 0 or exhcal == 0:
        return wavecntr, waveblue, wavered

    # Determine XD groove spacing and HIRES angle setting
    try:
        xdsigmai = keys['XDSIGMAI']
        xdangl = keys['XDANGL']
        echangl = keys['ECHANGL']
    except KeyError:
        return wavecntr, waveblue, wavered

    # Specifications camera-collimator, blaze, cal offset angles
    camcol = 40.*math.pi/180.
    blaze = -4.38*math.pi/180.
    offset = 25.0 - 0.63        # 0-order + 5 deg for home

    # Grating Equation
    alpha = (xdangl+offset)*math.pi/180.
    d = 10**7/xdsigmai                    # microns
    wavecntr = d*((1.+math.cos(camcol))*math.sin(alpha)
            - math.sin(camcol)*math.cos(alpha))
    ccdangle = math.atan(npix*psize/1.92/762.0)    # f = 762mm, psize u pix, 1.92 amag

    # Blue end
    alphab = alpha - ccdangle
    waveblue = d*((1.+math.cos(camcol))*math.sin(alphab)
            - math.sin(camcol)*math.cos(alphab))

    # Red end
    alphar = alpha + ccdangle
    wavered =  d*((1.+math.cos(camcol))*math.sin(alphar)
            - math.sin(camcol)*math.cos(alphar))

    # Center
    wavecntr = int(wavecntr)
    waveblue = int(waveblue)
    wavered  = int(wavered)

    # Get the correct equation constants
    if xdispers == 'RED':
        # Order 62, 5748 A, order*wave= const
        const = 62.0 * 5748.0
        a = 1.4088
        b = -306.6910
        c = 16744.1946
        if nexten == 0:
            a = 1.1986
            b = -226.6224
            c = 10472.6948
    elif xdispers == 'UV':
        # Order 97, 3677 A, order*wave = const
        const = 97.0*3677.0
        a = 0.9496
        b = -266.2792
        c = 19943.7496
        if nexten == 0:
            a = 0.5020
            b = -148.3824
            c = 10743.1746
    elif xdispers == '':
        return wavecntr, waveblue, wavered

    # Correct wavelength values
    i = 1
    while i <= 3:
        if i == 1:
            wave = wavecenter
        elif i == 2:
            wave = waveblue
        elif i == 3:
            wave = wavered
        # Find order
        order = math.floor(const/wave)

        # Find shift in Y: order 62 = npix with XD=ECH=0 (RED)
        # Find shift in Y: order 97 = npix with XD=ECH=0 (BLUE)
        tryit = 1
        while nexten != 0 and tryit < 100:
            if i == 1:
                shift = a*order*order + b*order + c
                newy = npix - shift
                newy = -newy
            else:
                shift2 = a*order*order + b*order + c
                if nexten == 0:
                    if i == 1:
                        shift2 = shift2 + npix
                    elif i == 3:
                        shift2 = shift2 + 2*npix
                newy2 = shift2 - newy
                if newy2 < 120:
                    order = order - 1
                    tryit += 1
                    if nexten != 0 and tryit < 100:
                        continue
                npix2 = 2*npix
                if nexten == 0:
                    npix2 = npix2/2
                if newy2 > npix2:
                    order += 1
                    tryit += 1
                    if nexten != 0 and tryit < 100:
                        continue

        # Find delta wave for order
        dlamb = -0.1407*order + 18.005

        # New wavecntr = central wavelength for this order
        wave = const/order

        # Correct for echangl
        wave += (4 * dlamb * echangl)

        # round to nearest 10 angstroms
        wave2 = wave % 10
        if wave2 < 5:
            wave -= wave2
        else:
            wave += (10 - wave2)

        # cleanup
        if wave < 2000 or wave > 20000:
            wave = 'null'
        if i == 1:
            wavecntr =  wave
        elif i == 2:
            waveblue = wave
        elif i == 3:
            wavered = wave
        i += 1
    return wavecntr, waveblue, wavered

def nirspec_disp(keys):
    dispersion = 'null'
    dispscal = 'null'
    k_id = keys['KOAID']
    if'NC' not in k_id:
        return dispersion, dispscal
    dispersion = 'unknown'
    try:
        echelle = keys['ECHLPOS']
    except KeyError:
        dispersion = 'unknown'
        return dispersion, dispscal
    if echelle > 100:
        dispersion = 'low'
        dispscal = 0.190
    elif echelle <= 100:
        dispersion = 'high'
        dispscal = 0.144
    return disperion, dispscal

def get_dtrack(keys, ancDir):
    # If DTRACK exists in header, return
    update = 'no'
    dtrack = keys['DTRACK']
#    if dtrack not None:
#        return dra, ddec, dtrack, update
    update = 'yes'

    # Get RA, DEC, TARGETNAME
    ra = keys['RA']              # ra = 49.509
    dec = keys['DEC']            # dec = 7.466
    targname = keys['TARGNAME']  # targname = '2001PT13 05UT'

    # Default values
    dra    = 'null'
    ddec   = 'null'
    dtrack = 'null'

    # Read DCSlog
    if not targname or not ra or not dec or not ancDir:
        return dra, ddec, dtrack, update

    # Does dcsinfo file exist
    dcsfile = ''.join((ancDir, '/nightly/dcsinfo'))
    if not os.path.exists(dcsfile):
        return 'null', 'null', 'null', 'no'

    # Read the file
    savevals = {'targname':'', 'targra':'', 'targdec':'', 'dtrack':'', 'dra':'', 'ddec':''}
    with open(dcsfile, 'r') as dcslog:
        for line in dcslog:
            use = 'no'
            targname = targra = targdec = dtrack = dra= ddec = ''
            for val in savevals:
                if val in line:
                    tmp = line.split('=')
                    savevals[val] = tmp[1].strip()
                    use = 'yes'
            # If target found then...
            if use == 'yes' and targname == name:
                hr, mn, sc = targra.split(':')
                thisRA = (hr + mn/60.0 + sc/3600.0) * 1500
                dg, mn, sc = targdec.split(':')
                sign = 1
                if dg < 0:
                    deg = -deg
                    sign = -1
                thisDEC = dg + mn/60.0 + sc/3600.0
                thisDEC *= sign
                dra = abs(thisRA - ra)
                ddec = abs(thisDEC - dec)
                if dra < 0.01 and ddec < 0.01:
                    return dra, ddec, dtrack, update
    return dra, ddec, dtrack, update

def nirspec_imagestat(keys, image, dispersion):
    if not keys and not image and not dispersion:
        log.info('Syntax: nirspec_imagestat: header, image, dispersion')
        return 'null', 'null', 'null'

    # Defaults
    imgmean = 'null'
    imgstdv = 'null'
    imgmed  = 'null'

    # Determine image format
    naxis1 = keys['NAXIS1']
    naxis2 = keys['NAXIS2']
    x = naxis1/2
    y = naxis2/2

    # For low dispersion, spectrum is to the right of center
    # Make sure NOT scam
    try:
        outdir2 = keys['OUTDIR2']
    except KeyError:
        if dispersion == 'low':
            x = 715.0
    if outdir2:
        y -= 20

    # Sampling Box
    img = image[0][x-15:x+15,y-15:y+15]
    imgmean = numpy.mean(img)
    imgstdv = numpy.std(img)
    imgmed  = numpy.median(img)

    return imgmean, imgstdv, imgmed

def nirspec_crash(keys, ifile, log):
    # Add CRASH keyword, default is CRASH = No
    crash = 'No'
    keys['CRASH'] = ('No', 'NIRSPEC server crash detected?')

    # Crash if FILNAME is UNKNOWN
    filname = keys['FILNAME']
    slitname = keys['SLITNAME']
    if filname != 'UNKNOWN' and slitname != 'UNKNOWN':
        return 'No'

    # Crash detected
    crash = 'Yes'
    log.warning('nirspec_crash: Crash detected')
    keys['CRASH'] = 'Yes'

    # Get the file number and root name of this file
    try:
        filenum = keys['FILENUM']
    except KeyError:
        filenum = keys['FILENUM2']
    rootname = keys['ROOTNAME'].strip()

    # Starting with the previous file, loop through until
    # file is found that was written before the crash.
    filenum -= 1
    while filenum >= 0:
        # Construct the filename to previous file
        num2 = int(filenum.strip())
        if 100 <= num2 < 1000:
            num2 = ''.join(('0', string(num2)))
        if 10 <= num2 < 100:
            num2 = ''.join(('00', string(num2)))
        if num2 < 10:
            num2 = ''.join(('000', string(num2)))
        prefile = ''.join((rootname, num2.strip(), '.fits'))

        # Directory to look in
        rdir = ifile.split(rootname)[0]

        # Find the file
        for root, dirs, files in os.walk(rdir):
            prevfile = ''.join((root,files))

        # If file found, continue
        if prevfile == '':
            filenum -= 1
            continue

        # Read this header
        prevhead = fits.getheader(prevfile)

        # Good header if FILNAME not UNKNOWN
        filname = prevhead['FILNAME'].strip()
        slitname = prevhead['SLITNAME'].strip()
        if filname != 'UNKNOWN' and slitname != 'UNKNOWN':
            # loop through all the keywords and fix those
            # That are bogus
            for key in prevhead:
                if key != 'COMMENT':
                    comment = prevhead[key].split('/')

