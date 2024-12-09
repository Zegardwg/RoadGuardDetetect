import os
import cv2
import numpy as np
import streamlit as st
import pymysql
from ultralytics import YOLO
from PIL import Image
from io import BytesIO
import pandas as pd

# Koneksi ke database
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

# Memuat model
def load_model(model_path, model_url):
    if not os.path.exists(model_path):
        from urllib.request import urlretrieve
        urlretrieve(model_url, model_path)
    return YOLO(model_path)

# Menyimpan hasil deteksi ke database
def save_report_to_db(connection, image_name, road_name, description, severity, annotated_image, detections):
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
                cursor.execute(sql_detection, (
                    report_id,
                    detection["name"],
                    detection["confidence"],
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

# Aplikasi Streamlit
st.set_page_config(page_title="Road Guard", page_icon="🛣️", layout="wide")

# Cek apakah pengguna sudah login
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.error("Silakan login terlebih dahulu!")
    st.stop()  # Hentikan eksekusi jika belum login

# CSS Kustom untuk styling
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

st.title("🌍 Road Guard: Deteksi Kerusakan Jalan")
st.markdown(
    "Aplikasi ini mendeteksi kerusakan jalan seperti retak longitudinal, retak melintang, retak buaya, dan lubang jalan. Unggah gambar jalan untuk memulai!"
)

# Sidebar
st.sidebar.header("🔧 Pengaturan Deteksi")
score_threshold = st.sidebar.slider("Tingkat Kepercayaan", 0.0, 1.0, 0.5, 0.05)
image_file = st.file_uploader("Unggah Gambar Jalan", type=["png", "jpg", "jpeg"])

# Model YOLO dan kelas
MODEL_PATH = "./models/YOLOv8_Small_RDD.pt"
MODEL_URL = "https://github.com/oracl4/RoadDamageDetection/raw/main/models/YOLOv8_Small_RDD.pt"
model = load_model(MODEL_PATH, MODEL_URL)
CLASSES = ["Retak Longitudinal", "Retak Melintang", "Retak Buaya", "Lubang Jalan"]

if image_file:
    # Memuat dan menampilkan gambar
    image = Image.open(image_file)
    image_array = np.array(image)

    col1, col2 = st.columns(2)
    with col1:
        st.image(image, caption="Gambar Unggahan", use_column_width=True)

    # Jalankan deteksi YOLO
    results = model.predict(cv2.resize(image_array, (640, 640)), conf=score_threshold)
    annotated_image = results[0].plot()

    with col2:
        st.image(annotated_image, caption="Hasil Deteksi", use_column_width=True)

    # Konversi gambar anotasi ke byte untuk disimpan
    buffer = BytesIO()
    Image.fromarray(annotated_image).save(buffer, format="PNG")
    annotated_image_bytes = buffer.getvalue()

    # Persiapkan data deteksi
    detections = [
        {"name": CLASSES[int(r[5])], "confidence": r[4], "box": tuple(map(int, r[:4]))}
        for r in results[0].boxes.data
    ]

    # Tampilkan hasil deteksi
    st.write("### Objek yang Terdeteksi:")
    st.write(pd.DataFrame(detections))

    # Input untuk informasi tambahan
    road_name = st.text_input("Masukkan Nama Jalan:", placeholder="Misalnya: Jalan Raya Utama")
    description = st.text_area("Deskripsi Laporan:", placeholder="Jelaskan kondisi jalan...")
    severity = st.selectbox("Pilih Tingkat Kerusakan:", ["Ringan", "Sedang", "Berat"])

    # Opsi untuk menyimpan ke database
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
