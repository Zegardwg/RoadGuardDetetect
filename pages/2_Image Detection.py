import os
import cv2
import numpy as np
import streamlit as st
import pymysql
from ultralytics import YOLO
from PIL import Image
from io import BytesIO
import pandas as pd

# Database connection
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
        st.error(f"Database connection failed: {e}")
        return None

# Load model
def load_model(model_path, model_url):
    if not os.path.exists(model_path):
        from urllib.request import urlretrieve
        urlretrieve(model_url, model_path)
    return YOLO(model_path)

# Save results to the database
def save_report_to_db(connection, image_name, annotated_image, detections):
    try:
        with connection.cursor() as cursor:
            # Save report
            sql_report = "INSERT INTO reports (image_name, annotated_image) VALUES (%s, %s)"
            cursor.execute(sql_report, (image_name, annotated_image))
            report_id = cursor.lastrowid

            # Save detections
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
        st.error(f"Error saving report to database: {e}")
        return None

# Streamlit app
st.set_page_config(page_title="Road Guard", page_icon="🛣️", layout="wide")

st.title("🌍 Road Guard: Road Damage Detection")
st.markdown(
    "Detect road damages such as longitudinal cracks, transverse cracks, alligator cracks, and potholes. Upload an image to start!"
)

# Sidebar
st.sidebar.header("🔧 Detection Settings")
score_threshold = st.sidebar.slider("Confidence Threshold", 0.0, 1.0, 0.5, 0.05)
image_file = st.file_uploader("Upload Road Image", type=["png", "jpg", "jpeg"])

# YOLO model and classes
MODEL_PATH = "./models/YOLOv8_Small_RDD.pt"
MODEL_URL = "https://github.com/oracl4/RoadDamageDetection/raw/main/models/YOLOv8_Small_RDD.pt"
model = load_model(MODEL_PATH, MODEL_URL)
CLASSES = ["Longitudinal Crack", "Transverse Crack", "Alligator Crack", "Potholes"]

if image_file:
    # Load and display the image
    image = Image.open(image_file)
    image_array = np.array(image)

    col1, col2 = st.columns(2)
    with col1:
        st.image(image, caption="Original Image", use_column_width=True)

    # Run YOLO detection
    results = model.predict(cv2.resize(image_array, (640, 640)), conf=score_threshold)
    annotated_image = results[0].plot()

    with col2:
        st.image(annotated_image, caption="Detection Results", use_column_width=True)

    # Convert annotated image to bytes for saving
    buffer = BytesIO()
    Image.fromarray(annotated_image).save(buffer, format="PNG")
    annotated_image_bytes = buffer.getvalue()

    # Prepare detections data
    detections = [
        {"name": CLASSES[int(r[5])], "confidence": r[4], "box": tuple(map(int, r[:4]))}
        for r in results[0].boxes.data
    ]

    # Display detections
    st.write("Detected Objects:")
    st.write(pd.DataFrame(detections))

    # Save to database option
    if st.button("Save Report to Database"):
        connection = connect_db()
        if connection:
            report_id = save_report_to_db(
                connection, image_file.name, annotated_image_bytes, detections
            )
            if report_id:
                st.success(f"Report saved with ID {report_id}!")
            connection.close()
