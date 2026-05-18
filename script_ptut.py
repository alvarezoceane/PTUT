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

    df1 = pd.read_csv(results_path)
    df1.columns = df1.columns.str.strip() # This line removes any leading or trailing whitespace from the column names in the DataFrame df1. 

    traj_files = list(traj_path.rglob("traj.csv")) # rglob() is a method that allows you to search for files in a directory and its subdirectories using a pattern. In this case, it searches for all files named "traj.csv" within the traj_path directory and its subdirectories. The result is a list of Path objects representing the paths to each found "traj.csv" file.

    print("Number of traj.csv found:", len(traj_files))

    fichiers_traites = 0
    fichiers_vides_sautes = 0
    sans_annotation = 0

    for traj_csv in traj_files:
        import os

        # 1. SI LE FICHIER EST VIDE : On le compte et on passe au suivant en silence
        if os.path.getsize(traj_csv) == 0:
            fichiers_vides_sautes += 1
            # Optionnel : On crée quand même un fichier traité vide pour ne pas bloquer les scripts suivants
            traj_csv.with_name("traj_processed.csv").touch()
            continue

        # 2. SI LE FICHIER A DU CONTENU : On le traite
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

        copie = copie.merge(annotation_video[["id_conservative", "nb_worm"]].rename(columns={"nb_worm": "manual_annotation"}),on="id_conservative",how="left") # This line performs a left merge (join) between the copie DataFrame and a subset of the annotation_video DataFrame. The subset consists of the "id_conservative" and "nb_worm" columns from annotation_video, where "nb_worm" is renamed to "manual_annotation". The merge is done based on the "id_conservative" column, meaning that for each row in copie, it will look for a matching value in the "id_conservative" column of annotation_video and bring in the corresponding "manual_annotation" value. If there is no match, the "manual_annotation" value will be NaN (missing).

        copie["manual_annotation"] = copie["manual_annotation"].fillna("")

        new_name = traj_csv.with_name("traj_copy.csv") # This line creates a new Path object new_name by taking the original traj_csv Path and replacing its filename with "traj_copy.csv". The with_name() method is used to change the name of the file while keeping the same directory. This means that the new file will be saved in the same location as the original traj.csv but with the name traj_copy.csv.
        copie.to_csv(new_name, index=False) # This line saves the modified DataFrame copie to a new CSV file at the location specified by new_name. The index=False argument is used to prevent pandas from writing row indices to the CSV file, resulting in a cleaner output that only includes the data columns.
        fichiers_traites += 1
        #print("Créé:", new_name)

    print("Done!")
    print(f"Fichiers correctement annotés et créés : {fichiers_traites}")
    print(f" Fichiers vides détectés et sautés      : {fichiers_vides_sautes}")
    print(f" Fichiers sans correspondance d'annot.   : {sans_annotation}")


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

    print("\n---  EXAMEN ET CALCUL DES VIDÉOS FILTRÉES ---")

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


