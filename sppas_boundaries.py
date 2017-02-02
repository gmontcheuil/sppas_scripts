#!/usr/bin/env python2
# vim: set fileencoding=UTF-8 ts=4 sw=4 expandtab:

#-----------
# Author: Grégoire Montcheuil
# Brief: SPPAS script to generate a boundaries tier
#-----------

# Python libraries:
from __future__ import print_function   # print to file/stderr
import os, argparse
from argparse import RawTextHelpFormatter
import re

# work in UTF-8
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

# SPPAS tools
import sppas_tools

# script options
opts = argparse.Namespace(
    # Input
    files=[],
    tiers_names=[],
    # Boundaries tier(s)
    radius=-1., # BILOU TimePoint radius
    begin_format="{:.1}", end_format="{:.1}",   # begin/end tag format
    out_tier_format="Boundaries - {:s}",
    bound_type='point',   # generate points or intervals
    # Equals tier(s)
    equals_tier=False,
    equals_label_format="SameTime({x},{y})",
    equals_tier_format="Boundaries {:s} VS {:s}",
    # Output
    keep_tiers="process", # in the output keep : 'all' tiers (default), 'process(ed)' tiers or 'any' (i.e. only the BILOU)
    out_file_format="{:s}-bound_{:s}",    # output file format (before the extension), 1st element is the filename (without extension), 2nd is the tier(s) name(s)
    )

# ----------------------------------------------------------------------------
# --- Script arguments
# ----------------------------------------------------------------------------

parser = argparse.ArgumentParser(description='Create Boundaries tier(s)',formatter_class=RawTextHelpFormatter)
# Input
# - file(s)
parser.add_argument("files", nargs='+'
    , help="file(s) to process"
    , metavar='<file>'
    )
# - tier(s)_name(s)
parser.add_argument("-t", "--tier", "--tier-name", action='append', dest='tiers_names'
    , help="tier(s) to process (repeat the option to process various tiers)."
    , metavar='<tier>'
    , required=True
    )
# Boundaries tier(s)
# - bound_type
#parser.add_argument("--type", dest='type'
#        , help="type of boundaries: 'point(s)' or 'interval(s)' (default:'%f')"%opts.bound_type
#    , metavar='<type>'
#    , choices=['point','points','interval','intervals']
#    )
parser.add_argument("-p","--point", "--points", dest='bound_type'
        , action='store_const'# , nargs=0
        , const='point'
        , help="Use points for the boundaries%s"%(" (default)" if opts.bound_type.startswith('point') else "")
    )
parser.add_argument("-i","--interval", "--intervals", dest='bound_type'
        , action='store_const'# , nargs=0
        , const='interval'
        , help="Use intervals for the boundaries%s"%(" (default)" if opts.bound_type.startswith('interval') else "")
    )
# - radius
parser.add_argument("-r", "--radius", dest='radius', type=float
        , help=("precision (radius) of the boundaries points/intervals (default:'%f', negative=>keep original)"%opts.radius)
            +"\n\tIn case of 'points', serve to compare points (see --equals options) - and some formats storing the radius."
                +" Negative value => keep original radius - 0.0005 (0.5ms) by default."
            +"\n\tIn case of 'intervals', it's the half of the intervals size (and also serve to compare (see --equals options)."
                +" Negative value => use the points radius - 0.0005 (0.5ms) by default."
    , metavar='<second>'
    )
# - Begin/End labels format
parser.add_argument("--begin-format", dest='begin_format'
        , help=("Format of the Begin labels (default:'%s')."%opts.begin_format)
            +"\n\tFirst field({0:}) is for Begin"
            +"\n\tSecond field({1:}) is for the annotation label"
            +"\nExamples:"
            +"\n\t'{}-{}' => full word with label, e.g.'Begin-Label'"
            +"\n\t'{:.1}-{}' => first letter with label, e.g.'B-Label'"
            +"\n\t'{:.1}' => first letter without label, e.g.'B'"
            +"\n\t'bound' => fixed value"
    , metavar='<format>'
    )
