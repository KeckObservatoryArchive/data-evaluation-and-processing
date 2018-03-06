import get_header
import importlib
import os
import logging as lg
import numpy as np
import getProgInfo as gpi
from glob import glob
from common import koaid
from datetime import datetime as dt
from astropy.io import fits
from urllib.request import urlopen
from imagetyp_instr import imagetyp_instr

#modules = ['nirspec', 'kcwi']

def dqa_run(instr, date, stageDir, lev0Dir, ancDir, tpxlog):
    """
    """
    # Set up default directories
    tablesDir = '/kroot/archive/tables'
    udfDir = ''.join((ancDir, '/udf/'))
    os.mkdir(udfDir)
    os.mkdir(lev0Dir)
    if instr == 'NIRSPEC':
        os.mkdir(lev0Dir + '/scam')
        os.mkdir(lev0Dir + '/spec')

    # Create the LOC file
    locFile = lev0Dir + '/dqa.LOC'

    # Create log file
    log = create_log()
    log.info(__name__ + ' ' + instr + ': DQA Started')

    udate = date
    createprog(instr, udate, stageDir, log)
    proginfo = gpi.ProgSplit()
    proginfo.getProgInfo()

    # Input file for dqa_run
    dqafile = ''.join((stageDir, '/dqa_', instr, '.txt'))

    # dep_obtain file
    obtfile = ''.join((stageDir, '/dep_obtain', instr, '.txt'))

    # Read the input file and store it in a something
    files = []
    with open(dqafile, 'r') as dqalist:
        for line in dqalist:
            files.append(line)

    # How many files will be processed?
    print(len(files))
    log.info(''.join((str(len(files)), ' files to be processed')))
    num_files = len(files)

    # Get the keys requires for the FITS files
    keysMeta = get_keys_meta(instr, tablesDir)
    num_keys = len(keysMeta)

    # Create containers to hold infile and outfile
    infile = []
    outfile = []

    # Store keyword values in the following arrays
    kname = []
    kvalue = []
    nkw = []

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
            log.info(''.join((instr, ': Input file ', filename)))
            infile.append(filename.strip())
            # Read the zero header
            with fits.open(filename) as hdulist:
                keys = hdulist[0].keys

                # Temp fix for bad file times (NIRSPEC legacy)
                fixdate = date
                fixdatetime(fixdate, filename, keys)

                # Is this a HIRES file?
                test = filename.split('/')
                goodfile = ''
                log.info(instr,': check_instr')
                check_instr(instr, filename, keys, udfDir, goodfile)
                if goodfile == 'no':
                    exit()
                # Number of Extensions: nexten = numccds * numamps
                log.info(instr, ': numamps')
                numAmps = numamps(keys)
                log.info(instr, ': numccds')
                numCCDs = numccds(keys)
                nexten = numAmps * numCCDs

                # Need Semester to Fix DATE-OBS, if not ERROR or 0
                if keys['DATE-OBS'] not in ['ERROR', 0]:
                    semester(keys)

                # Determine KOAID
                log.info(instr, ': koaid')
                koaid(keys)
                if keys['KOAID'] == 'bad':
                    log.warning(instr,
                            ': KOAID could not be created for ', filename)
                    exit()

                # Add mosaic keywords to legacy data, UT from UTC
                log.info(instr, ': add_keywords')
                add_keywords(instr, keys, nexten)
                skip = 'n'
                j = 0
                for j in range(key):
                    if keycheck[j] eq 'Y':
                        try:
                            test = keys[keycheck2[j]]
                        # If key does not exist, log it and skip
                        except KeyError:
                            log.warning(''.join((instr, ': ',
                                    keycheck2[j], ' keyword missing')))
                            exit()
            # Read the header and image data from the input file
            # Legacy data and NIRESPEC
            if nexten == 0:
                naxis1 = keys.get('NAXIS1')
                naxis2 = keys.get('NAXIS2')
                # Define image array
                if instr in ['DEIMOS','ESI','HIRES','LRIS']:
                    image = [1,int(naxis1),int(naxis2)]
                elif instr in ['NIRC2','NIRSPEC']:
                    image = [1,long(naxis1),long(naxis2)]
                elif instr in ['OSIRIS']:
                    image = [float(1),float(naxis1),float(naxis2)]
                # Read image
                data = hdulist[0].data

                # Write to log (HIRES)
                if instr == 'HIRES':
                    log.info(''.join((instr, ': Legacy data')))

                # Add BLANK (HIRES -32768), if missing
                try:
                    blank = keys['BLANK']
                except KeyError:
                    blank = -32768
                    text = ' Keyword added by KOA software'
                    keys.insert('BLANK'  , (blank, text))
                    log.info(''.join((instr, ': BLANK added to header')))
            else:
            #Mosaic Data
                ext = 0
                # Define header, nkeywords, size_image arrays
                header = []
                image=[]
                hdr = None
                nkeywords = []
                size_image = [0 for i in range(nexten+1)]
                while ext < nexten:
                    # Read extension header
                    try:
                        hdr = fits.getheader(filename, ext=ext+1)
                    except Exception as e:
                        log.error(''.join((instr, ': Error reading extension ', str(ext))))
                        exit()
                    try:
                        blank = hdr['BLANK']
                    except KeyError:
                        blank = -32768
                        text = ' Keyword added by KOA software'
                        hdr.insert('BLANK', (blank, text))
                        log.info(''.join((instr, ': BLANK added to image header for extension ', str(ext+1))))
                    # Determine the number of keywords
                    try:
                        # This gets rid of the extra whitespace for some reason
                        hdr.pop('')
                    except:
                        pass
                    nkeywords.append(len(hdr))

                    # Store extension header in array
                    header.append(hdr)

                    # Read image
                    try:
                        img = hdulist[ext+1].data
                    except Exception as e:
                        log.error(instr, ': Error reading image extension ', str(ext))
                        exit()
                    # Append the extension image to the list
                    image.append(img)

                    # Increment Extensions
                    ext += 1
                # End While loop
            # End else

            # First fix the BINNING keyword, if necessary
            try:
                binning = header['BINNING']
                bin2 = binning.replace(' ','')
                if binning not in bin2:
                    text = ''.join((' Keyword changed from '. binning))
                    keys.update('BINNING', (bin2, text))
            except:
                pass

            # Get current list of KOAIDs in lev0_dir
            koaid_found = []
            for root, dirs, files in os.walk(lev0Dir):
                for koaid in files:
                    if '.fits' not in koaid:
                        continue
                    elif koaid not in koaid_found:
                        koaid_found.append(''.join((root,'/',item)))
                    else:
                        log.warning(instr, ': KOAID ', koaid,
                                ' exists for ' + filename)
                        exit()

            # Call SEMESTER
            log.info(instr, ': semester')
            semester(keys)

            # Call IMAGETYP
            log.info(instr, ': imagetyp')
            imgtype = imagetyp_instr(instr, keys)
            if imgtype == 'object':
                num_sci += 1

            # Add DQA generated keywords
            log.info(instr, ': add_metakeywords')
            pi, sdata, datlevel, progid, progtitl, acct = add_metakeywords(
                    instr, date, filename, koaid, imtype, keys, image, header,
                    nexten, obtfile, ancDir)

    except KeyError:
        print('Invalid Key')
        log.error('Invalid Key')
    except Exception as err:
        print('Program Crashed - Exiting: ', str(err))
        log.error('Program Crashed - Exiting: ', str(err))

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

