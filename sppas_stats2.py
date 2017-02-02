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
from collections import namedtuple, Counter

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
    annotationdata.aio = sppas_tools.getAnnotationdataAio(); # import annotationdata.aio or annotationdata.io
    
    for f in files:
        print("[%s] Loading annotation file..." % f)
        # Read an annotated file, put content in a Transcription object.
        trs = annotationdata.aio.read(f)
        print("[%s] Number of tiers:%d" % (f, trs.GetSize()))
      
        # Compute the intra annotation delays
        mVoc_proc_intra = process_intra(trs, 'Vocabulaire')
        mFb_proc_intra = process_intra(trs, 'M-Feedback', perLabel=True)
        # Compute the feedbacks per (interaction's) phases 
        process_feedback_per_phases(trs, 'M-Feedback', 'Script')
        pFb_proc_intra = process_intra(trs, 'P-Feedback', perLabel=True)
        # Compute the feedbacks per (interaction's) phases 
        process_feedback_per_phases(trs, 'P-Feedback', 'Script')
 
        
        # Compute the intra Feedback/Eyes Direction relation
        process_feedback_eyes(trs, 'M-Feedback', 'M-Regard')
        process_feedback_eyes(trs, 'P-Feedback', 'P-Regard')
        
        # Compute the inter Feedback/Eyes Direction relation
        process_feedback_eyes(trs, 'M-Feedback', 'P-Regard')
        process_feedback_per_phases(trs, 'M-Feedback', 'P-Regard', most_common=True)
        process_feedback_eyes(trs, 'P-Feedback', 'M-Regard')
        process_feedback_per_phases(trs, 'P-Feedback', 'M-Regard', most_common=True)

        # Compute Vocabulaire/P-Feedback relation
        #pFb_mVoc_proc = process_pFb_mVoc(trs, 'P-Feedback', 'Vocabulaire', perLabel=True) # /!\ this create the P-fb-after-M-Voc tier
        pFb_mVoc_proc = process_feedback_after(trs, 'P-Feedback', 'Vocabulaire', after_Max=1., perLabel=True, after_tierAppend=True
            #, after_tierName="P-fb-after-M-Voc"
            ); # /!\ this create the P-fb-after-M-Voc tier
        # Other 'during/after' relations
        process_feedback_after(trs, 'P-Feedback', 'M-Feedback', after_Max=3., perLabel=True);
        process_feedback_after(trs, 'M-Feedback', 'P-Feedback', after_Max=3., perLabel=True);
        # feedback/gestes
        # - Dimensions
        process_feedback_after(trs, 'P-Feedback', 'M-Dimensions', after_Max=1., perLabel=True);
        process_feedback_per_phases(trs, 'P-Feedback', 'M-Dimensions', most_common=True);
        process_feedback_after(trs, 'M-Feedback', 'P-Dimensions', after_Max=1., perLabel=True);
        process_feedback_per_phases(trs, 'M-Feedback', 'P-Dimensions', most_common=True);
        # - Affiliation lexicale
        process_feedback_after(trs, 'P-Feedback', 'M-Affiliation lexicale', after_Max=1., perLabel=True);
        process_feedback_per_phases(trs, 'P-Feedback', 'M-Affiliation lexicale', most_common=True);
        process_feedback_after(trs, 'M-Feedback', 'P-Affiliation lexicale', after_Max=1., perLabel=True);
        process_feedback_per_phases(trs, 'M-Feedback', 'P-Affiliation lexicale', most_common=True);
        # - Lien geste/parole
        process_feedback_after(trs, 'P-Feedback', 'M-Lien geste/parole', after_Max=1., perLabel=True);
        process_feedback_per_phases(trs, 'P-Feedback', 'M-Lien geste/parole', most_common=True);
        process_feedback_after(trs, 'M-Feedback', 'P-Lien geste/parole', after_Max=1., perLabel=True);
        process_feedback_per_phases(trs, 'M-Feedback', 'P-Lien geste/parole', most_common=True);
        # - Extra-communicative G
        process_feedback_after(trs, 'P-Feedback', 'M-Extra-communicative G', after_Max=1., perLabel=True);
        process_feedback_per_phases(trs, 'P-Feedback', 'M-Extra-communicative G', most_common=True);
        process_feedback_after(trs, 'M-Feedback', 'P-Extra-communicatif G', after_Max=1., perLabel=True); # /!\ communicatif
        process_feedback_per_phases(trs, 'M-Feedback', 'P-Extra-communicatif G', most_common=True); # /!\ communicatif

        # Write the resulting file
        of = re.sub(r"\.\w+$", "-fbAfter\g<0>", f)
        print("[%s] Saving file into %s" % (f, of))
        annotationdata.aio.write(of, trs)

