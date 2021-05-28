from send_email import *
from common import update_koatpx, get_api_data
from datetime import datetime as dt
import os
import yaml
import json


def koaxfr(instrObj, tpx=0):
    """
    Transfers the contents of outputDir to its final destination.
    Location transferring to is located in config.live.ini:
        KOAXFR:server
        KOAXFR:account
        KOAXFR:dir
    Email is sent to KOAXFR:emailto upon successful completion
    Email is sent to KOAXFR:emailerror if an error occurs
    """

    # shorthand vars

    instr   = instrObj.instr.upper()
    utDate  = instrObj.utDate
    log     = instrObj.log
    fromDir = instrObj.dirs['output']

    # Verify that the directory to transfer exists

    if not os.path.isdir(fromDir):
        log.error('koaxfr.py directory ({}) does not exist'.format(fromDir))
        return False

    # Read config file
    with open('config.live.ini') as f: config = yaml.safe_load(f)
    emailFrom = config['KOAXFR']['EMAILFROM']
    emailTo = config['KOAXFR']['EMAILTO']
    api     = config['API']['INGESTAPI']
    url     = f"{api}instrument={instr}&ingestType=lev0&date={utDate.replace('-', '')}"

    # If no FITS files then email IPAC verifying (empty) transfer complete

#    count = len([name for name in os.listdir(instrObj.dirs['lev0']) if name.endswith('.fits.gz')])
    count = 0
    for dirpath, dirnames, filenames in os.walk(instrObj.dirs['lev0']):
        for f in filenames:
            if f.endswith('.fits.gz'):
                count += 1

    if count == 0:
        log.info('koaxfr.py no FITS files to transfer')
#        subject = ''.join((utDate.replace('-', ''), ' ', instr))
#        message = ''.join(('No metadata for ', utDate.replace('-', '')))
#        log.info('koaxfr.py sending no data email to {}'.format(emailTo))
#        send_email(emailTo, emailFrom, subject, message)
        # Send ingestionAPI request - need extra json.loads() for IPAC call
        url = f"{url}&numFiles=0"
        log.info('koaxfr.py sending API call to {}'.format(url))
        data = get_api_data(url)
        try: # incase None returned
            data = json.loads(data)
        except:
            pass
        # Success?
        if not data or data.get('stat').lower() != 'ok':
            subject = 'IPAC API FAILURE'
            message = f"IPAC API failure\n\n{url}"
            send_email(emailFrom, emailFrom, subject, message)
        # Update koatpx
        if tpx:
            update_koatpx(instr, utDate, 'files_arch', '0', log)
            update_koatpx(instr, utDate, 'sci_files', '0', log)
            update_koatpx(instr, utDate, 'ondisk_stat', 'N/A', log)
            update_koatpx(instr, utDate, 'arch_stat', 'N/A', log)
            update_koatpx(instr, utDate, 'metadata_stat', 'N/A', log)
            update_koatpx(instr, utDate, 'dvdwrit_stat', 'N/A', log)
            update_koatpx(instr, utDate, 'dvdsent_stat', 'N/A', log)
            update_koatpx(instr, utDate, 'dvdstor_stat', 'N/A', log)
            #update_koatpx(instr, utDate, 'tpx_stat', 'N/A', log)

        return True

    # Configure the transfer command

    server = config['KOAXFR']['SERVER']
    account = config['KOAXFR']['ACCOUNT']
    toDir = config['KOAXFR']['DIR']
    toLocation = ''.join((account, '@', server, ':', toDir, '/', instr))
    log.info('koaxfr.py transferring directory {} to {}'.format(fromDir, toLocation))
    log.info('koaxfr.py rsync -avz --no-t {} {}'.format(fromDir, toLocation))

    # Transfer the data

    import subprocess as sp
    xfrCmd = sp.Popen(["rsync -avz --no-t " + fromDir + ' ' + toLocation],
                      stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
    output, error = xfrCmd.communicate()
    if not error:
        # Send email verifying transfer complete and update koatpx
#        log.info('koaxfr.py sending email to {}'.format(emailTo))
#        subject = ''.join(('lev0 ', utDate.replace('-', ''), ' ', instr))
#        message = 'lev0 data successfully transferred to koaxfr'
#        send_email(emailTo, emailFrom, subject, message)
        # Send ingestionAPI request - need extra json.loads() for IPAC call
        url = f"{url}&numFiles={count}"
        log.info('koaxfr.py sending API call to {}'.format(url))
        data = get_api_data(url)
        try: # incase None returned
            data = json.loads(data)
        except:
            pass
        if not data or data.get('stat').lower() != 'ok':
            subject = 'IPAC API FAILURE'
            message = f"IPAC API failure\n\n{url}"
            send_email(emailFrom, emailFrom, subject, message)
        # Update koatpx
        if tpx:
            utcTimestamp = dt.utcnow().strftime("%Y%m%d %H:%M")
            val = 'ERROR' if not data or data.get('stat').lower() != 'ok' else 'DONE'
            update_koatpx(instr, utDate, 'dvdsent_stat', val, log)
            update_koatpx(instr, utDate, 'dvdsent_time', utcTimestamp, log)
        return True
    else:
        # Send email notifying of error
        emailError = config['KOAXFR']['EMAILERROR']
        log.error('koaxfr.py error transferring directory ({}) to {}'.format(fromDir, toLocation))
        log.error('koaxfr.py sending email to {}'.format(emailError))
        message = ''.join(('Error transferring directory', fromDir, ' to ', toDir, '\n\n'))
        send_email(emailError, emailFrom, 'Error - koaxfr transfer', message)
        return False

