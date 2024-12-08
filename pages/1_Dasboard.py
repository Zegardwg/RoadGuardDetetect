import streamlit as st
import pymysql
import pandas as pd
from PIL import Image
import base64
import io
import altair as alt

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
def create_report(road_name, report_description, pothole_severity, user_id):
    connection = create_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                query = """
                INSERT INTO reports (road_name, report_description, pothole_severity, user_id)
                VALUES (%s, %s, %s, %s)
                """
                cursor.execute(query, (road_name, report_description, pothole_severity, user_id))
                connection.commit()
                st.success("Laporan berhasil ditambahkan!")
        except pymysql.MySQLError as e:
            st.error(f"Gagal menambahkan laporan: {e}")
        finally:
            connection.close()

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

# Fungsi untuk menampilkan antarmuka CRUD di sidebar
def crud_ui():
    st.sidebar.header("⚙️ Kelola Data")

    action = st.sidebar.selectbox("Pilih Aksi", ["Tambah Laporan", "Tambah Pengguna"])

    if action == "Tambah Laporan":
        st.sidebar.subheader("📝 Tambah Laporan Baru")
        road_name = st.sidebar.text_input("Nama Jalan")
        report_description = st.sidebar.text_area("Deskripsi Laporan")
        pothole_severity = st.sidebar.selectbox("Tingkat Kerusakan", ["Ringan", "Sedang", "Berat"])
        user_id = st.sidebar.number_input("User ID", min_value=1, step=1)

        if st.sidebar.button("Tambah Laporan"):
            create_report(road_name, report_description, pothole_severity, user_id)

    elif action == "Tambah Pengguna":
        st.sidebar.subheader("👤 Tambah Pengguna Baru")
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        photo = st.sidebar.file_uploader("Unggah Foto", type=["jpg", "jpeg", "png"])

        if st.sidebar.button("Tambah Pengguna"):
            photo_data = photo.read() if photo else None
            create_user(username, password, photo_data)

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
                    use_column_width=True
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
    st.title("📊 Dashboard Monitoring Laporan Kerusakan Jalan dan Data Pengguna")

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

    # Fitur untuk melihat laporan berdasarkan ID
    show_report_by_id()
