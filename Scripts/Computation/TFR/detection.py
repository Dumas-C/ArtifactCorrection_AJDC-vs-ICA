# -*- coding: utf-8 -*-
"""
Copyright (c) 2024 Paris Brain Institute. All rights reserved.

Created on October 2024

@author: Cassandra Dumas
"""

# Modules
# -------
# Import required libraries and custom modules
import os 
import re
import mne
import numpy as np

from tools.data_manager import load_data, load_epochs, save_epoch, save_mne_reports, save_numpy_data, load_numpy_data
from tools.utils import extract_number, get_channels
from tools.mne_reporting import generate_tfr_report
from tools.preprocessing import preparing_data_BetaPark, preprocessing

# Functions
# ---------

def generate_tfr_mi(subjects, frequencie_file, path, dataset):
    """
    Main function to generate Time-Frequency Representations (TFR) for Motor Imagery (MI).

    Parameters:
        subjects (list): List of subject identifiers.
        frequencie_file (str): Frequency band identifier for processing.
        path (dict): Paths dictionary containing data locations.
        dataset (str): Dataset name (e.g., "BetaPark").
    """
    for subject in subjects:
        # Skip specific subjects with missing data
        if extract_number(subject) in [0, 1, 9, 10]:
            print("Data not available")
            continue
        
        # Perform TFR detection for the subject
        tfr_mi_detection(subject, frequencie_file, path)
    
    # Compute global TFR across all subjects
    compute_global_tfr(subjects, frequencie_file, path, dataset)

def tfr_mi_detection(subject, frequencie_file, path):
    """
    Detect and compute Time-Frequency Representations for Motor Imagery (MI).

    Parameters:
        subject (str): Subject identifier.
        frequencie_file (str): Frequency band identifier.
        path (dict): Paths dictionary containing data locations.
    """
    # Define paths for processing types
    paths_types = {
        "ICA": f"{path['ica_path']}/_DENOISING_EEG_/{subject}",
        "RAW": f"{path['raw_data']}/{subject}",
        "AJDC": f"{path['ajdc_path']}/_DENOISING_EEG_/{frequencie_file}/_HAND_OBSERVATION_/{subject}"
    }
    
    # Define valid file prefixes
    valid_files = ["5-2", "6-2", "7-2", "8-2"]
    
    for processing_type, directory in paths_types.items():
        os.chdir(directory)
        available_files = [f for f in os.listdir(directory) if any(vf in f for vf in valid_files) and ".vhdr" in f]
        
        for file_prefix in valid_files:
            file_a = next((f for f in available_files if f"{file_prefix}-a" in f), None)
            file_b = next((f for f in available_files if f"{file_prefix}-b" in f), None)
            
            # Merge files if both are available
            if file_a and file_b:
                print(f"Processing {file_prefix}: merging {file_a} and {file_b}")
                signal_a = load_data(file_a)
                signal_b = load_data(file_b)
                signal = mne.concatenate_raws([signal_a, signal_b])
            elif file_a or file_b:
                file_to_process = file_a if file_a else file_b
                print(f"Processing {file_prefix}: using {file_to_process} only")
                signal = load_data(file_to_process)
            else:
                print(f"Skipping {file_prefix}: no files found")
                continue
            
            # Preprocess data for RAW processing type
            if processing_type == "RAW":
                preparing_data_BetaPark(signal, extract_number(subject), average_reference=True)
                preprocessing(signal, notch=True, high_pass_filter=0.5, average_reference=True)
            
            # Extract relevant annotations for stimulus
            annot_stimulus = next(((annot['description'], int(re.search(r'\b[34]\b', annot['description']).group())) 
                                    for annot in signal.annotations 
                                    if re.search(r'\b[34]\b', annot['description'])), None)
            
            event_id = dict(IM=annot_stimulus[1])
            select_id = {annot_stimulus[0]: annot_stimulus[1]}
            events, _ = mne.events_from_annotations(signal, event_id=select_id)
            
            # Create epochs
            epochs_im = mne.Epochs(signal, events, event_id, -5, 30, proj=True, baseline=None, preload=True)
            
            # Handle bad epochs for ICA processing type
            saving_path = f"{path['tfr_path']}/_MOTOR_IMAGERY_/_BAD_EPOCHS_INDICES_/{subject}"
            filename = f"bad_epochs_indices_{file_prefix}.npy"
            if processing_type == "ICA" and not os.path.isfile(os.path.join(saving_path, filename)):
                epochs_im.plot(block=True)
                bad_epochs_indices = [i for i, log in enumerate(epochs_im.drop_log) if log]
                save_numpy_data(bad_epochs_indices, saving_path, filename)
            else:
                bad_epochs_indices = list(load_numpy_data(saving_path, filename))
                epochs_im.drop(bad_epochs_indices, reason='BAD')
            
            # Save epochs
            if processing_type == "AJDC":
                saving_path = f"{path['tfr_path']}/_MOTOR_IMAGERY_/_EPOCHS_/_{processing_type}_/{frequencie_file}/{subject}"
            else:
                saving_path = f"{path['tfr_path']}/_MOTOR_IMAGERY_/_EPOCHS_/_{processing_type}_/{subject}"
            filename = f"{file_prefix}-epo.fif"
            save_epoch(epochs_im, saving_path, filename)
            
            # Compute and save TFR
            tfr_im = epochs_im.compute_tfr("morlet", freqs=np.arange(0.5, 80, 0.5), n_cycles=np.arange(0.5, 80, 0.5)/2, n_jobs=15, average=True)
            report = generate_tfr_report(tfr_im, processing_type, subject, file_prefix)
            
            # Save report
            if processing_type == "AJDC":
                saving_path = f"{path['mne_reports_path']}_TFR_/_{processing_type}_/{frequencie_file}/{subject}"
            else:
                saving_path = f"{path['mne_reports_path']}_TFR_/_{processing_type}_/{subject}"
            filename = f"Time_Frequency_{file_prefix}.html"
            save_mne_reports(report, saving_path, filename)

