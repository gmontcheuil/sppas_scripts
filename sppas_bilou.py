#!/usr/bin/env python2
# vim: set fileencoding=UTF-8 ts=4 sw=4 expandtab:

#-----------
# Author: Grégoire Montcheuil
# Brief: SPPAS script to generate a BILOU sub-division tier
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
    # BILOU tier(s)
    base_time=0.1, # BILOU interval's duration
    radius=0.0005, # BILOU TimePoint radius
    bilu_format="{:.1}", o_label="",   # BILOU labels format (see bilouTags())
    labels="BILOU", # TODO: use a sub-set of the BILOU tags
    out_tier_format="BILOU - {:s} - {:.3f}s",
    # Output
    keep_tiers="process", # in the output keep : 'all' tiers (default), 'process(ed)' tiers or 'any' (i.e. only the BILOU)
    out_file_format="{:s}-BILOU_{:s}",    # output file format (before the extension), 1st element is the filename (without extension), 2nd is the tier(s) name(s)
    )

# ----------------------------------------------------------------------------
# --- Script arguments
# ----------------------------------------------------------------------------

parser = argparse.ArgumentParser(description='Create BILOU tier(s)',formatter_class=RawTextHelpFormatter)
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
# BILOU tier(s)
# - base time
parser.add_argument("-b", "--base", "--base-time", dest='base_time', type=float
    , help="time subdivision of the BILOU tier (in second, default:'%f')"%opts.base_time
    , metavar='<second>'
    )
# - radius
parser.add_argument("-r", "--radius", dest='radius', type=float
        , help="precision (radius) of the BILOU tier's time points (default:'%f')"%opts.radius
    , metavar='<second>'
    )
#TODO: labels => selection of the BILOU tagset : IO, BIO, etc.
# - BILU labels format
parser.add_argument("--bilu-format", dest='bilu_format'
        , help=("Format of the BILU labels (default:'%s')."%opts.bilu_format)
            +"\n\tFirst field({0:}) is for Begin/Inside/Last/Unit"
            +"\n\tSecond field({1:}) is for the annotation label"
            +"\nExamples:"
            +"\n\t'{}-{}' => full word with label, e.g.'Begin-Label'"
            +"\n\t'{:.1}-{}' => first letter with label, e.g.'B-Label'"
            +"\n\t'{:.1}' => first letter without label, e.g.'B'"
    , metavar='<format>'
    )
# - Outside label
parser.add_argument("-O", "--o-label", "--outside-label", dest='o_label'
        , help="'Outside' label (default:'%s')"%opts.o_label
    , metavar='<string>'
    )
# - Output/BILOU tier(s) format
parser.add_argument("--out-tier", "--out-tier-format", "--bilou-tier-format", dest='out_tier_format'
        , help=("Format for the BILOU tier(s) (default:'%s')"%opts.out_tier_format)
            +"\n\tFirst field({0:}) is for processed tier's name"
            +"\n\tSecond field({1:f}) is for the base time (see option -b)"
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
            +"\n\t'all' => keep all original tiers (BILOU tiers are append to the end)"
            +"\n\t'process' (or 'processed') => keep only processed tiers (BILOU tiers are added after each processed tier)"
            +"\n\t'any'/'bilou' => keep any original tier, output only the BILOU tiers"
    , metavar='(all|process|any)'
    , choices=['all','process','processed','any','bilou']
    )
#TODO: output extension
# sppas_tools: sppas_dir/sppas_version
sppas_tools.parserAddLoadSPPASArgument(parser);


# ----------------------------------------------------------------------------
# --- The real Work
# ----------------------------------------------------------------------------


