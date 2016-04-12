#!/usr/bin/env python2
# vim: set fileencoding=UTF-8 ts=4 sw=4 expandtab:

#-----------
# Author: Grégoire Montcheuil
# Brief: Simple SPPAS script to analyse ACORFORMED elan file(s)
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

parser = argparse.ArgumentParser(description='Statistics on input file(s)')
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
    from annotationdata import Rel, Filter, RelationFilter
    
    p = ( Rel("equals") # P-Fb equals M-Voc
        | Rel(after=1.) # P-Fb after M-Voc (max: 1s)
        | Rel("metby") # P-Fb metby M-Voc (i.e. P-Fb just after M-Voc)
        | Rel("overlappedby") # P-Fb overlapped by M-Voc (i.e. P-Fb starts during M-Voc)
        | Rel("starts") | Rel("startedby") # P-Fb start at same time of M-Voc
        | Rel("finishedby") # P-Fb starts after M-Voc and ends at same time
        | Rel("during") # P-Fb starts after M-Voc and ends before
        )
    for f in files:
        print("[%s] Loading annotation file..." % f)
        # Read an annotated file, put content in a Transcription object.
        trs = annotationdata.io.read(f)
        print("[%s] Number of tiers:%d" % (f, trs.GetSize()))
        
        # Search  Vocabulaire and P-Feedback tiers
        not_found=0
        # (a) 'Vocabulaire'
        tMVocName='Vocabulaire'
        tMVoc = sppas_tools.tierFind(trs, tMVocName)
        if tMVoc is None:
            print("[%s] No medecin's medical vocabulary tier find (%s) ;-(" % (f, tMVocName))
            not_found+=1
        else:
            print("[%s] Medecin's medical vocabulary tier (%s) has %d annotations" % (f, tMVoc.GetName(), tMVoc.GetSize()))
        # (b) 'P-Feedback'
        tPFbName='P-Feedback'
        tPFb = sppas_tools.tierFind(trs, tPFbName)
        if tPFb is None:
            print("[%s] No patient's feedbacks tier find (%s) ;-(" %  (f, tPFbName))
            not_found+=1
        else:
            print("[%s] Patient's feedbacks tier (%s) has %d annotations" % (f, tPFb.GetName(), tPFb.GetSize()))
        if not_found:
            print("[%s] %d unfound tier(s) => skip this file")
            break;

        # Combine the 2 tiers
        fMVoc = Filter(tMVoc); fPFb=Filter(tPFb);
        rf = RelationFilter(p,fPFb,fMVoc)
        newtier = rf.Filter(annotformat="{x} [{rel}({y})]")
        newtier.SetName('P-fb-after-M-Voc')
        print("[%s] filter tier %s has %d annotations" % (f, newtier.GetName(), newtier.GetSize()))
        trs.Append(newtier)

        # Write the resulting file
        of = re.sub(r"\.\w+$", "-fbAfter\g<0>", f)
        print("[%s] Saving file into %s" % (f, of))
        annotationdata.io.write(of, trs)



        


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
