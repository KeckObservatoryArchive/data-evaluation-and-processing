from sys import argv
import argparse
from datetime import datetime
from dep import *
import configparser
from common import *


# Parse the configuration file

config = configparser.ConfigParser()
config.read('config.live.ini')

# Input parameters

parser = argparse.ArgumentParser(description='DEP input parameters')
parser.add_argument('instr', type=str, help='Instrument name')
parser.add_argument('utDate', type=str, nargs='?', default=None, help='UTC Date to search for FITS files in prior 24 hours.')
parser.add_argument('tpx', type=int, nargs='?', default=1, help='Update TPX databse?')
args = parser.parse_args()

instr  = args.instr.upper()
utDate = args.utDate
tpx    = args.tpx

# Use the current UT date if none provided

if (utDate == None): utDate = datetime.utcnow().strftime('%Y-%m-%d')

# Create and run Dep

try:
	dep = Dep(instr, utDate, config[instr]['ROOTDIR'], tpx)
	dep.go()
except Exception as error:
    do_fatal_error(repr(error), instr, utDate, 'dep_go')
