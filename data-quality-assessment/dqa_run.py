import get_header
import importlib
from glob import glob

modules = ['nirspec', 'kcwi']

files = glob('*.fits*')
for filename in files:
    header = get_header.HDU(filename)
    keywords = header.keywords
    data = header.data
    instr = keywords['INSTRUME'].lower()
    
    if instr in modules:
        module = importlib.import_module(instr)
        module.go(keywords, data, filename)
        # Write file to lev1 directory
        # header.hdu.writeto('')   
    else:
        # Do something
        pass
