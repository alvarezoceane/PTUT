from pathlib import Path  # pathlib is a module used to work with files and folders , Path: allows you to: navigate through directories and list files and folders
import os # os is a module that allows Python to interact with the operating system
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import pprint as pprint
import matplotlib.pyplot as plt
import seaborn as sns

#2.a
def open_folders():  
    """
    This function parse all of the folders and return a list of all of the folders
    """
    data = Path("/Users/noursaad/Desktop/PTUT/Minipatches_light_20260116") # Path is used to set our current working directory
    folders = [] #This list will store all folders found 

    for folder in data.iterdir(): # iterdir() lists everything inside data # This loop will go through all the folders in the directory 
        if folder.is_dir(): # is_dir() checks if a path corresponds to a directory and returns True only for folders
            folders.append(folder) # Each directory found is added to dossiers
    
    return folders 
    
def file_existence(folder:Path):
    
    traj_csv = folder / "traj.csv" # This syntax builds the path to a file (.csv, .mat)  inside each folder using pathlib 
    traj_mat = folder / "traj.mat"
    foodpatches_reviewed_mat= folder / "foodpatches_reviewed.mat"

        
    has_traj_csv = int(traj_csv.exists())
    has_traj_mat = int(traj_mat.exists())
    has_foodpatch_reviewed_mat = int(foodpatches_reviewed_mat.exists())
    
    return (traj_csv,traj_mat,foodpatches_reviewed_mat, has_traj_csv,has_traj_mat,has_foodpatch_reviewed_mat)
    

def file_size(folder:Path):
    """
    This fonction finds the size of the folders and compares file sizes across folders
    """
    traj_csv=folder / "traj.csv"
    traj_mat =folder / "traj.mat"
    foodpatches_reviewed_mat =folder / "foodpatches_reviewed.mat"
    
    sizes = []
 
    if foodpatches_reviewed_mat.exists() == False and traj_csv.exists() == False :  #if these 2 files do not exists 
        return traj_mat.stat().st_size
    return None


def threshold(folder: Path):
    traj_mat = folder / "traj.mat"
    if traj_mat.exists() and traj_mat.stat().st_size <= 200:
        traj_mat_empty = 1
    else:
        traj_mat_empty = 0
    return(traj_mat_empty)


def worm_diagnosis(has_traj_csv, has_foodpatches_reviewed_mat, has_traj_mat, traj_mat_empty):
    diagnosis=None
    if has_traj_mat==0 or traj_mat_empty==1:
        diagnosis= "NO WORM"
    elif has_traj_mat==1 and has_traj_csv ==1 and has_foodpatches_reviewed_mat ==1:
        diagnosis= "OK"
    elif traj_mat_empty== 0 and (has_traj_csv ==0 or has_foodpatches_reviewed_mat ==0): 
        diagnosis="WEIRD"
    return(diagnosis)

def count_frames_simple(traj_csv):

    if not traj_csv.exists():
        return 0, 0, 0
    if os.path.getsize(traj_csv) == 0:
        return 0, 0, 0

    df = pd.read_csv(traj_csv)

    # if seperator ;
    if len(df.columns) == 1 and ";" in df.columns[0]:
        df = pd.read_csv(traj_csv, sep=";")

    # cleans the spaces in the name frame
    df.columns = df.columns.str.strip()

    if df.empty:
        return 0, 0, 0

    if "frame" not in df.columns:
        # stops if no column
        return 0, 0, 0

    frame_counts = df["frame"].value_counts()

    max_frame = int(frame_counts.index.max())
    total_frames = max_frame + 1

    frames_1 = int((frame_counts == 1).sum())
    frames_2plus = int((frame_counts >= 2).sum())
    frames_0 = int(total_frames - frames_1 - frames_2plus)

    return (frames_0, frames_1, frames_2plus)


def compute_prop_multiple(frames_0, frames_1, frames_2plus):

    total_frames = frames_0 + frames_1 + frames_2plus

    # checking if the totale number of frame is = to 0 for safety 
    if total_frames == 0:
        return 0.0

    prop_multiple = frames_2plus / total_frames

    return prop_multiple

