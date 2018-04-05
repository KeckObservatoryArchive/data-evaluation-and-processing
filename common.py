from datetime import datetime

def set_directory(typeDir, rootDir, instr, utDate):
    """
    Returns the specified directory

    @param typeDir: type of directory to create
    @type typeDir: string
    @param rootDir: root directory for data processing
    @type rootDir: string
    @param instr: instrument name
    @type instr: string
    @param utDate: UT date (yyyy-mm-dd)
    @type utDate: string
    """

    instr = instr.upper()
    utDate = utDate.replace('-', '')
    utDate = utDate.replace('/', '')

    dir = {}
    processDir = ''.join((rootDir, '/', instr))
    dir['processDir'] = processDir
    dir['stageDir'] = ''.join((rootDir, '/stage/', instr, '/', utDate))
    processDir = ''.join((processDir, '/', utDate))
    dir['lev0Dir'] = ''.join((processDir, '/lev0'))
    dir['lev1Dir'] = ''.join((processDir, '/lev1'))
    dir['ancDir'] = ''.join((processDir, '/anc'))

    if typeDir in dir:
        return dir[typeDir]
    else:
        return 'None'

def semester(keywords, utDate):
        """
        Determines the Keck observing semester for the supplied UT date

        semester('2017-08-01') --> 2017A
        semester('2017-08-02') --> 2017B

        A = Feb. 2 to Aug. 1 (UT)
        B = Aug. 2 to Feb. 1 (UT)
        """

        utDate = utDate.replace('-', '')
        utDate = utDate.replace('/', '')

        try:
                utDate = datetime.strptime(utDate, '%Y%m%d')
        except ValueError:
                raise ValueError("Incorrect date format, should be YYYYMMDD")

        year = utDate.year
        month = utDate.month
        day = utDate.day

        # All of January and February 1 are semester B of previous year
        if month == 1 or (month == 2 and day == 1):
                semester = 'B'
                year -= 1
        # August 2 onward is semester B
        elif month >= 9 or (month == 8 and day >= 2):
                semester = 'B'
        else:
                semester = 'A'

        keywords['SEMESTER'] = semester

def koaid(keywords, utDate):
        '''
        Determines the KOAID

        KOAID = II.YYYYMMDD.######.fits
           - II = instrument prefix
           - YYYYMMDD = UT date of observation
           - ###### = number of seconds into UT date
         '''

        # Get UTC or default to DATE
        try:
                utc = keywords['UTC']
        except:
                try:
                        utc = keywords['UT']
                except:
                        utc = keywords['DATE'].split('T')
                        if len(utc) == 2:
                                utc = utc[1] + '.0'
                        else:
                                return False

        # Get DATE-OBS or default to DATE
        try:
                dateobs = keywords['DATE-OBS']
        except:
                dateobs = keywords['DATE'].split('T')
                if len(dateobs) == 2:
                        dateobs = dateobs[0]
                else:
                        return False

        try:
                utc = datetime.strptime(utc, '%H:%M:%S.%f')
        except ValueError:
                raise ValueError

        hour = utc.hour
        minute = utc.minute
        second = utc.second

        totalSeconds = str((hour * 3600) + (minute * 60) + second)

        instr_prefix = {'esi':'EI', 'hires':'HI', 'lris':'LR', 'lrisblue':'LB', 'mosfire':'MF', 'nirc2':'N2'}

        try:
            instr = keywords['INSTRUME'].lower()
        except KeyError:
            return False
        instr = instr.split(' ')
        instr = instr[0].replace(':', '')
        outdir = ''
        try:
            outdir = keywords['OUTDIR']
        except KeyError:
            if instr == 'nires':
                outdir = ''

        if '/fcs' in outdir:
            instr = 'deimos'

        if instr in instr_prefix:
            prefix = instr_prefix[instr]
        elif instr == 'deimos':
            if '/fcs' in outdir:
                prefix = 'DF'
            else:
                prefix = 'DE'
        elif instr == 'kcwi':
            try:
                camera = keywords['CAMERA'].lower()
            except KeyError:
                logging.warning('No keyword CAMERA exists for {}'.format(instr))
            if camera == 'blue':
                prefix = 'KB'
            elif camera == 'red':
                prefix = 'KR'
            elif camera == 'fpc':
                prefix = 'KF'
        elif instr == 'nirspec':
            if '/scam' in outdir:
                prefix = 'NC'
            elif '/spec' in outdir:
                prefix = 'NC'
        elif instr == 'osiris':
            if '/SCAM' in outdir:
                prefix = 'OI'
            elif '/SPEC' in outdir:
                prefix = 'OS'
        elif instr == 'nires':
            dfile = keywords['DATAFILE']
            if dfile[0] == 's':
                prefix = 'NR'
            elif dfile[0] == 'v':
                prefix = 'NI'
        else:
                print('Cannot determine prefix')
                return False

        # Will utDate be a string, int, or datetime object?
        dateobs = dateobs.replace('-', '')
        dateobs = dateobs.replace('/', '')
        koaid = prefix + '.' + dateobs + '.' + totalSeconds.zfill(5) + '.fits'
        keywords['KOAID'] = koaid
        return True
