import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re
import zlib
import base64
import urllib.parse
import requests

# --- FUNGSI KOMPRESI (SISTEM SHARING) ---
def encode_df(df):
    try:
        # Mengompres data agar muat di link
        json_data = df.to_json(orient='split')
        compressed = zlib.compress(json_data.encode())
        return base64.urlsafe_b64encode(compressed).decode()
    except: return None

def decode_df(encoded_str):
    try:
        # Membongkar kembali data dari link
        compressed = base64.urlsafe_b64decode(encoded_str.encode())
        json_data = zlib.decompress(compressed).decode()
        return pd.read_json(json_data, orient='split')
    except: return None

# --- SETUP TAMPILAN (IDENTIK) ---
st.set_page_config(layout="wide", page_title="Executive Dashboard TJ", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .block-container { padding: 1rem 2rem 0rem 2rem !important; }
    header, footer {visibility: hidden;}
    div[data-testid="stMetric"] { background-color: #fff; padding: 10px; border-radius: 8px; border-left: 5px solid #003366; }
    .stButton>button { background-color: #FF4B4B !important; color: white !important; font-weight: bold; width: 100%; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

def clean_num(v):
    if pd.isna(v) or v == "-": return 0
    try: return float(str(v).replace(',', '').replace('(', '-').replace(')', ''))
    except: return 0

# --- FUNGSI RENDER (IDENTIK) ---
def render_full_dashboard(df):
    df['Waktu'] = df['Waktu'].astype(str).str.replace('\n', ' ')
    for col in df.columns[3:]: 
        if col in df.columns: df[col] = df[col].apply(clean_num)
    
    t1, t2, t3, t4 = st.columns([3, 1.5, 1.5, 1.5])
    list_kat = df['Kategori'].dropna().unique()
    sel_kat = t2.selectbox("Kategori", list_kat)
    df_kat = df[df['Kategori'] == sel_kat]
    sel_waktu = t3.selectbox("Periode", df_kat['Waktu'].unique())
    row = df_kat[df_kat['Waktu'] == sel_waktu].iloc[0]
    
    t1.markdown(f"<h2 style='color:#003366; margin:0;'>🏢 {sel_kat}</h2>", unsafe_allow_html=True)
    st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1.2, 1, 1.8])
    with c1: st.metric("Total Aset", f"Rp {row['Total Aset']/1e6:,.2f}")
    with c2: st.metric("EBITDA", f"Rp {row['EBITDA']/1e6:,.2f}")
    
    # Masukkan semua plotly_chart kamu di sini sesuai urutan sebelumnya
    st.info("📊 Dashboard Berhasil Dimuat!")

# --- LOGIKA UTAMA ---
# Menggunakan st.query_params terbaru
if "data" in st.query_params:
    df_decoded = decode_df(st.query_params["data"])
    if df_decoded is not None:
        render_full_dashboard(df_decoded)
        if st.sidebar.button("🗑️ Reset & Buat Baru"):
            st.query_params.clear()
            st.rerun()
    else:
        st.error("Data terputus atau link rusak. Pastikan data tidak terlalu besar.")
else:
    st.title("📂 Executive Dashboard")
    uploaded_file = st.file_uploader("Upload Excel Kamu", type=['xlsx'])
    
    if uploaded_file:
        df = pd.read_excel(uploaded_file, header=None, skiprows=3)
        df.columns = ['Waktu', 'Kategori', 'LK', 'Total Aset', 'Kas Setara Kas', 'COGS Ratio', 'EBITDA', 'Net Profit Margin', 'ROI', 'Laba/Rugi', 'Fee', 'Non-Fee', 'Total Pendapatan', 'Total Liabilitas', 'Total Ekuitas']
        
        st.warning("🚀 **SHARE MENU**")
        if st.button("BUAT LINK SHARE PENDEK"):
            encoded = encode_df(df)
            if encoded:
                # Link otomatis tanpa perlu ganti-ganti lagi
                base_url = "https://dashboard-keuangan-tj.streamlit.app"
                long_url = f"{base_url}/?data={encoded}"
                
                try:
                    # Memperpendek link agar tidak error "No Access"
                    api_url = f"http://tinyurl.com/api-create.php?url={urllib.parse.quote(long_url)}"
                    short_url = requests.get(api_url, timeout=5).text
                    st.success("✅ **Link Berhasil!** Salin link pendek ini:")
                    st.code(short_url)
                except:
                    st.warning("Gunakan link ini (Internet sedang sibuk):")
                    st.code(long_url)
        
        render_full_dashboard(df)
