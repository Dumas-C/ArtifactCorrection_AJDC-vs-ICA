# -*- coding: utf-8 -*-
"""
Copyright (c) 2024 Paris Brain Institute. All rights reserved.

Created on June 2024

@author: Cassandra Dumas

"""

# Modules
# -------
import mne
import numpy as np
import os
from tools.utils import create_directory

# Functions
# ---------

def load_data(file_path):
    """
    Load raw EEG data from a file.
    
    Parameters:
        file_path (str): Path to the raw data file.
    
    Returns:
        Raw data object from MNE.
    """
    data = mne.io.read_raw(file_path, preload=True)
    return data


def load_epochs(directory):
    """
    Load all epoch files in a directory.
    
    Parameters:
        directory (str): Directory containing epoch files.
    
    Returns:
        list: List of Epochs objects.
    """
    return [mne.read_epochs(os.path.join(directory, file), preload=True) for file in os.listdir(directory)]


def load_epoch(file_path):
    """
    Load a single epochs file.
    
    Parameters:
        file_path (str): Path to the epochs file.
    
    Returns:
        Epochs object.
    """
    return mne.read_epochs(file_path, preload=True)


def load_numpy_data(directory, file):
    """
    Load a NumPy file.
    
    Parameters:
        directory (str): Directory containing the file.
        file (str): File name.
    
    Returns:
        NumPy array.
    """
    data = np.load(os.path.join(directory, file), allow_pickle=True)
    return data


def export_signal(signal, path, filename, format='brainvision', overwrite=False):
    """
    Export raw EEG signal to a specified format.
    
    Parameters:
        signal (Raw): MNE Raw object.
        path (str): Directory to save the file.
        filename (str): Name of the file.
        format (str): Export format (default is 'brainvision').
        overwrite (bool): Overwrite existing files (default is False).
    """
    create_directory(path)
    mne.export.export_raw(os.path.join(path, filename), signal, fmt=format, overwrite=overwrite)


def save_epoch(epochs, path, filename):
    """
    Save Epochs object to a file.
    
    Parameters:
        epochs (Epochs): MNE Epochs object.
        path (str): Directory to save the file.
        filename (str): Name of the file.
    """
    create_directory(path)
    epochs.save(os.path.join(path, filename), overwrite=True)


def save_ajdc_parameters(ajdc, blink, saccade, path, filename):
    """
    Save AJDC parameters to a file.
    
    Parameters:
        ajdc (AJDC): AJDC object.
        blink (list): Blink components.
        saccade (list): Saccade components.
        path (str): Directory to save the file.
        filename (str): Name of the file.
    """

    create_directory(path)
    np.savez(os.path.join(path, filename), 
             n_channel=ajdc.n_channels_, 
             sfreq=ajdc.freqs_, 
             fmax=ajdc.fmax, 
             fmin=ajdc.fmin, 
             n_source=ajdc.n_sources_, 
             overlap=ajdc.overlap, 
             demixage=ajdc.forward_filters_, 
             mixage=ajdc.backward_filters_,
             blinks_components=blink, 
             saccades_components=saccade)
    
    
def save_ica_parameters(ica, path, filename):
    """
    Save ICA parameters to a file.
    
    Parameters:
        ica (ICA): ICA object.
        path (str): Directory to save the file.
        filename (str): Name of the file.
    """
    create_directory(path)
    ica.save(os.path.join(path, filename), overwrite=True)
    
    
def save_ica_bad_components(blinks_components, saccades_components, path, filename):
    """
    Save bad ICA components for blinks and saccades.
    
    Parameters:
        blinks_components (list): Blink components.
        saccades_components (list): Saccade components.
        path (str): Directory to save the files.
        filename (str): Base name of the files.
    """
    artefacts = [('BLINKS', blinks_components), ('SACCADES', saccades_components)]
    for artefact_name, components in artefacts:
        create_directory(path + f"/_{artefact_name}_IC_")
        np.save(os.path.join(path + f"/_{artefact_name}_IC_", filename + f"{artefact_name}_IC_"), components)
    
    
def save_numpy_data(matrix, path, filename):
    """
    Save a NumPy array to a file.
    
    Parameters:
        matrix (array): NumPy array to save.
        path (str): Directory to save the file.
        filename (str): Name of the file.
    """
    
    create_directory(path)
    np.save(os.path.join(path, filename), matrix)
    
    
def save_mne_annotations(annotations, path, filename):
    """
    Save MNE annotations to a file.
    
    Parameters:
        annotations (Annotations): MNE Annotations object.
        path (str): Directory to save the file.
        filename (str): Name of the file.
    """
    
    create_directory(path)
    annotations.save(os.path.join(path, filename), overwrite = True)
    
    
def save_evoked_potential_data(evoked_potential, path, filename):
    """
    Save evoked potential data to a file.
    
    Parameters:
        evoked_potential (Evoked): MNE Evoked object.
        path (str): Directory to save the file.
        filename (str): Name of the file.
    """
    create_directory(path)
    evoked_potential.save(os.path.join(path, filename), overwrite = True)
    
    
def save_mne_reports(report, path, filename):
    """
    Save an MNE report to a file.
    
    Parameters:
        report (Report): MNE Report object.
        path (str): Directory to save the file.
        filename (str): Name of the file.
    """
    create_directory(path)
    report.save(os.path.join(path, filename), open_browser=False, overwrite=True)
    
    
def save_tfr(tfr_im, path, filename):
    """
    Save a time-frequency representation to a file.
    
    Parameters:
        tfr_im (TFR): MNE TFR object.
        path (str): Directory to save the file.
        filename (str): Name of the file.
    """
    create_directory(path)
    tfr_im.save(os.path.join(path, filename), overwrite=True)


