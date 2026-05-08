import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re
import requests
import json

# ==========================================
# 1. SETUP HALAMAN & CSS PRO
# ==========================================
st.set_page_config(layout="wide", page_title="FINS (Financial Index and Navigation for Subsidiaries)", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .block-container { padding: 1rem 2rem 0rem 2rem !important; max-width: 100% !important; }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    h6 { font-weight: 700; text-align: center; font-size: 14px; margin-top: 0px; margin-bottom: 0px; }
    .chart-title { margin-bottom: 30px; } 
    </style>
""", unsafe_allow_html=True)

def parse_time(t_str):
    t_str = str(t_str).lower()
    year = int(re.search(r'\d{4}', t_str).group()) if re.search(r'\d{4}', t_str) else 2025
    months = {'jan':1, 'feb':2, 'mar':3, 'apr':4, 'mei':5, 'may':5, 'jun':6, 'jul':7, 'agu':8, 'aug':8, 'sep':9, 'okt':10, 'oct':10, 'nov':11, 'des':12, 'dec':12}
    month = next((v for k, v in months.items() if k in t_str), 12)
    return year * 100 + month

def clean_num(v):
    if pd.isna(v) or str(v).strip() == '': return 0.0
    try:
        if isinstance(v, (int, float)): return float(v)
        v_str = str(v).replace('Rp', '').replace(' ', '').strip()
        if '.' in v_str and ',' in v_str:
            v_str = v_str.replace('.', '').replace(',', '.')
        elif ',' in v_str:
            v_str = v_str.replace(',', '')
        elif '.' in v_str and v_str.count('.') > 1: 
            v_str = v_str.replace('.', '')
        return float(v_str)
    except: 
        return 0.0 

# ==========================================
# 2. FUNGSI VISUALISASI
# ==========================================
def render_dashboard(df):
    t1, t2, t3, t4 = st.columns([3, 1.5, 1.5, 1.5])
    
    list_kat = df['Kategori'].dropna().unique()
    sel_kat = t2.selectbox("Kategori", list_kat)
    df_kat = df[df['Kategori'] == sel_kat]
    
    list_waktu = df_kat['Waktu'].unique()
    sel_waktu = t3.selectbox("Periode", list_waktu)
    row = df_kat[df_kat['Waktu'] == sel_waktu].iloc[0]
    
    t1.markdown(f"<h2 style='color:#3B82F6; margin:0;'>🏢 {sel_kat}</h2>", unsafe_allow_html=True)
    
    if pd.notna(row['LK']):
        t4.markdown(f"<a href='{row['LK']}' target='_blank'><button style='width:100%; margin-top:25px; padding:8px; background-color:#FFCC00; color:#003366; font-weight:bold; border:none; border-radius:5px;'>DOKUMEN LAPORAN KEUANGAN</button></a>", unsafe_allow_html=True)

    st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)
    c_kiri, c_tengah, c_kanan = st.columns([1.2, 1.0, 1.8])

    def fmt_juta(val):
        val = float(val) 
        s = f"{val/1e6:,.2f}"
        return "Rp " + s.replace(',', 'X').replace('.', ',').replace('X', '.')

    def render_metric(label, value_str, val_num):
        val_color = "#EF4444" if float(val_num) < 0 else "#003366"
        html = f"""
        <div style='background-color: #ffffff; padding: 10px 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-left: 5px solid #003366; margin-bottom: 10px;'>
            <p style='color: #555555; font-weight: 800; font-size: 13px; margin:0; line-height: 1.2; padding-bottom:5px;'>{label}</p>
            <div style='color: {val_color}; font-size: 22px; font-weight: 900; margin:0; line-height: 1.2;'>{value_str}</div>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)

    with c_kiri:
        m1, m2 = st.columns(2)
        with m1: render_metric("Total Aset (Juta)", fmt_juta(row['Total Aset']), row['Total Aset'])
        with m2: render_metric("Kas & Setara Kas (Juta)", fmt_juta(row['Kas Setara Kas']), row['Kas Setara Kas'])
        
        m3, m4 = st.columns(2)
        with m3: render_metric("EBITDA (Juta)", fmt_juta(row['EBITDA']), row['EBITDA'])
        with m4:
            roi_str = f"{float(row['ROI'])*100:.2f}".replace('.', ',') + "%"
            render_metric("ROI (%)", roi_str, float(row['ROI']))
        
        is_itj = "integrasi" in str(sel_kat).lower()
        if is_itj and 'Rev3' in df.columns:
            x_vals = [row['Rev1'], row['Rev2'], row['Rev3']]
            y_vals = ['Jasa Konsultan', 'Tenaga Alih Daya', 'Komersial Kawasan']
            judul_kontribusi = "🏢 Kontribusi Pendapatan"
        else:
            x_vals = [row['Rev1'], row['Rev2']]
            y_vals = ['Transaction Fee', 'Non-Transaction']
            judul_kontribusi = "🏢 Kontribusi Pendapatan (Fee vs Non-Fee)"

        fig_cont = px.bar(x=x_vals, y=y_vals, orientation='h')
        fig_cont.update_traces(marker_color='#003366', text=x_vals, textposition='outside', texttemplate='<b>%{text:,.0f}</b>', cliponaxis=False)
        fig_cont.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', separators=",.", height=260, margin=dict(t=20,b=0,l=0,r=60), xaxis_title=None, yaxis_title=None, xaxis_visible=False, xaxis=dict(showgrid=False), yaxis=dict(showgrid=False))
        st.plotly_chart(fig_cont, use_container_width=True)
        st.markdown(f"<div class='chart-title'><h6>{judul_kontribusi}</h6></div>", unsafe_allow_html=True)

    with c_tengah:
        cogs_val = float(row['COGS Ratio']) * 100
        cogs_color = "#EF4444" if cogs_val < 0 else "#3B82F6"
        fig_g1 = go.Figure(go.Indicator(mode="gauge+number", value=cogs_val, gauge={'axis':{'range':[-100,100]}, 'bar':{'color':cogs_color}}))
        fig_g1.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', separators=",.", height=140, margin=dict(t=20,b=0,l=20,r=20))
        st.plotly_chart(fig_g1, use_container_width=True)
        st.markdown("<div class='chart-title'><h6>COGS Ratio (%)</h6></div>", unsafe_allow_html=True)
        
        npm_val = float(row['Net Profit Margin']) * 100
        npm_color = "#EF4444" if npm_val < 0 else "#3B82F6" 
        fig_g2 = go.Figure(go.Indicator(mode="gauge+number", value=npm_val, gauge={'axis':{'range':[-100,100]}, 'bar':{'color': npm_color}}))
        fig_g2.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', separators=",.", height=140, margin=dict(t=10,b=0,l=20,r=20))
        st.plotly_chart(fig_g2, use_container_width=True)
        st.markdown("<div class='chart-title'><h6>Net Profit Margin (%)</h6></div>", unsafe_allow_html=True)

    with c_kanan:
        st.markdown("<h6>📈 Tren Pendapatan vs Laba/Rugi (Combo)</h6>", unsafe_allow_html=True)
        fig_combo = make_subplots(specs=[[{"secondary_y": True}]])
        waktu_list = df_kat['Waktu'].tolist()
        pend_list = df_kat['Total Pendapatan'].tolist()
        lr_list = df_kat['Laba/Rugi'].tolist()

        fig_combo.add_trace(go.Bar(x=waktu_list, y=pend_list, name='Total Pendapatan', marker_color='#003366', text=pend_list, texttemplate='<b>%{text:,.0f}</b>', textposition='outside', cliponaxis=False), secondary_y=False)

        for i in range(1, len(waktu_list)):
            x_seg = [waktu_list[i-1], waktu_list[i]]
            y_seg = [lr_list[i-1], lr_list[i]]
            seg_color = '#EF4444' if y_seg[1] < y_seg[0] else '#3B82F6'
            fig_combo.add_trace(go.Scatter(x=x_seg, y=y_seg, mode='lines', line=dict(color=seg_color, width=4, shape='spline'), showlegend=False, hoverinfo='skip'), secondary_y=True)

        lr_colors = ['#EF4444' if val < 0 else '#3B82F6' for val in lr_list] 
        fig_combo.add_trace(go.Scatter(x=waktu_list, y=lr_list, name='Laba / Rugi', mode='markers+text', marker=dict(size=12, color=lr_colors, line=dict(width=2, color='#FFFFFF')), text=lr_list, texttemplate='<b>%{text:,.0f}</b>', textposition='top center', textfont=dict(color=lr_colors, size=14), cliponaxis=False), secondary_y=True)

        max_pend = max(pend_list) if len(pend_list) > 0 else 1
        max_lr = max(lr_list) if len(lr_list) > 0 else 1
        min_lr = min(lr_list) if len(lr_list) > 0 else 0
        pad_lr = (max_lr - min_lr) * 0.35 if max_lr != min_lr else abs(max_lr) * 0.35

        fig_combo.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', separators=",.", height=320, margin=dict(t=40, b=0, l=0, r=0), legend=dict(orientation="h", yanchor="bottom", y=1.1, xanchor="center", x=0.5), hovermode="x unified", xaxis_title=None)
        fig_combo.update_yaxes(showgrid=False, visible=False, secondary_y=False, range=[0, max_pend * 1.30])
        fig_combo.update_yaxes(showgrid=False, visible=False, secondary_y=True, range=[min_lr - pad_lr, max_lr + pad_lr])
        fig_combo.update_xaxes(showgrid=False)
        st.plotly_chart(fig_combo, use_container_width=True)

        df_stack = pd.melt(df_kat, id_vars=['Waktu'], value_vars=['Total Liabilitas', 'Total Ekuitas'])
        fig_bar = px.bar(df_stack, x='Waktu', y='value', color='variable', color_discrete_map={'Total Liabilitas':'#3B82F6', 'Total Ekuitas':'#003366'})
        fig_bar.update_traces(textposition='inside', texttemplate='<b>%{y:,.0f}</b>', textfont=dict(color='white'))
        fig_bar.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', separators=",.", barmode='group', height=240, margin=dict(t=10,b=0,l=0,r=0), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.1, xanchor="right", x=1, title=""), xaxis_title=None, yaxis_title=None, xaxis=dict(showgrid=False), yaxis=dict(showgrid=False))
        st.plotly_chart(fig_bar, use_container_width=True)
        st.markdown("<div class='chart-title'><h6>⚖️ Liabilitas & Ekuitas</h6></div>", unsafe_allow_html=True)

