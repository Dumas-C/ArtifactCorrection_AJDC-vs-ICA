# -*- coding: utf-8 -*-
"""
Copyright (c) 2024 Paris Brain Institute. All rights reserved.

Created on October 2024

@author: Cassandra Dumas

"""

# Required modules
# -------

import os
import mne
import csv
import json
import math
import numpy as np
import pandas as pd

# Main
# -------

# TODO : update the base_path !
base_path = "C:/Users/cassandra.dumas/OneDrive - ICM/Documents/PHD/Data/ETUDE_BETAPARK"
file_dir = os.path.dirname(os.path.abspath(__file__))

# Define the list of subjects to process
sub_list = [f'sub-S{"00" if s < 10 else "0"}{s}' for s in range(2, 25) if f'sub-S{"00" if s < 10 else "0"}{s}' not in ['sub-S009', 'sub-S010']]

# --------------
# Evoked Potential Conversion
# --------------

# Initialize arrays to store Evoked Potential values
pe_RAW = np.zeros((21, 30, 1001))
pe_AJDC = np.zeros((21, 30, 1001))
pe_ICA = np.zeros((21, 30, 1001))

for sub in sub_list:
    index = sub_list.index(sub)

    # Extract RAW Evoked Potential
    epochs_RAW = mne.read_evokeds(f"{base_path}/_PE_/_PE_/_RAW_/_BLINKS_/{sub}/_GLOBAL_/Evoked_Potential_{sub}_ave.fif")[0].drop_channels(['FT9', 'TP9'], on_missing='ignore')
    pe_RAW[index] = epochs_RAW.data

    # Extract AJDC Evoked Potential
    epochs_AJDC = mne.read_evokeds(f"{base_path}/_PE_/_PE_/_AJDC_/_BAND_1_80_/_BLINKS_/{sub}/_GLOBAL_/Evoked_Potential_{sub}_ave.fif")[0].drop_channels(['FT9', 'TP9'], on_missing='ignore')
    pe_AJDC[index] = epochs_AJDC.data

    # Extract ICA Evoked Potential
    epochs_ICA = mne.read_evokeds(f"{base_path}/_PE_/_PE_/_ICA_/_BLINKS_/{sub}/_GLOBAL_/Evoked_Potential_{sub}_ave.fif")[0].drop_channels(['FT9', 'TP9'], on_missing='ignore')
    pe_ICA[index] = epochs_ICA.data

# Extract the average amplitudes at 500ms (blink pick) for the frontal electrodes for each subject
amp_RAW = pe_RAW[:, :7, 500].mean(axis=1) * 10**6 
amp_AJDC = pe_AJDC[:, :7, 500].mean(axis=1) * 10**6
amp_ICA = pe_ICA[:, :7, 500].mean(axis=1) * 10**6

# Save data in a csv file
with open(f"{file_dir}/Statistics/df_EP_amplitudes.csv", "w") as file:
    file.write("Subject,Amplitude_RAW,Amplitude_AJDC,Amplitude_ICA\n")
    for i in range(len(sub_list)):
        file.write(f"{sub_list[i]},{amp_RAW[i]},{amp_AJDC[i]},{amp_ICA[i]}\n")


# --------------
# PSD Conversion
# --------------

# Initialize arrays to store Power Spectral Density (PSD) values
PSD_AJDC = np.zeros((21, 30, 80)) # Array for PSD values from AJDC (21 subjects, 30 electrodes, 80 frequencies)
PSD_ICA = np.zeros((21, 30, 80)) # Array for PSD values from ICA (same dimensions)

for sub in sub_list:
    os.chdir(f"{base_path}/_PE_/_EPOCHS_/_AJDC_/_BAND_1_80_/_BLINKS_/{sub}/_GLOBAL_")
    epochs_AJDC = mne.read_epochs(f"BLINKS_{sub}-epo.fif", preload=True).drop_channels(['FT9', 'TP9'], on_missing='ignore')
    
    # Compute PSD using multitaper method, average across epochs, and store in the array
    PSD_AJDC[sub_list.index(sub)] = epochs_AJDC.compute_psd(method='multitaper', fmin=0.9, fmax=80).average(method='mean').get_data()
    
    os.chdir(f"{base_path}/_PE_/_EPOCHS_/_ICA_/_BLINKS_/{sub}/_GLOBAL_")
    epochs_ICA = mne.read_epochs(f"BLINKS_{sub}-epo.fif", preload=True).drop_channels(['FT9', 'TP9'], on_missing='ignore')
    
    # Compute PSD using multitaper method, average across epochs, and store in the array
    PSD_ICA[sub_list.index(sub)] = epochs_ICA.compute_psd(method='multitaper', fmin=0.9, fmax=80).average(method='mean').get_data()

