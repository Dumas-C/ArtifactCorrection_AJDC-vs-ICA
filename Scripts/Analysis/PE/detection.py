# -*- coding: utf-8 -*-
"""
Copyright (c) 2024 Paris Brain Institute. All rights reserved.

Created on September 2024

@author: Cassandra Dumas

"""

# Modules
# -------
import os
import mne

# Custom modules for data management, and preprocessing
from tools.data_manager import load_data, save_mne_annotations, save_evoked_potential_data, save_mne_reports, save_epoch, load_epoch
from tools.utils import extract_number
from tools.mne_reporting import generate_evoked_potential_report
from tools.preprocessing import preparing_data_BetaPark, preprocessing

# Functions
# ---------
def generate_artefact_pe(subjects, frequencie_file, path, dataset):
    """
    Generate evoked potentials for artefacts (e.g., blinks) for a list of subjects.
    
    Parameters:
        subjects (list): List of subject identifiers.
        frequencie_file (str): Frequency range for processing.
        path (dict): Dictionary containing paths for data storage and retrieval.
        dataset (str): Dataset name (e.g., BetaPark).
    """
    
    for subject in subjects:
        # Skip specific subjects
        if extract_number(subject) in [0, 1, 9, 10]:
            print("Data not available")
            continue
        
        # Perform artefact detection and compute corrected evoked potentials
        pe_detection(subject, path)
        pe_corrected_detection(subject, frequencie_file, path)
    
    # Compute global evoked potentials across all subjects
    compute_global_pe(subjects, frequencie_file, path, dataset)

def pe_detection(subject, path):
    """
    Detect artefacts in the raw EEG signal and compute evoked potentials.
    
    Parameters:
        subject (str): Subject identifier.
        path (dict): Dictionary containing paths for data storage and retrieval.
    """
    
    artefacts = ["BLINKS"] # Artefacts of interest
    directory = path['raw_data'] + subject
    os.chdir(directory)
    
    for artefact in artefacts :
        for file in filter(lambda f: ".vhdr" in f, os.listdir(directory)):
            run = file[9:-5] # Extract run information from the filename
            signal = load_data(file)
            
            # Prepare and preprocess the EEG signal
            preparing_data_BetaPark(signal, extract_number(subject), average_reference=True)
            preprocessing(signal, notch=True, high_pass_filter = 0.5, average_reference=True)
            
            # Detect EOG events for blinks using specific channels
            eog_events = mne.preprocessing.find_eog_events(signal, ch_name=["Fp1", "Fp2"])
            
            # Create annotations for the detected events
            onsets = eog_events[:, 0] / signal.info['sfreq']
            durations = [0.5] * len(eog_events)
            descriptions = [artefact] * len(eog_events)
            artefact_annotations = mne.Annotations(onsets, durations, descriptions, orig_time=signal.annotations.orig_time)
            
            # Save annotations
            saving_path = f"{path['pe_path']}/_ANNOTATIONS_/_{artefact}_/{subject}"
            filename = f'Annotations_{run}-annot.fif'
            save_mne_annotations(artefact_annotations, saving_path, filename)
            
            # Apply annotations to the signal and compute epochs
            signal.set_annotations(artefact_annotations) 
            eog_epochs = mne.Epochs(signal, mne.events_from_annotations(signal)[0], event_id=10001, tmin=-0.50,
                                   tmax=0.50, preload=True, proj=False, reject_by_annotation=False)
            
            # Save epochs
            saving_path = f"{path['pe_path']}/_EPOCHS_/_RAW_/_{artefact}_/{subject}/_RUN_"
            filename = f"{artefact}_{run}-epo.fif"
            save_epoch(eog_epochs, saving_path, filename)
            
            # Compute evoked potential
            raw_evoked_artefact = eog_epochs.average()
            
            # Save evoked potential data
            saving_path = f"{path['pe_path']}/_PE_/_RAW_/_{artefact}_/{subject}/_RUN_"
            filename = f"Evoked_Potential_{run}_ave.fif"
            save_evoked_potential_data(raw_evoked_artefact, saving_path, filename)
            
            # Generate and save MNE report
            report = generate_evoked_potential_report(signal, raw_evoked_artefact, "RAW", artefact, subject, run)
            saving_path = f"{path['mne_reports_path']}_PE_/_RAW_/_{artefact}_/{subject}/_RUN_"
            filename = f"Evoked_Potential_{run}.html"
            save_mne_reports(report, saving_path, filename)
            
        