def define_category(frames_0, frames_1, frames_2plus, prop_multiple, threshold): # we choose a thershold of 2% and consider that under this value its an error (its not possible that its 2 worms)

    # Case 1: zero worms
    if frames_1 == 0 and frames_2plus == 0:
        category = "0 worms"

    # Case 2: one worm clean
    elif frames_1 > 0 and frames_2plus == 0:
        category = "1 worm clean"

    # Case 3: one worm with errors
    elif frames_2plus > 0 and prop_multiple <= threshold:
        category = "1 worm with errors"

    # Case 4: two or more worms
    else:
        category = "2+ worms"

    return category


def create_csv(file_path,file_name):
    
    base = Path.home() / "Desktop" 
    output_folder = base / "PTUT"
    output_folder.mkdir(exist_ok=True)

    output_path = output_folder / file_name
    
    if output_path.exists():
        print(f"The file already exists : {output_path}")
        return 

    # columns of the CSV
    csv_columns = [
        "Folder Path",
        "traj.csv exists?",
        "foodpatches_reviewed.csv exists?",
        "traj.mat exists?",
        "traj.mat empty?",
        "Diagnosis of video",
        "frames with zero worms",
        "frames with one worm",
        "frames with two or more worms",
        "proportion of frames with multiple worms",
        "final classification of the video"
    ]

    data = Path("/Users/noursaad/Desktop/PTUT/Minipatches_light_20260116")
    rows = []

    for folder in open_folders():

        (
            traj_csv,
            traj_mat,
            foodpatches_reviewed_mat,
            has_traj_csv,
            has_traj_mat,
            has_foodpatches_reviewed_mat
        ) = file_existence(folder)

        traj_mat_empty = int(threshold(folder))
        diagnosis = worm_diagnosis(
            has_traj_csv,
            has_foodpatches_reviewed_mat,
            has_traj_mat,
            traj_mat_empty
        )
        
        f0, f1, f2 = count_frames_simple(traj_csv)
        prop_multiple = compute_prop_multiple(f0, f1, f2)
        category = define_category(f0, f1, f2, prop_multiple, threshold=0.05)


        rows.append([
            str(folder),
            has_traj_csv,
            has_traj_mat,
            has_foodpatches_reviewed_mat,
            traj_mat_empty,
            diagnosis,f0,f1,f2,prop_multiple,category
        ])
    df = pd.DataFrame(rows, columns=csv_columns)
    df.to_csv(output_path, index=False)

    print(f"CSV created : {output_path}")

def histogram(file_path, seuil):
	# read the csv file
	df = pd.read_csv(file_path)
	# verify if the column exists, if not print a message and stop the function
	if "proportion of frames with multiple worms" in df.columns:
		# Tracer l'histogramme
		df["proportion of frames with multiple worms"].hist(bins=100)
		plt.yscale('log')
		plt.xlabel("Proportion of the frames")
		plt.ylabel("Number of frames")
		plt.title("Proportion of frames with multiple worms")
		# Ajouter une ligne rouge pour le seuil sur l'axe des abscisses (X)
		plt.axvline(seuil, color='red', linestyle='--', linewidth=2, label=f'Seuil = {seuil}')
		plt.text(seuil + 0.01, plt.ylim()[1] * 0.9, f'Threshold = {seuil}', color='red', fontsize=12, ha='left')
		plt.show()
	else:
		print("La colonne 'proportion of frames with multiple worms' n'existe pas dans ce fichier.")

def histogramme_annotate(file_path) : 
	df = pd.read_csv(file_path)
	video_annotated = []
	proportion = []
