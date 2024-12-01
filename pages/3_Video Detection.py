import os
import logging
from pathlib import Path
from typing import List, NamedTuple

import cv2
import numpy as np
import streamlit as st

# Deep learning framework
from ultralytics import YOLO

from sample_utils.download import download_file

# Halaman Config
st.set_page_config(
    page_title="Road Guard - Deteksi Kerusakan Jalan",
    page_icon="🛣️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Paths dan Model Setup
HERE = Path(__file__).parent
ROOT = HERE.parent

logger = logging.getLogger(__name__)

MODEL_URL = "https://github.com/oracl4/RoadDamageDetection/raw/main/models/YOLOv8_Small_RDD.pt"
MODEL_LOCAL_PATH = ROOT / "./models/YOLOv8_Small_RDD.pt"
download_file(MODEL_URL, MODEL_LOCAL_PATH, expected_size=89569358)

# Caching Model
cache_key = "yolov8smallrdd"
if cache_key in st.session_state:
    net = st.session_state[cache_key]
else:
    net = YOLO(MODEL_LOCAL_PATH)
    st.session_state[cache_key] = net

CLASSES = [
    "Retakan Longitudinal",
    "Retakan Transversal",
    "Retakan Aligator",
    "Lubang Jalan",
]

class Detection(NamedTuple):
    class_id: int
    label: str
    score: float
    box: np.ndarray

# Create temporary folder if doesn't exists
if not os.path.exists('./temp'):
   os.makedirs('./temp')

temp_file_input = "./temp/video_input.mp4"
temp_file_infer = "./temp/video_infer.mp4"

# Processing state
if 'processing_button' in st.session_state and st.session_state.processing_button == True:
    st.session_state.runningInference = True
else:
    st.session_state.runningInference = False

# func to save BytesIO on a drive
def write_bytesio_to_file(filename, bytesio):
    with open(filename, "wb") as outfile:
        outfile.write(bytesio.getbuffer())

def processVideo(video_file, score_threshold):
    write_bytesio_to_file(temp_file_input, video_file)
    
    videoCapture = cv2.VideoCapture(temp_file_input)

    if (videoCapture.isOpened() == False):
        st.error('Error membuka file video')
    else:
        _width = int(videoCapture.get(cv2.CAP_PROP_FRAME_WIDTH))
        _height = int(videoCapture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        _fps = videoCapture.get(cv2.CAP_PROP_FPS)
        _frame_count = int(videoCapture.get(cv2.CAP_PROP_FRAME_COUNT))
        _duration = _frame_count/_fps
        _duration_minutes = int(_duration/60)
        _duration_seconds = int(_duration%60)
        _duration_strings = str(_duration_minutes) + ":" + str(_duration_seconds)

        st.write("Durasi Video:", _duration_strings)
        st.write("Lebar, Tinggi dan FPS:", _width, _height, _fps)

        inferenceBarText = "Melakukan inferensi pada video, harap tunggu."
        inferenceBar = st.progress(0, text=inferenceBarText)

        imageLocation = st.empty()

        fourcc_mp4 = cv2.VideoWriter_fourcc(*'mp4v')
        cv2writer = cv2.VideoWriter(temp_file_infer, fourcc_mp4, _fps, (_width, _height))

        _frame_counter = 0
        while(videoCapture.isOpened()):
            ret, frame = videoCapture.read()
            if ret == True:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                _image = np.array(frame)
                image_resized = cv2.resize(_image, (640, 640), interpolation = cv2.INTER_AREA)
                results = net.predict(image_resized, conf=score_threshold)

                for result in results:
                    boxes = result.boxes.cpu().numpy()
                    detections = [
                        Detection(
                            class_id=int(_box.cls),
                            label=CLASSES[int(_box.cls)],
                            score=float(_box.conf),
                            box=_box.xyxy[0].astype(int),
                        )
                        for _box in boxes
                    ]

                annotated_frame = results[0].plot()
                _image_pred = cv2.resize(annotated_frame, (_width, _height), interpolation = cv2.INTER_AREA)

                _out_frame = cv2.cvtColor(_image_pred, cv2.COLOR_RGB2BGR)
                cv2writer.write(_out_frame)
                imageLocation.image(_image_pred)

                _frame_counter += 1
                inferenceBar.progress(_frame_counter/_frame_count, text=inferenceBarText)
            else:
                inferenceBar.empty()
                break

        videoCapture.release()
        cv2writer.release()

    st.success("Video Telah Diproses!")

    col1, col2 = st.columns(2)
    with col1:
        with open(temp_file_infer, "rb") as f:
            st.download_button(
                label="⬇️ Unduh Video Prediksi",
                data=f,
                file_name="RDD_Prediction.mp4",
                mime="video/mp4",
                use_container_width=True
            )
            
    with col2:
        if st.button('Mulai Ulang Aplikasi', use_container_width=True, type="primary"):
            st.rerun()

# Header Section
# st.image("./resource/banner.png", use_column_width="always")  # Ganti dengan banner Anda
st.title("🚧 Road Guard: Deteksi Kerusakan Jalan - Video")
st.markdown(
    """
    **Selamat datang di Road Guard**, aplikasi AI yang kuat untuk mendeteksi kerusakan jalan dalam video!  
    Unggah file video untuk menganalisis kondisi jalan, dan dapatkan wawasan tentang retakan, lubang jalan, dan lainnya.  
    """
)

# Sidebar
st.sidebar.header("🔧 Pengaturan Deteksi Video")
video_file = st.file_uploader("Unggah Video", type=".mp4", disabled=st.session_state.runningInference)
st.sidebar.caption("Silakan unggah video hingga 1GB. Ukur atau potong video besar jika diperlukan.")

score_threshold = st.sidebar.slider(
    "Ambang Batas Keyakinan",
    min_value=0.0,
    max_value=1.0,
    value=0.5,
    step=0.05,
    disabled=st.session_state.runningInference
)
st.sidebar.write(
    """
    - **Ambang batas rendah**: Deteksi lebih banyak namun bisa jadi positif palsu.  
    - **Ambang batas tinggi**: Lebih akurat namun bisa melewatkan beberapa kerusakan.
    """
)

if video_file is not None:
    if st.button('Proses Video', use_container_width=True, disabled=st.session_state.runningInference, type="secondary", key="processing_button"):
        st.warning(f"Memproses Video: {video_file.name}")
        processVideo(video_file, score_threshold)

# Footer Section
st.divider()
st.markdown(
    """
    <style>
    .footer {
        text-align: center;
        font-size: 14px;
        margin-top: 20px;
        padding: 10px;
        background-color: #f9f9f9;
    }
    </style>
    <div class="footer">
        © 2024 Road Guard | Ditenagai oleh YOLOv8 dan Streamlit  
    </div>
    """,
    unsafe_allow_html=True,
)
