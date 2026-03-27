from pathlib import Path  # pathlib is a module used to work with files and folders , Path: allows you to: navigate through directories and list files and folders
import os # os is a module that allows Python to interact with the operating system
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import pprint as pprint

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
# Vérifier si la colonne existe
	if "proportion of frames with multiple worms" in df.columns:
	#	Boucle sur toutes les lignes
		for el, row in df.iterrows():
			if row["proportion of frames with multiple worms"] < 0.02:
				video = row['Folder Path']
 # Ajouter seulement si pas déjà dans la liste
				if video not in video_annotated:
					video_annotated.append(video)
	print("Vidéos à annoter associées aux frames <20% :")
	pprint.pprint(video_annotated)



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




if __name__ == "__main__": # To prevent the function from running automatically when the file is imported somewhere else
	#create_csv("/home/alvarez/Desktop/PTUT","results.csv")
	#histogram("results.csv", 0.05)
	#calculs("/home/alvarez/Desktop/PTUT/Minipatches_light_20260116")
	histogramme_annotate("/home/ibrahim/Bureau/PTUT/results.csv")



