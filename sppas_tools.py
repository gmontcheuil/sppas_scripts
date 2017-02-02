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
#from os.path import *

# ----------------------------------------------------------------------------
# --- SPPAS tools
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
def load_sppas(opts):
    """ Method to load SPPAS API
        Use global sppas_dir/sppas_version to find the SPPAS directory
        Then import annotationdata
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
    
    sppas_path = os.path.abspath(os.path.join(opts.sppas_dir, 'sppas', 'src'))
    sys.path.insert(0,sppas_path)
    # Import SPPAS API
    #global annotationdata
    import annotationdata
    # copy 'annotationdata' into __main__ namespace
    import __main__
    __main__.annotationdata = annotationdata
    #print(globals())

def getAnnotationdataAio():
    """ Return the SPPAS annotationdata.aio module
         (or annotationdata.io from older version)
    """
    try:
        import annotationdata.aio as aio
        #print("annotationdata.aio imported as aio")
    except ImportError:
        import annotationdata.io as aio
        #print("annotationdata.io imported as aio")
    #import __main__
    #__main__.aio = aio
    return aio


# ----------------------------------------------------------------------------
def parserAddLoadSPPASArgument(parser):
    if parser is None:
        import argparse
        parser = argparse.ArgumentParser()
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
    return parser;

    
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

def parentdir(f, level=0):
    i=0; p=f;
    while (i<level):
        p = os.path.dirname(p);
        i+=1
    return os.path.dirname(p)

# ----------------------------------------------------------------------------
def main():
    """ This is the main function to do something. """
    import argparse
    # (A) Create the argument parser
    parser = argparse.ArgumentParser(description='Test the sppas_tools module')
    # and add the SPPAS arguments
    parserAddLoadSPPASArgument(parser);
    # (B) Parse the script arguments
    opts = argparse.Namespace() # create the result
    parser.parse_args(namespace=opts)
    print("Parsed options are :", opts)
    # (C) Loas SPPAS (annotationdata)
    load_sppas(opts);
    spassdir = parentdir(annotationdata.__file__, 3); # sppas/src/annotationdata => 3 level
    print("SPPAS is loaded from: '%s' (real path: '%s')" % (spassdir, os.path.realpath(spassdir)))


# ----------------------------------------------------------------------------
# This is the python entry point:
# Here, we just ask to execute the main function.
if __name__ == '__main__':
    main()
# ----------------------------------------------------------------------------