# Convert the PSD arrays into DataFrames for easier analysis and storage

# Define ranges for subjects, electrodes, and frequencies
sujets = np.arange(1, 22)  # 21 subjects
electrodes = np.arange(1, 31)  # 30 electrodes
frequences = np.arange(1, 81)  # 80 frequency bands

# Create DataFrame for AJDC PSD values
df_AJDC = pd.DataFrame(
    [(sujet, electrode, frequence, PSD_AJDC[sujet-1, electrode-1, frequence-1])
     for sujet in sujets
     for electrode in electrodes
     for frequence in frequences],
    columns=['Subject', 'Electrode', 'Frequency', 'PSD']
)

# Create DataFrame for ICA PSD values
df_ICA = pd.DataFrame(
    [(sujet, electrode, frequence, PSD_ICA[sujet-1, electrode-1, frequence-1])
     for sujet in sujets
     for electrode in electrodes
     for frequence in frequences],
    columns=['Subject', 'Electrode', 'Frequency', 'PSD']
)

# Save the DataFrames as CSV files in the specified directory
df_AJDC.to_csv(f"{file_dir}/Statistics/df_PSD_AJDC.csv")
df_ICA.to_csv(f"{file_dir}/Statistics/df_PSD_ICA.csv")


# -------------------------
# Time-Frequency Conversion
# -------------------------

# Define the correction conditions to process
conditions = ['RAW', 'AJDC', 'ICA']

# Initialize a dictionary to store TFR data for each condition
MI_ALL_TFR = {'RAW' : [], 'AJDC' : [], 'ICA' : []}

for corr in conditions:
    MI = [] # Temporary list to store TFR data for all subjects in the current condition
    
    for sub in sub_list:
        if corr == "AJDC":
            os.chdir(f"{base_path}/_TFR_/_MOTOR_IMAGERY_/_EPOCHS_/_AJDC_/_BAND_1_80_/{sub}")
        else:  
             os.chdir(f"{base_path}/_TFR_/_MOTOR_IMAGERY_/_EPOCHS_/_{corr}_/{sub}")
        MI_RAW = mne.read_epochs(f'{sub}-epo.fif', preload=True)
        MI_RAW.drop_channels(['FT9', 'TP9'], on_missing='ignore')
        
        # Compute the Time-Frequency Representation (TFR) using Morlet wavelets
        MI.append(MI_RAW.compute_tfr("morlet", freqs=np.arange(0.5, 45, 0.5), n_cycles=np.arange(0.5, 45, 0.5)/2, n_jobs=10, average=True))
    
    MI_ALL_TFR[corr] = MI
    
# Define parameters for the Region of Interest (ROI)
freq_range = (8, 30) 
elecs_of_interest = ['FC1', 'FC5', 'C3', 'CP1', 'CP5']  

# Initialize a DataFrame to store ERD results for each subject and condition
results_df = pd.DataFrame(columns=['Subject', 'RAW', 'AJDC', 'ICA'])

for i, sub in enumerate(sub_list):
    # Temporary dictionary to store ERD values for the subject
    subject_data = {'Subject': sub}
    
    for corr in conditions:
        # Apply baseline correction to the TFR data for the current condition and subject
        tfr_data = MI_ALL_TFR[corr][i].apply_baseline(baseline=(-3, -1), mode="logratio")
        
        # Select data for the ROI (electrodes of interest and frequency range)
        data_roi = tfr_data.copy().pick(elecs_of_interest).crop(fmin=freq_range[0], fmax=freq_range[1])
        
        # Compute the mean power within the ROI (averaged across electrodes, frequencies, and time)
        mean_alpha_erd = np.mean(data_roi.data[:, :, 5000:30000])
        
        # Add the mean ERD value for the current condition
        subject_data[corr] = mean_alpha_erd
    
    # Append the subject's data to the results DataFrame
    results_df = results_df.append(subject_data, ignore_index=True)

