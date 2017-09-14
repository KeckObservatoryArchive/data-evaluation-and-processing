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
    fitsname = os.path.basename(filePath)[:-5]

    image = fits.getdata(filePath)

    plt.imshow(image, cmap='gray')
    plt.axis('off')
    plt.savefig(path + '/' + fitsname + '.png')
    Image.open(path + '/' + fitsname + '.png').save(path + '/' + fitsname + '.jpg')
    os.remove(path + '/' + fitsname + '.png')


def config(header):
    '''
    Determines KOA keywords based on KCWI configurations

    Parameters
    ----------
	header : object
		header.keywords
		header.hdu
		header.data
    '''

    camera = header.keywords['camera'].lower()
    gratname = header.keywords['bgratname'].lower()
    slicer = header.keywords['slit'].lower()

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

	header.keywords['WAVEBLUE'] = waveblue
	header.keywords['WAVECNTR'] = wavecntr
	header.keywords['WAVERED'] = wavered
	header.keywords['SPECRES'] = specres
	header.keywords['SPATSCAL'] = spatscal
	header.keywords['DISPSCAL'] = dispscal
	header.keywords['SLITWIDT'] = slitwidt
	header.keywords['SLITLEN'] = slitlen

def wcs(header):
	'''
	Computes WCS keywords

    Parameters
    ----------
	header : object
		header.keywords
		header.hdu
		header.data
    '''

	if 'parantel' not in keywords:
		parantel = header.keywords['parang']
	else:
		parantel = header.keywords['parantel']

	modes = {'posi': header.keywords['pa'],
			'vert': header.keywords['pa'] + parantel,
			'stat': header.keywords['pa'] + parantel - header.keywords['el'],
			}

	pa1 = modes.get(header.keywords['rotmode'][:4])
	paZero = 0.7
	pa = -(pa1 - paZero) * (pi/180)

	raKey = [float(i) for i in header.keywords['ra'].split(':')]
	crval1 = (rakey[0] + rakey[1]/60 + rakey[2]/3600) * 15

	decKey = [float(i) for i in header.keywords['dec'].split(':')]
	if decKey[0] >= 0:
		crval2 = decKey.split[0] + decKey[1]/60 + decKey[2]/3600
	else:
		crval2 = -(decKey.split[0] + decKey[1]/60 + decKey[2]/3600)

	pixelScale = 0.0075 * header.keywords['binning'].split(',')[0]
	cd1_1 = -(pixelScale*cos(pa)/3600)
	cd1_2 = (pixelScale *cos(pa)/3600)
	cd2_1 = -(pixelScale*sin(pa)/3600)
	cd2_2 = -(pixelScale*sin(pa)/3600)

	crpix1 = (header.keywords['naxis1']+1)/2.
	crpix2 = (header.keywords['naxis2']+1)/2.

	if header.keywords['equinox'] == 2000.0:
		radecsys = 'FK5'
	else:
		radecsys = 'FK4'

	header.keywords['CD1_1'] = cd1_1
	header.keywords['CD1_2'] = cd1_2
	header.keywords['CD2_1'] = cd2_1
	header.keywords['CD2_2'] = cd2_2
	header.keywords['CRPIX1'] = crpix1
	header.keywords['CRPIX2'] = crpix2
	header.keywords['CRVAL1'] = crval1
	header.keywords['CRVAL2'] = crval2
	header.keywords['CD1_1'] = pixelScale
	header.keywords['RADECSYS'] = radecsys

def image_stats(header):
	'''
	Calculates basic image statistics

    Parameters
    ----------
	header : object
		header.keywords
		header.hdu
		header.data
    '''

	x = header.keywords['naxis1']/2
	y = header.keywords['naxis2']/2

	image = header.data[x-15:x+15,y-15:y+15]
	imageMean = np.mean(image)
	imageStdV = np.std(image)
	imageMedian =  np.median(image)

	header.keywords['IMAGEMD'] = imageMean
	header.keywords['IMAGEMN'] = imageMedian
	header.keywords['IMAGESD'] = imageStdV

def go(header):
	# All functions are executed in sequential order
	image_stats(header)
	wcs(header)
	config(header)
	make_jpg(filename)
