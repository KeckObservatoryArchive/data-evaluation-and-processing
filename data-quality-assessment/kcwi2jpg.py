import argparse
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

parser = argparse.ArgumentParser()
parser.add_argument('filePath', type=str, help='/net/vm-koaserver5/koadataXX/KCWI/YYYYMMDD/kcwi.fits')
args = parser.parse_args()

if __name__ == '__main__':
    make_jpg(args.filePath)
