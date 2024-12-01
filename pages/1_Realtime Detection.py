import logging
import queue
from pathlib import Path
from typing import List, NamedTuple

import av
import cv2
import numpy as np
import streamlit as st
from streamlit_webrtc import WebRtcMode, webrtc_streamer

# Deep learning framework
from ultralytics import YOLO

from sample_utils.download import download_file
from sample_utils.get_STUNServer import getSTUNServer

# Halaman Config
st.set_page_config(
    page_title="Road Guard - Realtime Detection",
    page_icon="🛣️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Paths dan Setup Model
HERE = Path(__file__).parent
ROOT = HERE.parent
logger = logging.getLogger(__name__)

MODEL_URL = "https://github.com/oracl4/RoadDamageDetection/raw/main/models/YOLOv8_Small_RDD.pt"  # noqa: E501
MODEL_LOCAL_PATH = ROOT / "./models/YOLOv8_Small_RDD.pt"
download_file(MODEL_URL, MODEL_LOCAL_PATH, expected_size=89569358)

# STUN Server
STUN_STRING = "stun:" + str(getSTUNServer())
STUN_SERVER = [{"urls": [STUN_STRING]}]

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
# st.image("./resource/banner2.png", use_column_width="always")  # banner2 yang menarik
st.title("🌍 Road Guard: Realtime Road Damage Detection")
st.markdown(
    """
    **Selamat datang di Road Guard**, aplikasi berbasis AI untuk deteksi kerusakan jalan secara real-time.  
    Kami menggunakan teknologi **YOLOv8** untuk menganalisis dan mendeteksi kerusakan seperti retakan atau lubang jalan.  
    """
)

st.divider()

# Bagian Pengaturan dan Input
st.sidebar.header("🔧 Pengaturan Deteksi")
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

st.markdown(
    """
    ### 🎥 Fitur Realtime Deteksi
    - **Gunakan Webcam atau Kamera Eksternal** untuk mendeteksi kerusakan jalan.  
    - Hasil deteksi ditampilkan secara langsung dengan anotasi visual.  
    - Cocok untuk pemantauan lapangan secara on-site.
    """
)

# Queue untuk prediksi hasil
result_queue: "queue.Queue[List[Detection]]" = queue.Queue()

def video_frame_callback(frame: av.VideoFrame) -> av.VideoFrame:
    image = frame.to_ndarray(format="bgr24")
    h_ori, w_ori = image.shape[:2]
    image_resized = cv2.resize(image, (640, 640), interpolation=cv2.INTER_AREA)
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
        result_queue.put(detections)
    
    annotated_frame = results[0].plot()
    _image = cv2.resize(annotated_frame, (w_ori, h_ori), interpolation=cv2.INTER_AREA)
    return av.VideoFrame.from_ndarray(_image, format="bgr24")

webrtc_ctx = webrtc_streamer(
    key="road-damage-detection",
    mode=WebRtcMode.SENDRECV,
    rtc_configuration={"iceServers": STUN_SERVER},
    video_frame_callback=video_frame_callback,
    media_stream_constraints={
        "video": {"width": {"ideal": 1280, "min": 800}},
        "audio": False,
    },
    async_processing=True,
)

# Tabel Prediksi
if st.checkbox("📝 Tampilkan Tabel Prediksi"):
    if webrtc_ctx.state.playing:
        labels_placeholder = st.empty()
        while True:
            result = result_queue.get()
            labels_placeholder.table(result)

st.divider()

# Footer
st.markdown(
    """
    <style>
    .footer {
        text-align: center;
        font-size: 14px;
        margin-top: 20px;
        padding: 10px;
        background-color: #f1f1f1;
    }
    </style>
    <div class="footer">
        © 2024 Road Guard | Powered by YOLOv8 and Streamlit
    </div>
    """,
    unsafe_allow_html=True,
)
