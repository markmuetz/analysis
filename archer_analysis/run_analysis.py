import os
import sys
from configparser import ConfigParser

from analyzers import ANALYZERS


class RunControl(object):
    def run(self):
	dataw_dir, datam_dir, user, suite = self.read_env()
	data_type, expt = self.read_args()
	self.dataw_dir = dataw_dir
	self.datam_dir = datam_dir
	self.user = user
	self.suite = suite
	self.data_type = data_type
	self.expt = expt

	self.run_analysis(dataw_dir, datam_dir, user, suite, data_type, expt)

    def read_env(self):
	dataw_dir = os.getenv('DATAW')
	datam_dir = os.getenv('DATAM')
	user = os.getenv('USER')
	suite = os.getenv('CYLC_SUITE_NAME')
	return dataw_dir, datam_dir, user, suite

    def read_args(self):
	data_type = sys.argv[1]
	expt = sys.argv[2]
	return data_type, expt

    def read_config(self, config_dir):
	config = ConfigParser()
	with open(os.path.join(config_dir, 'rose-app-run.conf'), 'r') as f:
	    config.read_file(f)
	return config

    def run_analysis(self, config_dir, datam_dir, user, suite, data_type, expt):
	config = self.read_config(config_dir)
	self.config = config

	runcontrol_sec = '{}_runcontrol'.format(data_type)
	runcontrol = config[runcontrol_sec]
	for ordered_analysis, enabled_str in sorted(runcontrol.items()):
	    analysis = ordered_analysis[3:]
	    enabled = enabled_str == 'True'
	    print('{}: enabled {}'.format(analysis, enabled))
	    if not enabled:
		continue

	    if config.has_section(analysis):
		analyzer_config = config[analysis]
	    else:
		raise Exception('NO CONFIG FOR ANALYSIS, SKIPPING')

	    if analysis not in ANALYZERS:
		raise Exception('COULD NOT FIND ANALYZER: {}'.format(analysis))

	    Analyzer = ANALYZERS[analysis]

	    filename = analyzer_config.pop('filename')
	    if data_type == 'dataw':
		print(filename)

		# N.B. config_dir is DATAW *for the current task*.
		# Need to work out where the atmos DATAW dir is.
		data_dir = os.path.join(os.path.dirname(config_dir), expt + '_atmos')
		results_dir = config_dir
		analyzer = Analyzer(user, suite, expt, data_type, data_dir, results_dir, filename)
		analyzer.set_config(analyzer_config)
		if not analyzer.already_analyzed() or analyzer.force:
		    analyzer.load()
		    analyzer.run()
		    analyzer.save()
	    elif data_type == 'datam':
		# filename can be a glob.
		filenames = Analyzer.get_files(datam_dir, filename)
		for actual_filename in filenames:
		    print(actual_filename)
		    results_dir = datam_dir
		    analyzer = Analyzer(user, suite, expt, data_type, datam_dir, results_dir, actual_filename)
		    analyzer.set_config(analyzer_config)
		    if not analyzer.already_analyzed() or analyzer.force:
			analyzer.load()
			analyzer.run()
			analyzer.save()
	    else:
		raise Exception('Unknown data_type: {}'.format(data_type))


if __name__ == '__main__':
    run_control = RunControl()
    run_control.run()
