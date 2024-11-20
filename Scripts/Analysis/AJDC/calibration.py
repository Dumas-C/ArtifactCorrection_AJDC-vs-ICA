# -*- coding: utf-8 -*-
"""
Copyright (c) 2024 Paris Brain Institute. All rights reserved.

Created on June 2024

@author: Cassandra Dumas

"""

# Modules
# -------
import os
import numpy as np
import mne

from pyriemann.spatialfilters import AJDC 
from scipy.signal import welch

# Custom modules for data management, visualization, and preprocessing
from tools.data_manager import load_data, export_signal, save_ajdc_parameters, save_mne_reports
from tools.utils import extract_number
from tools.mne_reporting import generate_ajdc_report
from tools.visualisation import plot_spectrum_and_topomap
from tools.preprocessing import preparing_data_BetaPark, preprocessing, crop_calibration_signal_BetaPark

# Functions
# ---------

def calibrate_ajdc(subjects, conditions, frequencie_file, path, dataset):
    """
    Perform AJDC calibration for a list of subjects and conditions.
    
    Parameters:
        subjects (list): List of subject identifiers.
        conditions (list): List of conditions to process.
        frequencie_file (str): Frequency range identifier for AJDC.
        path (dict): Paths for data storage and retrieval.
        dataset (str): Dataset name (e.g., BetaPark).
    """
    for condition in conditions:
        for subject in subjects:
            # Skip specific subjects
            if extract_number(subject) in [0, 1, 9, 10]:
                print("Data not available")
                continue
            
            # Process calibration for the given subject and condition
            process_calibration(subject, condition, frequencie_file, path, dataset)
            
def process_calibration(subject, condition, frequencie_file, path, dataset):
    """
    Process calibration data for a subject and condition.
    
    Parameters:
        subject (str): Subject identifier.
        condition (str): Condition name.
        frequencie_file (str): Frequency range identifier.
        path (dict): Paths for data storage and retrieval.
        dataset (str): Dataset name.
    """
    
    directory = path['raw_data'] + subject
    os.chdir(directory)
    
    for file in os.listdir(directory):
        if '2-1.vhdr' in file:
            # Load and prepare the calibration signal
            signal = load_data(file)
            preparing_data_BetaPark(signal, extract_number(subject), average_reference=False)
            crop_calibration_signal_BetaPark(signal, condition)
    
        if 'signal' in locals():
            # Preprocess the calibration signal
            preprocessing(signal, notch=True, high_pass_filter = 1.0, average_reference=False)
            
            # Save the preprocessed calibration signal
            saving_path = f"{path['ajdc_path']}/_CALIBRATION_DATA_/{frequencie_file}/{condition}/{subject}"
            filename = f"{subject}_calibration_data.vhdr"
            export_signal(signal, saving_path, filename, format='brainvision', overwrite=True)
            
            # Fitting AJDC
            ajdc = AJDC(window=signal.info['sfreq'], overlap=0.5, fmin=int(frequencie_file[-5:-4]), fmax=int(frequencie_file[-3:-1]), fs=signal.info['sfreq'], dim_red={'expl_var': 0.99}, verbose=True)
            ajdc.fit(signal.get_data()[np.newaxis, np.newaxis, ...])
            
            # Transform signal into source space
            source_signal = ajdc.transform(signal.get_data()[np.newaxis, ...])[0]
            sr_names = ['S' + str(s).zfill(2) for s in range(ajdc.n_sources_)]
            sr_info = mne.create_info(ch_names=sr_names, ch_types=['misc'] * ajdc.n_sources_, sfreq=signal.info['sfreq']) 
            source = mne.io.RawArray(source_signal, sr_info, first_samp=signal.first_samp, verbose=False)
            source.set_meas_date(signal.info['meas_date'])
            source.set_annotations(signal.annotations)
            
            # Save the source data
            saving_path = f"{path['ajdc_path']}/_SOURCES_/{frequencie_file}/{condition}"
            filename = f"{subject}_components_data.vhdr"
            export_signal(source, saving_path, filename, format='brainvision', overwrite=True)
            
            # Compute spectra and generate figures for each source
            spectrums_figures = []
            for i in range(ajdc.n_sources_):
                data = source.get_data(picks=[i])
                f, spectrum_abs = compute_spectrum(data, signal.info['sfreq'], int(frequencie_file[-5:-4]), int(frequencie_file[-3:-1]))
                fig = plot_spectrum_and_topomap(f, spectrum_abs, ajdc.backward_filters_[:, i], signal.info, i)
                spectrums_figures.append(fig)
                
            source.plot(block=True)
            
            # Ask the user which component is considered as blinks and saccades
            blink_str = input("Blink Component(s) : ").split()
            saccade_str = input("Saccade Component(s) : ").split()
            
            # Filter and convert valid numeric inputs into integers
            blink = [int(num) for num in blink_str if num.isdigit()]
            saccade = [int(num) for num in saccade_str if num.isdigit()]
            
            # Combine blink and saccade lists to form the bad_sources list
            bad_sources = blink + saccade
            # Remove any components labeled as NaN (though previous filtering should suffice)
            bad_sources = [source for source in bad_sources if 'NaN' not in str(source)]
            
            # Save AJDC parameters
            saving_path = f"{path['ajdc_path']}/_PARAMETERS_/{frequencie_file}/{condition}"
            filename = f"{subject}parameters_AJDC.npz"
            save_ajdc_parameters(ajdc, blink, saccade, saving_path, filename)
            
            # Correct the calibration signal according the bad components previously selected
            corrected_signal = ajdc.inverse_transform(source.get_data()[np.newaxis, ...], supp=bad_sources)[0]
            signal_corrected = mne.io.RawArray(corrected_signal, signal.info, first_samp=signal.first_samp, verbose=False)
            signal_corrected.set_meas_date(signal.info['meas_date'])
            signal_corrected.set_annotations(signal.annotations)
            
            # Save the corrected calibration signal
            saving_path = f"{path['ajdc_path']}/_CALIBRATION_DATA_/{frequencie_file}/{condition}/{subject}"
            filename = f"{subject}calibration_corrected.vhdr"
            export_signal(signal_corrected, saving_path, filename, format='brainvision', overwrite=True)
            
            # Generate and save the AJDC report
            report = generate_ajdc_report(subject, condition, ajdc, blink, saccade, signal, source, sr_names, spectrums_figures, signal_corrected)
            saving_path = f"{path['mne_reports_path']}_AJDC_/{frequencie_file}/{condition}"
            filename = f"{subject}_AJDC_Decomposition_{frequencie_file}.html"
            save_mne_reports(report, saving_path, filename)
            
def compute_spectrum(data, sfreq, fmin, fmax):
    """
    Compute the power spectrum of the signal using Welch's method.
    
    Parameters:
        data (ndarray): Input signal data.
        sfreq (float): Sampling frequency.
        fmin (int): Minimum frequency of interest.
        fmax (int): Maximum frequency of interest.
    
    Returns:
        tuple: Frequencies and normalized power spectrum.
    """
    f, spectrum = welch(data, fs=sfreq, nperseg=1024, noverlap=int(1024 * 0.5))
    f_mask = (f >= fmin) & (f <= fmax)
    spectrum_abs = spectrum[0, f_mask]
    spectrum_abs /= np.linalg.norm(spectrum_abs)
    return f[f_mask], spectrum_abs
            