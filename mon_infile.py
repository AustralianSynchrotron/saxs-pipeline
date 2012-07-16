#!/usr/bin/python


import getopt
import os
import time
import shutil
import subprocess
import sys


def main():
    infile = ""
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "i:", ["infile"])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognised"
        usage()
        sys.exit(2)

    # get infile option, example: -i /full/path/to/sample_0.in     
    for o, a in opts:
        if o in ("-i", "--infile"):
            infile = str(a)

    if not infile.endswith('.in'):
        print "ERROR: *.in file is expected as input file."
        sys.exit(2)

    monitorInFile(infile)


def monitorInFile(infile):
  
    print '#---- monitor the existence of *.in file -----#'
    start_time = time.time()
    while (1):
        if os.path.isfile(infile):
            print '#---- *.in file exists -----#'
            # remove random seed line from infile (*.in)
            lines = open(infile, 'r').readlines()
            new_lines = []
            for line in lines:
                if (line.find('initial random seed') != -1):
                    new_lines.append('\n')
                else:
                    new_lines.append(line)
            open(infile, 'w').writelines(new_lines)
            print '#---- initial random seed removed from *.in file  -----#'
            print '#---- exit with total running time %s seconds -----#' % (time.time() - start_time)
            break
        else:
            time.sleep(1)
        # exceed 100 seconds then enforce to finish
        if time.time() - start_time > 100:
            break
      


def usage():
    print 'Usage: %s [OPTIONS] -i /full/path/filename_0.in \n' % (sys.argv[0])
    print '''
-i --infile    the full path of the .in file to be used as input parameters for 
               re-run 9 DAMMIF to get a chained PDB output.


'''
  

if __name__ == "__main__":
    main()
        