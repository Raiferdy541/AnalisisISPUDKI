# ============================================================
# STREAMLIT BUSINESS INTELLIGENCE DASHBOARD
# Analisis Kualitas Udara Jakarta Berbasis Data ISPU
# ============================================================
# Dashboard ini dibuat untuk memenuhi Tugas 6 Studi Kasus Data Analyst:
# 1. Overview Kualitas Udara Jakarta
# 2. Tren Temporal Kualitas Udara
# 3. Perbandingan Kualitas Udara Antar Stasiun
# 4. Analisis Parameter Pencemar Kritis
# 5. Pola Musiman Kualitas Udara
# 6. Risiko Hari Tidak Sehat
# 7. Matriks Prioritas Intervensi Stasiun
# 8. Anomali dan Episode Polusi Ekstrem
# ============================================================

# ============================================================
# AUTO-INSTALL DEPENDENCIES UNTUK STREAMLIT CLOUD / LOCAL RUN
# ============================================================
# Catatan:
# Streamlit Cloud biasanya membaca dependencies dari requirements.txt.
# Blok ini ditambahkan sebagai fallback agar modul penting seperti plotly
# otomatis dicoba di-install jika belum tersedia di environment.
import sys
import subprocess
import importlib.util

REQUIRED_PACKAGES = {
    "numpy": "numpy",
    "pandas": "pandas",
    "plotly": "plotly",
    "streamlit": "streamlit",
}

def ensure_package(import_name: str, pip_name: str) -> None:
    """Cek modul. Jika belum ada, install menggunakan pip."""
    if importlib.util.find_spec(import_name) is None:
        subprocess.check_call([
            sys.executable,
            "-m",
            "pip",
            "install",
            pip_name,
        ])

for _import_name, _pip_name in REQUIRED_PACKAGES.items():
    ensure_package(_import_name, _pip_name)

import os
import re
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ------------------------------------------------------------
# KONFIGURASI HALAMAN
# ------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard ISPU Jakarta",
    page_icon="🌫️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------
# KONSTANTA ANALISIS
# ------------------------------------------------------------
DEFAULT_DATA_PATH = "ispu_jakarta_validated_clean.csv"
RAW_DATA_PATH = "ispu_jakarta_clean.csv"
POLLUTANT_COLS = ["pm10", "pm25", "so2", "co", "o3", "no2"]
CATEGORY_ORDER = ["BAIK", "SEDANG", "TIDAK SEHAT", "SANGAT TIDAK SEHAT", "BERBAHAYA"]
UNHEALTHY_CATEGORIES = ["TIDAK SEHAT", "SANGAT TIDAK SEHAT", "BERBAHAYA"]
CRITICAL_ORDER = ["PM10", "PM2.5", "SO2", "CO", "O3", "NO2"]

CATEGORY_COLORS = {
    "BAIK": "#2ECC71",
    "SEDANG": "#F1C40F",
    "TIDAK SEHAT": "#E67E22",
    "SANGAT TIDAK SEHAT": "#E74C3C",
    "BERBAHAYA": "#8E44AD",
}

PRIORITY_COLORS = {
    "Prioritas Tinggi": "#E74C3C",
    "Prioritas Sedang": "#F1C40F",
    "Prioritas Rendah": "#2ECC71",
}

STATION_COORDS = {
    "DKI1 Bunderan HI": {"lat": -6.1948, "lon": 106.8230},
    "DKI2 Kelapa Gading": {"lat": -6.1610, "lon": 106.9042},
    "DKI3 Jagakarsa": {"lat": -6.3343, "lon": 106.8230},
    "DKI4 Lubang Buaya": {"lat": -6.2898, "lon": 106.9098},
    "DKI5 Kebon Jeruk": {"lat": -6.1917, "lon": 106.7694},
}

MONTH_MAP = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "Mei", 6: "Jun",
    7: "Jul", 8: "Agu", 9: "Sep", 10: "Okt", 11: "Nov", 12: "Des",
}
MONTH_ORDER = list(MONTH_MAP.values())

