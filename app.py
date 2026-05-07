import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re

# ==========================================
# 1. SETUP HALAMAN & CSS PRO (IDENTIK)
# ==========================================
st.set_page_config(layout="wide", page_title="Executive Dashboard TJ", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .block-container { padding: 1rem 2rem 0rem 2rem !important; max-width: 100% !important; }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    div[data-testid="stMetric"] {
        background-color: #ffffff; padding: 10px 15px; border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-left: 5px solid #003366;
        margin-bottom: 10px;
    }
    [data-testid="stMetricLabel"] p { color: #555555 !important; font-weight: 800 !important; font-size: 13px !important; }
    [data-testid="stMetricValue"] div { color: #003366 !important; font-size: 22px !important; font-weight: 900 !important; }
    h6 { color: #333; font-weight: 700; text-align: center; font-size: 14px; margin-top: 5px; margin-bottom: 5px; }
    </style>
""", unsafe_allow_html=True)

# Fungsi Helper (IDENTIK)
def parse_time(t_str):
    t_str = str(t_str).lower()
    year = int(re.search(r'\d{4}', t_str).group()) if re.search(r'\d{4}', t_str) else 2026
    months = {'jan':1, 'feb':2, 'mar':3, 'apr':4, 'mei':5, 'may':5, 'jun':6, 'jul':7, 'agu':8, 'aug':8, 'sep':9, 'okt':10, 'oct':10, 'nov':11, 'des':12, 'dec':12}
    month = next((v for k, v in months.items() if k in t_str), 12)
    return year * 100 + month

def clean_num(v):
    if pd.isna(v) or v == "-": return 0
    try: return float(str(v).replace(',', '').replace('(', '-').replace(')', ''))
    except: return 0

# ==========================================
# 2. FUNGSI RENDER DASHBOARD (IDENTIK)
# ==========================================
def render_full_dashboard(df):
    df['Waktu'] = df['Waktu'].astype(str).str.replace('\n', ' ')
    for col in df.columns[3:]: 
        if col in df.columns: df[col] = df[col].apply(clean_num)
    
    # Header & Filter
    t1, t2, t3, t4 = st.columns([3, 1.5, 1.5, 1.5])
    list_kat = df['Kategori'].dropna().unique()
    sel_kat = t2.selectbox("Kategori", list_kat)
    df_kat = df[df['Kategori'] == sel_kat]
    sel_waktu = t3.selectbox("Periode", df_kat['Waktu'].unique())
    row = df_kat[df_kat['Waktu'] == sel_waktu].iloc[0]
    
    t1.markdown(f"<h2 style='color:#003366; margin:0;'>🏢 {sel_kat}</h2>", unsafe_allow_html=True)
    st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)
    
    # Grid Visualisasi (Logika Plotly Anda)
    c_kiri, c_tengah, c_kanan = st.columns([1.2, 1.0, 1.8])
    def fmt_juta(val):
        s = f"{val/1e6:,.2f}"
        return "Rp " + s.replace(',', 'X').replace('.', ',').replace('X', '.')

    with c_kiri:
        m1, m2 = st.columns(2)
        m1.metric("Total Aset", fmt_juta(row['Total Aset']))
        m2.metric("Kas & Setara", fmt_juta(row['Kas Setara Kas']))
        st.markdown("<h6>🏢 Kontribusi Pendapatan</h6>", unsafe_allow_html=True)
        fig_cont = px.bar(x=[row['Fee'], row['Non-Fee']], y=['Fee', 'Non-Fee'], orientation='h', text_auto=',.0f')
        fig_cont.update_traces(marker_color='#003366', textposition='inside')
        fig_cont.update_layout(height=250, margin=dict(t=20,b=0,l=0,r=20), xaxis_visible=False)
        st.plotly_chart(fig_cont, use_container_width=True)

    with c_tengah:
        fig_g1 = go.Figure(go.Indicator(mode="gauge+number", value=row['COGS Ratio']*100, number={'suffix': "%"}, gauge={'axis':{'range':[0,100]}, 'bar':{'color':"#E63946"}}))
        fig_g1.update_layout(height=180, margin=dict(t=30,b=0,l=20,r=20))
        st.plotly_chart(fig_g1, use_container_width=True)
        st.markdown("<h6>COGS Ratio (%)</h6>", unsafe_allow_html=True)

    with c_kanan:
        fig_combo = make_subplots(specs=[[{"secondary_y": True}]])
        fig_combo.add_trace(go.Bar(x=df_kat['Waktu'], y=df_kat['Total Pendapatan'], name='Pendapatan', marker_color='#8ECAE6'), secondary_y=False)
        fig_combo.add_trace(go.Scatter(x=df_kat['Waktu'], y=df_kat['Laba/Rugi'], name='Laba/Rugi', line=dict(color='#023047', width=4)), secondary_y=True)
        fig_combo.update_layout(height=300, margin=dict(t=30, b=0, l=0, r=0), legend=dict(orientation="h", yanchor="bottom", y=1.1, xanchor="center", x=0.5))
        st.plotly_chart(fig_combo, use_container_width=True)
        st.markdown("<h6>📈 Tren Pendapatan vs Laba/Rugi</h6>", unsafe_allow_html=True)

# ==========================================
# 3. LOGIKA UTAMA (SUMBER DATA)
# ==========================================
st.title("📂 Executive Dashboard")

# Mode Input: Pilih Link Google Sheets atau File Upload
input_mode = st.radio("Pilih Sumber Data:", ["Link Google Sheets", "Upload Excel (.xlsx)"])

if input_mode == "Link Google Sheets":
    sheet_url = st.text_input("Tempel Link Google Sheets Anda di Sini:")
    if sheet_url:
        try:
            # Mengubah link edit menjadi link export CSV otomatis
            if "/edit" in sheet_url:
                csv_url = sheet_url.replace('/edit', '/export?format=csv').split('?')[0]
                if "usp=sharing" in sheet_url:
                    # Menangani gid jika ada banyak sheet
                    gid = re.search(r'gid=(\d+)', sheet_url)
                    csv_url += f"&gid={gid.group(1)}" if gid else ""
            else:
                csv_url = sheet_url

            df = pd.read_csv(csv_url, header=None, skiprows=3)
            df = df.iloc[:, :15] # Ambil 15 kolom
            df.columns = ['Waktu', 'Kategori', 'LK', 'Total Aset', 'Kas Setara Kas', 'COGS Ratio', 'EBITDA', 'Net Profit Margin', 'ROI', 'Laba/Rugi', 'Fee', 'Non-Fee', 'Total Pendapatan', 'Total Liabilitas', 'Total Ekuitas']
            
            render_full_dashboard(df)
            st.success("✅ Data berhasil dimuat dari Google Sheets!")
        except Exception as e:
            st.error(f"Gagal membaca link. Pastikan Sheet sudah di-share 'Anyone with the link'. Error: {e}")

else:
    file = st.file_uploader("Upload Excel", type=['xlsx'])
    if file:
        df = pd.read_excel(file, header=None, skiprows=3)
        df = df.iloc[:, :15]
        df.columns = ['Waktu', 'Kategori', 'LK', 'Total Aset', 'Kas Setara Kas', 'COGS Ratio', 'EBITDA', 'Net Profit Margin', 'ROI', 'Laba/Rugi', 'Fee', 'Non-Fee', 'Total Pendapatan', 'Total Liabilitas', 'Total Ekuitas']
        render_full_dashboard(df)