# ----------------------------------------------------------------------------
# --- sub-process methods
# ----------------------------------------------------------------------------
def process_intra(trs, tierName='Feedback', perLabel=False):
    """
    Compute some intra-tier statistic
    @param trs: the annotation file or the tier
    @param tierName: the tier name
    """
    #from annotationdata.filter.delay_relations import IntervalsDelay

    res = namedtuple('Intra', "tier,end_start_delays,end_start_delays_stats,middle_middle_delays,middle_middle_delays_stats") # list of fields
    # (0) Get the tier
    res.tier = getTier(trs, tierName)
    if res.tier is None:
        print("[{tierName}] No tier found ;-(".format(**locals()))
        return
    elif len(res.tier)==0:
        print("[{tierName}] tier is empty".format(**locals()))
        return

    # (1) Annotation, duration
    res.durations = durations(res.tier)
    res.duration_stats = stats(res.durations)
    res.radius = radius(res.tier) # max of all begin/end points radius
    print("\t[{tierName}] {tier_len} annotations (time point radius:{res.radius})".format(tier_len=len(res.tier), **locals()))
    print("\t  durations: mean={s.Mean:.3f}, std.dev.={s.StdDev:.3f} [{s.Min:.3f}, {s.Max:.3f}]".format(s=res.duration_stats, **locals()))
    # (2) Compute End-Start and Mid-Mid delays
    intraDelays(res, "\t  ");
    # (3) Stats per label
    if perLabel:
        if len(res.tier)>1:
            statsPerLabel(res.tier, "\t\t", normLabelWithSep
                , intraDelays 
            );
    # return
    return res

def process_pFb_mVoc(trs, pFb_tierName='P-Feedback', mVoc_tierName='Vocabulaire', perLabel=False):
    """
    Process relation between patient feedbacks and medical vocabulary
    """
    from annotationdata import Filter, RelationFilter#, Rel
    from annotationdata.filter.delay_relations import IntervalsDelay, AndPredicates
    
    #TODO? parameters
    pFb_mVoc_tierName='P-fb-after-M-Voc'
    pFbStart_mVocEnd_Max = 1.   # max time between feedback and previous vocabulary


    res = namedtuple('res', "mVoc_tier, mVoc_durations, mVoc_duration_stats, mVoc_radius"
               +", pFb_tier, pFb_durations, pFb_duration_stats, pFb_radius"
               ) # list of fields
    # Search  Vocabulaire and P-Feedback tiers
    not_found=0
    
    # (a) 'Vocabulaire'
    res.mVoc_tier = sppas_tools.tierFind(trs, mVoc_tierName)
    if res.mVoc_tier is None:
        print("\t[{mVoc_tierName}] No medecin's medical vocabulary tier found ;-(".format(**locals()))
        not_found+=1
    # (b) 'P-Feedback'
    res.pFb_tier = sppas_tools.tierFind(trs, pFb_tierName)
    if res.pFb_tier is None:
        print("[{pFb_tierName}] No patient's feedbacks tier found ;-(".format(**locals()))
        not_found+=1
    if not_found:
        print("[%s] %d unfound tier(s) => skip this file")
        return;

    # Combine the 2 tiers
    # - create the predicates
    # [1] pDuringAfter <=> P-feedback(X) start during or a few time(1s) after Vocabulaire (Y)
    #pDuringAfter = IntervalsDelay.create('start_start', (None, 0) # X=Pfb starts after Y=MVoc starts <=> Xs >= Ys <=> Ys-Xs <= 0
    #        , 'start_end', (-pFbStart_mVocEnd_Max, None) # AND X=Pfb starts at least 1s after Y=MVoc ends <=> -inf < Xs-Ye <= 1s <=> -inf > Ye-Xs => 1s
    #        )
    # (a) pStartStart : X (P-feedback) starts after Y (Vocabulaire) starts <=> delay(Xstart - Ystart) >= 0
    pStartStart = IntervalsDelay.create('after', 'start_start_min', 0) # X=Pfb starts after Y=MVoc starts <=> Xs >= Ys <=> Ys-Xs <= 0
    # (b) pStartEnd : X (P-feedback) starts at the latest 1s after Y (Vocabulaire) ends <=> -infinity < delay(Xstart - Yends) <= 1s
    #   nota: -infinity as X can start during Y, the pStartStart allow to eliminate the case of X start before Y
    pStartEnd = IntervalsDelay.create('after', 'start_end', (None, pFbStart_mVocEnd_Max))
    # => 
    pDuringAfter = AndPredicates(pStartStart, pStartEnd)

    fMVoc = Filter(res.mVoc_tier); fPFb=Filter(res.pFb_tier);
    rf = RelationFilter(pDuringAfter,fPFb,fMVoc)
    newtier = rf.Filter(annotformat="{x} [after({y})]")
    newtier.SetName(pFb_mVoc_tierName)
    res.pFb_mVoc_tier = newtier
    print("\t[{pFb_mVoc_tierName}] {tier_len} (of {pFb_len}) patient feedbacks during/after a medic vocabulary".format(tier_len=len(res.pFb_mVoc_tier), pFb_len=len(res.pFb_tier), **locals()))
    trs.Append(newtier) # ?
    #-- # (1) Annotation, duration
    #-- res.pFb_mVoc_durations = durations(res.pFb_mVoc_tier)
    #-- res.pFb_mVoc_duration_stats = stats(res.pFb_mVoc_durations)
    #-- print("\t  durations: mean={s.Mean:.3f}, std.dev.={s.StdDev:.3f} [{s.Min:.3f}, {s.Max:.3f}]".format(s=res.pFb_mVoc_duration_stats, **locals()))
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
        # 'all' annotations
        if groups['all']:
            group=groups['all']
            ssDelays = [rel[0].delay for (x, rel, y) in group]    # rel[0] is pStartStart
            ssStats = stats(ssDelays)
            xDurStats = stats(durations([x for (x, rel, y) in group])) # p-Feedback durations
            yDurStats = stats(durations([y for (x, rel, y) in group])) # Vocabulary durations
            print ("\t  all: {} feedbacks 'linked' to vocabulaire".format(len(group))
                    +"\n\t    Start-Start delays: mean={s.Mean:.3f}, std.dev.={s.StdDev:.3f} [{s.Min:.3f~},{s.Max:.3f~}]".format(s=ssStats)
                    +"\n\t    Vocabulary durations: mean={s.Mean:.3f}, std.dev.={s.StdDev:.3f} [{s.Min:.3f},{s.Max:.3f}]".format(s=yDurStats)
                    +"\n\t    Feedback durations: mean={s.Mean:.3f}, std.dev.={s.StdDev:.3f} [{s.Min:.3f},{s.Max:.3f}]".format(s=xDurStats)
                  )
            if perLabel:
                statsPerLabel([x for (x, rel, y) in group], "\t\t", normLabelWithSep);
            
        if groups['during']:
            group=groups['during']
            ssDelays = [rel[0].delay for (x, rel, y) in group]    # rel[0] is pStartStart
            ssStats = stats(ssDelays)
            ssPercents = [ float((rel[0].delay) / y.GetLocation().GetDuration()) for (x, rel, y) in group]    # at each percent of the Vocabulaire starts the Feedback
            ssPStats = stats(ssPercents)
            print ("\t  during: {} feedbacks starts during the vocabulaire".format(len(group))
                    +"\n\t    Start-Start delays: mean={s.Mean:.3f}, std.dev.={s.StdDev:.3f} [{s.Min:.3f~},{s.Max:.3f~}]".format(s=ssStats)
                    +"\n\t    Percent of Vocabulary when P-Feedback starts: mean={s.Mean:.0%}, std.dev.={s.StdDev:.3f} [{s.Min:.0%},{s.Max:.0%}]".format(s=ssPStats)
                  )
            if perLabel:
                statsPerLabel([x for (x, rel, y) in group], "\t\t", normLabelWithSep);
        if groups['after']:
            group=groups['after']
            ssDelays = [rel[0].delay for (x, rel, y) in group]    # rel[0] is pStartStart
            ssStats = stats(ssDelays)
            seDelays = [rel[1].delay for (x, rel, y) in group]    # rel[1] is pStartEnd
            seStats = stats(seDelays)
            print ("\t  after: {} feedbacks starts (at most {:.3f}s) after the vocabulaire".format(len(group), pFbStart_mVocEnd_Max)
                    +"\n\t    Start-Start delays: mean={s.Mean:.3f}, std.dev.={s.StdDev:.3f} [{s.Min:.3f~},{s.Max:.3f~}]".format(s=ssStats)
                    +"\n\t    Vocabulaire end - P-Feedback start delays: mean={s.Mean:.3f}, std.dev.={s.StdDev:.3f} [{s.Min:.3f~},{s.Max:.3f~}]".format(s=seStats)
                  )
            if perLabel:
                statsPerLabel([x for (x, rel, y) in group], "\t\t", normLabelWithSep);

