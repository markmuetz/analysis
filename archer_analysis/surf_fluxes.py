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


class SurfFluxAnalyzer(object):
    ARCHER_BASE_DIR = '/work/n02/n02/{}/cylc-run/{}/work/20000101T0000Z/{}_atmos/'
    PP1_FILE = 'atmos.pp1'

    @staticmethod
    def get_file(user, suite, expt):
        directory = SurfFluxAnalyzer.get_directory(user, suite, expt)
        return os.path.join(directory, SurfFluxAnalyzer.PP1_FILE)

    @staticmethod
    def get_directory(user, suite, expt):
        return os.path.join(SurfFluxAnalyzer.ARCHER_BASE_DIR.format(user, suite, expt))

    def __init__(self, user, suite, expt, results_dir):
        self.user = user
        self.directory = self.get_directory(user, suite, expt)
        self.suite = suite
        self.expt = expt
        self.file = os.path.join(self.directory, self.PP1_FILE)
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
        self.pp1 = iris.load(self.file)

        try:
            import omnium as om
            stash = om.Stash()
            stash.rename_unknown_cubes(self.dump, True)
        except:
            self.say('Cannot rename cubes')
        self.append_log('Loaded')

    def _plot(self):
        name = self.name
        precip_ts = self.precip_ts
        lhf_ts = self.lhf_ts
        shf_ts = self.shf_ts
        times = self.times

        plt.figure(name + '_energy_fluxes')
        plt.clf()
        plt.title(name + '_energy_fluxes')

        plt.plot(times, lhf_ts.data, 'g-', label='LHF')
        plt.plot(times, shf_ts.data, 'r-', label='SHF')
        # TODO: fix for any time delta.
        # daily smoothing with 15 min means.
        precip_ts_smoothed = np.convolve(precip_ts.data, np.ones((96, )) / 96., mode='same')
        plt.plot(times[96:-96], precip_ts_smoothed[96:-96] * L, 'b-', label='PFE (smoothed)')
        plt.ylim((0, 400))
        plt.legend()
        plt.ylabel('flux (W m$^{-2}$)')
        plt.xlabel('time (hrs)')
        plt.savefig(os.path.join(self.results_dir, name + '_energy_fluxes.png'))

        plt.figure(name + '_water_fluxes')
        plt.clf()
        plt.title(name + '_water_fluxes')
        plt.plot(times, lhf_ts.data / L * 3600, 'g-', label='UWF')
        plt.plot(times[96:-96], precip_ts_smoothed[96:-96] * 3600, 'b-', label='Precip. (smoothed)')
        plt.plot(times, precip_ts.data * 3600, 'b--', label='Precip.')
        plt.ylim((0, 1))
        plt.legend()
        plt.ylabel('water flux (mm hr$^{-1}$)')
        plt.xlabel('time (hrs)')
        plt.savefig(os.path.join(self.results_dir, name + '_water_fluxes.png'))

    def run(self):
        """Analyze surface fluxes, plot graphs of energy/moisture fluxes."""
        self.append_log('Analyzing')
        pp1 = self.pp1

        precip = get_cube(pp1, 4, 203)
        lhf = get_cube(pp1, 3, 234)
        shf = get_cube(pp1, 3, 217)

        self.precip_ts = precip.collapsed(['grid_latitude', 'grid_longitude'], iris.analysis.MEAN)
        self.lhf_ts = lhf.collapsed(['grid_latitude', 'grid_longitude'], iris.analysis.MEAN)
        self.shf_ts = shf.collapsed(['grid_latitude', 'grid_longitude'], iris.analysis.MEAN)

        start_time = precip.coord('time').points[0]
        self.times = precip.coord('time').points - start_time

        self.results['precip_ts'] = self.precip_ts
        self.results['lhf_ts'] = self.lhf_ts
        self.results['shf_ts'] = self.shf_ts

        self.append_log('Analyzed')

    def save(self):
        """Save all results for surf flux analysis."""
        self.append_log('Saving')
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)

        cubelist_filename = os.path.join(self.results_dir, self.name + '_surf_flux_analysis.nc')
        cubelist = iris.cube.CubeList(self.results.values())

        self._plot()

        iris.save(cubelist, cubelist_filename)
        self.append_log('Saved')

    def say(self, message):
        """Speak out loud."""
        print(message)


def main(user, expts, suite, results_dir):
    for expt in expts:
        sfa = SurfFluxAnalyzer(user, suite, expt, results_dir)
        # SFA: OK!
        # TODO: reinstate.
        #if sfa.already_analyzed():
        #    print('{} already analyzed'.format(file))
        #    continue
        sfa.load()
        sfa.run()
        sfa.save()


if __name__ == '__main__':
    user = os.path.expandvars('$USER')
    suite = os.path.expandvars('$CYLC_SUITE_NAME')
    results_dir = os.path.expandvars('$DATAW')
    main(user, sys.argv[1:], suite, results_dir)
