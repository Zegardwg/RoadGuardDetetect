import streamlit as st
import pymysql
import pandas as pd
import plotly.express as px
from ultralytics import YOLO
from pathlib import Path
import cv2
import numpy as np
from io import BytesIO

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

# === Fungsi untuk menyimpan laporan ke database ===
def save_report_to_db(connection, road_name, description, severity):
    try:
        with connection.cursor() as cursor:
            sql_report = """
            INSERT INTO reports (road_name, report_description, pothole_severity)
            VALUES (%s, %s, %s)
            """
            cursor.execute(sql_report, (road_name, description, severity))
            connection.commit()
            return cursor.lastrowid
    except Exception as e:
        st.error(f"Kesalahan menyimpan laporan: {e}")
        return None

# === Fungsi untuk menyimpan deteksi ke database ===
def save_detections_to_db(connection, report_id, detections):
    try:
        with connection.cursor() as cursor:
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
    except Exception as e:
        st.error(f"Kesalahan menyimpan deteksi: {e}")

# === Fungsi untuk mengambil data deteksi berdasarkan report_id ===
def get_detections_by_report_id(connection, report_id):
    try:
        with connection.cursor() as cursor:
            sql = """
            SELECT class_label, confidence, x, y, width, height
            FROM detections
            WHERE report_id = %s
            """
            cursor.execute(sql, (report_id,))
            return cursor.fetchall()
    except Exception as e:
        st.error(f"Kesalahan mengambil deteksi: {e}")
        return []

# === Fungsi untuk memproses video ===
def process_video(video_file, score_threshold, report_id):
    temp_input = "./temp/input_video.mp4"
    temp_output = "./temp/output_infer.mp4"

    with open(temp_input, "wb") as f:
        f.write(video_file.getbuffer())

    cap = cv2.VideoCapture(temp_input)
    if not cap.isOpened():
        st.error("Gagal membuka video.")
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    out = cv2.VideoWriter(temp_output, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))

    detections_list = []
    frame_counter = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        results = net.predict(frame, conf=score_threshold)
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
        out.write(cv2.cvtColor(annotated_frame, cv2.COLOR_RGB2BGR))
        frame_counter += 1

    cap.release()
    out.release()

    connection = connect_db()
    if connection:
        save_detections_to_db(connection, report_id, detections_list)
        connection.close()

    st.success("Video selesai diproses dan data deteksi disimpan!")

    with open(temp_output, "rb") as f:
        st.download_button("\u2b07\ufe0f Unduh Video Hasil", data=f, file_name="output_infer.mp4")

# === Kelas untuk deteksi ===
class Detection:
    def __init__(self, class_id, label, score, box):
        self.class_id = class_id
        self.label = label
        self.score = score
        self.box = box

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

# === Fungsi utama aplikasi ===
def main():
    st.title("Road Guard: Deteksi Kerusakan Jalan")

    menu = ["Unggah Video & Analisis", "Lihat Laporan"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Unggah Video & Analisis":
        st.subheader("Unggah Video dan Analisis Kerusakan Jalan")
        video_file = st.file_uploader("Unggah Video", type=["mp4"])
        score_threshold = st.slider("Ambang Batas Deteksi", 0.1, 1.0, 0.5, step=0.05)

        road_name = st.text_input("Nama Jalan", placeholder="Contoh: Jalan Raya Utama")
        description = st.text_area("Deskripsi", placeholder="Deskripsi kondisi jalan...")
        severity = st.selectbox("Tingkat Kerusakan", ["Ringan", "Sedang", "Berat"])

        if st.button("Simpan dan Proses Video"):
            connection = connect_db()
            if connection:
                report_id = save_report_to_db(connection, road_name, description, severity)
                if report_id:
                    process_video(video_file, score_threshold, report_id)
                    st.success(f"Laporan berhasil disimpan dengan ID: {report_id}")
                connection.close()

    elif choice == "Lihat Laporan":
        st.subheader("Lihat Laporan Kerusakan Jalan")
        connection = connect_db()
        if connection:
            report_id = st.number_input("Masukkan Report ID", min_value=1, step=1)

            if st.button("Tampilkan Data"):
                detections = get_detections_by_report_id(connection, report_id)
                if detections:
                    df = pd.DataFrame(detections)
                    st.write("Tabel Deteksi:")
                    st.dataframe(df)

                    st.write("Visualisasi Data:")
                    fig = px.bar(df, x="class_label", y="confidence", color="class_label", title="Confidence per Kelas")
                    st.plotly_chart(fig)
                else:
                    st.warning("Tidak ada data untuk Report ID tersebut.")
            connection.close()

if __name__ == "__main__":
    main()