# Save the results DataFrame to a CSV file
results_df.to_csv(f"{file_dir}/Statistics/df_MITF.csv")


# -------------------------
# Neurofeedback Performance
# -------------------------

# Load neurofeedback session data from a JSON file
with open('C:/Users/cassandra.dumas/OneDrive - ICM/Documents/PHD/Dev/Online_Denoising/Tools/BetaPark.json', 'r') as openfile:
    nf_session= json.load(openfile)['NF_SESSION']

# Update session labels: remove "MainTactile" and rename "MainIllusion" to "MainVibration".
for key, sessions in nf_session.items():
    if "MainTactile" in sessions:
        sessions.remove("MainTactile")
    nf_session[key] = ['MainVibration' if session == 'MainIllusion' else session for session in sessions]

# Define the correction methods to compare
corrections = ['RAW', 'AJDC']

# Initialize dictionaries to store performance data and thresholds
nf_perf = {'RAW' : [], 'AJDC' : []}
seuil_global = {'RAW' : [], 'AJDC' : []}

# Loop through correction methods and subjects to extract thresholds
for corr in corrections:
    for sub in sub_list:
        os.chdir(f"{base_path}/_NF_PERF_/_PERF_/{sub}/_{corr}_")
       
        with open("values_threshold.csv", newline='') as csvthreshold:
            reader = csv.reader(csvthreshold, delimiter=",")
            reader.__next__() # Skip header
            for row in reader:
                seuil = float(row[5]) # Extract threshold value
                
        seuil_global[corr].append(seuil)

# Calculate the definitive threshold as the mean between RAW and AJDC thresholds
seuil_definitif = np.mean([seuil_global['RAW'], seuil_global['AJDC']], axis=0)

# Initialize dictionary for first and last performance values
first_last_perf = {"RAW_FIRST" : np.zeros(21), 
                   "RAW_LAST" : np.zeros(21),
                   "AJDC_FIRST" : np.zeros(21),
                   "AJDC_LAST" : np.zeros(21)}

# Loop through corrections and subjects to calculate performance metrics
for corr in corrections:
    for sub in sub_list:
        os.chdir(f"{base_path}/_NF_PERF_/_PERF_/{sub}/_{corr}_")
        index=sub_list.index(sub)
        dict_key = list(nf_session.keys())[index]
        
        run_perf = []        
        for file in filter(lambda f: "save" in f, os.listdir()):
            raw_moy = []
            with open(file, newline='') as csvfile:
                reader = csv.reader(csvfile, delimiter=",")
                reader.__next__() # Skip header
                
                column_moy = []
                for row in reader:
                    raw_moy.append(float(row[1]))
                    column_moy.append(float(row[1]))
                
                # Calculate performance for the first session
                if nf_session[dict_key][0] in file and first_last_perf[f'{corr}_FIRST'][index] == 0.0:
                    ratio_first = np.array(column_moy)/seuil_definitif[index]
                    first_last_perf[f'{corr}_FIRST'][index] = -math.log10(np.median(ratio_first))
                
                # Calculate performance for the last session
                elif nf_session[dict_key][-1] in file and first_last_perf[f'{corr}_LAST'][index] == 0.0:
                    ratio_last = np.array(column_moy)/seuil_definitif[index]
                    first_last_perf[f'{corr}_LAST'][index] = -math.log10(np.median(ratio_last))
            
            # Calculate median performance for the current run
            ratio = np.array(raw_moy)/seuil_definitif[index]
            median_ratio = np.median(ratio)
            perf = -math.log10(median_ratio)
            run_perf.append(perf)
        
        # Store mean performance across runs
        mean_perf = np.mean(np.array(run_perf))
        nf_perf[corr].append(mean_perf)
        
# Save the results DataFrame to a CSV file
df = pd.DataFrame.from_dict(nf_perf)
df.to_csv(f"{file_dir}/Statistics/df_NFperf.csv")


# ---------------------
# Signal-to-Noise Ratio
# ---------------------

target_suffixes = ['5-2-a', '5-2-b', '6-2-a', '6-2-b', '7-2-a', '7-2-b', '8-2-a', '8-2-b']

