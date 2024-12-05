import os
import logging
from pathlib import Path
from typing import NamedTuple

import cv2
import numpy as np
import streamlit as st

# Deep learning framework
from ultralytics import YOLO
from PIL import Image
from io import BytesIO

from sample_utils.download import download_file

# Halaman Config
st.set_page_config(
    page_title="Road Guard - Image Detection",
    page_icon="🛣️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Cek apakah pengguna sudah login
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.error("Silakan login terlebih dahulu!")
    st.stop()  # Hentikan eksekusi jika belum login
    
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
    "Longitudinal Crack",
    "Transverse Crack",
    "Alligator Crack",
    "Potholes",
]

class Detection(NamedTuple):
    class_id: int
    label: str
    score: float
    box: np.ndarray

# Header
# st.image("./resource/banner.png", use_column_width="always")  # Ganti dengan banner Anda
st.title("🌍 Road Guard: Road Damage Detection")
st.markdown(
    """
    **Selamat datang di Road Guard**, aplikasi berbasis AI untuk mendeteksi kerusakan jalan melalui gambar!  
    Unggah gambar jalan untuk mendeteksi kerusakan seperti **retakan longitudinal**, **retakan transversal**, **retakan aligator**, dan **lubang jalan**.  
    """
)

st.divider()

# Upload Gambar
st.sidebar.header("🔧 Pengaturan Deteksi")
image_file = st.file_uploader("Unggah Gambar Jalan", type=["png", "jpg", "jpeg"])
score_threshold = st.sidebar.slider(
    "Confidence Threshold",
    min_value=0.0,
    max_value=1.0,
    value=0.5,
    step=0.05,
    help="Atur ambang batas kepercayaan untuk menyesuaikan sensitivitas deteksi.",
)

st.sidebar.write(
    """
    - **Ambang Batas Rendah**: Deteksi lebih banyak, tetapi bisa menghasilkan prediksi palsu.  
    - **Ambang Batas Tinggi**: Prediksi lebih akurat, tetapi bisa mengabaikan kerusakan kecil.
    """
)

if image_file is not None:

    # Load dan Tampilkan Gambar
    image = Image.open(image_file)
    _image = np.array(image)
    h_ori, w_ori = _image.shape[:2]

    col1, col2 = st.columns(2)

    with col1:
        st.write("### 🖼️ Gambar Original")
        st.image(image, caption="Gambar Original", use_column_width="true")

    # Prediksi
    image_resized = cv2.resize(_image, (640, 640), interpolation=cv2.INTER_AREA)
    results = net.predict(image_resized, conf=score_threshold)

    # Anotasi Hasil
    annotated_frame = results[0].plot()
    _image_pred = cv2.resize(annotated_frame, (w_ori, h_ori), interpolation=cv2.INTER_AREA)

    with col2:
        st.write("### 📊 Hasil Prediksi")
        st.image(_image_pred, caption="Gambar dengan Anotasi Deteksi", use_column_width="true")

        # Download Gambar Hasil
        buffer = BytesIO()
        _downloadImage = Image.fromarray(_image_pred)
        _downloadImage.save(buffer, format="PNG")
        _downloadImageByte = buffer.getvalue()

        st.download_button(
            label="⬇️ Unduh Gambar Prediksi",
            data=_downloadImageByte,
            file_name="Road_Guard_Prediction.png",
            mime="image/png",
        )

else:
    st.write("📥 **Unggah gambar untuk memulai deteksi.**")

# Footer
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
        © 2024 Road Guard | Powered by YOLOv8 and Streamlit  
    </div>
    """,
    unsafe_allow_html=True,
)
