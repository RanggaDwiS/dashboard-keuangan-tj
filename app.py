import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
import zlib
import base64

# ==========================================
# 1. FUNGSI ENCODE & DECODE (SISTEM SHARING)
# ==========================================
def encode_data(df):
    json_data = df.to_json(orient='split')
    compressed = zlib.compress(json_data.encode())
    return base64.urlsafe_b64encode(compressed).decode()

def decode_data(encoded_str):
    try:
        compressed = base64.urlsafe_b64decode(encoded_str.encode())
        json_data = zlib.decompress(compressed).decode()
        return pd.read_json(json_data, orient='split')
    except:
        return None

# ==========================================
# 2. PEMBERSIHAN DATA KHUSUS KEUANGAN
# ==========================================
def clean_num(v):
    if pd.isna(v) or v == "-": return 0
    if isinstance(v, (int, float)): return float(v)
    
    s = str(v).strip().replace(',', '')
    # Menangani format akuntansi: (100) menjadi -100
    if s.startswith('(') and s.endswith(')'):
        s = '-' + s[1:-1]
    # Menangani persen
    if '%' in s:
        s = float(s.replace('%', '')) / 100
        return s
    
    try: return float(s)
    except: return 0

# ==========================================
# 3. LOGIKA DASHBOARD UTAMA
# ==========================================
st.set_page_config(layout="wide", page_title="Executive Dashboard TJ")

# Gunakan query_params untuk cek apakah ini User B (Viewer)
query_params = st.query_params

if "data" in query_params:
    # --- MODE USER B (VIEWER) ---
    encoded_str = query_params["data"]
    df = decode_data(encoded_str)
    
    if df is not None:
        st.success("✅ Menampilkan Visualisasi Data Shared")
        # Tombol untuk reset/kembali ke awal
        if st.sidebar.button("🔄 Buat Dashboard Baru"):
            st.query_params.clear()
            st.rerun()
        
        # JALANKAN VISUALISASI (Masukkan kode chart kamu di sini)
        st.write("### Data Preview (Hanya Contoh)")
        st.dataframe(df) 
        # (Tambahkan plotly_chart kamu di bawah sini)
    else:
        st.error("Link tidak valid atau data rusak.")
else:
    # --- MODE USER A (UPLOADER) ---
    st.title("📂 Financial Dashboard Uploader")
    uploaded_file = st.file_uploader("Upload Excel Laporan Keuangan", type=['xlsx'])

   if uploaded_file:
    # 1. Baca excel tanpa menentukan kolom dulu
    df_raw = pd.read_excel(uploaded_file, header=None, skiprows=3)
    
    # 2. Ambil hanya 13 kolom pertama (biar tidak error kalau ada kolom kosong di kanan)
    df_raw = df_raw.iloc[:, :13] 
    
    # 3. Baru kasih nama
    df_raw.columns = [
        'Waktu', 'Total Aset', 'Kas Setara Kas', 'COGS Ratio', 'EBITDA', 
        'Net Profit Margin', 'ROI', 'Laba/Rugi', 'Fee', 'Non-Fee', 
        'Total Pendapatan', 'Total Liabilitas', 'Total Ekuitas'
    ]
        
        # Bersihkan semua angka
        for col in df_raw.columns[1:]:
            df_raw[col] = df_raw[col].apply(clean_num)

        # Tombol Share
        st.markdown("---")
        if st.button("🔗 Generate Link untuk di-Share"):
            encoded_link = encode_data(df_raw)
            # URL ini akan otomatis menyesuaikan link website kamu nanti
            base_url = "https://streamline.streamlit.app" # Ganti dengan link asli kamu
            final_link = f"{base_url}/?data={encoded_link}"
            
            st.success("Salin link di bawah ini dan kirim ke User B:")
            st.code(final_link)
            st.info("User B tidak perlu upload file lagi, cukup klik link tersebut.")
        
        # Tampilkan dashboard untuk pengupload
        st.write("### Preview Dashboard Kamu")
        st.dataframe(df_raw)
