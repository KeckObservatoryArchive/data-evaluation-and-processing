import get_header
import importlib
from glob import glob

modules = ['nirspec', 'kcwi']

files = glob('*.fits*')
for file in files:
    header = get_header.HDU(file)
    instr = header.keywords['instrume'].lower()
    
    if instr in modules:
        module = importlib.import_module(instr)
        module.go(header, file)
        # Write file to lev1 directory
        # header.hdu.writeto('')   
    else:
        # Do something
        pass
