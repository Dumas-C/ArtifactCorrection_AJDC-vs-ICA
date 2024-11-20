# -*- coding: utf-8 -*-
"""
Copyright (c) 2024 Paris Brain Institute. All rights reserved.

Created on June 2024

@author: Cassandra Dumas

"""

# Modules
# -------
import os 
os.chdir((os.path.dirname(os.path.realpath(__file__))))

from tools.utils import load_paths, setup_betapark

# Variables
# ---------

# Dictionary containing the available commands and their descriptions
commands = {
    1 : "AJDC_calibration", 
    2 : "AJDC_denoising", 
    3 : "ICA_denoising", 
    4 : "EP_artefact_generation",
    5 : "TF_MI_generation",
    6 : "SNR_computation"
    }

# Specify the dataset and frequency band for AJDC
dataset = "BetaPark" # Adjust for the desired dataset
fmin_ajdc, fmax_ajdc = 1, 80 # Frequency band decomposition for AJDC
frequencie_file = f"_BAND_{fmin_ajdc}_{fmax_ajdc}_"

# Load subject list, conditions, and paths for BetaPark study
sub_list, conditions = setup_betapark()
path = load_paths('Tools/BetaPark.json')['PATH']
runs_desc = load_paths('Tools/BetaPark.json')['STEP']
nf_session = load_paths('Tools/BetaPark.json')['NF_SESSION']

# Input
# -----
print("\nIn the list above, you will find the different analyses available")
for cle, valeur in commands.items():
    print(str(cle) + " : " + valeur)

# Prompt the user to select an analysis
key = int(input("\nSelect the analysis you want to perform \n"))
analysis = commands[key]


# Functions
# ---------
def main():
    """
    Main function to perform the selected analysis based on user input.
    """
    
    ####### AJDC #######
    # ------------------
    if analysis == "AJDC_calibration":
        from AJDC.calibration import calibrate_ajdc
        print('AJDC calibration')
        calibrate_ajdc(sub_list, conditions, frequencie_file, path, dataset)
        
    elif analysis == "AJDC_denoising":
        from AJDC.denoising import denoise_ajdc
        print("AJDC Denoising")
        denoise_ajdc(sub_list, conditions, frequencie_file, path, dataset)
    
    ####### ICA #######
    # ------------------
    elif analysis == "ICA_denoising":
        from ICA.denoising import denoise_ica
        print("ICA Denoising")
        denoise_ica(sub_list, path, runs_desc, dataset)
    
    ####### EVOKED POTENTIAL #######
    # ----------------------------
    elif analysis == "EP_artefact_generation":
        from PE.detection import generate_artefact_pe
        print("EP Generation")
        generate_artefact_pe(sub_list, frequencie_file, path, dataset)
        
    ####### SIGNAL TO NOISE RATIO #######
    # ----------------------------
    elif analysis == "SNR_computation":
        from SNR.computation import snr_computation
        print("SNR_computation")
        snr_computation(sub_list, frequencie_file, path, dataset, nf_session)
        
    ####### TIME FREQUENCY #######
    # ----------------------------
    elif analysis == "TF_MI_generation":
        from TFR.detection import generate_tfr_mi
        print("TF Generation")
        generate_tfr_mi(sub_list, frequencie_file, path, dataset)
        
    elif analysis == "TF_MI_comparaison":
        print("TF Comparaison")
        

####### MAIN #######
# ------------------
if __name__ == '__main__':
    main()