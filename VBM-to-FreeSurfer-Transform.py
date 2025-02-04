import os
import argparse
import logging
import pandas as pd
import subprocess

def setup_logging(log_path):
    """Sets up logging to both console and file."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler()
        ]
    )

def load_subjects(csv_path):
    """Loads subjects from a CSV file."""
    if not os.path.isfile(csv_path):
        logging.error(f"File not found: {csv_path}")
        return None
    return pd.read_csv(csv_path, header=None)[0]

def find_matching_subjects(mwp1_subjects, freesurfer_subjects):
    """Finds matching and unmatched subjects."""
    matching = mwp1_subjects[mwp1_subjects.isin(freesurfer_subjects)]
    unmatched = freesurfer_subjects[~freesurfer_subjects.isin(mwp1_subjects)]
    return matching, unmatched

def write_unmatched_subjects(unmatched, output_log_path):
    """Writes unmatched subjects to a log file."""
    with open(output_log_path, "w") as log_file:
        log_file.write("Unmatched FreeSurfer IDs:\n")
        log_file.writelines(f"{subj}\n" for subj in unmatched.tolist())

def process_subjects(matching_subjects, freesurfer_subjects, data_dir, output_dir, subjects_dir, freesurfer_home):
    """Processes each subject and transforms brain images from VBM space to FreeSurfer space."""
    os.environ["FREESURFER_HOME"] = freesurfer_home
    os.environ["SUBJECTS_DIR"] = subjects_dir
    os.environ["PATH"] = f"{freesurfer_home}/bin:" + os.environ["PATH"]
    
    for subject_id in matching_subjects:
        mwp1_file = f"mwp1{subject_id}_T1w.nii"
        freesurfer_id = freesurfer_subjects[freesurfer_subjects == subject_id].iloc[0]
        logging.info(f"Processing {mwp1_file} with FreeSurfer ID {freesurfer_id}")

        cat12_gm = os.path.join(data_dir, mwp1_file)
        reg_output = os.path.join(output_dir, f"{mwp1_file}_register.dat")
        output_image = os.path.join(output_dir, f"{mwp1_file}_output.mgz")
        brain_mgz = os.path.join(subjects_dir, freesurfer_id, "mri", "brain.mgz")

        if not os.path.exists(cat12_gm):
            logging.warning(f"File not found {cat12_gm}. Skipping...")
            continue
        
        if not os.path.exists(os.path.join(subjects_dir, freesurfer_id)):
            logging.warning(f"FreeSurfer directory not found for {freesurfer_id}. Skipping...")
            continue

        bbregister_command = [
            f"{freesurfer_home}/bin/bbregister", "--s", freesurfer_id,
            "--mov", cat12_gm, "--reg", reg_output, "--t1"
        ]
        try:
            subprocess.run(bbregister_command, check=True)
        except subprocess.CalledProcessError as e:
            logging.error(f"bbregister failed for {mwp1_file}: {e}")
            continue

        mri_vol2vol_command = [
            f"{freesurfer_home}/bin/mri_vol2vol", "--mov", cat12_gm,
            "--targ", brain_mgz, "--reg", reg_output, "--o", output_image,
            "--interp", "trilin", "--no-save-reg"
        ]
        try:
            subprocess.run(mri_vol2vol_command, check=True)
        except subprocess.CalledProcessError as e:
            logging.error(f"mri_vol2vol failed for {mwp1_file}: {e}")
            continue
        
        logging.info(f"Transformation completed for {mwp1_file}")

def main():
    parser = argparse.ArgumentParser(description="Transform brain images from VBM space to FreeSurfer space.")
    parser.add_argument("--mwp1_csv", required=True, help="Path to subject list CSV")
    parser.add_argument("--freesurfer_csv", required=True, help="Path to FreeSurfer subjects CSV")
    parser.add_argument("--data_dir", required=True, help="Path to input MRI directory")
    parser.add_argument("--output_dir", required=True, help="Path to output directory")
    parser.add_argument("--subjects_dir", required=True, help="Path to FreeSurfer subjects directory")
    parser.add_argument("--freesurfer_home", required=True, help="Path to FreeSurfer installation")
    parser.add_argument("--log_path", default="processing.log", help="Path to log file")
    
    args = parser.parse_args()
    
    setup_logging(args.log_path)
    logging.info("Starting processing...")

    mwp1_subjects = load_subjects(args.mwp1_csv)
    freesurfer_subjects = load_subjects(args.freesurfer_csv)
    if mwp1_subjects is None or freesurfer_subjects is None:
        logging.error("Missing required files. Exiting...")
        return

    matching_subjects, unmatched_subjects = find_matching_subjects(mwp1_subjects, freesurfer_subjects)
    logging.info(f"Number of unmatched FreeSurfer IDs: {len(unmatched_subjects)}")
    write_unmatched_subjects(unmatched_subjects, args.log_path)
    process_subjects(matching_subjects, freesurfer_subjects, args.data_dir, args.output_dir, args.subjects_dir, args.freesurfer_home)
    logging.info("Batch processing complete.")

if __name__ == "__main__":
    main()
