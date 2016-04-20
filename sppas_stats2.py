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
    
    for f in files:
        print("[%s] Loading annotation file..." % f)
        # Read an annotated file, put content in a Transcription object.
        trs = annotationdata.io.read(f)
        print("[%s] Number of tiers:%d" % (f, trs.GetSize()))
        
        # Compute the intra annotation delays
        mVoc_proc_intra = process_intra(trs, 'Vocabulaire')
        mFb_proc_intra = process_intra(trs, 'M-Feedback')
        pFb_proc_intra = process_intra(trs, 'P-Feedback')
        
        # Compute the intra Feedback/Eyes Direction relation
        process_feedback_eyes(trs, 'M-Feedback', 'M-Regard')
        process_feedback_eyes(trs, 'P-Feedback', 'P-Regard')
        
        # Compute the inter Feedback/Eyes Direction relation
        process_feedback_eyes(trs, 'M-Feedback', 'P-Regard')
        process_feedback_eyes(trs, 'P-Feedback', 'M-Regard')

        # Compute Vocabulaire/P-Feedback relation
        pFb_mVoc_proc = process_pFb_mVoc(trs, 'P-Feedback', 'Vocabulaire') # /!\ this create the P-fb-after-M-Voc tier

        # Write the resulting file
        of = re.sub(r"\.\w+$", "-fbAfter\g<0>", f)
        print("[%s] Saving file into %s" % (f, of))
        annotationdata.io.write(of, trs)

# ----------------------------------------------------------------------------
# --- sub-process methods
# ----------------------------------------------------------------------------
def process_intra(trs, tierName='Feedback'):
    """
    Compute some intra-tier statistic
    @param trs: the annotation file or the tier
    @param tierName: the tier name
    """
    from annotationdata.filter.delay_relations import IntervalsDelay

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
        print("\t  first start at {firstStart}, inter end-start delays: mean={s.Mean:.3f}, std.dev.={s.StdDev:.3f} [{s.Min:.3f~}, {s.Max:.3f~}]".format(s=res.end_start_delays_stats, **locals()))
        print("\t  first middle point at {firstMiddle}, inter middle-middle delays: mean={s.Mean:.3f}, std.dev.={s.StdDev:.3f} [{s.Min:.3f~}, {s.Max:.3f~}]".format(s=res.middle_middle_delays_stats, **locals()))
    # return
    return res

def process_pFb_mVoc(trs, pFb_tierName='P-Feedback', mVoc_tierName='Vocabulaire'):
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

def process_feedback_eyes(trs, fb_tierName='Feedback', eyes_tierName='Regard'):
    """
    Process relation between feedbacks and eyes direction
    """
    from annotationdata import Filter, RelationFilter, Rel
    from annotationdata.filter.delay_relations import IntervalsDelay, OrPredicates
    
    #TODO? parameters
    fb_eyes_tierName='P-fb-after-M-Voc'
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



## sub-process tools

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
    stats.Min = min(lst)
    stats.Max = max(lst)
    stats.Mean = mean(lst)
    stats.StdDev = stddev(lst, stats.Mean)
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
