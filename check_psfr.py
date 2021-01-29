'''
Checks koa.psfr table for entries that are done processing and need transfer.
Transfer script lives on psfrdataserver1 and this script calls it via ssh+authkeys.
Transfer script path is defined in pyDEP config as [INSTR]['PSFR_XFR']
This is meant to be run on a cron once each morning for each PSFR instrument:

  30  8 * * * /usr/local/anaconda3-5.0.0.1/bin/python /kroot/archive/dep/default/check_psfr NIRC2  `date -u +\%Y-\%m-\%d` >> ~/log/check_psfr.log

Overview of PSFR archive process:
- PSFR processing is activated by overriding the Instrument.run_psfr() function for an instrument in pyDEP.
- An authorized keys is setup for koaadmin@vm-koaserver5 to ssh to psfr@psfrdataserver1
- The psfr script that is executed on psfrdataserver1 is stored in pyDEP config as [INSTR]['PSFR']
- The script takes as inputs the instr, utdate, and remote path to lev0 dir.  
- So, psfrdataserver1 is dependent on a mount to vm-koaserver5.
- gettrsdata.csh handles creating and updating the psfr db record and calling gettrsdata.pro.  The latter does the heavy lifting along with gettrs.pro to create the .sav files.
- gettrsdata.pro monitors the lev0 directory for the DQA.loc file and will continue monitoring it for new fits images until the loc file disappears.  This could be problematic if pyDEP crashed in DQA.
- koaxfr.csh is the script that lives on psfrdataserver1 that needs to be called by this script.

TODO/NOTES:
- koa.psfr does not have a primary/unique key.  It could be instr+utdate, but for now we won't worry about this.
- This script could look for existing similar process on psfrdataserver1 and kill them), although the worst that might 
happen is they overwrite the save .sav files and double the log entries and double the transfer, so we won't worry
about this for now.
'''

import os
import sys
from urllib.request import urlopen
import json
import argparse
import traceback
import yaml
import subprocess


#todo: use logger module?
#todo: wait for exit status and log/report output

def main():

    #parse args
    parser = argparse.ArgumentParser()
    parser.add_argument('instr',  type=str, help='instrument')
    parser.add_argument('utdate', type=str, help='YYYY-MM-DD')
    parser.add_argument('--dev', default=False, action='store_true', help='Report only.  No action.')
    args = parser.parse_args()

    instr  = args.instr.upper()
    utdate = args.utdate
    dev    = args.dev
    print(f"Running {sys.argv}")

    #cd to script dir so relative paths work
    os.chdir(sys.path[0])

    #open config
    with open('config.live.ini') as f: 
        config = yaml.safe_load(f)

    #make sure call is defined in config
    psfr_xfr = config.get(instr, {}).get('PSFR_XFR')
    if not psfr_xfr:
        email_admin(f"No config defined for {instr} PSFR_XFR")
        return

    #get record via KOA API
    url = config['API']['KOAAPI'] + f"cmd=getPsfr&instr={instr}&utdate={utdate}"
    try:
        rows = json.loads(urlopen(url).read().decode("utf8"))
    except Exception as e:
        email_admin(f"Error: Could not query API URL: {url}\n" + traceback.format_exc())
        return

    #No results?
    if not rows:
        print(f"No PSFR record for {instr} {utdate}")
        return
    row = rows[0]

    # Check if no PSFR files
    if not row['files']:
        print(f"No PSFR files for {instr} {utdate}")
        return

    # See if it is still processing
    if not row['end_time']:
        print(f"Record still processing for {instr} {utdate}")
        return

    # See if it was already sent
    if row['ingest_stat'] == 'DONE':
        print(f"Record already ingested for {instr} {utdate}")
        return

    #execute command
    cmd = psfr_xfr.split();
    cmd += [instr, utdate, row['location']]
    print('Command: ', ' '.join(cmd))
    if dev:
        print("DEV MODE: NOT EXECUTING COMMAND")
    else:
        print("Executing command")
        out, stat = run_cmd(cmd)
        if stat != 0:
            email_admin(f"Command returned status {stat}.\nOutput:\n{out}")
            return
    print("DONE")


def run_cmd(cmd):
    '''Run command and get output and return code.'''
    try:
        ps = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out = ps.communicate()[0]
        out = out.decode("utf-8").strip()
    except Exception as e:
        print(traceback.format_exc())
        return None, -1
    return out, ps.returncode


def email_admin(msg):

    print(msg)

    with open('config.live.ini') as f: 
        config = yaml.safe_load(f)
    email = config.get('REPORT', {}).get('ADMIN_EMAIL')
    if not email: return

    import smtplib
    from email.mime.text import MIMEText

    em = MIMEText(msg)
    em['Subject'] = 'ERROR: check_psfr'
    em['To'] = email
    em['From'] = 'koaadmin@keck.hawaii.edu'
    s = smtplib.SMTP('localhost')
    s.send_message(em)
    s.quit()


if __name__ == "__main__":
    main()