# verify if the column exists, if not print a message and stop the function
	if "proportion of frames with multiple worms" in df.columns:
	#	loop on the rows of the dataframe and if the proportion of frames with multiple worms is under 20% we add the video to the list of videos to annotate and the proportion to the list of proportions
		for el, row in df.iterrows():
			if row["proportion of frames with multiple worms"] < 0.2:
				video = row['Folder Path']
				proportion1 = row["proportion of frames with multiple worms"] 
 # add only if the video is not already in the list to avoid duplicates
				if video not in video_annotated:
					video_annotated.append(video)
					proportion.append(proportion1)
	print("Vidéos à annoter associées aux frames <20% :")
	#pprint.pprint(video_annotated + proportion )
	# direct loop without creating the lists, we print directly the video and the proportion if the condition is met
	for idx, row in df.iterrows():
		if row["proportion of frames with multiple worms"] < 0.2:
			pprint.pprint(f"{row['Folder Path']}  ->  {row['proportion of frames with multiple worms']:.3f}")


def histogram_JustOneWorm(csv_path, ods_path) : 
# load the files
	df_comments = pd.read_excel("results_manual_annotation.ods", engine="odf")
	df_results = pd.read_csv("results.csv")
	#print(df_comments.columns)
	#print(df_results.columns)
# 1. filter the videos "1 worm"
	df_1worm = df_comments[df_comments["Comments"].str.contains("1 worm", na=False)]
# 2. get the unique paths
	paths_1worm = df_1worm["Path to each video"].unique()
# 3. filter the results file
	df_filtered = df_results[df_results["Path to each video"].isin(paths_1worm)]
# 4. retrieve the proportions
	proportions = df_filtered["proportion of frames with multiple worms"]
	print("Unique videos in results:", df_results["Path to each video"].nunique())
	print("Unique videos after filtering:", df_filtered["Path to each video"].nunique())
	print(proportions)
# Histogram
	plt.hist(proportions, bins=10)
	plt.xlabel("Proportion of duplicated frames")
	plt.ylabel("Number of videos")
	plt.title("Histogram - 1 worm videos only")
	plt.show()

def histogram_MoreThanOneWorm(csv_path, ods_path) : 
# load the files
	df_comments = pd.read_excel("results_manual_annotation.ods", engine="odf")
	df_results = pd.read_csv("results.csv")
	#print(df_comments.columns)
	#print(df_results.columns)
# 1. filter the videos "1 worm"
	df_MoreThan1Worm = df_comments[(df_comments["Comments"].str.contains("1 worm", na=False) == False) &
	(df_comments["Comments"].str.contains("no traj.csv", na=False) == False)]
# 2. get the unique paths
	paths_MoreThan1Worm = df_MoreThan1Worm["Path to each video"].unique()
# 3. filter the results file
	df_filtered = df_results[df_results["Path to each video"].isin(paths_MoreThan1Worm)]
# 4. retrieve the proportions
	proportions = df_filtered["proportion of frames with multiple worms"]
	
	print("Unique videos in results:", df_results["Path to each video"].nunique())
	print("Unique videos after filtering:", df_filtered["Path to each video"].nunique())
# Histogramme
	plt.hist(proportions, bins=10)
	plt.xlabel("Proportion of duplicated frames")
	plt.ylabel("Number of videos")
	plt.title("Histogram with > 1 worm videos only")
	plt.show()


def calculs(folder:Path):
	all_folders = list(open_folders())  # open() returns a generator, so we convert it to a list to be able to use it multiple times and to print it if needed
	#print("folders found :", all_folders)

	if len(all_folders) == 0:
		print("no files found with open() !")
		return []

	# Tirage aléatoire jusqu'à 10 dossiers
	random_folders = random.sample(all_folders, k=min(10, len(all_folders)))
	print("folders selected randomly :", random_folders)

	all_speeds = []

	for folder in random_folders:
		traj_file = folder / "traj.csv"
		print("verification of the file :", traj_file)
		if not traj_file.exists():
			print("file not found :", traj_file)
			continue
		df = pd.read_csv(traj_file)

		# Vérifie que les colonnes x et y existent
		# Vérifie que les colonnes x et y existent
		if "x" not in df.columns or "y" not in df.columns:
			print("column x or y missing in :", traj_file)
			continue

		# Calcul des vitesses
		x = df["x"].values
		y = df["y"].values
		dx = x[1:] - x[:-1]
		dy = y[1:] - y[:-1]
		speed = np.sqrt(dx**2 + dy**2)

		print(f"Speed calculated for {traj_file} :", speed)

	return all_speeds
	


