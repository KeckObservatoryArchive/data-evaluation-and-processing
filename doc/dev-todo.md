(NOTE: This is an uber detailed list of development TODOs.)
(NOTE: High level todos also listed in github projects page.)  


##LRIS
- todo: do we need to compare raw vs idl processed header keywords to see what keywords are added?  I only see set_wcs adding keywords.
- todo: JPG creation, see IDL?
- issue: lris blue and amplist for get_numamps
- Issue: Image mean, median, std are not always exact but within one decimal typically so we are calling this good.
- Issue: IDL code looks to incorrectly use CCDGN01-04 keywords with LRISBLUE. LRIS(red) ok.  Code writes CCDGN00 to header but not to metadata.  And it does not write CCDGN04 to header and puts null val in metadata. We are mimicing this behavior.  We could fix by added a CCDGN00 keyword (same for CCDRN01-04)
- Issue: SIG2NOIS keyword off a bit, but we have decided to get rid of this keyword entirely anyway so not debugging for now.  Need to ask IPAC to remove.
- bug fix: satVal changed to 65535 and that seems to fix the problem of NPIXSAT, but idl code has logic where it adds 32786 to image values and checks for >= 65535.  Not sure if this data wraps around or not as it would in python with uint16.
- bug fix: set_npixsat and set_wcs also needed fix in loop which was skipping last entension
- issue: In order to mimic IDL behavior in image stats, we are not subtracting 1 from AMPLOC. This means read images will have null values for IM01MN02 and IM02MN04 in metadata but header will have these values.
- NOTE: IDL has instances of adding 32768 to image before calling image stats.  This is an IDL issue, not needed in python.
- NOTE: IDL division is integer division and you need '//' in python3 to mimic.
- NOTE: IDL array indexing is inclusive while python is not.  ie idl image[4:8, 2:4] == python image[4:9, 2:5]
- NOTE: Elysia fixed bug in IDL code was incorrectly not truncating the wavelength range bc the dichroic wavelength is in nanometers and the wavelength range is in angstroms.
- add ofname



## HIGH PRIORITY
- Update NIRES live DEP with new version?
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






