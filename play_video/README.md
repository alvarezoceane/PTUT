# Play Video & Manual Annotation Tools

This folder contains user interface (UI) utilities, script protocols, and reference documentation used during the manual data curation, video annotation, and trajectory visualization phases of the *C. elegans* tracking project.

## 📌 Overview

Before implementing the automated cleaning filters, a targeted validation dataset was generated manually. The scripts in this directory allow researchers to load specific tracking folders, visualize coordinate overlays on top of the experimental videos, record true biological classifications, and produce exploratory histograms.

---

## 🗂️ File Inventory & Descriptions

### 🚀 Core Python Scripts
* **`play_video.py`**: The main interactive visualization script. It overlays recorded trajectory coordinates onto the raw video frames, allowing manual verification of tracking accuracy, worm identities, and body loops.
* **`video_visualiser-3.py`**: A specialized auxiliary utility script used to inspect specific tracking segments and isolate frames containing spatial anomalies or duplicate detection noise.

### 📈 Figures & Histograms
* **`histogram_new.png`**: An exploratory plot capturing the initial distribution of duplicated frame frequencies before global automated filtering was applied.

### 📋 Guidelines & Documentation (PDFs)
* **`video_to_annotate.pdf`**: The official protocol sheet and guidelines detailing the target criteria for selection, labeling standards, and video identification codes.
* **`list_to_generate_histo-1.pdf`**: Reference documentation listing the exact subset of video directories selected for manual histogram validation and verification testing.

---

## 🛠️ Requirements & Setup

These visualization tools rely on OpenCV and standard data handlers. Ensure your environment has the following libraries installed:

```bash
pip install opencv-python pandas matplotlib
