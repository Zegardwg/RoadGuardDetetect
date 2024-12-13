import os
import cv2
import numpy as np
import streamlit as st
import pymysql
from ultralytics import YOLO
from PIL import Image
from io import BytesIO
import pandas as pd

# ===================== Fungsi untuk Koneksi ke Database =====================

def connect_db():
    """Menghubungkan ke database MySQL."""
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


# ===================== Fungsi untuk Mendapatkan Statistik =====================

def get_stats():
    """Mengambil statistik total laporan, pengguna, dan deteksi dari database."""
    connection = connect_db()
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) AS total_reports FROM reports")
                total_reports = cursor.fetchone()["total_reports"]

                cursor.execute("SELECT COUNT(*) AS total_users FROM users")
                total_users = cursor.fetchone()["total_users"]

                cursor.execute("SELECT COUNT(*) AS total_detections FROM detections")
                total_detections = cursor.fetchone()["total_detections"]

            connection.close()
            return total_reports, total_users, total_detections
        except pymysql.MySQLError as e:
            st.error(f"Error saat mengambil data: {e}")
            connection.close()
            return 0, 0, 0


# ===================== Fungsi untuk Memuat Model YOLO =====================

def load_model(model_path, model_url):
    """Memuat model YOLO dari path lokal atau mengunduhnya jika belum ada."""
    if not os.path.exists(model_path):
        from urllib.request import urlretrieve
        urlretrieve(model_url, model_path)
    return YOLO(model_path)


# ===================== Fungsi untuk Menyimpan Laporan ke Database =====================

def save_report_to_db(connection, image_name, road_name, description, severity, annotated_image, detections):
    """Menyimpan laporan dan deteksi ke database."""
    try:
        with connection.cursor() as cursor:
            # Simpan laporan
            sql_report = """
            INSERT INTO reports (image_name, road_name, report_description, pothole_severity, annotated_image)
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql_report, (image_name, road_name, description, severity, annotated_image))
            report_id = cursor.lastrowid

            # Simpan deteksi
            sql_detection = """
            INSERT INTO detections (report_id, class_label, confidence, x, y, width, height)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            for detection in detections:
                rounded_confidence = round(float(detection["confidence"]), 4)
                cursor.execute(sql_detection, (
                    report_id,
                    detection["name"],
                    rounded_confidence,
                    detection["box"][0],
                    detection["box"][1],
                    detection["box"][2],
                    detection["box"][3],
                ))

            connection.commit()
            return report_id
    except Exception as e:
        st.error(f"Terjadi kesalahan saat menyimpan laporan ke database: {e}")
        return None


# ===================== Konfigurasi Aplikasi Streamlit =====================

st.set_page_config(page_title="Road Guard", page_icon="\U0001F6E3\uFE0F", layout="wide")

# Cek apakah pengguna sudah login
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.error("Silakan login terlebih dahulu!")
    st.stop()

# ===================== CSS Kustom untuk Styling =====================

st.markdown("""
<style>
    .report-title {
        font-size: 24px;
        font-weight: bold;
        color: #4CAF50;
    }
    .detection-title {
        font-size: 20px;
        font-weight: bold;
        color: #2196F3;
    }
    .description {
        font-size: 16px;
        color: #555;
    }
</style>
""", unsafe_allow_html=True)

# ===================== Judul Aplikasi =====================

st.title("\U0001F30D Road Guard: Deteksi Kerusakan Jalan")
st.markdown(
    "Aplikasi ini mendeteksi kerusakan jalan seperti retak longitudinal, retak melintang, retak buaya, dan lubang jalan. Unggah gambar jalan untuk memulai!"
)

# ===================== Sidebar =====================

st.sidebar.header("\U0001F527 Pengaturan Deteksi")
score_threshold = st.sidebar.slider("Tingkat Kepercayaan", 0.0, 1.0, 0.5, 0.05)
image_file = st.file_uploader("Unggah Gambar Jalan", type=["png", "jpg", "jpeg"])

# ===================== Load Model =====================

MODEL_PATH = "./models/YOLOv8_Small_RDD.pt"
MODEL_URL = "https://github.com/oracl4/RoadDamageDetection/raw/main/models/YOLOv8_Small_RDD.pt"
model = load_model(MODEL_PATH, MODEL_URL)
CLASSES = ["Retak Longitudinal", "Retak Melintang", "Retak Buaya", "Lubang Jalan"]

# ===================== Proses Deteksi =====================

if image_file:
    image = Image.open(image_file)
    image_array = np.array(image)

    col1, col2 = st.columns(2)
    with col1:
        st.image(image, caption="Gambar Unggahan", use_container_width=True)

    # Jalankan deteksi YOLO
    results = model.predict(cv2.resize(image_array, (640, 640)), conf=score_threshold)
    annotated_image = results[0].plot()

    with col2:
        st.image(annotated_image, caption="Hasil Deteksi", use_container_width=True)

    # Konversi gambar anotasi ke byte untuk disimpan
    buffer = BytesIO()
    Image.fromarray(annotated_image).save(buffer, format="PNG")
    annotated_image_bytes = buffer.getvalue()

    # Persiapkan data deteksi
    detections = [
        {"name": CLASSES[int(r[5])], "confidence": r[4], "box": tuple(map(int, r[:4]))}
        for r in results[0].boxes.data
    ]

    st.write("### Objek yang Terdeteksi:")
    st.write(pd.DataFrame(detections))

    # Input informasi tambahan
    road_name = st.text_input("Masukkan Nama Jalan:", placeholder="Misalnya: Jalan Raya Utama")
    description = st.text_area("Deskripsi Laporan:", placeholder="Jelaskan kondisi jalan...")
    severity = st.selectbox("Pilih Tingkat Kerusakan:", ["Ringan", "Sedang", "Berat"])

    # Simpan laporan ke database
    if st.button("Simpan Laporan ke Database"):
        if not road_name or not description or not severity:
            st.error("Harap lengkapi semua kolom sebelum menyimpan.")
        else:
            connection = connect_db()
            if connection:
                report_id = save_report_to_db(
                    connection, image_file.name, road_name, description, severity, annotated_image_bytes, detections
                )
                if report_id:
                    st.success(f"Laporan berhasil disimpan dengan ID: {report_id}!")
                connection.close()

