# -*- coding: utf-8 -*-
"""
Copyright (c) 2024 Paris Brain Institute. All rights reserved.

Created on June 2024

@author: Cassandra Dumas

"""

# Modules
# -------
import numpy as np
import mne
import matplotlib.pyplot as plt
from pyriemann.utils.viz import plot_cospectra

from tools.utils import extract_number, get_lobes_channels

# Functions
# ---------
def generate_html_table(data):
    """
    Generate an HTML table from a dictionary of key-value pairs.
    
    Parameters:
        data (dict): Dictionary with headers as keys and values for rows.
    
    Returns:
        str: HTML table as a string.
    """
    rows = []
    for i, (header, value) in enumerate(data.items()):
        background_color = "#f2f2f2" if i % 2 == 0 else "#ffffff"
        rows.append(f"""
        <tr style="background-color: {background_color};">
            <td style="border: 1px solid black; text-align: center; padding: 10px;"><b>{header}</b></td>
            <td style="border: 1px solid black; text-align: center; padding: 10px;">{value}</td>
        </tr>
        """)
    return f"""
    <table style="margin-left: auto; margin-right: auto; width: 60%; border-collapse: collapse; border: 1px solid black;">
        {''.join(rows)}
    </table>
    """
    
    
def generate_ajdc_report(subject, condition, ajdc, blink, saccade, signal, source, sr_names, spectrums_figures, signal_corrected):
    """
    Generate an MNE report for AJDC calibration and decomposition results.
    
    Parameters:
        subject (str): Subject ID.
        condition (str): Calibration condition.
        ajdc (AJDC): AJDC object containing decomposition parameters.
        blink (list): Blink components identified by AJDC.
        saccade (list): Saccade components identified by AJDC.
        signal (Raw): Original signal.
        source (Raw): Decomposed source signal.
        sr_names (list): Source signal names.
        spectrums_figures (Figure): Spectrum plots.
        signal_corrected (Raw): Corrected signal after AJDC.
    
    Returns:
        Report: MNE report object.
    """
    
    # Create a summary table for AJDC parameters
    table_data = {
        "Calibration Condition": condition,
        "Frequencies of decomposition": f"{ajdc.fmin} - {ajdc.fmax}",
        "Number of AJDC components": ajdc.n_sources_,
        "Blinks components": blink if blink else "None",
        "Saccades components": saccade if saccade else "None"
    }
    html_code = generate_html_table(table_data)
    
    # Initialize MNE report
    report_title = f"BETAPARK - {subject} - AJDC Calibration/Decomposition on {ajdc.fmin}/{ajdc.fmax}Hz"
    report = mne.Report(title=report_title)
    report.add_html(html_code, title="Decomposition Informations", tags=('Informations',))
    
    # Add figures to the report
    figures = [
        (signal.plot(duration=(signal.n_times / signal.info['sfreq']), n_channels=signal.info['nchan'], scalings={'eeg': 40e-6}, show=False), "AJDC Calibration Signal", "Calibration Signal", 'Raw_Calibration_Signal'),
        (source.plot(duration=(source.n_times / signal.info['sfreq']), n_channels=source.info['nchan'], scalings={'misc': 6e-4}, show=False), "AJDC Components Signal", "Signal Decomposition", 'Components_Calibration_Signal'),
        (plot_cospectra(ajdc._cosp_channels, ajdc.freqs_, ylabels=signal.info['ch_names'], title='Cospectra, in channel space'), "Cospectra, in channel space", "Cospectra", 'AJDC_Cospectra'),
        (plot_cospectra(ajdc._cosp_sources, ajdc.freqs_, ylabels=sr_names, title="Diagonalized cospectra, in source space"), "Cospectra, in source space", "Cospectra", 'AJDC_Cospectra'),
        (spectrums_figures, "Power Spectrums & Components", "Spectrums & Topographies", 'Components_Power_Spectrum'),
        (signal_corrected.plot(duration=(signal_corrected.n_times / signal.info['sfreq']), n_channels=signal_corrected.info['nchan'], scalings={'eeg': 40e-6}, show=False), "AJDC Calibration Corrected Signal", "Signal corrected", 'Corrected_Calibration_Signal')
    ]

    for fig, title, section, tag in figures:
        report.add_figure(fig, title=title, section=section, tags=(tag,))
    
    # Close all open figures to avoid overlapping in memory
    plt.close('all')
    
    return report


