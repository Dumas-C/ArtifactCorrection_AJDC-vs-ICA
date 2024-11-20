# -*- coding: utf-8 -*-
"""
Copyright (c) 2024 Paris Brain Institute. All rights reserved.

Created on October 2024

@author: Cassandra Dumas
"""

# Modules
# -------
import os
import mne
import numpy as np

# Custom modules for data management and preprocessing
from tools.data_manager import save_mne_reports, save_numpy_data, load_numpy_data
from tools.utils import extract_number
from tools.mne_reporting import generate_snr_report

# Functions
# ---------

def snr_computation(subjects, frequencie_file, path, dataset, nf_session):
    """
    Main function to compute SNR for each subject and globally.

    Parameters:
        subjects (list): List of subject identifiers.
        frequencie_file (str): Frequency band identifier for processing.
        path (dict): Paths dictionary containing data locations.
        dataset (str): Name of the dataset (e.g., "BetaPark").
        nf_session (dict): Neurofeedback session information for SNR reports.
    """
    for subject in subjects:
        # Skip unavailable subjects
        if extract_number(subject) in [0, 1, 9, 10]:
            print("Data not available")
            continue
        
        # Compute SNR for individual subject
        subject_computation(subject, frequencie_file, path, nf_session)
    
    # Compute global SNR across subjects
    global_computation(subjects, frequencie_file, path, dataset)

def subject_computation(subject, frequencie_file, path, nf_session):
    """
    Computes SNR for a single subject across all processing types.

    Parameters:
        subject (str): Subject identifier.
        frequencie_file (str): Frequency band identifier.
        path (dict): Paths dictionary containing data locations.
        nf_session (dict): Neurofeedback session information for SNR reports.
    """
    artefacts = ["BLINKS"]  # Artefacts of interest (e.g., blinks)
    
    for artefact in artefacts:
        paths_types = {
            "RAW": f"{path['pe_path']}/_RAW_/_{artefact}_/{subject}/_RUN_",
            "AJDC": f"{path['pe_path']}/_AJDC_/{frequencie_file}/_{artefact}_/{subject}/_RUN_",
            "ICA": f"{path['pe_path']}/_ICA_/_{artefact}_/{subject}/_RUN_"
        }

        pe_data = {}  # To store evoked potential data by processing type
        runs = []  # To track runs for the subject
        
        for processing_type, directory in paths_types.items():
            os.chdir(directory)
            files = os.listdir()

            pe_data[processing_type] = []
            
            for file in files:
                # Read evoked potential
                evoked = mne.read_evokeds(file)[0]
                evoked.drop_channels(['FT9', 'TP9'], on_missing='ignore')  # Drop specific channels
                pe_data[processing_type].append(evoked)

                # Extract run name
                run = file[17:-8]
                runs.append(run)

        # Compute SNR for the subject
        snr_global_ajdc, snr_electrode_ajdc, snr_global_ica, snr_electrode_ica, electrodes = process_evokeds_for_type(pe_data, subject, runs)
        
        # Save SNR results
        saving_path = f"{path['snr_path']}/_SNR_SCORES_/{subject}"
        filenames = ['snr_global_ajdc.npy', 'snr_electrode_ajdc.npy', 'snr_global_ica.npy', 'snr_electrode_ica.npy']
        
        for i, element in enumerate([snr_global_ajdc, snr_electrode_ajdc, snr_global_ica, snr_electrode_ica]):
            save_numpy_data(element, saving_path, filenames[i])
        
        # Generate and save SNR report
        report = generate_snr_report(snr_global_ajdc, snr_electrode_ajdc, snr_global_ica, snr_electrode_ica, electrodes, subject, nf_session)
        saving_path = f"{path['mne_reports_path']}_SNR_/_{subject}_"
        filename = f"SNR_scores_{subject}.html"
        save_mne_reports(report, saving_path, filename)

