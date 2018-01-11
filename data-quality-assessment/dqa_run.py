import get_header
import importlib
import os
import logging as lg
import numpy as np
from glob import glob
from datetime import datetime as dt
from astropy.io import fits
from urllib import urlopen

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
    createprog(instr, udate, stageDir)
    
    
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
                ofile.write(newFile+'\n')
                ofile.write(udate+'\n')
                ofile.write(utc+'\n')
                ofile.write(outdir+'\n')
                ofile.write(observer+'\n')
                ofile.write(fileno+'\n')
                ofile.write(imagetyp+'\n')

                try:
                    progname = header['PROGNAME'].strip()
                except KeyError:
                    ofile.write('PROGNAME\n')
                    ofile.write('PROGPI\n')
                    ofile.write('PROGINST\n')
                    ofile.write('PROGTITL\n')
                else:
                    ofile.write(progname + '\n')
                    semester(header)
                    sem = header['SEMESTER'].strip()
                    seq = (sem, '_', progname)
                    ktn = ''.join(seq)
                    progpi,proginst, progtitl = get_prog_info(ktn)                   
                    if progpi == '':
                        ofile.write('PROGPI\n')
                    else:
                        ofile.write(progpi+'\n')
                    if proginst == '':
                        ofile.write('PROGINST\n')
                    else:
                        ofile.write(proginst+'\n')
                    if progtitl == '':
                        ofile.write('PROGTITL\n')
                    else:
                        ofile.write(progtitl+'\n')
                ofile.write(oa + '\n')

