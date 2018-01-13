import get_header
import importlib
import os
import logging as lg
import numpy as np
from glob import glob
from datetime import datetime as dt
from astropy.io import fits
from urllib.request import urlopen
from imagetyp_instr import imagetyp_instr

modules = ['nirspec', 'kcwi']

def dqa_run(instr, date, stageDir, lev0Dir, ancDir, tpxlog):
    
    # Set up default directories
    tablesDir = '/kroot/archive/tables'
    udfDir = ancDir + '/udf/'
    os.mkdir(udfDir)
    os.mkdir(lev0Dir)
    if instr == 'NIRSPEC':
        os.mkdir(lev0Dir + '/scam')
        os.mkdir(lev0Dir + '/spec')
    
    # Create the LOC file
    locFile = lev0Dir + '/dqa.LOC'
    
    # Setup logfile
    user = os.getlogin()
    log = lg.getLogger(user)
    log.setLevel(lg.INFO)
    fh = lg.FileHandler(__name__ + '.txt')
    fh.setLevel(lg.INFO)
    fmat = lg.Formatter('%(asctime)s - %(name)s - %(levelname)s: %(message)s')
    fh.setFormatter(fmat)
    log.addHandler(fh)
    
    log.info(__name__ + ' ' + instr + ': DQA Started')
    
    udate = date
    createprog(instr, udate, stageDir, log)

    
    
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

    seq = (year, sem)
    semester = ''.join(seq).strip()
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
