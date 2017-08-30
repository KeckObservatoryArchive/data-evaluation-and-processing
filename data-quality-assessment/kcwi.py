import argparse
import os
from astropy.io import fits
from PIL import Image
import os
import matplotlib.pyplot as plt
from math import pi
from math import cos
from math import sin
import numpy as np


def make_jpg(filePath):
    '''
    Converts a FITS file to JPG image

    Parameters
    ----------
    filePath : string
	   Full path directory of FITS file
    '''

    path = os.path.dirname(filePath)
    filename = os.path.basename(filePath)[:-5]

    image = fits.getdata(filePath)

    plt.imshow(image, cmap='gray')
    plt.axis('off')
    plt.savefig(path + '/' + filename + '.png')
    Image.open(path + '/' + filename + '.png').save(path + '/' + filename + '.jpg')
    os.remove(path + '/' + filename + '.png')


def config(camera, gratname, slicer, binning):
    '''
    Determines KOA keywords based on KCWI configurations

    Parameters
    ----------
    camera : string
        Detector name. Blue or FPC
    gratName : string
        Name of grating
    slicer : string
        Position of slicer
    binning : string
        binning ratio
    '''

    camera = camera.lower()
    gratname = gratname.lower()
    slicer = slicer.lower()

    configurations = {'bl': {'waves': (3500, 4550, 5600), 'large': 900, 'medium': 1800, 'small': 3600},
					'bm': {'waves': (3500, 4500, 5500), 'large': 2000, 'medium': 4000, 'small': 8000},
					'bh3': {'waves': (4700, 5150, 5600), 'large': 4500, 'medium': 9000, 'small': 18000},
					'bh2': {'waves': (4000, 4400, 4800), 'large': 4500, 'medium': 9000, 'small': 18000},
					'bh1': {'waves': (3500, 3800, 4100), 'large': 4500, 'medium': 9000, 'small': 18000},
					'plate scale': {'fpc': 0.0075, 'blue': 0.147},
					'slits': {'large': '1.35', 'medium': '0.69', 'small': '0.35'}
					}

	if camera in configurations['plate scale']:
		binRatio = binning.split(',')
		dispscal = configurations['plate scale'].get(camera) * int(binRatio[0])
		spatscal = dispscal
	else:
		dispscal = 'null'
		spatscal = 'null'

	if slicer in configurations['slits']:
		slitwidt = configurations['slits'].get(slicer)
		slitlen = 20.4
	else:
		slitwidt = 'null'
		slitlen = 'null'

	if gratname in configurations.keys() and slicer in configurations['slits'].keys():
		waveblue = configurations.get(gratname)['waves'][0]
		wavecntr = configurations.get(gratname)['waves'][1]
		wavered = configurations.get(gratname)['waves'][2]
		specres = configurations.get(gratname)[slicer]
	else:
		waveblue = 'null'
		wavecntr = 'null'
		wavered  = 'null'
		specres  = 'null'

	return waveblue, wavecntr, wavered, specres, spatscal, dispscal, slitwidt, slitlen

def wcs(ra, dec, naxis1, naxis2, rotmode, parantel, parang, el, binning, equinox):
	'''
	Computes WCS keywords

	Parameters
    	----------
	All parameters are keyword strings from the header object
	'''

	if not parantel:
		parantel = parang

	modes = {'posi': pa,
		'vert': pa + parantel,
		'stat': pa + parantel - el,
		}

	pa1 = modes.get(rotmode[:4])
	paZero = 0.7
	pa = -(pa1 - paZero) * (pi/180)

	raKey = [float(i) for i in ra.split(':')]
	crval1 = (rakey[0] + rakey[1]/60 + rakey[2]/3600) * 15

	decKey = [float(i) for i in dec.split(':')]
	if decKey[0] >= 0:
		crval2 = decKey.split[0] + decKey[1]/60 + decKey[2]/3600
	else:
		crval2 = -(decKey.split[0] + decKey[1]/60 + decKey[2]/3600)

	pixScale = 0.0075 * binning.split(',')[0]
	cd1_1 = -(pixScale*cos(pa)/3600)
	cd2_2 = (pixScale *cos(pa)/3600)
	cd2_1 = -(pixScale*sin(pa)/3600)
	cd2_2 = -(pixScale*sin(pa)/3600)

	crpix1 = (naxis1+1)/2.
	crpix2 = (naxis2+1)/2.

	if equinox == 2000.0:
		radecsys = 'FK5'
	else:
		radecsys = 'FK4'

	return, cd1_1, cd2_2, cd2_1, cd2_2, crpix1, crpix2, crval1, crval2, pixScale, radecsys

def image_stats(data, naxis1, naxis2):
	'''
	Calculates basic image statistics

	Parameters
   	----------
	data : numpy array
		Raw image data from data object

	naxis1 and naxis are keyword strings from header object
	'''

	x = naxis1/2
	y = naxis2/2

	image = data[x-15:x+15,y-15:y+15]
	imageMean = np.mean(image)
	imageStdV = np.std(image)
	imageMedian =  np.median(image)

	return imageMean, imageStdV, imageMedian