def generate_evoked_potential_report(signal, evoked_potential, signal_type, artefact, subject=None, run=None):
    """
    Generate a report for evoked potentials including plots and PSD analysis.
    
    Parameters:
        signal (Raw): Original raw signal.
        evoked_potential (Evoked): Evoked potential data.
        signal_type (str): Type of signal (RAW, ICA, AJDC).
        artefact (str): Artefact type (e.g., blinks, saccades).
        subject (str): Subject ID (optional).
        run (str): Run name (optional).
    
    Returns:
        Report: MNE report object.
    """
    
    # Initialize MNE report
    report = mne.Report(title=f"{artefact} Evoked Potential - {subject} - {run}")
    
    # Add evoked potential plot
    ylim_eeg = dict(eeg=[-100, 300]) if signal_type == "RAW" else dict(eeg=[-30, 30])
    evoked_eog_plot = evoked_potential.plot(ylim=ylim_eeg, show=False)
    evoked_eog_plot.set_constrained_layout(True)  # Use constrained layout instead of tight_layout
    report.add_figure(evoked_eog_plot, title="Evoked Potential", section="Evoked Potential")
    
    # Generate PSD plots for global and lobes
    fig_psd_global, axs_psd_global = plt.subplots(nrows=1, ncols=1, figsize=(25, 10), constrained_layout=True)  # Enable constrained_layout here
    evoked_potential.compute_psd(method='multitaper',fmin=1, fmax=80).plot(average=True, axes=axs_psd_global, exclude='bads', sphere='auto', show=False)
    axs_psd_global.set_ylim(-20, 50)
    report.add_figure(fig_psd_global, title="PSD", section="PSD global")
    
    lobes = get_lobes_channels()
    
    figs_psd = []
    for name, lobe in lobes.items():
        lobe_electrodes = [electrode for electrode in lobe if electrode in signal.info['ch_names']]
        if not lobe_electrodes:
            continue
    
        fig_psd_lobe, axs_psd_lobe = plt.subplots(nrows=1, ncols=1, figsize=(25, 10), constrained_layout=True)
        evoked_potential.compute_psd(method='multitaper', fmin=1, fmax=80).plot(average=True, picks=lobe_electrodes, exclude='bads', axes=axs_psd_lobe, show=False)
        axs_psd_lobe.set_ylim(-20, 50)
        
        sensors_specific = evoked_potential.copy().pick(lobe_electrodes)
        ax2_psd_lobe = fig_psd_lobe.add_axes([.9, .75, .1, .2])
        mne.viz.plot_sensors(sensors_specific.info, axes=ax2_psd_lobe)
        
        figs_psd.append(fig_psd_lobe)
    
    report.add_figure(figs_psd, title="PSD", section="PSD lobes")
    
    # Add topography plot plot
    vlim_topomap = (-30, 30)
    evoked_eog_topo = evoked_potential.plot_topomap(times=[-0.3, -.15, 0, 0.15, 0.3], vlim=vlim_topomap, show=False)
    evoked_eog_topo.set_constrained_layout(True)  # Use constrained_layout here
    report.add_figure(evoked_eog_topo, title="Topomap", section="Topomap")
    
    # Add joint evoked potential plot
    times = [-0.3, -.15, 0, 0.15, 0.3]
    ts_args = dict(ylim=ylim_eeg)
    topomap_args = dict(vlim=vlim_topomap)
    
    evoked_eog_joint = evoked_potential.plot_joint(times=times, ts_args=ts_args, topomap_args=topomap_args, show=False)
    evoked_eog_joint.set_figwidth(20)
    evoked_eog_joint.set_figheight(10)
    evoked_eog_joint.set_constrained_layout(True)  # Constrained layout for joint plot
    
    report.add_figure(evoked_eog_joint, title="Joint Evoked Potential", section="Joint")
    
    # Close all open figures to avoid overlapping in memory
    plt.close('all')
    
    return report
    

