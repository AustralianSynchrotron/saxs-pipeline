#!/usr/bin/python


import getopt
import os
import time
import subprocess
import sys
import traceback

# Set logging
import logging
path = str(os.path.abspath(sys.argv[0]))
logfile = path[:path.rfind('/')] + '/dammif.log'
log = logging.getLogger(logfile)
hdlr = logging.StreamHandler(sys.stderr)
formatter = logging.Formatter('[%(levelname)s]: %(message)s')
hdlr.setFormatter(formatter)
log.addHandler(hdlr)
log.setLevel(2)


def main():
    prefix = ""
    outfile = ""
    infile = ""
    mode = "INTERACTIVE"
    ssh_access = ""
    scp_dest = ""
    harvest_script = ""
    config = ""
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "p:o:i:m:s:d:h:c:", ["prefix", "outfile", "infile", "mode", "ssh", "destination", "harvest", "config"])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)

    # get options  
    for o, a in opts:
        if o in ("-p", "--prefix"):
            prefix = str(a)
        if o in ("-o", "--outfile"):
            outfile = str(a)
        if o in ("-i", "--infile"):
            infile = str(a)
        if o in ("-m", "--mode"):
            mode = str(a)
        if o in ("-s", "--ssh"):
            ssh_access = str(a)
        if o in ("-d", "--destination"):
            scp_dest = str(a)
        if o in ("-h", "--harvest"):
            harvest_script = str(a)
        if o in ("-c", "--config"):
            config = str(a)

    if not outfile.endswith('.out'):
        print "ERROR: *.out file (GNOM output file) is expected as an input file."
        sys.exit(2)
    if not infile.endswith('.in'):
        print "ERROR: *.in file (DAMMIF .in file) is expected as an input set of parameters."
        sys.exit(2)
    if mode.upper() not in ["FAST", "SLOW", "INTERACTIVE"]:
        print "ERROR: Invalid mode '%s'. One of 'FAST', 'SLOW', or 'INTERACTIVE'." % (mode)
        sys.exit(2)
    if not scp_dest.endswith('/'):
        scp_dest += '/'
   
    # check if there autorg data error is
    #prefix: avg_sub_sample_101_n2_40C_bic_dmpc_cfos_12p5mgml__0
    #porod file: avg_sub_sample_101_n2_40C_bic_dmpc_cfos_12p5mgml__porod_volume
    autorg_data_error = False
    porod_file_path = prefix[:-2] + '_porod_volume' 
    try:
        porod_file = open(porod_file_path, 'r')
        value = str(porod_file.read())
        if value.startswith('AUTORG DATA ERROR'):
            autorg_data_error = True
        porod_file.close()
    except IOError, e:
        msg = "ERROR: No file: %s" % (porod_file_path)
        print msg
        log.error(msg)
        
    if not autorg_data_error:
        if mode.upper() == "INTERACTIVE":
            if os.path.isfile(infile) and os.path.isfile(outfile):
                dammif(prefix, outfile, infile, mode, ssh_access, scp_dest, harvest_script, config)
        elif mode.upper() == "SLOW": 
            if os.path.isfile(outfile):
                dammif(prefix, outfile, infile, mode, ssh_access, scp_dest, harvest_script, config)


