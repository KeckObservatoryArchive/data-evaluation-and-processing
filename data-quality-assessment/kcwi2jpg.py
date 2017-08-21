import argparse
from astropy.io import fits
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
import os

def make_jpg(filePath):
    '''
    Converts a FITS file to JPG image
    
    Parameters
    ----------
    filePath : string
	Full path directory of FITS file
    '''

    path = os.path.dirname(filePath)
    filename = filePath.split(path)[1][1:-5]

    hdu = fits.open(filePath)
    image = hdu[0].data
   
    plt.imshow(image, cmap='gray')
    plt.axis('off')
    plt.savefig(path + '/' + filename + '.png')
    Image.open(path + '/' + filename + '.png').save(path + '/' + filename + '.jpg')
    os.remove(path + '/' + filename + '.png')

parser = argparse.ArgumentParser()
parser.add_argument('filePath', type=str, help='/net/vm-koaserver5/koadataXX/KCWI/YYYYMMDD/kcwi.fits')
args = parser.parse_args()

make_jpg(args.filePath)

