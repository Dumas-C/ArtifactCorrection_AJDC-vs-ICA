# -*- coding: utf-8 -*-
"""
Copyright (c) 2024 Paris Brain Institute. All rights reserved.

Created on June 2024

@author: Cassandra Dumas

"""

# Modules
# -------
import mne

from tools.utils import get_channels

# Functions
# ---------
def preparing_data_BetaPark(signal, subject, average_reference=True):
    """
    

    Parameters
    ----------
    signal : mne.io.Raw
        EEG signal to prepare for preprocessing.
    subject : int
        Numerous of the actual subject.

    Returns
    -------
    None.

    """
    print("\nReorder Channels...")
    channels = get_channels()
    
    if average_reference:
        print("\nPreparing the data and adding Fz...")    
        signal.add_reference_channels('Fz')
    else:
        channels.remove('Fz')
        
    signal.reorder_channels(channels)
            
    print("\nRemoving non EEG Channels...")
    signal.drop_channels(['ECG', 'ECG2', 'HEOG', 'VEOG', 'EMG', 'ACC_X', 'ACC_Y', 'ACC_Z'], on_missing='ignore')
    
    if (int(subject) == 6 or (int(subject) == 19)):
        signal.drop_channels(['TP9'], on_missing='ignore')
        
    if (int(subject) == 12) or (int(subject) == 13) or (int(subject) == 14) or (int(subject) == 16) or (int(subject) == 19):
        signal.drop_channels(['FT9'], on_missing='ignore')     
        
                
def preprocessing(signal, notch = False, high_pass_filter = None, low_pass_filter = None, average_reference=True):
    """
    

    Parameters
    ----------
    signal : mne.io.Raw
        EEG signal to preprocess.
    high_pass_filter : int, optional
        Frequency to which you want to apply a high-pass filter. The default is None.
    low_pass_filter : int, optional
        Frequency to which you want to apply a low-pass filter. The default is None.

    Returns
    -------
    None.

    """
    if average_reference:
        print("\nAverage Referencing...")
        signal.set_eeg_reference(ref_channels='average')
    
    if notch :
        print("\n50Hz Notch Filter")
        signal.notch_filter([50])

    print("\nHigh-Pass and/or Low-Pass Filter")
    signal.filter(l_freq = high_pass_filter, h_freq= low_pass_filter)
    
    print("\nDefine EEG montage")
    ten_twenty_montage = mne.channels.make_standard_montage('easycap-M1')
    signal.set_montage(ten_twenty_montage)
            
        
def crop_calibration_signal_BetaPark(signal, condition):
    """
    

    Parameters
    ----------
    signal : mne.io.Raw
        EEG Signal you want to crop.
    condition : str
        Condition you are, in order to crop the signal correctly.

    Returns
    -------
    None.

    """          
    if condition == "_HAND_OBSERVATION_":
        for annot in signal.annotations:
            if ' 16' in annot['description']:
                tmin = annot['onset'] + 5.0
                tmax = tmin + 20.0
                
        signal.crop(tmin, tmax)
        
    elif condition == "_CLEAN_":
        signal.plot(block=True)
        
        tmin = float(input("Begin of clean signal : "))
        tmax = float(input("End of clean signal : "))
        
        signal.crop(tmin, tmax)

        
        
        
        
            
            
            
            
            


 

