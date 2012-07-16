#!/bin/bash

#--------- pipeline_wrapper.sh ------------------#
#
# Usage:
# 
#     $ ./pipeline_wrapper.sh DAT_FILE OUTPUT_PATH PROD_SSH_ACCESS PROD_SCP_DEST PROD_PIPELINE_HARVEST PIPELINE_SOURCE_CODE_HOME
# 
# DAT_FILE:
#
#     It is a full path of your SAS experimental data file to be used for models.
#     eg: /home/saxswaxs/ASync011_scratch/pipeline_data/test_user_epn/test_experiment/avg/sample.dat
#
# OUTPUT_PATH: 
#
#     It is a full directory path for all output files generated during pipeline modelling. 
#     eg: /home/saxswaxs/ASync011_scratch/pipeline_data/test_user_epn/test_experiment/analysis
#
# PROD_SSH_ACCESS:
#
#     A string of ssh username and remote hostname used to connect to SAXS production server.
#     eg: saxs_user@saxs_production.synchrotron.org.au
#
# PROD_SCP_DEST:
#
#     It is a remote full directory path for this pipeline script to copy output files back to remote SAXS production server.
#     eg: saxs_user@saxs_production.synchrotron.org.au:/production/data/test_user_epn/test_experiment/analysis
#
# PROD_PIPELINE_HARVEST:
#
#     It is a remote full path to trigger pipeline harvest script on remote SAXS production server.
#     eg: saxs_user@saxs_production.synchrotron.org.au:/production/data/test_user_epn/test_experiment/analysis
#
# PIPELINE_SOURCE_CODE_HOME:
#
#    It is a full absolute path of home directory of Pipeline source code on MASSIVE.
#    eg: /gpfs/M1Home/projects/ASync011/pipeline

DAT_FILE=$1
OUTPUT_PATH=$2
PROD_SSH_ACCESS=$3
PROD_SCP_DEST=$4
PROD_PIPELINE_HARVEST=$5
PIPELINE_SOURCE_CODE_HOME=$6
PROD_CONFIG=$7

# autorg, datgnom, datporod
POROD_VOLUME=`qsub -v dat_file=$DAT_FILE,output_path=$OUTPUT_PATH,pipeline_home=$PIPELINE_SOURCE_CODE_HOME,prod_ssh_access=$PROD_SSH_ACCESS,prod_scp_dest=$PROD_SCP_DEST,prod_pipeline_harvest=$PROD_PIPELINE_HARVEST,prod_config=$PROD_CONFIG $PIPELINE_SOURCE_CODE_HOME/porod_volume.pbs -e $OUTPUT_PATH -o $OUTPUT_PATH`

# mon_outfile to monitor the existence of GNOM output file (*.out)
MON_OUTFILE=`qsub -W depend=afterok:$POROD_VOLUME -v dat_file=$DAT_FILE,output_path=$OUTPUT_PATH,pipeline_home=$PIPELINE_SOURCE_CODE_HOME $PIPELINE_SOURCE_CODE_HOME/mon_outfile.pbs -e $OUTPUT_PATH -o $OUTPUT_PATH`

# dammif in slow mode with 1 run
DAMMIF_SLOW=`qsub -W depend=afterok:$MON_OUTFILE -t 0 -v dat_file=$DAT_FILE,output_path=$OUTPUT_PATH,pipeline_home=$PIPELINE_SOURCE_CODE_HOME,mode=slow,prod_ssh_access=$PROD_SSH_ACCESS,prod_scp_dest=$PROD_SCP_DEST,prod_pipeline_harvest=$PROD_PIPELINE_HARVEST,prod_config=$PROD_CONFIG $PIPELINE_SOURCE_CODE_HOME/dammif.pbs -e $OUTPUT_PATH -o $OUTPUT_PATH`

# mon_infile to monitor and process input parameters from first dammif run
MON_INFILE=`qsub -W depend=afterok:$POROD_VOLUME -v dat_file=$DAT_FILE,output_path=$OUTPUT_PATH,pipeline_home=$PIPELINE_SOURCE_CODE_HOME $PIPELINE_SOURCE_CODE_HOME/mon_infile.pbs -e $OUTPUT_PATH -o $OUTPUT_PATH`

# dammif in interactive mode with 9 runs in parallel
DAMMIF_INTERACTIVE=`qsub -W depend=afterok:$MON_INFILE -t 1-9 -v dat_file=$DAT_FILE,output_path=$OUTPUT_PATH,pipeline_home=$PIPELINE_SOURCE_CODE_HOME,mode=interactive,prod_ssh_access=$PROD_SSH_ACCESS,prod_scp_dest=$PROD_SCP_DEST,prod_pipeline_harvest=$PROD_PIPELINE_HARVEST,prod_config=$PROD_CONFIG $PIPELINE_SOURCE_CODE_HOME/dammif.pbs -e $OUTPUT_PATH -o $OUTPUT_PATH`






# damclust 
#DAMCLUST=`qsub -W depend=afterokarray:$DAMMIF -v dat_file=$DAT_FILE,output_path=$OUTPUT_PATH $PIPELINE_SOURCE_CODE_HOME/damclust.pbs -e $OUTPUT_PATH -o $OUTPUT_PATH`

# copy pipeline output files (*-1.pdb) back to remote saxs production server 
# and trigger remote pipeline_harvest script off to extract required values from pipeline output files and store them into database.
#POST_PROCESSOR=`qsub -W depend=afterok:$DAMCLUST -v dat_file=$DAT_FILE,output_path=$OUTPUT_PATH,prod_ssh_access=$PROD_SSH_ACCESS,prod_scp_dest=$PROD_SCP_DEST,prod_pipeline_harvest=$PROD_PIPELINE_HARVEST $PIPELINE_SOURCE_CODE_HOME/postprocessor.pbs -e $OUTPUT_PATH -o $OUTPUT_PATH`

exit 0