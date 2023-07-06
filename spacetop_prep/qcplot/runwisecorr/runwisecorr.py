# %% libraries
import os, glob, re
import shutil
import gzip
from os.path import join
import nilearn
from nilearn import image, plotting, masking
import numpy as np
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import itertools
import pathlib
import argparse

# %% -------------------------------------------------------------------
#                               parameters 
# ----------------------------------------------------------------------
parser = argparse.ArgumentParser()
parser.add_argument("--slurm-id", 
                    type=int, help="slurm id in numbers")
parser.add_argument("--qcdir", 
                    type=str, help="the top directory of fmriprep preprocessed files")
parser.add_argument("--fmriprepdir", 
                    type=str, help="the top directory of fmriprep preprocessed files")
parser.add_argument("--savedir", 
                    type=str, help="the directory where you want to save your files")
parser.add_argument("--scratchdir", 
                    type=str, help="the directory where you want to save your files")
parser.add_argument("--canlabdir", 
                    type=str, help="the directory where you want to save your files")
args = parser.parse_args()
slurm_id = args.slurm_id
qc_dir = args.qcdir
fmriprep_dir = args.fmriprepdir
save_dir = args.savedir
scratch_dir = args.scratchdir
canlab_dir = args.canlabdir
print(f"{slurm_id} {qc_dir} {fmriprep_dir} {save_dir} {scratch_dir}")

npy_dir = join(qc_dir, 'numpy_bold')
sub_folders = next(os.walk(npy_dir))[1]
sub_list = [i for i in sorted(sub_folders) if i.startswith('sub-')]
sub = sub_list[slurm_id]#f'sub-{sub_list[slurm_id]:04d}'
print(f" ________ {sub} ________")

pathlib.Path(join(scratch_dir, sub)).mkdir( parents=True, exist_ok=True )
npy_flist = sorted(glob.glob(join(npy_dir, sub, '*.npy'), recursive=True))

# %% -------------------------------------------------------------------
#                               main code 
# ----------------------------------------------------------------------

# construct an index list _____________________________________________________
index_list = []
sessions = ['ses-01', 'ses-03', 'ses-04']
runs = ['run-01', 'run-02', 'run-03', 'run-04', 'run-05', 'run-06']

for i, session in enumerate(sessions):
    for j, run in enumerate(runs):
        index = i * len(runs) + j 
        index_list.append((index, f"{session}_{run}"))

corrdf = pd.DataFrame(index=range(len(index_list)), columns=range(len(index_list)))


for a, b in itertools.combinations(npy_flist, 2):
    print(a, b)
    # 1. get index _____________________________________________________
    # Extract the integers following 'ses-' and 'run-'
    a_ses = int(re.search(r'ses-(\d+)', a).group(1))
    a_run = int(re.search(r'run-(\d+)', a).group(1))
    b_ses = int(re.search(r'ses-(\d+)', b).group(1))
    b_run = int(re.search(r'run-(\d+)', b).group(1))
    # Reconstruct the 'ses-XX_run-XX' string
    a_subses = f"ses-{a_ses:02d}_run-{a_run:02d}"
    b_subses = f"ses-{b_ses:02d}_run-{b_run:02d}"

    a_matching_index = None
    b_matching_index = None

    for index, subses in index_list:
        if subses == a_subses:
            a_index = index
            break
    for index, subses in index_list:
        if subses == b_subses:
            b_index = index

