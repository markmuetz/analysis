import os

import numpy as np
import matplotlib
matplotlib.use('Agg')
import pylab as plt
import iris

from analyzer import Analyzer
from utils import get_cube, get_cube_from_attr, count_blobs_mask
from consts import Re, L, cp, g


class MassFluxAnalyzer(Analyzer):
    analysis_name = 'mass_flux_analysis'

    def run_analysis(self):
        cubes = self.cubes

        w = get_cube_from_attr(cubes, 'id', 'w')
	w_mask_cube = get_cube_from_attr(cubes, 'id', 'w_mask')
	qcl_mask_cube = get_cube_from_attr(cubes, 'id', 'qcl_mask')
	cloud_mask_cube = get_cube_from_attr(cubes, 'id', 'cloud_mask')

        blob_cube = w.copy()
	blob_cube.rename('cloud_blobs')
	blob_cube.units = ''

	blob_cube_data = np.zeros_like(blob_cube.data)
	mass_fluxes = []
	for time_index in range(cloud_mask_cube.data.shape[0]):
	    w_ss = w[time_index].data
	    cloud_mask_ss = cloud_mask_cube[time_index].data.astype(bool)
	    max_blob_index, blobs = count_blobs_mask(cloud_mask_ss, True)
	    blob_cube_data[time_index] = blobs

	    for i in range(1, max_blob_index + 1):
		mask = (blobs == i)
		mass_flux = w_ss[mask].sum()
		mass_fluxes.append(mass_flux)

	blob_cube.data = blob_cube_data
	self.results['blobs'] = blob_cube

	print(sorted(mass_fluxes))
	values = iris.coords.DimCoord(range(len(mass_fluxes)), long_name='values')
	mass_flux_cube = iris.cube.Cube(mass_fluxes, 
		                        long_name='mass-flux', 
					dim_coords_and_dims=[(values, 0)], 
					units='kg s-1')

	self.results['mass_flux'] = mass_flux_cube
