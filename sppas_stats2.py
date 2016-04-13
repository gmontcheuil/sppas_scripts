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
    from annotationdata.filter.delay_relations import IntervalsDelay, Delay
    
    p = IntervalsDelay.create('start_start', (None, 0) # X=Pfb starts after Y=MVoc starts <=> Xs >= Ys <=> Ys-Xs <= 0
            , 'start_end', (-1, None) # AND X=Pfb starts at least 1s after Y=MVoc ends <=> -inf < Xs-Ye <= 1s <=> -inf > Ye-Xs => 1s
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
        #rf = RelationFilter(p,fMVoc,fPFb) # we us the 'reverse' relation
        #newtier = rf.Filter(annotformat="{x} [{rel}({y})]")
        newtier = rf.Filter(annotformat="{x} [after({y})]")
        #newtier = rf.Filter(annotformat="{y} [after({x})]") # we us the 'reverse' relation
        newtier.SetName('P-fb-after-M-Voc')
        print("[%s] filter tier %s has %d annotations" % (f, newtier.GetName(), newtier.GetSize()))
        trs.Append(newtier)
        # Analyse rf results
        if True:
            groups = {'after':[], 'overlap':[]}
            for x, rel, y in rf:
                if rel[1].delay<0:    # rel is a conjunction of 2 relations, the second give use the Xstart-Yend delay
                    groups['after'].append((x, rel, y)); # feedback start after the vocabulaire
                else:
                    groups['overlap'].append((x, rel, y)); # feedback start during the vocabulaire
            if groups['overlap']:
                ssmean = mean(-rel[0].delay for (x, rel, y) in groups['overlap'])
                sspercentmean = mean( (-rel[0].delay / (y.GetLocation().GetDuration())) for (x, rel, y) in groups['overlap'])
                print ("{} feedbacks starts during the 'vocabulaire'".format(len(groups['overlap']))
                      +"\n\tStart-Start mean delay is {}".format(ssmean)
                      +"\n\tFeedback mean start is at {:%} of the Voc".format(ssmean)
                      )
            if groups['after']:
                ssmean = mean(-rel[0].delay for (x, rel, y) in groups['after'])
                esmean = mean(-rel[1].delay for (x, rel, y) in groups['after'])
                print ("{} feedbacks starts after the 'vocabulaire'".format(len(groups['after']))
                      +"\n\tStart-Start mean delay is {}".format(ssmean)
                      +"\n\tVoc end - FB start mean delay is {}".format(esmean)
                      +"\n\tVoc end - FB start delays are {}".format([-rel[1].delay for (x, rel, y) in groups['after']])
                      )

        # Write the resulting file
        of = re.sub(r"\.\w+$", "-fbAfter\g<0>", f)
        print("[%s] Saving file into %s" % (f, of))
        annotationdata.io.write(of, trs)


def mean(list_):
    """
    Compute the mean of the values of a list
    """
    sum_=0.; n=0;
    for v in list_:
        sum_ += float(v); n+=1
    return sum_/n if n else 0;


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
