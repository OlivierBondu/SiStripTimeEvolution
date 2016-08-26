# coding=utf-8
# import sys
import numpy as np
import matplotlib.pyplot as plt
import json
from datetime import datetime
import scipy.stats as st
import pylandau
# to prevent pyroot to hijack argparse we need to go around
# tmpargv = sys.argv[:]
# sys.argv = []
# ROOT imports
import ROOT
ROOT.gROOT.SetBatch()
ROOT.PyConfig.IgnoreCommandLineOptions = True
ROOT.gROOT.ProcessLine(".x setTDRStyle.C")
ROOT.TGaxis.SetMaxDigits(3)
# sys.argv = tmpargv
from ROOT import TCanvas
from ROOT import TH1F
from ROOT import TH2F

# various global constants
n_bx_in_orbit = 3564  # in number of bx
n_orbits_in_lumisection = pow(2, 10)  # in number of orbits, ~23.36 seconds
bunch_spacing = 25.e-9  # in s, note that this is fixed
ls_duration_in_s = n_orbits_in_lumisection * n_bx_in_orbit * bunch_spacing


def main():
    # Initialisation
    tstart = datetime.now()

    # Simulation parameters
    run_duration_in_ls = 1  # in number of LS
    init_lumi = 700.  # in e30 cm-1.s-1
    zerobias_trigger_rate = 20  # in Hz
    p_mip = .5  # TODO: replace by flux from FLUKA or GEANT * inst lumi

    # Variables to fit
    hip_recovery_time_constant = 300  # in ns
    p_hip = 1.e-3


    # declaration of histos and containers
    c1 = TCanvas('c1', 'c1', 600, 600)
    c2 = TCanvas('c2', 'c2', 1200, 600)
    h_cluster_charge = TH1F('h_cluster_charge', 'h_cluster_charge', 400, 0, 400)
    h_cluster_charge_vs_bx = TH2F('h_cluster_charge_vs_bx', 'h_cluster_charge_vs_bx', 3600, 0, 3600, 400, 0, 400)
    cluster_charge = {}  # cluster charge for each ls and orbit
    bunch_fill = get_bunch_fill()
    non_empty_bunch_fill = {i:x for i, x in enumerate(bunch_fill) if x > 0}
    n_non_empty_bunches = len(non_empty_bunch_fill)

    #     cluster_charge = [0 for x in xrange(n_bx_in_orbit)]
    # #    n_clusters = [0 for x in xrange(n_bunches)]
    fraction_of_non_empty_bx = n_non_empty_bunches / float(n_bx_in_orbit)
    #     frequency_non_empty_bx = n_orbits_in_lumisection * n_non_empty_bunches
    #     p_trigger = zerobias_trigger_rate / float(frequency_non_empty_bx)
    print "\n##### #####"
    print "# Fraction of non-empty bunches: %.1f %%" % (fraction_of_non_empty_bx * 100)
    #     print "# Frequency of non-empty bunches: %.1e Hz" % (frequency_non_empty_bx)
    #     print "# ZeroBias-like trigger rate: %.1f Hz" % (zerobias_trigger_rate)
    #     print "# Trigger probability: %.2e" % (p_trigger)
    print "##### #####\n"

    # Looping over the beams à la LHC
    for ils in xrange(run_duration_in_ls):
        cluster_charge[ils] = {}
        for iorbit in xrange(n_orbits_in_lumisection):
            if iorbit % (n_orbits_in_lumisection / 5) == 0:
                print "\t# Processing orbit %i / %i (elapsed time: %s)" % (iorbit +1, n_orbits_in_lumisection, datetime.now() - tstart)
            cluster_charge[ils][iorbit] = get_cluster_charge(n_events=n_non_empty_bunches, crude_gaussian_approximation=True)
            for i, i_non_empty_bx in enumerate(non_empty_bunch_fill):
                charge = cluster_charge[ils][iorbit][i]
                h_cluster_charge.Fill(charge)
                h_cluster_charge_vs_bx.Fill(i_non_empty_bx, charge)

