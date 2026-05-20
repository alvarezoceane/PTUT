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
    data = Path("/home/ibrahim/Bureau/Minipatches_light_20260116") # Path is used to set our current working directory
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
    
    base = Path.home() / "Bureau" 
    output_folder = base / "PTUT"
    output_folder.mkdir(exist_ok=True)

    output_path = output_folder / file_name
    
    if output_path.exists():
        print(f"The file already exists : {output_path}")
        return 

    # Colonnes du CSV
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

    data = Path("/home/ibrahim/Bureau/Minipatches_light_20260116")
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
	# Lire le fichier CSV
	df = pd.read_csv(file_path)
	# Vérifier si la colonne existe dans le DataFrame
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
# Vérifier si la colonne existe
	if "proportion of frames with multiple worms" in df.columns:
	#	Boucle sur toutes les lignes
		for el, row in df.iterrows():
			if row["proportion of frames with multiple worms"] < 0.2:
				video = row['Folder Path']
				proportion1 = row["proportion of frames with multiple worms"] 
 # Ajouter seulement si pas déjà dans la liste
				if video not in video_annotated:
					video_annotated.append(video)
					proportion.append(proportion1)
	print("Vidéos à annoter associées aux frames <20% :")
	#pprint.pprint(video_annotated + proportion )
	# Boucle directe
	for idx, row in df.iterrows():
		if row["proportion of frames with multiple worms"] < 0.2:
			pprint.pprint(f"{row['Folder Path']}  ->  {row['proportion of frames with multiple worms']:.3f}")


def histogram_JustOneWorm(csv_path, ods_path) : 
# Charger les fichiers
	df_comments = pd.read_excel("results_manual_annotation.ods", engine="odf")
	df_results = pd.read_csv("results.csv")
	#print(df_comments.columns)
	#print(df_results.columns)
# 1. Filtrer les vidéos "1 worm"
	df_1worm = df_comments[df_comments["Comments"].str.contains("1 worm", na=False)]
# 2. Récupérer les chemins uniques
	paths_1worm = df_1worm["Path to each video"].unique()
# 3. Filtrer le fichier results
	df_filtered = df_results[df_results["Path to each video"].isin(paths_1worm)]
# 4. Récupérer les proportions
	proportions = df_filtered["proportion of frames with multiple worms"]
	print("Unique videos in results:", df_results["Path to each video"].nunique())
	print("Unique videos after filtering:", df_filtered["Path to each video"].nunique())
	print(proportions)
# Histogramme
	plt.hist(proportions, bins=10)
	plt.xlabel("Proportion of duplicated frames")
	plt.ylabel("Number of videos")
	plt.title("Histogram - 1 worm videos only")
	plt.show()

def histogram_MoreThanOneWorm(csv_path, ods_path) : 
# Charger les fichiers
	df_comments = pd.read_excel("results_manual_annotation.ods", engine="odf")
	df_results = pd.read_csv("results.csv")
	#print(df_comments.columns)
	#print(df_results.columns)
# 1. Filtrer les vidéos "1 worm"
	df_MoreThan1Worm = df_comments[(df_comments["Comments"].str.contains("1 worm", na=False) == False) &
	(df_comments["Comments"].str.contains("no traj.csv", na=False) == False)]
# 2. Récupérer les chemins uniques
	paths_MoreThan1Worm = df_MoreThan1Worm["Path to each video"].unique()
# 3. Filtrer le fichier results
	df_filtered = df_results[df_results["Path to each video"].isin(paths_MoreThan1Worm)]