def global_computation(subjects, frequencie_file, path, dataset):
    """
    Compute global SNR across all subjects.

    Parameters:
        subjects (list): List of subject identifiers.
        frequencie_file (str): Frequency band identifier.
        path (dict): Paths dictionary containing data locations.
        dataset (str): Name of the dataset (e.g., "BetaPark").
    """
    artefacts = ["BLINKS"]  # Artefacts of interest
    
    for artefact in artefacts:
        # Lists to store global SNR and electrode-wise SNR
        snr_ajdc, snr_electrode_ajdc, snr_ica, snr_electrode_ica = [], [], [], []
        
        for subject in subjects:
            # Skip unavailable subjects in BetaPark
            if dataset == "BetaPark" and extract_number(subject) in {0, 1, 9, 10}:
                print("Data not available")
                continue
            
            directory = f"{path['snr_path']}/_SNR_SCORES_/{subject}"
            filenames = ['snr_global_ajdc.npy', 'snr_electrode_ajdc.npy', 'snr_global_ica.npy', 'snr_electrode_ica.npy']
            target_lists = [snr_ajdc, snr_electrode_ajdc, snr_ica, snr_electrode_ica]
        
            for filename, target_list in zip(filenames, target_lists):
                # Load SNR data and append to the appropriate list
                data = load_numpy_data(directory, filename).flatten()[0]
                target_list.append(data)

def compute_snr(data_processed, data_raw):
    """
    Compute global and electrode-wise Signal-to-Noise Ratio (SNR).

    Parameters:
        data_processed (array): Processed EEG data.
        data_raw (array): Raw EEG data.

    Returns:
        snr_global (float): Global SNR across all electrodes.
        snr_electrode (array): SNR computed for each electrode.
    """
    snr_global = 10 * np.log10(np.mean(data_processed**2) / np.mean(data_raw**2))
    snr_electrode = 10 * np.log10(np.mean(data_processed**2, axis=1) / np.mean(data_raw**2, axis=1))
    return snr_global, snr_electrode

def process_evokeds_for_type(pe_data, subject, runs=None):
    """
    Process evoked potentials for each processing type and compute SNR.

    Parameters:
        pe_data (dict): Dictionary containing evoked potentials for each processing type.
        subject (str): Subject identifier.
        runs (list, optional): List of run identifiers.

    Returns:
        snr_global_ajdc (dict): Global SNR for AJDC.
        snr_electrode_ajdc (dict): Electrode-wise SNR for AJDC.
        snr_global_ica (dict): Global SNR for ICA.
        snr_electrode_ica (dict): Electrode-wise SNR for ICA.
        common_electrodes (set): Set of common electrodes across processing types.
    """
    snr_global_ajdc, snr_electrode_ajdc = {}, {}
    snr_global_ica, snr_electrode_ica = {}, {}

    for i, raw in enumerate(pe_data["RAW"]):
        # Find common electrodes across all processing types
        common_electrodes = set(raw.ch_names).intersection(
            set(pe_data["AJDC"][i].ch_names), set(pe_data["ICA"][i].ch_names)
        )
        # Select only common electrodes for all processing types
        for pe_set in ["RAW", "AJDC", "ICA"]:
            pe_data[pe_set][i].pick(list(common_electrodes))
        
        # Extract raw and processed data
        data_raw = pe_data["RAW"][i].get_data(units='uV', tmin=-0.2, tmax=0.2)
        data_ajdc = pe_data["AJDC"][i].get_data(units='uV', tmin=-0.2, tmax=0.2)
        data_ica = pe_data["ICA"][i].get_data(units='uV', tmin=-0.2, tmax=0.2)

        # Compute SNR for AJDC and ICA
        snr_global_ajdc[runs[i]], snr_electrode_ajdc[runs[i]] = compute_snr(data_ajdc, data_raw)
        snr_global_ica[runs[i]], snr_electrode_ica[runs[i]] = compute_snr(data_ica, data_raw)

    return snr_global_ajdc, snr_electrode_ajdc, snr_global_ica, snr_electrode_ica, common_electrodes
