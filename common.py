from datetime import datetime
import os
import hashlib
import urllib
import json
from send_email import send_email
import configparser



def get_root_dirs(rootDir, instr, utDate):
    """
    Gets the various rootDir subdirectories of interest

    @param rootDir: root directory for data processing
    @type rootDir: string
    @param instr: instrument name
    @type instr: string
    @param utDate: UT date (yyyy-mm-dd)
    @type utDate: string
    """

    instr = instr.upper()
    ymd = utDate
    ymd = ymd.replace('-', '')
    ymd = ymd.replace('/', '')

    dirs = {}
    dirs['stage']   = ''.join((rootDir, '/stage/', instr, '/', ymd))
    dirs['process'] = ''.join((rootDir, '/', instr))
    dirs['output']  = ''.join((rootDir, '/', instr, '/', ymd))
    dirs['lev0']    = ''.join((rootDir, '/', instr, '/', ymd, '/lev0'))
    dirs['lev1']    = ''.join((rootDir, '/', instr, '/', ymd, '/lev1'))
    dirs['anc']     = ''.join((rootDir, '/', instr, '/', ymd, '/anc'))
    dirs['udf']     = ''.join((dirs['anc'], '/udf'))

    return dirs


# def semester(keywords, utDate):
#         """
#         Determines the Keck observing semester for the supplied UT date

#         semester('2017-08-01') --> 2017A
#         semester('2017-08-02') --> 2017B

#         A = Feb. 2 to Aug. 1 (UT)
#         B = Aug. 2 to Feb. 1 (UT)
#         """

#         utDate = utDate.replace('-', '')
#         utDate = utDate.replace('/', '')

#         try:
#                 utDate = datetime.strptime(utDate, '%Y%m%d')
#         except ValueError:
#                 raise ValueError("Incorrect date format, should be YYYYMMDD")

#         year = utDate.year
#         month = utDate.month
#         day = utDate.day

#         # All of January and February 1 are semester B of previous year
#         if month == 1 or (month == 2 and day == 1):
#                 semester = 'B'
#                 year -= 1
#         # August 2 onward is semester B
#         elif month >= 9 or (month == 8 and day >= 2):
#                 semester = 'B'
#         else:
#                 semester = 'A'

#         keywords['SEMESTER'] = semester


def semester(keys):
    """
    Determines the Keck observing semester from the DATE-OBS keyword in header
    and updates the SEMESTER keyword in header.

    semester('2017-08-01') --> 2017A
    semester('2017-08-02') --> 2017B

    A = Feb. 2 to Aug. 1 (UT)
    B = Aug. 2 to Feb. 1 (UT)
    """


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
        if int(year)<50: year = '20' + year
        else:            year = '19' + year
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



def koaid(keywords, utDate):
        '''
        Determines the KOAID

        KOAID = II.YYYYMMDD.######.fits
           - II = instrument prefix
           - YYYYMMDD = UT date of observation
           - ###### = number of seconds into UT date
         '''


        #TODO: move this to instrument.py, instr_*.py


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




def fixdatetime(utdate, fname, keys):

    utdate = utdate.replace('-','')
    utdate = utdate.replace('/','')

    datefile = ''.join(('/home/koaadmin/fixdatetime/', utdate, '.txt'))
    datefile = '/home/koaadmin/fixdatetime/20101128.txt'
    if os.path.isfile(datefile) is False:
        return

    fileroot = fname.split('/')
    fileroot = fileroot[-1]
    output = ''

    with open(datefile, 'r') as df:
        for line in df:
            if fileroot in line:
                output = line
                break

    if output != '':
        dateobs = keys.get('DATE-OBS')
        if 'Error' not in dateobs and dateobs.strip() != '':
            return
        vals = output.split(' ')
        keys.update({'DATE-OBS':(vals[1], ' Original value missing - added by KOA')})
        keys.update({'UTC':(vals[2], 'Original value missing - added by KOA')})




def make_dir_md5_table(readDir, endswith, outfile):

    files = []
    for file in sorted(os.listdir(readDir)):
        if (endswith == None or file.endswith(endswith)): 
            files.append(readDir + '/' + file)

    with open(outfile, 'w') as fp:
        for file in files:
            md5 = hashlib.md5(open(file, 'rb').read()).hexdigest()
            fp.write(md5 + '  ' + os.path.basename(file) + "\n")


def url_get(url, getOne=False):
    '''
    Gets data for common calls to url API requests.

    #todo: add some better validation checks and maybe some options (ie getOne, typeCast)
    '''
    
    try:
        data = urllib.request.urlopen(url)
        data = data.read().decode('utf8')
        data = json.loads(data)

        if (getOne and len(data) > 0):
            data = data[0]

        return data

    except:
        return None



def do_fatal_error(msg, instr=None, utDate=None, failStage=None, log=None):

    #read config vars
    config = configparser.ConfigParser()
    config.read('config.live.ini')
    adminEmail = config['REPORT']['ADMIN_EMAIL']

    
    #form subject
    subject = 'DEP ERROR: ['
    if (instr)     : subject += instr     + ' '
    if (utDate)    : subject += utDate    + ' '
    if (failStage) : subject += failStage + ' '
    subject += ']'


    #always print
    print (subject + ' ' + msg)


    #if log then log
    if log: log.error(subject + ' ' + msg)


    #if admin email and not dev then email
    if (adminEmail != ''):
        send_email(adminEmail, adminEmail, subject, msg)

def update_koatpx(instr, utDate, column, value, log=''):
    """
    Sends command to update KOA data

    @param instrObj: the instrument object
    @param column: column to update in koa.koatpx
    @type column: string
    @param value: value to update column to
    @type value: string
    """

    import configparser
    config = configparser.ConfigParser()
    config.read('config.live.ini')

    user = os.getlogin()
    import hashlib
    myHash = hashlib.md5(user.encode('utf-8')).hexdigest()

    # Database access URL

    url = config['API']['koaapi']
    sendUrl = ('cmd=updateTPX&instr=', instr.upper())
    sendUrl = sendUrl + ('&utdate=', utDate.replace('/', '-'), '&')
    sendUrl = sendUrl + ('column=', column, '&value=', value.replace(' ', '+'))
    sendUrl = ''.join(sendUrl)
    sendUrl = ''.join((url, sendUrl, '&hash=', myHash))

    if log:
        log.info('update_koatpx {} - {}'.format(user, sendUrl))

    data = urllib.request.urlopen(sendUrl)
    data = data.read().decode('utf8')       # Convert from byte to ascii
    if data == 'false':
        if log:
            log.info('update_koatpx failed')
        return False
    return True

def get_directory_size(dir):
    """
    Returns the directory size in MB

    @param dir: directory to determine size for
    @type dir: string
    """

    #directory doesn't exist
    if not os.path.isdir(dir):
        return 0

    #walk through and sum up size
    total = 0
    for dirpath, dirnames, filenames in os.walk(dir):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total += os.path.getsize(fp)
    return total

