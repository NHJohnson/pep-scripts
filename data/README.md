# Observation data
This directory (peptop/data) contains all the observations used by PEP. They have the .obslib (OBS-lybe) extension. To reduce the size of the files, all partial derivatives have been stripped out,
but they will be reintroduced by the appropriate prefit (observed-calculated or O-C) step, once an integration has been done to generate the partials. Important: The Mars Odyssey and Mars Global Surveyor 
obslibs were too big for GitHub even stripped of partials, so they have been split into pieces and need to be reassembled prior to use. From the command line in this directory (after downloading and unzipping,
run:
$ cat mgs1aa mgs1ab > mgs1.obslib
$ cat ody1aa ody1ab ody1ac ody1ad > ody1.obslib
You may then delete the pieces mgs1a* and ody1a* 
