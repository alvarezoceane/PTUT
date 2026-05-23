# Pipeline automated analysis for C. elegans Tracking Data

This folder contains the core Python pipeline (`script_ptut.py`) designed to automate data quality control, structural auditing, and spatial noise filtering for large-scale *C. elegans* behavioral tracking datasets.

## Overview

The script processes raw experimental directories to clean tracking artifacts (duplicated frames) and systematically standardize data before downstream ecological modeling (Marginal Value Theorem). 

It operates across 5 main phases:
1. **File Integrity Checking:** Verifies the presence of `traj.csv`, `traj.mat`, and `foodpatches_reviewed.csv`.
2. **Empty Dataset Filtering:** Flags empty experiments using a strict structural 200-byte threshold on binary files.
3. **Behavioral Categorization:** Automatically classifies video folders into operational groups (`0 worms`, `1 worm clean`, `1 worm with errors`, `2+ worms`).
4. **Validation Analysis:** Compares pre- and post-filtering duplication rates using a manually annotated validation subset (`traj_copy.csv`).
5. **Secondary Spatial Filtering:** Automatically isolates and cleans persistent tracking anomalies using custom distance-centroid thresholds.

---

## Prerequisites & Installation

The pipeline is written in **Python 3.9+** and requires standard data science libraries. 

