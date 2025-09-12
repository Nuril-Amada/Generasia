import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import plotly.express as px

st.set_page_config(page_title="Dashboard Angka Partisipasi Sekolah", layout="wide")

# --- HEADER ---
st.markdown(
    """
    <div style="background-color:#ADD8E6; padding:0px; border-radius:10px; text-align:center;">
        <h1 style="color:black; margin:0; font-size:28px;">Dashboard Angka Partisipasi Sekolah</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# --- SESSION STATE ---
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "tahun" not in st.session_state:
    st.session_state.tahun = "Semua Tahun"
if "provinsi" not in st.session_state:
    st.session_state.provinsi = "Semua Provinsi"

# --- LAYOUT UTAMA ---
col_nav, col_content = st.columns([1, 5])

# --- NAVIGASI ---
with col_nav:
    if st.button("Home"):
        st.session_state.page = "Home"
    if st.button("SD"):
        st.session_state.page = "SD"
    if st.button("SMP"):
        st.session_state.page = "SMP"
    if st.button("SMA/SMK"):
        st.session_state.page = "SMA/SMK"
    if st.button("Perguruan Tinggi"):
        st.session_state.page = "Perguruan Tinggi"

# --- LOAD DATA ---
@st.cache_data
def load_excel(path):
    sheets = pd.read_excel(path, sheet_name=None)

    for name, df in sheets.items():
        # rapikan nama kolom
        df.columns = df.columns.str.strip()

        for col in df.columns:
            if col != "Provinsi":
                df[col] = (
                    df[col]
                    .astype(str)
                    .str.replace("%", "", regex=False)
                    .str.replace(",", ".", regex=False)
                    .str.replace(" ", "", regex=False)
                )
                df[col] = pd.to_numeric(df[col], errors="coerce")
        sheets[name] = df
    return sheets

default_path = "ESC.xlsx"
try:
    all_sheets = load_excel(default_path)
except Exception:
    st.error("File 'ESC.xlsx' tidak ditemukan.")
    st.stop()

# --- KPI CARD ---
def kpi_card(col, title, value, color="#f8f9fa"):
    col.markdown(
        f"""
        <div style="background-color:{color}; padding:10px; border-radius:10px; 
                    text-align:center; box-shadow:1px 1px 3px rgba(0,0,0,0.1);">
            <div style="font-size:12px; color:gray;">{title}</div>
            <div style="font-size:16px; font-weight:bold; color:black;">{value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# --- FORMAT ANGKA ---
def fmt_num(x):
    try:
        return f"{int(x):,}".replace(",", ".")
    except:
        return "-"

def fmt_pct(x):
    try:
        return f"{x:.2f}%"
    except:
        return "-"

# --- FILTER DATA ---
def get_filtered_data():
    if st.session_state.tahun == "Semua Tahun":
        df = pd.concat(all_sheets.values(), ignore_index=True)
    else:
        df = all_sheets[st.session_state.tahun]
    if st.session_state.provinsi != "Semua Provinsi":
        df = df[df["Provinsi"] == st.session_state.provinsi]
    return df

# --- HITUNG TOTAL SISWA & TENDIK ---
def get_totals(df):
    total_siswa = 0
    total_tendik = 0

    siswa_cols = ["Siswa SD", "Siswa SMP", "Siswa SMA/SMK", "Mahasiswa Perguruan Tinggi"]
    tendik_cols = ["Tendik SD", "Tendik SMP", "Tendik SMA/SMK", "Tendik Perguruan Tinggi"]

    if any(col in df.columns for col in siswa_cols):
        total_siswa = df[siswa_cols].sum().sum()

    if any(col in df.columns for col in tendik_cols):
        total_tendik = df[tendik_cols].sum().sum()

    return total_siswa, total_tendik
import plotly.express as px

def plot_tren_aps_interaktif(col_name, title, key=None):
    trend_data = []
    for tahun, sheet in all_sheets.items():
        if col_name in sheet.columns:
            sheet[col_name] = (
                sheet[col_name]
                .astype(str)
                .str.replace("%", "", regex=False)
                .str.replace(",", ".", regex=False)
            )
            sheet[col_name] = pd.to_numeric(sheet[col_name], errors="coerce")

            aps_mean = sheet[col_name].mean(skipna=True)
            trend_data.append({"Tahun": int(tahun), "APS": aps_mean})

    if trend_data:
        trend_df = pd.DataFrame(trend_data).sort_values("Tahun")

        st.markdown(
            f"<div style='text-align: center; font-size:14px; font-weight:bold;'>{title}</div>",
            unsafe_allow_html=True
        )

        fig = px.line(
            trend_df,
            x="Tahun",
            y="APS",
            markers=True,
            title="",
            labels={"APS": "APS (%)", "Tahun": "Tahun"}
        )
        fig.update_traces(
            line=dict(color="blue", width=2),
            marker=dict(size=8, symbol="circle"),
            hovertemplate="Tahun: %{x}<br>APS: %{y:.2f}%<extra></extra>"
        )
        fig.update_layout(
            xaxis=dict(tickmode="linear", dtick=1),
            yaxis_title="APS (%)",
            xaxis_title="Tahun",
            margin=dict(l=40, r=40, t=20, b=40),
            height=350
        )

        st.plotly_chart(fig, use_container_width=True, key=key)

def plot_perbandingan_aps_ipm(df, col_aps, title, key=None):
    if "IPM" not in df.columns:
        st.warning("Data IPM tidak tersedia di dataset.")
        return

    scatter_df = df[["Provinsi", col_aps, "IPM"]].copy()

    scatter_df[col_aps] = (
        scatter_df[col_aps]
        .astype(str)
        .str.replace("%", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    scatter_df[col_aps] = pd.to_numeric(scatter_df[col_aps], errors="coerce")

    scatter_df = scatter_df.dropna(subset=[col_aps, "IPM"])

    if scatter_df.empty:
        st.warning("Tidak ada data valid untuk APS dan IPM.")
        return

    st.markdown(
        f"<div style='text-align: center; font-size:14px; font-weight:bold;'>{title}</div>",
        unsafe_allow_html=True
    )

    fig = px.scatter(
        scatter_df,
        x=col_aps,
        y="IPM",
        color="Provinsi",
        hover_name="Provinsi",
        size=col_aps,
        labels={col_aps: "APS (%)", "IPM": "Indeks Pembangunan Manusia"},
    )
    fig.update_traces(
        marker=dict(line=dict(width=1, color="DarkSlateGrey"))
    )
    fig.update_layout(
        height=400,
        margin=dict(l=40, r=40, t=40, b=40),
    )
    st.plotly_chart(fig, use_container_width=True, key=key)
def plot_tren_semua_aps():
    # Siapkan data kosong
    trend_data = []

    for tahun, sheet in all_sheets.items():
        # Filter provinsi kalau dipilih spesifik
        if st.session_state.provinsi != "Semua Provinsi":
            sheet = sheet[sheet["Provinsi"] == st.session_state.provinsi]

        for col, label in {
            "APS 7-12": "APS SD (7-12)",
            "APS 13-15": "APS SMP (13-15)",
            "APS 16-18": "APS SMA/SMK (16-18)",
            "APS 19-23": "APS PT (19-23)"
        }.items():
            if col in sheet.columns:
                sheet[col] = (
                    sheet[col]
                    .astype(str)
                    .str.replace("%", "", regex=False)
                    .str.replace(",", ".", regex=False)
                )
                sheet[col] = pd.to_numeric(sheet[col], errors="coerce")

                aps_mean = sheet[col].mean(skipna=True)
                trend_data.append({"Tahun": int(tahun), "APS": aps_mean, "Jenjang": label})

    if not trend_data:
        st.warning("Data tren APS tidak tersedia.")
        return

    trend_df = pd.DataFrame(trend_data).sort_values("Tahun")

    st.markdown(
        "<div style='text-align: center; font-size:14px; font-weight:bold;'>"
        "Tren Rata-rata APS Nasional per Jenjang (2020–2024)"
        "</div>", unsafe_allow_html=True
    )

    fig = px.line(
        trend_df,
        x="Tahun",
        y="APS",
        color="Jenjang",
        markers=True,
        labels={"APS": "APS (%)", "Tahun": "Tahun", "Jenjang": "Jenjang Pendidikan"}
    )
    fig.update_traces(
        line=dict(width=2),
        marker=dict(size=7, symbol="circle"),
        hovertemplate="Jenjang: %{fullData.name}<br>Tahun: %{x}<br>APS: %{y:.2f}%<extra></extra>"
    )
    fig.update_layout(
        xaxis=dict(tickmode="linear", dtick=1),
        yaxis_title="APS (%)",
        margin=dict(l=40, r=40, t=20, b=40),
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)
# Ubah definisi fungsi kpi_card agar mendukung warna
def kpi_card(container, title, value, bg_color="#ffffff"):
    container.markdown(
        f"""
        <div style='
            background-color:{bg_color};
            padding:8px;
            border-radius:10px;
            text-align:center;
        '>
            <h5 style='margin:0'>{title}</h5>
            <h4 style='margin:0'>{value}</h4>
        </div>
        """,
        unsafe_allow_html=True
    )

# --- KONTEN ---
with col_content:
    if st.session_state.page == "Home":
        # FILTER
        col_filter1, col_filter2 = st.columns([1, 1])
        with col_filter1:
            tahun_opsi = ["Semua Tahun"] + list(all_sheets.keys())
            st.session_state.tahun = st.selectbox(
                "Pilih Tahun",
                tahun_opsi,
                index=tahun_opsi.index(st.session_state.tahun)
                if st.session_state.tahun in tahun_opsi else 0
            )
        if st.session_state.tahun == "Semua Tahun":
            df_temp = pd.concat(all_sheets.values(), ignore_index=True)
        else:
            df_temp = all_sheets[st.session_state.tahun]
        with col_filter2:
            prov_opsi = ["Semua Provinsi"] + sorted(df_temp["Provinsi"].unique().tolist())
            st.session_state.provinsi = st.selectbox(
                "Pilih Provinsi",
                prov_opsi,
                index=prov_opsi.index(st.session_state.provinsi)
                if st.session_state.provinsi in prov_opsi else 0
            )

        df = get_filtered_data()

        # KPI Ringkas
        col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

        kpi_card(col1, "APS SD", fmt_pct(df["APS 7-12"].mean()), bg_color="#cce5ff")       # biru muda
        kpi_card(col2, "APS SMP", fmt_pct(df["APS 13-15"].mean()), bg_color="#d4edda")     # hijau muda
        kpi_card(col3, "APS SMA/SMK", fmt_pct(df["APS 16-18"].mean()), bg_color="#fff3cd") # kuning muda
        kpi_card(col4, "APS PT", fmt_pct(df["APS 19-23"].mean()), bg_color="#f8d7da")      # merah muda

        if "IPM" in df.columns:
            kpi_card(col5, "Rata-rata IPM", fmt_pct(df["IPM"].mean()), bg_color="#e2e3e5")   # abu-abu muda

        total_siswa, total_tendik = get_totals(df)
        kpi_card(col6, "Total Tendik Nasional", fmt_num(total_tendik), bg_color="#d1ecf1")  # biru langit
        kpi_card(col7, "Total Siswa Nasional", fmt_num(total_siswa), bg_color="#f5c6cb")    # merah muda soft


        # Pastikan APS rata-rata ada
        if "APS_Rata2" not in df.columns:
            df["APS_Rata2"] = df[["APS 7-12", "APS 13-15", "APS 16-18", "APS 19-23"]].mean(axis=1)

        # --- GRID ATAS: Tren (kiri) & Scatter (kanan) ---
        col_left, col_right = st.columns([1, 1])

        with col_left:
            #st.subheader("Tren Rata-rata APS Nasional per Jenjang (2020–2024)")
            plot_tren_semua_aps()

            with col_right:
                fig_scatter = px.scatter(
                    df,
                    x="APS_Rata2",
                    y="Tingkat Pengangguran",
                    color="Provinsi",
                    hover_name="Provinsi",
                    size="Tingkat Pengangguran",
                    labels={
                        "APS_Rata2": "APS Rata-rata (%)",
                        "Tingkat Pengangguran": "Jumlah Tingkat Pengangguran"
                    },
                )
                fig_scatter.update_traces(
                    marker=dict(opacity=0.7, line=dict(width=0.5, color="DarkSlateGrey"))
                )
                fig_scatter.update_layout(
                    height=400,
                    title=dict(
                        text="Hubungan APS Rata-rata dengan Tingkat Pengangguran",
                        x=0.5,               # posisi tengah horizontal
                        xanchor='center',
                        yanchor='top',
                        font=dict(size=14)    # ukuran huruf lebih kecil
                    )
                )
                st.plotly_chart(fig_scatter, use_container_width=True)


        # --- GRID BAWAH: Top 5 Tertinggi & Terendah ---
        col1, col2 = st.columns(2)

        with col1:
            top5 = df.groupby("Provinsi")["APS_Rata2"].mean().nlargest(5).reset_index()
            fig_top5 = px.bar(
                top5,
                x="APS_Rata2",
                y="Provinsi",
                orientation="h",
                text="APS_Rata2",
                labels={"APS_Rata2": "APS Rata-rata (%)", "Provinsi": "Provinsi"},
                color="APS_Rata2",
                color_continuous_scale="Blues",
            )
            fig_top5.update_traces(texttemplate="%{text:.2f}", textposition="outside")
            fig_top5.update_layout(
                yaxis=dict(categoryorder="total ascending"),
                height=400,
                title=dict(
                    text="Top 5 Provinsi dengan APS Tertinggi",
                    x=0.5,
                    xanchor='center'
                )
            )
            st.plotly_chart(fig_top5, use_container_width=True)

        with col2:
            top5_lowest = df.groupby("Provinsi")["APS_Rata2"].mean().nsmallest(5).reset_index()
            fig_lowest = px.bar(
                top5_lowest,
                x="APS_Rata2",
                y="Provinsi",
                orientation="h",
                text="APS_Rata2",
                labels={"APS_Rata2": "APS Rata-rata (%)", "Provinsi": "Provinsi"},
                color="APS_Rata2",
                color_continuous_scale="Reds",
            )
            fig_lowest.update_traces(texttemplate="%{text:.2f}", textposition="outside")
            fig_lowest.update_layout(
                yaxis=dict(categoryorder="total descending"),
                height=400,
                title=dict(
                    text="Top 5 Provinsi dengan APS Terendah",
                    x=0.5,
                    xanchor='center'
                )
            )
            st.plotly_chart(fig_lowest, use_container_width=True)

        # --- HALAMAN LAIN ---
    else:
        df = get_filtered_data()

        # --- TEKS FILTER NATURAL ---
        prov = st.session_state.provinsi
        tahun = st.session_state.tahun

        if prov != "Semua Provinsi" and tahun != "Semua Tahun":
            filter_text = f"Provinsi {prov} Tahun {tahun}"
        elif prov != "Semua Provinsi" and tahun == "Semua Tahun":
            filter_text = f"Provinsi {prov} (Semua Tahun)"
        elif prov == "Semua Provinsi" and tahun != "Semua Tahun":
            filter_text = f"Semua Provinsi Tahun {tahun}"
        else:
            filter_text = "Semua Provinsi dan Semua Tahun"

        st.markdown(
            f"<div style='text-align:center; color:black; font-size:16px; font-weight:bold;'>"
            f"{filter_text}"
            f"</div>", unsafe_allow_html=True
        )

        # --- SD ---
        if st.session_state.page == "SD":
            total_sd = df["Jumlah SD"].sum()
            total_siswa = df["Siswa SD"].sum()
            total_tendik = df["Tendik SD"].sum()
            aps_sd = df["APS 7-12"].mean()

            c1, c2, c3, c4 = st.columns(4)
            kpi_card(c1, "Total SD", fmt_num(total_sd), "#cce5ff")
            kpi_card(c2, "Total Siswa SD", fmt_num(total_siswa), "#d4edda")
            kpi_card(c3, "Total Tendik SD", fmt_num(total_tendik), "#f8d7da")
            kpi_card(c4, "APS SD", fmt_pct(aps_sd), "#fff3cd")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(
                "<div style='text-align: center; font-size:16px; font-weight:bold;'>Jumlah SD per Provinsi</div>",
                unsafe_allow_html=True)
                st.bar_chart(df.groupby("Provinsi")["Jumlah SD"].sum())
            with col2:
                st.markdown(
                "<div style='text-align: center; font-size:16px; font-weight:bold;'>Jumlah Siswa SD per Provinsi</div>",
                unsafe_allow_html=True)
                st.bar_chart(df.groupby("Provinsi")["Siswa SD"].sum())
            with col3:
                st.markdown(
                "<div style='text-align: center; font-size:16px; font-weight:bold;'>Jumlah Tendik SD per Provinsi</div>",
                unsafe_allow_html=True)
                st.bar_chart(df.groupby("Provinsi")["Tendik SD"].sum())

            # Bagian tren & perbandingan 
            col_tren, col_perbandingan = st.columns(2)
            with col_tren:
                plot_tren_aps_interaktif("APS 7-12", "Tren Rata-rata APS SD Nasional (2020–2024)", key="tren_sd")
            with col_perbandingan:
                plot_perbandingan_aps_ipm(df, "APS 7-12", "Perbandingan APS SD dan IPM per Provinsi", key="ipm_sd")


        # --- SMP ---
        elif st.session_state.page == "SMP":
            total_smp = df["Jumlah SMP"].sum()
            total_siswa = df["Siswa SMP"].sum()
            total_tendik = df["Tendik SMP"].sum()
            aps_smp = df["APS 13-15"].mean()

            c1, c2, c3, c4 = st.columns(4)
            kpi_card(c1, "Total SMP", fmt_num(total_smp), "#cce5ff")
            kpi_card(c2, "Total Siswa SMP", fmt_num(total_siswa), "#d4edda")
            kpi_card(c3, "Total Tendik SMP", fmt_num(total_tendik), "#f8d7da")
            kpi_card(c4, "APS SMP", fmt_pct(aps_smp), "#fff3cd")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(
                "<div style='text-align: center; font-size:16px; font-weight:bold;'>Jumlah SMP per Provinsi</div>",
                unsafe_allow_html=True)
                st.bar_chart(df.groupby("Provinsi")["Jumlah SMP"].sum())
            with col2:
                st.markdown(
                "<div style='text-align: center; font-size:16px; font-weight:bold;'>Jumlah Siswa SMP per Provinsi</div>",
                unsafe_allow_html=True)
                st.bar_chart(df.groupby("Provinsi")["Siswa SMP"].sum())
            with col3:
                st.markdown(
                "<div style='text-align: center; font-size:16px; font-weight:bold;'>Jumlah Tendik SMP per Provinsi</div>",
                unsafe_allow_html=True)
                st.bar_chart(df.groupby("Provinsi")["Tendik SMP"].sum())

            # Bagian tren & perbandingan 
            col_tren, col_perbandingan = st.columns(2)
            with col_tren:
                plot_tren_aps_interaktif("APS 13-15", "Tren Rata-rata APS SMP Nasional (2020–2024)", key="tren_smp")
            with col_perbandingan:
                plot_perbandingan_aps_ipm(df, "APS 13-15", "Perbandingan APS SMP dan IPM per Provinsi", key="ipm_smp")           


        # --- SMA/SMK ---
        elif st.session_state.page == "SMA/SMK":
            total_sma = df["Jumlah SMA/SMK"].sum()
            total_siswa = df["Siswa SMA/SMK"].sum()
            total_tendik = df["Tendik SMA/SMK"].sum()
            aps_sma = df["APS 16-18"].mean()

            c1, c2, c3, c4 = st.columns(4)
            kpi_card(c1, "Total SMA/SMK", fmt_num(total_sma), "#cce5ff")
            kpi_card(c2, "Total Siswa SMA/SMK", fmt_num(total_siswa), "#d4edda")
            kpi_card(c3, "Total Tendik SMA/SMK", fmt_num(total_tendik), "#f8d7da")
            kpi_card(c4, "APS SMA/SMK", fmt_pct(aps_sma), "#fff3cd")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(
                "<div style='text-align: center; font-size:16px; font-weight:bold;'>Jumlah SMA/SMK per Provinsi</div>",
                unsafe_allow_html=True)
                st.bar_chart(df.groupby("Provinsi")["Jumlah SMA/SMK"].sum())
            with col2:
                st.markdown(
                "<div style='text-align: center; font-size:16px; font-weight:bold;'>Jumlah Siswa SMA/SMK per Provinsi</div>",
                unsafe_allow_html=True)
                st.bar_chart(df.groupby("Provinsi")["Siswa SMA/SMK"].sum())
            with col3:
                st.markdown(
                "<div style='text-align: center; font-size:16px; font-weight:bold;'>Jumlah Tendik SMA/SMK per Provinsi</div>",
                unsafe_allow_html=True)
                st.bar_chart(df.groupby("Provinsi")["Tendik SMA/SMK"].sum())

            # Bagian tren & perbandingan 
            col_tren, col_perbandingan = st.columns(2)
            with col_tren:
                 plot_tren_aps_interaktif("APS 16-18", "Tren Rata-rata APS SMA Nasional (2020–2024)", key="tren_sma")
            with col_perbandingan:
                plot_perbandingan_aps_ipm(df, "APS 16-18", "Perbandingan APS SMA dan IPM per Provinsi", key="ipm_sma")
            

        # --- PERGURUAN TINGGI ---
        elif st.session_state.page == "Perguruan Tinggi":
            total_pt = df["Jumlah Perguruan Tinggi"].sum()
            total_mhs = df["Mahasiswa Perguruan Tinggi"].sum()
            total_tendik = df["Tendik Perguruan Tinggi"].sum()
            aps_pt = df["APS 19-23"].mean()

            c1, c2, c3, c4 = st.columns(4)
            kpi_card(c1, "Total Perguruan Tinggi", fmt_num(total_pt), "#cce5ff")
            kpi_card(c2, "Total Mahasiswa Perguruan Tinggi", fmt_num(total_mhs), "#d4edda")
            kpi_card(c3, "Total Tendik Perguruan Tinggi", fmt_num(total_tendik), "#f8d7da")
            kpi_card(c4, "APS Perguruan Tinggi", fmt_pct(aps_pt), "#fff3cd")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(
                "<div style='text-align: center; font-size:16px; font-weight:bold;'>Jumlah Perguruan Tinggi per Provinsi</div>",
                unsafe_allow_html=True)
                st.bar_chart(df.groupby("Provinsi")["Jumlah Perguruan Tinggi"].sum())
            with col2:
                st.markdown(
                "<div style='text-align: center; font-size:16px; font-weight:bold;'>Jumlah Mahasiswa Perguruan Tinggi per Provinsi</div>",
                unsafe_allow_html=True)
                st.bar_chart(df.groupby("Provinsi")["Mahasiswa Perguruan Tinggi"].sum())
            with col3:
                st.markdown(
                "<div style='text-align: center; font-size:16px; font-weight:bold;'>Jumlah Tendik Perguruan Tinggi per Provinsi</div>",
                unsafe_allow_html=True)
                st.bar_chart(df.groupby("Provinsi")["Tendik Perguruan Tinggi"].sum())

             # Bagian tren & perbandingan 
            col_tren, col_perbandingan = st.columns(2)
            with col_tren:
                plot_tren_aps_interaktif("APS 19-23", "Tren Rata-rata APS PT Nasional (2020–2024)", key="tren_pt")
            with col_perbandingan:
                plot_perbandingan_aps_ipm(df, "APS 19-23", "Perbandingan APS PT dan IPM per Provinsi", key="ipm_pt")



        
