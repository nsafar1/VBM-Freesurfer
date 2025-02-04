# MIT License
# Copyright (c) 2024 [Your Name]
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.

import os
import nibabel as nib
import numpy as np
import pandas as pd
from scipy.stats import entropy
from itertools import combinations
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_freesurfer_lut(file_path):
    """Parses the FreeSurfer LUT file into a dictionary."""
    lut = {}
    try:
        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        label = int(parts[0])
                        region_name = " ".join(parts[1:])
                        lut[label] = region_name
                    except ValueError:
                        logging.warning(f"Skipping invalid line: {line}")
        logging.info(f"Parsed LUT with {len(lut)} regions.")
    except Exception as e:
        logging.error(f"Error reading LUT file: {e}")
    return lut

def extract_voxel_distributions(image_path, lut, output_dir, subject_id):
    """Extracts voxel intensity values for each region based on LUT."""
    distributions = {}
    big_dist = []
    missing_regions = []

    if not os.path.exists(image_path):
        logging.error(f"Segmentation file not found: {image_path}")
        return distributions, big_dist

    try:
        img = nib.load(image_path)
        data = img.get_fdata()

        for label_id, region_name in lut.items():
            region_voxels = data[np.isclose(data, label_id, atol=1e-3)]
            if region_voxels.size > 0:
                distributions[region_name] = region_voxels
                big_dist.extend(region_voxels)
            else:
                missing_regions.append((region_name, label_id))
    except Exception as e:
        logging.error(f"Error processing image {image_path}: {e}")

    pd.DataFrame(missing_regions, columns=["Region Name", "Label"]).to_csv(
        os.path.join(output_dir, f"missing_regions_sub-{subject_id}.csv"), index=False
    )

    return distributions, np.array(big_dist)

def compute_kl_divergence(distributions, bin_edges_big, subject_id, output_dir):
    """Computes KL divergence for all region pairs."""
    kl_dir = os.path.join(output_dir, f"KL_divergences_sub-{subject_id}")
    os.makedirs(kl_dir, exist_ok=True)

    region_names = list(distributions.keys())
    for region1, region2 in combinations(region_names, 2):
        dist1 = distributions[region1]
        dist2 = distributions[region2]

        hist1, _ = np.histogram(dist1, bins=bin_edges_big, density=True)
        hist2, _ = np.histogram(dist2, bins=bin_edges_big, density=True)

        hist1 = np.where(hist1 == 0, 1e-10, hist1)
        hist2 = np.where(hist2 == 0, 1e-10, hist2)

        kl_div = entropy(hist1, hist2)
        pair_filename = f"{region1}_vs_{region2}.csv".replace(" ", "_")
        
        with open(os.path.join(kl_dir, pair_filename), "w") as f:
            f.write("Region1,Region2,KL_Divergence\n")
            f.write(f"{region1},{region2},{kl_div}\n")

def main():
    """Main processing function."""
    freesurfer_dir = "./freesurfer"
    vbm_dir = "./vbm"
    lut_path = "./FreeSurferColorLUT.txt"
    output_dir = "./results"

    os.makedirs(output_dir, exist_ok=True)
    lut = parse_freesurfer_lut(lut_path)
    
    if not lut:
        logging.error("LUT is empty. Exiting.")
        return

    freesurfer_subjects = {sub.replace("sub-", "") for sub in os.listdir(freesurfer_dir) if sub.startswith("sub-")}
    vbm_subjects = {f.split("sub-")[1].split("_")[0] for f in os.listdir(vbm_dir) if f.startswith("mwp1sub-")}
    common_subjects = list(freesurfer_subjects & vbm_subjects)
    
    if not common_subjects:
        logging.error("No common subjects found. Exiting.")
        return

    for subject_id in common_subjects:
        freesurfer_seg_path = os.path.join(freesurfer_dir, f"sub-{subject_id}/mri/aparc.a2009s+aseg.mgz")
        vbm_seg_path = os.path.join(vbm_dir, f"mwp1sub-{subject_id}_T1w.nii_output.mgz")

        if not os.path.exists(freesurfer_seg_path) or not os.path.exists(vbm_seg_path):
            logging.warning(f"Segmentation file missing for subject {subject_id}")
            continue

        cortical_distributions, cortical_big_dist = extract_voxel_distributions(freesurfer_seg_path, lut, output_dir, subject_id)
        subcortical_distributions, subcortical_big_dist = extract_voxel_distributions(vbm_seg_path, lut, output_dir, subject_id)
        
        all_distributions = {**cortical_distributions, **subcortical_distributions}
        big_dist = np.concatenate((cortical_big_dist, subcortical_big_dist))
        
        if not all_distributions:
            logging.warning(f"No voxel distributions found for subject {subject_id}. Skipping.")
            continue

        _, bin_edges_big = np.histogram(big_dist, bins=100, density=True)
        compute_kl_divergence(all_distributions, bin_edges_big, subject_id, output_dir)

if __name__ == "__main__":
    main()
