#!/bin/env bash
#
#SBATCH -c 12                      # number of cores
#SBATCH -t 300                  # time (minutes)
#SBATCH -o logs/clearmap2_%j_%a.out        # STDOUT #add _%a to see each array job
#SBATCH -e logs/clearmap2_%j_%a.err        # STDERR #add _%a to see each array job
#SBATCH --contiguous #used to try and get cpu mem to be contigous
#SBATCH --mem 120000 #120 gbs

module load anacondapy/5.3.1
. activate cm2

#combine blocks
xvfb-run python cell_detect.py 2 "/scratch/ejdennis/cm2_brains/j317/ch_642"