def plot_all_speeds(random_folders):

    plt.figure()

    for file in random_folders:
        
        df = pd.read_csv(traj_file) # lire le csv
        
        frames = df["frames"].values   # colonne frames
        
        speeds = calculs(random_folders)   # ta fonction existante
        
        # moyenne des frames 2 à 2
        frames_mid = (frames[:-1] + frames[1:]) / 2
        
        plt.plot(frames_mid, speeds, alpha=0.6)

    plt.xlabel("Frames")
    plt.ylabel("Speed")
    plt.title("superposition of the speeds of 10 random videos")
    plt.grid()
    plt.show()
    


def manual_annotation(results_path: Path, traj_path: Path):

    results_path = Path(results_path)
    traj_path = Path(traj_path)

    df1 = pd.read_csv(results_path, sep=';', engine='python') # This line reads the CSV file located at results_path into a pandas DataFrame called df1. The sep=None argument allows pandas to automatically detect the separator used in the CSV file (e.g., comma, semicolon, etc.), and engine='python' specifies that the Python engine should be used for parsing the CSV file, which can handle more complex cases than the default C engine.

    df1.columns = ['Folder Path', 'id_conservative', 'manual_annotation', 'Comments']
    traj_files = list(traj_path.rglob("traj.csv")) # rglob() is a method that allows you to search for files in a directory and its subdirectories using a pattern. In this case, it searches for all files named "traj.csv" within the traj_path directory and its subdirectories. The result is a list of Path objects representing the paths to each found "traj.csv" file.

    print("Number of traj.csv found:", len(traj_files))

    fichiers_traites = 0
    fichiers_vides_sautes = 0
    sans_annotation = 0

    for traj_csv in traj_files:
        import os

        # 1. if the file is empty, we skip it and we create an empty processed file to avoid blocking the next scripts
        if os.path.getsize(traj_csv) == 0:
            fichiers_vides_sautes += 1
            # optional : print("Empty file skipped:", traj_csv)
            traj_csv.with_name("traj_processed.csv").touch()
            continue

        # 2. if the file has content : we process it
        try:
            df2 = pd.read_csv(traj_csv)
        except Exception as e:
            # security if the file is not well formatted, we skip it and we create an empty processed file to avoid blocking the next scripts
            fichiers_vides_sautes += 1
            continue

        df2.columns = df2.columns.str.strip()

        folder_path = str(traj_csv.parent.relative_to(traj_path.parent)) # This line calculates the relative path of the parent directory of traj_csv with respect to the parent directory of traj_path. The result is a string representing the relative path from the parent directory of traj_path to the parent directory of traj_csv. This is useful for matching the folder paths in df1 with the corresponding traj.csv files.

        annotation_video = df1[df1["Folder Path"] == folder_path] # This line filters the DataFrame df1 to find the row(s) where the value in the "Folder_Path" column matches the folder_path variable. The result is a new DataFrame annotation_video that contains only the rows corresponding to the current traj.csv file being processed. If there are no matching rows, annotation_video will be an empty DataFrame.

        if annotation_video.empty:
            sans_annotation += 1
            continue

        copie = df2.copy()

        copie = copie.merge(annotation_video[["id_conservative", "manual_annotation"]], on="id_conservative", how="left")
        copie["manual_annotation"] = copie["manual_annotation"].fillna("")

        new_name = traj_csv.with_name("traj_copy.csv") # This line creates a new Path object new_name by taking the original traj_csv Path and replacing its filename with "traj_copy.csv". The with_name() method is used to change the name of the file while keeping the same directory. This means that the new file will be saved in the same location as the original traj.csv but with the name traj_copy.csv.
        copie.to_csv(new_name, index=False) # This line saves the modified DataFrame copie to a new CSV file at the location specified by new_name. The index=False argument is used to prevent pandas from writing row indices to the CSV file, resulting in a cleaner output that only includes the data columns.
        fichiers_traites += 1
        #print("Created:", new_name)

    print("Done!")
    print(f"folders correctly processed and annotated : {fichiers_traites}")
    print(f" empty folders skipped   : {fichiers_vides_sautes}")
    print(f" folders without corresponding annotations   : {sans_annotation}")


