import sys
import os
import datetime as dt
import subprocess


# usage
if len(sys.argv) <= 5:
    print ("USAGE: dep_go_reprocess.py instr startDate endDate tpx searchDirBase")
    sys.exit(0)


# get inputs
instr           = sys.argv[1]
startDateStr    = sys.argv[2]
endDateStr      = sys.argv[3]
tpx             = sys.argv[4]
searchDirBase   = sys.argv[5]


# loop dates and call 
startDate = dt.datetime.strptime(startDateStr, '%Y-%m-%d')
endDate   = dt.datetime.strptime(endDateStr,   '%Y-%m-%d')
curDate   = dt.datetime.strptime(startDateStr, '%Y-%m-%d')
while curDate <= endDate:

    curDateStr = curDate.strftime('%Y-%m-%d')
    searchDir = searchDirBase + '/' + curDateStr.replace('-', '')
    searchDir = searchDir.replace('//', '/')

    print ('----------------------------------------------------')

    if not os.path.isdir(searchDir):
        print ("NOTICE: Could not find dir for: " + searchDir)    

    else:
        # cmd = "python3 dep_go.py " + instr + ' ' + curDateStr + ' ' + tpx + ' obtain tar --modtimeOverride 1 --reprocess 1 --searchDir ' + searchDir
        params = ['python3', 'dep_go.py', instr, curDateStr, tpx, 'obtain', 'tar', '--modtimeOverride', '1', '--reprocess', '1', '--searchDir', searchDir]
        print ('COMMAND: ', ' '.join(params))
        subprocess.call(params)

    curDate += dt.timedelta(days=1)

print ("DONE")