# ==========================================
# 3. ALUR KERJA UTAMA (PINDAH SERVER KE NPOINT)
# ==========================================
params = st.query_params

# JIKA ADA LINK SHARE YANG DIBUKA
if "id" in params:
    paste_id = params["id"]
    try:
        # Menarik data dari server npoint
        url_target = f"https://api.npoint.io/{paste_id}"
        req = requests.get(url_target, timeout=10)
        
        if req.status_code == 200:
            # Npoint otomatis membaca sebagai JSON
            raw_data = req.json()
            df_shared = pd.DataFrame(raw_data)
            
            st.info("👀 Anda sedang melihat Dashboard (Versi Link)")
            if st.button("🗑️ Hapus Tampilan & Buat Baru"):
                st.query_params.clear()
                st.rerun()
                
            render_dashboard(df_shared)
        else:
            st.error(f"Gagal memuat! Data tidak ditemukan. (Status Code: {req.status_code})")
            
    except Exception as e:
        st.error(f"Error Sistem saat menarik data: {e}")

# JIKA TIDAK ADA LINK (MODE UPLOAD NORMAL)
else:
    area_upload = st.empty()
    uploaded_file = area_upload.file_uploader("Silahkan Unggah File Untuk Di Visualisasikan", type=['xlsx', 'csv'])

    if uploaded_file:
        area_upload.empty()
        try:
            df_raw = pd.read_excel(uploaded_file, header=None, skiprows=3)
            df_raw.dropna(axis=1, how='all', inplace=True) 
            
            num_cols = len(df_raw.columns)
            if num_cols >= 16:
                df = df_raw.iloc[:, :16].copy()
                df.columns = ['Waktu', 'Kategori', 'LK', 'Total Aset', 'Kas Setara Kas', 'COGS Ratio', 'EBITDA', 'Net Profit Margin', 'ROI', 'Laba/Rugi', 'Rev1', 'Rev2', 'Rev3', 'Total Pendapatan', 'Total Liabilitas', 'Total Ekuitas']
            else:
                df = df_raw.iloc[:, :15].copy()
                df.columns = ['Waktu', 'Kategori', 'LK', 'Total Aset', 'Kas Setara Kas', 'COGS Ratio', 'EBITDA', 'Net Profit Margin', 'ROI', 'Laba/Rugi', 'Rev1', 'Rev2', 'Total Pendapatan', 'Total Liabilitas', 'Total Ekuitas']
            
            df['Waktu'] = df['Waktu'].astype(str).str.replace('\n', ' ')
            for col in df.columns[3:]: df[col] = df[col].apply(clean_num)
            df['SortKey'] = df['Waktu'].apply(parse_time)
            df = df.sort_values('SortKey').drop(columns=['SortKey'])
            
            # --- TOMBOL GENERATE LINK ---
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚀 GENERATE LINK SHARE (BAGIKAN VISUALISASI INI)", type="primary", use_container_width=True):
                with st.spinner("Mengunggah data ke server baru..."):
                    json_data = df.to_json(orient='records')
                    headers = {'Content-Type': 'application/json'}
                    
                    # Upload ke server npoint.io
                    resp = requests.post("https://api.npoint.io", data=json_data, headers=headers)
                    
                    if resp.status_code == 200:
                        # Ambil ID dari balasan server
                        paste_id = resp.json().get('id')
                        
                        base_url = "https://dashboard-tj.streamlit.app"
                        share_url = f"{base_url}/?id={paste_id}"
                        
                        st.success("✅ BERHASIL! Link ini menggunakan server baru dan 100% aman. Silakan di-copy:")
                        st.code(share_url)
                    else:
                        st.error(f"Gagal membuat link. Server cloud menolak. Status: {resp.status_code}")
            
            st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)
            render_dashboard(df)

        except Exception as e:
            st.error(f"Error memproses Excel: {e}")
