import streamlit as st
from PIL import Image

# Konfigurasi halaman
st.set_page_config(
    page_title="Road Guard: Road Damage Detection",
    page_icon="🛣️",
    layout="wide",
)

# Cek apakah pengguna sudah login
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.error("Silakan login terlebih dahulu!")
    st.stop()  # Hentikan eksekusi jika belum login


# Header
with st.container():
    # st.image("./resource/banner.png", use_column_width="always")  # Tambahkan banner jika ada
    st.title("🌍 Road Guard: Road Damage Detection Application")
    st.markdown(
        """
        **Selamat datang di Road Guard**, aplikasi berbasis kecerdasan buatan untuk mendeteksi kerusakan jalan secara otomatis!  
        Powered by **YOLOv8** dan **CRDDC2022 Dataset**, kami berkomitmen untuk membantu menjaga keselamatan jalan dan mempercepat proses pemeliharaan infrastruktur.
        """
    )
st.divider()

# Section 1: Tentang Aplikasi
with st.container():
    st.subheader("🛠️ Tentang Aplikasi")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(
            """
            ### **Fitur Utama**
            - Deteksi kerusakan jalan secara otomatis.
            - Dukungan untuk input gambar, video, atau real-time webcam.
            - Analisis akurat untuk empat jenis kerusakan jalan:
                1. **Retakan Longitudinal**  
                2. **Retakan Transversal**  
                3. **Retakan Aligator**  
                4. **Lubang Jalan (Potholes)**  
            - Teknologi deep learning terkini menggunakan model YOLOv8.
            """
        )


st.divider()

# Section 2: Cara Penggunaan
with st.container():
    st.subheader("📋 Cara Penggunaan")
    st.markdown(
        """
        1. Pilih jenis input yang ingin digunakan melalui sidebar (gambar, video, atau real-time webcam).  
        2. Unggah file atau aktifkan kamera untuk memulai deteksi.  
        3. Hasil deteksi akan ditampilkan secara visual dengan klasifikasi jenis kerusakan.  
        """
    )

st.divider()

# Section 3: Dokumentasi dan Sumber
with st.container():
    st.subheader("📚 Dokumentasi dan Sumber")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
            - **Github Project Page:**  
              [Github](https://github.com/oracl4/RoadDamageDetection)  
            - **Kontak Pengembang:**  
              📧 eggardewangga100@student.uns.ac.id  
            """
        )
    with col2:
        st.markdown(
            """
            - **Lisensi dan Hak Cipta:**  
              Dataset: [CRDDC2022](https://github.com/oracl4/RoadDamageDetection)  
              Framework: [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) dan [Streamlit](https://streamlit.io/)  
            """
        )

st.divider()

# Section 4: Footer
with st.container():
    st.markdown(
        """
        <style>
        .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: #f1f1f1;
            color: black;
            text-align: center;
            padding: 10px 0;
        }
        </style>
        <div class="footer">
            <p>© 2024 Road Guard. All rights reserved.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
