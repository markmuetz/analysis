import os
import sys
from glob import glob
import datetime as dt
from collections import OrderedDict

import matplotlib
matplotlib.use('Agg')
import numpy as np
import pylab as plt
import iris

from utils import get_cube

from consts import Re, L, cp, g


class ProfileAnalyzer(object):
    #ARCHER_BASE_DIR = '/work/n02/n02/{}/cylc-run/{}/share/data/history/{}/'
    ARCHER_BASE_DIR = '/nerc/n02/n02/{}/um10.7_runs/archive/{}/share/data/history/{}/'
    PP2_FILE_GLOB = 'atmos.???.pp2'

    @staticmethod
    def get_files(user, suite, expt):
        directory = ProfileAnalyzer.get_directory(user, suite, expt)
        return sorted(glob(os.path.join(directory, ProfileAnalyzer.PP2_FILE_GLOB)))

    @staticmethod
    def get_directory(user, suite, expt):
        return os.path.join(ProfileAnalyzer.ARCHER_BASE_DIR.format(user, suite, expt))

    def __init__(self, user, suite, expt, pp2_file, results_dir):
        self.user = user
        self.directory = self.get_directory(user, suite, expt)
        self.suite = suite
        self.expt = expt
        self.pp2_file = os.path.join(self.directory, pp2_file)
        self.results_dir = results_dir
        self.name = '{}_{}'.format(suite, os.path.basename(self.pp2_file))
        self.results = OrderedDict()

    def already_analyzed(self):
        return os.path.exists(self.pp2_file + '.analyzed')

    def append_log(self, message):
        with open(self.pp2_file + '.analyzed', 'a') as f:
            f.write('{}: {}\n'.format(dt.datetime.now(), message))

    def load(self):
        """Load iris cube list into self.dump, rename if omnium available."""
        self.append_log('Loading')
        self.pp2 = iris.load(self.pp2_file)

        try:
            import omnium as om
            stash = om.Stash()
            stash.rename_unknown_cubes(self.dump, True)
        except:
            self.say('Cannot rename cubes')
        self.append_log('Loaded')

    def _plot_uv(self):
        name = self.name
        u_profile = self.results['u_profile']
        v_profile = self.results['v_profile']
        u_heights = self.u_heights
        plt.figure(name + '_uv_profile')
        plt.clf()
        plt.title(name + '_uv_profile')

        plt.plot(u_profile.data, u_heights, 'g-', label='u')
        plt.plot(v_profile.data, u_heights, 'b--', label='v')

        plt.ylabel('height (m)')
        plt.xlabel('(m s$^{-1}$)')

        plt.legend()
        plt.savefig(os.path.join(self.results_dir, name + '_uv_profile.png'))

    def _plot_momentum_flux(self):
        name = self.name
        u_mom_flux_ts = self.u_mom_flux_ts
        v_mom_flux_ts = self.v_mom_flux_ts
        z = u_mom_flux_ts.coord('level_height').points

        plt.figure(name + '_momentum_flux_profile')
        plt.clf()
        plt.title(name + '_momentum_flux_profile')

        plt.plot(u_mom_flux_ts.data.mean(axis=0), z, 'g-', label='u')
        plt.plot(v_mom_flux_ts.data.mean(axis=0), z, 'b--', label='v')
        plt.ylabel('height (m)')
        plt.xlabel('mom flux (kg m$^{-1}$ s$^{-2}$)')
        plt.legend()
        plt.savefig(os.path.join(self.results_dir, name + '_momentum_flux_profile.png'))

    def run(self):
        self.append_log('Analyzing')
        pp2 = self.pp2

        u = get_cube(pp2, 0, 2)
        v = get_cube(pp2, 0, 3)
        u_profile = u.collapsed(['time', 'grid_latitude', 'grid_longitude'], iris.analysis.MEAN)
        v_profile = v.collapsed(['time', 'grid_latitude', 'grid_longitude'], iris.analysis.MEAN)
        self.u_heights = u.coord('level_height').points

        self.results['u_profile'] = u_profile
        self.results['v_profile'] = v_profile

        u_inc = get_cube(pp2, 53, 185)
        v_inc = get_cube(pp2, 53, 186)
        rho = (get_cube(pp2, 0, 253) / Re ** 2)

        u_inc_ts = u_inc.collapsed(['grid_latitude', 'grid_longitude'], iris.analysis.MEAN)
        v_inc_ts = v_inc.collapsed(['grid_latitude', 'grid_longitude'], iris.analysis.MEAN)
        rho_ts = rho.collapsed(['grid_latitude', 'grid_longitude'], iris.analysis.MEAN)

        theta = get_cube(pp2, 0, 4)
        z = theta.coord('level_height').points
        dz = z[1:] - z[:-1]

        #dz3d = dz.repeat(u_inc.shape[1] * u_inc.shape[2]) \
                 #.reshape(u_inc.shape[0] - 1, u_inc.shape[1], u_inc.shape[2])
        dz_ts = dz.repeat(u_inc_ts.shape[0]).reshape(*u_inc_ts.shape)
        dt = 30 # delta_t = 30s.
        self.u_mom_flux_ts = rho_ts * u_inc_ts * dz_ts / dt
        self.v_mom_flux_ts = rho_ts * v_inc_ts * dz_ts / dt

        start_time = u_inc_ts.coord('time').points[0]
        self.times = u_inc_ts.coord('time').points - start_time

        self.results['u_mom_flux_ts'] = self.u_mom_flux_ts
        self.results['v_mom_flux_ts'] = self.v_mom_flux_ts

        self.append_log('Analyzed')

    def save(self):
        self.append_log('Saving')
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)

        cubelist_filename = os.path.join(self.results_dir, self.name + '_profile_analysis.nc')
        cubelist = iris.cube.CubeList(self.results.values())

        self._plot_uv()
        self._plot_momentum_flux()
        plt.close('all')

        iris.save(cubelist, cubelist_filename)
        self.append_log('Saved')

    def say(self, message):
        """Speak out loud."""
        print(message)


def main(user, expts, suite, results_dir):
    for expt in expts:
        print(expt)
        for pp2_file in ProfileAnalyzer.get_files(user, suite, expt):
            pa = ProfileAnalyzer(user, suite, expt, os.path.basename(pp2_file), results_dir)
            if pa.already_analyzed():
                print('{} already analyzed'.format(dump_file))
                continue
            pa = ProfileAnalyzer(user, suite, expt, os.path.basename(pp2_file), results_dir)
            pa.load()
            pa.run()
            pa.save()


if __name__ == '__main__':
    user = os.path.expandvars('$USER')
    suite = os.path.expandvars('$CYLC_SUITE_NAME')
    results_dir = os.path.expandvars('$DATAM')
    main(user, sys.argv[1:], suite, results_dir)
