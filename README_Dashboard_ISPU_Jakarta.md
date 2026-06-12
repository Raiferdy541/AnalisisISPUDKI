# Dashboard BI ISPU Jakarta — 8 Dashboard Interaktif

Dashboard ini dibuat untuk studi kasus **Analisis Kualitas Udara Jakarta Berbasis Data ISPU**. Tools yang digunakan adalah **Python Streamlit** dengan visualisasi interaktif berbasis Plotly.

## Isi Dashboard

1. **Overview Kualitas Udara Jakarta**  
   KPI rata-rata ISPU, persentase hari Tidak Sehat+, pencemar dominan, kondisi terkini per stasiun, dan peta SPKU.

2. **Tren Temporal Kualitas Udara**  
   Tren nilai ISPU dengan granularitas harian, bulanan, dan tahunan, serta filter per stasiun.

3. **Perbandingan Kualitas Udara Antar Stasiun**  
   Perbandingan rata-rata ISPU, distribusi kategori ISPU, dan sebaran nilai ISPU harian antar stasiun.

4. **Analisis Parameter Pencemar Kritis**  
   Distribusi, komposisi per stasiun, dan tren kemunculan pencemar kritis seperti PM10, PM2.5, O3, CO, SO2, dan NO2.

5. **Pola Musiman Kualitas Udara**  
   Heatmap tahun-bulan, rata-rata ISPU bulanan, dan pola bulanan per stasiun.

6. **Risiko Hari Tidak Sehat**  
   Frekuensi kategori risiko, tren persentase hari Tidak Sehat+, dan risiko per stasiun.

7. **Matriks Prioritas Intervensi Stasiun**  
   Skor prioritas berdasarkan rata-rata ISPU, persentase hari Tidak Sehat+, dan tren perubahan kualitas udara.

8. **Anomali dan Episode Polusi Ekstrem**  
   Deteksi episode ekstrem menggunakan ambang IQR, ISPU >= 200, atau Top 1%, serta daftar episode prioritas investigasi.

## Revisi Terbaru

Setiap chart/visualisasi sudah dilengkapi **penjelasan atau insight langsung di bawah visualisasi**. Insight menjelaskan arti grafik, temuan utama, serta relevansinya untuk keputusan Dinas Lingkungan Hidup DKI Jakarta.

Footer dashboard juga sudah memuat:

**© 2026 Raihan Ferdyanza w/ AI**

## File Utama

- `app_ispu_dashboard.py` — kode utama aplikasi Streamlit.
- `ispu_jakarta_validated_clean.csv` — dataset bersih hasil validasi.
- `requirements_dashboard_ispu.txt` — daftar library Python.

## Cara Menjalankan

Pastikan Python sudah terpasang, lalu jalankan perintah berikut dari folder file dashboard:

```bash
pip install -r requirements_dashboard_ispu.txt
streamlit run app_ispu_dashboard.py
```

Dashboard akan terbuka pada browser lokal melalui alamat yang ditampilkan oleh Streamlit, biasanya:

```bash
http://localhost:8501
```

## Catatan Interpretasi

Dashboard ini menggunakan data ISPU yang tersedia pada dataset. Interpretasi penyebab polusi perlu dilengkapi dengan data meteorologi, lalu lintas, aktivitas industri, sumber emisi, dan informasi lapangan lainnya.