def process_feedback_after(trs, pFb_tierName='P-Feedback', mVoc_tierName='Vocabulaire', after_Max=1., perLabel=False, after_tierAppend=False, after_tierName=None):
    """
    Process relation between (patient) feedbacks during/after another tier (b.e. Vocabulaire, ...)
    """
    from annotationdata import Filter, RelationFilter#, Rel
    from annotationdata.filter.delay_relations import IntervalsDelay, AndPredicates
    
    #TODO? parameters
    if isinstance(after_tierName, basestring):
        after_tierName = after_tierName.format(**locals());
    else:
        after_tierName = "{pFb_tierName} after {mVoc_tierName}".format(**locals()); # default
    #after_Max = 1.   # max time between feedback and previous vocabulary


    res = namedtuple('res', "mVoc_tier, mVoc_durations, mVoc_duration_stats, mVoc_radius"
               +", pFb_tier, pFb_durations, pFb_duration_stats, pFb_radius"
               ) # list of fields
    # Search  Vocabulaire and P-Feedback tiers
    not_found=0
    
    # (a) 'Vocabulaire'
    res.mVoc_tier = sppas_tools.tierFind(trs, mVoc_tierName)
    if res.mVoc_tier is None:
        print("\t[{mVoc_tierName}] No tier found ;-(".format(**locals()))
        not_found+=1
    # (b) 'P-Feedback'
    res.pFb_tier = sppas_tools.tierFind(trs, pFb_tierName)
    if res.pFb_tier is None:
        print("[{pFb_tierName}] No tier found ;-(".format(**locals()))
        not_found+=1
    if not_found:
        print("[%s] %d unfound tier(s) => skip this file")
        return;

    # Combine the 2 tiers
    # - create the predicates
    # [1] pDuringAfter <=> P-feedback(X) start during or a few time(1s) after Vocabulaire (Y)
    #pDuringAfter = IntervalsDelay.create('start_start', (None, 0) # X=Pfb starts after Y=MVoc starts <=> Xs >= Ys <=> Ys-Xs <= 0
    #        , 'start_end', (-after_Max, None) # AND X=Pfb starts at least 1s after Y=MVoc ends <=> -inf < Xs-Ye <= 1s <=> -inf > Ye-Xs => 1s
    #        )
    # (a) pStartStart : X (P-feedback) starts after Y (Vocabulaire) starts <=> delay(Xstart - Ystart) >= 0
    pStartStart = IntervalsDelay.create('after', 'start_start_min', 0) # X=Pfb starts after Y=MVoc starts <=> Xs >= Ys <=> Ys-Xs <= 0
    # (b) pStartEnd : X (P-feedback) starts at the latest 1s after Y (Vocabulaire) ends <=> -infinity < delay(Xstart - Yends) <= 1s
    #   nota: -infinity as X can start during Y, the pStartStart allow to eliminate the case of X start before Y
    pStartEnd = IntervalsDelay.create('after', 'start_end', (None, after_Max))
    # => 
    pDuringAfter = AndPredicates(pStartStart, pStartEnd)

    fMVoc = Filter(res.mVoc_tier); fPFb=Filter(res.pFb_tier);
    rf = RelationFilter(pDuringAfter, fPFb, fMVoc)
    newtier = rf.Filter(annotformat="{x} [after({y})]")
    res.pFb_mVoc_tier = newtier
    if after_tierAppend:
        newtier.SetName(after_tierName)
        trs.Append(newtier) # ?
    print("\t[{after_tierName}] {tier_len} (of {pFb_len}) {pFb_tierName} during/after({after_Max}s) a {mVoc_tierName}".format(tier_len=len(res.pFb_mVoc_tier), pFb_len=len(res.pFb_tier), **locals()))
    #-- # (1) Annotation, duration
    #-- res.pFb_mVoc_durations = durations(res.pFb_mVoc_tier)
    #-- res.pFb_mVoc_duration_stats = stats(res.pFb_mVoc_durations)
    #-- print("\t  durations: mean={s.Mean:.3f}, std.dev.={s.StdDev:.3f} [{s.Min:.3f}, {s.Max:.3f}]".format(s=res.pFb_mVoc_duration_stats, **locals()))
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
        # 'all' annotations
        for gkey in ['all', 'during', 'after']:
            group=groups[gkey]
            if not len(group):
                continue;
            ssDelays = [rel[0].delay for (x, rel, y) in group]    # rel[0] is pStartStart
            ssStats = stats(ssDelays)
            seDelays = [rel[1].delay for (x, rel, y) in group]    # rel[1] is pStartEnd
            seStats = stats(seDelays)
            xDurStats = stats(durations([x for (x, rel, y) in group])) # p-Feedback durations
            yDurStats = stats(durations([y for (x, rel, y) in group])) # Vocabulary durations
            linked_to = "'linked' to" if gkey=='all' else gkey;
            print("\t  {gkey}: {gsize} {pFb_tierName} {linked_to} a {mVoc_tierName}".format(gsize=len(group), **locals()))
            print("\t    Start-Start delays: mean={s.Mean:.3f}, std.dev.={s.StdDev:.3f} [{s.Min:.3f~},{s.Max:.3f~}]".format(s=ssStats))
            if gkey != 'during':
                print("\t    End-Start delays: mean={s.Mean:.3f}, std.dev.={s.StdDev:.3f} [{s.Min:.3f~},{s.Max:.3f~}]".format(s=seStats))
            print("\t    {mVoc_tierName} durations: mean={s.Mean:.3f}, std.dev.={s.StdDev:.3f} [{s.Min:.3f},{s.Max:.3f}]".format(s=yDurStats, **locals()))
            print("\t    {pFb_tierName} durations: mean={s.Mean:.3f}, std.dev.={s.StdDev:.3f} [{s.Min:.3f},{s.Max:.3f}]".format(s=xDurStats, **locals()))
            if perLabel:
                statsPerLabel([x for (x, rel, y) in group], "\t\t", normLabelWithSep);

