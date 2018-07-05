#!/usr/bin/env python2
# vim: set fileencoding=UTF-8 ts=4 sw=4 expandtab:

#-----------
# Author: Grégoire Montcheuil
# Brief: Simple SPPAS script to show information of annotation file(s)
#-----------

# Python libraries:
from __future__ import print_function   # print to file/stderr
import os, argparse
import re

# work in UTF-8
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

# SPPAS tools
import sppas_tools

# script options
opts = argparse.Namespace(
    files=[],
    )

# ----------------------------------------------------------------------------
# --- Script arguments
# ----------------------------------------------------------------------------

parser = argparse.ArgumentParser(description='Show informations about annotation file(s)')
# files
parser.add_argument("files", nargs='+'
    , help="file(s) to process"
    , metavar='<file>'
    )
# sppas_tools: sppas_dir/sppas_version
sppas_tools.parserAddLoadSPPASArgument(parser);


# ----------------------------------------------------------------------------
# --- The real Work
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
def process_files(files, opts):
    """ Process each file
        @param files the file(s) to process
    """
    annotationdata.aio = sppas_tools.getAnnotationdataAio(); # import annotationdata.aio or annotationdata.io
    from annotationdata import Transcription
    for f in files:
        print("[%s] Loading annotation file..." % f)
        # Read an annotated file, put content in a Transcription object.
        trs = annotationdata.aio.read(f)
        print("[%s] Number of tiers:%d" % (f, trs.GetSize()))
        if True:
            print("[%s] Tiers are : %s" % (f, 
                ''.join([ "{}[{}] '{}'".format("\n   " if (i % 4)==0 else ", ", i, t.GetName()) for i, t in enumerate(trs)])
                ))
        print("[%s] Min/Max times: [ %s ; %s ]" % (f, trs.GetMinTime(), trs.GetMaxTime()))
        

# ----------------------------------------------------------------------------
# --- Main stuffs
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
def main():
    """ This is the main function to do something. """
    parser.parse_args(namespace=opts)
    #print(opts)
    if len(opts.files)==0:
        print("ERROR: at least one file to process is required", file=sys.stderr)
        parser.print_help()
        exit(1)
    sppas_tools.load_sppas(opts);
    process_files(opts.files, opts)

# ----------------------------------------------------------------------------
# This is the python entry point:
# Here, we just ask to execute the main function.
if __name__ == '__main__':
    main()
# ----------------------------------------------------------------------------
