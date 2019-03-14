from datetime import datetime
import os
import hashlib
import urllib
import json
from send_email import send_email
import configparser
import glob


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



def make_dir_md5_table(readDir, endswith, outfile):

    files = []
    for file in sorted(os.listdir(readDir)):
        if (endswith == None or file.endswith(endswith)): 
            files.append(readDir + '/' + file)

    with open(outfile, 'w') as fp:
        for file in files:
            md5 = hashlib.md5(open(file, 'rb').read()).hexdigest()
            fp.write(md5 + '  ' + os.path.basename(file) + "\n")



def removeFilesByWildcard(wildcardPath):
    for file in glob.glob(wildcardPath):
        os.remove(file)



def get_api_data(url, getOne=False, isJson=True):
    '''
    Gets data for common calls to url API requests.

    #todo: add some better validation checks and maybe some options (ie getOne, typeCast)
    '''
    
    try:
        data = urllib.request.urlopen(url)
        data = data.read().decode('utf8')
        if isJson: data = json.loads(data)

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

    # Create database access URL

    sendUrl = config['API']['koaapi']
    sendUrl += 'cmd=updateTPX&instr=' + instr.upper()
    sendUrl += '&utdate=' + utDate.replace('/', '-') + '&'
    sendUrl += 'column=' + column + '&value=' + value.replace(' ', '+')
    sendUrl += '&hash=' + myHash
    if log: log.info('update_koatpx {} - {}'.format(user, sendUrl))

    # Call URL and check result 
    data = get_api_data(sendUrl)
    if not data:
        if log: log.error('update_koatpx failed! URL: ' + sendUrl)
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