def pe_corrected_detection(subject, frequencie_file, path):
    """
    Compute evoked potentials for corrected signals using AJDC and ICA.
    
    Parameters:
        subject (str): Subject identifier.
        frequencie_file (str): Frequency range for processing.
        path (dict): Dictionary containing paths for data storage and retrieval.
    """
    
    artefacts = ["BLINKS"] # Artefacts of interest
    
    # Define paths for different processing types
    paths_types = {
        "AJDC": f"{path['ajdc_path']}/_DENOISING_EEG_/{frequencie_file}/_HAND_OBSERVATION_/{subject}",
        "ICA": f"{path['ica_path']}/_DENOISING_EEG_/{subject}"
    }
    
    for processing_type, directory in paths_types.items():
        os.chdir(directory)
        
        for artefact in artefacts:
            for file in filter(lambda f: ".vhdr" in f, os.listdir(directory)):
                # Determine run information
                run = file[9:-5] if processing_type == "RAW" else file[9:-14]
                
                # Load signal
                signal = load_data(file)
                
                # Set montage
                ten_twenty_montage = mne.channels.make_standard_montage('easycap-M1')
                signal.set_montage(ten_twenty_montage)
                
                # Load annotations
                annotations_path = f"{path['pe_path']}/_ANNOTATIONS_/_{artefact}_/{subject}"
                blinks_annotations = mne.read_annotations(os.path.join(annotations_path, f'Annotations_{run}-annot.fif'))
                signal.set_annotations(blinks_annotations)
                
                # Compute epochs
                eog_epochs = mne.Epochs(signal, mne.events_from_annotations(signal)[0], event_id=10001, tmin=-0.50,
                                        tmax=0.50, preload=True, proj=False, reject_by_annotation=False)
                
                # Save epochs and evoked potential data
                save_path_type = processing_type if processing_type != "AJDC" else f"{processing_type}/{frequencie_file}"
                saving_path = f"{path['pe_path']}/_EPOCHS_/_{save_path_type}_/_{artefact}_/{subject}/_RUN_"
                filename = f"{artefact}_{run}-epo.fif"
                save_epoch(eog_epochs, saving_path, filename)
                
                evoked_artefact = eog_epochs.average()
                saving_path = f"{path['pe_path']}/_PE_/_{save_path_type}_/_{artefact}_/{subject}/_RUN_"
                filename = f"Evoked_Potential_{run}_ave.fif"
                save_evoked_potential_data(evoked_artefact, saving_path, filename)
                
                # Generate and save report
                report = generate_evoked_potential_report(signal, evoked_artefact, processing_type, artefact, subject, run)
                saving_path = f"{path['mne_reports_path']}_PE_/_{save_path_type}_/_{artefact}_/{subject}/_RUN_"
                filename = f"Evoked_Potential_{run}.html"
                save_mne_reports(report, saving_path, filename)


