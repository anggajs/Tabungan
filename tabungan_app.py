import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime
import qrcode
from PIL import Image

USER_FILE = "user.json"
DATA_FILE = "data_tabungan.csv"

# ------- Helper Functions -------
def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f)

def verify_user(username, password):
    users = load_users()
    if username in users and users[username]["password"] == password:
        return users[username]["role"]
    return None

def register_user(username, password, role="user"):
    users = load_users()
    users[username] = {"password": password, "role": role}
    save_users(users)

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=["Tanggal", "User", "Jumlah (Rp)", "Keterangan"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def generate_qr(data):
    # Pastikan folder 'images' ada
    if not os.path.exists("images"):
        os.makedirs("images")

    # Tentukan nama file QR dan simpan di folder 'images'
    file_name = f"images/qr_{data.replace(':', '_').replace(' ', '_')}.png"
    img = qrcode.make(data)
    img.save(file_name)
    return file_name

# ------- Session Defaults -------
for key in ["logged_in", "username", "role", "login_successful"]:
    if key not in st.session_state:
        st.session_state[key] = False if key == "logged_in" else ""

# ------- Login Page -------
def login_page():
    st.title("🔐 Login Aplikasi Tabungan Kita")

    tab_login, tab_register = st.tabs(["Login", "Daftar Akun"])

    with tab_login:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            role = verify_user(username, password)
            if role:
                st.session_state.username = username
                st.session_state.role = role
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Username atau password salah.")

    with tab_register:
        new_user = st.text_input("Username Baru")
        new_pass = st.text_input("Password Baru", type="password")
        if st.button("Daftar"):
            users = load_users()
            if new_user in users:
                st.warning("Username sudah digunakan.")
            else:
                register_user(new_user, new_pass)
                st.success("Akun berhasil dibuat. Silakan login.")

# ------- Main App -------
def tabungan_app():
    st.title("💰 Aplikasi Tabungan Ke BALIII")

    df = load_data()

    st.sidebar.markdown(f"👋 Selamat datang, **{st.session_state.username}**")
    if st.sidebar.button("🚪 Logout"):
        for key in ["logged_in", "username", "role"]:
            st.session_state[key] = False if key == "logged_in" else ""
        st.rerun()

    # Tambah Tabungan
    st.subheader("📥 Tambah Tabungan")
    jumlah = st.number_input("Jumlah Tabungan (Rp)", min_value=10000, step=10000)
    ket = st.selectbox("Metode Tabungan", ["Cash", "Transfer (TF)"])
    simpan = st.button("Simpan Tabungan")
    if simpan:
        new_entry = {
            "Tanggal": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "User": st.session_state.username,
            "Jumlah (Rp)": jumlah,
            "Keterangan": ket
        }
        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        save_data(df)
        st.success("✅ Tabungan berhasil disimpan.")
        
        # Tampilkan QR Code
        qr_content = f"{st.session_state.username} - Rp{jumlah:,} - {ket}"
        qr_file = generate_qr(qr_content)
        st.image(Image.open(qr_file), caption="QR Transaksi", use_column_width=False)

   # Riwayat & Statistik
    st.subheader("📊 Riwayat & Total Tabungan")

    if st.session_state.role == "admin":
        total = df["Jumlah (Rp)"].sum()
        st.write(f"💼 **Total Semua Saldo:** Rp {int(total):,}")

        # Tampilkan dengan tombol hapus
        for i, row in df[::-1].reset_index().iterrows():
            col1, col2 = st.columns([8, 1])
            with col1:
                st.write(f"📅 {row['Tanggal']} | 👤 {row['User']} | 💵 Rp {int(row['Jumlah (Rp)']):,} | 📝 {row['Keterangan']}")
            with col2:
                if st.button("🗑️", key=f"hapus_{row['index']}"):
                    df = df.drop(index=row['index'])
                    df = df.reset_index(drop=True)
                    save_data(df)
                    st.success("✅ Entri berhasil dihapus.")
                    st.rerun()

    else:
        user_df = df[df["User"] == st.session_state.username]
        total_user = user_df["Jumlah (Rp)"].sum()
        st.write(f"💼 **Saldo Anda:** Rp {int(total_user):,}")
        st.dataframe(user_df[::-1])


    # Admin Panel
    if st.session_state.role == "admin":
        st.subheader("⚙️ Admin Panel")

        # Manajemen User
        st.markdown("### 👥 Manajemen Pengguna")
        users = load_users()
        st.json(users)

        # Export & Reset
        col1, col2 = st.columns(2)
        with col1:
            st.download_button("⬇️ Download Data", df.to_csv(index=False).encode(), file_name="data_tabungan.csv")
        with col2:
            if st.button("🗑️ Reset Semua Data"):
                os.remove(DATA_FILE)
                st.success("Data berhasil dihapus.")
                st.rerun()

# ------- Jalankan Aplikasi -------
if not st.session_state.logged_in:
    login_page()
else:
    tabungan_app()
