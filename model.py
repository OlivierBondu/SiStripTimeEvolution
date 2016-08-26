import numpy as np
import matplotlib.pyplot as plt
import json
from datetime import datetime
import scipy.stats as st
import pylandau

# various constants
n_bx_in_orbit = 3564  # in number of bx
n_bx_in_train = 72  # in number of bx
n_orbits_in_lumisection = pow(2, 18)  # in number of orbits, ~93 seconds
bunch_spacing = 25.e-9  # in s, note that this is fixed
ls_duration_in_s = n_orbits_in_lumisection * n_bx_in_orbit * bunch_spacing

def main():
    tstart = datetime.now()
    # Initial parameters
    run_duration_in_ls = 3  # in number of LS
    init_lumi = 700.  # in e30 cm-1.s-1
    # Variables to fit
    hip_recovery_time_constant = 300  # in ns
    hip_probability = 1.e-3
    # external inputs
    zerobias_trigger_rate = 20  # in Hz
    n_events = int(1e3)

    bunch_fill = get_bunch_fill()
    n_non_empty_bunches = len([x for x in bunch_fill if x > 0])
    cluster_charge = [0 for x in xrange(n_bx_in_orbit)]
#    n_clusters = [0 for x in xrange(n_bunches)]
    fraction_of_non_empty_bx = n_non_empty_bunches / float(n_bx_in_orbit)
    frequency_non_empty_bx = n_orbits_in_lumisection * n_non_empty_bunches
    p_trigger = zerobias_trigger_rate / float(frequency_non_empty_bx)
    print "\n##### #####"
    print "# Fraction of non-empty bunches: %.1f %%" % (fraction_of_non_empty_bx * 100)
    print "# Frequency of non-empty bunches: %.1e Hz" % (frequency_non_empty_bx)
    print "# ZeroBias-like trigger rate: %.1f Hz" % (zerobias_trigger_rate)
    print "# Trigger probability: %.2e" % (p_trigger)
    print "##### #####\n"

    avg_trigger_rate = {}
    non_empty_bunch_fill = {}
    for ibx, bx in enumerate(bunch_fill):
        if bx > 0.01:
            non_empty_bunch_fill[ibx] = bx
    for ils in xrange(run_duration_in_ls):
        avg_trigger_rate[ils] = []
        if ((ils % 10  == 0 and ils < 100)
            or (ils % 100 == 0 and ils < 1000)
            or (ils % 500 == 0 )):
            print "# Processing lumi section %i / %i (elapsed time: %s)" % (ils +1, run_duration_in_ls, datetime.now() - tstart)
        for iorbit in xrange(n_orbits_in_lumisection):
            if iorbit % 50000 == 0:
                print "\t# Processing orbit %i / %i (elapsed time: %s)" % (iorbit +1, n_orbits_in_lumisection, datetime.now() - tstart)
            for ibx, bx in non_empty_bunch_fill.iteritems():
                is_triggered = np.random.uniform() < p_trigger
                avg_trigger_rate[ils].append(is_triggered)
                # cluster_charge[ibx]
    n_events_triggered = sum(avg_trigger_rate)
    avg_trigger_rate = n_events_triggered / float(run_duration_in_ls * n_orbits_in_lumisection * n_bx_in_orbit)

    tstop = datetime.now()
    print "\n##### #####"
    print "# Average observed (expected) trigger rate: %.1f (%.1f) Hz" % (avg_trigger_rate * n_orbits_in_lumisection * n_bx_in_orbit, zerobias_trigger_rate)
    print "# Number of triggered events: %s" % (int_with_commas(n_events_triggered))
    print "# Script ran in %s" % (tstop - tstart)
    # get_cluster_charge(plot=False, nEvents=n_events)
    print "##### #####\n"

class landau_generator(st.rv_continuous):
    """Landau distribution generator"""
    def _pdf(self, x):
        return pylandau.get_landau_pdf(x, mu=150.0, eta=20.0)


def get_cluster_charge(plot=True, nEvents=10):
    """
    Generates a list of cluster charges
    :param plot: display the generated cluster Charge histogram
    :return: list of cluster charges
    """
    landau = landau_generator(name='cluster charge landau', a=0.)
    clusterCharge = landau.rvs(size=nEvents, scale=1, loc=0)
    if plot:
        nBins = 50
        X = np.arange(0, 500, 0.01)
        Y = [landau.pdf(x) for x in X]
        plt.plot(X, Y, '-',
                 label='mu=%1.1f, eta=%1.1f' % (150.0, 20.0))
        n, bins, patches = plt.hist(clusterCharge, nBins, facecolor='green', alpha=0.75, normed=True)
        # plt.axis([0, 500., 0, 0.02])
        plt.grid(True)
        plt.show()
    return clusterCharge

def int_with_commas(x):
    # From http://stackoverflow.com/questions/1823058/how-to-print-number-with-commas-as-thousands-separators
    if type(x) not in [type(0), type(0L)]:
        raise TypeError("Parameter must be an integer.")
    if x < 0:
        return '-' + intWithCommas(-x)
    result = ''
    while x >= 1000:
        x, r = divmod(x, 1000)
        result = ",%03d%s" % (r, result)
    return "%d%s" % (x, result)

def get_bunch_fill():
    """
    return the bunch fill a la https://cmswbm.web.cern.ch/cmswbm/cmsdb/servlet/BunchFill?FILL=5013
    :return: return a list of size 3564 with the initial lumi
    """
    # bx_fill_4915_run_273162.json
    with open('bx_fill_4915_run_273162.json') as f:
        data = json.load(f)
    bunch_fill = [0 for x in xrange(n_bx_in_orbit)]
    bunch_fill = [data[str(ix)]['InitialLumi'] for ix, x in enumerate(bunch_fill)]
    # print bunch_fill[3064]
    # bunch_fill = [0 for x in xrange(orbit_length)]
    # for x in range(548, 620):
    #     local_lumi = np.random.uniform(high=4.547, low=3.223)
    #     bunch_fill[x] = local_lumi
    return bunch_fill


if __name__ == '__main__':
    # get_bunch_fill()
    # get_cluster_charge(plot=True, nEvents=200)
    main()
