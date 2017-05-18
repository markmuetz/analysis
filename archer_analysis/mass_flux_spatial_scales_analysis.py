import os
from collections import OrderedDict

import numpy as np
import iris

from analyzer import Analyzer
from utils import get_cube_from_attr, coarse_grain


class MassFluxSpatialScalesAnalyzer(Analyzer):
    analysis_name = 'mass_flux_spatial_scales_analysis'

    def run_analysis(self):
        cubes = self.cubes

        w = get_cube_from_attr(cubes, 'id', 'w')
	cloud_mask_cube = get_cube_from_attr(cubes, 'id', 'cloud_mask')

	mass_flux = OrderedDict()
	for time_index in range(cloud_mask_cube.data.shape[0]):
	    w_ss = w[time_index].data
	    cloud_mask_ss = cloud_mask_cube[time_index].data.astype(bool)
	    coarse_data = coarse_grain(w_ss, cloud_mask_ss)
	    for n, coarse_datum in coarse_data:
		if n not in mass_flux:
		    mass_flux[n] = []
		else:
		    mass_flux[n] = np.append(mass_flux[n], coarse_datum.flatten())
	
	for key, mass_fluxes in mass_flux.items():
	    values = iris.coords.DimCoord(range(len(mass_fluxes)), long_name='values')
	    name = 'spatial-mass-flux-{}'.format(key)
	    mass_flux_cube = iris.cube.Cube(mass_fluxes, 
					    long_name=name, 
					    dim_coords_and_dims=[(values, 0)], 
					    units='kg s-1')
	    mass_flux_cube.attributes['id'] = name
	    self.results[name] = mass_flux_cube
