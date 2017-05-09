import os
import sys
from configparser import ConfigParser

def main():
    #print(sys.argv)
    #for k, v in os.environ.items():
	#print((k, v))
    dataw_dir = os.getenv('DATAW')
    print(dataw_dir)
    cp = ConfigParser()
    cp.read(os.path.join(dataw_dir, 'rose-app-run.conf'))
    #print(cp.sections())

    data_type = sys.argv[1]
    expt = sys.argv[2]
    runcontrol_sec = '{}_runcontrol'.format(data_type)
    runcontrol = cp[runcontrol_sec]
    for analysis, enabled in runcontrol.items():
	print((analysis, enabled == 'True'))
	if cp.has_section(analysis):
	    section_settings = cp[analysis]
	    print(section_settings.items())

if __name__ == '__main__':
    main()
