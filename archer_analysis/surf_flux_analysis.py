import os

import matplotlib
matplotlib.use('Agg')
import numpy as np
import pylab as plt
import iris

from analyzer import Analyzer
from utils import get_cube
from consts import L


class SurfFluxAnalyzer(Analyzer):
    """Analyze surface fluxes, plot graphs of energy/moisture fluxes."""
    analysis_name = 'surf_flux_analysis'

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

    def run_analysis(self):
        cubes = self.cubes

        precip = get_cube(cubes, 4, 203)
        lhf = get_cube(cubes, 3, 234)
        shf = get_cube(cubes, 3, 217)

        self.precip_ts = precip.collapsed(['grid_latitude', 'grid_longitude'], iris.analysis.MEAN)
        self.lhf_ts = lhf.collapsed(['grid_latitude', 'grid_longitude'], iris.analysis.MEAN)
        self.shf_ts = shf.collapsed(['grid_latitude', 'grid_longitude'], iris.analysis.MEAN)

        start_time = precip.coord('time').points[0]
        self.times = precip.coord('time').points - start_time

        self.results['precip_ts'] = self.precip_ts
        self.results['lhf_ts'] = self.lhf_ts
        self.results['shf_ts'] = self.shf_ts

    def save_analysis(self):
        """Save all results for surf flux analysis."""
        self._plot()