def add_filtered_proportion(csv_path):
    # 1. Automatic detection of the separator (, or ;) to avoid KeyError
    with open(csv_path, 'r') as f:
        first_line = f.readline()
    
    separateur = ';' if ';' in first_line else ','
    
    # read the CSV file with the detected separator
    df = pd.read_csv(csv_path, sep=separateur)
    df.columns = df.columns.str.strip()

    # Column from the original file for copying the non-filtered videos
    col_before = 'proportion of frames with multiple worms'
    base_dir = "/Users/noursaad/Desktop/PTUT"
    proportions_after = []
    compteur_trouves = 0

    print("\n---  examination and calculation of filtered videos ---")

    for index, row in df.iterrows():
        folder_path_raw = str(row['Folder Path']).strip()
        folder_path_clean = folder_path_raw.replace('\\', '/')
        
        if "Minipatches_light_20260116" in folder_path_clean:
            if "Minipatches_light_20260116/" in folder_path_clean:
                sub_folder = folder_path_clean.split("Minipatches_light_20260116/")[-1]
            else:
                sub_folder = folder_path_clean
            full_folder_path = os.path.join(base_dir, "Minipatches_light_20260116", sub_folder)
        else:
            full_folder_path = os.path.join(base_dir, "Minipatches_light_20260116", folder_path_clean)
            
        processed_traj_path = os.path.join(full_folder_path, 'traj_copy.csv')
#shouldnt know if it s the thirteen vids, just read traj copy and compute the proportion with the info there. we assume that it s one worm.
        # if the video is part of the filtered videos, we calculate the new proportion of frames with multiple worms after filtering, otherwise we keep the same proportion as before (no change for non-filtered videos)
        if os.path.exists(processed_traj_path):
            compteur_trouves += 1
            try:
                df_traj = pd.read_csv(processed_traj_path)
                df_traj.columns = df_traj.columns.str.strip()

                col_frame = 'frame' if 'frame' in df_traj.columns else ('Frame' if 'Frame' in df_traj.columns else None)
                df_clean = df_traj[df_traj['manual_annotation'] != 'noise']

                if col_frame and not df_clean.empty:
                    counts_per_frame = df_clean.groupby(col_frame).size()
                    multiple_worms = (counts_per_frame > 1).sum()
                    total_frames = counts_per_frame.index.max() + 1
                    prop = multiple_worms / total_frames
                else:
                    prop = 0.0
                
                if compteur_trouves <= 5:
                    print(f"   • Vidéo {compteur_trouves} calculée : {os.path.basename(full_folder_path)} -> {prop}")
                    
            except Exception as e:
                prop = row[col_before] if col_before in df.columns else 0.0
        else:
            # if no filtering is applied, the value remains the same as before
            prop = row[col_before] if col_before in df.columns else 0.0
        
        proportions_after.append(prop)


    # save the new column in the dataframe
    df['proportion of frames with multiple worms after filtering'] = proportions_after
    
    # save the updated dataframe to the same CSV file (overwriting it)
    df.to_csv(csv_path, sep=separateur, index=False)
    print(f" Terminé ! Le fichier {csv_path} a été mis à jour avec succès ({compteur_trouves} fichiers calculés).")