parser.add_argument("--end-format", dest='end_format'
        , help=("Format of the End labels (default:'%s')."%opts.end_format)
            +"\n\tFirst field({0:}) is for End"
            +"\n\tSecond field({1:}) is for the annotation label"
            +"\nSee --begin-format"
    , metavar='<format>'
    )
# - Output/Boundaries tier(s) format
parser.add_argument("--out-tier", "--out-tier-format", "--bound-tier-format", dest='out_tier_format'
        , help=("Format for the Boundaries tier(s) name (default:'%s')"%opts.out_tier_format)
            +"\n\tThe field({}) is for the processed tier's name"
    , metavar='<format>'
    )
# Equals tier(s)
parser.add_argument("-e","--equals", "--equals-tier", dest='equals_tier'
        , action='store_const'# , nargs=0
        , const=True
        , help="Calculate equals boundaries (only if various tiers, compared to the first one)"
    )
# - Equals label format
parser.add_argument("--equals-label", "--equals-label-format", dest='equals_label_format'
        , help=("Format for the Equals tier(s) labels (default:'%s')"%opts.equals_label_format)
            +"\n\tField 'x' ({x:}) is the current tier label"
            +"\n\tField 'y' ({y:}) is the reference tier label (i.e. the first tier)"
            +"\n\tField 'rel' ({rel:}) is the relation name ('equals' or 'convergent' for intervals)"
    , metavar='<format>'
    )
# - Equals tier(s) format
parser.add_argument("--equals-tier-format", dest='equals_tier_format'
        , help=("Format for the Equals tier(s) name (default:'%s')"%opts.equals_tier_format)
            +"\n\tFirst field({0:}) is the current tier name"
            +"\n\tSecond field({1:}) is the reference tier name (i.e. the first tier)"
    , metavar='<format>'
    )
# Output
# - Output file (format)
parser.add_argument("-o","--outfile", "--outfile-format", dest='out_file_format'
        , help=("Format for the output file without extension(default:'%s')."%opts.out_file_format)
            +"\n\tFirst field({0:}) is the file name without extension."
            +"\n\tSecond field({1:}) is the tier(s) name(s) (join with '+' if various)"
    , metavar='<format>'
    )
# - Tiers to keep in the output file
parser.add_argument("-k","--keep", "--keep-tiers", dest='keep_tiers'
        , help=("Tiers to keep in the output (default:'%s')"%opts.keep_tiers)
            +"\n\t'all' => keep all original tiers (Boundaries tiers are append to the end)"
            +"\n\t'process' (or 'processed') => keep only processed tiers (Boundaries tiers are added after each processed tier)"
            +"\n\t'any'/'boundaries' => keep any original tier, output only the Boundaries tiers"
    , metavar='(all|process|any)'
    , choices=['all','process','processed','any','bounds', 'boundaries']
    )
#TODO: output extension
# sppas_tools: sppas_dir/sppas_version
sppas_tools.parserAddLoadSPPASArgument(parser);


# ----------------------------------------------------------------------------
# --- The real Work
# ----------------------------------------------------------------------------


