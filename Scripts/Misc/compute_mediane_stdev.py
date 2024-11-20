# -*- coding: utf-8 -*-
"""
Copyright (c) 2024 Paris Brain Institute. All rights reserved.

Created on July 2024

@author: claire.dussard
"""

import pandas as pd
import numpy as np
import os

# Generate a list of subjects excluding sub-S009 and sub-S010
sub_list = [f'sub-S{"00" if s < 10 else "0"}{s}' for s in range(2, 25) if s not in [9, 10]]
# List of conditions to iterate over
conditions = ["RAW", "AJDC"]

for cond in conditions:
    for sub in sub_list:
        # Define the working directory for the current subject and condition
        dir_path = f"C:/Users/cassandra.dumas/OneDrive - ICM/Documents/PHD/Data/ETUDE_BETAPARK/_NF_PERF_/_PERF_/{sub}/_{cond}_"
        try:
            # Change the current working directory
            os.chdir(dir_path)
        except FileNotFoundError:
            print(f"Directory not found: {dir_path}")
            continue
        
        # Count the number of files containing "mediane" in their name
        count = sum(1 for file in os.listdir() if "mediane" in file and os.path.isfile(file))

        # Load data from the respective mediane files
        try:
            echantillons_a = np.array(pd.read_csv("mediane_a.csv").iloc[:, 2])
            echantillons_b = np.array(pd.read_csv("mediane_b.csv").iloc[:, 2])
            echantillons_c = (
                np.array(pd.read_csv("mediane_c.csv").iloc[:, 2]) if count == 3 else None
            )
        except FileNotFoundError as e:
            print(f"File not found: {e.filename}")
            continue
        
        # Combine the loaded arrays into a single array
        final_echantillon = np.concatenate(
            (echantillons_a, echantillons_b, echantillons_c) if echantillons_c is not None else (echantillons_a, echantillons_b)
        )
        
        # Calculate required statistical metrics
        thresholds = {
            'min': final_echantillon.min(),
            'percentile5': np.percentile(final_echantillon, 5),
            'percentile10': np.percentile(final_echantillon, 10),
            'percentile25': np.percentile(final_echantillon, 25),
            'percentile47': np.percentile(final_echantillon, 47),
            'percentile50': np.percentile(final_echantillon, 50),
            'percentile75': np.percentile(final_echantillon, 75),
            'max': final_echantillon.max(),
            'stdev': round(np.std(final_echantillon), 3),
        }

        # Create a DataFrame for the thresholds
        df_thresholds = pd.DataFrame(thresholds, index=['values'])

        # Display and save the DataFrame
        print(df_thresholds)
        output_file = os.path.join(dir_path, 'values_threshold.csv')
        try:
            df_thresholds.to_csv(output_file, index=False)
        except Exception as e:
            print(f"Error saving file: {e}")