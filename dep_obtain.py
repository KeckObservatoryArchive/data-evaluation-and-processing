from datetime import datetime, timedelta
from pytz import timezone
from verification import *
import os
import json
import urllib.request

def dep_obtain(instrObj):
    """
    Queries the telescope schedule database and creates the following files
    in stageDir:

    dep_obtainINSTR.txt
    dep_notschedINSTR.txt (if no entries fouund in database)

    @param instrObj: the instrument object
    @type instrObj: instrument class
    """

    # Verify the supplied instrument and UT date are allowed values/formats

    #verify_instrument(instrObj.instr)
    #verify_date(instrObj.utDate)

    instrObj.log.info('dep_obtain: started for {} {} UT'.format(instrObj.instr, instrObj.utDate))

    # Verify that the stage directory exists.  If not, then make it.

    if not os.path.isdir(instrObj.dirs['stage']):
        instrObj.log.info('dep_obtain: making stage directory {}'.format(stageDir))
        os.makedirs(instrObj.dirs['stage'])

    # Get HST from utDate

    utDateObj = datetime.strptime(instrObj.utDate, '%Y-%m-%d')
    hstDateObj = utDateObj - timedelta(days=1)
    hstDate = hstDateObj.strftime('%Y-%m-%d')

    # URL to query telescope schedule

    #url = ('https://www.keck.hawaii.edu/software/db_api/telSchedule.php', '?')
    schedUrl = (instrObj.telUrl, 'cmd=getSchedule', '&date=', hstDate, '&instr=', instrObj.instr)
    schedUrl = ''.join(schedUrl)

    # Output files

    notScheduledFile = (instrObj.dirs['stage'], '/dep_notsched', instrObj.instr, '.txt')
    notScheduledFile = ''.join(notScheduledFile)
    obtainFile = (instrObj.dirs['stage'], '/dep_obtain', instrObj.instr, '.txt')
    obtainFile = ''.join(obtainFile)

    try:
        instrObj.log.info('dep_obtain: retrieving telescope schedule information for {}'.format(instrObj.instr))

        # Read the input URL

        data = urllib.request.urlopen(schedUrl)
        data = data.read().decode('utf8')    # Convert from byte to ascii
        if len(data) > 0:
            data = json.loads(data)            # Convert to Python list
        if isinstance(data, dict):
            data = [data]

        # Get the telescope number

        sendUrl = (instrObj.telUrl, 'cmd=getTelnr&instr=', instrObj.instr)
        sendUrl = ''.join(sendUrl)
        telGet = urllib.request.urlopen(sendUrl)
        telGet = telGet.read().decode('utf8')       # Convert from byte to ascii
        telGet = json.loads(telGet)                 # Convert to Python list
        telnr = telGet[0]['TelNr']

        # Get OA

        oaUrl = (instrObj.telUrl, 'cmd=getNightStaff', '&date=', hstDate)
        oaUrl = oaUrl + ('&telnr=', str(telnr), '&type=oa')
        oaUrl = ''.join(oaUrl)
        oaGet = urllib.request.urlopen(oaUrl)
        oaGet = oaGet.read().decode('utf8')
        oa = 'None'
        if len(oaGet) > 0:
            oaGet = json.loads(oaGet)
            if isinstance(oaGet, dict):
                if ('Alias' in oaGet):
                    oa = oaGet['Alias']
            else:
                for entry in oaGet:
                    if entry['Type'] == 'oa':
                        oa = entry['Alias']

        # No entries found
        # Create stageDir/dep_notschedINSTR.txt and dep_obtainINSTR.txt

        if len(data) == 0:
            instrObj.log.info('dep_obtain: no information found for {}'.format(instrObj.instr))

            with open(notScheduledFile, 'w') as fp:
                fp.write('{} not scheduled'.format(instrObj.instr))

            with open(obtainFile, 'w') as fp:
                fp.write('{} {} NONE NONE NONE NONE NONE'.format(hstDate, oa))

        # Entries found
        # Create stageDir/dep_obtainINSTR.txt

        else:
            with open(obtainFile, 'w') as fp:
                num = 0
                for entry in data:

                    # Get observer list from URL

                    obsUrl = (instrObj.telUrl, 'cmd=getObservers', '&schedid=', entry['SchedId'])
                    obsUrl = ''.join(obsUrl)
                    observer = urllib.request.urlopen(obsUrl)
                    observer = observer.read().decode('utf8')
                    observer = json.loads(observer)
                    observers = 'None'
                    if len(observer) > 0:
                        observers = observer[0]['Observers']

                    if num > 0:
                        fp.write('\n')

                    fp.write('{} {} {} {} {} {} {}'.format(hstDate, oa, entry['Account'], entry['Institution'], entry['Principal'], entry['ProjCode'], observers))

                    instrObj.log.info('dep_obtain: {} {} {} {} {} {} {}'.format(hstDate, oa, entry['Account'], entry['Institution'], entry['Principal'], entry['ProjCode'], observers))

                    num += 1

    except:
        instrObj.log.info('dep_obtain: {} error reading telescope schedule'.format(instrObj.instr))