def compute_global_tfr(subjects, frequencie_file, path, dataset):
    """
    Compute global Time-Frequency Representations (TFR) for Motor Imagery (MI) across all subjects.

    Parameters:
        subjects (list): List of subject identifiers.
        frequencie_file (str): Frequency band identifier for processing.
        path (dict): Paths dictionary containing data locations.
        dataset (str): Dataset name (e.g., "BetaPark").
    """
    processing_type = ["RAW", "AJDC", "ICA"]
    
    for processing in processing_type:
        global_epoch_im = []  # To store concatenated epochs across all subjects

        for subject in subjects:
            # Skip specific subjects in BetaPark dataset
            if dataset == "BetaPark" and extract_number(subject) in [0, 1, 9, 10]:
                print("Data not available")
                continue

            # Define directory based on processing type
            if processing == "AJDC":
                directory = f"{path['tfr_path']}/_MOTOR_IMAGERY_/_EPOCHS_/_{processing}_/{frequencie_file}/{subject}"
            else:
                directory = f"{path['tfr_path']}/_MOTOR_IMAGERY_/_EPOCHS_/_{processing}_/{subject}"

            # Load and concatenate epochs for the subject
            epochs_im = load_epochs(directory)
            for epoch in epochs_im:
                epoch.event_id = {'IM': 3}
                for event in epoch.events:
                    event[2] = 3  # Uniform event code for concatenation
            
            s_epochs = mne.concatenate_epochs(epochs_im)

            # Save concatenated epochs for the subject
            if processing == "AJDC":
                saving_path = f"{path['tfr_path']}/_MOTOR_IMAGERY_/_EPOCHS_/_{processing}_/{frequencie_file}/{subject}"
            else:
                saving_path = f"{path['tfr_path']}/_MOTOR_IMAGERY_/_EPOCHS_/_{processing}_/{subject}"
            filename = f"{subject}-epo.fif"
            save_epoch(s_epochs, saving_path, filename)

            global_epoch_im.append(s_epochs)

            # Compute TFR for the subject and save the report
            tfr_im = s_epochs.compute_tfr(
                "morlet", freqs=np.arange(0.5, 80, 0.5), 
                n_cycles=np.arange(0.5, 80, 0.5) / 2, 
                n_jobs=15, average=True
            )

            report = generate_tfr_report(tfr_im, processing, subject)

            if processing == "AJDC":
                saving_path = f"{path['mne_reports_path']}_TFR_/_{processing}_/{frequencie_file}/{subject}"
            else:
                saving_path = f"{path['mne_reports_path']}_TFR_/_{processing}_/{subject}"
            filename = f"Time_Frequency_{subject}.html"
            save_mne_reports(report, saving_path, filename)

        # Ensure common channels across all subjects
        common_channels = set(global_epoch_im[0].info['ch_names'])
        for epoch in global_epoch_im[1:]:
            common_channels.intersection_update(epoch.info['ch_names'])

        # Preserve channel order
        ordered_channels = get_channels()
        common_channels = [ch for ch in ordered_channels if ch in common_channels]

        # Pick only common channels for all epochs
        for i, epoch in enumerate(global_epoch_im):
            global_epoch_im[i] = epoch.pick(common_channels)

        # Concatenate epochs across all subjects
        global_epoch_im = mne.concatenate_epochs(global_epoch_im)

        # Save global concatenated epochs
        if processing == "AJDC":
            saving_path = f"{path['tfr_path']}/_MOTOR_IMAGERY_/_EPOCHS_/_{processing}_/{frequencie_file}/_GLOBAL_"
        else:
            saving_path = f"{path['tfr_path']}/_MOTOR_IMAGERY_/_EPOCHS_/_{processing}_/_GLOBAL_"
        filename = "GLOBAL-epo.fif"
        save_epoch(global_epoch_im, saving_path, filename)

        # Compute global TFR and save the report
        tfr_im = global_epoch_im.compute_tfr(
            "morlet", freqs=np.arange(0.5, 80, 0.5), 
            n_cycles=np.arange(0.5, 80, 0.5) / 2, 
            n_jobs=15, average=True
        )

        report = generate_tfr_report(tfr_im, processing)

        if processing == "AJDC":
            saving_path = f"{path['mne_reports_path']}_TFR_/_{processing}_/{frequencie_file}/_GLOBAL_"
        else:
            saving_path = f"{path['mne_reports_path']}_TFR_/_{processing}_/_GLOBAL_"
        filename = f"Time_Frequency_{processing}.html"
        save_mne_reports(report, saving_path, filename)
