# -*- coding: utf-8 -*-
"""
Copyright (c) 2024 Paris Brain Institute. All rights reserved.

Created on June 2024

@author: Cassandra Dumas

"""

# Modules
# -------
import os
import mne
import numpy as np

from pyriemann.spatialfilters import AJDC 

# Custom modules for data management, and preprocessing
from tools.data_manager import load_data, export_signal
from tools.utils import extract_number
from tools.preprocessing import preparing_data_BetaPark, preprocessing


# Functions
# ---------
def denoise_ajdc(subjects, conditions, frequencie_file, path, dataset):
    """
    Apply AJDC denoising to EEG data for a list of subjects and conditions.
    
    Parameters:
        subjects (list): List of subject identifiers.
        conditions (list): List of conditions for denoising.
        frequencie_file (str): Frequency band identifier for AJDC.
        path (dict): Dictionary containing paths for data storage and retrieval.
        dataset (str): Dataset name (e.g., BetaPark).
    """
    
    for condition in conditions:
        for subject in subjects:
            # Skip specific subjects 
            if extract_number(subject) in [0, 1, 9, 10]:
                print("Data not available")
                continue
            
            # Process denoising for the current subject and condition
            process_denoising(subject, condition, frequencie_file, path)
            
def process_denoising(subject, condition, frequencie_file, path):
    """
    Perform the AJDC denoising process for a specific subject and condition.
    
    Parameters:
        subject (str): Subject identifier.
        condition (str): Condition name.
        frequencie_file (str): Frequency band identifier for AJDC.
        path (dict): Dictionary containing paths for data storage and retrieval.
    """
    
    # Load precomputed AJDC parameters from the calibration step
    parameters_path = os.path.join(path['ajdc_path'], "_PARAMETERS_", frequencie_file, condition, f"{subject}parameters_AJDC.npz")
    ajdc_parameters = np.load(parameters_path)
    
    # Reconstruct the AJDC object using saved parameters
    ajdc = AJDC(window=ajdc_parameters['sfreq'], overlap=ajdc_parameters['overlap'], fmin=ajdc_parameters['fmin'], fmax=ajdc_parameters['fmax'], fs=ajdc_parameters['sfreq'], dim_red={'max_cond': 100})
    
    # Restore AJDC-specific attributes
    ajdc.n_channels_ = ajdc_parameters['n_channel']
    ajdc.n_sources_ = ajdc_parameters['n_source']
    ajdc.backward_filters_ = ajdc_parameters['mixage']
    ajdc.forward_filters_ = ajdc_parameters['demixage']
    ajdc.freqs_ = ajdc_parameters['sfreq']
    
    # Extract bad components (blinks and saccades) for denoising
    bad_sources = [ajdc_parameters['blinks_components'].flatten()]
    bad_sources = [int(b) for b in bad_sources if not np.isnan(b)]

    eeg_path = path['raw_data'] + subject
    os.chdir(eeg_path)
    suffixe = ".vhdr"

    for file in filter(lambda f: suffixe in f, os.listdir()):
        signal = load_data(file)
        
        # Prepare and preprocess the signal for AJDC
        preparing_data_BetaPark(signal, extract_number(subject), average_reference=True)
        preprocessing(signal, notch=True, high_pass_filter = 0.5, average_reference=True) 
        
        # Create fixed-length epochs of 500 ms
        epochs = mne.make_fixed_length_epochs(signal, duration=0.5, preload=True)
    
        raws = []
        # Denoise each epoch in a 'replay' mode using AJDC
        for epoch in epochs:
            # Transform the epoch to source space
            sources = ajdc.transform(epoch[np.newaxis, ...])
            # Suppress bad components and reconstruct the signal
            denoised_data = ajdc.inverse_transform(sources, supp=bad_sources)
            # Convert the denoised data back to a RawArray format
            denoised_epoch = mne.io.RawArray(denoised_data[0], signal.info, first_samp=0, verbose=False)
            raws.append(denoised_epoch)

        # Concatenate all denoised epochs into a single Raw object
        signal_corrected = mne.concatenate_raws(raws, preload=True)
        # Preserve the original annotations
        signal_corrected.set_annotations(signal.annotations)
        
        # Save the denoised signal to the specified directory
        saving_path = f"{path['ajdc_path']}/_DENOISING_EEG_/{frequencie_file}/{condition}/{subject}"
        filename = file[:file.index(".")]+"_denoised.vhdr"
        export_signal(signal_corrected, saving_path, filename, format='brainvision', overwrite=True)
        