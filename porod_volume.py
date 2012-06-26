#!/usr/bin/python

import getopt
import subprocess
import sys

def main():
    datfile = ""
    output_path = ""
    ssh_access = ""
    scp_dest = ""
    harvest_script = ""
    
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "f:o:s:d:h:", ["file", "output", "ssh", "destination", "harvest"])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognised"
        usage()
        sys.exit(2)

    # get options, example: -f /full/path/to/sample.dat        
    for o, a in opts:
        if o in ("-f", "--file"):
            datfile = str(a)
        if o in ("-o", "--output"):
            output_path = str(a)
        if o in ("-s", "--ssh"):
            ssh_access = str(a)
        if o in ("-d", "--destination"):
            scp_dest = str(a)
        if o in ("-h", "--harvest"):
            harvest_script = str(a)

    if not datfile.endswith('.dat'):
        print "ERROR: *.dat file is expected as input file."
        sys.exit(2)
        
    if not output_path.endswith('/'):
        output_path += '/'
        
    if not scp_dest.endswith('/'):
        scp_dest += '/'

    processDatFile(datfile, output_path, ssh_access, scp_dest, harvest_script)


def processDatFile(datfile, output_path, ssh_access, scp_dest, harvest_script):
  
    # automatically computes Rg and I(0) using the Guinier approximation, 
    # estimates data quality, finds the beginning of the useful data range.
    print '#---- autorg -----------------------#'
    command_list = ['autorg', '-f', 'ssv', datfile]
    process = subprocess.Popen(command_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (output, error_output) = process.communicate()
    print ' '.join(command_list)
    print output
        
    # estimates Dmax, computes the distance distribution function p(r) and the 
    # regularized scattering curve.
    print '#---- datgnom ----------------------#'    
    valuePoints = output.split(" ")
    rg = valuePoints[0]
    skip = valuePoints[4]
    try:
        skip = int(skip)
        skip = skip - 1
    except ValueError:
        print "Error happened when converting skip value into integer."
    #eg: file="sample.dat" if input file is /input_path/sample.dat
    file = datfile.split('/')[-1] 
    if file.endswith('.dat'):
        #eg: filename="sample" if input file is /input_path/sample.dat
        filename = file[:-4] 
    outfile = output_path + filename + '.out'
    command_list = ['datgnom', '-r', str(rg), '-s', str(skip), '-o', outfile, datfile]
    process = subprocess.Popen(command_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (output, error_output) = process.communicate()
    # it generates a gnom output file (*.out)
    print ' '.join(command_list)
    print output
      
    # computes Porod volume from the regularised scattering curve.
    print '#---- datporod ---------------------#' 
    command_list = ['datporod', outfile]
    process = subprocess.Popen(command_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (output, error_output) = process.communicate()
    print ' '.join(command_list)
    print output
  
  
    # create and ssh copy file of porod volume back to production
    print '#---- copy porod volume ------------#'
    # create file with porod valume value
    porod_file_path = output_path + filename + '_porod_volume'
    porod_file = open(porod_file_path, 'w')
    value = str(output).strip(' ').split(' ')[0]
    porod_file.write(value)
    porod_file.close()
    # ssh copy file back to production
    scp_dest_path = ssh_access + ":" + scp_dest
    command_list = ['scp', porod_file_path, scp_dest_path]
    process = subprocess.Popen(command_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (output, error_output) = process.communicate()
    print ' '.join(command_list)
    
    # trigger production harvest script 
    print '#---- production harvest -----------#'
    file_to_harvest = scp_dest_path + filename + '_porod_volume'
    command_list = ['ssh', ssh_access, 'python', harvest_script, '-t', 'porod_volume', '-f', file_to_harvest]
    process = subprocess.Popen(command_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (output, error_output) = process.communicate()
    print ' '.join(command_list)



def usage():
    print 'Usage: %s [OPTIONS] -f /full/path/filename.dat -o /output/full/path/ -s username@host.domain -d /full/path/data/home -h /full/path/pipeline_harvest.py \n' % (sys.argv[0])
    print '''
-f --file         The full path of your SAXS experimental data file to be used 
                  for models.
-o --output       The full directory path for all output files generated during 
                  pipeline modelling. 
-s --ssh          A string of ssh username and remote hostname used to connect 
                  to SAXS production server.
-d --destination  A remote full directory path for this pipeline script to copy 
                  output files back to remote SAXS production server.
-h --harvest      A remote full path to trigger pipeline harvest script on 
                  remote SAXS production server.


'''
  

if __name__ == "__main__":
    main()
        