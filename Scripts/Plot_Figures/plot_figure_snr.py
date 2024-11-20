# -*- coding: utf-8 -*-
"""
Copyright (c) 2024 Paris Brain Institute. All rights reserved.

Created on October 2024

@author: Cassandra Dumas

"""

# Required modules
# ----------------
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.lines as mlines
import os

from mpl_toolkits.axes_grid1.inset_locator import zoomed_inset_axes
from mpl_toolkits.axes_grid1.inset_locator import mark_inset

# Function
# --------
def darken_color(color, factor=0.7):
    # Convert the color to RGB format
    rgb = mcolors.to_rgb(color)
    # Darken the color by reducing each component
    dark_rgb = [max(c * factor, 0) for c in rgb]
    return mcolors.to_hex(dark_rgb)

# Main
# -------

# TODO: update the base_path !
base_path = "C:/Users/cassandra.dumas/OneDrive - ICM/Documents/PHD/Data/ETUDE_BETAPARK"

# Define the list of subjects to process
sub_list = [f'sub-S{"00" if s < 10 else "0"}{s}' for s in range(2, 25) if f'sub-S{"00" if s < 10 else "0"}{s}' not in ['sub-S009', 'sub-S010']]

# Define the target runs of interest
target_suffixes = ['5-2-a', '5-2-b', '6-2-a', '6-2-b', '7-2-a', '7-2-b', '8-2-a', '8-2-b']

first = [] # List to store SNR of the first run
last = [] # List to store SNR of the last run
regions = []  # List to store the corresponding regions

# Mapping of electrodes to scalp regions
region_map = {
    'Fp1': 'Frontal', 'Fp2': 'Frontal', 'F7': 'Frontal', 'F3': 'Frontal', 
    'Fz': 'Frontal', 'F4': 'Frontal', 'F8': 'Frontal',
    
    'FT10': 'Central', 'T7': 'Central', 'T8': 'Central', 'TP10': 'Central',
    'FC5': 'Central', 'FC1': 'Central', 'FC2': 'Central', 'FC6': 'Central', 
    'C3': 'Central', 'Cz': 'Central', 'C4': 'Central',
    'CP5': 'Central', 'CP1': 'Central', 'CP2': 'Central', 'CP6': 'Central', 
    
    'P7': 'Posterior', 'P3': 'Posterior', 'Pz': 'Posterior', 'P4': 'Posterior', 'P8': 'Posterior',
    'O1': 'Posterior', 'Oz': 'Posterior', 'O2': 'Posterior'
}

# Color palette for each region
colors = {'Frontal': 'red', 'Central': 'green', 'Posterior': 'blue'}
regions = [region_map.get(electrode, 'Other') for electrode in region_map.keys()]

# Retrieve SNR across subjects for the first and last runs
for sub in sub_list:
    os.chdir(f"{base_path}/_SNR_/_SNR_SCORES_/{sub}")
    snr_electrode = np.load("snr_electrode_ajdc.npy", allow_pickle=True).flatten()[0]
    
    filtered_elements = sorted([el for el in snr_electrode.keys() if any(suffix in el for suffix in target_suffixes)])
    
    first_snr = snr_electrode[filtered_elements[0]]
    last_snr = snr_electrode[filtered_elements[-1]]
    
    first.append(-first_snr)
    last.append(-last_snr)
    
# Convert to numpy arrays
data_first = np.array(first)
data_last = np.array(last)

# Compute the mean
mean_values_first = np.mean(data_first, axis=0)
mean_values_last = np.mean(data_last, axis=0)

# Calculate the delta for each subject and each electrode between first and last
delta = data_last - data_first
std_delta = np.std(delta, axis=0)

# Parameters for circle sizes based on variability (standard deviation)
small_circle_size = 50   
medium_circle_size = 150 
large_circle_size = 250  

# Standard deviation thresholds to classify variability
std_threshold_low = np.percentile(std_delta, 33) 
std_threshold_high = np.percentile(std_delta, 66) 

# Create figure and axis
fig, ax = plt.subplots(figsize=(8, 6))
axins = zoomed_inset_axes(ax, 2, loc='lower right', borderpad=2.5) 

# Create separate "handles" lists for legend of colors and sizes
region_handles = []
size_handles = []