#
#     avg_trigger_rate = {}
#     non_empty_bunch_fill = {}
#     for ibx, bx in enumerate(bunch_fill):
#         if bx > 0.01:
#             non_empty_bunch_fill[ibx] = bx
#     for ils in xrange(run_duration_in_ls):
#         avg_trigger_rate[ils] = []
#         if ((ils % 10  == 0 and ils < 100)
#             or (ils % 100 == 0 and ils < 1000)
#             or (ils % 500 == 0 )):
#             print "# Processing lumi section %i / %i (elapsed time: %s)" % (ils +1, run_duration_in_ls, datetime.now() - tstart)
#         for iorbit in xrange(n_orbits_in_lumisection):
#             if iorbit % 50000 == 0:
#                 print "\t# Processing orbit %i / %i (elapsed time: %s)" % (iorbit +1, n_orbits_in_lumisection, datetime.now() - tstart)
#             for ibx, bx in non_empty_bunch_fill.iteritems():
#                 is_triggered = np.random.uniform() < p_trigger
#                 avg_trigger_rate[ils].append(is_triggered)
#                 # cluster_charge[ibx]
#     n_events_triggered = sum(avg_trigger_rate)
#     avg_trigger_rate = n_events_triggered / float(run_duration_in_ls * n_orbits_in_lumisection * n_bx_in_orbit)

    tstop = datetime.now()
    print "\n##### #####"
    # print "# Average observed (expected) trigger rate: %.1f (%.1f) Hz" % (avg_trigger_rate * n_orbits_in_lumisection * n_bx_in_orbit, zerobias_trigger_rate)
    # print "# Number of triggered events: %s" % (int_with_commas(n_events_triggered))
    print "# Script ran in %s" % (tstop - tstart)
    c1.cd()
    h_cluster_charge.Draw()
    c1.Print('h_cluster_charge.pdf')
    c1.Print('h_cluster_charge.png')
    c2.cd()
    h_cluster_charge_vs_bx.Draw('colz')
    c2.Print('h_cluster_charge_vs_bx.pdf')
    c2.Print('h_cluster_charge_vs_bx.png')
    h_cluster_charge_vs_bx.RebinX(10)
    px_cluster_charge_vs_bx = h_cluster_charge_vs_bx.ProfileX()
    px_cluster_charge_vs_bx.SetMinimum(50)
    px_cluster_charge_vs_bx.SetMaximum(250)
    px_cluster_charge_vs_bx.Draw()
    c2.Print('px_cluster_charge_vs_bx.pdf')
    c2.Print('px_cluster_charge_vs_bx.png')
    print "##### #####\n"



class landau_generator(st.rv_continuous):
    """Landau distribution generator"""
    def _pdf(self, x):
        return pylandau.get_landau_pdf(x, mu=150.0, eta=20.0)


def get_cluster_charge(plot=False, n_events=10, crude_gaussian_approximation=True):
    """
    Generates a list of cluster charges
    :param plot: display the generated cluster Charge histogram
    :return: list of cluster charges
    """
    cluster_charge = []
    if not crude_gaussian_approximation:
        landau = landau_generator(name='cluster charge landau', a=0.)
        cluster_charge = landau.rvs(size=n_events, scale=1, loc=0)
    else:
        cluster_charge = np.random.normal(loc=150.0, scale=20.0, size=n_events)
    if plot:
        n_bins = 50
        X = np.arange(0, 500, 0.01)
        Y = [landau.pdf(x) for x in X]
        plt.plot(X, Y, '-',
                 label='mu=%1.1f, eta=%1.1f' % (150.0, 20.0))
        n, bins, patches = plt.hist(cluster_charge, n_bins, facecolor='green', alpha=0.75, normed=True)
        # plt.axis([0, 500., 0, 0.02])
        plt.grid(True)
        plt.show()
    return cluster_charge

def int_with_commas(x):
    # From http://stackoverflow.com/questions/1823058/how-to-print-number-with-commas-as-thousands-separators
    if type(x) not in [type(0), type(0L)]:
        raise TypeError("Parameter must be an integer.")
    if x < 0:
        return '-' + int_with_commas(-x)
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
    with open('data/bx_fill_4915_run_273162.json') as f:
        data = json.load(f)
    bunch_fill = [0 for x in xrange(n_bx_in_orbit)]
    bunch_fill = [data[str(ix)]['InitialLumi'] for ix, x in enumerate(bunch_fill)]
    return bunch_fill


if __name__ == '__main__':
    # get_bunch_fill()
    # get_cluster_charge(plot=True, nEvents=200)
    main()