def process_feedback_eyes(trs, fb_tierName='Feedback', eyes_tierName='Regard'):
    """
    Process relation between feedbacks and eyes direction
    """
    from annotationdata import Filter, RelationFilter, Rel
    from annotationdata.filter.delay_relations import IntervalsDelay, OrPredicates
    
    #TODO? parameters
    fb_eyes_min_overlap = 1.   # minimum overlap time for overlaps/overlappedby relations


    res = namedtuple('res', "eyes_tier, eyes_radius"
               +", fb_tier, fb_durations, fb_duration_stats, fb_radius"
               ) # list of fields
    # Search  Vocabulaire and P-Feedback tiers
    not_found=0
    
    # (a) 'Vocabulaire'
    res.eyes_tier = sppas_tools.tierFind(trs, eyes_tierName)
    if res.eyes_tier is None:
        print("\t[{eyes_tierName}] No eyes direction tier found ;-(".format(**locals()))
        not_found+=1
    # (b) 'P-Feedback'
    res.fb_tier = sppas_tools.tierFind(trs, fb_tierName)
    if res.fb_tier is None:
        print("[{fb_tierName}] No feedbacks tier found ;-(".format(**locals()))
        not_found+=1
    if not_found:
        print("[%s] %d unfound tier(s) => skip this file")
        return;

    # Combine the 2 tiers
    # - create the predicates
    # [1] 'convergent' a combination of Allen relations for 2 intervals that (partly) overlaps
    pStable = IntervalsDelay.create('start_start_after_min', 0, 'end_end_min', 0, name='stable')    # X during Y <=> X starts after Y and X ends before Y <=> (Xs>Ys) and (Xe<Ye)
    pBefore = IntervalsDelay.create('start_start_after_min', 0, 'start_end_min', 0, 'end_end_after_min', 0, name='before')    # Y ends during X (Y before X) <=> (Xs>Ys) and (Xs<Ye) and (Xe>Ye)
    pInside = IntervalsDelay.create('start_start_min', 0, 'end_end_after_min', 0, name='inside')    # Y inside X <=> X starts before Y and X ends after Y <=> (Xs<Ys) and (Xe>Ye)
    pAfter = IntervalsDelay.create('start_start_min', 0, 'end_start_after_min', 0, 'end_end_min', 0, name='after')    # Y starts during X (Y after X) <=> (Xs<Ys) and (Xe>Ys) and (Xe<Ye)
    #print("pStable={pStable:r}, str()={pStable:s}; pBefore={pBefore:r}, str()={pBefore:s}; pAfter={pAfter:r}, str()={pAfter:s}; pInside={pInside:r}, str()={pInside:s};".format(**locals()))
    #-- pConv = Rel('convergent')
    #-- pConv = OrPredicates( Rel('during') # X during Y => no eyes direction change during the feedback
    #        # Y starts before  Y
    #        , Rel(overlappedby=fb_eyes_min_overlap) # X overlappedby Y (Y starts before X) => eyes direction changes during the feedback
    #        , Rel('finishes')  # X finishes Y (Y starts before X) => eyes direction changes just after the feedback
    #        , IntervalsDelay.create(start_end=(-fb_eyes_min_overlap, 0)) # add -max < start_end < 0
    #        # Y inside X
    #        , Rel('startedby')  # X startedby Y (same start, X longer) => eyes direction changes when the feedback start, and change anoter time ~ contains
    #        , Rel('contains')   # X contains Y => at least 2 changes during the feedback
    #        , Rel('finishedby') # X finishedby Y (same end, X longer) => eyes direction changes during AND just after the feedback
    #        # Y ends after X
    #        , Rel('starts') # X starts Y (same start, Y longer) => eyes direction changes when the feedback start (an is maintain)
    #        , Rel(overlaps=fb_eyes_min_overlap) # X overlaps Y (Y start during X) => eyes direction changes during the feedback
    #        , IntervalsDelay.create(end_start=(0, fb_eyes_min_overlap)) # add 0 < end_start < max
    #--      )
    # nota: OrPredicates orders
    #    if X=Y, all predicates are true
    #    if X finishes Y, pBefore and pStable are true
    #    if X started by Y, pAfter and pStable are true
    pConv = OrPredicates(pInside, pBefore, pAfter, pStable)
    def sbia(rel):
        """
        Classify relation in 'stable', 'before'/'inside'/'after'
        """
        if str(rel) in ['stable', 'before', 'inside', 'after']:
            return str(rel)
        elif str(rel)=='during':
            return 'stable'   # X during Y => stable Y before/inside/after
        elif str(rel) in ['overlappedby', 'finishes']:
            return 'before' # X rel Y => Y starts before X
        elif str(rel) in ['startedby', 'contains', 'finishedby']:
            return 'inside' # X rel Y => Y inside X
        elif str(rel) in ['starts', 'overlaps']:
            return 'after' # X rel Y => Y ends after X
        elif str(rel).startswith('start_end'):
            return 'before' # -max < X start_end Y < 0 => Y ends just before X
        elif str(rel).startswith('end_start'):
            return 'after' # 0 < X end_start Y < max => Y starts just after X
        return; #ERROR

    fEyes = Filter(res.eyes_tier); fFb=Filter(res.fb_tier);
    rf = RelationFilter(pConv,fFb,fEyes)
    rConv = [(x, rel, y) for (x, rel, y) in rf]
    print("\t[{fb_tierName}|{eyes_tierName}] {tier_len} feedbacks-eyes links (for {fb_len} feedbacks and {eyes_len} eyes)".format(tier_len=len(rConv), fb_len=len(res.fb_tier), eyes_len=len(res.eyes_tier), **locals()))
    if len(rConv)==0:
        return  # any feedback linked to eyes direction
    # group relations by name
    if False:
        rels={};
        for (x, rel, y) in rf:
            srel = str(rel)
            if srel not in rels: rels[srel] = []    # init
            rels[srel].append((x, rel, y))
        for srel, lst in rels.items():
            print("\t  '{srel}' {lst_len} feedbacks-eyes links".format(lst_len=len(lst), **locals()))
    # group relation by 1st interval
    xrels={}
    for (x, rel, y) in rf:
        if x not in xrels: xrels[x] = [] # init
        xrels[x].append((x, rel, y))
    # organize the relations associated to x
    xgroups={}; groups={}; # groups
    xtransitions={}  # eye's direction transitions
    for (x, lst) in xrels.items():
        # sort lst 
        lst.sort(cmp=lambda a,b: cmp(a[2], b[2]))   # sort based on y order (a/b = (x, rel, y))
        xtransitions[x]=[]
        xgroups[x] = {}
        # 3 cases:
        # (a) any eyes direction change <=> X during Y  ('stable' group)
        # (b) only one change 'during' X => one Y 'before' (overlappedby; finishes; ~start_end<0) and one Y 'after' (overlaps; ~end_start>0; starts)
        # (b) only various changes 'during' X => one Y 'before' (overlappedby; ~start_end<0), one Y 'after' (overlaps; ~end_start>0), and others Ys 'inside' (contains, startedby, finishedby)
        lastY=None
        for (xi, rel, y) in lst:
            # - transition
            if lastY is not None:
                xtransitions[x].append(' -> '.join([str(lastY.GetLabel().GetValue()), str(y.GetLabel().GetValue())]))
            lastY = y
            # - group
            ygr = sbia(rel)
            if ygr not in xgroups[x]:    xgroups[x][ygr]=[];
            xgroups[x][ygr].append((x, rel, y))
        # In which case we are ?
        if 'stable' in xgroups[x]:  # case (a)
            xgr = 'any'
        elif 'inside' in xgroups[x]:    # case (c)
            xgr = 'various'
        else:   # case (b)
            xgr = 'one'
        if xgr not in groups:   groups[xgr] = [];
        groups[xgr].append(x)
    allTransitionsCnt=Counter();
    allGrRels={'stable':[], 'before':[], 'inside':[], 'after':[]}
    for y1 in ['before', 'inside', 'after']:
        allGrRels["(%s + stable)"%y1]=[]
    for nb in ['any', 'one', 'various']:
        if nb not in groups: continue;
        xAnnots = groups[nb]; lst_len=len(xAnnots)
        percent = float(lst_len) / len(res.fb_tier)
        # groups
        ygroups = []
        if nb=='any':   # 0 changement, only 1 interval <=> X during Y
            print("\t  No change : {lst_len} feedbacks-eyes links ({percent:.1%})".format(**locals()))
            ygroups = ['stable']
        elif nb=='one': # 1 changement, 2 intervals => before/after (i.e. X overlapped by Y[0] and X overlaps Y[1])
            print("\t  One change : {lst_len} feedbacks-eyes links ({percent:.1%})".format(**locals()))
            ygroups = ['before', 'after']
        else: # nb changements, nb+1 intervals => before/contains+/after  (i.e. X overlapped by Y[0] and X contains Y[1:-1] and X overlaps Y[-1])
            print("\t  Various changes : {lst_len} feedbacks-eyes links ({percent:.1%})".format(**locals()))
            ygroups = ['before', 'inside', 'after']
        grRels = {}; yLabels = {}; yLabelsCnt={};
        for ygr in ygroups:
            grRels[ygr] = []
            for x in xAnnots:
                if ygr in xgroups[x]:
                    grRels[ygr] += xgroups[x][ygr];
                #TODO   else: print warning
            allGrRels[ygr] += grRels[ygr]
            if ygr=='stable':
                for y1 in ['before', 'inside', 'after']:
                    allGrRels["(%s + stable)"%y1] += grRels[ygr]
            else:
                allGrRels["(%s + stable)"%ygr] += grRels[ygr]
            yLabels[ygr] = [str(y.GetLabel().GetValue()) for (x, rel, y) in grRels[ygr] ]
            yLabelsCnt[ygr] = Counter(yLabels[ygr]);
            print("\t   {ygr} eyes-direction: {cnt}".format(cnt=counterWithPercent(yLabelsCnt[ygr]), **locals()))
        # transitions
        if nb!='any':
            transitionsCnt=Counter()
            for x in xAnnots:
                if x in xtransitions:
                    transitionsCnt.update(xtransitions[x])
                    #for t in xtransitions[x]: transitionsCnt[t] += 1
            print("\t   transitions: {cnt}".format(cnt=counterWithPercent(transitionsCnt, sep="\n\t                "), **locals()))
            allTransitionsCnt.update(transitionsCnt)
    # ALL
    print("\t  All : {x_len} feedbacks-eyes".format(x_len=len(xrels.keys()), **locals()))
    for ygr in ['stable', 'before', '(before + stable)', 'inside', '(inside + stable)', 'after', '(after + stable)']:
        yLabels[ygr] = [str(y.GetLabel().GetValue()) for (x, rel, y) in allGrRels[ygr] ]
        yLabelsCnt[ygr] = Counter(yLabels[ygr]);
        print("\t   {ygr} eyes-direction: {cnt}".format(cnt=counterWithPercent(yLabelsCnt[ygr]), **locals()))
    print("\t   transitions: {cnt}".format(cnt=counterWithPercent(transitionsCnt, sep="\n\t                "), **locals()))


