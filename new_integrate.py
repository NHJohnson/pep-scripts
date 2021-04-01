#!/usr/bin/env python3

""" Generate solar system ephemeris files """

import argparse
import glob
import os
import shutil
import subprocess

class Integrator(object):
    """ Class for keeping track of runstreams and files 
            associated with integrations
    """
    def __init__(self, runstream_name, iter_extension, fort_number, ephem_name, log_dir=None):
        """ Create a new Integrator with associated 
                runstream_name (e.g. nbodyint) and
                iter_extension (e.g. mod3)
                fort_number should be an integer corresponding to the
                    file on which the integrator output is written, e.g. 10 for fort.10
                ephem_name is the name of the ephemeris file that is created by this
                    Integrator, e.g. embary.allpart
                log_dir is a directory in which pep.out will be renamed and saved
                    If this option is not set, these files will be discarded
        """
        runstream_file = os.path.join('pepin', runstream_name+'.peprun')
        if not os.path.isfile(runstream_file):
            raise IOError('Expected runstream %s not found in pepin' % runstream_file)
        self.runstream = runstream_name
        self.iter = iter_extension
        self.fort_file = 'fort.%s' % fort_number
        self.ephem_name = ephem_name
        self.integration_count = 0
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        self.log_dir = log_dir

    def integrate(self, jd1, jd2, *args, **kwargs):
        """ Run integration for this object from jd1 to jd2 (Julian days)
            Any args and kwargs will be unpacked and added to the command
            If the PEP process returns a nonzero exit code, raises RuntimeError
        """
        if jd1 >= jd2:
            raise ValueError('Initial Julian day must be less than final one')
        command = ['pepint', self.runstream, '-iter', self.iter, 
                   '-jd1', str(jd1), '-jd2', str(jd2)]
        for arg in args:
            command.append('-'+str(arg))
        for flag, kwarg in kwargs.items():
            command += ['-'+flag, str(kwarg)]

        print(' '.join(command))
        process = subprocess.Popen(command)
        process.communicate()
        exitcode = process.returncode
        if exitcode:
            raise RuntimeError('%s failed with exit code %s' % (self.runstream, exitcode))

        self.integration_count += 1 
        if self.log_dir:
            log_name = '%s-%s.out' % (self.runstream, self.integration_count)
            os.rename('pep.out', os.path.join(self.log_dir, log_name))

    def move_ephem(self, directory):
        """ Move fort.XX file for this object to ephem_name in supplied directory
            Raises IOError if fort file not found
            Raises IOError if target file already exists
        """
        if not os.path.isfile(self.fort_file):
            raise IOError('Fort file %s from runstream %s not found' %
                           (self.fort_file, self.runstream))
        target_file = os.path.join(directory, self.ephem_name)
        if os.path.isfile(target_file):
            raise IOError('Target ephemeris file %s already exists' % target_file)
        os.rename(self.fort_file, target_file)

def remove_forts():
    """ Delete all files fort.* in the current directory """
    for fort in glob.glob('fort.*'):
        os.remove(fort)

def empty_directory(dir_name):
    """ Delete all files in target directory """
    files = glob.glob(os.path.join(dir_name, '*'))
    for f in files:
        os.remove(f)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-jd1', type=int, default=2439301,
                        help='initial Julian day, default corresp. June 24 1966')
    parser.add_argument('-jd2', type=int, default=2463601,
                        help='final Julian day, default corresp. Jan 3 2033')
    parser.add_argument('-i', '--iter', default='mod3',
                        help='extension of desired initial condition files [mod3]')
    parser.add_argument('-L', '--logdir', 
                        help='directory in which to save pep.out from integration [None]')

    args = parser.parse_args()
    jd1 = args.jd1
    jd2 = args.jd2
    iter_ext = args.iter
    log_dir = args.logdir

    if not shutil.which('pepint'):
        raise IOError('pepint not in path')

    remove_forts()
    empty_directory('ephem')
    empty_directory('newephem')

    planet_names = ['mercury', 'venus', 'embary', 'mars', 
                    'jupiter', 'saturn', 'uranus', 'neptune']
    planetary_runstreams = ['mrcryint', 'venusint', 'embryint', 'marsint', 
                            'jupint', 'satrnint', 'uranint', 'neptint']
    planetary_forts = range(11,19)
    planetary_ephemerides = ['%s.allpart' % planet for planet in  planet_names]

    save_ephem_dirs = ['i1ephem', 'i2ephem', 'i3ephem', 'i4ephem']
    output_dirs = ['tmpephem1', 'tmpephem2', 'tmpephem3', 'tmpephem4'] 
    noind_on = [True, False, False, False]

    # integrate nbody over a longer span out to 2100
    nbody = Integrator('nbodyint', iter_ext, 10, 'nbody753.2100', log_dir=log_dir)
    nbody.integrate(2429301, 2488071, ipert=0)
    nbody.move_ephem('ephem')

    # integrate nbody including moon over a shorter span
    nbodymoon = Integrator('nbdyintm', iter_ext, 10, 'nbody753.2020', log_dir=log_dir)
    nbodymoon.integrate(jd1, jd2, ipert=0)
    nbodymoon.move_ephem('ephem')

    # shrink integration interval
    jd1 += 200
    jd2 -= 200

    # create planetary integrators
    planetary_integrators = []
    for runstream, fortfile, ephemeris in \
            zip(planetary_runstreams, planetary_forts, planetary_ephemerides):
        planetary_integrators.append(Integrator(runstream, iter_ext, fortfile, 
                                                ephemeris, log_dir=log_dir))
    lunar_integrator = Integrator('moonintc', iter_ext, 20, 'moon.allpart', log_dir=log_dir)
    # no separate integration for moonrot, just need to move file
    lunar_integrator_rot = Integrator('moonintc', iter_ext, 21, 'moonrot.allpart', log_dir=log_dir)

    # iterate over planets and moon
    for backup_dir, tmp_dir, noind_status in zip(save_ephem_dirs, output_dirs, noind_on):
        if os.path.isdir(backup_dir):
            shutil.rmtree(backup_dir)
        os.makedirs(tmp_dir, exist_ok=True)
        empty_directory(tmp_dir)
        for integrator in planetary_integrators:
            if noind_status:
                integrator.integrate(jd1, jd2, 'noind')
            else:
                integrator.integrate(jd1, jd2)
            integrator.move_ephem(tmp_dir)
        jd1 += 60
        jd2 -= 60
        if os.path.isdir('newephem'):
            os.rename('newephem', backup_dir)
        os.rename(tmp_dir, 'newephem')
        lunar_integrator.integrate(jd1, jd2)
        lunar_integrator.move_ephem('newephem') #tmp_dir)
        lunar_integrator_rot.move_ephem('newephem') #tmp_dir)
        jd1 += 40
        jd2 -= 40
        # os.rename(tmp_dir, 'newephem')

    for integrator in planetary_integrators:
        if integrator.runstream == 'embryint':
            embary_integrator = integrator
            continue
        integrator.integrate(jd1, jd2)
        integrator.move_ephem('ephem')
    embary_integrator.integrate(jd1, jd2)
    embary_integrator.move_ephem('ephem')
    jd1 += 60
    jd2 -= 60
    shutil.rmtree('newephem')
    shutil.copytree('ephem', 'newephem')
    lunar_integrator.integrate(jd1, jd2)
    lunar_integrator.move_ephem('ephem')
    lunar_integrator_rot.move_ephem('ephem')