def create_log():
    # Setup logfile
    user = os.getlogin()
    log = lg.getLogger(user)
    log.setLevel(lg.INFO)
    fh = lg.FileHandler(__name__ + '.txt')
    fh.setLevel(lg.INFO)
    fmat = lg.Formatter('%(asctime)s - %(name)s - %(levelname)s: %(message)s')
    fh.setFormatter(fmat)
    log.addHandler(fh)
    return log

#----------------END CREATE LOG---------------------------------------

def get_keys_meta(instrument, tablesDir):
    # Get the critical keywords from from keyword.check
    if instrument in ['DEIMOS', 'ESI', 'LRIS', 'OSIRIS']:
        key_check = ''.join((tablesDir, '/keywordsMyKOA.check'))
    elif instrument == 'HIRES':
        key_check = ''.join((tablesDir, '/keywords.check'))
    elif instrument == 'NIRC2':
        key_check = ''.join((tablesDir, '/keywordsNirc2.check'))
    elif instrument == 'NIRSPEC':
        key_check = ''.join((tablesDir, '/NIRSPECkeywords.check'))
    elif instrument == 'NIRES':
        key_check = ''.join((tablesDir, '/keywords.format.NIRES'))

    # Get the key meta data from the check file
    keysMeta = []
    with open(key_check, 'r') as fitskeys:
        for line in fitskeys:
            keysMeta.append(line.split(' '))
    return keysMeta

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
        keys.update('KOAID', (koaid, ' KOA data file name'))
        stageDir = ancDir.replace(instr, ''.join(('stage/',instr)))
        stageDir = stageDir.replace('/anc','')

        # Get ProgID, ProgPI, ProgInst
        req = ''.join(('https://www.keck.hawaii.edu/software/db_api/',
                'telSchedule.php?cmd=getSchedule&date=', date, '&instr=',
                instr, '&column=ProjCode,Principal,Institution'))
        res = url.urlopen(req).read().decode()
        dat = json.loads(res)

        progid = dat['ProjCode']
        progpi = dat['Principal']
        proginst = dat['Institution']

        # Get ProgTitl
        req = ''.join(('https://www.keck.hawaii.edu/software/db_api/',
                'koa.php?cmd=getTitle&semid=', progid))
        res = url.urlopen(req).read().decode()
        dat = json.loads(res)
        progtitl = dat['progtitl']

        # progpi, proginst, progtitl = get_prog_info(progid)