def process_feedback_per_phases(trs, fb_tierName='P-Feedback', phases_tierName='Script', most_common=False):
    """
    Process relation between feedbacks and 'phases' (Script, eye's directions, ...)
    """
    from annotationdata import Filter, SingleFilter, Sel, RelationFilter, Rel
    from annotationdata.filter.delay_relations import IntervalsDelay, OrPredicates
    
    #TODO? parameters
    fb_phases_min_overlap = 1.   # minimum overlap time for overlaps/overlappedby relations
    
    res = namedtuple('res', "phases_tier, phases, phases_counter, phases_radius, perphases"
               +", fb_tier, fb_durations, fb_duration_stats, fb_radius"
               ) # list of fields

    # looking for phases labels
    not_found=0
    res.phases_tier = sppas_tools.tierFind(trs, phases_tierName)
    # (a) Phases
    if res.phases_tier is None:
        print("\t[{phases_tierName}] No phases tier found ;-(".format(**locals()))
        not_found+=1
    # (b) 'P-Feedback'
    res.fb_tier = sppas_tools.tierFind(trs, fb_tierName)
    if res.fb_tier is None:
        print("[{fb_tierName}] No feedbacks tier found ;-(".format(**locals()))
        not_found+=1
    if not_found:
        print("[%s] %d unfound tier(s) => skip this file")
        return;
    
    # Look for the various phases
    res.phases = []
    res.perphases=dict();
    res.phases_counter = Counter();
    for ph_ann in res.phases_tier:
        phase = ph_ann.GetLabel().GetValue()
        res.phases_counter[phase] += 1
        if res.phases_counter[phase] == 1: #init phases
            res.phases.append(phase)
            res.perphases[phase] = namedtuple('perph', "phase, count, tier, durations, sumduration");
            res.perphases[phase].phase = phase;
    # sum of annotations/durations of phases_tier
    ptSize = len(res.phases_tier); ptSumDurations = sum(durations(res.phases_tier));
    print("\t[{fb_tierName}/{phases_tierName}] {nbphases} phases (#annots:{ptSize}, sum_durations={ptSumDurations:.3f}), {fbsize} feedbacks".format(nbphases=len(res.phases), fbsize=len(res.fb_tier), **locals()))
    if not len(res.phases):
        return res; # any phases

    # sort phases by occurences
    if most_common:
        res.phases = [ phase for (phase,count) in res.phases_counter.most_common() ];
    
    # phases_tier filter
    ptFilter = Filter(res.phases_tier)
    # split feedback tier by phases
    fbFilter = Filter(res.fb_tier)
    phRel = OrPredicates( Rel('during') # fb during the phase
        , Rel('starts') # fb starts with the phase (and is shorter)
        , Rel('finishes') # fb ends with the phase (and is shorter)
        , Rel(overlappedby=fb_phases_min_overlap) # fb overlaped by the phase (i.e. start during the phase but end after)
        #?, Rel('startedby') #? fb starts with the phase and is longer
        )
    #for phase, perph in res.perphases.items():
    for phase in res.phases:
        perph = res.perphases[phase]
        perph.count = res.phases_counter[phase]
        phaseFilter = SingleFilter( Sel(exact=phase), ptFilter)
        perph.tier = phaseFilter.Filter();
        perph.durations = durations(perph.tier)
        perph.sum_durations = sum(perph.durations)
        print("\t  Phase:'{phase}' => #annot={perph.count} ({pannot:.0%}), sum_durations={perph.sum_durations} ({psdur:.0%}) (mean={s.Mean:.3f}, min={s.Min:.3f}, max={s.Max:.3f})".format(s=stats(perph.durations), pannot=float(perph.count)/ptSize, psdur=perph.sum_durations/ptSumDurations, **locals()))
        rf = RelationFilter(phRel, fbFilter, phaseFilter)
        perph.fb_tier = rf.Filter(); perph.fb_count = len(perph.fb_tier)
        perph.fb_durations = durations(perph.fb_tier)
        perph.fb_sum_durations = sum(perph.fb_durations)
        perph.fb_per_sec = perph.fb_count / perph.sum_durations if perph.fb_count else 0;
        perph.sec_per_fb = perph.sum_durations / perph.fb_count if perph.fb_count else 0;
        print("\t   #feedback={perph.fb_count}, freq={perph.fb_per_sec:.3f}/s (every {perph.sec_per_fb:.3f}s), sum_durations={perph.fb_sum_durations:.3f} ({sdurpercent:.0%})".format(sdurpercent=perph.fb_sum_durations/perph.sum_durations, **locals()))
        if perph.fb_count:
            print("\t    durations: mean={s.Mean:.3f}, std.dev.={s.StdDev:.3f} [{s.Min:.3f}, {s.Max:.3f}]".format(s=stats(perph.fb_durations), **locals()))
            statsPerLabel(perph.fb_tier, "\t\t", normLabelWithSep
                #TODO(pb repeated phases)# , intraDelays 
                );
    return res;


