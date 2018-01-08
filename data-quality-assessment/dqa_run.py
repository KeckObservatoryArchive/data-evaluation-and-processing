import get_header
import importlib
import os
import logging as lg
from glob import glob
from datetime import datetime as dt

modules = ['nirspec', 'kcwi']

def dqa_run(instr, date, stageDir, lev0Dir, ancDir, tpxlog)
    
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
    fh.setLevel(lg.INFO
    fmat = lg.Formatter('%(asctime)s - %(name)s - %(levelname)s: %(message)s')
    fh.setFormatter(fmat)
    log.addHandler(fh)
    
    log.info(__name__ + ' ' + instr + ': DQA Started')
    
    udate = date
    
    
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
    
    dep_obtain = stageDir + '/dep_obtain' + instr + '.txt')
 
    oa = []
    fileList = []

    # Get OA
    with open(dep_obtain, 'r') as dob:
        for line in dob:
            items = line.split(' ')
            if len(items)>1:
                oa.append(items[0])
            else:
                oa.append(items)
    
    # Get all files
    for root, dirs, files in os.walk(stageDir):
        for item in files:
            if '.fits' in item:
                seq = (root, item)
                fileName = ''.join(seq)
                fileList.append(fileName)

    seq = (stageDir, '/dqa_', instr, '.txt')
    dqa_instr = ''.join(seq)
    with open(dqa_instr, 'r') as dqa:
        for item in dqa:
            fileList.append(item)

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

                # need to fix this somehow
                fixdate = utdate
                fixdatetime, fixdate, item, header = header
                imagetyp_instr, instr, header, imagetyp=imagetyp
                try:
                    udate = header['DATE-OBS'].strip()
                except KeyError:
                    log.warning('Bad header file')
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
                try:
                    observer = header['OBSERVER'].strip()
                except KeyError:
                    pass
                try:
                    fileno = header['FILENUM'].strip()
                except KeyError:
                    try:
                        fileno = header['FILENUM2'].strip()
                    except KeyError:
                        try:
                            fileno = header['FRAMENO'].strip()
                        except KeyError:
                            try:
                                fileno = header['IMGNUM'].strip()
                            except KeyError:
                                pass
                try:
                    outdir = header['OUTDIR']
                except KeyError:
                    try:
                        outdir = header['OUTDIR2']
                    except KeyError:
                        pass
                newFile = item.split('/sdata')
                if len(newFile) > 1:
                    newFile = '/sdata' + newFile[-1]
                newFile = newFile.replace('//','/')
                ofile.write(file, udate, utc, outdir, observer, fileno, imagetyp)

                try:
                    progname = header['PROGNAME'].strip()
                except KeyError:
                    ofile.write('PROGNAME\n')
                    ofile.write('PROGPI\n')
                    ofile.write('PROGINST\n')
                    ofile.write('PROGTITL\n')
                else:
                    ofile.write(progname + '\n')
                    try:
                        semester = header['SEMESTER']
                    except KeyError:
                        pass

def imagetype_instr(self, keys):
    """
    """
    instr = keys.get('INSTR')
    imgtype = ''
    if "KCWI" in instr:
        try:
            imgtype = keys['IMTYPE']
        except KeyError:
            imgtype = keys.get('CAMERA')
            if imgtype != None and imgtype.strip().upper() != 'FPC':
                imgtype = ''
        else:
            imgtype = ''

    elif "OSIRIS" in instr:
        imgtype = keys.get('')
    else:
        # do something

    imgtype = imgtype.strip()
    imgtype = imgtype.lower()

    return imgtype

def fixdatetime(self, keys):
    datestuff = ''

    return datestuff
