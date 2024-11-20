# Automatic Ocular Artifact Correction in Electroencephalography for Neurofeedback

---
This repository contains the code and supporting documents associated with the following manuscript:

C. Dumas, M.-C. Corsi, C. Dussard, F. Grosselin, N. George (2025). Automatic Ocular Artifact Correction in Electroencephalography for Neurofeedback. 
 
---
## Authors:
* [Cassandra Dumas](https://www.linkedin.com/in/cassandra-dumas-a002a2153/), Sorbonne Université, Institut du Cerveau (_alias_ [@Dumas-C](https://github.com/Dumas-C))
* [Marie-Constance Corsi](https://marieconstance-corsi.netlify.app), Sorbonne Université, Institut du Cerveau (_alias_ [@mccorsi](https://github.com/mccorsi))
* [Claire Dussard](https://www.linkedin.com/in/claire-dussard-92469a256/), Sorbonne Université, Institut du Cerveau (_alias_ [@cdussard](https://github.com/cdussard))
* [Fanny Grosselin](https://www.linkedin.com/in/fanny-grosselin/), Sorbonne Université, Institut du Cerveau
* [Nathalie George](https://www.linkedin.com/in/nathalie-george-406a09167/), Sorbonne Université, Institut du Cerveau


---
## Abstract
<p align="justify"> Ocular artifacts can significantly impact electroencephalography (EEG) signals, potentially compromising the performance of neurofeedback (NF) and brain-computer interfaces (BCI) based on EEG. This study investigates if the Approximate Joint Diagonalization of Fourier Cospectra (AJDC) method can effectively correct blink-related artifacts and preserve relevant neurophysiological signatures in a pseudo-online context. AJDC is a frequency-domain Blind Source Separation (BSS) technique, which uses cospectral analysis to isolate and attenuate blink artifacts. Using EEG data from 21 participants recorded during a NF motor imagery (MI) task, we compared AJDC with Independent Component Analysis (ICA), a widely used method for EEG denoising. We assessed the quality of blink artifact correction, the preservation of MI-related EEG signatures, and the influence of AJDC correction on the NF performance indicator. We show that AJDC effectively attenuates blink artifacts without distorting MI-related beta band signatures and with preservation of NF performance. AJDC was calibrated once on initial EEG data. We therefore assessed AJDC correction quality over time, showing some decrease. This suggests that periodic recalibration may benefit long EEG recording. This study highlights AJDC as a promising real-time solution for artifact management in NF, with the potential to provide consistent EEG quality and to enhance NF reliability. </p>

## Code
<p align="justify">
This repository contains the code used to run the analysis performed and to plot the figures.
Computation and figures were performed with the following Python version: 3.12.4. In 'requirements.txt' a list of all the Python dependencies is proposed ..
Statistical analysis was performed with following R version: 4.4.1.
</p>

---
## Figures

### Figure 1a - Blink Evoked Potential
![Fig. 1a](./Figures/Fig_1a.jpeg)

*<p align="justify"> Blink EPs for the conditions: RAW (left), AJDC-corrected (centre), ICA-corrected (right) signals. The grand average of the EPs across subjects is presented. At the top of each plot, topographies represent the spatial distribution of the blink EPs at t = 0 s corresponding to the blink peak. The inset boxes zoom in on the corrected EPs for better visualization of the differences between methods. Vertical axis: amplitude (µV); horizontal axis: time (s). </p>*

### Figure 1b - Power Spectra on blink Evoked Potential
![Fig. 1b](./Figures/Fig_1b.jpeg)

### Figure 2 - Motor Imagery Signature
![Fig. 2](./Figures/Fig_2.jpeg)

### Figure 3 - Comparison of Neurofeedback Performance between RAW and AJDC
![Fig. 3](./Figures/Fig_3.png)

### Figure 4 - Comparison of Signal-to-Noise Ratio between first and last neurofeedback runs
![Fig. 4](./Figures/Fig_4.jpeg)
