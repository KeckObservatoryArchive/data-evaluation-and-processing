import os
from datetime import datetime, timedelta
from common import url_get

def dep_obtain(instrObj):
    """
    Queries the telescope schedule database and creates the following files in stageDir:

    dep_obtainINSTR.txt
    dep_notschedINSTR.txt (if no entries found in database)

    @param instrObj: the instrument object
    @type instrObj: instrument class
    """

    log = instrObj.log
    log.info('dep_obtain: started for {} {} UT'.format(instrObj.instr, instrObj.utDate))

    # Get HST from utDate

    utDateObj = datetime.strptime(instrObj.utDate, '%Y-%m-%d')
    hstDateObj = utDateObj - timedelta(days=1)
    hstDate = hstDateObj.strftime('%Y-%m-%d')

    # Output files

    notScheduledFile = ''.join((instrObj.dirs['stage'], '/dep_notsched', instrObj.instr, '.txt'))
    obtainFile       = ''.join((instrObj.dirs['stage'], '/dep_obtain', instrObj.instr, '.txt'))

    try:

        # Get OA

        telnr = instrObj.get_telnr()
        oaUrl = ''.join((instrObj.telUrl, 'cmd=getNightStaff', '&date=', hstDate, '&telnr=', str(telnr), '&type=oa'))
        log.info('dep_obtain: retrieving night staff info: {}'.format(oaUrl))
        oaData = url_get(oaUrl)
        oa = 'None'
        if oaData:
            if isinstance(oaData, dict):
                if ('Alias' in oaData):
                    oa = oaData['Alias']
            else:
                for entry in oaData:
                    if entry['Type'] == 'oa' or entry['Type'] == 'oar':
                        oa = entry['Alias']

        # Read the telescope schedul URL
        # No entries found: Create stageDir/dep_notschedINSTR.txt and dep_obtainINSTR.txt

        instrBase = 'NIRSP' if (instrObj.instr == 'NIRSPEC') else instrObj.instr
        schedUrl = ''.join((instrObj.telUrl, 'cmd=getSchedule', '&date=', hstDate, '&instr=', instrBase))
        log.info('dep_obtain: retrieving telescope schedule info: {}'.format(schedUrl))
        schedData = url_get(schedUrl)
        if schedData and isinstance(schedData, dict): schedData = [schedData]
        if not schedData:
            log.info('dep_obtain: no telescope schedule info found for {}'.format(instrObj.instr))

            with open(notScheduledFile, 'w') as fp:
                fp.write('{} not scheduled'.format(instrObj.instr))

            with open(obtainFile, 'w') as fp:
                fp.write('{} {} NONE NONE NONE NONE NONE'.format(hstDate, oa))

        # Entries found: Create stageDir/dep_obtainINSTR.txt

        else:
            with open(obtainFile, 'w') as fp:
                num = 0
                for entry in schedData:

                    if entry['Account'] == '': entry['Account'] = '-'
                    obsUrl = ''.join((instrObj.telUrl, 'cmd=getObservers', '&schedid=', entry['SchedId']))
                    log.info('dep_obtain: retrieving observers info: {}'.format(obsUrl))
                    obsData = url_get(obsUrl)
                    if obsData and len(obsData) > 0: observers = obsData[0]['Observers']
                    else                           : observers = 'None'

                    if num > 0: fp.write('\n')
                    fp.write('{} {} {} {} {} {} {}'.format(hstDate, oa, entry['Account'], entry['Institution'], entry['Principal'], entry['ProjCode'], observers))
                    log.info('dep_obtain: {} {} {} {} {} {} {}'.format(hstDate, oa, entry['Account'], entry['Institution'], entry['Principal'], entry['ProjCode'], observers))

                    num += 1

    except:
        log.info('dep_obtain: {} error reading telescope schedule'.format(instrObj.instr))
        return False

    return True



def get_obtain_data(file):
    '''
    Reads an obtain output file (presumably one it created)
    and parses it into a key-value pair array for each entry
    '''

    #check
    if not os.path.exists(file):
        raise Exception('get_obtain_data: file "{}" does not exist!!'.format(file))
        return

    #read each line and create key-value pair rows from col list names
    data = []
    cols = ['utdate', 'oa','account', 'proginst', 'progpi', 'progid', 'observer']
    with open(file, 'r') as rfile:
        for line in rfile:
            vals = line.strip().split(' ')
            row = {}
            for i in range(0, len(cols)):
                row[cols[i]] = vals[i]
            data.append(row)
            del row

    return data
