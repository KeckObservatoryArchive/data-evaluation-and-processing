
import sys
import pdb
sys.path.append('..')
import metadata
import os
from glob import glob

INST_MAPPING = { 
                 'DEIMOS': {'DE', 'DF'},
                 'ESI': {'EI'},
                 'HIRES': {'HI'},
                 'KCWI': {'KB', 'KF'}, 
                 'LRIS': {'LB', 'LR'},
                 'MOSFIRE': {'MF'},
                 'OSIRIS': {'OI', 'OS'},
                 'NIRES': {'NR', 'NI', 'NS'},
                 'NIRC2': {'N2', 'NC'},
                }
#  extra data needed to pass all assertions
EXTRA_DATA = {
'PROPINT': 18,
'PROPINT1': 18,
'PROPINT2': 18,
'PROPINT3': 18,
'PROPMIN3': 18,
'PROPMIN': -999,
'PROPINT': 8,
'FILESIZE_MB': 0.0,
'OFNAME': 'ofNamePlaceholder',
'PROGTITL': '',
}

if __name__=='__main__':
    outDir = 'out'
    keywordTablePath = os.path.join(os.pardir, os.pardir, 'KeywordTables')
    fitsFilePath = os.path.join(os.getcwd(), os.pardir, os.pardir, 'fits')
    if not os.path.exists(outDir): 
        os.mkdir(outDir)

    for inst in INST_MAPPING.keys():
        keywordsDefFile = glob(os.path.join(keywordTablePath, f'KOA_{inst}_Keyword_Table.txt'))[0]
        metaOutFile = os.path.join(os.getcwd(), outDir, f'dep_{inst}.metadata.table') # must end in metadata.table

        metadata.make_metadata(keywordsDefFile, metaOutFile, fitsFilePath, EXTRA_DATA)
        metadata.create_md5_checksum_file(metaOutFile)

