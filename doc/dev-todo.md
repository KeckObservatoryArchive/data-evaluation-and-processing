(NOTE: This is an uber detailed list of development TODOs.)
(NOTE: High level todos also listed in github projects page.)  



##LRIS
- todo: Chris recommends we fix WCS


## HIGH PRIORITY
- Change DEP to look for optional full semid in progname/progid.  (ie 2019A_C123)
- How do we keep track of new sdata dirs?  A: Added by Jchock and we aren't necessarily notified.  Need better system.
- Overhaul scrubber checks system (which verifies data has been archived before deleting from sdata).
- Q: Do we need 'ls -d' calls to ensure refresh of sdata mounts?  Possibly not.
- Put in check/warning if cron/run is at a different hour than self.endTime 
- Need end of day cron to ensure all instruments processing ran and completed (query koatpx?)
- Find and fix remaining hard-coded API URLS.
- Search TODOs in code
- Improve documentation


## LOW PRIORITY
- See instr_lris.py for examples of condensed or streamlined functions that we can either apply to other instr_* files or create shared functions.
- Increase PROGPI colwidth to 48 and do First + Last Name?
- READ env data file once instead of every image.  
- Look at old Missing Data tables usage
- Metadata graph demo with Pyviz + jupyter notebook
- Add "duplicate metadata keyword" check.  What to do? (ok if same val, otherwise ?)
- Make get_dir_list more readable (use glob function?) (just list them) (put in config)
- Review all koatpx columns vs which ones we touch and when (ie zero files)
- Improve logging, email reporting and error handling.


## MISC IDEAS
- Change processing steps to classes and have them create their own instrObj, log, etc.  Move common to processing base class and maybe get rid of common.py?
- Make instrument.py a better base class; denote which functions/vars must be defined abstract methods.
- Do instrObj header fixes up front so we can just refer to things in the header as header['name']?
- Change back to instrument.py and subclasses as a FITS service class (ie not holding current fits file etc)?
- Command line option for dir removal and tpx removal if running manually?
- Create command line options to force program assignment by outdir or timerange.
- Processing instructions for sub-steps (ie just running make_fits_extension_metadata_files)
- Make more functions as independent processing steps instead of dependent on self.
- Pull out metadata from DQA so it can be run as independent step after DQA? 
- Change keyword metadata defs to database tables?  Coordinate with IPAC.
- Change instr classes to use wildcard for locate dirs (see dep_locate.csh, ie set subdir = 'sdata7*/esi*')


## REGRESSION TESTING
- Create test directory with collection of sample non-proprietary FITS files and corresponding "gold standard" DEP output for comparison.
- Create test script to validate DEP against sample FITS test directory.