## sub-process tools

def statsPerLabel(tier, prefix="", normalize=None, moreStats=None):
    res = namedtuple('res', "labels, labels_count, labels_annotations, labels_durations, labels_sumdurations"
              #+", fb_tier, fb_durations, fb_duration_stats, fb_radius"
          ) # list of fields
    res.labels = []; res.labels_count = Counter();
    res.labels_annotations = dict();
    count=0;
    # group by labels
    for ann in tier:
        count += 1;
        label = ann.GetLabel().GetValue()
        if normalize:
            label = normalize(label)
        res.labels_count[label] += 1
        if res.labels_count[label] == 1:
            res.labels.append(label)
            res.labels_annotations[label] = [] #init
        res.labels_annotations[label].append(ann)
    # durations
    res.labels_durations = dict(); res.labels_sumdurations = dict();
    sum_durations=0; 
    for label in res.labels:
        res.labels_durations[label] = durations(res.labels_annotations[label])
        res.labels_sumdurations[label] = sum(res.labels_durations[label])
        sum_durations += res.labels_sumdurations[label]
    # sort by more frequent (in number)
    for label, nb in res.labels_count.most_common():
        nbpercent= float(nb) / count;
        sdur=res.labels_sumdurations[label];
        sdurpercent = sdur / sum_durations;
        print(prefix+"label:'{label}' nb={nb} ({nbpercent:.0%}), sum_durations={sdur:.3f} ({sdurpercent:.0%})".format(**locals()))
        print(prefix+"  durations: mean={s.Mean:.3f}, std.dev.={s.StdDev:.3f} [{s.Min:.3f}, {s.Max:.3f}]".format(s=stats(res.labels_durations[label]), **locals()))
        if moreStats:
            moreStats(res.labels_annotations[label], prefix=prefix+"  ");
    
