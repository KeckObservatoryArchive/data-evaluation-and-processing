## PROGID assignment notes:
- dep_obtain.py gets list of programs for the instrument that night plus OA and observers list
  - NOTE: new code includes start/end times, but for old data we do not have this which affects progid assignment later.
  - NOTE: new code will run the old IDL dep_obtain if need be.
- dep_locate.py gets 24-hour FITS files list
  - NOTE: For old data reprocessing, we may not have the original raw files in their original directory structure, so we override the search dir to point to /lev0/ FITS files.  If the OUTDIR keyword does not exist, the actual FITS path will be used, but this is not the true OUTDIR now which affects progid assignment later.
- create_prog.py gathers info on a per-image basis, including OUTDIR, PROGID, PROGPI, PROGTITL, PROGINST
  - When getting OUTDIR, it first looks for keyword.  If none, then it creates one from the search file path (which is useless and misleading for processing old data that didn't have the staging dir output files.)
  - Tries to get PROGNAME/PROGID from header (processed old /lev0/ data should have PROGID)
  - FOR PROGPI/INST/TITL it also tries to get from header (for old /lev0/ data)
  - If we found a PROGID keyword, this is great and we can retrieve PROGPI/INST/TITL using this if need be.
  - Q: We use the proposals API for INST/PI and koa API for TITL here.  Why not use obtain output? Is it b/c the old dep_obtain had to deal with concatenating field values and so API is unambiguous?
  - If we don't have a PROGID from create_prog step, we will rely on dep_obtain output later in getProgInfo.py to figure this out
- getProgInfo.py will attempt various methods to figure out PROGID if it hasn't been assigned yet already.
  - Reads dep_obtain output for list of programs.
  - Reads createprog output and looks for any Engineering or ToO markers and assigns them right away.
  - If no programs, placeholders would be written for PROG* and DQA will set them to "NONE" and warn.
  - If one program, will assign to the one program for that night (skipping any that are already assigned)
  - If two or more programs:
    - Will look at each unique OUTDIR and count how many science files fall into each program by time.  If an OUTDIR has a very large percentage of files from one program, we assume that directory must belong to that program. This can produce false positives, especially if the observers forgot to switch outdirs during a split night program switch.
    - Else, will attempt to determine OUTDIR program assignment by smartly matching Observer names between Observers keyword and program Observers list.  This can produce false positives, especially if the observers forgot to re-enter their Observer list during a split night program switch.
    - Else, as a last resort, code will attempt to figure out what program each outdir belongs to using basic program start/end time ranges.  This of course can have all sorts of issues.  One is that prior to 2018, we did not have reliable program start/stop info in the database.  This was hand-logged in the schedules.splitNight table and/or in schedule.telSched.comments.  Also, the old IDL code had a bug for a while that was not assigning split nights by time correctly, so re-processing data will flag lots of mismatches.  Also of course data can be taken by one program during another programs half of the night.
    - NOTE: for processing old /lev0/ data, everything gets consolidated into one outdir so these methods will not work.  And we don't have program start/end times either, so we have no way of determining assignments.  That is why we added looking for PROG* info in header at the createprog step.
    - If PROGID assignment is inconclusive, PROGID and other PROG* keywords are set to NULL.  Warnings/Errors will be issues in email report




## PI data email notification components:
(more or less in process order)

- koa.koapi_send (koaserver DB)
  - Database table to store whether we have sent an email to PI for a program id. New record per unique SEMID. Record is re-used if consecutive nights, else new record for SEMID.)
  - See pi_status.php for simple view of koapi_send table

