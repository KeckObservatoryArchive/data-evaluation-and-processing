from common import fixdatetime
from imagetyp_instr import imagetyp_instr
from astropy.io import fits



def create_prog(instrObj):

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

    if len(oa) >= 1: oa = oa[0]


    # Get all files
    fileList = []
    dqa_instr = stageDir + '/dqa_' + instr + '.txt'
    with open(dqa_instr, 'r') as dqa:
        for item in dqa:
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
            header = fits.getheader(filename)

            # Temp fix for bad file times(NIRSPEC legacy)
            fixdatetime(utDate, filename, header)
            imagetyp = imagetyp_instr(instr, header)
            udate = header.get('DATE-OBS').strip()
            if 'Error' in udate or udate == '':
                lastMod = os.stat(filename).st_mtime
                udate = dt.fromtimestamp(lastMod).strftime('%Y-%m-%d')

            # Fix yy/mm/dd to yyyy-mm-dd
            if '-' not in udate:
                yr, mo, dy = udate.split('/')
                seq = ('20', yr, '-', mo, '-', dy)
                udate = ''.join(seq)

            #get utc
            try:
                utc = header['UT'].strip()
            except KeyError:
                try:
                    utc = header['UTC'].strip()
                except KeyError:
                    utc = dt.fromtimestamp(lastMod).strftime('%H:%M:%S')


            #get observer
            observer = header.get('OBSERVER').strip()

            #get fileno
            fileno = instrObj.get_fileno(header)

            #get outdir
            outdir = instrObj.get_outdir(header, filename)


            fileparts = filename.split('/sdata')
            if len(fileparts) > 1: newFile = '/sdata' + fileparts[-1]
            else                 : newFile = filename

            newFile = newFile.replace('//','/')
            ofile.write(newFile+'\n')
            ofile.write(udate+'\n')
            ofile.write(utc+'\n')
            ofile.write(outdir+'\n')
            ofile.write(observer+'\n')
            ofile.write(str(fileno)+'\n')
            ofile.write(imagetyp+'\n')

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
                semester(header)
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

            ofile.write(oa + '\n')
    if log: log.info('create_prog: finished, {} created'.format(outfile))