def generate_histograms_all_videos(csv_path):
    with open(csv_path, 'r') as f:
        first_line = f.readline()
    separateur = ';' if ';' in first_line else ','
    
    df = pd.read_csv(csv_path, sep=separateur)
    df.columns = df.columns.str.strip()
    
    col_classification = 'final classification of the video'
    col_before = 'proportion of frames with multiple worms'
    col_after = 'proportion of frames with multiple worms after filtering'

    categories = ['0 worms', '1 worm clean', '1 worm with errors', '2+ worms']

    # 2. creation of the figure with 2 lines and 5 columns (1 for global + 4 for each category)
    fig, axes = plt.subplots(2, 5, figsize=(22, 10))
    fig.suptitle("impact of the spatial filtering on the dataset (Axe Y = Log)", fontsize=16, fontweight='bold')
    #  CORRECTION : we add 1e-6 to avoid the problem of log(0) for the videos that have no duplicated frames, which would make the histogram impossible to read. This way, we can still visualize the distribution of videos with very low duplication rates without losing them in the log scale.
    epsilon = 1e-6
    log_bins = np.logspace(np.log10(1e-6), np.log10(1.0), 50)
    # --- LINE 1 : BEFORE FILTERING (BLUE) ---
    # Global
    data_all_before = df[col_before].dropna() + epsilon
    axes[0, 0].hist(data_all_before, bins=log_bins, color='skyblue', edgecolor='black', log=True)
    axes[0, 0].set_title("All the videos\n(before filtering)", fontweight='bold')
    axes[0, 0].set_ylabel("Number of videos (Log)")
    axes[0, 0].set_xscale('log')
    axes[0, 0].set_xlim(5e-7, 1.2)

    for i, cat in enumerate(categories):
        data_sub = df[df[col_classification] == cat][col_before].dropna() + epsilon
        axes[0, i + 1].hist(data_sub, bins=log_bins, color='skyblue', edgecolor='black', log=True)
        axes[0, i + 1].set_title(f"{cat}\n(before filtering)")
        axes[0, i + 1].set_xscale('log')
        axes[0, i + 1].set_xlim(5e-7, 1.2)
        print(cat)
        print(data_sub)
    # --- LINE 2 : AFTER FILTERING (Salmon) ---
    # Global
    print("AFTER FILTERING - ALL VIDEOS:")
    data_all_after = df[col_after].dropna() + epsilon
    axes[1, 0].hist(data_all_after, bins=log_bins, color='salmon', edgecolor='black', log=True)
    axes[1, 0].set_title("all the videos\n(after filtering)", fontweight='bold')
    axes[1, 0].set_ylabel("number of videos (Log)")
    axes[1, 0].set_xlabel("Proportion of duplicates")
    axes[1, 0].set_xscale('log')
    axes[1, 0].set_xlim(5e-7, 1.2)

    for i, cat in enumerate(categories):
        data_sub = df[df[col_classification] == cat][col_after].dropna() + epsilon
        axes[1, i + 1].hist(data_sub, bins=log_bins, color='salmon', edgecolor='black', log=True)
        axes[1, i + 1].set_title(f"{cat}\n(after filtering)")
        axes[1, i + 1].set_xlabel("Proportion of duplicates")
        axes[1, i + 1].set_xscale('log')
        axes[1, i + 1].set_xlim(5e-7, 1.2)
        print(cat)
        print(data_sub)
    
    plt.tight_layout()
    plt.savefig("filtered_analysis_all_videos_log.png", dpi=300)
    print("Graphiques mis à jour et sauvegardés dans 'filtered_analysis_all_videos_log.png' ")
    plt.show()


