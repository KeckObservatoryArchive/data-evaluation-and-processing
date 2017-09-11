import get_header
from glob import glob
import kcwi

files = glob('*.fits*')
for file in files:
    header = get_header.HDU(file)
    instr = header.instr
    
    # Instrument specific functions
    if instr == 'NIRSPEC':
        header.nirspec()
    elif instr == 'KCWI':
        header.kcwi()
        kcwi.make_jpg(file)
        stats = kcwi.image_stats(header.data, header.naxis1, header.naxis2)
        # kcwi.wcs(...)
        # kcwi.config(...)        
    else:
        # Do something
        pass
