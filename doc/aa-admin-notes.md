# Creating Metadata Format File

If you need to create or make changes to the keyword metadata definitions:

- Get latest spreadsheet definition file (currently as Google docs)
- Export columns in this order: keyword, dataType, colSize, allowNull
- Make sure KOAID is first keyword row
- Save to repo as /metadata/keywords.format.<INSTR> (ie "keywords.format.NIRES")


# Regression Testing
TODO


# Tag and Release Process

Before tagging:
- Commit config.ini with new "DEP_VERSION" value

To tag with github: 
- Go to 'Code' => 'Release' tab
- Click "Create a new release"
- Use "v0.0.0" versioning

To release to server:
- Use account: ssh koabuild@vm-koaserver5
- cd to build folder: cd /kroot/archive/koa/dep/
- Checkout as version folder: git clone https://github.com/KeckObservatoryArchive/data-evaluation-and-processing.git ./dep-v0.1.0
- Create/edit "config.live.ini".
- TEST!
- change "default" symbolic link: ln -s dep-v0.1.0 release

Verify cron job:
- A cron job should be running on the server for each instrument using 'koaadmin' user account.  Example:
    0 9 * * * /usr/local/anaconda3-5.0.0.1/bin/python /kroot/archive/koa/dep/default/dep_go.py NIRES `date -u +\%Y-\%m-\%d` 1 > /dev/null 2>&1
