import get_header
import importlib
import os
import logging as lg
import numpy as np
from glob import glob
from datetime import datetime as dt
from astropy.io import fits

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
    imagetyp = 'undefined'
    imtype = ''
    if "KCWI" in instr:
        try:
            imtype = keys['IMTYPE']
        except KeyError:
            imtype = keys.get('CAMERA')
            if imtype != None and imtype.strip().upper() != 'FPC':
                imtype = ''
        else:
            imtype = ''
        imagetyp = imtype.strip().lower()
        if imagetyp = '':
            imagetyp = 'undefined'
    elif "OSIRIS" in instr:
        ifilter = keys.get('IFILTER').strip().lower()
        sfilter = keys.get('SFILTER').strip().lower()
        axestat = keys.get('AXESTAT').strip().lower()
        domeposn = keys.get('DOMEPOSN').strip().lower()
        az = keys.get('AZ').strip().lower()
        obsfname = keys.get('OBSFNAME').strip().lower()
        obsfx = keys.get('OBSFX').strip().lower()
        obsfy = keys.get('OBSFY').strip().lower()
        obsfz = keys.get('OBSFZ').strip().lower()
        instr = keys.get('INSTR').strip().lower()
        el = keys.get('EL').strip().lower()
        datafile = keys.get('DATAFILE').strip().lower()
        coadds = keys.get('COADDS').strip().lower()

        if 'telescope' in obsfname:
            imagetyp = 'object'
        if datafile[8] == 'c':
            imagetyp = 'calib'
        
        # If ifilter or sfilter is 'dark' we have a dark
        if ifilter == 'drk' and datafile[0] == 'i':
            imagetyp = 'dark'
        elif sfilter == 'drk' and datafile[0] == 's':
            imagetyp = 'dark'
        # If instr='imag' uses dome lamps
        elif instr == 'imag':
            if (obsfname == 'telescope' and axestat == 'not controlling' 
                    and el < 45.11 and el gt 44.89 
                    and abs(float(domeposn)-float(az)) > 80 
                    and abs(float(domeposn)-float(az)) < 100):
                image1 = fits.open(infile)
                img = image1[0].data
                imgdv = img/float(coadds)
                imgmed = np.median(imgdv)
                if imgmed > 30:
                    imagetyp = 'flatlamp'
                else:
                    imagetyp = 'flatlampoff'
        # If instr == 'spec' use internal source
        if datafile[8] == 'a':
            if obsfname == 'telsim' or (obsfx > 30 and abs(obsfy) < 0.1 and abs(obsfz) < 0.1):
                imagetyp = 'undefined'
            elif obsfz > 10:
                imagetyp = 'undefined'
        elif datafile[8] = 'c':
            imagetyp = 'calib'
    elif 'ESI' in instr:
        obstype = keys.get('OBSTYPE').strip().lower()
        hatchpos = keys.get('HATCHPOS').strip().lower()
        lampqtz1 = keys.get('LAMPQTZ1').strip().lower()
        lampar1 = keys.get('LAMPAR1').strip().lower()
        lampcu1 = keys.get('LAMPCU1').strip().lower()
        lampne1 = keys.get('LAMPNE1').strip().lower()
        lampne2 = keys.get('LAMPNE2').strip().lower()
        imfltnam = keys.get('IMFLTNAM').strip().lower()
        ldfltnam = keys.get('LDFLTNAM').strip().lower()
        prismnam = keys.get('PRISMNAM').strip().lower()
        el = keys.get('EL').strip().lower()
        domestat = keys.get('DOMESTAT').strip().lower()
        axestat = keys.get('AXESTAT').strip().lower()
        slmsknam = keys.get('SLMSKNAM').strip().lower()
        apmsknam = keys.get('APMSKNAM').strip().lower()
        dwfilnam = keys.get('DWFILNAM').strip().lower()
        imfltnam = keys.get('IMFLTNAM').strip().lower()

        configs = { # all configs start with 'hole' in slmsknam
                # hatchpos, lampqtz1, lampar1, lampcu1, lampne1, lampne2
                (False, 'closed', 'on', 'off', 'off', 'off', 'off'):'flatlamp',
                # hatchpos, lampqtz1, lampar1, lampcu1, lampne1, lampne2, prismnam, imfltnam
                (True, 'closed', 'on', 'off', 'off', 'off', 'off', 'in', 'out'):'trace',
                # hatchpos, lampqtz1, lampar1, lampcu1, lampne1, lampne2
                (True, 'closed', 'on', 'off', 'off', 'off', 'off'):'focus',
                # hatchpos, lampqtz1, (lampar1 or lampcu1 or lampne1 or lampne2) is on, imfltnam, prismnam
                (False, 'closed', 'off', True, 'out', 'in'):'arclamp',
                # hatchpos, lampqtz1, (lampar1 or lampcu1 or lampne1 or lampne2) is on, imfltnam, prismnam
                (True, 'closed', 'off', True, 'out', 'in'):'focus',
                # hatchpos, [44.00<=el<=46.01, domestat == 'not tracking', 
                #            axestat == 'not tracking', obstype == 'dmflat'].count(True) > 3
                (False, 'open', True):'flatlamp',
                # hatchpos, prismnam, imfltnam, [44.00<=el<=46.01, domestat == 'not tracking', axestat == 'not tracking', 
                #                                obstype == 'dmflat'].count > 3
                (True, 'open', 'in', 'out', True):'trace',
                # hatchpos, prismnam, imfltnam, [44.00<=el<=46.01, domestat == 'not tracking', axestat == 'not tracking', 
                #                                obstype == 'dmflat'].count > 3
                (True, 'open', 'out', 'in', True):'focus',
                # imfltname, ldfltnam, prismnam
                (True, 'in', 'out', 'out'):'focus',
                # apmasknam, dwfilnam, imfltnam, prismnam
                (True, 'decker', 'clear_s', 'out', 'in'):'focus',
                # hatchpos, lampqtz1, lampar1, lampcu1, lampne1, lampne2
                (False, 'open', 'off', 'off', 'off', 'off', 'off'):'object' 
                }

        slmsk = 'hole' in slmsknam
        instConfig = [(slmsk, hatchpos, lampqtz1, lampar1, lampcu1, lampne1, lampne2),
                (slmsk, hatchpos, lampqtz1, lampar1, lampcu1, lampne1, lampne2, prismnam, imfltnam),
                (slmsk, hatchpos,'on' in [lampar1, lampcu1, lampne1, lampne2], imfltnam, prismnam),
                (slmsk, hatchpos, [44.00<=el<=46.01, domestat=='not tracking', axestat=='not tracking'
                        obstype=='dmflat'].count(True)>=3),
                (slmsk, hatchpos, prismnam, imfltnam, 
                        [44.00<=el<=46.01, domestat=='not tracking', axestat=='not tracking'
                        obstype=='dmflat'].count(True)>=3),
                (slmsk, imfltnam, ldfltnam, prismnam),
                (slmsk, apmsknam, dwfilnam, imfltnam, prismnam)
                ]

        # If obstype is 'bias' we have a bias
        if obstype == 'bias':
            imagetyp = 'bias'
        # If obsmode is 'dark' we have a dark
        elif obstype == 'dark':
            imagetyp = 'dark'
        # Otherwise use the list of configs to figure out the imagetyp
        else:
            for item in instConfig:
                if configs.get(item) not None:
                    imagetyp = configs.get(item)
    elif 'DEIMOS' in instr:
        obstype = keys.get('OBSTYPE').strip().lower()
        slmsknam = keys.get('SLMSKNAM').strip().lower()
        hatchpos = keys.get('HATCHPOS').strip().lower()
        flimagin = keys.get('FLIMGNAM').strip().lower()
        flspectr = keys.get('FLSPECTR').strip().lower()
        lamps = keys.get('LAMPS').strip().lower()
        gratepos = keys.get('GRATEPOS').strip().lower()

        # If obstype == 'bias' we have a bias
        if obstype == 'bias':
            imagetyp = 'bias'
        # If obstype == 'dark' we have a dark
        elif obstype == 'dark':
            imagetyp = 'dark'
        # If slmsknam contains goh we have a focus image
        elif 'goh' in slmsknam:
            imagetyp = 'focus'
        # If hatchpos is 'closed' and lamps are quartz we have a flat
        elif hatchpos == 'closed' and lamps == 'qz':
            imagetyp = 'flatlamp'
        elif hatchpos == 'open' and 'on' in [flimagin, flspectr]:
            imagetp = 'flatlamp'
        elif (hatchpos == 'closed' and lamps not in['off', 'qz'] 
                and gratepos in ['3','4']):
            imagetyp = 'arclamp'
        elif hatchpos == 'open':
            imagetyp = 'object'

        # Check if this is an FCS calibration
        outdir = keys.get('OUTDIR')
        if 'fcs' in outdir:
            imagetyp = 'fcscal'

    elif 'HIRES' in instr:
        autoshut = keys.get('AUTOSHUT')
        lampname = keys.get('LAMPNAME').strip()
        lmirrin = keys.get('LMIRRIN')
        darkclos = keys.get('DARKCLOS')
        ttime = keys.get('ELAPTIME')

        if autoshut == 0:
            bad = 'n'

            if lampname == 'none' and (lmirrin!=0 or darkclos != 1):
                bad = 'y'
            if ttime == 0 and bad == 'n':
                imagetyp = 'bias'
            elif ttime == 0 and bad == 'y':
                imagetyp = 'bias_lamp_on'
            elif ttime != 0 and bad == 'n':
                imagetyp = 'dark'
            elif ttime != 0 and bad == 'y':
                imagetyp = 'dark_lamp_on'
            return
        elif autoshut == 1:
            deckname = keys.get('DECKNAME').strip()
            catcur1 = keys.get('CATCUR1')
            catcur2 = keys.get('CATCUR2')
            hatclos = keys.get('HATCLOS')
            xcovclos = keys.get('XCOVCLOS')
            ecovclos = keys.get('ECOVCLOS')

            if lampname == 'none':
                if ttime == 0:
                    imagetyp = 'bias'
                elif hatclos == 1:
                    imagetyp = 'dark'
                else:
                    imagetyp = 'object'


            elif lampname in ['quartz' ,'quartz1', 'quartz2']:
                if deckname == 'D5':
                    imagetyp == 'trace'
                else: # deckname != 'D5'
                    imagetyp = 'flatlamp'
                if lmirrin == 0:
                    if hatclos == 0:
                        imagetyp = 'object_lamp_on'
                    elif hatclos == 1:
                        imagetyp = 'undefined'
            elif lampname in ['ThAr1', 'ThAr2']:
                if catcur1 >= 5.0:
                    if deckname == 'D5':
                        imagetyp = 'focus'
                    else:
                        imagetyp = 'arclamp'
                elif carcur1 < 5.0:
                    imagetyp = 'undefined'
                elif lmirrin == 0:
                    if hatclos == 0:
                        imagetyp = 'object_lamp_on'
                    elif hatclos == 1:
                        imagetyp = 'undefined'
                elif xcovclos == 1 and ecovclos == 1:
                    imagetyp = 'undefined'
            elif lampname == 'undefined':
                imagetyp = 'undefined'
    
    else:
        # do something

    imgtype = imgtype.strip()
    imgtype = imgtype.lower()

    return imgtype

def fixdatetime(self, keys):
    datestuff = ''

    return datestuff
