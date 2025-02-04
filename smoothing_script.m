% MATLAB Script for Smoothing Normalized GM Images
% -------------------------------------------------
% This script is based on SPM12 and CAT12 but modified to run independently
% without a GUI. It automates the smoothing process for multiple subjects
% based on a given subject list.
%
% GitHub Repository: [Your GitHub Repo Link]
%
% Author: [Your Name]
% Date: [Date]
% License: MIT (or another license of your choice)
% -------------------------------------------------

% Define paths (use relative paths for GitHub compatibility)
project_dir = fileparts(mfilename('fullpath')); % Get script directory
spm12_path = fullfile(project_dir, 'spm12');  % Update this if needed
cat12_path = fullfile(project_dir, 'cat12');  % Update this if needed
data_path = fullfile(project_dir, 'data');    % Input MRI data directory
smoothed_dir = fullfile(project_dir, 'results'); % Output directory
subject_list_file = fullfile(data_path, 'ACEVBMSUB.csv'); % Subject list file

% Ensure required directories exist
if ~isfolder(smoothed_dir)
    mkdir(smoothed_dir);
    disp(['Created output directory: ', smoothed_dir]);
end

% Verify SPM12 and CAT12 paths
if ~isfolder(spm12_path)
    error('SPM12 directory not found. Please add it to the project.');
end
if ~isfolder(cat12_path)
    error('CAT12 directory not found. Please add it to the project.');
end

% Add SPM12 and CAT12 to MATLAB search path
addpath(spm12_path);
addpath(cat12_path);
disp('SPM12 and CAT12 paths added successfully.');

% Check if the subject list exists
if ~isfile(subject_list_file)
    error('Subject list file not found: %s', subject_list_file);
end

% Read subject IDs from the list file
subject_ids = readlines(subject_list_file);
subject_ids = strip(subject_ids); % Remove any whitespace

% Initialize SPM
spm('defaults', 'FMRI');
spm_jobman('initcfg');

% Define smoothing kernel (FWHM)
fwhm = [8 8 8];

% Process each subject
for i = 1:length(subject_ids)
    subject_id = subject_ids{i};
    disp(['Processing subject: ' subject_id]);

    % Define the subject's normalized GM image filename
    normalized_gm_file = fullfile(data_path, ['wmwp1', subject_id, '_T1w.nii']);

    % Check if the file exists
    if ~isfile(normalized_gm_file)
        warning('File not found: %s', normalized_gm_file);
        continue;
    end

    % Prepare SPM batch
    clear matlabbatch;
    matlabbatch{1}.spm.spatial.smooth.data = {normalized_gm_file};
    matlabbatch{1}.spm.spatial.smooth.fwhm = fwhm;
    matlabbatch{1}.spm.spatial.smooth.dtype = 0;
    matlabbatch{1}.spm.spatial.smooth.im = 0;
    matlabbatch{1}.spm.spatial.smooth.prefix = 's';

    % Run the smoothing batch
    try
        spm_jobman('run', matlabbatch);
        disp(['Smoothing completed for subject: ' subject_id]);
    catch ME
        warning('Error smoothing subject %s: %s', subject_id, ME.message);
    end
end

disp('Smoothing process completed for all subjects.');
