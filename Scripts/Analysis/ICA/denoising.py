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

import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Qt5Agg')

# Custom modules for data management, and preprocessing
from tools.data_manager import load_data, export_signal, save_ica_parameters, save_ica_bad_components, save_mne_reports
from tools.utils import extract_number
from tools.preprocessing import preparing_data_BetaPark, preprocessing

# Functions
# ---------

def denoise_ica(subjects, path, runs_desc, dataset):
    """
    Apply ICA-based denoising to EEG data for a list of subjects.
    
    Parameters:
        subjects (list): List of subject identifiers.
        path (dict): Dictionary containing paths for data storage and retrieval.
        runs_desc (dict): Dictionary mapping runs to descriptions.
        dataset (str): Dataset name (e.g., BetaPark).
    """
    
    for subject in subjects:
        # Skip specific subjects
        if extract_number(subject) in [0, 1, 9, 10]:
            print("Data not available")
            continue
        
        # Process denoising for the current subject
        process_denoising(subject, path, runs_desc)
        
def process_denoising(subject, path, runs_desc):
    """
    Perform the ICA denoising process for a specific subject.
    
    Parameters:
        subject (str): Subject identifier.
        path (dict): Dictionary containing paths for data storage and retrieval.
        runs_desc (dict): Dictionary mapping runs to descriptions.
    """
    
    # Initialize an MNE report to document the ICA process
    report = mne.Report(title=f"Subject: {subject}")
    blinks_components = {}
    saccades_components = {}
    
    # Navigate to the subject's raw EEG data directory
    os.chdir(path['raw_data'] + subject)
    for file in filter(lambda f: ".vhdr" in f, os.listdir()):
        # Extract the run identifier and corresponding description
        run = file[9:]
        etape = [key for key in runs_desc.keys() if key in run][0]
        
        # Load and preprocess the EEG signal
        signal = load_data(file)
        preparing_data_BetaPark(signal, extract_number(subject), average_reference=True)
        preprocessing(signal, notch=True, high_pass_filter = 0.5, average_reference=True)
        
        # Fit ICA model to the preprocessed signal
        ica = mne.preprocessing.ICA(n_components=0.99, random_state=97)
        ica.fit(signal)
        
        # Plot ICA components for user review
        ica.plot_components()
        source = ica.get_sources(signal)
        
        # Save the source components
        saving_path = f"{path['ica_path']}/_SOURCES_/{subject}"
        filename = f"{run}_components.vhdr"
        export_signal(signal, saving_path, filename, format='brainvision', overwrite=True)
        
        # Display the source signals and prompt the user to identify blink and saccade components
        source.plot(block=True)
        blink_str = input('Blinks components : ').split(" ")
        saccade_str = input('Saccades components : ').split(" ")
        
        # Convert user inputs into integer lists for blink and saccade components
        blinks = [int(item) for item in blink_str if item.isdigit()]
        saccades = [int(item) for item in saccade_str if item.isdigit()]
        
        # Update the component dictionaries with identified components
        blinks_components[f"{run}"] = 'None' if not blinks else "ICA" + ("00" if blinks[0] < 10 else "0") + str(blinks[0])
        saccades_components[f"{run}"] = 'None' if not saccades else "ICA" + ("00" if saccades[0] < 10 else "0") + str(saccades[0])
        
        # Exclude the identified blink components
        ica.exclude = blinks 
        
        # Save the ICA parameters
        saving_path = f"{path['ica_path']}/_ICA_/{subject}"
        filename = f"{run}-ica.fif"
        save_ica_parameters(ica, saving_path, filename)
        
        # Apply the ICA model to remove artifacts from the signal
        ica.apply(signal)
        
        # Save the denoised signal
        saving_path = f"{path['ica_path']}/_DENOISING_EEG_/{subject}"
        filename = file[:file.index(".")]+"_denoised.vhdr"
        export_signal(signal, saving_path, filename, format='brainvision', overwrite=True)
        
        # Add the ICA information to the MNE report
        report.add_ica(ica, title=runs_desc[etape], inst=signal)
    
    # Save the identified bad components (blinks and saccades)
    saving_path = f"{path['ica_path']}"
    filename = f"{subject}_"
    save_ica_bad_components(blinks_components, saccades_components, saving_path, filename)
    
    # Save the MNE report
    saving_path = f"{path['mne_reports_path']}_ICA_/"
    filename = f"{subject}_ICA.html"
    save_mne_reports(report, saving_path, filename)
    
    # Close all open Matplotlib figures
    plt.close('all')
