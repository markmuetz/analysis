import os

import numpy as np
import matplotlib
matplotlib.use('Agg')
import pylab as plt
import iris

from analyzer import Analyzer
from utils import get_cube, count_blobs_mask
from consts import Re, L, cp, g


class MassFluxAnalyzer(Analyzer):
    def set_config(self, config):
	super(MassFluxAnalyzer, self).set_config(config)
	self.height_level = int(config['height_level'])
	self.w_thresh = float(config['w_thresh'])
	self.qcl_thresh = float(config['qcl_thresh'])
	    
    def run_analysis(self):
	# COPIED from cloud_analysis, work out how not to copy.
        cubes = self.cubes

        w = get_cube(cubes, 0, 150)
        qcl = get_cube(cubes, 0, 254)

	w_mask = w[:, self.height_level].data > self.w_thresh
	qcl_mask = qcl[:, self.height_level].data > self.qcl_thresh

        w_mask_cube = w.slices_over('model_level_number').next().copy()
	w_mask_cube.data = w_mask.astype(int)
        w_mask_cube.rename('w_mask_w>{}'.format(self.w_thresh))

        qcl_mask_cube = qcl.slices_over('model_level_number').next().copy()
	qcl_mask_cube.data = qcl_mask.astype(int)
        qcl_mask_cube.rename('qcl_mask_qcl>{}'.format(self.qcl_thresh))

        cloud_mask_cube = qcl.slices_over('model_level_number').next().copy()
	cloud_mask_cube.data = (w_mask & qcl_mask).astype(int)
        cloud_mask_cube.rename('Cloud_mask_w>{}_qcl>{}'.format(self.w_thresh, self.qcl_thresh))

	self.results['w'] = w
	self.results['qcl'] = qcl
	self.results['w_mask'] = w_mask_cube
	self.results['qcl_mask'] = qcl_mask_cube
	self.results['cloud_mask'] = cloud_mask_cube

        blob_cube = qcl.slices_over('model_level_number').next().copy()
	blob_cube.rename('cloud_blobs')

	blob_cube_data = np.zeros_like(blob_cube.data)
	mass_fluxes = []
	for time_index in range(cloud_mask_cube.data.shape[0]):
	    w_ss = w[time_index, self.height_level].data
	    cloud_mask_ss = cloud_mask_cube[time_index].data.astype(bool)
	    max_blob_index, blobs = count_blobs_mask(cloud_mask_ss, True)
	    blob_cube_data[time_index] = blobs

	    for i in range(1, max_blob_index + 1):
		mask = (blobs == i)
		mass_flux = w_ss[mask]
		mass_fluxes.append(mass_flux.sum())

	blob_cube.data = blob_cube_data
	self.results['blobs'] = blob_cube

	print(sorted(mass_fluxes))
	values = iris.coords.DimCoord(range(len(mass_fluxes)), long_name='values')
	mass_flux_cube = iris.cube.Cube(mass_fluxes, 
		                        long_name='mass-flux', 
					dim_coords_and_dims=[(values, 0)], 
					units='kg s-1')

	self.results['mass_flux'] = mass_flux_cube
