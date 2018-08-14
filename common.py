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

    if log:
        log.info('update_koatpx {} - {}'.format(user, sendUrl))

    sendUrl = ''.join((url, sendUrl, '&hash=', myHash))

    data = urllib.request.urlopen(sendUrl)
    data = data.read().decode('utf8')       # Convert from byte to ascii
    if data == 'false':
        if log:
            log.warning('update_koatpx failed! URL: ' + sendUrl)
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
    return str(total/1000000.0)

