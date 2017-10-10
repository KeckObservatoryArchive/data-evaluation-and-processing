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


def config(keywords):
    '''
    Determines KOA keywords based on KCWI configurations

    Parameters
    ----------
	keywords : dict
		FITS header keywords
    '''

    camera = keywords['CAMERA'].lower()
    gratname = keywords['BGRATNAME'].lower()
    slicer = keywords['SLIT'].lower()

    configurations = {'bl': {'waves': (3500, 4550, 5600), 'large': 900, 'medium': 1800, 'small': 3600},
					'bm': {'waves': (3500, 4500, 5500), 'large': 2000, 'medium': 4000, 'small': 8000},
					'bh3': {'waves': (4700, 5150, 5600), 'large': 4500, 'medium': 9000, 'small': 18000},
					'bh2': {'waves': (4000, 4400, 4800), 'large': 4500, 'medium': 9000, 'small': 18000},
					'bh1': {'waves': (3500, 3800, 4100), 'large': 4500, 'medium': 9000, 'small': 18000},
					'plate scale': {'fpc': 0.0075, 'blue': 0.147},
					'slits': {'large': '1.35', 'medium': '0.69', 'small': '0.35'}
					}

	if camera in configurations['plate scale']:
		binRatio = keywords['BINNING'].split(',')
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

	keywords['WAVEBLUE'] = waveblue
	keywords['WAVECNTR'] = wavecntr
	keywords['WAVERED'] = wavered
	keywords['SPECRES'] = specres
	keywords['SPATSCAL'] = spatscal
	keywords['DISPSCAL'] = dispscal
	keywords['SLITWIDT'] = slitwidt
	keywords['SLITLEN'] = slitlen

def wcs(keywords):
	'''
	Computes WCS keywords

    Parameters
    ----------
	keywords : dict
		FITS header keywords
    '''

	if 'PARANTEL' not in keywords:
		parantel = keywords['PARANG']
	else:
		parantel = keywords['PARANTEL']

	pa = keywords['PA']

	modes = {'posi': pa,
			'vert': pa + parantel,
			'stat': pa + parantel - keywords['EL'],
			}

	pa1 = modes.get(keywords['ROTMODE'][:4])
	paZero = 0.7
	pa = -(pa1 - paZero) * (pi/180)

	raKey = [float(i) for i in keywords['RA'].split(':')]
	crval1 = (rakey[0] + rakey[1]/60 + rakey[2]/3600) * 15

	decKey = [float(i) for i in keywords['DEC'].split(':')]
	if decKey[0] >= 0:
		crval2 = decKey.split[0] + decKey[1]/60 + decKey[2]/3600
	else:
		crval2 = -(decKey.split[0] + decKey[1]/60 + decKey[2]/3600)

	pixelScale = 0.0075 * keywords['BINNING'].split(',')[0]
	cd1_1 = -(pixelScale*cos(pa)/3600)
	cd1_2 = (pixelScale *cos(pa)/3600)
	cd2_1 = -(pixelScale*sin(pa)/3600)
	cd2_2 = -(pixelScale*sin(pa)/3600)

	crpix1 = (keywords['NAXIS1']+1)/2.
	crpix2 = (keywords['NAXIS2']+1)/2.

	if keywords['EQUINOX'] == 2000.0:
		radecsys = 'FK5'
	else:
		radecsys = 'FK4'

	keywords['CD1_1'] = cd1_1
	keywords['CD1_2'] = cd1_2
	keywords['CD2_1'] = cd2_1
	keywords['CD2_2'] = cd2_2
	keywords['CRPIX1'] = crpix1
	keywords['CRPIX2'] = crpix2
	keywords['CRVAL1'] = crval1
	keywords['CRVAL2'] = crval2
	keywords['CD1_1'] = pixelScale
	keywords['RADECSYS'] = radecsys

def image_stats(keywords, data):
	'''
	Calculates basic image statistics

    Parameters
    ----------
	keywords : dict
		FITS header keywords
	data : nummpy array
		FITS image data
    '''

	x = keywords['NAXIS1']/2
	y = keywords['NAXIS2']/2

	image = data[x-15:x+15,y-15:y+15]
	imageMean = np.mean(image)
	imageStdV = np.std(image)
	imageMedian =  np.median(image)

	keywords['IMAGEMD'] = imageMean
	keywords['IMAGEMN'] = imageMedian
	keywords['IMAGESD'] = imageStdV

def go(keywords, data, filename):
	# All functions are executed in sequential order
	image_stats(keywords, data)
	wcs(keywords)
	config(keywords)
	make_jpg(filename)
