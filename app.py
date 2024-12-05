import streamlit as st
import pymysql
import base64

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
        
        # Query untuk memasukkan data user
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
    st.title("Registrasi")
    
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    uploaded_file = st.file_uploader("Upload Foto (JPEG/PNG)", type=["jpg", "jpeg", "png"])
    
    if st.button("Daftar"):
        if username and password and uploaded_file:
            # Mengubah file foto ke format binary
            photo = base64.b64encode(uploaded_file.read())
            
            if register_user(username, password, photo):
                st.success("Registrasi berhasil! Silakan login.")
            else:
                st.error("Username sudah terdaftar atau terjadi kesalahan.")
        else:
            st.error("Harap isi semua kolom dan unggah foto!")

# Halaman Login
def login():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if authenticate_user(username, password):
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            st.success("Login berhasil!")
            st.experimental_rerun()  # Reload aplikasi
        else:
            st.error("Username atau password salah.")

# Fungsi untuk Otentikasi Pengguna
def authenticate_user(username, password):
    try:
        conn = create_connection()
        cursor = conn.cursor()
        
        # Query untuk memeriksa user
        sql = "SELECT * FROM users WHERE username = %s AND password = %s"
        cursor.execute(sql, (username, password))
        user = cursor.fetchone()
        
        conn.close()
        return user is not None
    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")
        return False

# Halaman Utama
def main():
    # Inisialisasi state untuk login jika belum ada
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'username' not in st.session_state:
        st.session_state['username'] = None

    # Jika pengguna belum login
    if not st.session_state['logged_in']:
        st.sidebar.header("Akses")
        choice = st.sidebar.selectbox("Pilih Halaman", ["Login", "Registrasi"])
        if choice == "Login":
            login()
        elif choice == "Registrasi":
            register()
    else:
        # Jika pengguna sudah login
        st.sidebar.header("Navigasi")
        if st.sidebar.button("Logout"):
            logout()

        st.title("Selamat Datang di Aplikasi Deteksi Kerusakan Jalan")
        st.write(f"Anda telah login sebagai **{st.session_state['username']}**")

        # Bagian 1: Tentang Aplikasi
        st.subheader("🛠️ Tentang Aplikasi")
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

        # Bagian 2: Cara Penggunaan
        st.subheader("📋 Cara Penggunaan")
        st.markdown(
            """
            1. Pilih jenis input yang ingin digunakan melalui sidebar (gambar, video, atau real-time webcam).  
            2. Unggah file atau aktifkan kamera untuk memulai deteksi.  
            3. Hasil deteksi akan ditampilkan secara visual dengan klasifikasi jenis kerusakan.  
            """
        )

        st.divider()

        # Bagian 3: Dokumentasi dan Sumber
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

# Fungsi Logout
def logout():
    st.session_state['logged_in'] = False
    st.session_state['username'] = None
    st.experimental_rerun()  # Refresh aplikasi untuk kembali ke halaman login


if __name__ == "__main__":
    main()