for i, electrode in enumerate(region_map.keys()):
    region = region_map[electrode]
    color = colors.get(region, 'black')
    
    # Use the standard deviation of delta to define the circle size
    variability = std_delta[i]
    if variability < std_threshold_low:
        size = small_circle_size
        size_label = "SD < 33%"  
    elif variability < std_threshold_high:
        size = medium_circle_size
        size_label = "33% < SD < 66%"  
    else:
        size = large_circle_size
        size_label = "SD > 66%"  
    
    # Plot points with circle size based on delta standard deviation
    ax.scatter(mean_values_first[i], mean_values_last[i], color=color, edgecolor=None, linewidth=0, s=size, alpha=0.7)
    axins.scatter(mean_values_first[i], mean_values_last[i], color=color, edgecolor=None, linewidth=0, s=size, alpha=0.7)
    
    # Plot a small dot at the center of the circle for the mean, with a darker color
    darker_color = darken_color(color)  # Darken the circle color
    ax.scatter(mean_values_first[i], mean_values_last[i], color=darker_color, s=5, edgecolor='none', alpha=0.9)
    axins.scatter(mean_values_first[i], mean_values_last[i], color=darker_color, s=5, edgecolor='none', alpha=0.9)
    
    # Define coordinates for displaying electrode labels
    if electrode == "F8":
        offset = (-5, -25)
        offset_zoom = (-10, -20)
    elif electrode == "FC5":
        offset = (15, -25)
        offset_zoom = (35, -17)
    elif electrode == "F3":
        offset = offset_zoom = (10, -20)
    else:
        offset = offset_zoom = None
    
    # Apply annotation with a line if the electrode is F8, FC5, or F3
    if offset:
        ax.annotate(
            electrode, 
            (mean_values_first[i], mean_values_last[i]), 
            textcoords="offset points", 
            xytext=offset,  # Specific offset for each electrode
            ha='center', 
            arrowprops=dict(arrowstyle="-", color='black', lw=0.5)  # Arrow connecting the circle to the label
        )
        
        axins.annotate(
            electrode, 
            (mean_values_first[i], mean_values_last[i]), 
            textcoords="offset points", 
            xytext=offset_zoom,  # Specific offset for each electrode
            ha='center', 
            arrowprops=dict(arrowstyle="-", color='black', lw=0.5)  # Arrow connecting the circle to the label
        )
        
    # Add a legend for the color 
    if region not in [handle.get_label() for handle in region_handles]:
        region_handles.append(mlines.Line2D([], [], marker='o', color='w', markerfacecolor=color, markersize=10, label=region))

    # Add an entry in the legend for circle size (variability)
    if size_label not in [handle.get_label() for handle in size_handles]:
        size_handles.append(ax.scatter([], [], color='grey', s=size, label=size_label, edgecolor='none', alpha=0.7))  # Point invisible juste pour la légende

# y=x reference line
min_val = min(min(mean_values_first), min(mean_values_last))
max_val = max(max(mean_values_first), max(mean_values_last))
ax.plot([min_val, max_val], [min_val, max_val], '--', color='gray')
axins.plot([min_val, max_val], [min_val, max_val], '--', color='gray')

# Axis labels
ax.set_xlabel("SNR First Run", fontsize=14)
ax.set_ylabel("SNR Last Run", fontsize=14)

# Set zoom area
x1, x2, y1, y2 = 16, 21, 14, 19.5
axins.set_xlim(x1, x2)
axins.set_ylim(y1, y2)

# Configure labels and axes of the zoom window
axins.set_xticks([17, 19, 21])
axins.set_yticks([15, 17, 19])
axins.set_xticklabels(["17", "19", "21"], fontsize=8)
axins.set_yticklabels(["15", "17", "19"], fontsize=8)
axins.yaxis.tick_right()

mark_inset(ax, axins, loc1=1, loc2=3, fc="none", ec="0")

# Change the order of the legend
size_handles[0], size_handles[1], size_handles[2] = size_handles[1], size_handles[2], size_handles[0]

# Create the legend in two parts: regions and circle sizes
handles = region_handles + size_handles  
labels = [handle.get_label() for handle in handles]

# Add the legend inside the plot (top left)
ax.legend(fancybox=True, framealpha=1, shadow=True, borderpad=1, handles=handles, title="Regions and Variability",
          labels=labels, loc='upper left', bbox_to_anchor=(0.01, 0.99), fontsize=10, ncol=2)

# Save the figure
output_dir = "{base_path}/_BIOSIGNALS_FIGURES_"
os.makedirs(output_dir, exist_ok=True)
fig.savefig(os.path.join(output_dir, 'SNR_Electrode.jpeg'), dpi=600, bbox_inches='tight')
