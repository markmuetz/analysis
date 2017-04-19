import os
import sys
import datetime as dt
from collections import OrderedDict

import matplotlib
matplotlib.use('Agg')
import numpy as np
import pylab as plt
import iris

from utils import get_cube

from consts import Re, L, cp, g


class MomentumFluxAnalyzer(object):
    ARCHER_BASE_DIR = '/work/n02/n02/{}/cylc-run/{}/share/data/history/{}/'
    PP2_FILE = 'atmos.024.pp2'

    @staticmethod
    def get_file(user, suite, expt):
        directory = MomentumFluxAnalyzer.get_directory(user, suite, expt)
        return os.path.join(directory, MomentumFluxAnalyzer.PP2_FILE)

    @staticmethod
    def get_directory(user, suite, expt):
        return os.path.join(MomentumFluxAnalyzer.ARCHER_BASE_DIR.format(user, suite, expt))

    def __init__(self, user, suite, expt, results_dir):
        self.user = user
        self.directory = self.get_directory(user, suite, expt)
        self.suite = suite
        self.expt = expt
        self.file = os.path.join(self.directory, self.PP2_FILE)
        self.results_dir = results_dir
        self.name = '{}_{}'.format(suite, expt)
        self.results = OrderedDict()

    def already_analyzed(self):
        return os.path.exists(self.file + '.analyzed')

    def append_log(self, message):
        with open(self.file + '.analyzed', 'a') as f:
            f.write('{}: {}\n'.format(dt.datetime.now(), message))

    def load(self):
        """Load iris cube list into self.dump, rename if omnium available."""
        self.append_log('Loading')
        self.pp2 = iris.load(self.file)

        try:
            import omnium as om
            stash = om.Stash()
            stash.rename_unknown_cubes(self.dump, True)
        except:
            self.say('Cannot rename cubes')
        self.append_log('Loaded')

    def _plot(self):
        u_mom_flux_ts = self.u_mom_flux_ts
        z = u_mom_flux_ts.coord('level_height').points
        dz = z[1:] - z[:-1]

        plt.figure(name + '_momentum_flux_profile')
        plt.clf()
        plt.title(name + '_momentum_flux_profile')

        plt.plot(u_mom_flux_ts[-1], z[:-1] + dz/2, 'g-', label='u')
        plt.ylabel('height (m)')
        plt.xlabel('mom flux (kg m$^{-2}$ s$^{-1}$)')
        plt.savefig(os.path.join(self.results_dir, name + '_momentum_flux_profile.png'))

    def run(self):
        self.append_log('Analyzing')
        pp2 = self.pp2

        tau = 25600.
        u_inc = get_cube(pp2, 53, 185)
        v_inc = get_cube(pp2, 53, 186)
        rho = get_cube(pp2, 0, 253) / Re ** 2

        u_inc_ts = u_inc.collapsed(['grid_latitude', 'grid_longitude'], iris.analysis.MEAN)
        v_inc_ts = v_inc.collapsed(['grid_latitude', 'grid_longitude'], iris.analysis.MEAN)
        rho_ts = rho.collapsed(['grid_latitude', 'grid_longitude'], iris.analysis.MEAN)

        theta = get_cube(pp2, 0, 4)
        z = theta.coord('level_height').points
        dz = z[1:] - z[:-1]

        #dz3d = dz.repeat(u_inc.shape[1] * u_inc.shape[2]) \
                 #.reshape(u_inc.shape[0] - 1, u_inc.shape[1], u_inc.shape[2])
        dz_ts = dz.repeat(u_inc_ts.shape[0]).reshape(*u_inc_ts.shape)
        self.u_mom_flux_ts = rho_ts * u_inc_ts * dz_ts

        start_time = u_inc_ts.coord('time').points[0]
        self.times = u_inc_ts.coord('time').points - start_time

        self.results['u_mom_flux_ts'] = self.u_mom_flux_ts

        self.append_log('Analyzed')

    def save(self):
        self.append_log('Saving')
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)

        cubelist_filename = os.path.join(self.results_dir, self.name + '_mom_flux_analysis.nc')
        cubelist = iris.cube.CubeList(self.results.values())

        self._plot()

        iris.save(cubelist, cubelist_filename)
        self.append_log('Saved')

    def say(self, message):
        """Speak out loud."""
        print(message)


def main(user, expts, suite, results_dir):
    for expt in expts:
        mfa = MomentumFluxAnalyzer(user, suite, expt, results_dir)
        mfa.load()
        mfa.run()
        mfa.save()


if __name__ == '__main__':
    user = os.path.expandvars('$USER')
    suite = os.path.expandvars('$CYLC_SUITE_NAME')
    results_dir = os.path.expandvars('$DATAW')
    main(user, sys.argv[1:], suite, results_dir)