def imagetype_instr(instr, keys):
    """
    """
    imagetyp = 'undefined'
    imtype = ''
    if "KCWI" in instr:
        try:
            imtype = keys['IMTYPE']
        except KeyError:
            imtype = keys.get('CAMERA')
            if imtype != None and imtype.strip().upper() != 'FPC':
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
        inst = keys.get('INSTR').strip().lower()
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
        elif inst == 'imag':
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
            if ttime == 0:
                if bad == 'n':
                    imagetyp = 'bias'
                else: # bad == 'y':
                    imagetyp = 'bias_lamp_on'
            else: #  ttime != 0 
                if bad == 'n':
                    imagetyp = 'dark'
                else: # bad == 'y':
                    imagetyp = 'dark_lamp_on'
        elif autoshut == 1:
            try:
                deckname = keys['DECKNAME'].strip()
                catcur1 = keys['CATCUR1']
                catcur2 = keys['CATCUR2']
                hatclos = keys['HATCLOS']
            except KeyError:
                return
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
                elif deckname != 'D5':
                    imagetyp = 'flatlamp'
                elif lmirrin == 0:
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
    elif 'LRIS' in instr:
        try:
            instrume = keys['INSTRUME'].strip()
        except:
            return 'undefined'

        # Focus
        slitname = keys.get('SLITNAME').strip()
        outfile = keys.get('OUTFILE').strip()
        if slitname == 'GOH_LRIS' or outfile in ['rfoc', 'bfoc']:
            imagetyp = focus

        # Bias
        elaptime = keys.get('ELAPTIME').strip()
        if elaptime == 0:
            imagetyp = 'bias'

        # Flat, dark, wave, object
        try:
            trapdoor = keys['TRAPDOOR'].strip()
        except:
            return 'undefined'
        graname = keys.get('GRANAME').strip()
        grisname = keys.get('GRISNAME').strip()

        if trapdoor == 'open':
            flimagin = keys.get('FLIMAGIN').strip()
            flspectr = keys.get('FLSPECTR').strip()
            flat1 = keys.get('FLAMP1').strip()
            flat2 = keys.get('FLAMP2').strip()

            if 'on' in [flimagin, flspectr, flat1, flat2]:
                imagetyp = 'flatlamp'
            else:
                try:
                    autoshut = keys['AUTOSHUT']
                except KeyError:
                    return 'undefined'
                else:
                    calname = keys.get('CALNAME').strip()
                    if calname in ['ir', 'hnpb', 'uv']:
                        imagetyp = polcal
                    else:
                        imagetyp = obj
        elif trapdoor == 'closed':
            lamps = keys.get('LAMPS').strip()

            if lamps not in ['', '0']:
                if '1' in lamps:
                    if lamps == '0,0,0,0,0,1':
                        imagetyp = 'flatlamp'
                    else:
                        if instrume == 'LRIS':
                            if graname != 'mirror':
                                imagetyp = 'arclamp'
                        elif instrume == 'LRISBLUE':
                            if graname != 'clear':
                                imagetyp = 'aarclamp'
                else:
                    if lamps == '0,0,0,0,0,0':
                        imagetyp = dark
            else:
                mercury = keys.get('MERCURY').strip()
                neon = keys.get('NEON').strip()
                argon = keys.get('ARGON').strip()
                cadmium = keys.get('CADMIUM').strip()
                zinc = keys.get('ZINC').strip()
                halogen = keys.get('HALOGEN').strip()
                krypton = keys.get('KRYPTON').strip()
                xenon = keys.get('XENON').strip()
                feargon = keys.get('FEARGON').strip()
                deuteri = keys.get('DEUTERI').strip()

                if halogen == 'on':
                    imagetyp = 'flatlamp'
                elif 'on' in [neon, argon, cadmium, zinc, krypton, xenon, feargon, deuteri]:
                    if instrume == 'LRIS':
                        if graname != 'mirror':
                            imagetyp = arclamp
                    elif instrume == 'LRISBLUE':
                        if graname != 'clear':
                            imagetyp = 'arclamp'
                elif neon == argon == cadmium == zinc == krypton == xenon == feargon == deuteri == 'off':
                    imagetyp = 'dark'
    elif 'MOSFIRE' in instr:
        # Defaults
        el = keys.get('EL')
        domestat = keys.get('DOMESTAT').strip()
        axestat = keys.get('AXESTAT').strip()

        # Dust Cover
        mdcmech = keys.get('MDCMECH').strip()
        mdcstat = keys.get('MDCSTAT').strip()
        mdcname = keys.get('MDCNAME').strip()
        dustcov = ''
        if mdcmech == 'Dust Cover' and mdcstat == 'OK':
            if mdcname == 'Open':
                dustcov = 'open'
            elif mdcname == 'Closed':
                dustcov = 'closed'

        # Dome Lamps
        try:
            flatspec = keys['FLATSPEC'].strip()
        except KeyError:
            flatspec = ''
        try: 
            flimagin = keys['FLIMAGIN'].strip()
        except KeyError:
            flimagin = ''
        try:
            flspectr = keys['FLSPECTR'].strip()
        except KeyError:
            flspectr = ''

        # Arc Lamps
        try:
            pwstata7 = keys['PWSTATA7'].strip()
        except KeyError:
            pwstata7 = ''
        try:
            pwstata8 = keys['PWSTATA8'].strip()
        except KeyError:
            pwstata8 = ''

        # Obs_mode
        obsmode = keys.get('OBSMODE').strip()

        # Mask name
        maskname = keys.get('MASKNAME').strip()

        # Dark
        if 'Dark' in obsmode and pwstata7 == pwstata8 == 0:
            imagetyp = 'dark'

        if dustcov == 'closed':
            # Arclamp
            if 'spectroscopy' in obsmode and 1 in [pwstata7, pwstata8]:
                imagetyp = 'arclamp'
        elif dustcov == 'open':
            # Object
            imagetyp = 'object'

            # Flatlamp
            if flatspec == 1 or 'on' in [flimagin, flspectr]:
                imagetyp = 'flatlamp'
            else:
                if 44.99 <= el <= 45.01 and 'tracking' not in [domestat, axestat]:
                    imagetyp = 'flatlamp'
        # For when no flatlamp keywords
        if imagetyp == 'undefined':
            if 44.99 <= el <= 45.01 and 'tracking' not in [domestat, axestat]:
                img = fits.open(filename)[0].data
                img_mean = np.mean(img)
                if img_mean > 500:
                    imagetyp = 'flatlamp'
                else:
                    imagetyp = 'flatlampoff'
    elif 'NIRSPEC' in instr:
        # Check calibration
        try:
            calmpos = keys['CALMPOS']
            calppos = keys['CALPPOS']
            calcpos = keys['CALCPOS']
        except KeyError:
            return

        # Arc
        xenon = keys.get('XENON')
        krypton = keys.get('KRYPTON')
        argon = keys.get('ARGON')
        neon = keys.get('NEON')
        if 1 in [argon. krypton, neon, xenon]:
            if calmpos == 1 and calppos == 0:
                imagetyp = 'arclamp'
            else:
                imagetyp = 'undefined'
            return imagetyp

        # Flat
        flat = keys.get('FLAT')
        if flat == 0 and calmpos == 1:
            imagetyp = 'flatlampoff'
        elif flat == 1:
            if calmpos == 1 and calppos == 0:
                imagetyp = 'flatlamp'
            else:
                imagetyp = 'undefined'
            return imagetyp
        
        # Dark
        filname = keys.get('FILNAME').strip()
        if filname == 'BLANK':
            imagetyp = dark
            try:
                itime = keys['ITIME']
            except KeyError:
                itime = keys.get('ITIME2')
            if itime == 0: 
                imagetyp = 'bias'
            return

        # If cal mirror, pinhole, and cover are out, then 'object'
        if calmpos == calppos == calcpos == 0:
            imagetyp = 'object'
    elif 'NIRC2' in instr:
        grsname = keys.get('GRSNAME').strip()
        shrname = keys.get('SHRNAME').strip()
        obsfname = keys.get('OBSFNAME').strip()
        domestat = keys.get('DOMESTAT').strip()
        axestat = keys.get('AXESTAT').strip()

        # Shutter open
        if shrname == 'open':
            if obsfname == 'telescope':
                if domestat != 'tracking' and axestat != 'tracking':
                    if grsname != 'clear':
                        imagetyp = 'telTBD'
                        return
                    flimagin = keys.get('FLIMAGIN').strip()

                    # if domelamps keyword exists
                    try:
                        flspectr = keys['FLSPECTR'].strip()
                    except KeyError:
                        el = float(keys.get('EL'))
                        if 44.99 <  el < 45.01:
                            imagetyp = 'flatTBD'
                    else:
                        flspectr = keys.get('FLSPECTR')
                        if 'on' in [flimagin, flspectr]:
                            imagetyp = 'flatlamp'
                        else:
                            imagetyp = 'flatlampoff'        
                else:
                    imagetyp = 'object'
            elif obsfname == 'telsim':
                try:
                    argonpwr = keys.get('ARGONPWR')
                    xenonpwr = keys.get('XENONPWR')
                    kryptpwr = keys.get('KRYPTPWR')
                    neonpwr = keys.get('NEONPWR')
                    lamppwr = keys.get('LAMPPWR')
                except KeyError:
                    if grsname in ['lowres', 'medres', 'GRS1', 'GRS2']:
                        imagetyp = 'specTBD'
                else:
                    # Special processing for lamppwr valid after 2011-10-10
                    dateObs = keys.get('DATE-OBS').strip()
                    date = dateObs.replace('-','')
                    dateVal = long(date)
                    goodDate = long(20111010)

                    if dateVal >= goodDate):
                        if lamppwr == 1:
                            imagetyp = 'flatlamp'
                        elif 1 in[argonpwr, xenonpwr, kryptpwr, neonpwr]:
                            imagetyp = 'arclamp'
                    else:
                        imagetyp = 'specTBD'
        # Dark or Bias
        elif shrname == 'closed':
            itime = keys.get('ITIME')
            if itime == 0:
                imagetyp = 'bias'
            else:
                imagetyp = 'dark'
    return imagetyp

def fixdatetime(utdate, fname, keys):
    utdate = utdate.replace('-','')
    utdate = utdate.replace('/','')

    seq = ('/home/koaadmin/fixdatetime/', utdate, '.txt')
    datefile = '' .join(seq)

    if os.path.isfile(fname) is False:
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
        keys.update('DATE-OBS', vals[1], ' Original value missing - added by KOA')
        keys.update('UTC', vals[2], 'Original value missing - added by KOA')

#---------------------------------- End fixdatetime ----------------------------

def semester(keys):
    try:
        dateobs = keys['DATE-OBS']
    except KeyError:
        dateobs = keys.get('DATE').strip()[0:10]
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
    url = 'http://www.keck.hawaii.edu/software/db_api/proposalsAPI.php?ktn='+ktn+'&cmd='
    progpi = request.urlopen(url+'getPI').read().decode('utf8')
    proginst = urlopen(url+'getAllocInst').read().decode('utf8')
    progtitl = urlopen(url+'getTitle').read().decode('utf8')
    return progpi, proginst, progtitl

#--------------- END GET PROG INFO-----------------------------------------
