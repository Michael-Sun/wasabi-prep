#!/bin/bash -l
#SBATCH --job-name=corr
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=12
#SBATCH --mem-per-cpu=40G
#SBATCH --time=5-00:00:00
#SBATCH -o ./logcorr/np_%A_%a.o
#SBATCH -e ./logcorr/np_%A_%a.e
#SBATCH --account=DBIC
#SBATCH --partition=standard
#SBATCH --array=1-12
##-3%10

mkdir -p ./logcorr

conda init bash

conda activate biopac

# Check if SLURM_ARRAY_TASK_ID is not set or is empty
if [ -z "$SLURM_ARRAY_TASK_ID" ]; then
    # Set SLURM_ARRAY_TASK_ID to a default value, e.g., 1
    SLURM_ARRAY_TASK_ID=1
fi

hostname
echo "SLURMSARRAY: " ${SLURM_ARRAY_TASK_ID}
ID=$((SLURM_ARRAY_TASK_ID-1))
# QCDIR='/dartfs-hpc/rc/lab/C/CANlab/labdata/projects/spacetop_projects_cue'
MAINDIR='/dartfs-hpc/rc/lab/C/CANlab/labdata/data/WASABI/scripts/biopac/wasabi-prep/spacetop_prep/qcplot'
QCDIR='/dartfs-hpc/rc/lab/C/CANlab/labdata/data/WASABI/derivatives/fmriprep_qc'
FMRIPREPDIR='/dartfs-hpc/rc/lab/C/CANlab/labdata/data/WASABI/derivatives/fmriprep/'
SAVEDIR='/dartfs-hpc/rc/lab/C/CANlab/labdata/data/WASABI/derivatives/fmriprep_qc/runwisecorr'
SCRATCHDIR='/dartfs-hpc/scratch/$USER'
CANLABDIR='/dartfs-hpc/rc/lab/C/CANlab/modules/CanlabCore'
PYBIDSDIR='/dartfs-hpc/rc/lab/C/CANlab/labdata/data/WASABI/1080_wasabi/1080_wasabi_BIDSLayout'

mkdir -p $SAVEDIR

python ${MAINDIR}/runwisecorr/runwisecorr.py \
--slurm-id ${ID} \
--qcdir ${QCDIR} \
--fmriprepdir ${FMRIPREPDIR} \
--savedir ${SAVEDIR} \
--scratchdir ${SCRATCHDIR} \
--canlabdir ${CANLABDIR} \
--task 'task-' \
--pybids_db ${PYBIDSDIR}