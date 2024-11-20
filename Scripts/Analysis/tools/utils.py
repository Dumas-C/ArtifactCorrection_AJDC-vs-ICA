# -*- coding: utf-8 -*-
"""
Copyright (c) 2024 Paris Brain Institute. All rights reserved.

Created on June 2024

@author: Cassandra Dumas

"""

# Modules
# -------
import os
import re
import json


# Functions
# ---------
def load_paths(file_path):
    """

    Parameters
    ----------
    file_path : str
        Path to the file containing the written paths for analysis.

    Returns
    -------
    dict
        A dictionary containing paths useful for analysis.

    """
    with open(file_path, 'r') as openfile:
        return json.load(openfile)


def setup_betapark():
    """

    Returns
    -------
    sub_list : list
        List of subjects.
    conditions : list
        List of different conditions for analysis.

    """
    sub_list = ["sub-Pilote2"] + [f'sub-S{"00" if s < 10 else "0"}{s}' for s in range(1, 25)]
    conditions = ["_HAND_OBSERVATION_", "_CLEAN_"]
    return sub_list, conditions


def create_directory(path):
    """
    

    Parameters
    ----------
    path : str
        Path to create if not existing.

    Returns
    -------
    None.

    """
    if not os.path.exists(path):
        os.makedirs(path)


def extract_number(element):
    """
    

    Parameters
    ----------
    element : str
        Subject to extract number.

    Returns
    -------
    int
        Number of the subject.

    """
    chiffres = re.findall(r'\d+', element)
    
    if element.startswith('sub-Pilote'):
        return 0
    elif chiffres:
        return int(chiffres[0])
    else:
        return None
    
    
def get_channels():
    electrodes = ['Fp1', 'Fp2', 
                            'F7', 'F3', 'Fz', 'F4', 'F8', 
                            'FT9', 'FC5', 'FC1', 'FC2', 'FC6', 'FT10',
                            'T7', 'C3', 'Cz', 'C4', 'T8',
                            'TP9', 'CP5', 'CP1', 'CP2', 'CP6', 'TP10',
                            'P7', 'P3', 'Pz', 'P4', 'P8',
                            'O1', 'Oz', 'O2']
    
    return electrodes


def get_lobes_channels():
    lobes = {
        "Frontal": ['Fp1', 'Fp2', 'AF7', 'AF3', 'AFz', 'AF4', 'AF8', 'F7', 'F5', 'F3', 'F1', 'Fz', 'F2', 'F4', 'F6', 'F8'],
        "Temporal": ['FT9', 'FT7', 'FT8', 'FT10', 'T7', 'T8', 'TP9', 'TP7', 'TP10', 'TP8'],
        "Central": ['FC5', 'FC3', 'FC1', 'FCz', 'FC2', 'FC4', 'FC6', 'C5', 'C3', 'C1', 'Cz', 'C2', 'C4', 'C6'],
        "Parietal": ['CP5', 'CP3', 'CP1', 'CPz', 'CP2', 'CP4', 'CP6', 'P7', 'P5', 'P3', 'P1', 'Pz', 'P2', 'P4', 'P6', 'P8'],
        "Occipital": ['PO7', 'PO3', 'POz', 'PO4', 'PO8', 'O1', 'Oz', 'O2', 'Iz']
    }
    
    return lobes


def check_common_channels_epochs(list_epochs):
    common_channels = set(list_epochs[0].info['ch_names'])
    for epochs in list_epochs[1:]:
        common_channels.intersection_update(epochs.info['ch_names'])

    return [epochs.pick_channels(list(common_channels)) for epochs in list_epochs]
    
    