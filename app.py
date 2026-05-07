import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re
import zlib
import base64

# ==========================================
# FUNGSI UNTUK SHARING (TIDAK MERUBAH TAMPILAN)
# ==========================================
def encode_df(df):
    """Mengompres data excel ke teks untuk URL"""
    json_data = df.to_json(orient='split')
    compressed = zlib.compress(json_data.encode())
    return base64.urlsafe_b64encode(compressed).decode()

def decode_df(encoded_str):
    """Mengembalikan teks URL ke data excel"""
    try:
        compressed = base64.urlsafe_b64decode(encoded_str.encode())
        json_data = zlib.decompress(compressed).decode()
        return pd.read_json(json_data, orient='split')
    except:
        return None

# ==========================================
# 1. SETUP HALAMAN & CSS PRO (IDENTIK)
# ==========================================
st.set_page_config(layout="wide", page_title="Executive Dashboard TJ", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .block-container { padding: 1rem 2rem 0rem 2rem !important; max-width: 100% !important; }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Card Metrik */
    div[data-testid="stMetric"] {
        background-color: #ffffff; padding: 10px 15px; border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-left: 5px solid #003366;
        margin-bottom: 10px;
    }
    [data-testid="stMetricLabel"] p { color: #555555 !important; font-weight: 800 !important; font-size: 13px !important; }
    [data-testid="stMetricValue"] div { color: #003366 !important; font-size: 22px !important; font-weight: 900 !important; }
    
    /* Judul Chart */
    h6 { color: #333; font-weight: 700; text-align: center; font-size: 14px; margin-top: 5px; margin-bottom: 5px; }
    </style>
""", unsafe_allow_html=True)

# Fungsi Pengurut Waktu (IDENTIK)
def parse_time(t_str):
    t_str = str(t_str).lower()
    year = int(re.search(r'\d{4}', t_str).group()) if re.search(r'\d{4}', t_str) else 2025
    months = {'jan':1, 'feb':2, 'mar':3, 'apr':4, 'mei':5, 'may':5, 'jun':6, 'jul':7, 'agu':8, 'aug':8, 'sep':9, 'okt':10, 'oct':10, 'nov':11, 'des':12, 'dec':12}
    month = next((v for k, v in months.items() if k in t_str), 12)
    return year * 100 + month

# Fungsi Clean Num (IDENTIK)
def clean_num(v):
    if pd.isna(v): return 0
    try: return float(v)
    except: return v

# ==========================================
# FUNGSI UNTUK MERENDER DASHBOARD (LOGIKA ANDA)
# ==========================================
def render_full_dashboard(df):
    # Logika Pembersihan Anda (IDENTIK)
    df['Waktu'] = df['Waktu'].astype(str).str.replace('\n', ' ')
    for col in df.columns[3:]: df[col] = df[col].apply(clean_num)
    
    # Urutkan Waktu Kronologis
    df['SortKey'] = df['Waktu'].apply(parse_time)
    df = df.sort_values('SortKey').drop(columns=['SortKey'])
    
    # --- HEADER & FILTER ---
    t1, t2, t3, t4 = st.columns([3, 1.5, 1.5, 1.5])
    
    list_kat = df['Kategori'].dropna().unique()
    sel_kat = t2.selectbox("Kategori", list_kat)
    df_kat = df[df['Kategori'] == sel_kat]
    
    list_waktu = df_kat['Waktu'].unique()
    sel_waktu = t3.selectbox("Periode", list_waktu)
    row = df_kat[df_kat['Waktu'] == sel_waktu].iloc[0]
    
    t1.markdown(f<h2 style='color:#003366; margin:0;'> {sel_kat}</h2>, unsafe_allow_html=True)
    
    if pd.notna(row['LK']):
        t4.markdown(f"<a href='{row['LK']}' target='_blank'><button style='width:100%; margin-top:25px; padding:8px; background-color:#FFCC00; color:#003366; font-weight:bold; border:none; border-radius:5px; cursor:pointer;'>DOKUMEN LAPORAN KEUANGAN</button></a>", unsafe_allow_html=True)

    st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)

    # --- GRID DASHBOARD ---
    c_kiri, c_tengah, c_kanan = st.columns([1.2, 1.0, 1.8])

    def fmt_juta(val):
        s = f"{val/1e6:,.2f}"
        return "Rp " + s.replace(',', 'X').replace('.', ',').replace('X', '.')

    # --- KOLOM KIRI ---
    with c_kiri:
        m1, m2 = st.columns(2)
        m1.metric("Total Aset (Juta)", fmt_juta(row['Total Aset']))
        m2.metric("Kas & Setara Kas (Juta)", fmt_juta(row['Kas Setara Kas']))
        m3, m4 = st.columns(2)
        m3.metric("EBITDA (Juta)", fmt_juta(row['EBITDA']))
        roi_str = f"{row['ROI']*100:.2f}".replace('.', ',')
        m4.metric("ROI (%)", f"{roi_str}%")
        
        st.markdown("<h6>🏢 Kontribusi Pendapatan</h6>", unsafe_allow_html=True)
        fig_cont = px.bar(x=[row['Fee'], row['Non-Fee']], y=['Fee', 'Non-Fee'], orientation='h', text_auto=',.0f')
        fig_cont.update_traces(marker_color='#003366', textposition='inside')
        fig_cont.update_layout(separators=",.", height=250, margin=dict(t=20,b=0,l=0,r=20), xaxis_visible=False, yaxis_title=None)
        st.plotly_chart(fig_cont, use_container_width=True)

    # --- KOLOM TENGAH ---
    with c_tengah:
        fig_g1 = go.Figure(go.Indicator(mode="gauge+number", value=row['COGS Ratio']*100, number={'suffix': "%"}, gauge={'axis':{'range':[0,100]}, 'bar':{'color':"#E63946"}}))
        fig_g1.update_layout(separators=",.", height=180, margin=dict(t=30,b=0,l=20,r=20))
        st.plotly_chart(fig_g1, use_container_width=True)
        st.markdown("<h6>COGS Ratio (%)</h6>", unsafe_allow_html=True)
        
        fig_g2 = go.Figure(go.Indicator(mode="gauge+number", value=row['Net Profit Margin']*100, number={'suffix': "%"}, gauge={'axis':{'range':[-100,100]}, 'bar':{'color':"#003366"}}))
        fig_g2.update_layout(separators=",.", height=180, margin=dict(t=30,b=0,l=20,r=20))
        st.plotly_chart(fig_g2, use_container_width=True)
        st.markdown("<h6>Net Profit Margin (%)</h6>", unsafe_allow_html=True)

    # --- KOLOM KANAN ---
    with c_kanan:
        fig_combo = make_subplots(specs=[[{"secondary_y": True}]])
        fig_combo.add_trace(go.Bar(x=df_kat['Waktu'], y=df_kat['Total Pendapatan'], name='Total Pendapatan', marker_color='#8ECAE6', text=df_kat['Total Pendapatan'], texttemplate='%{text:,.0f}', textposition='inside'), secondary_y=False)
        fig_combo.add_trace(go.Scatter(x=df_kat['Waktu'], y=df_kat['Laba/Rugi'], name='Laba / Rugi', mode='lines+markers+text', line=dict(color='#023047', width=4), marker=dict(size=10, line=dict(width=2, color='white')), text=df_kat['Laba/Rugi'], texttemplate='%{text:,.0f}', textposition='top center'), secondary_y=True)
        fig_combo.update_layout(separators=",.", height=300, margin=dict(t=30, b=0, l=0, r=0), legend=dict(orientation="h", yanchor="bottom", y=1.1, xanchor="center", x=0.5), hovermode="x unified", xaxis_title=None)
        fig_combo.update_yaxes(visible=False, secondary_y=False)
        fig_combo.update_yaxes(visible=False, secondary_y=True)
        st.plotly_chart(fig_combo, use_container_width=True)
        st.markdown("<h6>📈 Tren Pendapatan vs Laba/Rugi (Combo)</h6>", unsafe_allow_html=True)
        
        df_stack = pd.melt(df_kat, id_vars=['Waktu'], value_vars=['Total Liabilitas', 'Total Ekuitas'])
        fig_bar = px.bar(df_stack, x='Waktu', y='value', color='variable', color_discrete_map={'Total Liabilitas':'#E63946', 'Total Ekuitas':'#2A9D8F'}, text_auto=',.0f')
        fig_bar.update_traces(textposition='inside')
        fig_bar.update_layout(separators=",.", barmode='group', height=200, margin=dict(t=10,b=0,l=0,r=0), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.1, xanchor="right", x=1, title=""), yaxis_visible=False, xaxis_title=None)
        st.plotly_chart(fig_bar, use_container_width=True)
        st.markdown("<h6>⚖️ Liabilitas & Ekuitas</h6>", unsafe_allow_html=True)

# ==========================================
# 2. PROSES LOGIKA HALAMAN (UPLOAD ATAU VIEW)
# ==========================================
params = st.query_params

if "data" in params:
    # --- MODE VIEW (USER B) ---
    df_decoded = decode_df(params["data"])
    if df_decoded is not None:
        render_full_dashboard(df_decoded)
        if st.sidebar.button("🗑️ Hapus Tampilan & Buat Baru"):
            st.query_params.clear()
            st.rerun()
    else:
        st.error("Link tidak valid atau data rusak.")
else:
    # --- MODE UPLOAD (USER A) ---
    area_upload = st.empty()
    uploaded_file = area_upload.file_uploader("Silahkan Unggah File Untuk Di Visualisasikan", type=['xlsx', 'csv'])

    if uploaded_file:
        area_upload.empty()
        try:
            df = pd.read_excel(uploaded_file, header=None, skiprows=3)
            df.columns = [
                'Waktu', 'Kategori', 'LK', 'Total Aset', 'Kas Setara Kas', 'COGS Ratio', 'EBITDA', 
                'Net Profit Margin', 'ROI', 'Laba/Rugi', 'Fee', 'Non-Fee', 
                'Total Pendapatan', 'Total Liabilitas', 'Total Ekuitas'
            ]
            
            # Tampilkan tombol share (opsional - diletakkan di sidebar agar rapi)
            with st.sidebar:
                st.write("### 🔗 Share Visualisasi")
                if st.button("Generate Share Link"):
                    encoded_string = encode_df(df)
                    # GANTI URL DI BAWAH INI DENGAN LINK STREAMLIT ANDA
                    base_url = "https://executive-tj.streamlit.app" 
                    share_url = f"{base_url}/?data={encoded_string}"
                    st.code(share_url, language="text")
                    st.success("Salin link di atas dan kirimkan ke orang lain.")

            # Jalankan tampilan dashboard
            render_full_dashboard(df)

        except Exception as e:
            st.error(f"Error: {e}")