# 4. Récupérer les proportions
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
	all_folders = list(open_folders())  # open() sans argument
	#print("Dossiers trouvés :", all_folders)

	if len(all_folders) == 0:
		print("Aucun dossier trouvé par open() !")
		return []

	# Tirage aléatoire jusqu'à 10 dossiers
	random_folders = random.sample(all_folders, k=min(10, len(all_folders)))
	print("Dossiers tirés au hasard :", random_folders)

	all_speeds = []

	for folder in random_folders:
		traj_file = folder / "traj.csv"
		print("Vérification du fichier :", traj_file)
		if not traj_file.exists():
			print("Fichier non trouvé :", traj_file)
			continue
		df = pd.read_csv(traj_file)

		# Vérifie que les colonnes x et y existent
		# Vérifie que les colonnes x et y existent
		if "x" not in df.columns or "y" not in df.columns:
			print("Colonnes x ou y manquantes dans :", traj_file)
			continue

		# Calcul des vitesses
		x = df["x"].values
		y = df["y"].values
		dx = x[1:] - x[:-1]
		dy = y[1:] - y[:-1]
		speed = np.sqrt(dx**2 + dy**2)

		print(f"Vitesse calculée pour {traj_file} :", speed)

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
    plt.title("Superposition des 10 trajectoires")
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

        #if the file is empty, we skip it and count it to avoid blocking the script, as some folders are empty and we dont want to lose time on them
        if os.path.getsize(traj_csv) == 0:
            fichiers_vides_sautes += 1
            # Optionnel : On crée quand même un fichier traité vide pour ne pas bloquer les scripts suivants
            traj_csv.with_name("traj_processed.csv").touch()
            continue

        #if the file is not empty but corrupted, we skip it and count it as well to avoid blocking the script
        try:
            df2 = pd.read_csv(traj_csv)
        except Exception as e:
            # Sécurité si un fichier n'est pas vide mais corrompu
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
        #print("Créé:", new_name)

    print("Done!")
    print(f"folders correctly processed and annotated : {fichiers_traites}")
    print(f" empty folders skipped   : {fichiers_vides_sautes}")
    print(f" folders without corresponding annotations   : {sans_annotation}")


def add_filtered_proportion(csv_path):
    # 1. Détection automatique du séparateur (, ou ;) pour éviter le KeyError
    with open(csv_path, 'r') as f:
        first_line = f.readline()
    
    separateur = ';' if ';' in first_line else ','
    
    # Lecture propre du fichier
    df = pd.read_csv(csv_path, sep=separateur)
    df.columns = df.columns.str.strip()

    # Colonne d'origine pour la recopie des vidéos non filtrées
    col_before = 'proportion of frames with multiple worms'
    base_dir = "/Users/noursaad/Desktop/PTUT"
    proportions_after = []
    compteur_trouves = 0

    print("\n---  examination and calculation of filtered videos ---")

    for index, row in df.iterrows():
        # Utilisation de ton nom de colonne exact : 'Folder Path'
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
        # Si la vidéo fait partie des 13 vidéos annotées
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
                    total_frames = counts_per_frame.nunique()
                    prop = multiple_worms / total_frames
                else:
                    prop = 0.0
                
                if compteur_trouves <= 5:
                    print(f"   • Vidéo {compteur_trouves} calculée : {os.path.basename(full_folder_path)} -> {prop}")
                    
            except Exception as e:
                prop = row[col_before] if col_before in df.columns else 0.0
        else:
            # Si pas de filtre, la valeur reste la même qu'avant
            prop = row[col_before] if col_before in df.columns else 0.0
        
        proportions_after.append(prop)


    # Enregistrement de la nouvelle colonne
    df['proportion of frames with multiple worms after filtering'] = proportions_after
    
    # Sauvegarde en conservant le séparateur d'origine
    df.to_csv(csv_path, sep=separateur, index=False)
    print(f" Terminé ! Le fichier {csv_path} a été mis à jour avec succès ({compteur_trouves} fichiers calculés).")


