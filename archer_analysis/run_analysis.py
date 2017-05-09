import os
import sys
from configparser import ConfigParser

from analyzers import ANALYZERS


def main():
    # Read in env vars.
    dataw_dir = os.getenv('DATAW')
    datam_dir = os.getenv('DATAM')
    user = os.getenv('USER')
    suite = os.getenv('CYLC_SUITE_NAME')
    #results_dir = os.getenv('DATAW')

    #print(dataw_dir)
    #print(user)
    #print(suite)
    #print(results_dir)

    # Read in args.
    data_type = sys.argv[1]
    expt = sys.argv[2]
    #print(data_type)
    #print(expt)

    # Read in config.
    parser = ConfigParser()
    with open(os.path.join(dataw_dir, 'rose-app-run.conf'), 'r') as f:
	parser.read_file(f)
    #print(parser.sections())

    runcontrol_sec = '{}_runcontrol'.format(data_type)
    runcontrol = parser[runcontrol_sec]
    for analysis, enabled_str in runcontrol.items():
	enabled = enabled_str == 'True'
	print('{}: enabled {}'.format(analysis, enabled))
	if not enabled:
	    continue

	if parser.has_section(analysis):
	    analyzer_config = parser[analysis]
	else:
	    print('NO CONFIG, skipping')
	    continue

	if analysis not in ANALYZERS:
	    print('COULD NOT FIND ANALYZER: {}'.format(analysis))
	    continue

	Analyzer = ANALYZERS[analysis]

	filename = analyzer_config.pop('filename')
	if data_type == 'dataw':
	    print(filename)
	    analyzer = Analyzer(user, suite, expt, data_type, dataw_dir, filename)
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
		analyzer = Analyzer(user, suite, expt, data_type, datam_dir, actual_filename)
		analyzer.set_config(analyzer_config)
		if not analyzer.already_analyzed() or analyzer.force:
		    analyzer.load()
		    analyzer.run()
		    analyzer.save()
	else:
	    raise Exception('Unknown data_type: {}'.format(data_type))


if __name__ == '__main__':
    main()
