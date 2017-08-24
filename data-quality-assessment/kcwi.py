import argparse
import os
from astropy.io import fits
from PIL import Image
import os
import matplotlib.pyplot as plt


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
    binning = binning

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
