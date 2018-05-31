=== CONTINUOUS INTEGRATION TESTING ===

Continuous Integration Testing (CIT) aims at minimizing integration time of new code and streamlining testing to catch bugs early.  

(TODO: finish description/overview)



===TESTING SETUP===

1) Download or clone DEP Github repository to your local machine: 

	https://github.com/KeckObservatoryArchive/data-evaluation-and-processing.git 


2) Create copy of 'config.ini' as 'config.live.ini', and set the following CIT variables:

	[MISC]
	METADATA_TABLES_DIR = ./cit/metadata_tables

	[CIT]
	CIT_LOCATE_DIR = ./cit/fits_files


(TODO: finish setup instructions)