# ------------------------------------------------------------
# STYLE HALAMAN
# ------------------------------------------------------------
st.markdown(
    """
    <style>
    .main .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #F8FAFC 0%, #EEF2F7 100%);
        border: 1px solid #E2E8F0;
        border-radius: 18px;
        padding: 18px 18px;
        min-height: 120px;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
    }
    .metric-label {
        color: #64748B;
        font-size: 0.88rem;
        font-weight: 600;
        margin-bottom: 6px;
    }
    .metric-value {
        color: #0F172A;
        font-size: 1.75rem;
        font-weight: 800;
        line-height: 1.2;
    }
    .metric-caption {
        color: #475569;
        font-size: 0.78rem;
        margin-top: 8px;
    }
    .insight-box {
        background: #F0F9FF;
        border-left: 6px solid #0284C7;
        border-radius: 12px;
        padding: 14px 16px;
        margin: 12px 0 20px 0;
        color: #0F172A;
        font-size: 0.92rem;
    }
    .action-box {
        background: #F8F5FF;
        border-left: 6px solid #7C3AED;
        border-radius: 12px;
        padding: 14px 16px;
        margin: 12px 0 20px 0;
        color: #0F172A;
        font-size: 0.92rem;
    }
    .chart-note {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-left: 5px solid #0EA5E9;
        border-radius: 12px;
        padding: 12px 14px;
        margin: 8px 0 22px 0;
        color: #0F172A;
        font-size: 0.90rem;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
    }
    .small-note {
        color: #64748B;
        font-size: 0.85rem;
    }
    .footer-box {
        text-align: center;
        color: #64748B;
        font-size: 0.88rem;
        padding: 18px 0 4px 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------
# FUNGSI UTILITAS
# ------------------------------------------------------------
def extract_station_code(station: str) -> str:
    """Mengambil kode stasiun DKI1-DKI5 dari nama stasiun."""
    match = re.search(r"DKI\d", str(station))
    return match.group(0) if match else str(station)


def is_unhealthy(category: str) -> bool:
    """Menentukan apakah kategori udara termasuk Tidak Sehat atau lebih buruk."""
    return str(category).upper().strip() in UNHEALTHY_CATEGORIES


def classify_ispu(value: float) -> str:
    """Mengklasifikasikan kategori ISPU berdasarkan nilai max."""
    if pd.isna(value):
        return np.nan
    if value <= 50:
        return "BAIK"
    if value <= 100:
        return "SEDANG"
    if value <= 199:
        return "TIDAK SEHAT"
    if value <= 299:
        return "SANGAT TIDAK SEHAT"
    return "BERBAHAYA"


def format_pct(value: float) -> str:
    """Format persentase untuk tampilan KPI."""
    if pd.isna(value):
        return "-"
    return f"{value:.1f}%"


def format_number(value: float, decimals: int = 1) -> str:
    """Format angka untuk tampilan KPI."""
    if pd.isna(value):
        return "-"
    return f"{value:,.{decimals}f}".replace(",", ".")


def metric_card(label: str, value: str, caption: str = ""):
    """Menampilkan KPI card dengan HTML sederhana."""
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-caption">{caption}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def insight_box(title: str, text: str):
    """Menampilkan kotak insight analisis dashboard."""
    st.markdown(
        f"""
        <div class="insight-box">
            <b>{title}</b><br>{text}
        </div>
        """,
        unsafe_allow_html=True,
    )


def action_box(title: str, text: str):
    """Menampilkan kotak rekomendasi tindak lanjut dashboard."""
    st.markdown(
        f"""
        <div class="action-box">
            <b>{title}</b><br>{text}
        </div>
        """,
        unsafe_allow_html=True,
    )


def chart_insight(title: str, text: str):
    """Menampilkan penjelasan/insight tepat di bawah chart atau visualisasi."""
    st.markdown(
        f"""
        <div class="chart-note">
            <b>{title}</b><br>{text}
        </div>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def load_default_data() -> pd.DataFrame:
    """Memuat dataset default dari folder aplikasi."""
    if os.path.exists(DEFAULT_DATA_PATH):
        return pd.read_csv(DEFAULT_DATA_PATH)
    if os.path.exists(RAW_DATA_PATH):
        return pd.read_csv(RAW_DATA_PATH)
    raise FileNotFoundError(
        "Dataset default tidak ditemukan. Letakkan ispu_jakarta_validated_clean.csv atau ispu_jakarta_clean.csv di folder aplikasi."
    )


def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    """Menyiapkan dataset untuk dashboard tanpa mengubah prinsip analisis utama."""
    data = df.copy()
    data.columns = [c.strip().lower() for c in data.columns]

    required_cols = ["tanggal", "periode_data", "stasiun", "max", "critical", "categori"]
    missing_required = [c for c in required_cols if c not in data.columns]
    if missing_required:
        st.error(f"Kolom wajib tidak ditemukan: {missing_required}")
        st.stop()

    data["tanggal"] = pd.to_datetime(data["tanggal"], errors="coerce")
    data = data.dropna(subset=["tanggal", "stasiun"]).copy()

    for col in POLLUTANT_COLS + ["max"]:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce")

    data["stasiun"] = data["stasiun"].astype(str).str.strip()
    data["station_code"] = data["stasiun"].apply(extract_station_code)
    data["critical"] = data["critical"].astype(str).str.upper().str.strip()
    data["critical"] = data["critical"].replace({"PM25": "PM2.5", "PM 2.5": "PM2.5", "NAN": np.nan, "NONE": np.nan})
    data["categori"] = data["categori"].astype(str).str.upper().str.strip()
    data["categori"] = data["categori"].replace({"NAN": np.nan, "NONE": np.nan, "LUARBIASA": "BERBAHAYA"})

    # Jika kategori kosong, isi berdasarkan nilai max agar dashboard tetap dapat berjalan.
    missing_category = data["categori"].isna() | (data["categori"] == "")
    data.loc[missing_category, "categori"] = data.loc[missing_category, "max"].apply(classify_ispu)

    data["tahun"] = data["tanggal"].dt.year
    data["bulan"] = data["tanggal"].dt.month
    data["nama_bulan"] = data["bulan"].map(MONTH_MAP)
    data["periode_bulanan"] = data["tanggal"].dt.to_period("M").dt.to_timestamp()
    data["periode_tahunan"] = data["tanggal"].dt.to_period("Y").dt.to_timestamp()
    data["is_unhealthy"] = data["categori"].apply(is_unhealthy)

    coords = pd.DataFrame.from_dict(STATION_COORDS, orient="index").reset_index().rename(columns={"index": "stasiun"})
    data = data.merge(coords, on="stasiun", how="left")
    return data


def apply_filters(data: pd.DataFrame) -> pd.DataFrame:
    """Menerapkan filter sidebar ke dataset."""
    st.sidebar.header("Filter Dashboard")

    min_date = data["tanggal"].min().date()
    max_date = data["tanggal"].max().date()
    selected_date_range = st.sidebar.date_input(
        "Periode tanggal",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    if isinstance(selected_date_range, tuple) and len(selected_date_range) == 2:
        start_date, end_date = selected_date_range
    else:
        start_date, end_date = min_date, max_date

    station_options = sorted(data["stasiun"].dropna().unique().tolist())
    selected_stations = st.sidebar.multiselect(
        "Stasiun SPKU",
        station_options,
        default=station_options,
    )

    category_options = [c for c in CATEGORY_ORDER if c in data["categori"].dropna().unique().tolist()]
    extra_categories = sorted(set(data["categori"].dropna()) - set(category_options))
    category_options = category_options + extra_categories
    selected_categories = st.sidebar.multiselect(
        "Kategori ISPU",
        category_options,
        default=category_options,
    )

    critical_options = [c for c in CRITICAL_ORDER if c in data["critical"].dropna().unique().tolist()]
    extra_critical = sorted(set(data["critical"].dropna()) - set(critical_options))
    critical_options = critical_options + extra_critical
    selected_critical = st.sidebar.multiselect(
        "Pencemar kritis",
        critical_options,
        default=critical_options,
    )

    filtered = data[
        (data["tanggal"].dt.date >= start_date)
        & (data["tanggal"].dt.date <= end_date)
        & (data["stasiun"].isin(selected_stations))
        & (data["categori"].isin(selected_categories))
        & (data["critical"].isin(selected_critical))
    ].copy()

    st.sidebar.markdown("---")
    st.sidebar.caption(
        "Gunakan filter ini saat presentasi untuk menunjukkan perbedaan kualitas udara berdasarkan periode, stasiun, kategori, dan pencemar kritis."
    )
    return filtered


def get_dominant(series: pd.Series) -> str:
    """Mengambil nilai terbanyak dari sebuah kolom kategorik."""
    counts = series.dropna().value_counts()
    return counts.index[0] if not counts.empty else "-"


def unhealthy_pct(data: pd.DataFrame) -> float:
    """Menghitung persentase hari Tidak Sehat atau lebih buruk."""
    if data.empty:
        return np.nan
    return data["is_unhealthy"].mean() * 100


def make_empty_warning():
    """Peringatan ketika data hasil filter kosong."""
    st.warning("Tidak ada data pada kombinasi filter yang dipilih. Silakan longgarkan filter periode, stasiun, kategori, atau pencemar kritis.")


def compute_trend_slope(df: pd.DataFrame, group_cols: List[str]) -> pd.DataFrame:
    """Menghitung slope sederhana per grup berdasarkan rata-rata ISPU bulanan."""
    rows = []
    for key, g in df.groupby(group_cols):
        monthly = g.groupby("periode_bulanan", as_index=False).agg(rata_rata_ispu=("max", "mean")).sort_values("periode_bulanan")
        if len(monthly) >= 2:
            x = np.arange(len(monthly))
            y = monthly["rata_rata_ispu"].values
            slope = float(np.polyfit(x, y, 1)[0])
        else:
            slope = 0.0
        if not isinstance(key, tuple):
            key = (key,)
        rows.append({**dict(zip(group_cols, key)), "trend_slope": slope})
    return pd.DataFrame(rows)


def normalize_series(series: pd.Series) -> pd.Series:
    """Normalisasi min-max dengan fallback jika nilai konstan."""
    if series.max() == series.min():
        return pd.Series(np.ones(len(series)) * 50, index=series.index)
    return (series - series.min()) / (series.max() - series.min()) * 100


def priority_label(score: float) -> str:
    """Mengubah skor prioritas menjadi kategori prioritas intervensi."""
    if score >= 66:
        return "Prioritas Tinggi"
    if score >= 33:
        return "Prioritas Sedang"
    return "Prioritas Rendah"

# ------------------------------------------------------------
# MEMUAT DATA
# ------------------------------------------------------------
st.sidebar.title("🌫️ ISPU Jakarta")
st.sidebar.write("Dashboard BI interaktif untuk analisis kualitas udara DKI Jakarta.")

uploaded_file = st.sidebar.file_uploader(
    "Opsional: unggah dataset CSV",
    type=["csv"],
    help="Gunakan file ispu_jakarta_validated_clean.csv atau ispu_jakarta_clean.csv.",
)

if uploaded_file is not None:
    raw_df = pd.read_csv(uploaded_file)
    source_label = "CSV yang diunggah"
else:
    raw_df = load_default_data()
    source_label = DEFAULT_DATA_PATH if os.path.exists(DEFAULT_DATA_PATH) else RAW_DATA_PATH

DATA = prepare_data(raw_df)
FILTERED = apply_filters(DATA)

# ------------------------------------------------------------
# HEADER DASHBOARD
# ------------------------------------------------------------
st.title("Dashboard Business Intelligence Kualitas Udara Jakarta")
st.markdown(
    "Dashboard ini menyajikan analisis interaktif data **Indeks Standar Pencemaran Udara (ISPU) DKI Jakarta** berdasarkan nilai ISPU tertinggi harian (`max`), kategori kualitas udara (`categori`), dan parameter pencemar kritis (`critical`)."
)

st.caption(
    f"Sumber data aktif: {source_label} | Jumlah data awal: {len(DATA):,} baris | Jumlah data setelah filter: {len(FILTERED):,} baris".replace(",", ".")
)

if FILTERED.empty:
    make_empty_warning()
    st.stop()

st.download_button(
    label="⬇️ Unduh data hasil filter",
    data=FILTERED.to_csv(index=False).encode("utf-8"),
    file_name="ispu_jakarta_filtered_dashboard.csv",
    mime="text/csv",
)

# ------------------------------------------------------------
# TAB DASHBOARD
# ------------------------------------------------------------
tabs = st.tabs(
    [
        "1. Overview",
        "2. Tren Temporal",
        "3. Antar Stasiun",
        "4. Pencemar Kritis",
        "5. Pola Musiman",
        "6. Risiko Tidak Sehat",
        "7. Prioritas Intervensi",
        "8. Anomali Ekstrem",
    ]
)

# ============================================================
# DASHBOARD 1 — OVERVIEW KUALITAS UDARA JAKARTA
# ============================================================
with tabs[0]:
    st.header("Dashboard 1 — Overview Kualitas Udara Jakarta")
    st.write("Menampilkan kondisi kualitas udara Jakarta secara keseluruhan melalui KPI utama, distribusi kategori, dan ringkasan kondisi terkini per stasiun.")

    avg_ispu = FILTERED["max"].mean()
    pct_unhealthy = unhealthy_pct(FILTERED)
    dominant_pollutant = get_dominant(FILTERED["critical"])
    latest_date = FILTERED["tanggal"].max().date()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Rata-rata ISPU", format_number(avg_ispu), "Rata-rata nilai max pada data terfilter")
    with c2:
        metric_card("Hari Tidak Sehat+", format_pct(pct_unhealthy), "Proporsi kategori Tidak Sehat atau lebih buruk")
    with c3:
        metric_card("Pencemar Dominan", dominant_pollutant, "Paling sering menjadi critical pollutant")
    with c4:
        metric_card("Tanggal Data Terkini", str(latest_date), "Tanggal maksimum pada filter aktif")

    insight_box(
        "Analisis utama",
        f"Pada filter aktif, rata-rata ISPU Jakarta berada pada nilai {format_number(avg_ispu)} dengan {format_pct(pct_unhealthy)} observasi masuk kategori Tidak Sehat atau lebih buruk. Parameter {dominant_pollutant} paling sering menjadi pencemar kritis, sehingga perlu menjadi perhatian utama dalam membaca kondisi umum kualitas udara.",
    )
    action_box(
        "Insight tindak lanjut untuk DLH DKI Jakarta",
        "KPI overview dapat digunakan sebagai indikator cepat untuk menentukan apakah kondisi kualitas udara perlu ditindaklanjuti melalui pemantauan intensif, komunikasi risiko, atau koordinasi program pengendalian pencemaran pada periode dan stasiun yang dipilih.",
    )

    col_left, col_right = st.columns([1.1, 1])

    with col_left:
        category_counts = FILTERED["categori"].value_counts().reindex(CATEGORY_ORDER).dropna().reset_index()
        category_counts.columns = ["categori", "jumlah"]
        fig_cat = px.pie(
            category_counts,
            values="jumlah",
            names="categori",
            hole=0.45,
            color="categori",
            color_discrete_map=CATEGORY_COLORS,
            title="Komposisi Kategori Kualitas Udara",
        )
        fig_cat.update_traces(textposition="inside", textinfo="percent+label")
        fig_cat.update_layout(height=430, margin=dict(l=10, r=10, t=60, b=10))
        st.plotly_chart(fig_cat, use_container_width=True)
        dominant_category = category_counts.sort_values("jumlah", ascending=False).iloc[0]
        chart_insight(
            "Insight visualisasi kategori",
            f"Grafik ini menunjukkan komposisi status kualitas udara pada filter aktif. Kategori yang paling dominan adalah {dominant_category['categori']} dengan {int(dominant_category['jumlah'])} observasi. Jika porsi kategori Tidak Sehat ke atas besar, maka periode/stasiun terfilter perlu menjadi prioritas komunikasi risiko dan pengendalian pencemaran.",
        )

    with col_right:
        latest_rows = (
            FILTERED.sort_values("tanggal")
            .groupby("stasiun", as_index=False)
            .tail(1)
            .sort_values("stasiun")
        )
        display_cols = ["tanggal", "stasiun", "max", "critical", "categori"]
        st.subheader("Ringkasan Kondisi Terkini per Stasiun")
        st.dataframe(
            latest_rows[display_cols].assign(tanggal=lambda x: x["tanggal"].dt.strftime("%Y-%m-%d")),
            use_container_width=True,
            hide_index=True,
        )
        latest_worst = latest_rows.sort_values("max", ascending=False).iloc[0]
        chart_insight(
            "Insight tabel kondisi terkini",
            f"Tabel ini memperlihatkan kondisi terbaru tiap stasiun setelah filter diterapkan. Pada tanggal data terkini, nilai ISPU tertinggi terdapat di {latest_worst['stasiun']} dengan nilai {format_number(latest_worst['max'])} dan pencemar kritis {latest_worst['critical']}. Informasi ini dapat dipakai sebagai bahan monitoring operasional harian.",
        )

    current_map = latest_rows.dropna(subset=["lat", "lon"]).copy()
    if not current_map.empty:
        fig_map = px.scatter_mapbox(
            current_map,
            lat="lat",
            lon="lon",
            color="categori",
            size="max",
            hover_name="stasiun",
            hover_data={"tanggal": True, "max": ":.1f", "critical": True, "lat": False, "lon": False},
            color_discrete_map=CATEGORY_COLORS,
            zoom=9.7,
            height=440,
            title="Peta Ringkas Kondisi Terkini SPKU",
        )
        fig_map.update_layout(mapbox_style="open-street-map", margin=dict(l=0, r=0, t=60, b=0))
        st.plotly_chart(fig_map, use_container_width=True)
        chart_insight(
            "Insight peta SPKU",
            "Peta ini membantu melihat sebaran kondisi terkini antar titik pemantauan. Ukuran titik menggambarkan nilai ISPU, sedangkan warna menunjukkan kategori kualitas udara. Titik dengan ukuran besar dan warna kategori risiko tinggi dapat menjadi lokasi awal untuk pengecekan lapangan atau koordinasi pengendalian sumber pencemar.",
        )
    else:
        st.info("Koordinat stasiun tidak tersedia untuk menampilkan peta. Ringkasan kondisi terkini tetap tersedia pada tabel.")

# ============================================================
# DASHBOARD 2 — TREN TEMPORAL KUALITAS UDARA
# ============================================================
with tabs[1]:
    st.header("Dashboard 2 — Tren Temporal Kualitas Udara")
    st.write("Menampilkan tren nilai ISPU dari waktu ke waktu dengan granularitas harian, bulanan, atau tahunan.")

    granularity = st.radio(
        "Pilih granularitas tren",
        ["Harian", "Bulanan", "Tahunan"],
        horizontal=True,
    )

    if granularity == "Harian":
        group_col = "tanggal"
        date_label = "Tanggal"
    elif granularity == "Bulanan":
        group_col = "periode_bulanan"
        date_label = "Bulan"
    else:
        group_col = "periode_tahunan"
        date_label = "Tahun"

    trend = (
        FILTERED.groupby([group_col, "stasiun"], as_index=False)
        .agg(rata_rata_ispu=("max", "mean"), jumlah_observasi=("max", "count"), pct_tidak_sehat=("is_unhealthy", lambda x: x.mean() * 100))
        .sort_values(group_col)
    )

    fig_trend = px.line(
        trend,
        x=group_col,
        y="rata_rata_ispu",
        color="stasiun",
        markers=(granularity != "Harian"),
        title=f"Tren Rata-rata ISPU ({granularity}) per Stasiun",
        labels={group_col: date_label, "rata_rata_ispu": "Rata-rata ISPU", "stasiun": "Stasiun"},
    )
    fig_trend.update_layout(height=520, hovermode="x unified", margin=dict(l=10, r=10, t=60, b=10))
    st.plotly_chart(fig_trend, use_container_width=True)
    peak_trend = trend.sort_values("rata_rata_ispu", ascending=False).iloc[0]
    chart_insight(
        "Insight tren temporal",
        f"Grafik tren memperlihatkan perubahan rata-rata ISPU berdasarkan granularitas {granularity.lower()}. Titik tertinggi pada filter aktif terjadi pada {pd.to_datetime(peak_trend[group_col]).strftime('%Y-%m-%d')} di {peak_trend['stasiun']} dengan rata-rata ISPU {format_number(peak_trend['rata_rata_ispu'])}. Periode puncak seperti ini perlu ditelusuri karena dapat menunjukkan episode pencemaran atau periode risiko tertentu.",
    )

    annual_summary = (
        FILTERED.groupby("tahun", as_index=False)
        .agg(rata_rata_ispu=("max", "mean"), pct_tidak_sehat=("is_unhealthy", lambda x: x.mean() * 100))
        .sort_values("tahun")
    )

    if not annual_summary.empty:
        best_year = annual_summary.loc[annual_summary["rata_rata_ispu"].idxmin()]
        worst_year = annual_summary.loc[annual_summary["rata_rata_ispu"].idxmax()]
        first_year = annual_summary.iloc[0]
        last_year = annual_summary.iloc[-1]
        trend_direction = "memburuk" if last_year["rata_rata_ispu"] > first_year["rata_rata_ispu"] else "membaik"
        change_value = last_year["rata_rata_ispu"] - first_year["rata_rata_ispu"]

        k1, k2, k3 = st.columns(3)
        with k1:
            metric_card("Tahun Terbaik", str(int(best_year["tahun"])), f"Rata-rata ISPU {format_number(best_year['rata_rata_ispu'])}")
        with k2:
            metric_card("Tahun Terburuk", str(int(worst_year["tahun"])), f"Rata-rata ISPU {format_number(worst_year['rata_rata_ispu'])}")
        with k3:
            metric_card("Arah Perubahan", trend_direction.title(), f"Perubahan awal-akhir: {format_number(change_value)} poin")

        insight_box(
            "Analisis utama",
            f"Berdasarkan rata-rata tahunan pada filter aktif, tahun dengan kualitas udara relatif terbaik adalah {int(best_year['tahun'])}, sedangkan tahun dengan rata-rata ISPU tertinggi adalah {int(worst_year['tahun'])}. Dibandingkan periode awal dan akhir data terfilter, tren rata-rata ISPU terindikasi {trend_direction} sebesar {format_number(abs(change_value))} poin.",
        )
        action_box(
            "Insight tindak lanjut untuk DLH DKI Jakarta",
            "Tren temporal membantu DLH mengidentifikasi periode yang perlu dievaluasi lebih lanjut. Periode dengan kenaikan ISPU signifikan dapat menjadi dasar penelusuran faktor lapangan, penguatan pemantauan, dan evaluasi efektivitas program pengendalian pencemaran udara.",
        )

        fig_annual = px.bar(
            annual_summary,
            x="tahun",
            y="rata_rata_ispu",
            text="rata_rata_ispu",
            title="Ringkasan Rata-rata ISPU Tahunan",
            labels={"tahun": "Tahun", "rata_rata_ispu": "Rata-rata ISPU"},
        )
        fig_annual.update_traces(texttemplate="%{text:.1f}", textposition="outside")
        fig_annual.update_layout(height=420, margin=dict(l=10, r=10, t=60, b=10))
        st.plotly_chart(fig_annual, use_container_width=True)
        chart_insight(
            "Insight ringkasan tahunan",
            f"Bar chart tahunan menegaskan perbandingan kinerja kualitas udara antar tahun. Tahun {int(worst_year['tahun'])} menjadi tahun dengan rata-rata ISPU tertinggi, sedangkan {int(best_year['tahun'])} menjadi tahun dengan rata-rata terendah. Gap antar tahun membantu mengevaluasi periode yang perlu pendalaman kebijakan dan operasional.",
        )

# ============================================================
# DASHBOARD 3 — PERBANDINGAN KUALITAS UDARA ANTAR STASIUN
# ============================================================
with tabs[2]:
    st.header("Dashboard 3 — Perbandingan Kualitas Udara Antar Stasiun")
    st.write("Membandingkan kualitas udara antar SPKU berdasarkan rata-rata ISPU, distribusi kategori, dan sebaran nilai harian.")

    station_summary = (
        FILTERED.groupby("stasiun", as_index=False)
        .agg(
            rata_rata_ispu=("max", "mean"),
            median_ispu=("max", "median"),
            nilai_maksimum=("max", "max"),
            pct_tidak_sehat=("is_unhealthy", lambda x: x.mean() * 100),
            jumlah_observasi=("max", "count"),
        )
        .sort_values("rata_rata_ispu", ascending=False)
    )

    worst_station = station_summary.iloc[0]
    best_station = station_summary.iloc[-1]
    gap_station = worst_station["rata_rata_ispu"] - best_station["rata_rata_ispu"]

    k1, k2, k3 = st.columns(3)
    with k1:
        metric_card("Stasiun Terburuk", worst_station["stasiun"], f"Rata-rata ISPU {format_number(worst_station['rata_rata_ispu'])}")
    with k2:
        metric_card("Stasiun Terbaik", best_station["stasiun"], f"Rata-rata ISPU {format_number(best_station['rata_rata_ispu'])}")
    with k3:
        metric_card("Selisih Rata-rata", format_number(gap_station), "Gap stasiun terburuk vs terbaik")

    insight_box(
        "Analisis utama",
        f"Pada filter aktif, {worst_station['stasiun']} memiliki rata-rata ISPU tertinggi ({format_number(worst_station['rata_rata_ispu'])}), sementara {best_station['stasiun']} memiliki rata-rata ISPU terendah ({format_number(best_station['rata_rata_ispu'])}). Selisih rata-rata sebesar {format_number(gap_station)} poin menunjukkan adanya variasi spasial antar lokasi pemantauan.",
    )
    action_box(
        "Insight tindak lanjut untuk DLH DKI Jakarta",
        "Perbandingan antar stasiun dapat digunakan untuk menyusun prioritas pengawasan dan intervensi. Stasiun dengan rata-rata ISPU dan persentase hari tidak sehat yang lebih tinggi perlu menjadi titik awal evaluasi sumber pencemar dan penguatan pemantauan lapangan.",
    )

    c1, c2 = st.columns([1, 1])

    with c1:
        fig_station_bar = px.bar(
            station_summary,
            x="stasiun",
            y="rata_rata_ispu",
            text="rata_rata_ispu",
            title="Rata-rata ISPU per Stasiun",
            labels={"stasiun": "Stasiun", "rata_rata_ispu": "Rata-rata ISPU"},
        )
        fig_station_bar.update_traces(texttemplate="%{text:.1f}", textposition="outside")
        fig_station_bar.update_layout(height=460, margin=dict(l=10, r=10, t=60, b=120), xaxis_tickangle=-25)
        st.plotly_chart(fig_station_bar, use_container_width=True)
        chart_insight(
            "Insight rata-rata per stasiun",
            f"Grafik ini mengurutkan stasiun berdasarkan rata-rata ISPU. {worst_station['stasiun']} berada pada posisi tertinggi, sehingga perlu menjadi prioritas untuk evaluasi sumber pencemar dan pemantauan lebih detail. {best_station['stasiun']} dapat menjadi pembanding untuk melihat kondisi relatif yang lebih baik.",
        )

    with c2:
        category_station = (
            FILTERED.groupby(["stasiun", "categori"], as_index=False)
            .size()
            .rename(columns={"size": "jumlah"})
        )
        category_station["total_stasiun"] = category_station.groupby("stasiun")["jumlah"].transform("sum")
        category_station["persentase"] = category_station["jumlah"] / category_station["total_stasiun"] * 100
        fig_stack = px.bar(
            category_station,
            x="stasiun",
            y="persentase",
            color="categori",
            category_orders={"categori": CATEGORY_ORDER},
            color_discrete_map=CATEGORY_COLORS,
            title="Distribusi Kategori ISPU per Stasiun",
            labels={"stasiun": "Stasiun", "persentase": "Persentase (%)", "categori": "Kategori"},
        )
        fig_stack.update_layout(height=460, margin=dict(l=10, r=10, t=60, b=120), xaxis_tickangle=-25, barmode="stack")
        st.plotly_chart(fig_stack, use_container_width=True)
        unhealthy_by_station = category_station[category_station["categori"].isin(UNHEALTHY_CATEGORIES)].groupby("stasiun", as_index=False)["persentase"].sum().sort_values("persentase", ascending=False)
        top_unhealthy_station = unhealthy_by_station.iloc[0]
        chart_insight(
            "Insight distribusi kategori per stasiun",
            f"Stacked bar menunjukkan proporsi kategori kualitas udara pada tiap stasiun. {top_unhealthy_station['stasiun']} memiliki proporsi kategori Tidak Sehat ke atas paling besar ({format_pct(top_unhealthy_station['persentase'])}), sehingga menjadi lokasi yang perlu diprioritaskan untuk pengendalian risiko kualitas udara.",
        )

    fig_box = px.box(
        FILTERED,
        x="stasiun",
        y="max",
        points="outliers",
        title="Sebaran Nilai ISPU Harian per Stasiun",
        labels={"stasiun": "Stasiun", "max": "ISPU Harian (max)"},
    )
    fig_box.update_layout(height=480, margin=dict(l=10, r=10, t=60, b=120), xaxis_tickangle=-25)
    st.plotly_chart(fig_box, use_container_width=True)
    station_with_highest_max = station_summary.sort_values("nilai_maksimum", ascending=False).iloc[0]
    chart_insight(
        "Insight sebaran dan outlier",
        f"Boxplot memperlihatkan variasi harian dan outlier tiap stasiun. Nilai maksimum tertinggi terdapat pada {station_with_highest_max['stasiun']} sebesar {format_number(station_with_highest_max['nilai_maksimum'])}. Stasiun dengan banyak outlier tinggi perlu ditinjau sebagai lokasi yang berpotensi mengalami episode polusi ekstrem.",
    )

    st.subheader("Tabel Ringkasan Antar Stasiun")
    st.dataframe(
        station_summary.assign(
            rata_rata_ispu=lambda x: x["rata_rata_ispu"].round(2),
            median_ispu=lambda x: x["median_ispu"].round(2),
            pct_tidak_sehat=lambda x: x["pct_tidak_sehat"].round(2),
        ),
        use_container_width=True,
        hide_index=True,
    )
    chart_insight(
        "Insight tabel ringkasan stasiun",
        "Tabel ini merangkum rata-rata, median, nilai maksimum, persentase hari Tidak Sehat+, dan jumlah observasi per stasiun. Ringkasan ini dapat digunakan untuk menyusun prioritas lokasi secara lebih transparan karena tidak hanya melihat nilai rata-rata, tetapi juga risiko dan cakupan data.",
    )

# ============================================================
# DASHBOARD 4 — ANALISIS PARAMETER PENCEMAR KRITIS
# ============================================================
with tabs[3]:
    st.header("Dashboard 4 — Analisis Parameter Pencemar Kritis")
    st.write("Menganalisis parameter yang paling sering menjadi pencemar dominan berdasarkan kolom `critical`.")

    critical_summary = (
        FILTERED.dropna(subset=["critical"])
        .groupby("critical", as_index=False)
        .agg(jumlah=("critical", "count"), rata_rata_ispu=("max", "mean"), pct_tidak_sehat=("is_unhealthy", lambda x: x.mean() * 100))
    )
    critical_summary["persentase"] = critical_summary["jumlah"] / critical_summary["jumlah"].sum() * 100
    critical_summary = critical_summary.sort_values("jumlah", ascending=False)

    dominant_critical = critical_summary.iloc[0]
    high_risk_critical = critical_summary.sort_values("pct_tidak_sehat", ascending=False).iloc[0]

    k1, k2, k3 = st.columns(3)
    with k1:
        metric_card("Pencemar Dominan", dominant_critical["critical"], f"Muncul {format_pct(dominant_critical['persentase'])} dari observasi")
    with k2:
        metric_card("Pencemar Risiko Tertinggi", high_risk_critical["critical"], f"Tidak Sehat+ {format_pct(high_risk_critical['pct_tidak_sehat'])}")
    with k3:
        metric_card("Jumlah Jenis Pencemar", str(critical_summary["critical"].nunique()), "Parameter critical pada filter aktif")

    insight_box(
        "Analisis utama",
        f"Parameter {dominant_critical['critical']} merupakan pencemar kritis paling sering muncul dengan kontribusi {format_pct(dominant_critical['persentase'])}. Sementara itu, {high_risk_critical['critical']} memiliki proporsi kategori Tidak Sehat atau lebih buruk paling tinggi pada saat menjadi pencemar kritis.",
    )
    action_box(
        "Insight tindak lanjut untuk DLH DKI Jakarta",
        "Analisis pencemar kritis membantu menentukan fokus program pengendalian emisi. Parameter yang paling dominan dan paling sering terkait kondisi Tidak Sehat perlu dijadikan prioritas dalam pemantauan sumber pencemar, edukasi publik, dan koordinasi lintas sektor.",
    )

    c1, c2 = st.columns([1, 1])

    with c1:
        fig_critical_bar = px.bar(
            critical_summary,
            x="critical",
            y="jumlah",
            text="persentase",
            title="Frekuensi Pencemar Kritis",
            labels={"critical": "Pencemar Kritis", "jumlah": "Jumlah Observasi"},
        )
        fig_critical_bar.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig_critical_bar.update_layout(height=450, margin=dict(l=10, r=10, t=60, b=10))
        st.plotly_chart(fig_critical_bar, use_container_width=True)
        chart_insight(
            "Insight frekuensi pencemar kritis",
            f"Grafik ini menunjukkan parameter yang paling sering menentukan nilai ISPU harian. {dominant_critical['critical']} menjadi pencemar paling dominan dengan kontribusi {format_pct(dominant_critical['persentase'])}. Program pengurangan emisi sebaiknya memprioritaskan pencemar yang paling sering menjadi penentu kualitas udara.",
        )

    with c2:
        critical_station = (
            FILTERED.groupby(["stasiun", "critical"], as_index=False)
            .size()
            .rename(columns={"size": "jumlah"})
        )
        critical_station["total_stasiun"] = critical_station.groupby("stasiun")["jumlah"].transform("sum")
        critical_station["persentase"] = critical_station["jumlah"] / critical_station["total_stasiun"] * 100
        fig_critical_station = px.bar(
            critical_station,
            x="stasiun",
            y="persentase",
            color="critical",
            title="Komposisi Pencemar Kritis per Stasiun",
            labels={"stasiun": "Stasiun", "persentase": "Persentase (%)", "critical": "Pencemar"},
        )
        fig_critical_station.update_layout(height=450, margin=dict(l=10, r=10, t=60, b=120), xaxis_tickangle=-25, barmode="stack")
        st.plotly_chart(fig_critical_station, use_container_width=True)
        dominant_station_pollutant = critical_station.sort_values("persentase", ascending=False).iloc[0]
        chart_insight(
            "Insight komposisi per stasiun",
            f"Grafik ini menunjukkan bahwa karakteristik pencemar dapat berbeda antar stasiun. Kombinasi paling dominan pada filter aktif adalah {dominant_station_pollutant['critical']} di {dominant_station_pollutant['stasiun']} dengan proporsi {format_pct(dominant_station_pollutant['persentase'])}. Ini penting agar strategi pengendalian tidak disamaratakan untuk semua lokasi.",
        )

    critical_granularity = st.selectbox("Granularitas tren pencemar kritis", ["Bulanan", "Tahunan"], index=0)
    critical_time_col = "periode_bulanan" if critical_granularity == "Bulanan" else "periode_tahunan"
    critical_trend = (
        FILTERED.groupby([critical_time_col, "critical"], as_index=False)
        .size()
        .rename(columns={"size": "jumlah"})
        .sort_values(critical_time_col)
    )
    fig_critical_trend = px.line(
        critical_trend,
        x=critical_time_col,
        y="jumlah",
        color="critical",
        markers=(critical_granularity == "Tahunan"),
        title=f"Tren Kemunculan Pencemar Kritis ({critical_granularity})",
        labels={critical_time_col: "Periode", "jumlah": "Frekuensi", "critical": "Pencemar"},
    )
    fig_critical_trend.update_layout(height=500, hovermode="x unified", margin=dict(l=10, r=10, t=60, b=10))
    st.plotly_chart(fig_critical_trend, use_container_width=True)
    peak_critical_trend = critical_trend.sort_values("jumlah", ascending=False).iloc[0]
    chart_insight(
        "Insight tren pencemar kritis",
        f"Grafik tren memperlihatkan kapan suatu parameter paling sering menjadi pencemar kritis. Puncak frekuensi pada filter aktif terjadi untuk {peak_critical_trend['critical']} pada {pd.to_datetime(peak_critical_trend[critical_time_col]).strftime('%Y-%m-%d')} dengan {int(peak_critical_trend['jumlah'])} kejadian. Puncak seperti ini dapat menjadi dasar investigasi periode dan sumber emisi dominan.",
    )

# ============================================================
# DASHBOARD 5 — POLA MUSIMAN KUALITAS UDARA
# ============================================================
with tabs[4]:
    st.header("Dashboard 5 — Pola Musiman Kualitas Udara")
    st.write("Menampilkan pola kualitas udara berdasarkan bulan dalam setahun untuk mengidentifikasi bulan dengan polusi tertinggi dan terendah.")

    seasonal_summary = (
        FILTERED.groupby(["bulan", "nama_bulan"], as_index=False)
        .agg(rata_rata_ispu=("max", "mean"), pct_tidak_sehat=("is_unhealthy", lambda x: x.mean() * 100), jumlah_observasi=("max", "count"))
        .sort_values("bulan")
    )

    worst_month = seasonal_summary.loc[seasonal_summary["rata_rata_ispu"].idxmax()]
    best_month = seasonal_summary.loc[seasonal_summary["rata_rata_ispu"].idxmin()]

    c1, c2, c3 = st.columns(3)
    with c1:
        metric_card("Bulan Terburuk", worst_month["nama_bulan"], f"Rata-rata ISPU {format_number(worst_month['rata_rata_ispu'])}")
    with c2:
        metric_card("Bulan Terbaik", best_month["nama_bulan"], f"Rata-rata ISPU {format_number(best_month['rata_rata_ispu'])}")
    with c3:
        metric_card("Gap Musiman", format_number(worst_month["rata_rata_ispu"] - best_month["rata_rata_ispu"]), "Selisih rata-rata bulan tertinggi vs terendah")

    insight_box(
        "Analisis utama",
        f"Berdasarkan filter aktif, bulan {worst_month['nama_bulan']} memiliki rata-rata ISPU tertinggi sebesar {format_number(worst_month['rata_rata_ispu'])}, sedangkan bulan {best_month['nama_bulan']} memiliki rata-rata ISPU terendah sebesar {format_number(best_month['rata_rata_ispu'])}. Pola ini menunjukkan adanya variasi musiman yang perlu diperhatikan dalam perencanaan operasional.",
    )
    action_box(
        "Insight tindak lanjut untuk DLH DKI Jakarta",
        "Bulan dengan rata-rata ISPU tinggi dapat dijadikan periode prioritas untuk penguatan pemantauan, kesiapan komunikasi risiko, dan koordinasi pengendalian sumber pencemar. Interpretasi musim hujan/kemarau tetap perlu dilengkapi dengan data meteorologi karena dashboard ini hanya menggunakan data ISPU.",
    )

    heatmap_data = (
        FILTERED.groupby(["tahun", "bulan"], as_index=False)
        .agg(rata_rata_ispu=("max", "mean"))
    )
    heatmap_pivot = heatmap_data.pivot(index="tahun", columns="bulan", values="rata_rata_ispu")
    heatmap_pivot = heatmap_pivot.reindex(columns=list(range(1, 13)))
    heatmap_pivot.columns = [MONTH_MAP.get(c, str(c)) for c in heatmap_pivot.columns]

    fig_heatmap = px.imshow(
        heatmap_pivot,
        aspect="auto",
        text_auto=".0f",
        title="Heatmap Rata-rata ISPU Berdasarkan Tahun dan Bulan",
        labels=dict(x="Bulan", y="Tahun", color="Rata-rata ISPU"),
    )
    fig_heatmap.update_layout(height=560, margin=dict(l=10, r=10, t=60, b=10))
    st.plotly_chart(fig_heatmap, use_container_width=True)
    heatmap_max = heatmap_data.sort_values("rata_rata_ispu", ascending=False).iloc[0]
    chart_insight(
        "Insight heatmap musiman",
        f"Heatmap memperlihatkan kombinasi tahun-bulan dengan rata-rata ISPU tinggi dan rendah. Sel paling tinggi pada filter aktif terjadi pada bulan {MONTH_MAP.get(int(heatmap_max['bulan']))} tahun {int(heatmap_max['tahun'])} dengan rata-rata ISPU {format_number(heatmap_max['rata_rata_ispu'])}. Pola warna yang berulang pada bulan tertentu dapat menjadi sinyal periode musiman berisiko.",
    )

    c1, c2 = st.columns([1, 1])
    with c1:
        fig_season_bar = px.bar(
            seasonal_summary,
            x="nama_bulan",
            y="rata_rata_ispu",
            text="rata_rata_ispu",
            title="Rata-rata ISPU Menurut Bulan",
            labels={"nama_bulan": "Bulan", "rata_rata_ispu": "Rata-rata ISPU"},
            category_orders={"nama_bulan": MONTH_ORDER},
        )
        fig_season_bar.update_traces(texttemplate="%{text:.1f}", textposition="outside")
        fig_season_bar.update_layout(height=430, margin=dict(l=10, r=10, t=60, b=10))
        st.plotly_chart(fig_season_bar, use_container_width=True)
        chart_insight(
            "Insight rata-rata bulanan",
            f"Bar chart memperjelas peringkat bulan berdasarkan rata-rata ISPU. Bulan {worst_month['nama_bulan']} perlu menjadi periode antisipasi utama, sedangkan bulan {best_month['nama_bulan']} dapat menjadi pembanding kondisi yang relatif lebih baik. Informasi ini berguna untuk kalender pengawasan kualitas udara.",
        )

    with c2:
        station_month = (
            FILTERED.groupby(["stasiun", "bulan", "nama_bulan"], as_index=False)
            .agg(rata_rata_ispu=("max", "mean"))
            .sort_values("bulan")
        )
        fig_station_month = px.line(
            station_month,
            x="nama_bulan",
            y="rata_rata_ispu",
            color="stasiun",
            markers=True,
            title="Pola Bulanan per Stasiun",
            labels={"nama_bulan": "Bulan", "rata_rata_ispu": "Rata-rata ISPU", "stasiun": "Stasiun"},
            category_orders={"nama_bulan": MONTH_ORDER},
        )
        fig_station_month.update_layout(height=430, margin=dict(l=10, r=10, t=60, b=10))
        st.plotly_chart(fig_station_month, use_container_width=True)
        peak_station_month = station_month.sort_values("rata_rata_ispu", ascending=False).iloc[0]
        chart_insight(
            "Insight pola bulanan per stasiun",
            f"Line chart menunjukkan apakah pola musiman terjadi merata atau berbeda antar stasiun. Kombinasi tertinggi pada filter aktif adalah {peak_station_month['stasiun']} pada bulan {peak_station_month['nama_bulan']} dengan rata-rata ISPU {format_number(peak_station_month['rata_rata_ispu'])}. Ini dapat membantu menargetkan pengawasan musiman per lokasi.",
        )

    st.subheader("Tabel Ringkasan Pola Musiman")
    st.dataframe(
        seasonal_summary.assign(
            rata_rata_ispu=lambda x: x["rata_rata_ispu"].round(2),
            pct_tidak_sehat=lambda x: x["pct_tidak_sehat"].round(2),
        )[["bulan", "nama_bulan", "rata_rata_ispu", "pct_tidak_sehat", "jumlah_observasi"]],
        use_container_width=True,
        hide_index=True,
    )
    chart_insight(
        "Insight tabel musiman",
        "Tabel musiman memberikan angka pendukung untuk membaca heatmap dan grafik bulanan. Kolom persentase hari Tidak Sehat+ penting karena bulan dengan rata-rata tinggi belum tentu memiliki risiko kategori yang sama; keduanya perlu dilihat bersamaan dalam perencanaan operasional.",
    )

# ============================================================
# DASHBOARD 6 — RISIKO HARI TIDAK SEHAT
# ============================================================
with tabs[5]:
    st.header("Dashboard 6 — Risiko Hari Tidak Sehat")
    st.write("Mengukur frekuensi dan persentase hari dengan kategori Tidak Sehat atau lebih buruk berdasarkan data kategori risiko harian.")

    risk_summary = (
        FILTERED.groupby("categori", as_index=False)
        .agg(jumlah=("categori", "count"), rata_rata_ispu=("max", "mean"))
    )
    risk_summary["persentase"] = risk_summary["jumlah"] / risk_summary["jumlah"].sum() * 100
    risk_summary["categori"] = pd.Categorical(risk_summary["categori"], categories=CATEGORY_ORDER, ordered=True)
    risk_summary = risk_summary.sort_values("categori")

    unhealthy_count = int(FILTERED["is_unhealthy"].sum())
    total_count = int(len(FILTERED))
    highest_risk_cat = risk_summary.sort_values("rata_rata_ispu", ascending=False).iloc[0]

    k1, k2, k3 = st.columns(3)
    with k1:
        metric_card("Jumlah Observasi Tidak Sehat+", f"{unhealthy_count:,}".replace(",", "."), f"Dari {total_count:,} observasi".replace(",", "."))
    with k2:
        metric_card("Persentase Tidak Sehat+", format_pct(pct_unhealthy), "Kategori Tidak Sehat, Sangat Tidak Sehat, atau Berbahaya")
    with k3:
        metric_card("Kategori Risiko Tertinggi", str(highest_risk_cat["categori"]), f"Rata-rata ISPU {format_number(highest_risk_cat['rata_rata_ispu'])}")

    fig_risk_bar = px.bar(
        risk_summary,
        x="categori",
        y="jumlah",
        text="persentase",
        color="categori",
        color_discrete_map=CATEGORY_COLORS,
        category_orders={"categori": CATEGORY_ORDER},
        title="Frekuensi Kategori Risiko Kualitas Udara",
        labels={"categori": "Kategori ISPU", "jumlah": "Jumlah observasi"},
    )
    fig_risk_bar.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig_risk_bar.update_layout(height=460, margin=dict(l=10, r=10, t=60, b=80))
    st.plotly_chart(fig_risk_bar, use_container_width=True)
    dominant_risk_cat = risk_summary.sort_values("jumlah", ascending=False).iloc[0]
    chart_insight(
        "Insight frekuensi risiko",
        f"Grafik ini menunjukkan komposisi kategori risiko kualitas udara. Kategori paling sering muncul adalah {dominant_risk_cat['categori']} dengan proporsi {format_pct(dominant_risk_cat['persentase'])}. Fokus kebijakan perlu diarahkan pada pengurangan proporsi kategori Tidak Sehat ke atas karena kategori tersebut berkaitan langsung dengan risiko kesehatan publik.",
    )

    monthly_risk = (
        FILTERED.groupby("periode_bulanan", as_index=False)
        .agg(pct_tidak_sehat=("is_unhealthy", lambda x: x.mean() * 100), rata_rata_ispu=("max", "mean"), jumlah_observasi=("max", "count"))
        .sort_values("periode_bulanan")
    )
    fig_monthly_risk = px.line(
        monthly_risk,
        x="periode_bulanan",
        y="pct_tidak_sehat",
        markers=True,
        title="Tren Persentase Hari Tidak Sehat+ per Bulan",
        labels={"periode_bulanan": "Bulan", "pct_tidak_sehat": "Persentase Tidak Sehat+ (%)"},
    )
    fig_monthly_risk.update_layout(height=460, hovermode="x unified", margin=dict(l=10, r=10, t=60, b=10))
    st.plotly_chart(fig_monthly_risk, use_container_width=True)
    peak_monthly_risk = monthly_risk.sort_values("pct_tidak_sehat", ascending=False).iloc[0]
    chart_insight(
        "Insight tren risiko bulanan",
        f"Grafik ini memperlihatkan bulan-bulan dengan proporsi hari Tidak Sehat+ tertinggi. Puncak risiko pada filter aktif terjadi pada {pd.to_datetime(peak_monthly_risk['periode_bulanan']).strftime('%b %Y')} dengan {format_pct(peak_monthly_risk['pct_tidak_sehat'])} observasi Tidak Sehat+. Periode puncak seperti ini perlu menjadi prioritas peringatan dini dan pengawasan operasional.",
    )

    station_risk = (
        FILTERED.groupby("stasiun", as_index=False)
        .agg(pct_tidak_sehat=("is_unhealthy", lambda x: x.mean() * 100), jumlah_observasi=("max", "count"), rata_rata_ispu=("max", "mean"))
        .sort_values("pct_tidak_sehat", ascending=False)
    )
    fig_station_risk = px.bar(
        station_risk,
        x="stasiun",
        y="pct_tidak_sehat",
        text="pct_tidak_sehat",
        title="Persentase Hari Tidak Sehat+ per Stasiun",
        labels={"stasiun": "Stasiun", "pct_tidak_sehat": "Persentase Tidak Sehat+ (%)"},
    )
    fig_station_risk.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig_station_risk.update_layout(height=460, margin=dict(l=10, r=10, t=60, b=120), xaxis_tickangle=-25)
    st.plotly_chart(fig_station_risk, use_container_width=True)
    top_station_risk = station_risk.iloc[0]
    chart_insight(
        "Insight risiko per stasiun",
        f"Grafik ini menunjukkan stasiun yang paling sering mengalami kondisi Tidak Sehat+. {top_station_risk['stasiun']} memiliki persentase tertinggi sebesar {format_pct(top_station_risk['pct_tidak_sehat'])}. Stasiun ini dapat menjadi prioritas intervensi karena frekuensi risiko kesehatannya paling besar pada filter aktif.",
    )

    action_box(
        "Insight tindak lanjut untuk DLH DKI Jakarta",
        "Dashboard risiko hari tidak sehat dapat digunakan untuk menentukan ambang respons operasional, seperti penyiapan komunikasi risiko saat proporsi hari Tidak Sehat+ meningkat, pengawasan periode puncak, dan penentuan lokasi prioritas berdasarkan persentase risiko tertinggi."
    )

# ============================================================
# DASHBOARD 7 — MATRIKS PRIORITAS INTERVENSI STASIUN
# ============================================================
with tabs[6]:
    st.header("Dashboard 7 — Matriks Prioritas Intervensi Stasiun")
    st.write("Menyusun prioritas intervensi stasiun berdasarkan rata-rata ISPU, persentase hari Tidak Sehat+, dan tren perubahan kualitas udara.")

    base_priority = (
        FILTERED.groupby("stasiun", as_index=False)
        .agg(
            rata_rata_ispu=("max", "mean"),
            pct_tidak_sehat=("is_unhealthy", lambda x: x.mean() * 100),
            nilai_maksimum=("max", "max"),
            jumlah_observasi=("max", "count"),
        )
    )
    slopes = compute_trend_slope(FILTERED, ["stasiun"])
    priority = base_priority.merge(slopes, on="stasiun", how="left")
    priority["skor_ispu"] = normalize_series(priority["rata_rata_ispu"])
    priority["skor_risiko"] = normalize_series(priority["pct_tidak_sehat"])
    priority["skor_tren"] = normalize_series(priority["trend_slope"])
    priority["skor_prioritas"] = (0.45 * priority["skor_ispu"] + 0.40 * priority["skor_risiko"] + 0.15 * priority["skor_tren"])
    priority["kategori_prioritas"] = priority["skor_prioritas"].apply(priority_label)
    priority = priority.sort_values("skor_prioritas", ascending=False)

    top_priority = priority.iloc[0]
    low_priority = priority.iloc[-1]

    k1, k2, k3 = st.columns(3)
    with k1:
        metric_card("Prioritas Utama", top_priority["stasiun"], f"Skor {format_number(top_priority['skor_prioritas'])}")
    with k2:
        metric_card("Kategori Prioritas", top_priority["kategori_prioritas"], "Berdasarkan skor gabungan")
    with k3:
        metric_card("Prioritas Terendah", low_priority["stasiun"], f"Skor {format_number(low_priority['skor_prioritas'])}")

    fig_matrix = px.scatter(
        priority,
        x="rata_rata_ispu",
        y="pct_tidak_sehat",
        size="skor_prioritas",
        color="kategori_prioritas",
        text="stasiun",
        color_discrete_map=PRIORITY_COLORS,
        title="Matriks Prioritas Intervensi Stasiun",
        labels={"rata_rata_ispu": "Rata-rata ISPU", "pct_tidak_sehat": "Tidak Sehat+ (%)", "kategori_prioritas": "Kategori prioritas"},
        hover_data={"trend_slope": ":.3f", "skor_prioritas": ":.1f", "jumlah_observasi": True},
    )
    fig_matrix.update_traces(textposition="top center")
    fig_matrix.update_layout(height=540, margin=dict(l=10, r=10, t=60, b=10))
    st.plotly_chart(fig_matrix, use_container_width=True)
    chart_insight(
        "Insight matriks prioritas",
        f"Matriks ini memetakan stasiun berdasarkan rata-rata ISPU dan persentase hari Tidak Sehat+. {top_priority['stasiun']} menjadi prioritas utama karena memiliki kombinasi skor risiko paling tinggi. Stasiun yang berada di kanan-atas perlu mendapat perhatian lebih besar karena kualitas udara rata-rata tinggi dan frekuensi risiko juga tinggi.",
    )

    fig_priority_score = px.bar(
        priority,
        x="stasiun",
        y="skor_prioritas",
        color="kategori_prioritas",
        color_discrete_map=PRIORITY_COLORS,
        text="skor_prioritas",
        title="Skor Prioritas Intervensi per Stasiun",
        labels={"stasiun": "Stasiun", "skor_prioritas": "Skor prioritas", "kategori_prioritas": "Kategori prioritas"},
    )
    fig_priority_score.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig_priority_score.update_layout(height=460, margin=dict(l=10, r=10, t=60, b=120), xaxis_tickangle=-25)
    st.plotly_chart(fig_priority_score, use_container_width=True)
    chart_insight(
        "Insight skor prioritas",
        f"Bar chart mengurutkan stasiun berdasarkan skor prioritas gabungan. Skor tertinggi berada pada {top_priority['stasiun']} dengan nilai {format_number(top_priority['skor_prioritas'])}. Hasil ini dapat dipakai sebagai dasar awal penyusunan urutan lokasi intervensi, bukan sebagai kesimpulan tunggal tanpa validasi lapangan.",
    )

    st.subheader("Tabel Matriks Prioritas")
    priority_display = priority[["stasiun", "rata_rata_ispu", "pct_tidak_sehat", "trend_slope", "nilai_maksimum", "jumlah_observasi", "skor_prioritas", "kategori_prioritas"]].copy()
    for col in ["rata_rata_ispu", "pct_tidak_sehat", "trend_slope", "nilai_maksimum", "skor_prioritas"]:
        priority_display[col] = priority_display[col].round(2)
    st.dataframe(priority_display, use_container_width=True, hide_index=True)
    chart_insight(
        "Insight tabel prioritas",
        "Tabel ini menunjukkan komponen pembentuk prioritas: rata-rata ISPU, persentase hari Tidak Sehat+, tren, nilai maksimum, dan jumlah observasi. Transparansi komponen ini penting agar Kepala DLH dapat melihat alasan suatu stasiun ditempatkan sebagai prioritas tinggi, sedang, atau rendah.",
    )

    action_box(
        "Insight tindak lanjut untuk DLH DKI Jakarta",
        "Matriks prioritas dapat digunakan untuk mengarahkan sumber daya pemantauan dan intervensi secara bertahap. Lokasi prioritas tinggi sebaiknya menjadi fokus awal untuk penelusuran sumber pencemar, penguatan koordinasi lintas sektor, serta pemantauan efektivitas kebijakan."
    )

# ============================================================
# DASHBOARD 8 — ANOMALI DAN EPISODE POLUSI EKSTREM
# ============================================================
with tabs[7]:
    st.header("Dashboard 8 — Anomali dan Episode Polusi Ekstrem")
    st.write("Mendeteksi lonjakan ISPU dan episode polusi ekstrem berdasarkan data harian per stasiun.")

    q1 = FILTERED["max"].quantile(0.25)
    q3 = FILTERED["max"].quantile(0.75)
    iqr = q3 - q1
    iqr_threshold = q3 + 1.5 * iqr
    threshold_choice = st.radio(
        "Metode ambang anomali",
        ["IQR outlier", "ISPU >= 200", "Top 1%"],
        horizontal=True,
    )

    if threshold_choice == "IQR outlier":
        threshold_value = iqr_threshold
    elif threshold_choice == "ISPU >= 200":
        threshold_value = 200
    else:
        threshold_value = FILTERED["max"].quantile(0.99)

    anomaly = FILTERED[FILTERED["max"] >= threshold_value].copy().sort_values("max", ascending=False)
    anomaly_count = int(len(anomaly))
    anomaly_pct = anomaly_count / len(FILTERED) * 100 if len(FILTERED) else 0
    top_episode = anomaly.iloc[0] if not anomaly.empty else FILTERED.sort_values("max", ascending=False).iloc[0]

    k1, k2, k3 = st.columns(3)
    with k1:
        metric_card("Ambang Anomali", format_number(threshold_value), threshold_choice)
    with k2:
        metric_card("Jumlah Episode", f"{anomaly_count:,}".replace(",", "."), f"{format_pct(anomaly_pct)} dari data terfilter")
    with k3:
        metric_card("ISPU Tertinggi", format_number(top_episode["max"]), f"{top_episode['stasiun']} | {top_episode['critical']}")

    fig_anomaly_time = px.scatter(
        FILTERED.sort_values("tanggal"),
        x="tanggal",
        y="max",
        color="categori",
        color_discrete_map=CATEGORY_COLORS,
        hover_data={"stasiun": True, "critical": True, "max": ":.1f"},
        title="Sebaran Harian ISPU dan Episode Anomali/Ekstrem",
        labels={"tanggal": "Tanggal", "max": "ISPU harian (max)", "categori": "Kategori"},
    )
    fig_anomaly_time.add_hline(y=threshold_value, line_dash="dash", annotation_text=f"Ambang {format_number(threshold_value)}", annotation_position="top left")
    fig_anomaly_time.update_layout(height=520, margin=dict(l=10, r=10, t=60, b=10))
    st.plotly_chart(fig_anomaly_time, use_container_width=True)
    chart_insight(
        "Insight sebaran anomali",
        f"Scatter plot menampilkan seluruh observasi harian dan garis ambang anomali. Terdapat {anomaly_count:,} episode di atas ambang {format_number(threshold_value)} atau {format_pct(anomaly_pct)} dari data terfilter. Titik yang jauh di atas ambang perlu ditelusuri sebagai episode polusi ekstrem atau potensi kejadian khusus.".replace(",", "."),
    )

    c1, c2 = st.columns([1, 1])
    with c1:
        anomaly_station = (
            anomaly.groupby("stasiun", as_index=False)
            .agg(jumlah_episode=("max", "count"), rata_rata_episode=("max", "mean"), maksimum_episode=("max", "max"))
            .sort_values("jumlah_episode", ascending=False)
        )
        if anomaly_station.empty:
            anomaly_station = pd.DataFrame({"stasiun": [], "jumlah_episode": [], "rata_rata_episode": [], "maksimum_episode": []})
        fig_anomaly_station = px.bar(
            anomaly_station,
            x="stasiun",
            y="jumlah_episode",
            text="jumlah_episode",
            title="Jumlah Episode Anomali/Ekstrem per Stasiun",
            labels={"stasiun": "Stasiun", "jumlah_episode": "Jumlah episode"},
        )
        fig_anomaly_station.update_traces(textposition="outside")
        fig_anomaly_station.update_layout(height=450, margin=dict(l=10, r=10, t=60, b=120), xaxis_tickangle=-25)
        st.plotly_chart(fig_anomaly_station, use_container_width=True)
        if not anomaly_station.empty:
            top_anomaly_station = anomaly_station.iloc[0]
            station_text = f"{top_anomaly_station['stasiun']} memiliki jumlah episode anomali/ekstrem terbanyak, yaitu {int(top_anomaly_station['jumlah_episode'])} episode. Lokasi ini perlu diprioritaskan untuk investigasi saat terjadi lonjakan ISPU."
        else:
            station_text = "Tidak ada episode yang melewati ambang pada filter aktif. Hal ini menunjukkan kondisi relatif tidak ekstrem berdasarkan metode ambang yang dipilih."
        chart_insight("Insight episode per stasiun", station_text)

    with c2:
        anomaly_critical = (
            anomaly.groupby("critical", as_index=False)
            .agg(jumlah_episode=("max", "count"), rata_rata_episode=("max", "mean"))
            .sort_values("jumlah_episode", ascending=False)
        )
        fig_anomaly_critical = px.bar(
            anomaly_critical,
            x="critical",
            y="jumlah_episode",
            text="jumlah_episode",
            title="Pencemar Kritis Saat Episode Anomali/Ekstrem",
            labels={"critical": "Pencemar kritis", "jumlah_episode": "Jumlah episode"},
        )
        fig_anomaly_critical.update_traces(textposition="outside")
        fig_anomaly_critical.update_layout(height=450, margin=dict(l=10, r=10, t=60, b=10))
        st.plotly_chart(fig_anomaly_critical, use_container_width=True)
        if not anomaly_critical.empty:
            top_anomaly_critical = anomaly_critical.iloc[0]
            critical_text = f"Saat episode anomali/ekstrem, pencemar yang paling sering muncul adalah {top_anomaly_critical['critical']} dengan {int(top_anomaly_critical['jumlah_episode'])} episode. Ini memberi petunjuk awal jenis pencemar yang perlu menjadi fokus investigasi saat lonjakan terjadi."
        else:
            critical_text = "Tidak ada episode anomali pada filter aktif, sehingga tidak ada pencemar dominan yang dapat disimpulkan untuk kondisi ekstrem."
        chart_insight("Insight pencemar saat episode ekstrem", critical_text)

    st.subheader("Top Episode Polusi Ekstrem")
    top_episodes = anomaly.head(20) if not anomaly.empty else FILTERED.sort_values("max", ascending=False).head(20)
    st.dataframe(
        top_episodes[["tanggal", "stasiun", "max", "critical", "categori"]].assign(tanggal=lambda x: x["tanggal"].dt.strftime("%Y-%m-%d")),
        use_container_width=True,
        hide_index=True,
    )
    chart_insight(
        "Insight tabel episode ekstrem",
        f"Tabel ini menampilkan daftar hari dengan nilai ISPU tertinggi pada filter aktif. Episode tertinggi terjadi pada {top_episode['tanggal'].strftime('%Y-%m-%d')} di {top_episode['stasiun']} dengan ISPU {format_number(top_episode['max'])}, kategori {top_episode['categori']}, dan pencemar kritis {top_episode['critical']}. Tabel ini dapat digunakan sebagai daftar awal untuk penelusuran kejadian polusi ekstrem.",
    )

    action_box(
        "Insight tindak lanjut untuk DLH DKI Jakarta",
        "Dashboard anomali membantu membangun daftar prioritas investigasi. Episode ekstrem perlu dikaitkan dengan data lapangan, meteorologi, aktivitas transportasi/industri, dan laporan kejadian untuk membedakan lonjakan alami, gangguan alat, atau kejadian pencemaran spesifik."
    )

# ------------------------------------------------------------
# FOOTER
# ------------------------------------------------------------
st.markdown("---")
st.caption(
    "Catatan: Dashboard ini menggunakan data ISPU yang tersedia pada dataset. Interpretasi penyebab polusi perlu dilengkapi dengan data meteorologi, lalu lintas, aktivitas industri, dan sumber emisi lainnya."
)
st.markdown('<div class="footer-box">© 2026 Raihan Ferdyanza w/ AI</div>', unsafe_allow_html=True)
