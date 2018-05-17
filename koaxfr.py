from send_email import *

def koaxfr(instrObj):
    """
    Transfers the contents of outputDir to its final destination.
    Location transferring to is located in config.live.ini:
        KOAXFR:server
        KOAXFR:account
        KOAXFR:dir
    Email is sent to KOAXFR:emailto upon successful completion
    Email is sent to KOAXFR:emailerror if an error occurs
    """

    import configparser
    import os

    # Directory that will be transfered

    fromDir = instrObj.dirs['output']

    # Verify that the directory to transfer exists

    if not os.path.isdir(fromDir):
        instrObj.log.error('koaxfr.py directory ({}) does not exist'.format(fromDir))
        return False

    # Configure the transfer command

    import configparser
    config = configparser.ConfigParser()
    config.read('config.live.ini')

    instr = instrObj.instr.upper()
    server = config['KOAXFR']['server']
    account = config['KOAXFR']['account']
    toDir = config['KOAXFR']['dir']
    toLocation = ''.join((account, '@', server, ':', toDir, '/', instr))
    instrObj.log.info('koaxfr.py transferring directory {} to {}'.format(fromDir, toLocation))
    instrObj.log.info('koaxfr.py rsync -avz {} {}'.format(fromDir, toLocation))
    emailFrom = config['KOAXFR']['emailfrom']

    # Transfer the data

    import subprocess as sp
    xfrCmd = sp.Popen(["rsync -avz " + fromDir + ' ' + toLocation],
                      stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
    output, error = xfrCmd.communicate()
    if not error:
        # Send email verifying transfer complete
        emailTo = config['KOAXFR']['emailto']
        instrObj.log.info('koaxfr.py sending email to {}'.format(emailTo))
        subject = ''.join(('lev0', instrObj.utDate, ' ', instr))
        message = 'lev0 data successfully transferred to koaxfr'
        send_email(emailTo, emailFrom, subject, message)
        return True
    else:
        # Send email notifying of error
        emailError = config['KOAXFR']['emailerror']
        instrObj.log.error('koaxfr.py error transferring directory ({}) to {}'.format(fromDir, toLocation))
        instrObj.log.error('koaxfr.py sending email to {}'.format(emailError))
        message = ''.join(('Error transferring directory', fromDir, ' to ', toDir, '\n\n'))
        send_email(emailError, emailFrom, 'Error - koaxfr transfer', message)
        return False

