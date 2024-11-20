# -*- coding: utf-8 -*-
"""
Copyright (c) 2024 Paris Brain Institute. All rights reserved.

Created on November 2024

@author: Cassandra Dumas

"""


# Required modules
# ----------------

import os
import math
import csv
import numpy as np
import json
import matplotlib.pyplot as plt


# Main
# ----

# TODO : update the base_path !
base_path = "C:/Users/cassandra.dumas/OneDrive - ICM/Documents/PHD/Data/ETUDE_BETAPARK"

# Define the list of subjects to process
sub_list = [f'sub-S{"00" if s < 10 else "0"}{s}' for s in range(2, 25) if f'sub-S{"00" if s < 10 else "0"}{s}' not in ['sub-S009', 'sub-S010']]

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


# Figure settings
fig, ax = plt.subplots(figsize=(10, 10))

# Define colors and styles
BG_WHITE = "white"
GREY50 = "#7f7f7f"
BLACK = "black"
GREY_DARK = "#505050"

# Define distinct jitters for each condition
x_jittered_raw = np.random.uniform(-0.08, 0.08, len(nf_perf))  # Jitter pour RAW
x_jittered_ajdc = np.random.uniform(-0.08, 0.08, len(nf_perf)) + 1  # Jitter pour AJDC (décalé à droite)

# Y data for each condition
y_raw = nf_perf['RAW']
y_ajdc = nf_perf['AJDC']

# Configure background
fig.patch.set_edgecolor(BLACK)
fig.patch.set_facecolor(BG_WHITE)
ax.set_facecolor(BG_WHITE)
ax.spines['left'].set_color(BLACK)
ax.spines['bottom'].set_color(BLACK)

# Add reference horizontal lines (adjust as needed)
ax.axhline(0, color=GREY50, linestyle='-', alpha=0.3, lw=2)

# Add violin plots for RAW and AJDC data
violins = ax.violinplot(
    [y_raw, y_ajdc], 
    positions=[0, 1],  # Positions for RAW and AJDC
    widths=0.45,
    bw_method="silverman",
    showmeans=False, 
    showmedians=False,
    showextrema=False
)

# Customize violins (edges and filling)
for pc in violins["bodies"]:
    pc.set_facecolor("none")
    pc.set_edgecolor(BLACK)
    pc.set_linewidth(1.4)
    pc.set_alpha(1)

# Add boxplots at the same positions
medianprops = dict(linewidth=4, color=GREY_DARK, solid_capstyle="butt")
boxprops = dict(linewidth=2, color=GREY_DARK)

ax.boxplot(
    [y_raw, y_ajdc],
    positions=[0, 1], 
    showfliers=False,  # Hide outliers
    showcaps=False,    # Hide caps
    medianprops=medianprops,
    whiskerprops=boxprops,
    boxprops=boxprops
)

# Add jittered points for each condition
for x, y in zip(x_jittered_raw, y_raw):
    ax.scatter(x, y, s=100, color="blue", alpha=0.4)
for x, y in zip(x_jittered_ajdc, y_ajdc):
    ax.scatter(x, y, s=100, color="blue", alpha=0.4)
    
# Connect points with lines
for x1, y1, x2, y2 in zip(x_jittered_raw, y_raw, x_jittered_ajdc, y_ajdc):
    ax.plot([x1, x2], [y1, y2], color="gray", alpha=0.4, lw=1)

# Add titles and labels
ax.set_ylabel("NF Performance", fontsize=20)
ax.set_xticks([0, 1])
ax.set_yticks([-0.8, -0.6, -0.4, -0.2, 0.0, 0.2, 0.4, 0.6, 0.8])
ax.set_yticklabels(["-0.8", "-0.6", "-0.4", "-0.2", "0.0", "0.2", "0.4", "0.6", "0.8"], fontsize=15)
ax.set_xticklabels(['RAW', 'AJDC'], fontsize=20)

ax.set_ylim(-0.9, 0.9)

# Save the plot
output_path = f"{base_path}/_BIOSIGNALS_FIGURES_"
os.makedirs(output_path, exist_ok=True)
fig.savefig('{output_path}/PERF_boxplot.png', dpi=600, bbox_inches='tight')









