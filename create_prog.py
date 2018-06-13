from common import fixdatetime
from imagetyp_instr import imagetyp_instr
from astropy.io import fits
from urllib.request import urlopen



def create_prog(instrObj):
    '''
    Creates a temporary staging data file "createprog.txt' listing all 
    program information for each file.  This file is input to getProgInfo.py.
    The following data are written out one value per line per fits file:

        file
        utdate
        utc
        outdir
        observer
        frameno
        imagetyp
        progid
        progpi
        proginst
        progtitl
        oa
        <repeats here>

    @type instrObj: instrument
    @param instr: The instrument object
    '''


    #short vars
    instr = instrObj.instr
    utDate = instrObj.utDate
    stageDir = instrObj.dirs['stage']
    log = instrObj.log


    #info
    if log: log.info('create_prog: Getting FITS file information')


    # Get OA from dep_obtain file
    dep_obtain = stageDir + '/dep_obtain' + instr + '.txt'
    oa = []
    with open(dep_obtain, 'r') as dob:
        for line in dob:
            items = line.strip().split(' ')
            if len(items)>1:
                oa.append(items[1])
    if (len(oa) == 0): oa = ''
    else             : oa = oa[0]


    # Get all files
    fileList = []
    locateFile = stageDir + '/dep_locate' + instr + '.txt'
    with open(locateFile, 'r') as loc:
        for item in loc:
            fileList.append(item.strip())


    # Open output file
    outfile = stageDir + '/createprog.txt'
    with open(outfile, 'w') as ofile:
        for filename in fileList:

        	#skip blank lines
            if filename.strip() == '': continue

            #skip OSIRIS files that end in 'x'
            if instr == 'OSIRIS':
                if filename[-1] == 'x':
                    log.info(filename + ': file ends with x')
                    continue

            #get header
            #todo: Move all keyword fixes as standard steps done upfront?
            instrObj.set_fits_file(filename)
            header = instrObj.fitsHeader

            # Temp fix for bad file times(NIRSPEC legacy)
            fixdatetime(utDate, filename, header)

            #get image type
            imagetyp = imagetyp_instr(instr, header)

            #get date-obs
            instrObj.set_dateObs()
            dateObs = header.get(instrObj.dateObs)

            #get utc
            instrObj.set_utc()
            utc = header.get(instrObj.utc)

            #get observer
            observer = header.get('OBSERVER').strip()

            #get fileno
            fileno = instrObj.get_fileno()

            #get outdir
            outdir = instrObj.get_outdir()

            #lop off everything before /sdata
            fileparts = filename.split('/sdata')
            if len(fileparts) > 1: newFile = '/sdata' + fileparts[-1]
            else                 : newFile = filename

            #write out vars to file, one line each var
            newFile = newFile.replace('//','/')
            ofile.write(newFile+'\n')
            ofile.write(dateObs+'\n')
            ofile.write(utc+'\n')
            ofile.write(outdir+'\n')
            ofile.write(observer+'\n')
            ofile.write(str(fileno)+'\n')
            ofile.write(imagetyp+'\n')

            #if PROGNAME exists, use that to populate the following
            try:
                progname = header.get('PROGNAME')
                if progname == None:
                    progname = header['PROGID']
            except KeyError:
                ofile.write('PROGNAME\n')
                ofile.write('PROGPI\n')
                ofile.write('PROGINST\n')
                ofile.write('PROGTITL\n')
            else:
                progname = progname.strip()
                ofile.write(progname + '\n')

                # Get the viewing semester from obs-date
                instrObj.set_semester()
                sem = header['SEMESTER'].strip()

                # Get the program ID
                ktn = ''.join((sem, '_', progname))

                # Get the program information from the program ID
                progpi, proginst, progtitl = get_prog_info(ktn)                   
                if 'Usage' in progpi  : ofile.write('PROGPI\n')
                else                  : ofile.write(progpi+'\n')
                if 'Usage' in proginst: ofile.write('PROGINST\n')
                else                  : ofile.write(proginst+'\n')
                if 'Usage' in progtitl: ofile.write('PROGTITL\n')
                else                  : ofile.write(progtitl+'\n')

            #write OA last
            ofile.write(oa + '\n')

    if log: log.info('create_prog: finished, {} created'.format(outfile))


def get_prog_info(ktn):
    """
    Retrives the program PI, allocating institution,
    and title from the proposals database web API

    @type ktn: string
    @param ktn: the program ID - consists of semester and progname (ie 2017B_U428)
    """
    url = 'http://www.keck.hawaii.edu/software/db_api/proposalsAPI.php?ktn='+ktn+'&cmd='
    progpi   = urlopen(url+'getPI').read().decode('utf8')
    proginst = urlopen(url+'getAllocInst').read().decode('utf8')
    progtitl = urlopen(url+'getTitle').read().decode('utf8')

    #remove whitespace from progpi str (this would mess up newproginfo.txt columns)
    progpi = progpi.replace(' ','')
    if (',' in progpi): 
        progpi = progpi.split(',')[0]

    return progpi, proginst, progtitl
