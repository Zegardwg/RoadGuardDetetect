import streamlit as st
import cv2
import numpy as np
import pymysql
from io import BytesIO
from ultralytics import YOLO
from pathlib import Path
import os

# === Konfigurasi halaman Streamlit ===
st.set_page_config(
    page_title="Road Guard - Deteksi Kerusakan Jalan",
    page_icon="🛣️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# === Fungsi untuk koneksi database ===
def connect_db():
    try:
        return pymysql.connect(
            host="localhost",
            user="root",
            password="",
            database="road_detection",
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )
    except Exception as e:
        st.error(f"Gagal terhubung ke database: {e}")
        return None

# === Inisialisasi model YOLO ===
MODEL_PATH = Path("./models/YOLOv8_Small_RDD.pt")

if not MODEL_PATH.exists():
    st.error("Model tidak ditemukan. Pastikan model sudah diunduh di folder 'models'.")
    st.stop()

@st.cache_resource
def load_model():
    return YOLO(str(MODEL_PATH))

net = load_model()
CLASSES = ["Retakan Longitudinal", "Retakan Transversal", "Retakan Aligator", "Lubang Jalan"]

# === Fungsi menyimpan BytesIO ke file ===
def write_bytesio_to_file(filename, bytesio):
    with open(filename, "wb") as outfile:
        outfile.write(bytesio.getbuffer())

# === Kelas untuk menyimpan deteksi ===
class Detection:
    def __init__(self, class_id, label, score, box):
        self.class_id = class_id
        self.label = label
        self.score = score
        self.box = box

# === Fungsi menyimpan laporan ke database ===
def save_report_to_db(connection, video_name, road_name, description, severity, detections):
    try:
        with connection.cursor() as cursor:
            sql_report = """
            INSERT INTO reports (video_name, road_name, report_description, pothole_severity)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql_report, (video_name, road_name, description, severity))
            report_id = cursor.lastrowid

            sql_detection = """
            INSERT INTO detections (report_id, class_label, confidence, x, y, width, height)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            for det in detections:
                cursor.execute(sql_detection, (
                    report_id,
                    det.label,
                    det.score,
                    det.box[0],
                    det.box[1],
                    det.box[2] - det.box[0],
                    det.box[3] - det.box[1],
                ))

            connection.commit()
            return report_id
    except Exception as e:
        st.error(f"Kesalahan menyimpan laporan: {e}")
        return None

# === Proses Video dengan Inferensi ===
def process_video_with_inference(video_file, score_threshold):
    temp_file_input = "./temp/input_video.mp4"
    temp_file_infer = "./temp/output_infer.mp4"

    write_bytesio_to_file(temp_file_input, video_file)
    video_capture = cv2.VideoCapture(temp_file_input)

    if not video_capture.isOpened():
        st.error("Error membuka file video.")
        return

    width = int(video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = video_capture.get(cv2.CAP_PROP_FPS)
    frame_count = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))

    writer = cv2.VideoWriter(temp_file_infer, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))
    progress_bar = st.progress(0)
    image_display = st.empty()

    detections_list = []
    frame_counter = 0
    while video_capture.isOpened():
        ret, frame = video_capture.read()
        if not ret:
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = net.predict(frame_rgb, conf=score_threshold)

        for result in results:
            for box in result.boxes.cpu().numpy():
                detections_list.append(
                    Detection(
                        class_id=int(box.cls),
                        label=CLASSES[int(box.cls)],
                        score=float(box.conf),
                        box=box.xyxy[0].astype(int),
                    )
                )

        annotated_frame = results[0].plot()
        writer.write(cv2.cvtColor(annotated_frame, cv2.COLOR_RGB2BGR))

        image_display.image(annotated_frame)
        frame_counter += 1
        progress_bar.progress(frame_counter / frame_count)

    video_capture.release()
    writer.release()
    progress_bar.empty()
    st.success("Proses video selesai!")

    return detections_list, temp_file_infer

# === UI Utama Streamlit ===
def main():
    st.title("🛣️ Road Guard: Deteksi Kerusakan Jalan")
    video_file = st.file_uploader("Unggah Video", type=["mp4"])
    score_threshold = st.slider("Ambang Batas Deteksi", 0.1, 1.0, 0.5, step=0.05)

    # State untuk mengelola apakah video sudah diproses
    if "detections" not in st.session_state:
        st.session_state.detections = None
        st.session_state.video_output = None
        st.session_state.video_processed = False

    if video_file and not st.session_state.video_processed:
        detections, video_output = process_video_with_inference(video_file, score_threshold)
        st.session_state.detections = detections
        st.session_state.video_output = video_output
        st.session_state.video_processed = True

    if st.session_state.video_processed:
        st.success("Video berhasil diproses!")
        road_name = st.text_input("Nama Jalan:", placeholder="Contoh: Jalan Raya Utama")
        description = st.text_area("Deskripsi:", placeholder="Deskripsi kondisi jalan...")
        severity = st.selectbox("Tingkat Kerusakan:", ["Ringan", "Sedang", "Berat"])

        if st.button("Simpan Laporan"):
            connection = connect_db()
            if connection:
                report_id = save_report_to_db(connection, video_file.name, road_name, description, severity, st.session_state.detections)
                if report_id:
                    st.success(f"Laporan berhasil disimpan dengan ID: {report_id}")
                connection.close()

        with open(st.session_state.video_output, "rb") as f:
            st.download_button("⬇️ Unduh Video Prediksi", data=f, file_name="RDD_Prediction.mp4", mime="video/mp4")

if __name__ == "__main__":
    main()
