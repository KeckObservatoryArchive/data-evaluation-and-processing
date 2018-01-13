def imagetyp_instr(instrument, keys):
    """
    """
    imagetyp = 'undefined'
    imtype = ''
    if "KCWI" in instrument:
        try:
            imtype = keys['IMTYPE']
        except KeyError:
            imtype = keys.get('CAMERA')
            if imtype != None and imtype.strip().upper() != 'FPC':
                imtype = ''
        imagetyp = imtype.strip().lower()
        if imagetyp == '':
            imagetyp = 'undefined'
    elif "OSIRIS" in instrument:
        ifilter = keys.get('IFILTER').strip().lower() if keys.get('IFILTER') != None else ''
        sfilter = keys.get('SFILTER').strip().lower() if keys.get('SFILTER') != None else ''
        axestat = keys.get('AXESTAT').strip().lower() if keys.get('AXESTAT') != None else ''
        domeposn = keys.get('DOMEPOSN')
        az = keys.get('AZ')
        obsfname = keys.get('OBSFNAME').strip().lower() if keys.get('OBSFNAME') != None else ''
        obsfx = float(keys.get('OBSFX'))
        obsfy = float(keys.get('OBSFY'))
        obsfz = float(keys.get('OBSFZ'))
        instr = keys.get('INSTR').strip().lower() if keys.get('INSTR') != None else ''
        el = keys.get('EL')
        datafile = keys.get('DATAFILE').strip().lower() if keys.get('DATAFILE') != None else ''
        coadds = keys.get('COADDS')

        if 'telescope' in obsfname:
            imagetyp = 'object'
        elif datafile[8] == 'c':
            imagetyp = 'calib'
        
        # If ifilter or sfilter is 'dark' we have a dark
        elif ifilter == 'drk' and datafile[0] == 'i':
            imagetyp = 'dark'
        elif sfilter == 'drk' and datafile[0] == 's':
            imagetyp = 'dark'
        # If instr='imag' uses dome lamps
        elif instr == 'imag':
            if (obsfname == 'telescope' and axestat == 'not controlling' 
                    and el < 45.11 and el < 44.89 
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
        elif len(datafile) > 8 and datafile[8] == 'a':
            if obsfname == 'telsim' or (abs(obsfx) > 30 and abs(obsfy) < 0.1 and abs(obsfz) < 0.1):
                imagetyp = 'undefined'
            elif obsfz > 10:
                imagetyp = 'undefined'
        elif len(datafile) > 8 and datafile[8] == 'c':
            imagetyp = 'calib'
    elif 'ESI' in instrument:
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
        el = keys.get('EL')
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
                (slmsk, hatchpos, [44.00<=el<=46.01, domestat=='not tracking', axestat=='not tracking',
                        obstype=='dmflat'].count(True)>=3),
                (slmsk, hatchpos, prismnam, imfltnam, 
                        [44.00<=el<=46.01, domestat=='not tracking', axestat=='not tracking',
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
                if configs.get(item) != None:
                    imagetyp = configs.get(item)
    elif 'DEIMOS' in instrument:
        obstype = keys.get('OBSTYPE').strip().lower() if keys.get('OBSTYPE') != None else ''
        slmsknam = keys.get('SLMSKNAM').strip().lower() if keys.get('SLMSKNAM') != None else ''
        hatchpos = keys.get('HATCHPOS').strip().lower() if keys.get('HATCHPOS') != None else ''
        flimagin = keys.get('FLIMGNAM').strip().lower() if keys.get('FLIMGNAM') != None else ''
        flspectr = keys.get('FLSPECTR').strip().lower() if keys.get('FLSPECTR') != None else ''
        lamps = keys.get('LAMPS').strip().lower() if keys.get('LAMPS') != None else ''
        gratepos = keys.get('GRATEPOS')

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

    elif 'HIRES' in instrument:
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
    elif 'LRIS' in instrument:
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
        elaptime = keys.get('ELAPTIME')
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
                    calname = keys.get('CALNAME').strip() if keys.get('CALNAME') != None else ''
                    if calname in ['ir', 'hnpb', 'uv']:
                        imagetyp = polcal
                    else:
                        imagetyp = 'object'
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
    elif 'MOSFIRE' in instrument:
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
            flatspec = keys['FLATSPEC']
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
            pwstata7 = keys['PWSTATA7']
        except KeyError:
            pwstata7 = ''
        try:
            pwstata8 = keys['PWSTATA8']
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
    elif 'NIRSPEC' in instrument:
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
        if 1 in [argon, krypton, neon, xenon]:
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
    elif 'NIRC2' in instrument:
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

                    if dateVal >= goodDate:
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
