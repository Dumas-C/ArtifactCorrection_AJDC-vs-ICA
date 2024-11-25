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
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from matplotlib.patches import Rectangle, ConnectionPatch
from matplotlib.colorbar import make_axes

# Main
# -------

# TODO : update the base_path !
base_path = "C:/Users/cassandra.dumas/OneDrive - ICM/Documents/PHD/Data/ETUDE_BETAPARK"

# Define the list of subjects to process
sub_list = [f'sub-S{"00" if s < 10 else "0"}{s}' for s in range(2, 25) if f'sub-S{"00" if s < 10 else "0"}{s}' not in ['sub-S009', 'sub-S010']]

# Define the conditions to compare
conditions = ['RAW', 'AJDC', 'ICA']
MI_TFR = {'RAW' : [],
           'AJDC' : [],
           'ICA' : []}

for corr in conditions:
    MI = [] # List to store the TFR of each subject
    for sub in sub_list:
        if corr == "AJDC":
            os.chdir(f"{base_path}/_TFR_/_MOTOR_IMAGERY_/_EPOCHS_/_AJDC_/_BAND_1_80_/{sub}")
        else:  
             os.chdir(f"{base_path}/_TFR_/_MOTOR_IMAGERY_/_EPOCHS_/_{corr}_/{sub}")
        MI_RAW = mne.read_epochs(f'{sub}-epo.fif', preload=True)
        MI_RAW.drop_channels(['FT9', 'TP9'], on_missing='ignore')
        
        # Compute TFR using Morlet wavelet
        TFR = MI_RAW.compute_tfr("morlet", freqs=np.arange(0.5, 45, 0.5), n_cycles=np.arange(0.5, 45, 0.5)/2, n_jobs=10, average=True)
        MI.append(TFR.apply_baseline(baseline=(-3, -1), mode="logratio"))
    
    # Compute the global average of the TFR
    power_data = np.stack([tfr.data for tfr in MI], axis=0)
    mean_power_data = np.mean(power_data, axis=0)
    
    # Create an MNE AverageTFRArray object
    mean_tfr = mne.time_frequency.AverageTFRArray(
        info=MI[0].info,
        data=mean_power_data,
        times=MI[0].times,
        freqs=MI[0].freqs,
        nave=len(MI),  
        method=MI[0].method
    )
    
    MI_TFR[corr] = mean_tfr

# Electrode montage
ten_twenty_montage = mne.channels.make_standard_montage('easycap-M1')
MI_RAW.set_montage(ten_twenty_montage)

# Separate electrodes of interest from others
channels = ['FC1', 'FC5', 'C3', 'CP1', 'CP5'] # Electrodes of interest
all_channels = MI_RAW.info['ch_names']
channels_excluded = [ch for ch in all_channels if ch not in channels]
ch_group = [channels, channels_excluded]

# Initialize the figure
fig, axes = plt.subplots(1, 4, figsize=(16, 6), gridspec_kw={'width_ratios': [1.5, 3, 3, 3]}, constrained_layout=True)  

# Visualize sensors on the topographic plot
sensors_specific = MI_RAW.copy().pick(channels)  
mne.viz.plot_sensors(MI_RAW.info, axes=axes[0], show_names=False, pointsize=18, show=True)

# Retrieve positions of electrodes of interest and others
sensor_points = axes[0].collections[0]
positions_all = sensor_points.get_offsets()
positions_excluded = [positions_all[all_channels.index(ch)] for ch in channels_excluded]

# Add legend text for frequencies
axes[0].text(0.15, -0.08, 'Frequency (Hz)', fontsize=14, color='black', rotation='vertical')

# Modify electrode colors to differentiate electrodes of interest
colors = []
for pos in positions_all:
    if any(np.all(pos == excluded_pos) for excluded_pos in positions_excluded):
        colors.append([0.8, 0.8, 0.8, 1])  # Gris clair pour les électrodes d'intérêt
    else:
        colors.append(sensor_points.get_facecolors()[0])  # Couleur par défaut (noir) pour les autres
sensor_points.set_facecolors(colors)
sensor_points.set_edgecolors(colors) 

