import datetime as dt
from pytz import timezone


def dep_obtain(instr, utDate, stageDir):
    """
    """

    verify_instrument()
    verify_date(utDate)
    assert stageDir != '', 'stageDir value is blank'
	
    # Make the staging directory

    # Get HST from utDate
    if '/' in utDate:
        utDateObj = dt.strptime(utDate, '%Y/%m/%d %H:%M:%S')
    elif '-' in utDate:
        utDateObj = dt.strptime(utDate, '%Y-%m-%d %H:%M:%S')
    
    hstDateObj = timezone('US/Hawaii').localize(utDateObj)
    hstDate = hstDateObj.strftime('%Y/%m/%d')
    year, month, day = hstDate.split('/')

    # Query the telescope schedule

	
    # Create stageDir/dep_obtainINSTR.txt
	
