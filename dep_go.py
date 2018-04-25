from sys import argv
import argparse
from datetime import datetime
from dep import *
import configparser

# Parse the configuration file

config = configparser.ConfigParser()
config.read('config.ini')

# Input parameters

parser = argparse.ArgumentParser(description='DEP input parameters')
parser.add_argument('instr', type=str, help='Instrument name')
args = parser.parse_args()
instr   = args.instr.upper()

# Use the current UT date

utDate = datetime.utcnow().strftime('%Y-%m-%d')

# TPX flag: 0 off, 1 on

tpx = 1

# Create and run Dep

try:
	dep = Dep(instr, utDate, config[instr]['ROOTDIR'], tpx)
except:
	print('Could not create Dep object')
	exit()

try:
	dep.go()
except:
	print('Error running dep.go')
	exit()