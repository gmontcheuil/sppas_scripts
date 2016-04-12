#!/usr/bin/env python2
# vim: set fileencoding=UTF-8 ts=4 sw=4 expandtab:

#-----------
# Author: Grégoire Montcheuil
# Brief: Some SPPAS tools
#-----------

# Python libraries:
from __future__ import print_function   # print to file/stderr
import sys, os
# Tell python whereis SPPAS API
from os.path import *

# ----------------------------------------------------------------------------
# --- SPPAS tools
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
def load_sppas(opts):
    """ Method to load SPPAS API
        Use global sppas_dir/sppas_version to find the SPPAS directory
        Then import annotationdata.io
    """
    # (a) SPPAS_DIR
    if opts.sppas_dir:
        print("Use argument SPPAS directory:%s" % opts.sppas_dir)
    elif os.environ.get('SPPAS_DIR'):
        opts.sppas_dir=os.environ['SPPAS_DIR']
        print("Use environment variable SPPAS_DIR as SPPAS directory:%s" % opts.sppas_dir)
    else:
        # (a.1) SPPAS_VERSION
        if opts.sppas_version:
            print("Use argument SPPAS version:%s" % opts.sppas_version)
        elif os.environ.get('SPPAS_VERSION'):
            opts.sppas_version=os.environ['SPPAS_VERSION']
            print("Use environment variable SPPAS_VERSION:%s" % opts.sppas_version)
        else:
            opts.sppas_version='1.7.7'
            print("Use default SPPAS_VERSION:%s" % opts.sppas_version)
        #TODO: try 
        opts.sppas_dir=os.path.join(os.environ['HOME'], 'bin', 'sppas-%s' % opts.sppas_version)
        if os.path.isdir(opts.sppas_dir):
            print("Use SPPAS directory:%s" % opts.sppas_dir)
        else:
            sys.exit("Any SPPAS directory !")
    
    sys.path.append(os.path.join(opts.sppas_dir, 'sppas', 'src'))
    # Import SPPAS API
    #global annotationdata
    import annotationdata.io
    # copy 'annotationdata' into __main__ namespace
    import __main__
    __main__.annotationdata = annotationdata
    #print(globals())

# ----------------------------------------------------------------------------
def parserAddLoadSPPASArgument(parser):
    # sppas_dir
    parser.add_argument("-D", "--sppas-dir", dest='sppas_dir'
        , help='change the spass directory (default to SPPAS_DIR environment variable or ${HOME}/bin/sppas-${sppas-version})'
        , metavar='<dir>'
    )
    # sppas_version
    parser.add_argument("-V", "--sppas-version", dest='sppas_version'
        , help='change the spass version (default to SPPAS_VERSION environment variable)'
        , metavar='<str>'
    )

    
# ----------------------------------------------------------------------------
def tierFind(trs, name):
    """ Robust search of a tier.
        Search first for the exact name (ignoring case)
            then for the same name removing all spaces
        @param trs  the annotationdata
        @param name the tier name
    """
    tier = trs.Find(name, case_sensitive=False)
    if tier is not None: return tier; # find with the exact name
    nname = name.lower().replace(" ","")
    for tier in trs:
        tname = tier.GetName().lower().replace(" ","")
        if tname == nname: return tier
        #else: print("Tier name '{}' != '{}' (searched name)".format(tname, nname))
    return None

