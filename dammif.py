#!/usr/bin/python


import getopt
import os
import time
import shutil
import subprocess
import sys


def main():
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "p:i:o:", ["prefix", "infile", "outfile"])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)

    # get options  
    for o, a in opts:
        if o in ("-p", "--prefix"):
            prefix = str(a)
        if o in ("-i", "--infile"):
            infile = str(a)
        if o in ("-o", "--outfile"):
            outfile = str(a)

    if not infile.endswith('.in'):
        print "ERROR: *.in file is expected as input file."
        sys.exit(2)

    dammif(prefix, infile, outfile)


def dammif(prefix, infile, outfile):
  
    #dammif --prefix="$OUTPUT_FILE_PREFIX"_${PBS_ARRAYID} --mode=interactive --symmetry=P1 --unit=n "$OUTPUT_FILE_PREFIX"_dammif.out < "$OUTPUT_FILE_PREFIX"_0.in 
  
    process = subprocess.Popen(['dammif', '--prefix=%s' % prefix, '--mode=interactive', '--symmetry=P1', '--unit=n', outfile, '<', infile], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (output, errorOutput) = process.communicate()
  
    start_time = time.time()
    while (1):
        # exit if the first dammif run with slow mode has finished
        pdb_first_run = prefix[:-1] + '0-0.pdb'
        pdb_this_run = prefix + '-0.pdb'
        if os.path.isfile(pdb_first_run) and os.path.isfile(pdb_this_run):
            break
        # exceed 15 minutes then enforce to finish
        if time.time() -  start_time > 900:
            break
      


def usage():
    print 'Usage: %s [OPTIONS] -p /full/path/filename -i /full/path/filename_0.in -o /full/path/filename.out \n' % (sys.argv[0])
    print '''
-p --prefix    Prefix to prepend to output filenames (*-1.pdb). Should include 
               absolute paths, all directory components must exist.
-i --infile    the full path of the .in file to be used for re-run 9 DAMMIF to
               get a chained PDB output.
-o --outfile   the full path of the .out file to be used as an input file for 
               dammif model.


'''
  

if __name__ == "__main__":
    main()