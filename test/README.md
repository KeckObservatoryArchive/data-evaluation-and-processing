# test_metadata.py

This test script creates IPAC tables and .md5 checksum files from TAP tables taken from [this repository](https://github.com/KeckObservatoryArchive/KeywordTables).

outDir is removed after tests have run.

Each instrument is covered in a for loop. The following parameters need to be manually set.
`
fitsFilePath = '/path/to/gzipped/fits/files'
keywordTablePath = '/path/to/keyword/table/repo'
outDir = '/path/where/to/place/output/files'

Tests are run with the command
`
python test_metadata.py
`
`



