#!/usr/bin/python


import getopt
import os
import time
import sys
import traceback

# Set logging
import logging
path = str(os.path.abspath(sys.argv[0]))
logfile = path[:path.rfind('/')] + '/mon_infile.log'
log = logging.getLogger(logfile)
hdlr = logging.StreamHandler(sys.stderr)
formatter = logging.Formatter('[%(levelname)s]: %(message)s')
hdlr.setFormatter(formatter)
log.addHandler(hdlr)
log.setLevel(2)

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
  
    print '#---- monitor the existence of infile -----#'
    start_time = time.time()
    any_error = False
    while (1):
        if os.path.isfile(infile):
            try:
                print '#---- infile exists -----#' 
                print infile
                
                print '#---- remove initial random seed from infile  -----#'
                # remove random seed line from infile (*.in)
                lines = open(infile, 'r').readlines()
                new_lines = []
                for line in lines:
                    if (line.find('initial random seed') != -1):
                        new_lines.append('\n')
                    else:
                        new_lines.append(line)
                open(infile, 'w').writelines(new_lines)
                print 'initial random seed removed.'
                
                print '#---- exit with total running time %s seconds -----#' % (time.time() - start_time)
                break
            except Exception, e:
                msg = excInfo(sys.exc_info())
                print msg
                log.error(msg + '\nInfile: ' + infile)
                any_error = True
        else:
            time.sleep(1)
        # exceed 100 seconds then enforce to finish
        time_limit = 100
        if time.time() - start_time > time_limit:
            msg = 'Error: there is no infile from slow mode dammif after waiting for %s seconds' % time_limit
            print msg
            log.error(msg + '\nInfile: ' + infile)
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
    print 'Usage: %s [OPTIONS] -i /full/path/filename_0.in \n' % (sys.argv[0])
    print '''
-i --infile    the full path of the .in file to be used as input parameters for 
               re-run 9 DAMMIF to get a chained PDB output.


'''
  

if __name__ == "__main__":
    main()
        