def boundaries(ref,radius,bound_type='point',minTime=0.,maxTime=None,begin_format="{:.1}({})",end_format="{:.1}({})"):
    from annotationdata import TimePoint, TimeInterval, Annotation, Label
    """ Compute the Boundaries point/intervals corresponding to a tier.
        Example:
          ref =       [--1---]     [-2--]   [--3--]     [4]     [--5--]
           =>         B      E     B    E   B     E     B E     B     E
           or       [ B ]  [ E ] [ B ][ E | B ] [ E ] [ B|E ] [ B ] [ E ]
          nota: In the case of intervals, sometime they are shorter to avoid overlap,
                like between [2] and [3] or inside [4]
        @param ref  the reference tier (were are the annotation)
        @param bound_type   points or intervals
        @param radius   new points radius (if non-negative) or intervals precision
        @param begin_format  format for the Begin labels.
            The first format parameter is Begin
            The second is the reference tier label.
            Default: "{:.1}()}", p.e. "B(label)"
        @param end_format  format for the End labels.
            see begin_format
        
        @return the list of boundaries annotations
    """
    # usefull value
    build_intervals = bound_type.startswith('interval');
    # iterator on the reference's intervals
    def nextRef(it):
        annot = nextOrNone(it);
        while (not annotHasLabel(annot,True)):
            #sys.stderr.write('#'); sys.stderr.flush(); # debug
            annot = nextOrNone(it);
        return annot;
    itRef = iter(ref);

    boundaries = []
    refAnnot = nextRef(itRef);
    while (refAnnot is not None):
        # (a) get begin/end point
        beginPoint = annotBegin(refAnnot);
        endPoint = annotEnd(refAnnot);
        # compute the Begin/End labels
        beginLabel = Label(begin_format.format('Begin', refAnnot.GetLabel().GetValue()))
        endLabel = Label(end_format.format('End', refAnnot.GetLabel().GetValue()))
        # (b) adjust radius/build interval for refAnnot
        beginAnnot = endAnnot = None
        if (build_intervals):
            beginP1 = TimePointSub(beginPoint, radius, minTime)
            beginP2 = TimePointAdd(beginPoint, radius, maxTime)
            endP1 = TimePointSub(endPoint, radius, minTime)
            endP2 = TimePointAdd(endPoint, radius, maxTime)
            beginAnnot = Annotation(TimeInterval(beginP1,beginP2),beginLabel)
            endAnnot = Annotation(TimeInterval(endP1,endP2),endLabel)
        else:
            if (radius >= 0):
                beginPoint = beginPoint.Copy(); beginPoint.SetRadius(radius);
                endPoint = endPoint.Copy(); endPoint.SetRadius(radius);
            beginAnnot = Annotation(beginPoint,beginLabel)
            endAnnot = Annotation(endPoint,endLabel)
        # (d) next
        boundaries.extend([beginAnnot,endAnnot]);
        refAnnot = nextRef(itRef)
    # in case of intervals, correct overlaps
    if (build_intervals):
        lastAnnot = None
        for annot in boundaries:
            if (lastAnnot is None):
                lastAnnot = annot;
                continue;
            lastEnd = annotEnd(lastAnnot)
            begin = annotBegin(annot)
            if (lastEnd > begin):
                midpoint = MidPoint(begin, lastEnd)
                #sys.stderr.write("Overlaps %s and %s => %s\n"%(lastAnnot,annot,midpoint)); sys.stderr.flush();#DEBUG
                lastAnnot.GetLocation().SetEnd(midpoint)
                annot.GetLocation().SetBegin(midpoint)
            lastAnnot = annot;
    # done
    return boundaries;

def filterEquals(xTier, yTier, bound_type='point', equals_label_format='{x}'):
    from annotationdata import Rel, Filter, RelationFilter
    build_intervals = bound_type.startswith('interval');
    
    # create the filters
    xFilter = Filter(xTier)
    yFilter = Filter(yTier)
    # create the predicate
    equals = Rel("equals") if not(build_intervals) else  Rel("convergent");
    #TODO: filter boundaries with the same labels
    equalsFilter = RelationFilter(equals, xFilter, yFilter)
    return equalsFilter.Filter(annotformat=equals_label_format)


def TimePointAdd(timePoint,value,maxValue=None):
    res = timePoint.Copy()
    if (value<0.):  # case of negative value => use the radius
        value = timePoint.GetRadius()
        res.SetRadius(0.);
    midpoint = timePoint.GetMidpoint() + value
    if ((maxValue is not None) and (midpoint>maxValue)):
        midpoint=maxValue
    res.SetMidpoint(midpoint)
    return res;

def TimePointSub(timePoint,value,minValue=0.):
    res = timePoint.Copy()
    if (value<0.):  # case of negative value => use the radius
        value = timePoint.GetRadius()
        res.SetRadius(0.);
    midpoint = timePoint.GetMidpoint() - value
    if ((minValue is not None) and (midpoint<minValue)):
        midpoint=minValue
    res.SetMidpoint(midpoint)
    return res;

