# MATLAB Smoothing Pipeline for Normalized GM Images

This repository provides a MATLAB script for performing spatial smoothing on normalized gray matter (GM) images. It is based on SPM12 and CAT12 but has been modified to run independently of the GUI.

## Features
- Reads subject IDs from a CSV file
- Uses SPM12 for batch processing
- Applies an 8mm FWHM Gaussian smoothing kernel
- Saves smoothed images in the `results/` directory

## Requirements
- MATLAB (tested with R2023b)
- [SPM12](https://www.fil.ion.ucl.ac.uk/spm/software/spm12/)
- [CAT12](https://neuro-jena.github.io/cat/)

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/MATLAB_Smoothing_Project.git
