import os
import logging
import nibabel as nib
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree as KDTree
from scipy import stats
from collections import defaultdict

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )

def parse_freesurfer_lut(file_path, valid_labels):
    """
    Parses FreeSurfer LUT into a dictionary mapping label IDs to region names, filtered by valid labels.
    """
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
                        if label in valid_labels:
                            lut[label] = region_name
                    except ValueError:
                        continue
    except Exception as e:
        logging.error(f"Error reading LUT file: {e}")
    return lut

def get_KDTree(x):
    """Build a KD-tree for the given data."""
    x = np.atleast_2d(x)
    return KDTree(x)

def get_KL(x, y, xtree, ytree):
    """Calculate KL divergence between two distributions using KD-tree-based density estimates."""
    x = np.atleast_2d(x)
    y = np.atleast_2d(y)
    n, d = x.shape
    m, _ = y.shape

    r = xtree.query(x, k=2, eps=0.01, p=2)[0][:, 1]
    s = ytree.query(x, k=1, eps=0.01, p=2)[0]

    rs_ratio = np.divide(r, s, out=np.zeros_like(r), where=(s != 0) & (r != 0))
    rs_ratio = rs_ratio[np.isfinite(rs_ratio) & (rs_ratio != 0.0)]
    
    if len(rs_ratio) == 0:
        return 0  # Return 0 KL divergence for problematic cases

    kl = -np.log(rs_ratio).sum() * d / n + np.log(m / (n - 1.0))
    return np.maximum(kl, 0)

def calculate_mind_network(data_df, feature_cols, region_list):
    """
    Compute the MIND network for the given data.
    """
    mind = pd.DataFrame(np.zeros((len(region_list), len(region_list))), index=region_list, columns=region_list)
    data_df = data_df.loc[data_df['Label'].isin(region_list)]
    kdtrees = {name: get_KDTree(dat[feature_cols]) for name, dat in data_df.groupby('Label')}
    
    for name_x, name_y in [(x, y) for x in region_list for y in region_list if x != y]:
        KLa = get_KL(data_df[data_df['Label'] == name_x][feature_cols],
                     data_df[data_df['Label'] == name_y][feature_cols],
                     kdtrees[name_x], kdtrees[name_y])
        KLb = get_KL(data_df[data_df['Label'] == name_y][feature_cols],
                     data_df[data_df['Label'] == name_x][feature_cols],
                     kdtrees[name_y], kdtrees[name_x])
        mind.at[name_x, name_y] = 1 / (1 + (KLa + KLb))
    
    return mind

def main():
    """Main function to process subjects."""
    setup_logging()
    logging.info("Starting MIND computation pipeline...")
    # Add argument parsing for flexibility
    
if __name__ == "__main__":
    main()
