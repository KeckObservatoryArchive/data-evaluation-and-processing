import os
import shutil
import tarfile
import gzip
import hashlib



def dep_tar(instrObj):
    """
    This function will tar the ancillary directory, gzip that
    tarball and remove the original contents of the directory.
    """

    instrObj.log.info('dep_tar.py started for {}'.format(instrObj.dirs['anc']))


    #only do tar if /anc/ exists
    if not os.path.isdir(instrObj.dirs['anc']):
        instrObj.log.info('dep_tar: not /anc/ dir found.  Nothing to tar.')
        return
        

    # Tarball name
    tarFileName = ('anc', instrObj.utDateDir, '.tar')
    tarFileName = ''.join(tarFileName)


    # Go to directory and create tarball
    instrObj.log.info('dep_tar.py creating {}'.format(tarFileName))
    os.chdir(instrObj.dirs['anc'])
    with tarfile.open(tarFileName, 'w:gz') as tar:
        tar.add('./')


    # gzip the tarball
    instrObj.log.info('dep_tar.py gzipping {}'.format(tarFileName))
    gzipTarFile = ''.join((tarFileName, '.gz'))
    with open(tarFileName, 'rb') as fIn:
        with gzip.open(gzipTarFile, 'wb') as fOut:
            shutil.copyfileobj(fIn, fOut)


    # Remove the original tar file
    os.remove(tarFileName)


    # Create md5sum of the tarball
    md5sumFile = gzipTarFile.replace('tar.gz', 'md5sum')
    instrObj.log.info('dep_tar.py creating {}'.format(md5sumFile))
    md5 = hashlib.md5(open(gzipTarFile, 'rb').read()).hexdigest()

    with open(md5sumFile, 'w') as f:
        md5 = ''.join((md5, '  ', gzipTarFile))
        f.write(md5)


    #remove anc dirs
    dirs = ['nightly', 'udf']
    for dir in dirs:
        delDir = ''.join((instrObj.dirs['anc'], '/', dir))
        if not os.path.isdir(delDir): continue
        instrObj.log.info('dep_tar.py removing {}'.format(delDir))
        shutil.rmtree(delDir)
