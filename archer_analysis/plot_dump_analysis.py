import os
import sys

import matplotlib
matplotlib.use('Agg')
import pylab as plt
import pandas as pd


def plot_dump_analysis(results_dir, expt):
    results_dir = os.path.join('/home/n02/n02/mmuetz/work/cylc-run/u-ak766/share/data/history/{}/results'.format(expt))
    filename = os.path.join(results_dir, expt + '.csv')
    if not os.path.exists(filename):
        raise Exception('Cannot find {}'.format(filename))
    df = pd.read_csv(filename)
    plt.clf()
    plt.plot(df['Time (hours)'].values, df['TMSE (J m-2)'].values)
    plt.xlabel('Time (hours)')
    plt.ylabel('TMSE (J m-2)')
    plt.savefig(os.path.join(results_dir, 'TMSE_' + expt + '.png'))

    plt.clf()
    plt.plot(df['Time (hours)'].values, df['TCW (kg m-2)'].values)
    plt.xlabel('Time (hours)')
    plt.ylabel('TCW (kg m-2)')
    plt.savefig(os.path.join(results_dir, 'TCW_' + expt + '.png'))


def main(user, expts, suite, results_dir):
    for expt in expts:
        plot_dump_analysis(results_dir, expt)


if __name__ == '__main__':
    user = os.path.expandvars('$USER')
    suite = os.path.expandvars('$SUITE')
    results_dir = os.path.expandvars('$RESULTS_DIR')
    main(user, sys.argv[1:], suite, results_dir)