def generate_tfr_report(global_tfr, processing_type, subject=None, run=None):
    """
    Generate a report for time-frequency representation (TFR) analysis.
    
    Parameters:
        global_tfr (AverageTFR): Global TFR object containing time-frequency data.
        processing_type (str): Processing type (e.g., RAW, ICA, AJDC).
        subject (str): Subject ID (optional).
        run (str): Run name (optional).
    
    Returns:
        Report: MNE report object.
    """
    
    # Initialize MNE report
    report = mne.Report(title=f"Time Frequency Motor Imagery - {processing_type} - {subject} - {run}")
    
    # Add TFR plots for each electrode
    for elec in global_tfr.info['ch_names']:
        fig_tfr = global_tfr.plot([elec], vlim=(-0.5,0.5), baseline=(-3, -1), mode="logratio", title=elec, combine='mean', show=False)[0]
        fig_tfr.axes[1].set_yticks([-0.5, -0.3, -0.1, 0.1, 0.3, 0.5])
        fig_tfr.axes[1].set_yticklabels(['- 0.5', '- 0.3', '- 0.1', '0.1', '0.3', '0.5'])
        report.add_figure(fig_tfr, title=f"{elec} TIME-FREQUENCY", section=f"{elec} TIME-FREQUENCY")
    
    # Close all open figures to avoid overlapping in memory
    plt.close('all')
    
    return report


def generate_snr_report(snr_global_ajdc, snr_electrode_ajdc, snr_global_ica, snr_electrode_ica, electrodes, subject, nf_session):
    """
    Generate a report for SNR (Signal-to-Noise Ratio) analysis across AJDC and ICA methods.
    
    Parameters:
        snr_global_ajdc (dict): Global SNR values for AJDC.
        snr_electrode_ajdc (dict): Electrode-specific SNR values for AJDC.
        snr_global_ica (dict): Global SNR values for ICA.
        snr_electrode_ica (dict): Electrode-specific SNR values for ICA.
        electrodes (list): List of electrode names.
        subject (str): Subject ID.
        nf_session (dict): Neurofeedback session data with run information.
    
    Returns:
        Report: MNE report object.
    """
    
    # Initialize MNE report
    report = mne.Report(title=f"SNR Scores - {subject}")
    
    # Define runs and corrections
    runs = ['5-2-a', '5-2-b', '6-2-a', '6-2-b', '7-2-a', '7-2-b', '8-2-a', '8-2-b']
    correction = ['AJDC', 'ICA']
    
    # Get labeled run names from the neurofeedback session data
    run_base_names = nf_session["S"+str(extract_number(subject))]
    labeled_run_names = [f"{name} {i+1}" for name in run_base_names for i in range(2)]
    
    # Get electrode lobes
    lobes = get_lobes_channels()
    jitter_strength = 0.05
    
    # Global SNR plots
    for i, snr in enumerate([snr_global_ajdc, snr_global_ica]): 
        fig_snr, axs_snr = plt.subplots(nrows = 1, ncols = 1, figsize=(18,11))    
        
        valeurs = []
        for run in runs:
            matching_key = next((key for key in snr if run in key), None)
            if matching_key is not None:
                valeurs.append(snr[matching_key])
            else:
                valeurs.append(np.nan)

        axs_snr.plot(runs, valeurs, marker='o', linestyle='-')
        
        axs_snr.set_xticks(range(len(labeled_run_names)))
        axs_snr.set_xticklabels(labeled_run_names)
        
        report.add_figure(fig_snr, title=f"Global - {correction[i]}", section=f"{correction[i]}")
    
    # Electrode-specific SNR plots for lobes
    for i, snr in enumerate([snr_electrode_ajdc, snr_electrode_ica]):
        figs = []
        
        for lobe in lobes:
            fig_snr, axs_snr = plt.subplots(nrows = 1, ncols = 1, figsize=(18,11)) 
            
            indices_lobe_electrodes = [list(electrodes).index(elec) for elec in lobes[lobe] if elec in list(electrodes)]
            
            for j in indices_lobe_electrodes:
                valeurs = []
                for run in runs:
                    matching_key = next((key for key in snr if run in key), None)
                    if matching_key is not None:
                        valeurs.append(snr[matching_key][j])
                    else:
                        valeurs.append(np.nan)
                        
                jittered_conditions = [np.random.normal(loc=idx, scale=jitter_strength, size=1)[0] for idx in range(len(runs))]
            
                axs_snr.plot(jittered_conditions, valeurs, marker='o', linestyle='-', label=list(electrodes)[j])
            
            axs_snr.set_xticks(range(len(labeled_run_names)))
            axs_snr.set_xticklabels(labeled_run_names)
    
            fig_snr.suptitle(lobe)
            axs_snr.legend()
            
            figs.append(fig_snr)
        
        report.add_figure(figs, title=f"Electrodes - {correction[i]}", section=f"{correction[i]}")
    
    # Close all open figures to avoid overlapping in memory
    plt.close('all')
    
    return report
    
    