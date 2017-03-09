import os
import sys
from glob import glob
from collections import OrderedDict

import numpy as np
import iris

Re = 6371229.
L = 2.5e6
cp = 1004
g = 9.81


def get_cube(cubes, section, item):
    for cube in cubes:
        stash = cube.attributes['STASH']
        if section == stash.section and item == stash.item:
            return cube
    return None


class DumpAnalyzer(object):
    ARCHER_BASE_DIR = '/work/n02/n02/{}/cylc-run/{}/share/data/history/{}/'
    DUMP_FILE_GLOB = 'atmosa_da???'

    @staticmethod
    def get_files(user, suite, expt):
        directory = DumpAnalyzer.get_directory(user, suite, expt)
        return sorted(glob(os.path.join(directory, DumpAnalyzer.DUMP_FILE_GLOB)))

    @staticmethod
    def get_directory(user, suite, expt):
        return os.path.join(DumpAnalyzer.ARCHER_BASE_DIR.format(user, suite, expt))

    def __init__(self, user, suite, expt, dump_file, results_dir):
        self.user = user
        self.directory = self.get_directory(user, suite, expt)
        self.suite = suite
        self.expt = expt
        self.dump_file = os.path.join(self.directory, dump_file)
        self.results_dir = results_dir
        self.dump = iris.load(self.dump_file)
        self.name = '{}:{}'.format(suite, os.path.basename(self.dump_file))
        try:
            import omnium as om
            stash = om.Stash()
            stash.rename_unknown_cubes(self.dump, True)
        except:
            self.say('Cannot rename cubes')
            pass
        # self.results = OrderedDict()

    def run(self):
        dump = self.dump
        rho = get_cube(dump, 0, 253) / Re ** 2
        rho_d = get_cube(dump, 0, 389)

        th = get_cube(dump, 0, 4)
        ep = get_cube(dump, 0, 255)

        q = get_cube(dump, 0, 10)
        qcl = get_cube(dump, 0, 254)
        qcf = get_cube(dump, 0, 12)
        qrain = get_cube(dump, 0, 272)
        qgraup = get_cube(dump, 0, 273)

        m = get_cube(dump, 0, 391)
        mcl = get_cube(dump, 0, 392)
        mcf = get_cube(dump, 0, 393)
        mrain = get_cube(dump, 0, 394)
        mgraup = get_cube(dump, 0, 395)

        qvars = [q, qcl, qcf, qrain, qgraup]
        mvars = [m, mcl, mcf, mrain, mgraup]

        self.sanity_check(qvars, mvars)

        self._calc_tcw(rho, qvars)
        self.say('Total col water (kg m-2/mm): {}'.format(self.tcw))

        self._calc_mse(rho, th, ep, q)

        q_rho = (q.data[:-1, :, :] + q.data[1:, :, :]) / 2
        m_rho = (m.data[:-1, :, :] + m.data[1:, :, :]) / 2

        self.say('max diff rho_d * m, rho * q: {}'.format(np.abs(rho_d.data * m_rho - rho.data * q_rho).max()))
        self.say('')

    def sanity_check(self, qvars, mvars):
        msum = np.zeros_like(mvars[0].data)
        for mv in mvars:
            msum += mv.data

        for qv, mv in zip(qvars, mvars):
            self.say(qv.name())
            diff = np.abs((mv.data / (1 + msum)) - qv.data)
            self.say('Max diff: {}'.format(diff.max()))
            if diff.max() > 1e-15:
                self.say('MAX DIFF TOO LARGE')

    def save(self):
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)

        with open(os.path.join(self.results_dir, self.expt + '.csv'), 'w') as f:
            f.write('MSE,TCW\n')
            f.write('{},{}\n'.format(self.mse, self.tcw))

    def say(self, message):
        print(message)

    def _calc_mse(self, rho, th, ep, q):
        """Calculate Moist Static Energy

        rho, th(eta), ep (Exner Pressure) and q must be 3D fields
        returns 3D MSE, stores all working in object.
        """
        z = th.coord('level_height').points
        dz = z[1:] - z[:-1]

        Lv_rho_heights = rho.coord('level_height').points
        Lv_rho = Lv_rho_heights.repeat(rho.shape[1] * rho.shape[2]).reshape(rho.shape[0], rho.shape[1], rho.shape[2])
        self.e_t = rho.data * (th[:-1, :, :].data + th[1:, :, :].data) / 2 * ep[:-1].data * cp
        self.e_q = rho.data * (q[:-1, :, :].data + q[1:, :, :].data) / 2 * L
        self.e_z = rho.data * g * Lv_rho

        self.mse = (self.e_t + self.e_q + self.e_z)

        self.e_t_profile = self.e_t.mean(axis=(1, 2))
        self.e_q_profile = self.e_q.mean(axis=(1, 2))
        self.e_z_profile = self.e_z.mean(axis=(1, 2))

        self.mse_profile = self.mse.mean(axis=(1, 2))
        #    f.write('{},{},{},{}\n'.format((mse_profile * dz).sum(),
        #                                  (e_t_profile * dz).sum(),
        #                                  (e_q_profile * dz).sum(),
        #                                  (e_z_profile * dz).sum()))
        self.say('MSE [GJ m^-2] = {0:.5f}'.format((self.mse_profile * dz).sum() / 1e9))
        self.say('  E(T) [GJ m^-2] = {0:.5f}'.format((self.e_t_profile * dz).sum() / 1e9))
        self.say('  E(q) [GJ m^-2] = {0:.5f}'.format((self.e_q_profile * dz).sum() / 1e9))
        self.say('  E(z) [GJ m^-2] = {0:.5f}'.format((self.e_z_profile * dz).sum() / 1e9))
        return self.mse

    def _calc_mwvi(self, rho, var):
        """Calculate Mass Weighted Vertical Integral

        Must be passed two iris cubes with ndim=3
        var must be on theta-level, and rho-level mast be halfway between theta-level.

        Calculates Integ(rho * var, 0, TOA, dz)
        """
        # Remember: for a 3D UM cube, height will be the first coord: e.g. var[0] selects first height.
        assert isinstance(rho, iris.cube.Cube)
        assert isinstance(var, iris.cube.Cube)
        assert rho.ndim == 3
        assert var.ndim == 3

        cube_heights = var.coord('level_height').points
        rho_heights = rho.coord('level_height').points

        if len(cube_heights) != len(rho_heights) + 1:
            raise Exception('Cube {} not on theta level'.format(var.name()))

        cube_heights_on_rho = (cube_heights[:-1] + cube_heights[1:]) / 2
        isclose = np.isclose(cube_heights_on_rho, rho_heights)
        if not isclose.all():
            raise Exception('Interpolation of var heights failed')

        # Work out dz, turn into 3d field to be multiplied by data.
        dz = cube_heights[1:] - cube_heights[:-1]
        dz3d = dz.repeat(var.shape[1] * var.shape[2]) \
                 .reshape(var.shape[0] - 1, var.shape[1], var.shape[2])
        # dz4d = np.tile(dz3d, (var.shape[0], 1, 1, 1))  # pylint: disable=no-member

        # Work out variable on rho grid, perform integral.
        var_on_rho_grid_data = (var.data[:-1] + var.data[1:]) / 2
        # Assume bottom rho level value equal to bottom theta level value
        # cf:
        # https://code.metoffice.gov.uk/trac/um/browser/main/branches/dev/chrissmith/
        # vn10.5_ium_base/src/atmosphere/energy_correction/
        # vert_eng_massq-vrtemq1b.F90?rev=24919#L297
        # N.B. has no effect on outcome for data that I have analysed so far:
        # np.isclose(var.data[:, 0], var.data[:, 1]).all() == True
        # Therefore adding and averaging is the same as just taking one of them.
        var_on_rho_grid_data[0] = var.data[0]
        varXrho = var_on_rho_grid_data * rho.data
        var_col = (dz3d * varXrho).sum(axis=0)

        # Stuff results into a lovingly crafted cube.
        # Get cube with correct shape (2D horizontal slice).
        new_cube = var.slices_over('model_level_number').next().copy()
        new_cube.data = var_col
        new_cube.rename('Mass weighted vertical integral of {}'.format(var.name()))
        new_cube.units = 'kg m-2'
        return new_cube

    def _calc_tcw(self, rho, qvars):
        """Calculates Total Column Water from all the specific water species."""
        self.mwvi_vars = []
        for qv in qvars:
            self.mwvi_vars.append((qv.name(), self._calc_mwvi(rho, qv)))
        self.tcw = np.sum([v[1].data.mean() for v in self.mwvi_vars])
        return self.tcw


def main(user, expts, suite, results_dir):
    for expt in expts:
        for dump_file in DumpAnalyzer.get_files(user, suite, expt):
            da = DumpAnalyzer(user, suite, expt, dump_file, results_dir)
            da.run()
            da.save()


if __name__ == '__main__':
    user = os.path.expandvars('$USER')
    suite = os.path.expandvars('$SUITE')
    results_dir = os.path.join(os.path.expandvars('$RESULTS_DIR'), suite)
    main(user, sys.argv[1:], suite, results_dir)