def generate_perfect_slide_plot(csv_path):

    # 1. Lecture du fichier
    with open(csv_path, 'r') as f:
        first_line = f.readline()
    separateur = ';' if ';' in first_line else ','
    df_all = pd.read_csv(csv_path, sep=separateur)
    df_all.columns = df_all.columns.str.strip()
    
    base_dir = "/Users/noursaad/Desktop/PTUT"
    col_before = 'proportion of frames with multiple worms'
    col_after = 'proportion of frames with multiple worms after filtering'

    # 2. Identification of the 13 videos with traj_copy.csv for the validation dataset
    validation_indices = []
    for index, row in df_all.iterrows():
        folder_path = str(row['Folder Path']).strip().replace('\\', '/')
        if "Minipatches_light_20260116" in folder_path:
            sub_folder = folder_path.split("Minipatches_light_20260116/")[-1]
            full_path = os.path.join(base_dir, "Minipatches_light_20260116", sub_folder)
        else:
            full_path = os.path.join(base_dir, "Minipatches_light_20260116", folder_path)
            
        if os.path.exists(os.path.join(full_path, 'traj_copy.csv')):
            validation_indices.append(index)
            
    df_val = df_all.loc[validation_indices].copy()

    # 3. Préparation de la figure (1 ligne, 2 graphiques)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle("Phase 4 - Controle Quality and Validation of the Spatial Filtering ", fontsize=16, fontweight='bold', y=0.98)
    # --- GRAPHIQUE 1 (À GAUCHE) : La masse des données du projet ---
    ax1.hist(df_all[col_before].dropna(), bins=20, color='#34495e', edgecolor='white', alpha=0.9)
    ax1.set_title(f"Dataset Global ({len(df_all)} analysed videos)", fontsize=12, fontweight='bold')
    ax1.set_xlabel("Proportion of duplicated frames (initial noise level)")
    ax1.set_ylabel("number of videos")
    ax1.grid(axis='y', linestyle='--', alpha=0.7)

    # --- GRAPHIQUE 2 (À DROITE) : Le zoom sur l'efficacité du filtre (Avant vs Après) ---
    vids = [f"V{i+1}" for i in range(len(df_val))]
    
    avant_vals = df_val[col_before].tolist()
    apres_vals = df_val[col_after].tolist() 

    x = range(len(vids))
    width = 0.35

    ax2.bar([p - width/2 for p in x], avant_vals, width, label='before filtering (Raw)', color='#3498db')
    ax2.bar([p + width/2 for p in x], apres_vals, width, label='after filtering (Clean)', color='#2ecc71')
    
    ax2.set_title(f"validation dataset ({len(df_val)} analysed videos)", fontsize=12, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(vids)
    ax2.set_xlabel("Manually Annotated Videos")
    ax2.set_ylabel("Error Rate (Duplicated Frames)")
    ax2.set_ylim(0, 0.2)
    ax2.legend()
    ax2.grid(axis='y', linestyle='--', alpha=0.5)

    plt.tight_layout()
    plt.savefig("perfect_slide_plot.png", dpi=300)
    plt.show()

def generate_histograms_all_videos(csv_path):
    # 1. Lecture du fichier (détection , ou ;)
    with open(csv_path, 'r') as f:
        first_line = f.readline()
    separateur = ';' if ';' in first_line else ','
    
    df = pd.read_csv(csv_path, sep=separateur)
    df.columns = df.columns.str.strip()
    
    col_classification = 'final classification of the video'
    col_before = 'proportion of frames with multiple worms'
    col_after = 'proportion of frames with multiple worms after filtering'

    categories = ['0 worms', '1 worm clean', '1 worm with errors', '2+ worms']

    # 2. Création de la grille (2 lignes, 5 colonnes)
    fig, axes = plt.subplots(2, 5, figsize=(22, 10))
    fig.suptitle("impact of the spatial filtering on the dataset (Axe Y = Log)", fontsize=16, fontweight='bold')
    #  CORRECTION : we add 1e-6 to avoid the problem of log(0) for the videos that have no duplicated frames, which would make the histogram impossible to read. This way, we can still visualize the distribution of videos with very low duplication rates without losing them in the log scale.
    epsilon = 1e-6

    # --- LIGNE 1 : AVANT FILTRAGE (Bleu) ---
    # Global
    data_all_before = df[col_before].dropna() + epsilon
    axes[0, 0].hist(data_all_before, bins=30, color='skyblue', edgecolor='black', log=True)
    axes[0, 0].set_title("all the videos\n(before filtering)", fontweight='bold')
    axes[0, 0].set_ylabel("number of videos (Log)")

    # Par Catégorie
    for i, cat in enumerate(categories):
        data_sub = df[df[col_classification] == cat][col_before].dropna() + epsilon
        axes[0, i + 1].hist(data_sub, bins=30, color='skyblue', edgecolor='black', log=True)
        axes[0, i + 1].set_title(f"{cat}\n(before filtering)")
        print(cat)
        print(data_sub)
    # --- LIGNE 2 : APRÈS FILTRAGE (Saumon) ---
    # Global
    print("AFTER FILTERING - ALL VIDEOS:")
    data_all_after = df[col_after].dropna() + epsilon
    axes[1, 0].hist(data_all_after, bins=30, color='salmon', edgecolor='black', log=True)
    axes[1, 0].set_title("all the videos\n(after filtering)", fontweight='bold')
    axes[1, 0].set_ylabel("number of videos (Log)")
    axes[1, 0].set_xlabel("Proportion of duplicates")

    # Par Catégorie
    for i, cat in enumerate(categories):
        data_sub = df[df[col_classification] == cat][col_after].dropna() + epsilon
        axes[1, i + 1].hist(data_sub, bins=30, color='salmon', edgecolor='black', log=True)
        axes[1, i + 1].set_title(f"{cat}\n(after filtering)")
        axes[1, i + 1].set_xlabel("Proportion of duplicates")
        print(cat)
        print(data_sub)
    # Ajustement visuel
    plt.tight_layout()
    plt.savefig("filtered_analysis_all_videos_log.png", dpi=300)
    print("Graphiques mis à jour et sauvegardés dans 'filtered_analysis_all_videos_log.png' ")
    plt.show()


def generate_alternative_plots(csv_path):
    # 1. Lecture du fichier
    with open(csv_path, 'r') as f:
        first_line = f.readline()
    separateur = ';' if ';' in first_line else ','
    df = pd.read_csv(csv_path, sep=separateur)
    df.columns = df.columns.str.strip()
    
    col_class = 'final classification of the video'
    col_before = 'proportion of frames with multiple worms'
    col_after = 'proportion of frames with multiple worms after filtering'

    # Création de la figure (1 ligne, 2 colonnes)
    fig, ax1 = plt.subplots(figsize=(10, 7))
    fig.suptitle("alternative visualization : before vs after filtering", fontsize=16, fontweight='bold', y=0.95)

    # GRAPHIQUE 1 :  BOXPLOT 
    df_melted = df.melt(id_vars=[col_class], value_vars=[col_before, col_after], 
                        var_name='Statut', value_name='Proportion')
    df_melted['Statut'] = df_melted['Statut'].replace({col_before: 'before filtering', col_after: 'after filtering'})
    
    # On isole la catégorie "1 worm with errors" pour bien voir l'effet du nettoyage
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
        # Reconstruction propre du chemin absolu
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
            # Lecture de traj_copy.csv
            df_traj = pd.read_csv(traj_path)

            # Étape A : Calcul de la position moyenne pour chaque ID
            means = df_traj.groupby('id_conservative')[['x', 'y']].mean().reset_index()
            means.rename(columns={'x': 'mean_x', 'y': 'mean_y'}, inplace=True)

            # Étape B : Calcul de la déviation maximale pour chaque ID
            df_merged = df_traj.merge(means, on='id_conservative')
            # Distance Euclidienne entre chaque frame et la position moyenne
            df_merged['dist_to_mean'] = np.sqrt((df_merged['x'] - df_merged['mean_x'])**2 + (df_merged['y'] - df_merged['mean_y'])**2)
            max_devs = df_merged.groupby('id_conservative')['dist_to_mean'].max().reset_index()
            max_devs.rename(columns={'dist_to_mean': 'max_dev'}, inplace=True)

            # Regroupement des statistiques (Position Moyenne + Max Deviation)
            id_stats = means.merge(max_devs, on='id_conservative')

            # Étape C : Identifier les centroïdes des bruits ("noise") déjà existants
            noise_ids = df_traj[df_traj['manual_annotation'] == 'noise']['id_conservative'].unique()
            noise_stats = id_stats[id_stats['id_conservative'].isin(noise_ids)]
            noise_centroids = noise_stats[['mean_x', 'mean_y']].values

            ids_to_noise = []

            # Étape D : Application de la règle logique
            if len(noise_centroids) > 0:
                for _, stat_row in id_stats.iterrows():
                    id_val = stat_row['id_conservative']
                    
                    # Si c'est déjà un noise, on passe
                    if id_val in noise_ids:
                        continue 

                    # Condition 1 : La déviation maximale est sous le threshold (Ex: < 5 px)
                    if stat_row['max_dev'] <= MAX_DEV_THRESHOLD:
                        mean_pos = np.array([stat_row['mean_x'], stat_row['mean_y']])
                        
                        # Calcul de la distance vers TOUS les bruits connus
                        distances_to_noises = np.linalg.norm(noise_centroids - mean_pos, axis=1)
                        
                        # Condition 2 : Est-ce proche d'au moins un bruit ?
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


# The goal is to create a script that reads results_final.csv, which contains summary information for all videos, including the column “proportion of frames with multiple worms after filtering”. The script should focus only on videos classified as “1 worm clean” or “1 worm with errors”, and identify those where this proportion is not equal to 0, meaning that duplicated frames still remain after filtering. For each of these videos, the script should use the corresponding Folder Path to enter the video folder and open traj_copy.csv, which contains trajectory information (id_conservative, frame, x, y, manual_annotation, etc.). For every individual (id_conservative), the script computes its average position by taking the mean of its x and y coordinates, and computes its maximum deviation by measuring, at each frame, the distance between the current position and the average position, then keeping the maximum value. Next, the script extracts the average positions of all individuals already tagged as noise and uses them as spatial references. Any individual whose average position is sufficiently close to one of these noise positions (below a distance threshold), and whose maximum deviation is also below a movement threshold (around 5 pixels), is considered stable and similar to known noise and is therefore reclassified as noise. Finally, a new file called traj_copy_2.csv is created in the corresponding video folder, containing the updated annotations. This second filtering step uses average position and movement information to distinguish remaining noise from real worms and further reduce duplicated frames after filtering.

def compute_individual_stats(df):
    stats = []
    for id_value, group in df.groupby("id_conservative"): # This line groups the DataFrame df by the values in the "id_conservative" column. The groupby() method is used to create groups of rows that share the same value in the "id_conservative" column. The result is an iterable of (id_value, group) pairs, where id_value is a unique value from the "id_conservative" column and group is a DataFrame containing all rows that have that id_value.
        avg_x = group["x"].mean()
        avg_y = group["y"].mean()
        distances = np.sqrt((group["x"] - avg_x) ** 2 +(group["y"] - avg_y) ** 2)
        max_deviation = distances.max()
        annotation = group["manual_annotation"].iloc[0] # This line retrieves the first value from the "manual_annotation" column of the group DataFrame that contains the data for that specific id_value.
        stats.append({
            "id_conservative": id_value,
            "avg_x": avg_x,
            "avg_y": avg_y,
            "max_deviation": max_deviation,
            "manual_annotation": annotation})
    return pd.DataFrame(stats)


def clean_remaining_noise(results_final_path,position_threshold=5,movement_threshold=5):
    results = pd.read_csv(results_final_path, sep=None, engine="python")
    results.columns = results.columns.str.strip()
    prop_col = "proportion of frames with multiple worms after filtering"
    
    category_col = "final classification of the video"
    results[category_col] = (results[category_col].astype(str).str.strip().str.lower())
    videos_to_fix = results[(results[prop_col].fillna(0).astype(float) != 0)& (results[category_col].isin(["1 worm clean","1 worm with errors"]))] # This line filters the results DataFrame to identify videos that still have a non-zero proportion of frames with multiple worms after filtering, and whose final classification is either "1 worm clean" or "1 worm with errors". The condition checks if the value in the prop_col column (proportion of frames with multiple worms after filtering) is not equal to zero (after filling NaN values with 0 and converting to float), and if the value in the category_col column (final classification of the video) is either "1 worm clean" or "1 worm with errors". The resulting videos_to_fix DataFrame will contain only those videos that meet these criteria, indicating that they may still have issues with noise that need to be addressed.
    print("Videos to fix:", len(videos_to_fix))
    for _ , row in videos_to_fix.iterrows(): # This loop iterates over each row in the videos_to_fix DataFrame, allowing you to process each video that still has a non-zero proportion of frames with multiple worms. The iterrows() method is used to iterate through the rows of the DataFrame, providing both the index and the row data for each iteration. Inside the loop, you can access the folder path and other relevant information for each video to perform further analysis and cleaning.
        folder = Path(row["Folder Path"])
        traj_copy = folder / "traj_copy.csv"
        if not traj_copy.exists():
            print("Missing traj_copy.csv:", traj_copy)
            continue
        print("Processing:", traj_copy)
        
        df = pd.read_csv(traj_copy, sep=None, engine="python")
        df.columns = df.columns.str.strip()
        df["manual_annotation"] = df["manual_annotation"].astype(str).str.strip()
        stats = compute_individual_stats(df)
        stats["manual_annotation"] = (
    stats["manual_annotation"]
    .fillna("")
    .astype(str)
    .str.strip()
)
        noise_stats = stats[stats["manual_annotation"].str.lower() == "noise"] # 

        if noise_stats.empty:
            print("No noise ids found in:", folder)
            continue

        for _, individual in stats.iterrows():
            if str(individual["manual_annotation"]).lower() == "noise":
                continue
            distances_to_noise = np.sqrt((noise_stats["avg_x"] - individual["avg_x"]) ** 2 + (noise_stats["avg_y"] - individual["avg_y"]) ** 2)
            min_distance_to_noise = distances_to_noise.min()
            if (min_distance_to_noise < position_threshold and individual["max_deviation"] < movement_threshold):
                id_to_change = individual["id_conservative"]
                df.loc[df["id_conservative"] == id_to_change,"manual_annotation"] = "noise"
                print( "Tagged as noise:",id_to_change,"| distance to noise:",min_distance_to_noise, "| max deviation:",individual["max_deviation"])

        new_path = folder / "traj_copy_2.csv"
        df.to_csv(new_path, index=False)
        print("Created:", new_path)
    print("Done.")
    
    
if __name__ == "__main__": # To prevent the function from running automatically when the file is imported somewhere else
	#create_csv("/home/alvarez/Desktop/PTUT","results.csv")
	#histogram("results.csv", 0.05)
	#calculs("/home/alvarez/Desktop/PTUT/Minipatches_light_20260116")
	#histogramme_annotate("/home/ibrahim/Bureau/PTUT/results.csv")
	#histogram_MoreThanOneWorm("/home/ibrahim/Bureau/PTUT/results.csv", "/home/ibrahim/Bureau/PTUT/results_manual_annotation.ods")
	#histogram_JustOneWorm("/home/ibrahim/Bureau/PTUT/results.csv", "/home/ibrahim/Bureau/PTUT/results_manual_annotation.ods")
    #manual_annotation(Path("/Users/benitaibrahim/Documents/PTUT/annotation.csv"), Path("/Users/benitaibrahim/Documents/PTUT/Minipatches_light_20260116"))

    #manual_annotation(Path("/Users/noursaad/Desktop/PTUT/results_manual_annotation_2.csv"), Path("/Users/noursaad/Desktop/PTUT/Minipatches_light_20260116"))
    #add_filtered_proportion('results_final_new.csv')
    #generate_perfect_slide_plot('results_final_new.csv')
    generate_histograms_all_videos('/Users/noursaad/Desktop/PTUT/results_final_new.csv')
    generate_alternative_plots('/Users/noursaad/Desktop/PTUT/results_final_new.csv')
    #apply_secondary_spatial_filter('/Users/noursaad/Desktop/PTUT/results_final_new.csv')
    #clean_remaining_noise("/Users/benitaibrahim/Documents/PTUT/results_final_2.csv", position_threshold=5, movement_threshold=5)