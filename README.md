Data Evaluation and Processing (DEP)
====================================

### Overview ###
DEP is the process and code by which Keck science data is processed, packaged and transmitted to the Keck Observatory Archive at NexSci.

### Processing Steps ###
The DEP process is divided into the following logical steps:

<ol>
<li>obtain<br>retrieve the program information from the telescope schedule</li>
<li>locate<br>locate the instrument FITS files written to disk in the 24 hour period</li>
<li>add<br>add the focus and weather logs</li>
<li>dqa (data quality assess)<br>assess the raw FITS files and add metadata keywords</li>
<li>lev1<br>level 1 data reduction</li>
<li>tar<br>tar the ancillary directory</li>
<li>koaxfr<br>transfer the data to NExScI</li>
</ol>

### Usage ###
The DEP code is designed to run at the Keck Observatory intranet.  However, a Continuous Integration Testing option is included in this repository with test FITS files and options to run a limited test of the code.  See the "/cit/" folder for further instructions.
