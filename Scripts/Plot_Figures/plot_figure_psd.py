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
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# Main
# -----

# TODO : update the base_path !
base_path = "C:/Users/cassandra.dumas/OneDrive - ICM/Documents/PHD/Data/ETUDE_BETAPARK"

# Define the list of subjects to process
sub_list = [f'sub-S{"00" if s < 10 else "0"}{s}' for s in range(2, 25) if f'sub-S{"00" if s < 10 else "0"}{s}' not in ['sub-S009', 'sub-S010']]

# Initialize matrices for PSDs
PSD_RAW = np.zeros((21, 30, 80))
PSD_AJDC = np.zeros((21, 30, 80))
PSD_ICA = np.zeros((21, 30, 80))

# Loop to load and compute PSD for each subject
for sub in sub_list:
    index = sub_list.index(sub)

    epochs_RAW = mne.read_epochs(f"{base_path}/_PE_/_EPOCHS_/_RAW_/_BLINKS_/{sub}/_GLOBAL_/BLINKS_{sub}-epo.fif", preload=True).drop_channels(['FT9', 'TP9'], on_missing='ignore')
    PSD_RAW[index] = epochs_RAW.compute_psd(method='multitaper', fmin=0.9, fmax=80).average(method='mean').get_data()
    
    epochs_AJDC = mne.read_epochs(f"{base_path}/_PE_/_EPOCHS_/_AJDC_/_BAND_1_80_/_BLINKS_/{sub}/_GLOBAL_/BLINKS_{sub}-epo.fif", preload=True).drop_channels(['FT9', 'TP9'], on_missing='ignore')
    PSD_AJDC[index] = epochs_AJDC.compute_psd(method='multitaper', fmin=0.9, fmax=80).average(method='mean').get_data()
    
    epochs_ICA = mne.read_epochs(f"{base_path}/_PE_/_EPOCHS_/_ICA_/_BLINKS_/{sub}/_GLOBAL_/BLINKS_{sub}-epo.fif", preload=True).drop_channels(['FT9', 'TP9'], on_missing='ignore')
    PSD_ICA[index] = epochs_ICA.compute_psd(method='multitaper', fmin=0.9, fmax=80).average(method='mean').get_data()

# Compute average PSD for each condition
PSD_mean_RAW = PSD_RAW.mean(axis=0)
PSD_mean_AJDC = PSD_AJDC.mean(axis=0)
PSD_mean_ICA = PSD_ICA.mean(axis=0)

# Configure MNE for average PSDs
freqs = np.arange(1, 81)
MNE_PSD_RAW = mne.time_frequency.SpectrumArray(PSD_mean_RAW, epochs_RAW.info, freqs)
MNE_PSD_AJDC = mne.time_frequency.SpectrumArray(PSD_mean_AJDC, epochs_AJDC.info, freqs)
MNE_PSD_ICA = mne.time_frequency.SpectrumArray(PSD_mean_ICA, epochs_ICA.info, freqs)

# List of electrodes by region
elec_regions = {
    "Frontal": ['Fp1', 'Fp2', 'F7', 'F3', 'Fz', 'F4', 'F8'],
    "Central": ['FC5', 'FC1', 'FC2', 'FC6', 'FT10', 'T7', 'C3', 'Cz', 'C4', 'T8', 'CP5', 'CP1', 'CP2', 'CP6', 'TP10'],
    "Parietal": ['P7', 'P3', 'Pz', 'P4', 'P8', 'O1', 'Oz', 'O2']
}

# Create the figure
fig_blinks_ep, axs_blinks_ep = plt.subplots(nrows=1, ncols=3, figsize=(16, 6.5))
plt.rcParams.update({'axes.labelsize': 15, 'axes.titlesize': 15, 'xtick.labelsize': 15, 'ytick.labelsize': 15, 'legend.fontsize': 15})

# Loop to display each region of electrodes
for i, (region, elec) in enumerate(elec_regions.items()):
    MNE_PSD_RAW.plot(average=True, picks=elec, exclude='bads', axes=axs_blinks_ep[i], color='#1f77b4', xscale='log', show=False)
    MNE_PSD_AJDC.plot(average=True, picks=elec, exclude='bads', axes=axs_blinks_ep[i], color='#ff7f0e', xscale='log', show=False)
    MNE_PSD_ICA.plot(average=True, picks=elec, exclude='bads', axes=axs_blinks_ep[i], color='#2ca02c', xscale='log', show=False)

    # Add legend
    axs_blinks_ep[i].legend(handles=[
        Line2D([0], [0], label='Raw', color='#1f77b4'),
        Line2D([0], [0], label='AJDC', color='#ff7f0e'),
        Line2D([0], [0], label='ICA', color='#2ca02c')
    ])
    
    # Configure axes and scales
    axs_blinks_ep[i].set_xlim(1, 80)
    axs_blinks_ep[i].set_xticks([2, 5, 10, 20, 40, 80])
    axs_blinks_ep[i].set_xticklabels([str(freq) for freq in [2, 5, 10, 20, 40, 80]], fontsize=10)
    axs_blinks_ep[i].set_ylim(10, 60)
    axs_blinks_ep[i].set_yticklabels([str(val) for val in [10, 20, 30, 40, 50, 60]], fontsize=10)
    axs_blinks_ep[i].set_xlabel('Frequency (Hz)', fontsize=15)
    axs_blinks_ep[i].set_ylabel('PSD$\\ \\mathrm{(dB)}$' if i == 0 else "", fontsize=15 )
    axs_blinks_ep[i].set_title("")

    # Display electrodes for each region
    sensors_specific = epochs_RAW.copy().pick(elec)
    ax_sensor = fig_blinks_ep.add_axes([0.235 + i * 0.275, 0.55, 0.15, 0.15])
    mne.viz.plot_sensors(sensors_specific.info, axes=ax_sensor, show=False)

# Save the figure
output_path = "{base_path}/_BIOSIGNALS_FIGURES_"
os.makedirs(output_path, exist_ok=True)
fig_blinks_ep.savefig(f'{output_path}/PSD_PE.jpeg', dpi=600, bbox_inches='tight')