def bilouTags(ref,dest,labels="BILOU",bilu_format="{:.1}({})",o_label="O",labels_sep=" + "):
    """ Compute the BILOU tags corresponding to a tier.
        Example:
          ref =       [------]   [---] [----]    []   [-----]   [] [---------]
          dest= |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
           =>   | O | B | I | L | B |L+B| L | O | U | B | L | O |U+B| I | I | L |

        @param ref  the reference tier (were are the annotation)
        @param dest the destination tier (with continious segmentation).
        @param labels   (TODO) the tagset to use: IO, BIO, BILO, BILOU, etc.
        @param bilu_format  a format for the Begin, In, Last, Unit labels.
            The first format parameter is Begin, Inside, Last, Unit.
            The second is the reference tier label.
            Default: "{:.1}()}", p.e. "B(label)"
        @parma o_label  the label for Outside
        
        @return ...
    """
    # usefull value
    destMaxEnd = dest.GetEnd()
    # iterator on the reference's intervals
    def nextRef(it):
        annot = nextOrNone(it);
        while (not annotHasLabel(annot,True)):
            #sys.stderr.write('#'); sys.stderr.flush(); # debug
            annot = nextOrNone(it);
        start = annotBegin(annot, destMaxEnd)
        end = annotEnd(annot, destMaxEnd)
        #sys.stderr.write('|'); sys.stderr.flush(); # debug
        return (annot, start, end);
    itRef = iter(ref);
    refAnnot, refStart, refEnd = nextRef(itRef);
    #sys.stderr.write("first ref [%s,%s]\n" % (refStart, refEnd)); sys.stderr.flush(); # debug
    # go through destination annotation
    destLastEnd = dest.GetBeginValue();
    for destAnnot in dest:
        #sys.stderr.write('.'); sys.stderr.flush(); # debug
        destStart = annotBegin(destAnnot)
        destEnd = annotEnd(destAnnot)
        #TODO: check/add [destLastEnd,destStart[ interval
        # Skip the reference intervals that ends before the destination interval
        while (refEnd <= destStart): # the reference intervals end before dest => go to the next reference interval
            #sys.stderr.write(refEnd+"<"+destStart); sys.stderr.flush(); # debug
            refAnnot, refStart, refEnd = nextRef(itRef);
            #sys.stderr.write("before => ref [%s,%s]\n" % (refStart, refEnd)); sys.stderr.flush(); # debug

        relations=[];
        while (True): # relations 'loop'
            # Here refEnd > destStart => the reference interval overlaps or is after the destination
            if (destEnd <= refStart): # dest ends before ref starts => Outside
                relations.append(["Outside"])
                #sys.stderr.write('o'); sys.stderr.flush(); # debug
                break; # relations loop
            # Here destEnd > refStart, i.e. reference and destination overlaps
            
            # (a) look for Last/Unit
            while ((refStart < destEnd) and (refEnd <= destEnd)):  # ref ends inside dest => Last/Unit
                #sys.stderr.write('l'); sys.stderr.flush(); # debug
                if (destStart <= refStart): # Unit
                    #TODO: insert "Outside" if destStart < refStart
                    relations.append(["Unit",refAnnot]);
                    #sys.stderr.write("U [%s,%s] in [%s,%s]\n" % (refStart, refEnd, destStart, destEnd)); sys.stderr.flush(); # debug
                else:   # Last
                    relations.append(["Last",refAnnot]);
                    #sys.stderr.write("L [%s,%s] ends in [%s,%s]\n" % (refStart, refEnd, destStart, destEnd)); sys.stderr.flush(); # debug
                # go to the next reference, see the L+B case in the example
                refAnnot, refStart, refEnd = nextRef(itRef);
                #sys.stderr.write("last/unit => ref [%s,%s]\n" % (refStart, refEnd)); sys.stderr.flush(); # debug
                #TODO: insert "Outside" if lastRefEnd < refStart
            # HERE: We have add all ref annotation that ends inside dest (if any)
            
            # (b) look for Unit/Begin
            while ((refStart < destEnd) and (destStart <= refStart)): # ref start in dest => Begin/Unit
                #sys.stderr.write('b'); sys.stderr.flush(); # debug
                if (refEnd <= destEnd):  # Unit
                    #TODO: insert "Outside" if destStart < refStart
                    relations.append(["Unit",refAnnot]);
                    #sys.stderr.write("U [%s,%s] in [%s,%s]\n" % (refStart, refEnd, destStart, destEnd)); sys.stderr.flush(); # debug
                    refAnnot, refStart, refEnd = nextRef(itRef);  # case of various Unit/Begin, see U+B in the example
                    #sys.stderr.write("unit => ref [%s,%s]\n" % (refStart, refEnd)); sys.stderr.flush(); # debug
                else:
                    #TODO: insert "Outside" if destStart < refStart
                    relations.append(["Begin",refAnnot]);
                    #sys.stderr.write("B [%s,%s] starts in [%s,%s]\n" % (refStart, refEnd, destStart, destEnd)); sys.stderr.flush(); # debug
                    break;
            # HERE: We have add all ref annotation that starts inside dest (if any)

            # (c) Check Inside
            if ((refStart < destStart) and (destEnd < refEnd)):
                #sys.stderr.write('i'); sys.stderr.flush(); # debug
                relations.append(["Inside",refAnnot]);
                #sys.stderr.write("I [%s,%s] overs [%s,%s]\n" % (refStart, refEnd, destStart, destEnd)); sys.stderr.flush(); # debug
            break;  # relations loop
        # HERE: relations contains a list of BILOU relations
        labels = [];
        for rel in relations:
            if ("Outside" == rel[0]):
                labels.append(o_label);
            else:
                labels.append(bilu_format.format(rel[0], rel[1].GetLabel().GetValue()));
        destAnnot.GetLabel().SetValue(labels_sep.join(labels));
    # HERE: all dest annotation are process
    # TODO: look for remaining ref annot
    return;

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

