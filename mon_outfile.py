#!/usr/bin/python

import getopt
import os
import time
import shutil
import sys


def main():
    outfile = ""
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "o:", ["outfile"])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognised"
        usage()
        sys.exit(2)

    # get outfile option, example: -o /full/path/to/sample.out   
    for o, a in opts:
        if o in ("-o", "--outfile"):
            outfile = str(a)

    if not outfile.endswith('.out'):
        print "ERROR: *.out file is expected as input file."
        sys.exit(2)

    # check if there autorg data error is
    #outfile: avg_sub_sample_101_n2_40C_bic_dmpc_cfos_12p5mgml__dammif.out
    #porod file: avg_sub_sample_101_n2_40C_bic_dmpc_cfos_12p5mgml__porod_volume
    autorg_data_error = False
    porod_file_path = outfile[:-11] + '_porod_volume'
    try:
        porod_file = open(porod_file_path, 'r')
        value = str(porod_file.read())
        if value.startswith('AUTORG DATA ERROR'):
            autorg_data_error = True
        porod_file.close()
    except IOError, e:
        print "ERROR: No file: %s" % (porod_file_path)
    
    if not autorg_data_error:
        monitorOutFile(outfile)


def monitorOutFile(outfile):
  
    print '#---- monitor the existence of *.out file -----#'
    start_time = time.time()
    while (1):
        # copy gnom out file (*.out) to *_dammif.out once it got generated.
        if os.path.isfile(outfile):
            print '#---- *.out file exists -----#'
            prefix = outfile[:-4]
            dammif_outfile = prefix + "_dammif.out" 
            print '#---- copy *.out file to *_dammif.out file -----#'
            shutil.copyfile(outfile, dammif_outfile)
            
            # found gnom out file then terminate this script execution
            print '#---- exit with total running time %s seconds -----#' % (time.time() - start_time)
            break
        # keep waiting since the gnom out file hasn't generated yet.
        else:
            time.sleep(1)
        # exceed 100 seconds then enforce to terminate this script execution
        if time.time() - start_time > 100:
            break
      


def usage():
    print 'Usage: %s [OPTIONS] -o /full/path/filename.out \n' % (sys.argv[0])
    print '''
-o --outfile   the full path of the GNOM output file (*.out) to be used as an
               input file for first DAMMIF run with slow mode.


'''
  

if __name__ == "__main__":
    main()