import streamlit as st
import pymysql
import base64
from streamlit_extras.switch_page_button import switch_page

# Koneksi ke Database
def create_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="road_detection"
    )

# Fungsi untuk Registrasi
def register_user(username, password, photo):
    try:
        conn = create_connection()
        cursor = conn.cursor()

        sql = "INSERT INTO users (username, password, photo) VALUES (%s, %s, %s)"
        cursor.execute(sql, (username, password, photo))

        conn.commit()
        conn.close()
        return True
    except pymysql.IntegrityError:
        return False  # Jika username sudah ada
    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")
        return False

# Halaman Registrasi
def register():
    st.title("🔒 Registrasi")
    st.markdown("Daftar akun baru untuk mengakses aplikasi.")

    with st.form("register_form"):
        username = st.text_input("👤 Username")
        password = st.text_input("🔑 Password", type="password")
        uploaded_file = st.file_uploader("📁 Upload Foto (JPEG/PNG)", type=["jpg", "jpeg", "png"])
        submit_button = st.form_submit_button("Daftar")

        if submit_button:
            if username and password and uploaded_file:
                photo = base64.b64encode(uploaded_file.read())
                if register_user(username, password, photo):
                    st.success("🚀 Registrasi berhasil! Silakan login.")
                    switch_page("Login")
                else:
                    st.error("Username sudah terdaftar atau terjadi kesalahan.")
            else:
                st.error("Harap isi semua kolom dan unggah foto!")

# Fungsi untuk Otentikasi Pengguna
def authenticate_user(username, password):
    try:
        conn = create_connection()
        cursor = conn.cursor()

        sql = "SELECT * FROM users WHERE username = %s AND password = %s"
        cursor.execute(sql, (username, password))
        user = cursor.fetchone()

        conn.close()
        return user is not None
    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")
        return False

# Halaman Login
def login():
    st.title("🔑 Login")
    st.markdown("Masuk dengan akun Anda untuk melanjutkan.")

    with st.form("login_form"):
        username = st.text_input("👤 Username")
        password = st.text_input("🔑 Password", type="password")
        submit_button = st.form_submit_button("Login")

        if submit_button:
            if authenticate_user(username, password):
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.success("🚀 Login berhasil!")
                st.experimental_set_query_params()  
            else:
                st.error("Username atau password salah.")

# Halaman Utama
def main():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'username' not in st.session_state:
        st.session_state['username'] = None

    if not st.session_state['logged_in']:
        st.sidebar.header("Akses")
        choice = st.sidebar.radio("Pilih Halaman", ["Login", "Registrasi"])
        if choice == "Login":
            login()
        elif choice == "Registrasi":
            register()
    else:
        st.sidebar.header("Navigasi")
        if st.sidebar.button("Logout"):
            logout()

        st.title(f"🌟 Selamat Datang, {st.session_state['username']}")
        st.write("Jelajahi fitur aplikasi deteksi kerusakan jalan kami.")

        st.subheader("⚙️ Tentang Aplikasi")
        st.markdown(
            """
            ### **Fitur Utama**
            - Deteksi kerusakan jalan otomatis (Retakan, Potholes, dll).
            - Input gambar, video, atau real-time webcam.
            - Analisis berbasis YOLOv8.
            """
        )

        st.divider()

        st.subheader("📋 Cara Penggunaan")
        st.markdown(
            """
            1. Pilih jenis input dari sidebar.
            2. Unggah file atau aktifkan kamera.
            3. Lihat hasil deteksi secara real-time.
            """
        )

        st.divider()
        # st.subheader("📊 Statistik Penggunaan")
        # st.markdown(
        #     """
        #     - **Pengguna Terdaftar:** 120
        #     - **Analisis Dilakukan:** 350
        #     - **Jenis Kerusakan Terdeteksi:**
        #       - Retakan: 200 kasus
        #       - Potholes: 150 kasus
        #     """
        # )

        st.divider()
        st.subheader("🔗 Dokumentasi dan Sumber")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(
                """
                - **Github Project Page:**  [Github](https://github.com/oracl4/RoadDamageDetection)  
                - **Kontak Pengembang:**  📧 eggardewangga100@student.uns.ac.id  
                """
            )

        with col2:
            st.markdown(
                """
                - **Lisensi dan Hak Cipta:**  
                  Dataset: [CRDDC2022](https://crddc2022.sekilab.global/)  
                  Framework: [YOLOv8](https://github.com/ultralytics/ultralytics)  
                """
            )

# Fungsi Logout
def logout():
    st.session_state['logged_in'] = False
    st.session_state['username'] = None
    st.experimental_set_query_params()  

if __name__ == "__main__":
    main()
