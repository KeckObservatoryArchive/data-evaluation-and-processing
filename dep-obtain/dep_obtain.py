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
	
def get_json_from_url(url):
    """
    Reads input URL and returns a Python List. It is assumed
    the URL returns data in JSON format.

    @type url: string
    @param url: URL to read and convert JSON to Python list
    """
    import json
    import urllib.request
    try:
        # Read the input URL
        data = urllib.request.urlopen(url)

        # Convert from byte to ascii
        newData = data.read().decode('utf8')

        # Convert to Python List
#        jsonData = json.loads(newData)
#        return jsonData
        return newData
    except:
        return 'ERROR'
