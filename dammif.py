#!/usr/bin/python


import getopt
import os
import time
import subprocess
import sys


def main():
    prefix = ""
    outfile = ""
    infile = ""
    mode = "INTERACTIVE"
    ssh_access = ""
    scp_dest = ""
    harvest_script = ""
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "p:o:i:m:s:d:h:", ["prefix", "outfile", "infile", "mode", "ssh", "destination", "harvest"])
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
   

    dammif(prefix, outfile, infile, mode, ssh_access, scp_dest, harvest_script)


def dammif(prefix, outfile, infile, mode, ssh_access, scp_dest, harvest_script):
  
    # dammif modelling
    # dammif --prefix="$OUTPUT_FILE_PREFIX"_${PBS_ARRAYID} --mode=interactive --symmetry=P1 --unit=n "$OUTPUT_FILE_PREFIX"_dammif.out < "$OUTPUT_FILE_PREFIX"_0.in 
  
    if mode.upper() == "SLOW":
        command_list = ['dammif', '--prefix=%s' % prefix, '--mode=slow', '--symmetry=P1', '--unit=n', outfile]
    elif mode.upper() == "INTERACTIVE":
        command_list = ['dammif', '--prefix=%s' % prefix, '--mode=interactive', '--symmetry=P1', '--unit=n', outfile, '<', infile]
        
    process = subprocess.Popen(command_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (output, error_output) = process.communicate()
    print ' '.join(command_list)
  
    # monitor output files (*-1.pdb)
    start_time = time.time()
    found_volume = False
    pdbfile_path = prefix + "-1.pdb"
    fitfile_path = prefix + ".fit"
    while (1):
        
        # monitor if "Total excluded DAM volume" value exists in output file *-1.pdb
        # monitor the existence of dammif output file *-1.pdb file
        if not found_volume and os.path.isfile(pdbfile_path):
            pdbfile = open(pdbfile_path, 'r')
            search = 'Total excluded DAM volume'
            for line in pdbfile:
                if line.find(search) > -1:
                    found_volume = True
                    # extract value
                    value = line.split(':')[1].strip(' ')
                    # create a file with dammif volume value
                    dammif_volume_file_path = prefix + '_dammif_volume'
                    valuefile = open(dammif_volume_file_path, 'w')
                    valuefile.write(value)
                    valuefile.close()
                    # ssh copy file to production server
                    scp_dest_path = ssh_access + ":" + scp_dest
                    command_list = ['scp', dammif_volume_file_path, scp_dest_path]
                    process = subprocess.Popen(command_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    (output, error_output) = process.communicate()
                    print ' '.join(command_list)
                    # trigger production harvest script 
                    filename_prefix = prefix.split('/')[-1] 
                    file_to_harvest = scp_dest_path + filename_prefix + '_dammif_volume'
                    command_list = ['ssh', ssh_access, 'python', harvest_script, '-t', 'dammif_volume', '-f', file_to_harvest]
                    process = subprocess.Popen(command_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    (output, error_output) = process.communicate()
                    print ' '.join(command_list)
                    # exit scanning line in pdbfile
                    break
            pdbfile.close()


        # monitor if dammif modelling process has finished
        # monitor the existence of dammif output file *.fit file which is generated in the end of dammif process.
        if os.path.isfile(fitfile_path) and os.path.isfile(pdbfile_path):
            # dammif modelling process has finished
            # ssh copy pdb file to production server
            scp_dest_path = ssh_access + ":" + scp_dest
            command_list = ['scp', pdbfile_path, scp_dest_path]
            process = subprocess.Popen(command_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            (output, error_output) = process.communicate()
            print ' '.join(command_list)
            break
        else:
            # keep waiting
            time.sleep(1)


        # exceed 15 minutes then enforce to terminate this script execution
        if time.time() - start_time > 900:
            break
      


def usage():
    print 'Usage: %s [OPTIONS] -p /full/path/filename -i /full/path/filename_0.in -o /full/path/filename.out -m slow -s username@host.domain -d /full/path/data/home -h /full/path/pipeline_harvest.py \n' % (sys.argv[0])
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
'''
  

if __name__ == "__main__":
    main()