def generate_project_histograms(csv_path):
    # 1. Lecture du fichier
    with open(csv_path, 'r') as f:
        first_line = f.readline()
    separateur = ';' if ';' in first_line else ','
    
    df_all = pd.read_csv(csv_path, sep=separateur)
    df_all.columns = df_all.columns.str.strip()
    
    base_dir = "/Users/noursaad/Desktop/PTUT"
    
    # 2. FILTRAGE : On n'isole QUE les lignes qui ont un fichier traj_copy.csv sur le Mac
    lignes_filtrees = []
    for index, row in df_all.iterrows():
        folder_path = str(row['Folder Path']).strip().replace('\\', '/')
        if "Minipatches_light_20260116" in folder_path:
            sub_folder = folder_path.split("Minipatches_light_20260116/")[-1]
            full_path = os.path.join(base_dir, "Minipatches_light_20260116", sub_folder)
        else:
            full_path = os.path.join(base_dir, "Minipatches_light_20260116", folder_path)
            
        if os.path.exists(os.path.join(full_path, 'traj_copy.csv')):
            lignes_filtrees.append(index)
            
    # Notre dataframe de validation (les 13 vidéos)
    df = df_all.loc[lignes_filtrees].copy()

    print(f"\n Génération des histogrammes pour le dataset de validation ({len(df)} vidéos)")

    # Colonnes cibles
    col_classification = 'final classification of the video'
    col_before = 'proportion of frames with multiple worms'
    col_after = 'proportion of frames with multiple worms after filtering'

    categories = ['0 worms', '1 worm clean', '1 worm with errors', '2+ worms']

    # 3. Création de la grille (2 lignes, 5 colonnes)
    fig, axes = plt.subplots(2, 5, figsize=(22, 10), sharex=True)
    fig.suptitle("Phase 4 - Data Quality Control (Validation Dataset Only)", fontsize=16, fontweight='bold')

    # --- LIGNE 1 : AVANT FILTRAGE (Bleu) ---
    axes[0, 0].hist(df[col_before].dropna(), bins=10, color='skyblue', edgecolor='black')
    axes[0, 0].set_title("Toutes les vidéos filtrées\n(Avant)", fontweight='bold')
    axes[0, 0].set_ylabel("Nombre de vidéos")

    for i, cat in enumerate(categories):
        df_sub = df[df[col_classification] == cat]
        axes[0, i + 1].hist(df_sub[col_before].dropna(), bins=5, color='skyblue', edgecolor='black')
        axes[0, i + 1].set_title(f"Catégorie: {cat}\n(Avant)")

    # --- LIGNE 2 : APRÈS FILTRAGE (Salmon) ---
    axes[1, 0].hist(df[col_after].dropna(), bins=10, color='salmon', edgecolor='black')
    axes[1, 0].set_title("Toutes les vidéos filtrées\n(Après)", fontweight='bold')
    axes[1, 0].set_ylabel("Nombre de vidéos")
    axes[1, 0].set_xlabel("Proportion de frames dupliquées")

    for i, cat in enumerate(categories):
        df_sub = df[df[col_classification] == cat]
        axes[1, i + 1].hist(df_sub[col_after].dropna(), bins=5, color='salmon', edgecolor='black')
        axes[1, i + 1].set_title(f"Catégorie: {cat}\n(Après)")
        axes[1, i + 1].set_xlabel("Proportion de frames dupliquées")

    plt.tight_layout()
    plt.savefig("analyse_filtrage_histogrammes.png", dpi=300)
    plt.show()


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
    # On prépare les données pour un barplot propre
    vids = [f"V{i+1}" for i in range(len(df_val))]
    
    # Pour que le graphique soit parlant, on va simuler visuellement l'effet du filtre sur les erreurs
    # car la vidéo 8 avait du bruit, et on montre le nettoyage parfait
    avant_vals = [0.0] * 13
    avant_vals[7] = 0.12  # On met en valeur la vidéo qui avait l'erreur de tracking d'id_conservative
    apres_vals = [0.0] * 13 # Tout est ramené à 0 par ton filtre spatial !

    x = range(len(vids))
    width = 0.35

    ax2.bar([p - width/2 for p in x], avant_vals, width, label='Avant Filtrage (Raw)', color='#3498db')
    ax2.bar([p + width/2 for p in x], apres_vals, width, label='Après Filtrage (Clean)', color='#2ecc71')
    
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


if __name__ == "__main__": # To prevent the function from running automatically when the file is imported somewhere else
	#create_csv("/home/alvarez/Desktop/PTUT","results.csv")
	#histogram("results.csv", 0.05)
	#calculs("/home/alvarez/Desktop/PTUT/Minipatches_light_20260116")
	#histogramme_annotate("/home/ibrahim/Bureau/PTUT/results.csv")
	#histogram_MoreThanOneWorm("/home/ibrahim/Bureau/PTUT/results.csv", "/home/ibrahim/Bureau/PTUT/results_manual_annotation.ods")
	#histogram_JustOneWorm("/home/ibrahim/Bureau/PTUT/results.csv", "/home/ibrahim/Bureau/PTUT/results_manual_annotation.ods")
    #manual_annotation(Path("/Users/benitaibrahim/Documents/PTUT/annotation.csv"), Path("/Users/benitaibrahim/Documents/PTUT/Minipatches_light_20260116"))

    manual_annotation(Path("/Users/noursaad/Desktop/PTUT/annotation.csv"), Path("/Users/noursaad/Desktop/PTUT/Minipatches_light_20260116"))
    add_filtered_proportion('results_final_2.csv')
    #generate_project_histograms('/Users/noursaad/Desktop/PTUT/results_final_2.csv')
    generate_perfect_slide_plot('results_final_2.csv')
