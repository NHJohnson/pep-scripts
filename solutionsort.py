#!/usr/bin/env python

import sys
import glob
import shutil
import datetime

if len(sys.argv) < 2:
	print 'Need to supply four-letter extension of existing initial-condition files, exiting ...'
	sys.exit()

extension = sys.argv[1]

solfile = open('pepin/newicinfo.txt', 'r')
nameflag = 0
siteflag = 0
spotflag = 0
biasflag = 0

now = datetime.datetime.now()
date = str(now)
timestamp = date[0:10]+'_'+date[11:13]+'-'+date[14:16]+'-'+date[17:19]

if extension == 'mod3':
	modlist = glob.glob('pepin/*.'+extension)
	for modfile in modlist:
		shutil.copyfile(modfile, modfile[:-5]+'.nhj1')
newfilelist = glob.glob('pepin/*.nhj1')
for nhjfilename in newfilelist:
	nhjfile = open(nhjfilename, 'a')
	nhjfile.write('$ sol '+timestamp+'\n')
	nhjfile.close() 

for line in solfile:
	if 'OBJECT' in line:
		continue
	if 'END' in line:
		break
	if 'PRMTER' in line:
		ssconfile = open('pepin/sscon.nhj1', 'a')
                ssconfile.write(line)
                if 'PRMTER( 41)' in line: # This section should force the values of beta' and gamma' to follow those of beta and gamma, as is necessary.
                        if line[9:11] == '41':
                                ssconfile.write(' PRMTER( 43)=' + line[13:36] + '\n')
                        else:
                                ssconfile.write(' PRMTER( 43)=' + line[49:])
                if 'PRMTER( 42)' in line:
                        if line[9:11] == '42':
                                ssconfile.write(' PRMTER( 44)=' + line[13:36] + '\n')
                        else:
                                ssconfile.write(' PRMTER( 44)=' + line[49:])
		if 'PRMTER( 43)' in line: # This section should force the values of beta and gamma to follow those of beta' and gamma', as is necessary.
			if line[9:11] == '43':
				ssconfile.write(' PRMTER( 41)=' + line[13:36] + '\n') 
			else:
				ssconfile.write(' PRMTER( 41)=' + line[49:])
                if 'PRMTER( 44)' in line: 
                        if line[9:11] == '44':
                                ssconfile.write(' PRMTER( 42)=' + line[13:36] + '\n') 
                        else:
                                ssconfile.write(' PRMTER( 42)=' + line[49:])
		ssconfile.close()
	if 'NAME' in line:
		nameflag = 1
		parts = line.split("'")
		bodyname = parts[1].strip()
		bodyname = bodyname.lower()
		currentfile = 'pepin/'+bodyname+'.nhj1'
		continue
	elif 'SITES' in line:
		nameflag = 0
		siteflag = 1
		currentfile = 'pepin/moonsite.nhj1'
		continue
	elif 'SPOTS' in line:
		nameflag = 0
		siteflag = 0
		spotflag = 1
		continue
	elif 'BIASES' in line:
		nameflag = 0 
		siteflag = 0
		spotflag = 0
		biasflag = 1
		continue	
	if nameflag:
		if ('D-' in line or 'D+' in line):
			nhjfile = open(currentfile, 'a')
			nhjfile.write(line)
			nhjfile.close()
	elif siteflag:
		nhjfile = open(currentfile, 'a')
		nhjfile.write(line)
		nhjfile.close()
	elif spotflag: 
		if line[5:7] == '10':
			currentfile = 'pepin/moonspot.nhj1'
			altline = line[0:65]+'0 0 0\n'
#			for index in range(0, len(line)):
#				print index, line[0:index]
			nhjfile = open('pepin/mnfxspot.nhj1', 'a')
			nhjfile.write(altline)
			nhjfile.close()
		elif line[0:3] == 'VKL':
			currentfile = 'pepin/lander.nhj1'
			altline = line[0:65]+'0 0 0\n'
	                nhjfile = open('pepin/fixlandr.nhj1', 'a')
	                nhjfile.write(altline)
	                nhjfile.close()
		elif line[0:4] == 'MPFR':
			currentfile = 'pepin/mpfl.nhj1'
                nhjfile = open(currentfile, 'a')
                nhjfile.write(line)
                nhjfile.close()
	elif biasflag:
		if line[0].isdigit():
			currentfile = 'pepin/mpfbias.nhj1'
		else:
			currentfile = 'pepin/moonbias.nhj1'
                nhjfile = open(currentfile, 'a')
                nhjfile.write(line)
                nhjfile.close()

