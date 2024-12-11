import streamlit as st
import pymysql
import pandas as pd
from PIL import Image
import base64
import io
import altair as alt
import bcrypt


# Fungsi untuk membuat koneksi ke database MySQL
def create_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="road_detection"
    )

# Fungsi untuk mendapatkan data statistik
def get_stats():
    connection = create_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM reports")
                total_reports = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM users")
                total_users = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM detections")
                total_detections = cursor.fetchone()[0]

            connection.close()
            return total_reports, total_users, total_detections

        except pymysql.MySQLError as e:
            st.error(f"Error saat mengambil data: {e}")
            connection.close()
            return 0, 0, 0


# Fungsi untuk menambahkan laporan baru
def create_report(road_name, report_description, pothole_severity, image_name=None, video_name=None, annotated_image=None):
    connection = create_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                # Tambahkan laporan ke tabel reports tanpa user_id
                query = """
                INSERT INTO reports (road_name, report_description, pothole_severity, image_name, video_name, annotated_image)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (road_name, report_description, pothole_severity, image_name, video_name, annotated_image))
                connection.commit()
                st.success("Laporan berhasil ditambahkan!")
        except pymysql.MySQLError as e:
            st.error(f"Gagal menambahkan laporan: {e}")
        finally:
            connection.close()



            # Fungsi untuk memperbarui laporan
def update_report(report_id, road_name, report_description, pothole_severity):
    connection = create_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                query = """
                UPDATE reports 
                SET road_name = %s, report_description = %s, pothole_severity = %s 
                WHERE report_id = %s
                """
                cursor.execute(query, (road_name, report_description, pothole_severity, report_id))
                connection.commit()
                st.success("Laporan berhasil diperbarui!")
        except pymysql.MySQLError as e:
            st.error(f"Gagal memperbarui laporan: {e}")
        finally:
            connection.close()

# Fungsi untuk menghapus laporan
def delete_report(report_id):
    connection = create_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                # Hapus data terkait di tabel detections
                delete_detections_query = "DELETE FROM detections WHERE report_id = %s"
                cursor.execute(delete_detections_query, (report_id,))
                
                # Hapus laporan di tabel reports
                delete_report_query = "DELETE FROM reports WHERE report_id = %s"
                cursor.execute(delete_report_query, (report_id,))
                
                connection.commit()
                st.success("Laporan dan data terkait berhasil dihapus!")
        except pymysql.MySQLError as e:
            st.error(f"Gagal menghapus laporan: {e}")
        finally:
            connection.close()

# Fungsi untuk mengambil data seluruh User          
def get_all_users():
    connection = create_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                query = """
                SELECT id, username, photo
                FROM users
                """
                cursor.execute(query)
                result = cursor.fetchall()
                connection.close()
                
                # Ubah hasil query menjadi DataFrame
                return pd.DataFrame(result, columns=["User ID", "Username", "Photo"])
        except pymysql.MySQLError as e:
            st.error(f"Gagal mengambil data pengguna: {e}")
            connection.close()
            return pd.DataFrame(columns=["User ID", "Username", "Photo"])


# Fungsi untuk menambahkan pengguna baru
def create_user(username, password, photo):
    connection = create_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                query = "INSERT INTO users (username, password, photo) VALUES (%s, %s, %s)"
                cursor.execute(query, (username, password, photo))
                connection.commit()
                st.success("Pengguna berhasil ditambahkan!")
        except pymysql.MySQLError as e:
            st.error(f"Gagal menambahkan pengguna: {e}")
        finally:
            connection.close()

# Fungsi untuk memperbarui pengguna
def update_user(user_id, username, password, photo):
    if not user_id:
        st.error("ID pengguna tidak boleh kosong.")
        return

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())  # Hashing password

    connection = create_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                # Periksa apakah ID pengguna ada
                query_check = "SELECT COUNT(*) FROM users WHERE id = %s"
                cursor.execute(query_check, (user_id,))
                result = cursor.fetchone()
                if result[0] == 0:
                    st.error("Pengguna tidak ditemukan.")
                    return
                
                # Lanjutkan pembaruan data
                query = """
                UPDATE users 
                SET username = %s, password = %s, photo = %s 
                WHERE id = %s
                """
                cursor.execute(query, (username, hashed_password, photo, user_id))
                connection.commit()
                
        except pymysql.MySQLError as e:
            st.error(f"Gagal memperbarui pengguna: {e}")
        finally:
            connection.close()


# Fungsi untuk menghapus pengguna
def delete_user(user_id):
    connection = create_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                query = "DELETE FROM users WHERE id = %s"  # Gunakan nama kolom yang benar
                cursor.execute(query, (user_id,))
                connection.commit()
                st.success("Pengguna berhasil dihapus!")
        except pymysql.MySQLError as e:
            st.error(f"Gagal menghapus pengguna: {e}")
        finally:
            connection.close()

# Fungsi untuk Fitur CRUD
def crud_ui():
    st.sidebar.title("⚙️ Kelola Data")

    action = st.sidebar.radio("Pilih Aksi", [
         "Tambah Pengguna", "Perbarui Laporan", "Hapus Laporan", 
        "Perbarui Pengguna", "Hapus Pengguna"
    ])

    st.title("🛠️ Manajemen Data")

    # Tambah Laporan
    if action == "Tambah Laporan":
        with st.form("tambah_laporan_form"):
            st.header("📝 Tambah Laporan Baru")
            col1, col2 = st.columns(2)
            road_name = col1.text_input("Nama Jalan")
            report_description = st.text_area("Deskripsi Laporan")
            pothole_severity = st.selectbox("Tingkat Kerusakan", ["Ringan", "Sedang", "Berat"])
            submit = st.form_submit_button("Tambah Laporan")
            
            if submit:
                create_report(road_name, report_description, pothole_severity, user_id)
                st.success("Laporan berhasil ditambahkan!")
    
    # Tambah Pengguna
    elif action == "Tambah Pengguna":
        with st.form("tambah_pengguna_form"):
            st.header("👤 Tambah Pengguna Baru")
            col1, col2 = st.columns(2)
            username = col1.text_input("Username")
            password = col2.text_input("Password", type="password")
            photo = st.file_uploader("Unggah Foto", type=["jpg", "jpeg", "png"])
            submit = st.form_submit_button("Tambah Pengguna")
            
            if submit:
                photo_data = photo.read() if photo else None
                create_user(username, password, photo_data)
                st.success("Pengguna berhasil ditambahkan!")
    
    # Perbarui Laporan
    elif action == "Perbarui Laporan":
        with st.form("perbarui_laporan_form"):
            st.header("🔄 Perbarui Laporan")
            report_id = st.number_input("Report ID", min_value=1, step=1)
            col1, col2 = st.columns(2)
            road_name = col1.text_input("Nama Jalan Baru")
            pothole_severity = col2.selectbox("Tingkat Kerusakan Baru", ["Ringan", "Sedang", "Berat"])
            report_description = st.text_area("Deskripsi Baru")
            submit = st.form_submit_button("Perbarui Laporan")
            
            if submit:
                update_report(report_id, road_name, report_description, pothole_severity)
                st.success("Laporan berhasil diperbarui!")
    
    # Hapus Laporan
    elif action == "Hapus Laporan":
        with st.form("hapus_laporan_form"):
            st.header("🗑️ Hapus Laporan")
            report_id = st.number_input("Report ID", min_value=1, step=1)
            submit = st.form_submit_button("Hapus Laporan")
            
            if submit:
                delete_report(report_id)
                st.success("Laporan berhasil dihapus!")

    # Perbarui Pengguna
    elif action == "Perbarui Pengguna":
        with st.form("perbarui_pengguna_form"):
            st.header("🔄 Perbarui Pengguna")
            user_id = st.number_input("User ID", min_value=1, step=1)
            col1, col2 = st.columns(2)
            username = col1.text_input("Username Baru")
            password = col2.text_input("Password Baru", type="password")
            photo = st.file_uploader("Unggah Foto Baru", type=["jpg", "jpeg", "png"])
            submit = st.form_submit_button("Perbarui Pengguna")
            
            if submit:
                photo_data = photo.read() if photo else None
                update_user(user_id, username, password, photo_data)
                st.success("Pengguna berhasil diperbarui!")
    
    # Hapus Pengguna
    elif action == "Hapus Pengguna":
        with st.form("hapus_pengguna_form"):
            st.header("🗑️ Hapus Pengguna")
            user_id = st.number_input("User ID", min_value=1, step=1)
            submit = st.form_submit_button("Hapus Pengguna")
            
            if submit:
                delete_user(user_id)
                st.success("Pengguna berhasil dihapus!")

# Fungsi untuk mendapatkan data laporan berdasarkan Report_id
def get_report_by_id(report_id):
    connection = create_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                query = """
                SELECT 
                    report_id, road_name, report_description, pothole_severity, 
                    upload_time, image_name, video_name, annotated_image 
                FROM reports
                WHERE report_id = %s
                """
                cursor.execute(query, (report_id,))
                result = cursor.fetchone()
                connection.close()
                return result
        except pymysql.MySQLError as e:
            st.error(f"Gagal mengambil data: {e}")
            connection.close()
            return None
        

# Fungsi untuk menampilkan laporan berdasarkan ID
def show_report_by_id():
    st.subheader("🔎 Cari Laporan Berdasarkan Report ID")
    report_id = st.number_input("Masukkan Report ID", min_value=1, step=1)
    if st.button("Cari Laporan"):
        report = get_report_by_id(report_id)
        if report:
            st.markdown(f"### 🛣️ {report[1]} (ID: {report[0]})")
            st.write(f"**Deskripsi:** {report[2]}")
            st.write(f"**Tingkat Kerusakan:** {report[3]}")
            st.write(f"**Waktu Unggah:** {report[4]}")

            # Tampilkan gambar jika ada
            if report[7]:
                st.image(
                    report[7],
                    caption=report[5] or "Gambar Anotasi",
                    use_container_width=True
                )
            else:
                st.write("*Tidak ada gambar tersedia*")

            # Tampilkan video jika ada
            if report[6]:
                st.write(f"**Video:** {report[6]}")
        else:
            st.warning("Laporan dengan ID ini tidak ditemukan.")

# Fungsi utama dashboard
def main():
    st.set_page_config(page_title="Dashboard Report", page_icon="📊", layout="wide")
    st.title("📊 Dashboard Monitoring Laporan Road Guard")

    # Cek apakah pengguna sudah login
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.error("Silakan login terlebih dahulu!")
    st.stop()  # Hentikan eksekusi jika belum login

    # Tampilkan UI untuk CRUD di sidebar
    crud_ui()

    # Ambil statistik
    total_reports, total_users, total_detections = get_stats()

    # Tampilkan statistik dengan tiga kolom
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("📋 **Total Reports**")
        st.metric(label="Jumlah Laporan", value=total_reports)

    with col2:
        st.success("👤 **Total Users**")
        st.metric(label="Jumlah Pengguna", value=total_users)

    with col3:
        st.warning("🕵️‍♂️ **Total Detections**")
        st.metric(label="Jumlah Deteksi", value=total_detections)

# Fungsi utama dashboard
def main():
    st.set_page_config(page_title="Dashboard Report", page_icon="📊", layout="wide")
    st.title("📊 Dashboard Monitoring ")

    # Ambil statistik
    total_reports, total_users, total_detections = get_stats()

    # Tampilkan statistik dengan tiga kolom
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("📋 **Total Reports**")
        st.metric(label="Jumlah Laporan", value=total_reports)

    with col2:
        st.success("👤 **Total Users**")
        st.metric(label="Jumlah Pengguna", value=total_users)

    with col3:
        st.warning("🕵️‍♂️ **Total Detections**")
        st.metric(label="Jumlah Deteksi", value=total_detections)

    #     # Tampilkan tabel data pengguna
    # st.subheader("👥 Data Pengguna")
    # user_data = get_all_users()
    # st.dataframe(user_data)


def get_all_reports():
    connection = create_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                query = """
                SELECT report_id, road_name, report_description, pothole_severity, upload_time
                FROM reports
                """
                cursor.execute(query)
                result = cursor.fetchall()
                connection.close()
                # Convert result to DataFrame
                return pd.DataFrame(result, columns=["Report ID", "Road Name", "Description", "Severity", "Upload Time"])
        except pymysql.MySQLError as e:
            st.error(f"Error saat mengambil data: {e}")
            connection.close()
            return pd.DataFrame(columns=["Report ID", "Road Name", "Description", "Severity", "Upload Time"])


# Fungsi untuk mendapatkan data kerusakan dari database
def get_damage_data():
    connection = create_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                query = """
                SELECT pothole_severity, COUNT(*) as count 
                FROM reports 
                GROUP BY pothole_severity
                """
                cursor.execute(query)
                result = cursor.fetchall()
                connection.close()
                return pd.DataFrame(result, columns=["Severity", "Count"])
        except pymysql.MySQLError as e:
            st.error(f"Gagal mengambil data kerusakan: {e}")
            connection.close()
            return pd.DataFrame(columns=["Severity", "Count"])

# Fungsi untuk menampilkan chart data kerusakan jalan
def visualize_damage_data():
    st.subheader("📊 Visualisasi Data Kerusakan Jalan")

    # Ambil data kerusakan
    damage_data = get_damage_data()

    if not damage_data.empty:
        # Buat chart menggunakan Altair
        chart = alt.Chart(damage_data).mark_bar().encode(
            x=alt.X("Severity", title="Tingkat Kerusakan"),
            y=alt.Y("Count", title="Jumlah"),
            color=alt.Color("Severity", legend=None)
        ).properties(
            width=600,
            height=400,
            title="Distribusi Tingkat Kerusakan"
        )

        st.altair_chart(chart, use_container_width=True)
    else:
        st.warning("Tidak ada data kerusakan untuk divisualisasikan.")

# Tambahkan visualisasi ke dashboard
if __name__ == '__main__':
    main()

# Tampilkan tabel laporan dan visualisasi data kerusakan secara berdampingan
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("📋 Tabel Laporan")
        report_data = get_all_reports()  
        st.dataframe(report_data)

    with col_right:
        visualize_damage_data()  

    st.markdown("---")

    # Tampilkan laporan berdasarkan ID terlebih dahulu
    show_report_by_id()

    # Tampilkan UI untuk CRUD di sidebar
    crud_ui()