def splitIntervals(tier,duration,maxTime,minTime=0.,radius=0.,label_format="",first_index=1):
    """ Generate the intervals of equals duration between [minTime,maxTime]
        @param tier (optional) the tier where insert the intervals
        @param duration the intervals duration
        @param maxTime  the maximum time for the intervals (inclusive)
        @param minTime  the minimum time for the intervals (default:0.)
        @param radius   the radius precision for intervals TimePoint.
        @param label_format a label format, combined with the interval index (starting from first_index)
        @param first_index  the first index for the label format

        @return the list of Annotation
    """
    from annotationdata import Tier, TimePoint, TimeInterval, Label, Annotation
    annots = [];
    startPoint = TimePoint(minTime, radius);
    endTime = minTime + duration;
    index = first_index
    while (endTime <= maxTime):
        endPoint = TimePoint(endTime,radius);
        interval = TimeInterval(startPoint, endPoint)
        label = Label(label_format.format(index))
        annot = Annotation(interval,label)
        annots.append(annot)
        if isinstance(tier,Tier):
            tier.Add(annot)
        # next
        startPoint = endPoint
        endTime += duration
        index += 1
    return annots;

# ----------------------------------------------------------------------------
def process_files(files, opts):
    """ Process each file
        @param files the file(s) to process
    """
    from annotationdata import Transcription, Tier  #, TimePoint, TimeInterval, Label, Annotation
    for f in files:
        print("[%s] Loading annotation file..." % f)
        # Read an annotated file
        trs = annotationdata.io.read(f)
        print("[%s] Number of tiers:%d" % (f, trs.GetSize()))

        # Prepare the output Transcription
        destTrs = trs; destAppendProcessed=False;   # default/'all' => work directly on trs
        if (opts.keep_tiers.startswith('process')):
            destTrs = Transcription(trs.GetName(), trs.GetMinTime(), trs.GetMaxTime()); # empty copy of trs
            destAppendProcessed=True; # append processed tiers
        elif ((opts.keep_tiers == 'any') or (opts.keep_tiers == 'bilou')):
            destTrs = Transcription(trs.GetName(), trs.GetMinTime(), trs.GetMaxTime()); # empty copy of trs
            
        # Look for the tier to process
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
            # Create the BILOU tier
            bilouName = opts.out_tier_format.format(tier_name, opts.base_time);
            bilouTier = Tier(bilouName);
            splitIntervals(bilouTier,opts.base_time, trs.GetMaxTime(), trs.GetMinTime(), opts.radius)
            bilouTags(tier,bilouTier,opts.labels,opts.bilu_format,opts.o_label);
            print("[%s] BILOU tier '%s' has %d annotations" % (f, bilouTier.GetName(), bilouTier.GetSize()))
            destTrs.Append(bilouTier);
        # Saving file
        (root, ext) = os.path.splitext(f)
        of = opts.out_file_format.format(root,"+".join(opts.tiers_names)) + ext
        print("[%s] Saving annotations into %s" % (f, of))
        annotationdata.io.write(of, destTrs)
        
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
