# -*- coding: utf-8 -*-
"""
Copyright (c) 2024 Paris Brain Institute. All rights reserved.

Created on June 2024

@author: Cassandra Dumas

"""

# Modules
# -------
import mne
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Qt5Agg')

# Functions
# ---------

def plot_spectrum_and_topomap(f, spectrum_abs, backward_filter, info, index):
    """
    Plots the power spectrum and the topographic map of a source.

    Parameters:
        f (array): Frequency values for the spectrum.
        spectrum_abs (array): Absolute power spectrum values for the source.
        backward_filter (array): Backward filter (spatial filter) used for the source.
        info (dict): Info dictionary containing channel location and montage information.
        index (int): Index of the source being plotted.

    Returns:
        fig (matplotlib.figure.Figure): A Matplotlib figure containing the power spectrum and topographic map.
    """
    # Create a figure with two subplots: one for the spectrum and one for the topographic map
    fig, axs = plt.subplots(nrows=1, ncols=2, figsize=(12, 5))

    # Plot the power spectrum
    axs[0].plot(f, spectrum_abs, label='Absolute power')
    axs[0].set(title=f'Power spectrum of the source {index} estimated by AJDC',
               xlabel='Frequency (Hz)', ylabel='Power spectral density')
    axs[0].legend()

    # Plot the topographic map
    axs[1].set_title(f'Topographic map of the source {index} estimated by AJDC')
    mne.viz.plot_topomap(backward_filter, pos=info, axes=axs[1], show=False)

    # Adjust layout to prevent overlapping
    fig.tight_layout()

    return fig

