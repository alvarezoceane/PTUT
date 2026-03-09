import os
import glob
import scipy
import re
import numpy as np
import sys
import numpy as np
from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtCore import Qt, QRect, QRectF, QPoint, QSize
from PyQt6.QtGui import QImage, QPixmap, QPainter, QAction
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QSlider, QLineEdit,
    QHBoxLayout, QVBoxLayout, QMessageBox, QRubberBand
)
from video_tools import FullVideo

def extract_middle_frame(folder):
    import cv2
    mkv_files = sorted(f for f in os.listdir(folder) if f.lower().endswith(".mkv"))
    if not mkv_files:
        raise ValueError("No MKV files found")

    video_path = os.path.join(folder, mkv_files[len(mkv_files) // 2])

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Cannot open video: {video_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames // 2)

    ret, frame = cap.read()
    cap.release()

    if not ret:
        raise IOError("Could not read frame")

    return frame, video_path

class FrameBuffer:    
    def __init__(self, max_frames):
        from collections import deque
        self.order = deque()
        self.frames = {}
        self.max_frames = max_frames

    def add_frame(self, frame_id, frame):
        # If frame already exists, do nothing or overwrite
        if frame_id in self.frames:
            return

        self.order.append(frame_id)
        self.frames[frame_id] = frame

        # Evict oldest
        if len(self.order) > self.max_frames:
            oldest_id = self.order.popleft()
            del self.frames[oldest_id]

    def get_frame(self, frame_id):
        return self.frames.get(frame_id, None)


@dataclass
class TierpsyVideo:
    import h5py
    f: h5py.File
    dset: h5py.Dataset

    def frame(self, i: int) -> np.ndarray:
        # copy=True so the returned array is usable after any internal buffering
        return self.dset[i].astype(np.uint8, copy=True)

    @property
    def n_frames(self) -> int:        
        return int(self.dset.shape[0]) - 1 # Because tierpsy repeats the last timestamp

    def close(self) -> None:
        self.f.close()

def open_tierpsy_video(h5_path, dataset: str = "mask") -> TierpsyVideo:
    import h5py
    h5_path = str(Path(h5_path))
    f = h5py.File(h5_path, "r")          # keep open    
    if dataset not in f:
        f.close()
        raise KeyError(f"Dataset '{dataset}' not found. Available: {list(f.keys())}")
    dset = f[dataset]
    if dset.ndim != 3:
        f.close()
        raise ValueError(f"Expected (n_frames,H,W). Got {dset.shape} for '{dataset}'.")
    ## Check that the last timestamp is duplicated
    #ts = dset["timestamp"]        
    #if ts["raw"].size >= 2 and ts["raw"][-1] != ts["raw"][-2]: # For some reason, tierpsy duplicates the last timestamp. We check that this is the case, and subtract one frame
    #    raise RuntimeError("THIS IS WEIRD: The last timestamp of the tierpsy file is not duplicated.")
    return TierpsyVideo(f=f, dset=dset)

@dataclass
class SilhouetteVideo:
    file: str
    intensities: list
    pixels: list
    frame_size: np.array
    background: np.array
    silhouette2frame: np.array

    def frame(self, i: int, color="black", background="real") -> np.ndarray:
        if background == "real" and self.background is not None:
            frame = self.background.copy()
        else:
            frame = np.full(self.frame_size, np.uint8(255))
        values = 0 # Default color
        ids_sil = np.where(self.silhouette2frame == i)
        #print(ids_sil[0])
        #print(len(ids_sil))
        #print(np.sum(np.sum(frame)))
        if len(ids_sil[0]) > 0:
            flat = frame.ravel(order="F")
            for i_sil in ids_sil[0]:            
                if color == "real":
                    # print(i_sil)                    
                    #print(len(self.intensities[int(i_sil)]))
                    values = self.intensities[int(i_sil)]                
                flat[self.pixels[i_sil]] = values
            frame[:] = flat.reshape(frame.shape, order="F")                        
        #print(np.sum(np.sum(frame)))
        return frame

    @property
    def n_frames(self) -> int:
        #print(len(self.pixels))
        #caca
        #print(int(np.shape(self.pixels)))
        #caca
        n_frames = int(len(self.pixels))
        #print(n_frames)
        #caca
        return n_frames # Because tierpsy repeats the last timestamp

def open_silhouettes(file):
    import pandas as pd
    data = scipy.io.loadmat(file)
    frame_size = data["frame_size"]
    #print(np.transpose(np.array(data["pixels"][0][0]))[0])
    #print(np.shape(data["pixels"][0][0]))
    #print(data["pixels"][1][0][0])
    pixels = [np.transpose(np.array(x[0]))[0] for x in data["pixels"]]
    intensities = [np.transpose(np.array(x[0]))[0] for x in data["intensities"]]
    try:
        data = pd.read_csv(Path(file).parent / "traj.csv")
    except:
        data = pd.read_csv(Path(file).parent / "traj_mm.csv")
    silhouette2frame = data["frame"].to_numpy()
    try:
        import tifffile as tiff
        background = tiff.imread(Path(file).parent / "background.tif")
    except:
        background = None
    return SilhouetteVideo(file=file, intensities=intensities, pixels=pixels, frame_size=frame_size, background=background, silhouette2frame=silhouette2frame)

#vid = open_silhouettes(r"D:\Results_PleaveDec_corrected_light\20240428T084622_PleaveDec_APE11-CAM2\silhouettes.mat")
#frame = vid.frame(3010, color="black")
#print(vid.silhouette2frame[:10])
#print(vid.n_frames)
#plt.imshow(frame)
#plt.imshow(float(frame) - float(vid.background))
#plt.show()


class FullVideo:
    def __init__(self, folder, type_video="tierpsy", open_all=False, pattern=None):
        self.folder = folder
        self.type_video = type_video
        if pattern is None:
            if type_video == "tierpsy":
                pattern = "video_*.hdf5"
            elif type_video == "mkv":
                pattern = "video_*.mkv"
            elif type_video == "tif":
                pattern = "Video*.tif"
            elif type_video == "silhouettes":
                pattern = "silhouettes.mat"
        self.buffer =  FrameBuffer(max_frames=100)
        self.files = self._list_files(folder, pattern=pattern)
        if len(self.files) == 0:
            raise RuntimeError(f"No files found matching {pattern}.")
        self.objs = []
        self._n_frames_list = []
        # Open all the files
        if open_all:
            self._open_all_files()
            
        #self.n_frames = [self.frames.shape[0]]

    def _open_all_files(self):
        print("Opening files...")
        while len(self._n_frames_list) < len(self.files):
            self._open_next_file()
        print("Done.")    
    # def frame2fileframe(self, id_frame):
    #     # Open files until we can determine the number of frames
    #     while np.sum(self.n_frames) < id_frame:
    #         pass
    
    @property
    def n_frames_estimate(self) -> int:
        if len(self._n_frames_list) == 0:
            self._open_next_file() # Open at least one file        
        n_frames = int(np.floor(np.mean(self._n_frames_list)*len(self.files)))        
        return n_frames

    @property
    def n_frames(self) -> int:
        self._open_all_files()
        return np.sum(self._n_frames_list)
    
    def _list_files(self, folder, pattern="video_*.hdf5"):
        pattern = os.path.join(folder, pattern)
        files = glob.glob(pattern)
        if len(files) > 1:
            def extract_number(filename):
                filename = os.path.basename(filename)
                return int(re.search(r'\d+', filename).group())    
            #def extract_number(filepath):
            #    filename = os.path.basename(filepath)
            #    match = re.search(r"video_(\d+)\.hdf5", filename)
            #    return int(match.group(1)) if match else float("inf")
            files_sorted = sorted(files, key=extract_number)
        else:
            files_sorted = files
        return files_sorted

    def _open_next_file(self):        
        id_video = len(self._n_frames_list)
        if id_video < len(self.files):
            if self.type_video == "tierpsy":  
                self.objs.append(open_tierpsy_video(self.files[id_video]))        
                self._n_frames_list.append(self.objs[-1].n_frames)
            elif self.type_video == "mkv":
                import cv2
                self.objs.append(cv2.VideoCapture(self.files[id_video]))
                if not self.objs[-1].isOpened():
                    raise IOError(f"Could not open video: {self.files[id_video]}")
                self._n_frames_list.append(int(self.objs[-1].get(cv2.CAP_PROP_FRAME_COUNT)))
            elif self.type_video == "tif":
                import tifffile as tiff
                self.objs.append(tiff.TiffFile(self.files[id_video]))
                self._n_frames_list.append(len(self.objs[-1].pages))
            elif self.type_video == "silhouettes":                           
                self.objs.append(open_silhouettes(self.files[id_video]))
                self._n_frames_list.append(self.objs[-1].n_frames)

    
    def frame2file(self, id_frame):
        while len(self._n_frames_list) == 0 or np.sum(self._n_frames_list) <= id_frame:
            self._open_next_file()        
        n_frames_cum = np.cumsum(self._n_frames_list)
        id_file = np.where(n_frames_cum > id_frame)[0][0]
        if id_file > 0:
            ind_frame = id_frame - n_frames_cum[id_file - 1]
        else:
            ind_frame = id_frame
        return id_file, ind_frame

    def frame(self, id_frame):        
        frame = self.buffer.get_frame(id_frame) # Try to get frame from the buffer
        if frame is None: # If the frame is not in the buffer, read it
            id_file, ind_frame = self.frame2file(id_frame)
            if self.type_video in ("tierpsy", "silhouettes"):
                #print(self.objs)
                #caca
                frame = self.objs[id_file].frame(ind_frame)
            elif self.type_video == "mkv":
                import cv2
                self.objs[id_file].set(cv2.CAP_PROP_POS_FRAMES, int(ind_frame))
                ok, frame = self.objs[id_file].read()
                if not ok:
                    raise IOError(f"Could not read frame {id_frame}")
                self.buffer.add_frame(id_frame, frame)
            elif self.type_video == "tif":
                frame = self.objs[id_file].pages[ind_frame].asarray()
                self.buffer.add_frame(id_frame, frame)
        return frame




# class video:
#     def __init__(self, folder):
#         self.files = self._list_files(folder, pattern="video_*.hdf5")
#         self.frames = open_tierpsy_video(self.files[0]) # Open the first video
#         self.n_frames = [self.frames.shape[0]]
        
#     def frame2fileframe(self, id_frame):
#         # Open files until we can determine the number of frames
#         while np.sum(self.n_frames) < id_frame:
            
#     def open_tierpsy_video(h5_path, dataset="mask"):
#         with h5py.File(h5_path, "r") as f:
#             if dataset not in f:
#                 raise KeyError(f"Dataset '{dataset}' not found. Available top-level keys: {list(f.keys())}")
#             dset = f[dataset]
#             if dset.ndim != 3:
#                 raise ValueError(f"Expected a 3D dataset (n_frames, height, width). Got shape {dset.shape} for '{dataset}'.")            
#             return dset[frame_number].astype(np.uint8, copy=True)

#     def _list_files(folder, pattern="video_*.hdf5"):
#         pattern = os.path.join(folder, pattern)
#         files = glob.glob(pattern)
#         def extract_number(filepath):
#             filename = os.path.basename(filepath)
#             match = re.search(r"video_(\d+)\.hdf5", filename)
#             return int(match.group(1)) if match else float("inf")
#         files_sorted = sorted(files, key=extract_number)

#     def _open_next_file(self):        
#         new_frames = open_tierpsy_video(self.files[len(self.n_frames)])
#         self.frames.append(new_frames)
#         self.n_frames.append(len(new_frames))
    
#     def get_frame(self, id_frame):
#         while self.frames.shape[0] <= id_frame:
#             self._open_next_file()



# ----------------------------
# Helpers
# ----------------------------
def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def np_to_qimage(arr: np.ndarray) -> QImage:
    """
    Robust conversion for PyQt6:
    - accepts uint8 grayscale (H,W) or uint8 RGB (H,W,3)
    - forces contiguous memory
    - uses sip.voidptr pointer
    - returns a QImage that owns its own copy (safe lifetime)
    """
    if arr.dtype != np.uint8:
        # If your frames are 16-bit, float, etc. you should convert appropriately.
        arr = arr.astype(np.uint8, copy=False)

    if arr.ndim == 2:
        h, w = arr.shape
        arr_c = np.ascontiguousarray(arr)
        qimg = QImage(arr_c.data, w, h, arr_c.strides[0], QImage.Format.Format_Grayscale8)
        return qimg.copy()  # IMPORTANT: detach from numpy buffer

    if arr.ndim == 3 and arr.shape[2] == 3:
        h, w, _ = arr.shape
        arr_c = np.ascontiguousarray(arr)
        qimg = QImage(arr_c.data, w, h, arr_c.strides[0], QImage.Format.Format_RGB888)
        return qimg.copy()

    if arr.ndim == 3 and arr.shape[2] == 4:
        h, w, _ = arr.shape
        arr_c = np.ascontiguousarray(arr)
        qimg = QImage(arr_c.data, w, h, arr_c.strides[0], QImage.Format.Format_RGBA8888)
        return qimg.copy()

    raise ValueError(f"Unsupported frame shape {arr.shape}, dtype={arr.dtype}")


# ----------------------------
# Viewer widget with interactions
# ----------------------------
class VideoViewer(QLabel):
    """
    Displays the current frame (optionally cropped), supports:
    - wheel to change frame
    - drag-rectangle to zoom in
    - double-click to reset zoom
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(QSize(320, 240))
        self.setStyleSheet("background: #111; color: #ddd;")

        self._frame_arr: np.ndarray | None = None
        self._frame_index: int = 0

        # zoom_rect in image coordinates (x,y,w,h), None => full frame
        self.zoom_rect: QRect | None = None

        # For drag zoom
        self._rubber = QRubberBand(QRubberBand.Shape.Rectangle, self)
        self._drag_origin: QPoint | None = None

        # Callback to ask parent to change frame
        self.on_wheel_frame_step = None  # function(delta_steps:int) -> None

    def set_frame(self, frame_index: int, frame_arr: np.ndarray):
        self._frame_index = int(frame_index)
        self._frame_arr = frame_arr
        self._render()

    def reset_zoom(self):
        self.zoom_rect = None
        self._render()

    def _render(self):
        if self._frame_arr is None:
            self.setText("No frame loaded")
            return

        arr = self._frame_arr
        h, w = arr.shape[:2]

        # Apply zoom crop
        if self.zoom_rect is not None and not self.zoom_rect.isNull():
            r = self.zoom_rect.intersected(QRect(0, 0, w, h))
            if r.width() >= 2 and r.height() >= 2:
                x, y, rw, rh = r.x(), r.y(), r.width(), r.height()
                arr = arr[y:y+rh, x:x+rw]

        qimg = np_to_qimage(arr)
        # Scale to label size while keeping aspect
        pix = QPixmap.fromImage(qimg).scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.setPixmap(pix)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._render()

    # --- mouse wheel => frame navigation ---
    def wheelEvent(self, event):
        if self.on_wheel_frame_step is None:
            return
        # Typically angleDelta().y() is +/-120 per "notch"
        steps = int(event.angleDelta().y() / 120)
        if steps != 0:
            self.on_wheel_frame_step(steps)
        event.accept()

    # --- drag zoom ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._frame_arr is not None:
            self._drag_origin = event.pos()
            self._rubber.setGeometry(QRect(self._drag_origin, QSize()))
            self._rubber.show()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_origin is not None:
            self._rubber.setGeometry(QRect(self._drag_origin, event.pos()).normalized())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._drag_origin is not None:
            self._rubber.hide()
            rect_widget = self._rubber.geometry()
            self._drag_origin = None

            # Convert widget-rect to image-rect
            img_rect = self._widget_rect_to_image_rect(rect_widget)
            if img_rect is not None and img_rect.width() >= 5 and img_rect.height() >= 5:
                self.zoom_rect = img_rect
                self._render()
        super().mouseReleaseEvent(event)

    # --- double click => reset zoom ---
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.reset_zoom()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def _widget_rect_to_image_rect(self, rect_widget: QRect) -> QRect | None:
        """
        Map a selection rectangle in widget coordinates to image coordinates.
        This respects aspect-fit (KeepAspectRatio) scaling with potential letterboxing.
        """
        if self._frame_arr is None:
            return None

        arr = self._frame_arr
        ih, iw = arr.shape[:2]
        ww, wh = self.width(), self.height()

        # Compute displayed pixmap area inside the label for KeepAspectRatio
        scale = min(ww / iw, wh / ih)
        disp_w = iw * scale
        disp_h = ih * scale
        offset_x = (ww - disp_w) / 2.0
        offset_y = (wh - disp_h) / 2.0

        # Intersection of selection with displayed image area
        img_area = QRectF(offset_x, offset_y, disp_w, disp_h)
        sel = QRectF(rect_widget)
        inter = sel.intersected(img_area)
        if inter.isEmpty():
            return None

        # Map to image coordinates
        x1 = (inter.left() - offset_x) / scale
        y1 = (inter.top() - offset_y) / scale
        x2 = (inter.right() - offset_x) / scale
        y2 = (inter.bottom() - offset_y) / scale

        x = int(np.floor(x1))
        y = int(np.floor(y1))
        w = int(np.ceil(x2) - np.floor(x1))
        h = int(np.ceil(y2) - np.floor(y1))

        x = clamp(x, 0, iw - 1)
        y = clamp(y, 0, ih - 1)
        w = clamp(w, 1, iw - x)
        h = clamp(h, 1, ih - y)
        return QRect(x, y, w, h)


# ----------------------------
# Main Window
# ----------------------------
class MainWindow(QMainWindow):
    def __init__(self, video: FullVideo):
        super().__init__()
        self.video = video

        self.setWindowTitle("Interactive Video Player (FullVideo.frame(n))")

        self.viewer = VideoViewer()
        self.viewer.on_wheel_frame_step = self._wheel_step

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(max(0, self.video.n_frames_estimate - 1))
        self.slider.valueChanged.connect(self._on_slider)

        self.frame_edit = QLineEdit()
        self.frame_edit.setPlaceholderText("Frame #")
        self.frame_edit.returnPressed.connect(self._on_edit_enter)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Frame:"))
        controls.addWidget(self.frame_edit)
        controls.addWidget(self.slider)

        root = QVBoxLayout()
        root.addWidget(self.viewer, stretch=1)
        root.addLayout(controls)

        central = QWidget()
        central.setLayout(root)
        self.setCentralWidget(central)

        self._set_frame(0)

    def _set_frame(self, n: int):
        n = clamp(int(n), 0, self.video.n_frames_estimate - 1)
        try:
            arr = self.video.frame(n)
        except Exception as e:
            QMessageBox.critical(self, "Frame error", f"Could not load frame {n}:\n{e}")
            return

        self.viewer.set_frame(n, arr)

        # keep UI in sync without recursion glitches
        self.slider.blockSignals(True)
        self.slider.setValue(n)
        self.slider.blockSignals(False)

        self.frame_edit.blockSignals(True)
        self.frame_edit.setText(str(n))
        self.frame_edit.blockSignals(False)

    def _on_slider(self, value: int):
        self._set_frame(value)

    def _on_edit_enter(self):
        txt = self.frame_edit.text().strip()
        if not txt:
            return
        try:
            n = int(txt)
        except ValueError:
            QMessageBox.information(self, "Invalid input", "Please enter an integer frame index.")
            return
        self._set_frame(n)

    def _wheel_step(self, steps: int):
        # steps is +/-1 per notch typically
        current = self.slider.value()
        self._set_frame(current + steps)

def play_video(folder, type_video="tierpsy"):
    if type_video == "tierpsy":
        folder = Path(folder) / "MaskedVideos"
    app = QApplication(sys.argv)
    video = FullVideo(folder, type_video=type_video)
    # video = FullVideo(n_frames=800)  # replace with your real FullVideo instance
    w = MainWindow(video)
    w.resize(1100, 700)
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    play_video(r"H:\aging_and_development\20260130T103823_Development_L1_Adult_APE1")