def intraDelays(res, prefix=""):
    """
    Compute the End-Start and Mid-Mid delays stats
    """
    from annotationdata.filter.delay_relations import IntervalsDelay
    # check res.tier or res is the tier
    if not hasattr(res, 'tier'):
        tier = res;
        res = namedtuple('res', "tier, end_start_delays, end_start_delays_stats, middle_middle_delays, middle_middle_delays_stats")
        res.tier = tier

    # (2) Compute End-Start and Mid-Mid delays
    if len(res.tier)>1:
        esPred = IntervalsDelay.create('end_start_min',0.)  # compute the end-start delays
        mmPred = IntervalsDelay.create('mid_mid_min',0.)  # compute the middle-middle delays
        res.end_start_delays=[]; res.middle_middle_delays=[];
        lastAnn=None
        for ann in res.tier:
            # inter annotation delays
            if lastAnn is not None:
                res.end_start_delays.append(esPred(lastAnn, ann))
                res.middle_middle_delays.append(mmPred(lastAnn, ann))
            lastAnn = ann
        res.end_start_delays_stats = stats(res.end_start_delays);
        res.middle_middle_delays_stats = stats(res.middle_middle_delays)
        firstStart = res.tier[0].GetLocation().GetBeginMidpoint()
        firstMiddle = (res.tier[0].GetLocation().GetBeginMidpoint() + res.tier[0].GetLocation().GetEndMidpoint()) / 2;
        print(prefix+"first start at {firstStart}, inter end-start delays: mean={s.Mean:.3f}, std.dev.={s.StdDev:.3f} [{s.Min:.3f~}, {s.Max:.3f~}]".format(s=res.end_start_delays_stats, **locals()))
        print(prefix+"first middle point at {firstMiddle}, inter middle-middle delays: mean={s.Mean:.3f}, std.dev.={s.StdDev:.3f} [{s.Min:.3f~}, {s.Max:.3f~}]".format(s=res.middle_middle_delays_stats, **locals()))
    return res;

