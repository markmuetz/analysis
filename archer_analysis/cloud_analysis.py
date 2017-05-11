import os

import matplotlib
matplotlib.use('Agg')
import pylab as plt
import iris

from analyzer import Analyzer
from utils import get_cube
from consts import Re, L, cp, g


class CloudAnalyzer(Analyzer):
    def set_config(self, config):
	super(CloudAnalyzer, self).set_config(config)
	self.height_level = int(config['height_level'])
	self.w_thresh = float(config['w_thresh'])
	self.qcl_thresh = float(config['qcl_thresh'])
	    
    def run_analysis(self):
        cubes = self.cubes

        w = get_cube(cubes, 0, 150)
        qcl = get_cube(cubes, 0, 254)

	w_mask = w[:, self.height_level].data > self.w_thresh
	qcl_mask = qcl[:, self.height_level].data > self.qcl_thresh

        w_mask_cube = w.slices_over('model_level_number').next().copy()
	w_mask_cube.data = w_mask.astype(int)
        w_mask_cube.rename('w mask w>{}'.format(self.w_thresh))

        qcl_mask_cube = qcl.slices_over('model_level_number').next().copy()
	qcl_mask_cube.data = qcl_mask.astype(int)
        qcl_mask_cube.rename('qcl mask qcl>{}'.format(self.qcl_thresh))

        cloud_mask_cube = qcl.slices_over('model_level_number').next().copy()
	cloud_mask_cube.data = (w_mask & qcl_mask).astype(int)
        cloud_mask_cube.rename('Cloud mask w>{}, qcl>{}'.format(self.w_thresh, self.qcl_thresh))

	self.results['w_mask'] = w_mask_cube
	self.results['qcl_mask'] = qcl_mask_cube
	self.results['cloud_mask'] = cloud_mask_cube
