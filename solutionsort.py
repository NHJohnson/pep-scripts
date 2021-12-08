#!/usr/bin/env python

""" Distribute the parameter estimates in a PEP solution file
    amongst the initial-condition files for iteration
"""

import argparse
import sys
import glob
import re
import shutil
from datetime import datetime

def to_file(line, path):
    """ Write a line to a file 
        This is done in 'add' mode
     """
    with open(path, 'a') as f:
        f.write(line)

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--initextension', default='mod3', 
                        help='extension of parameter files to be used initially')
    parser.add_argument('-o', '--newextension', default='nhj1',
                        help='extension of parameter files to be written to')
    parser.add_argument('-s', '--solutionfile')

    args = parser.parse_args()
    initextension = args.initextension
    newextension = args.newextension
    solutionpath = args.solutionfile

    if newextension in ('mod3', 'lock5'):
        raise IOError('This script prevents you from modifying mod3 or lock5 files; '
                      'specify some new or different extension')

    nameflag = 0
    siteflag = 0
    spotflag = 0
    biasflag = 0

    currenttime = datetime.now()
    timestamp = '%s_%s_%s_%s_%s' % (currenttime.year, currenttime.month, 
            currenttime.day, currenttime.hour, currenttime.minute)

    if initextension != newextension:
        modlist = glob.glob('pepin/*.%s' % initextension)
        for modfile in modlist:
            newfile = '.'.join(modfile.split('.')[:-1] + [newextension])
            shutil.copyfile(modfile, newfile)

    newfilelist = glob.glob('pepin/*.%s' % newextension)
    for newfile in newfilelist:
        with open(newfile, 'a') as new:
            new.write('$ sol '+timestamp+'\n')

    sscon = 'pepin/sscon.%s' % newextension

    with open(solutionpath, 'r') as solfile:

        for line in solfile:
            if 'OBJECT' in line:
                continue
            if 'END' in line:
                break
            if 'PRMTER' in line:
                to_file(line, sscon)
                # Force beta' and gamma' to follow beta and gamma
                prmstring = re.search('PRMTER\( *(\d+)\)', line)
                prmnum = int(prmstring.group(1))
                if prmnum == 41:
                    # newline = re.sub('PRMTER\( *\d+\)', 'PRMTER( 43)', line)
                    if line[9:11] == '41': 
                        # what circumstances are differentiated by this logic
                        # is no longer clear to me. -NHJ
                        to_file(' PRMTER( 43)=' + line[13:36] + '\n', sscon)
                    else:
                        to_file(' PRMTER( 43)=' + line[49:], sscon)
                elif prmnum == 42:
                    if line[9:11] == '42':
                        to_file(' PRMTER( 44)=' + line[13:36] + '\n', sscon)
                    else:
                        to_file(' PRMTER( 44)=' + line[49:], sscon)
                elif prmnum == 43:
                    if line[9:11] == '43':
                        to_file(' PRMTER( 41)=' + line[13:36] + '\n', sscon) 
                    else:
                        to_file(' PRMTER( 41)=' + line[49:], sscon)
                elif prmnum == 44: 
                    if line[9:11] == '44':
                        to_file(' PRMTER( 42)=' + line[13:36] + '\n', sscon) 
                    else:
                        to_file(' PRMTER( 42)=' + line[49:], sscon)

            if 'NAME' in line:
                nameflag = 1
                parts = line.split("'")
                bodyname = parts[1].strip().lower()
                continue
            elif 'SITES' in line:
                siteflag = 1
                continue
            elif 'SPOTS' in line:
                spotflag = 1
                continue
            elif 'BIASES' in line:
                biasflag = 1
                continue

            if biasflag:
                if line[0].isdigit():
                    outfile = 'pepin/mpfbias.%s' % newextension
                else:
                    outfile = 'pepin/moonbias.%s' % newextension
            elif spotflag:
                if line[5:7] == '10':
                    outfile = 'pepin/moonspot.%s' % newextension
                    altline = line[:65] + '0 0 0\n'
                    to_file(altline, 'pepin/mnfxspot.%s' % newextension)
                elif line.startswith('VKL'):
                    outfile = 'pepin/lander.%s' % newextension
                    altline = line[:65] + '0 0 0\n'
                    to_file(altline, 'pepin/fixlandr.%s' % newextension)
                elif line.startswith('MPFR'):
                    outfile = 'pepin/mpfl.%s' % newextension
            elif siteflag:
                outfile = 'pepin/moonsite.%s' % newextension
            elif nameflag:
                if not ('D+' in line or 'D-' in line):
                    continue
                outfile = 'pepin/%s.%s' % (bodyname, newextension)            
            else:
                continue

            to_file(line, outfile)
