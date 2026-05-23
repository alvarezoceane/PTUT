# Graphs

This folder contains the figures generated to evaluate the quality of the trajectory filtering process and the reduction of duplicated worm detections after manual and automatic cleaning.

## 1. Histogram: analyse_alternatives.png : duplicated-frame proportions before and after filtering

This figure compares the proportion of duplicated frames before and after filtering across the dataset and for each video category:

- **0 worms**
- **1 worm clean**
- **1 worm with errors**
- **2+ worms**

The histogram allows visualization of the distribution of duplicated-frame proportions and evaluates the impact of filtering on tracking quality.

## 2. Boxplot: filtered_analysis_all_videos_log.png : “1 worm with errors” before and after filtering

This figure focuses specifically on videos classified as **“1 worm with errors”** and compares duplicated-frame proportions before and after filtering.
The boxplot highlights changes in the distribution of tracking errors and helps evaluate whether filtering reduces duplicated detections in problematic videos.
