#!/usr/local/anaconda/bin/python

#import pyfits as pf
from astropy.io import fits as pf
import numpy as np
import optparse
from scipy import misc

# Script that converts a fits file to a jpg with some scaling assumptions
# It also rotates ESI images

def main(filename, instr, outdir="."):
    
    esdata=pf.getdata(filename)
    hdr=pf.getheader(filename)
     
    #Prevent turnover in images with super bright regions
    if np.mean(esdata)-40 > np.median(esdata): do_scale=False 
    else: do_scale=True    
    
    # File string parsing to get the final file.fits->file.jpg
    file1=filename.split('/')
    file2=file1[len(file1)-1]
    if '.fits' in file2: file3=file2[0:len(file2)-5]
    else: file3=file2

    if instr=='ESI': esdata=np.rot90(esdata) 
              
    # take log of data, scales better  
    esdata=np.log10(esdata)
    a=np.min(esdata)
    b=np.max(esdata)

    if do_scale:
        # required for more faint features
        linval=10.0+999.0*(esdata-float(a))/(b-a)
        im=misc.toimage(linval,cmin=0,cmax=255)
        im.save(outdir+file3+'.jpg','JPEG')    
    else: misc.imsave(outdir+file3+'.jpg',esdata)

if __name__=="__main__":
    usage ="""
%prog koaid instr outdir

need to input filename and instrument name
ex: makejpg.py ES.20111002.54826.fits ESI
or: makejpg.py ES.20111002.54826.fits ESI /home/jholt/esi/
"""
    p=optparse.OptionParser(usage=usage)
    (options,args)=p.parse_args()
    if len(args) >= 2:
        filename=args[0]
        instr=args[1] 
        if len(args) ==3: outdir=args[2]+"/"
    else:
        p.error('Wrong arguments')
    main(filename,instr,outdir)