def normLabelWithSep(label, split="\s*\+\s*", sep=" + ", sort=True):
    elems = re.split(split, label)
    if sort:
        elems = sorted(elems)
    return sep.join(elems)

def counterWithPercent(cnt, sep=', ', order='most_common', fmt='"{k}":{v} ({p:.1%})'):
    s = sum(cnt.values())
    items = cnt.most_common() if order=='most_common' else cnt.items()
    if order=='keys':
        items = sort(items, cmp=lambda a,b: cmp(a[0], b[0]))    # sort based on keys
    return sep.join([fmt.format(k=k, v=v, p=float(v)/s) for (k,v) in items])


def radius(tier):
    """
    Get the (maximum) radius of tier's annotation points
    """
    radiusList = [ann.GetLocation().GetBeginRadius() for ann in tier] # all begin points radius
    radiusList += [ann.GetLocation().GetEndRadius() for ann in tier] # add end point radius
    return max(radiusList) # max of all begin/end points radius

def durations(tier):
    """
    Get the list of duration of tier's annotations
    """
    return [ann.GetLocation().GetDuration().GetValue() for ann in tier]

def getTier(trs, tierName=None, errorMsg=None):
    """
    Get the corresponding tier
    @param trs: an annotation file or a tier
    @param tierName: the tier name
    @param errorMsg:    (optional) message (format) for the ValueError raised if no tier is found
        if falsy, any ValueError is raised (=> return is None)
    @return:    the tier found or None
    """
    from annotationdata import Tier
    if isinstance(trs, Tier):
        #TODO? check tierName
        return trs
    tier = sppas_tools.tierFind(trs, tierName)
    if tier is None and errorMsg:
        raise ValueError(errorMsg.format(**locals()))
    return tier


# ----------------------------------------------------------------------------
# --- Statistic methods
# ----------------------------------------------------------------------------

def stats(lst):
    """
    Compute various statistics
    @rtype: something with attributes:
        - Max/Min : the maximum value
        - Mean : the mean value
    """
    stats = namedtuple('Stats', "Min,Max,Mean,StdDev") # list of fields
    stats.Min = min(lst) if len(lst) else 0.;
    stats.Max = max(lst) if len(lst) else 0.;
    stats.Mean = mean(lst) if len(lst) else 0.;
    stats.StdDev = stddev(lst, stats.Mean) if len(lst) else 0.;
    return stats

def mean(lst):
    """
    Compute the mean of the values of a list
    @param lst: the list of values
    @rtype: float
    """
    from annotationdata.filter.delay_relations import Delay
    sum_=0.; n=0;
    for v in lst:
        value, margin = Delay.unpack(v) # safer way to get the value part, as float(Duration) didn't work
        sum_ += float(value); n+=1
    return sum_/n if n else 0;

def stddev(lst, mean=None):
    """
    Compute the standard deviation of the values of a list
    @param lst: the list of values
    @param mean: (optinal) a values mean if yet computed
    @rtype: float
    """
    if mean is None:
        mean = mean(lst)
    from annotationdata.filter.delay_relations import Delay
    sum_=0.; n=0;
    for v in lst:
        value, margin = Delay.unpack(v) # safer way to get the value part, as float(Duration) didn't work
        sum_ += (float(value)-mean) ** 2; n+=1
    return (sum_/n) ** 0.5 if n else 0;

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
