% MATLAB Script for Normalizing GM Images
% -------------------------------------------------
% This script is based on SPM12 and CAT12 but modified to run independently
% without a GUI. It automates the normalization process for multiple subjects
% based on a given subject list.
%
% GitHub Repository: [---]
%
% Author: [Nooshin Safari]
% Date: [Date]
% License: MIT (or another license of your choice)
% -------------------------------------------------

% Define paths (use relative paths for GitHub compatibility)
project_dir = fileparts(mfilename('fullpath')); % Get script directory
spm12_path = fullfile(project_dir, 'spm12');  % Update this if needed
cat12_path = fullfile(project_dir, 'cat12');  % Update this if needed
data_path = fullfile(project_dir, 'data');    % Input MRI data directory
output_dir = fullfile(project_dir, 'results'); % Output directory
subject_list_file = fullfile(data_path, 'ACEVBMSUB.csv'); % Subject list file

% Ensure required directories exist
if ~isfolder(output_dir)
    mkdir(output_dir);
    disp(['Created output directory: ', output_dir]);
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

% Process each subject
for i = 1:length(subject_ids)
    subject_id = subject_ids{i};
    disp(['Processing subject: ' subject_id]);

    % Define input files for the subject
    gm_file = fullfile(data_path, ['mwp1', subject_id, '_T1w.nii']); % Gray matter file
    deformation_field = fullfile(data_path, ['y_', subject_id, '_T1w.nii']); % Deformation field

    % Check if the required files exist
    if ~isfile(gm_file)
        warning('GM file not found for subject %s: %s', subject_id, gm_file);
        continue;
    end
    if ~isfile(deformation_field)
        warning('Deformation field not found for subject %s: %s', subject_id, deformation_field);
        continue;
    end

    % Prepare SPM batch for normalization
    clear matlabbatch;
    matlabbatch{1}.spm.spatial.normalise.write.subj.def = {deformation_field}; % Deformation field
    matlabbatch{1}.spm.spatial.normalise.write.subj.resample = {gm_file}; % File to normalize

    % Normalization options
    matlabbatch{1}.spm.spatial.normalise.write.woptions.bb = [-78 -112 -70; 78 76 85]; % Bounding box in MNI space
    matlabbatch{1}.spm.spatial.normalise.write.woptions.vox = [1 1 1]; % 1mm isotropic resolution
    matlabbatch{1}.spm.spatial.normalise.write.woptions.interp = 4; % 4th-degree B-spline interpolation
    matlabbatch{1}.spm.spatial.normalise.write.woptions.prefix = 'w'; % Prefix for output

    % Change to output directory
    cd(output_dir);

    % Run the normalization batch
    try
        spm_jobman('run', matlabbatch);
        disp(['Normalization completed successfully for subject: ' subject_id]);
    catch ME
        warning('Error during normalization for subject %s: %s', subject_id, ME.message);
    end
end

disp('Normalization process completed for all subjects.');