def compute_global_pe(sub_list, frequencie_file, path, dataset):
    """
    Compute global evoked potentials for artefacts across all subjects.

    Parameters:
        sub_list (list): List of subject identifiers.
        frequencie_file (str): Frequency range identifier for processing.
        path (dict): Dictionary containing paths for data storage and retrieval.
        dataset (str): Dataset name (e.g., BetaPark).
    """
    
    artefacts = ["BLINKS"]  # Define the artefacts of interest
    processing_type = ["RAW", "AJDC", "ICA"]  # Define the processing types to evaluate

    for artefact in artefacts:
        for processing in processing_type:
            global_pe = []  # Store global evoked potentials for all subjects
            global_epochs = []  # Store concatenated epochs for all subjects

            for subject in sub_list:
                # Skip unavailable subjects for the BetaPark dataset
                if dataset == "BetaPark" and extract_number(subject) in [0, 1, 9, 10]:
                    print("Data not available")
                    continue

                # Define paths for AJDC and other processing types
                if processing == "AJDC":
                    signal_directory = f"{path['ajdc_path']}/_DENOISING_EEG_/{frequencie_file}/_HAND_OBSERVATION_/{subject}"
                    epochs_directory = f"{path['pe_path']}/_EPOCHS_/_{processing}_/{frequencie_file}/_{artefact}_/{subject}/_RUN_"
                    ep_directory = f"{path['pe_path']}/_PE_/_{processing}_/{frequencie_file}/_{artefact}_/{subject}/_RUN_"
                else:
                    signal_directory = f"{path['ica_path']}/_DENOISING_EEG_/{subject}"
                    epochs_directory = f"{path['pe_path']}/_EPOCHS_/_{processing}_/_{artefact}_/{subject}/_RUN_"
                    ep_directory = f"{path['pe_path']}/_PE_/_{processing}_/_{artefact}_/{subject}/_RUN_"

                # Process signals and drop specific channels
                os.chdir(signal_directory)
                for file in filter(lambda f: ".vhdr" in f, os.listdir(signal_directory)[:3]):
                    signal = load_data(file)
                    signal.drop_channels(['TP9', 'FT9'], on_missing='ignore')

                # Load epochs for the subject and concatenate them
                eog_epochs = []
                os.chdir(epochs_directory)
                for file in filter(lambda f: ".fif" in f, os.listdir(epochs_directory)):
                    eog_epoch = load_epoch(file)
                    eog_epoch.drop_channels(['TP9', 'FT9'], on_missing='ignore')
                    eog_epochs.append(eog_epoch)

                eog_epochs = mne.concatenate_epochs(eog_epochs)
                global_epochs.append(eog_epochs)

                # Save concatenated epochs for the subject
                saving_path = f"{path['pe_path']}/_EPOCHS_/_{processing}_/{frequencie_file}/_{artefact}_/{subject}/_GLOBAL_" \
                              if processing == "AJDC" else \
                              f"{path['pe_path']}/_EPOCHS_/_{processing}_/_{artefact}_/{subject}/_GLOBAL_"
                filename = f"{artefact}_{subject}-epo.fif"
                save_epoch(eog_epochs, saving_path, filename)

                # Combine evoked potentials for the subject
                os.chdir(ep_directory)
                list_subject_pe = []
                for file in filter(lambda f: ".fif" in f, os.listdir(ep_directory)):
                    evoked_eog = mne.read_evokeds(file)[0]
                    evoked_eog.drop_channels(['TP9', 'FT9'], on_missing='ignore')
                    list_subject_pe.append(evoked_eog)

                subject_pe = mne.combine_evoked(list_subject_pe, 'nave')
                subject_pe.nave = int(subject_pe.nave)

                # Save combined evoked potentials for the subject
                saving_path = f"{path['pe_path']}/_PE_/_{processing}_/{frequencie_file}/_{artefact}_/{subject}/_GLOBAL_" \
                              if processing == "AJDC" else \
                              f"{path['pe_path']}/_PE_/_{processing}_/_{artefact}_/{subject}/_GLOBAL_"
                filename = f"Evoked_Potential_{subject}_ave.fif"
                save_evoked_potential_data(subject_pe, saving_path, filename)

                # Generate and save subject-level report
                report = generate_evoked_potential_report(signal, subject_pe, processing, artefact, subject, None)
                saving_path = f"{path['mne_reports_path']}_PE_/_{processing}_/{frequencie_file}/_{artefact}_/{subject}/_GLOBAL_" \
                              if processing == "AJDC" else \
                              f"{path['mne_reports_path']}_PE_/_{processing}_/_{artefact}_/{subject}/_GLOBAL_"
                filename = f"Evoked_Potential_{subject}.html"
                save_mne_reports(report, saving_path, filename)

                # Append the subject's evoked potential to the global list
                subject_pe.drop_channels(['TP9', 'FT9'], on_missing='ignore')
                global_pe.append(subject_pe)

            # Combine evoked potentials across all subjects
            global_pe = mne.combine_evoked(global_pe, 'equal')
            global_pe.nave = int(global_pe.nave)

            # Save the global evoked potential
            saving_path = f"{path['pe_path']}/_PE_/_{processing}_/{frequencie_file}/_{artefact}_/_GLOBAL_" \
                          if processing == "AJDC" else \
                          f"{path['pe_path']}/_PE_/_{processing}_/_{artefact}_/_GLOBAL_"
            filename = f"Evoked_Potential_{processing}_ave.fif"
            save_evoked_potential_data(global_pe, saving_path, filename)

            # Combine global epochs and save
            global_epochs = mne.concatenate_epochs(global_epochs)
            saving_path = f"{path['pe_path']}/_EPOCHS_/_{processing}_/{frequencie_file}/_{artefact}_/_GLOBAL_" \
                          if processing == "AJDC" else \
                          f"{path['pe_path']}/_EPOCHS_/_{processing}_/_{artefact}_/_GLOBAL_"
            filename = f"{artefact}_{processing}-epo.fif"
            save_epoch(global_epochs, saving_path, filename)

            # Generate and save global-level report
            report = generate_evoked_potential_report(signal, global_pe, processing, artefact, processing, None)
            saving_path = f"{path['mne_reports_path']}_PE_/_{processing}_/{frequencie_file}/_{artefact}_/_GLOBAL_" \
                          if processing == "AJDC" else \
                          f"{path['mne_reports_path']}_PE_/_{processing}_/_{artefact}_/_GLOBAL_"
            filename = f"Evoked_Potential_{processing}.html"
            save_mne_reports(report, saving_path, filename)

