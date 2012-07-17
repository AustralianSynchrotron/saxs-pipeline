#!/usr/bin/python

import getopt
import os
import time
import shutil
import sys
import traceback

# Set logging
import logging
path = str(os.path.abspath(sys.argv[0]))
logfile = path[:path.rfind('/')] + '/mon_outfile.log'
log = logging.getLogger(logfile)
hdlr = logging.StreamHandler(sys.stderr)
formatter = logging.Formatter('[%(levelname)s]: %(message)s')
hdlr.setFormatter(formatter)
log.addHandler(hdlr)
log.setLevel(2)

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

    monitorOutFile(outfile)


def monitorOutFile(outfile):
  
    print '#---- monitor the existence of outfile -----#'
    start_time = time.time()
    any_error = False
    while (1):
        # copy gnom out file (*.out) to *_dammif.out once it got generated.
        if os.path.isfile(outfile):
            try:
                print '#---- outfile exists -----#'
                print outfile
                prefix = outfile[:-4]
                dammif_outfile = prefix + "_dammif.out" 
                
                print '#---- copy outfile to -----#' 
                print dammif_outfile
                shutil.copyfile(outfile, dammif_outfile)
                
                # found gnom out file then terminate this script execution
                print '#---- exit with total running time %s seconds -----#' % (time.time() - start_time)
                break
            except Exception, e:
                msg = excInfo(sys.exc_info())
                print msg
                log.error(msg + '\nOutfile: ' + outfile)
                any_error = True
        # keep waiting since the gnom out file hasn't generated yet.
        else:
            time.sleep(1)
        # exceed 100 seconds then enforce to terminate this script execution
        time_limit = 100
        if time.time() - start_time > time_limit:
            msg = 'Error: there is no outfile from datgnom after waiting for %s seconds' % time_limit
            print msg
            log.error(msg + '\nOutfile: ' + outfile)
            any_error = True
            break
      
    if any_error:
        sys.exit(2)

def excInfo(exc_info):
    exc_type, exc_value, exc_traceback = exc_info[:3]
    lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    msg = ''.join('!! ' + line for line in lines)
    return msg

def usage():
    print 'Usage: %s [OPTIONS] -o /full/path/filename.out \n' % (sys.argv[0])
    print '''
-o --outfile   the full path of the GNOM output file (*.out) to be used as an
               input file for first DAMMIF run with slow mode.


'''
  

if __name__ == "__main__":
    main()