import configparser
import os
import hashlib
import urllib.request
import json

def update_koatpx(instrObj, column, value):
    """
    Sends command to update KOA data

    @param instrObj: the instrument object
    @param column: column to update in koa.koatpx
    @type column: string
    @param value: value to update column to
    @type value: string
    """

    config = configparser.ConfigParser()
    config.read('config.live.ini')

    user = os.getlogin()
    myHash = hashlib.md5(user.encode('utf-8')).hexdigest()

    # Database access URL

    url = config['API']['koaapi']
    sendUrl = ('cmd=updateTPX&instr=', instrObj.instr.upper())
    sendUrl = sendUrl + ('&utdate=', instrObj.utDate, '&')
    sendUrl = sendUrl + ('column=', column, '&value=', value.replace(' ', '+'))
    sendUrl = ''.join(sendUrl)
    sendUrl = ''.join((url, sendUrl, '&hash=', myHash))

    instrObj.log.info('update_koatpx {} - {}'.format(user, sendUrl))

    data = urllib.request.urlopen(sendUrl)
    data = data.read().decode('utf8')       # Convert from byte to ascii
    if data == 'false':
        instrObj.log.info('update_koatpx failed')
        return False
    return True