# 2. mask run 1 and run 2 _____________________________________________________
    mask_fname = join(canlab_dir, 'CanlabCore/canlab_canonical_brains/Canonical_brains_surfaces/brainmask_canlab.nii')
    mask_fname_gz = mask_fname + '.gz'
    brain_mask = image.load_img(mask_fname_gz)

    # imgfname = glob.glob(join(nifti_dir, sub, f'{sub}_{ses}_*_runtype-vicarious_event-{fmri_event}_*_cuetype-low_stimintensity-low.nii.gz'))
    # ref_img_fname = '/Users/h/Documents/projects_local/sandbox/sub-0061_ses-04_task-social_acq-mb8_run-6_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz'
    # ref_img_fname = '/Users/h/Documents/projects_local/sandbox/fmriprep_bold/sub-0002_ses-01_task-social_acq-mb8_run-1_space-MNI152NLin2009cAsym_desc-preproc_bold.nii'
    ref_img_fname = join(fmriprep_dir, sub, f"ses-{a_ses:02d}", 'func', f"{sub}_ses-{a_ses:02d}_task-social_acq-mb8_run-{a_run:01d}_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz")
    ref_img = image.index_img(image.load_img(ref_img_fname),8) #image.load_img(ref_img_fname)
    threshold = 0.5
    
    nifti_masker = nilearn.maskers.NiftiMasker(mask_img= masking.compute_epi_mask(image.load_img(mask_fname_gz), lower_cutoff=threshold, upper_cutoff=1.0),
                                target_affine = ref_img.affine, target_shape = ref_img.shape, 
                        memory="nilearn_cache", memory_level=1)
    
# 3. check if they plot correctly back into a brain map (nii) _____________________________________________________
    # convert back to 3d brain
    singlemasked = []
    for img_fname in [a, b]:
        img = np.load(img_fname)
        singlemasked.append(
            nifti_masker.fit_transform(
        image.new_img_like(ref_img,img))
        )
    # convert back to 3d brain DEP
    masked_X = nifti_masker.inverse_transform(singlemasked[0])
    masked_img_X = image.new_img_like(ref_img, masked_X.get_fdata()[..., 0])
    plotting.plot_stat_map(masked_img_X, title = f"masked img: {sub} ses-{a_ses:02d} run-{a_run:02d}")
    plt.savefig(join(scratch_dir, sub, f"maskedimage_{sub}_{a_subses}.png"))
    plt.close()

# 4. calculated correlation between run 1 and run 2 _____________________________________________________
    singlemasked_X = np.mean(singlemasked[0], axis=0)
    singlemasked_Y = np.mean(singlemasked[1], axis=0)
    corr = np.corrcoef(singlemasked_X,singlemasked_Y)[0, 1]
    corrdf.at[a_index, b_index] = corr#np.mean(correlation_coefficients)#correlation


# 5. plot runs by overlaying each other _____________________________________________________
    masked_X = nifti_masker.inverse_transform(singlemasked[0])
    masked_Y = nifti_masker.inverse_transform(singlemasked[1])

    coords = (-5, -6, -15)
    fig, axes = plt.subplots(3, 1, figsize=(10, 10))
    display = plotting.plot_anat(image.mean_img(masked_X), cmap='Blues', alpha=0.9, 
                                colorbar=False, black_bg=False, dim=False, title=f"Overlay: {sub} {a_subses} and {b_subses}", 
                                figure = fig, cut_coords=coords, axes=axes[0], draw_cross=False)
    display.add_overlay(image.mean_img(masked_Y), cmap="Reds", alpha = .5)

    plotting.plot_anat(image.mean_img(masked_X), cmap='Reds', alpha=1, colorbar=False, cut_coords=coords, 
                    display_mode='ortho',title=f"{a_subses}", figure = fig,axes=axes[1], black_bg=False, dim=False, draw_cross=False)
    plotting.plot_anat(image.mean_img(masked_Y), cmap='Reds', alpha=1, colorbar=False, cut_coords=coords, 
                    display_mode='ortho', title=f"{b_subses}", figure = fig,axes=axes[2], black_bg=False, dim=False, draw_cross=False)

    plt.savefig(join(scratch_dir, sub, f"corr_{sub}_x-{a_subses}_y-{b_subses}.png"))
    plt.close(fig)

# save df
corrdf.index = [x[1] for x in index_list]
corrdf.columns = [x[1] for x in index_list]
corrdf.to_csv(join(scratch_dir, sub, f"{sub}_runwisecorrelation.csv"))

shutil.copytree(join(scratch_dir, sub), save_dir) #join(save_dir, sub))#, dirs_exist_ok=True)
