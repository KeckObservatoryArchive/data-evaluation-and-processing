#
# kcwi_config.py
#
# Returns parameters based on KCWI configuration
#	waveblue
#	wavecntr
#	wavered
#	specres
#	spatscal
#	dispscal
#	slitwidt
#	slitlen
#

import argparse
import os

parser = argparse.ArgumentParser(description='Keywords from IDL')
parser.add_argument('camera')
parser.add_argument('gratname')
parser.add_argument('slicer')
parser.add_argument('binning')
args = parser.parse_args()

camera = args.camera.lower()
gratname = args.gratname.lower()
slicer = args.slicer.lower()
binning = args.binning

waveblue = 'null'
wavecntr = 'null'
wavered  = 'null'
specres  = 'null'
dispscal = 'null'
slitwidt = 'null'
slitlen  = 'null'
#
# Camera plate scale, arcsec/pixel unbinned
#
pscale = {'fpc':0.0075, 'blue':0.147}
if camera in pscale.keys():
	bin = binning.split(',')
	dispscal = pscale.get(camera) * int(bin[0])
	spatscal = dispscal

configurations = {'bl' : {'waves':(3500, 4550, 5600), 'large':900, 'medium':1800, 'small':3600},
		  'bm' : {'waves':(3500, 4500, 5500), 'large':2000, 'medium':4000, 'small':8000},
		  'bh3' : {'waves':(4700, 5150, 5600), 'large':4500, 'medium':9000, 'small':18000},
		  'bh2' : {'waves':(4000, 4400, 4800), 'large':4500, 'medium':9000, 'small':18000},
		  'bh1' : {'waves':(3500, 3800, 4100), 'large':4500, 'medium':9000, 'small':18000}
		 }

# Slit width by slicer, slit length is always 20.4"
slits = {'large':'1.35', 'medium':'0.69', 'small':'0.35'}
if slicer in slits.keys():
	slitwidt = slits[slicer]
	slitlen = 20.4

if gratname in configurations.keys() and slicer in slits.keys():
	waveblue = configurations.get(gratname)['waves'][0]
	wavecntr = configurations.get(gratname)['waves'][1]
	wavered = configurations.get(gratname)['waves'][2]
	specres = configurations.get(gratname)[slicer]

print waveblue, wavecntr, wavered, specres, spatscal, dispscal, slitwidt, slitlen