def generate_alternative_plots(csv_path):
    with open(csv_path, 'r') as f:
        first_line = f.readline()
    separateur = ';' if ';' in first_line else ','
    df = pd.read_csv(csv_path, sep=separateur)
    df.columns = df.columns.str.strip()
    
    col_class = 'final classification of the video'
    col_before = 'proportion of frames with multiple worms'
    col_after = 'proportion of frames with multiple worms after filtering'

    # create a figure with 1 line and 1 column to compare before vs after filtering for the category "1 worm with errors"
    fig, ax1 = plt.subplots(figsize=(10, 7))
    fig.suptitle("alternative visualization : before vs after filtering", fontsize=16, fontweight='bold', y=0.95)

    # GRAPH 1 :  BOXPLOT 
    df_melted = df.melt(id_vars=[col_class], value_vars=[col_before, col_after], 
                        var_name='Statut', value_name='Proportion')
    df_melted['Statut'] = df_melted['Statut'].replace({col_before: 'before filtering', col_after: 'after filtering'})
    
    # we isolate the category "1 worm with errors" to compare the before vs after filtering for this specific category, which is the one that should be impacted the most by the filtering and where we expect to see the most significant changes in the proportion of duplicated frames. This allows us to focus on the videos that are most likely to benefit from the spatial filtering and to visualize the impact of the filtering on this specific group of videos.
    df_errors = df_melted[df_melted[col_class] == '1 worm with errors']

    sns.boxplot(data=df_errors, x='Statut', y='Proportion', ax=ax1, palette=['skyblue', 'salmon'])
    sns.stripplot(data=df_errors, x='Statut', y='Proportion', ax=ax1, color='black', alpha=0.4, jitter=True) # Ajoute les points réels
    
    ax1.set_title("Boxplot : category '1 worm with errors'", fontweight='bold')
    ax1.set_ylabel("Proportion of frames with duplicates")
    ax1.set_xlabel("")

    plt.tight_layout()
    plt.savefig("analyse_alternatives.png", dpi=300)
    print("New graphs generated in 'analyse_alternatives.png' !")
    plt.show()

def apply_secondary_spatial_filter(csv_path):
    with open(csv_path, 'r') as f:
        first_line = f.readline()
    sep = ';' if ';' in first_line else ','
    
    df_results = pd.read_csv(csv_path, sep=sep)
    df_results.columns = df_results.columns.str.strip()

    col_class = 'final classification of the video'
    col_after = 'proportion of frames with multiple worms after filtering'

    # filtering of the videos : "1 worm..." and also has duplicates (> 0)
    mask_target = df_results[col_class].str.contains('1 worm', na=False, case=False)
    mask_errors = df_results[col_after] > 0.0
    df_target = df_results[mask_target & mask_errors]

    print(f" Phase 2 : {len(df_target)} videos detected as '1 worm with errors' and with duplicates > 0, will be re-annotated with a secondary spatial filter. ")

    base_dir = "/Users/noursaad/Desktop/PTUT"
    
    # --- filtering parameters (Thresholds) ---
    MAX_DEV_THRESHOLD = 5.0       # maximum deviation from the mean position to be considered as "stable" (ex: 5 pixels)
    DIST_TO_NOISE_THRESHOLD = 30.0 # maximum distance to known noise centroids to be considered as "close" (ex: 30 pixels)

    compteur_modifies = 0

    for index, row in df_target.iterrows():
        # reconstruction of the full path to the traj_copy.csv file based on the "Folder Path" column in the results CSV, ensuring that we correctly handle any variations in the folder path format and avoid issues with backslashes or missing subfolder names.
        folder_path = str(row['Folder Path']).strip().replace('\\', '/')
        if "Minipatches_light_20260116" in folder_path:
            sub_folder = folder_path.split("Minipatches_light_20260116/")[-1]
            full_path = os.path.join(base_dir, "Minipatches_light_20260116", sub_folder)
        else:
            full_path = os.path.join(base_dir, "Minipatches_light_20260116", folder_path)

        traj_path = os.path.join(full_path, 'traj_copy.csv')

        if not os.path.exists(traj_path):
            print(f"folder not found, skipping: {os.path.basename(full_path)}")
            continue

        try:
            df_traj = pd.read_csv(traj_path)

            # step A : calculation of the mean position (centroid) for each ID
            means = df_traj.groupby('id_conservative')[['x', 'y']].mean().reset_index()
            means.rename(columns={'x': 'mean_x', 'y': 'mean_y'}, inplace=True)

            # step B : calculation of the maximum deviation for each ID
            df_merged = df_traj.merge(means, on='id_conservative')
            # euclidean distance between each point and the mean position for its ID
            df_merged['dist_to_mean'] = np.sqrt((df_merged['x'] - df_merged['mean_x'])**2 + (df_merged['y'] - df_merged['mean_y'])**2)
            max_devs = df_merged.groupby('id_conservative')['dist_to_mean'].max().reset_index()
            max_devs.rename(columns={'dist_to_mean': 'max_dev'}, inplace=True)

            # regrouping the mean positions and the maximum deviations in a single DataFrame for easier processing in the next steps
            id_stats = means.merge(max_devs, on='id_conservative')

            # step C : Identify the centroids of the existing noise ("noise") instances
            noise_ids = df_traj[df_traj['manual_annotation'] == 'noise']['id_conservative'].unique()
            noise_stats = id_stats[id_stats['id_conservative'].isin(noise_ids)]
            noise_centroids = noise_stats[['mean_x', 'mean_y']].values

            ids_to_noise = []

            # step D : Application of the logical rule
            if len(noise_centroids) > 0:
                for _, stat_row in id_stats.iterrows():
                    id_val = stat_row['id_conservative']
                    
                    # If it's already a noise, we skip
                    if id_val in noise_ids:
                        continue 

                    # Condition 1 : The maximum deviation is below the threshold (Ex: < 5 px)
                    if stat_row['max_dev'] <= MAX_DEV_THRESHOLD:
                        mean_pos = np.array([stat_row['mean_x'], stat_row['mean_y']])
                        
                        # Calculation of the distance to ALL known noises (not just the closest one) to ensure that we correctly identify IDs that are close to any noise instance, which could indicate that they are also noise and should be re-annotated accordingly.
                        distances_to_noises = np.linalg.norm(noise_centroids - mean_pos, axis=1)
                        
                        # Condition 2 : is it close to at least one known noise centroid (Ex: < 30 px) ? If yes, we re-annotate it as "noise"
                        if np.min(distances_to_noises) <= DIST_TO_NOISE_THRESHOLD:
                            ids_to_noise.append(id_val)

            # step E : updating DataFrame and saving the new CSV
            if ids_to_noise:
                df_traj.loc[df_traj['id_conservative'].isin(ids_to_noise), 'manual_annotation'] = 'noise'
                print(f"{len(ids_to_noise)} ID(s) re-classé(s) en 'noise' dans la vidéo {os.path.basename(full_path)}")
                compteur_modifies += 1
            else:
                print(f"➖ no new noise IDs found in {os.path.basename(full_path)}")

            output_path = os.path.join(full_path, 'traj_copy_2.csv')
            df_traj.to_csv(output_path, index=False)

        except Exception as e:
            print(f"error while loading {os.path.basename(full_path)} : {e}")
            
    print(f"\n done ! {compteur_modifies} videos modified and saved to 'traj_copy_2.csv'.")


