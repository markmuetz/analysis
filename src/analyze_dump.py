import os
import sys
from glob import glob

import numpy as np
import pandas as pd
import iris

import omnium as om

Re = 6371229.
L = 2.5e6
cp = 1004
g = 9.81

ARCHER_BASE_DIR = '/work/n02/n02/$USER/cylc-run/$SUITE/share/data/history/'


def get_cube(cubes, section, item):
    for cube in cubes:
        stash = cube.attributes['STASH']
        if section == stash.section and item == stash.item:
            return cube
    return None


def calc_mse(rho, th, ep, q):
    z = th.coord('level_height').points
    dz = z[1:] - z[:-1]

    Lv_rho_heights = rho.coord('level_height').points
    Lv_rho = Lv_rho_heights.repeat(rho.shape[1] * rho.shape[2]).reshape(rho.shape[0], rho.shape[1], rho.shape[2])
    e_t = rho.data * (th[:-1, :, :].data + th[1:, :, :].data) / 2 * ep[:-1].data * cp
    e_q = rho.data * (q[:-1, :, :].data + q[1:, :, :].data) / 2 * L
    e_z = rho.data * g * Lv_rho

    mse = (e_t + e_q + e_z)

    e_t_profile = e_t.mean(axis=(1, 2))
    e_q_profile = e_q.mean(axis=(1, 2))
    e_z_profile = e_z.mean(axis=(1, 2))

    mse_profile = mse.mean(axis=(1, 2))
    #    f.write('{},{},{},{}\n'.format((mse_profile * dz).sum(),
    #                                  (e_t_profile * dz).sum(),
    #                                  (e_q_profile * dz).sum(),
    #                                  (e_z_profile * dz).sum()))
    print('MSE [GJ m^-2] = {0:.5f}'.format((mse_profile * dz).sum() / 1e9))
    print('  E(T) [GJ m^-2] = {0:.5f}'.format((e_t_profile * dz).sum() / 1e9))
    print('  E(q) [GJ m^-2] = {0:.5f}'.format((e_q_profile * dz).sum() / 1e9))
    print('  E(z) [GJ m^-2] = {0:.5f}'.format((e_z_profile * dz).sum() / 1e9))


def mwvi(rho, var):
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


def calc_q_diffs(da):
    rho = get_cube(da, 0, 253) / Re ** 2
    rho_d = get_cube(da, 0, 389)

    th = get_cube(da, 0, 4)
    ep = get_cube(da, 0, 255)

    q = get_cube(da, 0, 10)
    qcl = get_cube(da, 0, 254)
    qcf = get_cube(da, 0, 12)
    qrain = get_cube(da, 0, 272)
    qgraup = get_cube(da, 0, 273)

    m = get_cube(da, 0, 391)
    mcl = get_cube(da, 0, 392)
    mcf = get_cube(da, 0, 393)
    mrain = get_cube(da, 0, 394)
    mgraup = get_cube(da, 0, 395)

    qvars = [q, qcl, qcf, qrain, qgraup]
    mvars = [m, mcl, mcf, mrain, mgraup]

    mwvi_vars = []
    for qv, mv in zip(qvars, mvars):
        print(qv.name())
        print(np.abs((mv.data / (1 + m.data + mcl.data + mcf.data + mrain.data + mgraup.data)) - qv.data).max())
        mwvi_vars.append(mwvi(rho, qv))

    q_rho = (q.data[:-1, :, :] + q.data[1:, :, :]) / 2
    m_rho = (m.data[:-1, :, :] + m.data[1:, :, :]) / 2

    tcw = np.sum([v.data.mean() for v in mwvi_vars])
    print('Total col water (kg m-2/mm): {}'.format(tcw))

    calc_mse(rho, th, ep, q)

    print('max diff rho_d * m, rho * q: {}'.format(np.abs(rho_d.data * m_rho - rho.data * q_rho).max()))
    print('')


def main(stash, expt, directory):
    print(directory)
    suite_dir = os.path.expandvars('$SUITE')
    results_dir = os.path.join(os.path.expandvars('$RESULTS_DIR'), suite_dir)

    if not os.path.exists(results_dir):
        os.makedirs(results_dir)

    if False:
        with open(os.path.join(results_dir, expt + '_demo.csv'), 'w') as f:
            f.write('h,h2,h3\n')
            f.write('1,2,3\n')

    for da_name in sorted(glob(os.path.join(directory, 'atmosa_da???'))):
        print(da_name)
        da = iris.load(da_name)
        stash.rename_unknown_cubes(da, True)
        calc_q_diffs(da)


if __name__ == '__main__':
    stash = om.Stash()
    for expt in sys.argv[1:]:
        directory = os.path.join(os.path.expandvars(ARCHER_BASE_DIR), expt)
        main(stash, expt, directory)
