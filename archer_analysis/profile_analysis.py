import os

import matplotlib
matplotlib.use('Agg')
import pylab as plt
import iris

from analyzer import Analyzer
from utils import get_cube
from consts import Re, L, cp, g


class ProfileAnalyzer(Analyzer):
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

    def run_analysis(self):
        cubes = self.cubes

        u = get_cube(cubes, 0, 2)
        v = get_cube(cubes, 0, 3)
        u_profile = u.collapsed(['time', 'grid_latitude', 'grid_longitude'], iris.analysis.MEAN)
        v_profile = v.collapsed(['time', 'grid_latitude', 'grid_longitude'], iris.analysis.MEAN)
        self.u_heights = u.coord('level_height').points

        self.results['u_profile'] = u_profile
        self.results['v_profile'] = v_profile

        u_inc = get_cube(cubes, 53, 185)
        v_inc = get_cube(cubes, 53, 186)
        rho = (get_cube(cubes, 0, 253) / Re ** 2)

        u_inc_ts = u_inc.collapsed(['grid_latitude', 'grid_longitude'], iris.analysis.MEAN)
        v_inc_ts = v_inc.collapsed(['grid_latitude', 'grid_longitude'], iris.analysis.MEAN)
        rho_ts = rho.collapsed(['grid_latitude', 'grid_longitude'], iris.analysis.MEAN)

        theta = get_cube(cubes, 0, 4)
        z = theta.coord('level_height').points
        dz = z[1:] - z[:-1]

        #dz3d = dz.repeat(u_inc.shape[1] * u_inc.shape[2]) \
                 #.reshape(u_inc.shape[0] - 1, u_inc.shape[1], u_inc.shape[2])
        dz_ts = dz.repeat(u_inc_ts.shape[0]).reshape(*u_inc_ts.shape)
        delta_t = 30 # 30s.
        self.u_mom_flux_ts = rho_ts * u_inc_ts * dz_ts / delta_t
        self.v_mom_flux_ts = rho_ts * v_inc_ts * dz_ts / delta_t

        start_time = u_inc_ts.coord('time').points[0]
        self.times = u_inc_ts.coord('time').points - start_time

        self.results['u_mom_flux_ts'] = self.u_mom_flux_ts
        self.results['v_mom_flux_ts'] = self.v_mom_flux_ts

    def save_analysis(self):
        self._plot_uv()
        self._plot_momentum_flux()
        plt.close('all')
