# -*- coding: utf-8 -*-
"""
Copyright (c) 2024 Paris Brain Institute. All rights reserved.

Created on October 2024

@author: Cassandra Dumas

"""

# Modules
# -------
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, ConnectionPatch
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import mne
import os


# Main
# -------

# TODO : update the base_path !
base_path = "C:/Users/cassandra.dumas/OneDrive - ICM/Documents/PHD/Data/ETUDE_BETAPARK"
file_paths = [
    f"{base_path}/_PE_/_PE_/_RAW_/_BLINKS_/_GLOBAL_/Evoked_Potential_RAW_ave.fif",
    f"{base_path}/_PE_/_PE_/_AJDC_/_BAND_1_80_/_BLINKS_/_GLOBAL_/Evoked_Potential_AJDC_ave.fif",
    f"{base_path}/_PE_/_PE_/_ICA_/_BLINKS_/_GLOBAL_/Evoked_Potential_ICA_ave.fif"
]
pe_Blinks = [mne.read_evokeds(fp)[0] for fp in file_paths]

# Figure configuration
fig_model, axs_model = plt.subplots(nrows=1, ncols=3, figsize=(16, 4))
ylim = dict(eeg=[-50, 200])
titles = ["RAW", 'AJDC', 'ICA']

# Main loop to plot evoked potentials and add visual elements
for i, (pe, ax) in enumerate(zip(pe_Blinks, axs_model)):
    # Plot the main evoked potential
    pe.plot(ylim=ylim, axes=ax, proj=False, spatial_colors=True, show=False)
    
    # Manage axis labels
    ax.set_xlabel("Time (s)", fontsize=15)
    ax.set_ylabel("µV" if i == 0 else "", fontsize=15)
    ax.tick_params(labelsize=10)
    
    # Remove top and right borders of the figure
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Remove automatic event count text added by MNE
    for text in ax.texts:
        if 'N' in text.get_text():
            text.set_visible(False)
    
    # Add the number of averaged events to the left of the figure
    ax.text(-0.48, 205, 'n$_{ave}$ = 15521', fontsize=10, color='black')

    # Add a zoom rectangle for AJDC and ICA conditions
    if i > 0:
        rect = Rectangle((-0.2, -12), 0.4, 25, linewidth=1, edgecolor='black', facecolor='none')
        ax.add_patch(rect)
        
        xyA = (-0.2, 12.5)  
        xyB = (-0.25, 31) 
        con = ConnectionPatch(xyA=xyA, xyB=xyB, coordsA='data', coordsB='data',
                              axesA=axs_model[i], axesB=axs_model[i], color='black')
        axs_model[i].add_artist(con)
        
        xyA = (0.2, 12.5)  
        xyB = (0.25, 31) 
        con = ConnectionPatch(xyA=xyA, xyB=xyB, coordsA='data', coordsB='data',
                              axesA=axs_model[i], axesB=axs_model[i], color='black')
        ax.add_artist(con)
        
        # Insert zoomed axis into the figure
        ax_zoom = inset_axes(ax, width="25%", height="35%", loc='center', bbox_to_anchor=(-0.5, 0, 2, 1),
                             bbox_transform=ax.transAxes)
        pe.plot(ylim=dict(eeg=[-10, 10]), xlim=(-0.2, 0.2), axes=ax_zoom, show=False)
        
        # Manage labels in the zoomed axis
        ax_zoom.set_title("")
        ax_zoom.set_xticks([-0.1, 0, 0.1])
        ax_zoom.set_xticklabels(["-0.1", "0", "0.1"], fontsize=8)
        ax_zoom.set_yticklabels(["-10", "0", "10"], fontsize=8)
        ax_zoom.set_ylabel("")
        ax_zoom.set_xlabel("")
        
        # Move the topo with electrodes to the background in the zoom
        ax_zoom.set_zorder(9) # Topo is not deleted but moved to the background
        
        # Add a vertical line at t=0s in the zoomed axis
        ax_zoom.axvline(x=0, color='grey', linestyle='dotted', linewidth=1)
        
        # Remove automatic text in the inset
        for text in ax_zoom.texts:
            if 'N' in text.get_text():
                text.set_visible(False)
    
    # Add topomap with colorbar
    inset_x, inset_y = 0.60, 0.75
    width, height = 0.35, 0.35
    ax_topo = ax.inset_axes([inset_x, inset_y, width, height])
    ax_colorbar = ax.inset_axes([inset_x + 0.33, inset_y - 0.03, 0.02, 0.35])
    
    vlim = (-30, 30) if titles[i] == "RAW" else (-15, 15)
    pe.plot_topomap(times=[0.0], axes=[ax_topo, ax_colorbar], show=False, vlim=vlim, colorbar=True)
    cbar = plt.colorbar(ax_topo.collections[0], cax=ax_colorbar)
    cbar.ax.tick_params(labelsize=10)
    ax_topo.set_title("")
    ax_colorbar.set_title("µV", fontsize=10)

    # Add a vertical line at t=0s in the topomap
    xyA = (0, 0)  
    xyB = (0, 150) 
    con = ConnectionPatch(xyA=xyA, xyB=xyB, coordsA='data', coordsB='data',
                          axesA=axs_model[i], axesB=axs_model[i], color='grey')
    axs_model[i].add_artist(con)
    
    xyC = (inset_x + 0.05, inset_y + height/3)
    con = ConnectionPatch(xyA=xyB, xyB=xyC, coordsA='data', coordsB='axes fraction',
                            axesA=axs_model[i], axesB=axs_model[i], color='grey')
    ax.add_artist(con)

    ax.set_title(titles[i], fontsize=15)

# Save the figure
output_path = f"{base_path}/_BIOSIGNALS_FIGURES_"
os.makedirs(output_path, exist_ok=True)
fig_model.savefig(f'{output_path}/ICA_AJDC_PE.jpeg', dpi=600, bbox_inches='tight')