if __name__ == "__main__": # To prevent the function from running automatically when the file is imported somewhere else
	#create_csv("/Users/noursaad/Desktop/PTUT","results.csv")
	#histogram("results.csv", 0.05)
	#calculs("/home/alvarez/Desktop/PTUT/Minipatches_light_20260116")
	#histogramme_annotate("/home/ibrahim/Bureau/PTUT/results.csv")
	#histogram_MoreThanOneWorm("/home/ibrahim/Bureau/PTUT/results.csv", "/home/ibrahim/Bureau/PTUT/results_manual_annotation.ods")
	#histogram_JustOneWorm("/home/ibrahim/Bureau/PTUT/results.csv", "/home/ibrahim/Bureau/PTUT/results_manual_annotation.ods")
    #manual_annotation(Path("/Users/benitaibrahim/Documents/PTUT/annotation.csv"), Path("/Users/benitaibrahim/Documents/PTUT/Minipatches_light_20260116"))

    #manual_annotation(Path("/Users/noursaad/Desktop/PTUT/results_manual_annotation.csv"), Path("/Users/noursaad/Desktop/PTUT/Minipatches_light_20260116"))
    #add_filtered_proportion('results.csv')
    #generate_histograms_all_videos('/Users/noursaad/Desktop/PTUT/results.csv')
    #generate_alternative_plots('/Users/noursaad/Desktop/PTUT/results.csv')
    #apply_secondary_spatial_filter('/Users/noursaad/Desktop/PTUT/results.csv')