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
from collections import namedtuple

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
    from annotationdata.filter.delay_relations import IntervalsDelay, Delay, AndPredicates
    
    # create the predicates
    # [1] pDuringAfter <=> P-feedback(X) start during or a few time(1s) after Vocabulaire (Y)
    FbStart_VocEnd_Max = 1.   # max time between feedback and previous vocabulary
    #pDuringAfter = IntervalsDelay.create('start_start', (None, 0) # X=Pfb starts after Y=MVoc starts <=> Xs >= Ys <=> Ys-Xs <= 0
    #        , 'start_end', (-FbStart_VocEnd_Max, None) # AND X=Pfb starts at least 1s after Y=MVoc ends <=> -inf < Xs-Ye <= 1s <=> -inf > Ye-Xs => 1s
    #        )
    # (a) pStartStart : X (P-feedback) starts after Y (Vocabulaire) starts <=> delay(Xstart - Ystart) >= 0
    pStartStart = IntervalsDelay.create('after', 'start_start_min', 0) # X=Pfb starts after Y=MVoc starts <=> Xs >= Ys <=> Ys-Xs <= 0
    # (b) pStartEnd : X (P-feedback) starts at the latest 1s after Y (Vocabulaire) ends <=> -infinity < delay(Xstart - Yends) <= 1s
    #   nota: -infinity as X can start during Y, the pStartStart allow to eliminate the case of X start before Y
    pStartEnd = IntervalsDelay.create('after', 'start_end', (None, FbStart_VocEnd_Max))
    # => 
    pDuringAfter = AndPredicates(pStartStart, pStartEnd)
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

        # Compute the inter P-Feedback delays
        if len(tPFb)>1:
            esPred = IntervalsDelay.create('end_start_min',0.)  # compute the end-start delay
            esDelays=[]
            lastAnn=None
            for ann in tPFb:
                if lastAnn is not None:
                    esDelays.append(esPred(lastAnn, ann))
                lastAnn = ann
            esDelaysStats = stats(esDelays)
            firstStart = tPFb[0].GetLocation().GetBegin()
            #print("[{f}] First P-Feedback at {firstStart}, inter-feedbacks delays: {esDelays}".format(**locals()))
            print("\tFirst P-Feedback at {firstStart}, inter-feedbacks delays: mean={s.Mean:.3f} [{s.Min:.3f~.3f}, {s.Max:.3f~.3f}]".format(s=esDelaysStats, **locals()))


        # Combine the 2 tiers
        fMVoc = Filter(tMVoc); fPFb=Filter(tPFb);
        rf = RelationFilter(pDuringAfter,fPFb,fMVoc)
        #rf = RelationFilter(pDuringAfter,fMVoc,fPFb) # we us the 'reverse' relation
        #newtier = rf.Filter(annotformat="{x} [{rel}({y})]")
        newtier = rf.Filter(annotformat="{x} [after({y})]")
        #newtier = rf.Filter(annotformat="{y} [after({x})]") # we us the 'reverse' relation
        newtier.SetName('P-fb-after-M-Voc')
        print("[%s] filter tier %s has %d annotations" % (f, newtier.GetName(), newtier.GetSize()))
        trs.Append(newtier)
        # Analyse rf results
        if True:
            groups = {'after':[], 'during':[], 'all':[]}
            # group result between after/during
            for x, rel, y in rf:
                groups['all'].append((x, rel, y))
                if rel[1].delay > 0:    # rel[1] correspond to pStartEnd => give use the Xstart-Yend delay
                    groups['after'].append((x, rel, y)); # feedback start strictly after the vocabulaire
                else:
                    groups['during'].append((x, rel, y)); # feedback start during the vocabulaire
            if groups['all']:
                group=groups['all']
                ssDelays = [rel[0].delay for (x, rel, y) in group]    # rel[0] is pStartStart
                ssStats = stats(ssDelays)
                yDurStats = stats([y.GetLocation().GetDuration().GetValue() for (x, rel, y) in group]) # Vocabulary durations
                xDurStats = stats([x.GetLocation().GetDuration().GetValue() for (x, rel, y) in group]) # p-Feedback durations
                print ("all: {} feedbacks 'linked' to vocabulaire".format(len(group))
                        +"\n\tStart-Start delays: mean={s.Mean:.3f} [{s.Min:.3f},{s.Max:.3f}]".format(s=ssStats)
                        +"\n\tVocabulary durations: mean={s.Mean:.3f} [{s.Min:.3f},{s.Max:.3f}]".format(s=yDurStats)
                        +"\n\tFeedback durations: mean={s.Mean:.3f} [{s.Min:.3f},{s.Max:.3f}]".format(s=xDurStats)
                      )
            if groups['during']:
                group=groups['during']
                ssDelays = [rel[0].delay for (x, rel, y) in group]    # rel[0] is pStartStart
                ssStats = stats(ssDelays)
                ssPercents = [ float((rel[0].delay) / y.GetLocation().GetDuration()) for (x, rel, y) in group]    # at each percent of the Vocabulaire starts the Feedback
                ssPStats = stats(ssPercents)
                print ("during: {} feedbacks starts during the 'vocabulaire'".format(len(group))
                        +"\n\tStart-Start delays: mean={s.Mean:.3f} [{s.Min:.3f},{s.Max:.3f}]".format(s=ssStats)
                        +"\n\tPercent of Vocabulary when P-Feedback starts: mean={s.Mean:.0%} [{s.Min:.0%},{s.Max:.0%}]".format(s=ssPStats)
                      )
            if groups['after']:
                group=groups['after']
                ssDelays = [rel[0].delay for (x, rel, y) in group]    # rel[0] is pStartStart
                ssStats = stats(ssDelays)
                seDelays = [rel[1].delay for (x, rel, y) in group]    # rel[1] is pStartEnd
                seStats = stats(seDelays)
                print ("after: {} feedbacks starts (at most {:.3f}s) after the 'vocabulaire'".format(len(group), FbStart_VocEnd_Max)
                        +"\n\tStart-Start delays: mean={s.Mean:.3f} [{s.Min:.3f},{s.Max:.3f}]".format(s=ssStats)
                        +"\n\tVocabulaire end - Feedback start delays: mean={s.Mean:.3f} [{s.Min:.3f},{s.Max:.3f}]".format(s=seStats)
                      )

        # Write the resulting file
        of = re.sub(r"\.\w+$", "-fbAfter\g<0>", f)
        print("[%s] Saving file into %s" % (f, of))
        annotationdata.io.write(of, trs)

# ----------------------------------------------------------------------------
# --- Statistic methods
# ----------------------------------------------------------------------------

def stats(list_):
    """
    Compute various statistics
    @rtype: something with attributes:
        - Max/Min : the maximum value
        - Mean : the mean value
    """
    stats = namedtuple('Stats', "Min,Max,Mean") # list of fields
    stats.Min = min(list_)
    stats.Max = max(list_)
    stats.Mean = mean(list_)
    return stats

def mean(list_):
    """
    Compute the mean of the values of a list
    @rtype: float
    """
    from annotationdata.filter.delay_relations import Delay
    sum_=0.; n=0;
    for v in list_:
        value, margin = Delay.unpack(v) # safer way to get the value part, as float(Duration) didn't work
        sum_ += float(value); n+=1
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