def MidPoint(p1,p2):
    res = p1.Copy();
    midpoint = (p1.GetMidpoint() + p2.GetMidpoint()) / 2.
    res.SetMidpoint(midpoint)
    return res;

def annotBegin(annot,orValue=0.):
    return annot.GetLocation().GetBegin() if annot is not None else orValue;

def annotEnd(annot,orValue=0.):
    return annot.GetLocation().GetEnd() if annot is not None else orValue;

def annotHasLabel(annot,noneValue=False):
    if (annot is None):
        return noneValue;
    return len(annot.GetLabel().GetValue())>0;

def nextOrNone(it,stopValue=None):
    """ Get the next value of an iterator or stopValue
    """
    try:
        return it.next();
    except StopIteration:
        return stopValue;


# ----------------------------------------------------------------------------
def process_files(files, opts):
    """ Process each file
        @param files the file(s) to process
    """
    annotationdata.aio = sppas_tools.getAnnotationdataAio(); # import annotationdata.aio or annotationdata.io
    from annotationdata import Transcription, Tier  #, TimePoint, TimeInterval, Label, Annotation
    for f in files:
        print("[%s] Loading annotation file..." % f)
        # Read an annotated file
        trs = annotationdata.aio.read(f)
        print("[%s] Number of tiers:%d" % (f, trs.GetSize()))

        # Prepare the output Transcription
        destTrs = trs; destAppendProcessed=False;   # default/'all' => work directly on trs
        if (opts.keep_tiers.startswith('process')):
            destTrs = Transcription(trs.GetName(), trs.GetMinTime(), trs.GetMaxTime()); # empty copy of trs
            destAppendProcessed=True; # append processed tiers
        elif ((opts.keep_tiers == 'any') or opts.keep_tiers.startwith('bound')):
            destTrs = Transcription(trs.GetName(), trs.GetMinTime(), trs.GetMaxTime()); # empty copy of trs
            
        # Look for the tier to process
        equalsRefBoundTier = None
        for tier_name in opts.tiers_names:
            tier = sppas_tools.tierFind(trs, tier_name)
            if tier is None:
                print("[%s] Any tier with name similar to '%s' ;-(" %  (f, opts.tier_name))
                print("[%s] Tiers are : %s" % (f, 
                    ''.join([ "{}[{}] '{}'".format("\n   " if (i % 4)==0 else ", ", i, t.GetName()) for i, t in enumerate(trs)])
                    ))
                break;
            print("[%s] Searched tier '%s' has %d annotations" % (f, tier.GetName(), tier.GetSize()))
            if (destAppendProcessed):
                destTrs.Append(tier);
            # Create the Boundaries tier
            boundName = opts.out_tier_format.format(tier_name);
            boundTier = Tier(boundName);
            bounds = boundaries(tier, opts.radius, opts.bound_type, trs.GetMinTime(), trs.GetMaxTime(), opts.begin_format, opts.end_format);
            for bound in bounds:
                boundTier.Append(bound);
            print("[%s] Boundaries tier '%s' has %d annotations" % (f, boundTier.GetName(), boundTier.GetSize()))
            destTrs.Append(boundTier);
            # Create the 'equals' tier
            if (opts.equals_tier):
                if (tier_name == opts.tiers_names[0]): # first => reference
                    equalsRefBoundTier = boundTier
                else:
                    equalsTier = filterEquals(boundTier, equalsRefBoundTier, opts.bound_type, opts.equals_label_format)
                    equalsName = opts.equals_tier_format.format(tier_name, opts.tiers_names[0]);
                    equalsTier.SetName(equalsName);
                    print("[%s] Equals tier '%s' has %d annotations" % (f, equalsTier.GetName(), equalsTier.GetSize()))
                    destTrs.Append(equalsTier)
        # Saving file
        (root, ext) = os.path.splitext(f)
        of = opts.out_file_format.format(root,"+".join(opts.tiers_names)) + ext
        print("[%s] Saving annotations into %s" % (f, of))
        annotationdata.aio.write(of, destTrs)
        
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
    if len(opts.tiers_names)==0:
        print("ERROR: at least one tier-name to process is required", file=sys.stderr)
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