# Configuration
target_suffixes = ['5-2-a', '5-2-b', '6-2-a', '6-2-b', '7-2-a', '7-2-b', '8-2-a', '8-2-b']

# Mapping of electrodes to scalp regions
region_map = {
    'Fp1': 'Frontal', 'Fp2': 'Frontal', 'F7': 'Frontal', 'F3': 'Frontal', 
    'Fz': 'Frontal', 'F4': 'Frontal', 'F8': 'Frontal',
    'FT10': 'Central', 'T7': 'Central', 'T8': 'Central', 'TP10': 'Central',
    'FC5': 'Central', 'FC1': 'Central', 'FC2': 'Central', 'FC6': 'Central', 
    'C3': 'Central', 'Cz': 'Central', 'C4': 'Central',
    'CP5': 'Central', 'CP1': 'Central', 'CP2': 'Central', 'CP6': 'Central', 
    'P7': 'Posterior', 'P3': 'Posterior', 'Pz': 'Posterior', 'P4': 'Posterior', 
    'P8': 'Posterior', 'O1': 'Posterior', 'Oz': 'Posterior', 'O2': 'Posterior'
}

# Mapping of electrode indices to their names
electrode_name_map = {
    1: 'Fp1', 2: 'Fp2', 3: 'F7', 4: 'F3', 5: 'Fz', 6: 'F4', 7: 'F8',
    8: 'FT10', 9: 'T7', 10: 'T8', 11: 'TP10',
    12: 'FC5', 13: 'FC1', 14: 'FC2', 15: 'FC6', 16: 'C3', 17: 'Cz', 18: 'C4',
    19: 'CP5', 20: 'CP1', 21: 'CP2', 22: 'CP6', 23: 'P7', 24: 'P3', 25: 'Pz', 
    26: 'P4', 27: 'P8', 28: 'O1', 29: 'Oz', 30: 'O2'
}

# Initialize a list to store the data
data = []

# Iterate over all subjects and load their data
for sub in sub_list:
    # Define the subject's directory path
    subject_path = os.path.join(base_path, "_SNR_", "_SNR_SCORES_", sub)
    
    # Check if the directory exists
    if not os.path.isdir(subject_path):
        print(f"Directory not found: {subject_path}")
        continue

    # Load the SNR scores file for AJDC
    try:
        snr_electrode = np.load(os.path.join(subject_path, "snr_electrode_ajdc.npy"), allow_pickle=True).flatten()[0]
    except FileNotFoundError:
        print(f"File not found: {subject_path}/snr_electrode_ajdc.npy")
        continue

    # Filter keys in `snr_electrode` based on target_suffixes
    filtered_elements = sorted([key for key in snr_electrode.keys() if any(suffix in key for suffix in target_suffixes)])
    
    # Reorder and extract data
    for idx, key in enumerate(filtered_elements):
        # Extract SNR values for each electrode in this run
        snr_values = snr_electrode[key]
        
        # Create a relative time position for the run
        time_position = f"T{idx + 1}"  # Creates labels T1, T2, ..., T6 for each run in order

        # Add each electrode with its SNR to the data list
        for electrode_idx, snr_value in enumerate(snr_values):
            data.append({
                'Subject': sub,
                'RelativeTime': idx + 1,  # T1 is treated as 1, T2 as 2, etc.
                'Electrode': electrode_idx + 1,  # Electrode number (1-indexed)
                'SNR': snr_value
            })

# Convert the data list to a DataFrame
df = pd.DataFrame(data)

# Process the DataFrame columns
df['Subject'] = df['Subject'].astype('category')
df['RelativeTime'] = df['RelativeTime'].astype(int)
df['SNR'] = -df['SNR']  # Transform SNR to -SNR for a positive interpretation
df['Electrode'] = df['Electrode'].astype(int)  # Convert to integer

# Add electrode names and regions
df['Electrode_Name'] = df['Electrode'].map(electrode_name_map)
df['Region'] = df['Electrode_Name'].map(region_map)

# Save the final DataFrame to a CSV file
output_file = os.path.join(file_dir, "Statistics", "df_SNR.csv")
os.makedirs(os.path.dirname(output_file), exist_ok=True)  # Create the directory if it does not exist
df.to_csv(output_file, index=False)
print(f"Data saved to {output_file}")