- dep_koapi.php
  (NEW) [KOA API]?cmd=updateKoapiSend&utdate=2018-07-21&semid=2018A_U172
  (API called each time an image is DQA'd to figure out whether to insert/update to koapi_send table.)

- ~/.forward
  - Needed email forwarding file to get mail forwarded to procmail

- ~/.procmailrc
  - (File with procmail rules)
  - Example rule:
	* ^From:.<TPX.Metadata@ipac.caltech.edu*
	* ^Subject:.[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9] KCWI
	| /kroot/archive/tpx/default/tpx_email.php KCWI ${ARCHIVE_LOCATION}/msg.${DATE} kcwi

- /kroot/archive/tpx/default/tpx_email.php
  - script called by procmail to do the email tasks

- /kroot/archive/dep/email/default/dep_pi_email.php
  - Looks at the koapi_send database table to see if any emails need to be sent out to the KOA PI's


## DEP keyword mapping explained
- instrument.py contains a dictionary var self.keywordMap with key value pairs.  
- An entry's key is how we will reference a certain keyword in the code.
- An entry's value is the actual keyword string to look for in the FITS header.  
- An entry's value can instead be an array denoting an order list of possible keyword strings to look for.
- An instrument subclass (ie instr_nires.py) can add or overwrite keywordMap entires
- Instrument.py now has a get_keyword and set_keyword functions that use keywordMap to access and modify keywords.
- A default return value can be specified in get_keyword.



## Processing Notes

How to run DEP on test data:
- Copy fits data to a test directory (use -p option to preserve timestamps)
- Clone DEP from git
- Create config.live.ini from config.ini
  - Edit ROOTDIR to point to your output directory for these test runs.
  - Edit SEARCH_DIR to point to the test directory to search for FITS files
  - Edit ADMIN_EMAIL to go to you.
  - Comment out all the KOAXFR section so you don't accidentally send stuff to IPAC
  - Optional: If you don't have appropriate timestamps on the fits files, turn on MODTIME_OVERRIDE.
- Run DEP with TPX flag off and up to tar step (don't koaxfr): python dep_go.py MOSFIRE 2019-01-20 0 obtain tar



## koatpx DB table summary:

	utdate         | date         | 
	instr          | varchar(10)  | 
	pi             | varchar(68)  | 
	files          | int(11)      | 
	files_arch     | int(11)      | 
	size           | float        | 
	sdata          | varchar(15)  | 
	ondisk_stat    | varchar(10)  | 
	ondisk_time    | varchar(15)  | 
	arch_stat      | varchar(10)  | 
	arch_time      | varchar(15)  | 
	metadata_stat  | varchar(10)  | 
	metadata_time  | varchar(15)  | 
	dvdwrit_stat   | varchar(10)  | 
	dvdwrit_time   | varchar(15)  | 
	dvdsent_stat   | varchar(10)  | 
	dvdsent_time   | varchar(15)  | 
	dvdsent_init   | char(3)      | 
	dvdsent_com    | varchar(80)  | 
	dvdstor_stat   | varchar(10)  | 
	dvdstor_time   | varchar(15)  | 
	dvdstor_init   | char(3)      | 
	dvdstor_com    | varchar(80)  | 
	tpx_stat       | varchar(10)  | 
	tpx_time       | varchar(15)  | 
	comment        | varchar(250) | 
	start_time     | varchar(15)  | 
	metadata_time2 | varchar(15)  | 
	sci_files      | int(11)      | 
	drpSent        | varchar(15)  | 
	lev1_stat      | varchar(10)  | 
	lev1_time      | varchar(15)  | 



## MISC notes:
- The NIRES echelle spectrograph (NR) and slit viewing camera (NI) are spreadsheet columns 's'=spec, 'v'=imag
- Percy Gomez is NIRES instrument master
- The new Telescope schedule API is kept alive with a cron on www that runs every 10 minutes to make sure API is running.  You can stop it with: dbServer.csh stop 50001
(Let the cron start it back up, though, until we fix the terminal issue.)

	grep "metadata check" dep_MOSFIRE_*.log | grep -v "in log" | grep -v "(ROT" | grep -v "(DDEC=" | grep -v "(DECOFF=" | grep -v "(RAOFF=" | grep -v "(DRA=" | grep -v "(TARG" | grep -v "(DEC=" | grep -v "(RA=" | grep -v "(OBJECT=" | grep -v "(MASKNAME"

	select t.Date, Instrument, Principal, ProjCode, t.Comment, s.Comment from telsched as t, splitNight as s where t.Date = s.Date and t.Instrument like '%MOSFIRE%' and ProjCode like '%/%' order by Date;