# Define positions for TFR plots
x_offsets = [-0.45, -0.95, -0.7, -0.45, -0.95]
y_offsets = [-0.4, -0.4, -0.725, -1.05, -1.05]

# Loop through conditions to display the averaged TFR
name_condition = ["RAW", "AJDC", "ICA"]
for i, condition in enumerate([MI_TFR['RAW'], MI_TFR['AJDC'], MI_TFR['ICA']]):
    ax_tfr = axes[i + 1]  # Axis for the current condition
    ax_tfr.set_title(name_condition[i], fontsize=10)
    ax_tfr.set_yticks([])
    ax_tfr.set_xticks([])
    
    # Dashed borders
    ax_tfr.spines['top'].set_linestyle('--')
    ax_tfr.spines['right'].set_linestyle('--')
    ax_tfr.spines['left'].set_linestyle('--')
    ax_tfr.spines['bottom'].set_linestyle('--')
    
    for j, channel in enumerate(channels):
        # Extract TFR data for the electrode of interest
        tfr_channel = condition.copy().pick([channel])
        data = tfr_channel.data[0]
        times = tfr_channel.times
        freqs = tfr_channel.freqs
        
        # Create an inset axis for each TFR inserted into the main axis
        inset = inset_axes(ax_tfr, width="14%", height="10%", loc='center', 
                            bbox_to_anchor=(x_offsets[j], y_offsets[j], 2.45, 2.45), bbox_transform=ax_tfr.transAxes)
        
        im = inset.imshow(data, aspect='auto', origin='lower', 
                          extent=[times[0], times[-1], freqs[0], freqs[-1]], 
                          vmin=-0.50, vmax=0.50, cmap='RdBu_r')
        
        tfr_channel.plot([0], axes=inset, vlim=(-0.50,0.50), colorbar=False, show=False)
        
        # Add dashed lines to delimit the moment of interest on each TFR
        inset.axvline(x=0, color='black', linestyle='--', linewidth=1)
        inset.axvline(x=25, color='black', linestyle='--', linewidth=1)
        
        # Set titles and labels for each TFR axis
        inset.set_title(channel, fontsize=9)
        inset.set_ylabel('', fontsize=9)
        inset.set_xlabel('', fontsize=9)
        inset.set_yticks([10, 20, 30, 40], labels=['10', '20', '30', '40'], fontsize=9)
        inset.set_xticks([0, 25], labels=['0', '25'], fontsize=9)
        
        if name_condition[i] == "AJDC":
            ax_tfr.text(0.4, -0.06, 'Time (s)', fontsize=14, color='black')

# Add a colorbar on the far-right side of the figure using the extracted image
cax, _ = make_axes(axes[-1], location='right', fraction=0.05, pad=0.05)
fig.colorbar(im, cax=cax)
fig.axes[19].set_yticks([-0.5, -0.25, 0, 0.25, 0.5])
fig.axes[19].set_yticklabels(['- 0.5', '- 0.25', '0', '0.25', '0.5'], fontsize=12)
fig.axes[19].set_ylabel('ERD/ERS (%)', fontsize=14)


# Add a rectangle to delimit the electrodes
rect_x = -0.07
rect_y = -0.03
rect_width = 0.055
rect_height = 0.06

rect = Rectangle((rect_x, rect_y), rect_width, rect_height,
                  linewidth=1, edgecolor='black', facecolor='none')
axes[0].add_patch(rect)

# Add lines between the rectangle and the TFR axes for zoom effect
xyA = (0.435, 0.602)  
xyB = (0, 1) 
con = ConnectionPatch(xyA=xyA, xyB=xyB, coordsA='axes fraction', coordsB='axes fraction',
                      axesA=axes[0], axesB=axes[1], color='black')
axes[0].add_artist(con)

xyA = (0.435, 0.336)  
xyB = (0, 0) 
con = ConnectionPatch(xyA=xyA, xyB=xyB, coordsA='axes fraction', coordsB='axes fraction',
                      axesA=axes[0], axesB=axes[1], color='black')
axes[0].add_artist(con)
        
# Save the figure
output_path = f"{base_path}/_BIOSIGNALS_FIGURES_"
os.makedirs(output_path, exist_ok=True)
fig.savefig(f'{output_path}/TFR.jpeg', dpi=600, bbox_inches='tight')