def dammif(prefix, outfile, infile, mode, ssh_access, scp_dest, harvest_script, config):
  
    # dammif modelling
    # dammif --prefix="$OUTPUT_FILE_PREFIX"_${PBS_ARRAYID} --mode=interactive --symmetry=P1 --unit=n "$OUTPUT_FILE_PREFIX"_dammif.out < "$OUTPUT_FILE_PREFIX"_0.in 
    print '#---- dammif modelling -------#'
    if mode.upper() == "SLOW":
        command_list = ['dammif', '--prefix=%s' % prefix, '--mode=slow', '--symmetry=P1', '--unit=n', outfile]
        process = subprocess.Popen(command_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (output, error_output) = process.communicate()
        print ' '.join(command_list)
        print '\n'
    elif mode.upper() == "INTERACTIVE":
        # replace subprocess.Popen with os.system due to a getopt error of "too many arguments".
        command = 'dammif --prefix=%s --mode=interactive --symmetry=P1 --unit=n %s < %s' % (prefix, outfile, infile)
        os.system(command)
        print command
        print '\n'
  
    # monitor output files (*-1.pdb)
    start_time = time.time()
    any_error = False
    
    pdbfile_path = prefix + "-1.pdb"
    fitfile_path = prefix + ".fit"
    while (1):
        
        # monitor if dammif modelling process has finished
        # monitor the existence of dammif output file *.fit file which is generated in the end of dammif process.
        # monitor the existence of dammif output file *-1.pdb file which holds DAM volume value.
        if os.path.isfile(fitfile_path) and os.path.isfile(pdbfile_path):
            # dammif modelling process has finished
            
            # monitor if "Total excluded DAM volume" value exists in output file *-1.pdb
            pdbfile = open(pdbfile_path, 'r')
            search = 'Total excluded DAM volume'
            for line in pdbfile:
                if line.find(search) > -1:
                    print '#---- Total excluded DAM volume value found -------#'
                    # extract value
                    value = line.split(':')[1].strip(' ')
                    print value
                    # create a file with dammif volume value
                    print '#---- create dammif volume file -------#'
                    dam_volume_file_path = prefix + '_dam_volume'
                    valuefile = open(dam_volume_file_path, 'w')
                    valuefile.write(value)
                    valuefile.close()
                    print dam_volume_file_path + '\n'
                    # ssh copy file to production server
                    print '#---- copy dammif volume file-------#'
                    scp_dest_path = ssh_access + ":" + scp_dest
                    command_list = ['scp', dam_volume_file_path, scp_dest_path]
                    process = subprocess.Popen(command_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    (output, error_output) = process.communicate()
                    print ' '.join(command_list)
                    print ''
                    # trigger production harvest script 
                    print '#---- production harvest -----------#'
                    filename_prefix = prefix.split('/')[-1] 
                    file_to_harvest = scp_dest + filename_prefix + '_dam_volume'
                    command_list = ['ssh', ssh_access, 'python', harvest_script, '-t', 'dam_volume', '-f', file_to_harvest, '-c', config]
                    process = subprocess.Popen(command_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    (output, error_output) = process.communicate()
                    print ' '.join(command_list)       
                    print ''          
                    break
            pdbfile.close()
            
            # ssh copy pdb file to production server
            print '#---- scp *-1.pdb files -----------#'
            scp_dest_path = ssh_access + ":" + scp_dest
            command_list = ['scp', pdbfile_path, scp_dest_path]
            process = subprocess.Popen(command_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            (output, error_output) = process.communicate()
            print ' '.join(command_list)
            print ''
            print '#---- exit with total running time %s seconds -----#\n' % (time.time() - start_time)
            break
        else:
            # keep waiting
            time.sleep(1)

        # exceed 15 minutes then enforce to terminate this script execution
        time_limit = 900
        if time.time() - start_time > time_limit:            
            msg = 'Error: there is no outfile from datgnom after waiting for %s seconds' % time_limit
            print msg
            log.error(msg + '\nPrefix: ' + prefix)
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
    print 'Usage: %s [OPTIONS] -p /full/path/filename -i /full/path/filename_0.in -o /full/path/filename.out -m slow -s username@host.domain -d /full/path/data/home -h /full/path/pipeline_harvest.py -c /full/path/configfile \n' % (sys.argv[0])
    print '''
-p --prefix    Prefix to prepend to output filenames (eg. "prefix"-1.pdb).   
               Should include absolute paths, all directory components must 
               exist.
               
-i --infile    The full path of the .in file to be used as input parameters for 
               re-run DAMMIF to get a chained PDB output.
               
-o --outfile   The full path of the .out file to be used as an input file for 
               dammif model.
               
-m --mode      Configuration of the annealing procedure, one of FAST, SLOW, or
               INTERACTIVE. Default is INTERACTIVE.
-s --ssh          A string of ssh username and remote hostname used to connect 
                  to SAXS production server.
-d --destination  A remote full directory path for this pipeline script to copy 
                  output files back to remote SAXS production server.
-h --harvest      A remote full path to trigger pipeline harvest script on 
                  remote SAXS production server.
-c --config    A full absolute path of config file in auto-processor.
'''
  

if __name__ == "__main__":
    main()