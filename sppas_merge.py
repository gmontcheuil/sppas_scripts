#!/usr/bin/env python2
# vim: set fileencoding=UTF-8 ts=4 sw=4 expandtab:

#-----------
# Author: Grégoire Montcheuil
# Brief: SPPAS script to merge tiers from various files (and/or reorder them)
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
    # Output
    out_file="merged",    # output file (if any extension, use the 1st file extension)
    # (first) tiers order
    first_tiers=[], # list of tiers to put at the start of the output Transcription
    exclude_tiers=[], # list of tiers to remove of the output Transcription
    case_sensitive=True,
    )

# ----------------------------------------------------------------------------
# --- Script arguments
# ----------------------------------------------------------------------------

parser = argparse.ArgumentParser(description='Merge various files in one (and/or reorder tiers)',formatter_class=RawTextHelpFormatter)
# Input
# - file(s)
parser.add_argument("files", nargs='+'
    , help="File(s) to process"
    , metavar='<file>'
    )
# Output
# - Output file (basename)
parser.add_argument("-o","--outfile", dest='out_file'
        , help=("The output file basename (default:%s)."%opts.out_file)
            +"\nIf no extension, use the same of the 1st (readable) file"
    , metavar='<file>'
    )
# - first tier(s)
parser.add_argument("-t", "--first-tiers", action='append', dest='first_tiers'
    , help="Tier(s) to put first in the output file"
            +"\nCan specify various separated by a comma and/or repeat the option,\nb.e. -t tier1,tier2 -t tier3"
    , metavar='<tier>'
    )
# - exclude tier(s)
parser.add_argument("-x", "--exclude-tiers", action='append', dest='exclude_tiers'
    , help="Tier(s) to put remove of the output file"
            +"\nCan specify various separated by a comma and/or repeat the option,\nb.e. -x tier1,tier2 -t tier3"
    , metavar='<tier>'
    )
# - ignore case
parser.add_argument("-i", "--ignore-case", dest='case_sensitive', action='store_false'
    , help="Ignore case when looking for tier names"
    )
# sppas_tools: sppas_dir/sppas_version
sppas_tools.parserAddLoadSPPASArgument(parser);


# ----------------------------------------------------------------------------
# --- The real Work
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
def process_files(files, opts):
    """ Process all files
        @param files the file(s) to process
    """
    annotationdata.aio = sppas_tools.getAnnotationdataAio(); # import annotationdata.aio or annotationdata.io
    from annotationdata import Transcription, Tier  #, TimePoint, TimeInterval, Label, Annotation
    mergedTrs = None; firstFile = None;
    for f in files:
        print("[%s] Loading annotation file..." % f)
        # Read an annotated file, put content in a Transcription object.
        trs = annotationdata.aio.read(f)
        if trs:
            print("[%s] Number of tiers:%d" % (f, trs.GetSize()))
            print("[%s] Tiers are : %s" % (f, 
                ''.join([ "{}[{}] '{}'".format("\n   " if (i % 4)==0 else ", ", i, t.GetName()) for i, t in enumerate(trs)])
                ))
            print("[%s] Min/Max times: [ %s ; %s ]" % (f, trs.GetMinTime(), trs.GetMaxTime()))
            # merge trs into mergedTrs
            if mergedTrs is None:    # 1rst file => copy
                mergedTrs = trs.Copy(); firstFile = f;
            else:
                # loop on tiers
                for t in trs:
                    # look if the tier is yet in the merge
                    inmerge = mergedTrs.Find(trs.GetName(), opts.case_sensitive)
                    if inmerge is None: # NO => append
                        mergedTrs.Append(t)
                    else:
                        print("[%s] tier '%s' is already in the merged Transcription, ignore it" % (f, t.GetName()))
        else:
            print("(!) Can't read '%s', skipped" % f)
    if mergedTrs is None:
        print("ERROR any merged Transcription")
        return
    # Exclude tiers
    if opts.exclude_tiers:
        for tierName in opts.exclude_tiers:
            tierIndex = mergedTrs.GetIndex(tierName, opts.case_sensitive)
            if tierIndex < 0:
                print("[exclude] (!) any tier named '%s'" % tierName)
                continue
            else:
                tier = mergedTrs.Pop(tierIndex)
                print("[exclude] Remove tier '%s' in position %i" % (tier.GetName(), tierIndex))
    # Reorder tiers
    if opts.first_tiers:
        index=0
        for tierName in opts.first_tiers:
            tierIndex = mergedTrs.GetIndex(tierName, opts.case_sensitive)
            if tierIndex < 0:
                print("[reorder] (!) any tier named '%s'" % tierName)
                continue
            elif tierIndex != index:
                tier = mergedTrs.Pop(tierIndex)
                print("[reorder] Move tier '%s' to position %i" % (tier.GetName(), index))
                mergedTrs.Add(tier, index)
            index+=1
    # Saving file
    print("Number of tiers:%d" % mergedTrs.GetSize())
    print("Tiers are : %s" % 
        ''.join([ "{}[{}] '{}'".format("\n   " if (i % 4)==0 else ", ", i, t.GetName()) for i, t in enumerate(mergedTrs)])
        )
    print("Min/Max times: [ %s ; %s ]" % (mergedTrs.GetMinTime(), mergedTrs.GetMaxTime()))
    (root, ext) = os.path.splitext(opts.out_file)
    if not ext: # empty string
        (firstRoot, ext) = os.path.splitext(firstFile)
    of = root + ext
    print("Saving merged annotations into %s" % of)
    annotationdata.aio.write(of, mergedTrs)
        
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
    if opts.first_tiers: # split first_tiers if necessary
        opts.first_tiers = split_tiers_option(opts.first_tiers)
    if opts.exclude_tiers: # split exclude_tiers if necessary
        opts.exclude_tiers = split_tiers_option(opts.exclude_tiers)
    sppas_tools.load_sppas(opts);
    process_files(opts.files, opts)

def split_tiers_option(tiers):
    splitted_tiers = []
    for item in tiers:
        spitems = item.split(',')
        splitted_tiers.extend(spitems)
    return splitted_tiers


# ----------------------------------------------------------------------------
# This is the python entry point:
# Here, we just ask to execute the main function.
if __name__ == '__main__':
    main()
# ----------------------------------------------------------------------------
