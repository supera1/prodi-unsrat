# prodi-unsrat — Platform Website Program Studi UNSRAT

Situs ke-97 program studi Universitas Sam Ratulangi di `https://prodi.unsrat.ac.id/<slug>/`, dengan template seragam
yang mengikuti kriteria akreditasi dan bisa disesuaikan oleh tiap prodi.

> **Status 19 November 2026:** Fase 1 selesai (PR #1). Fase 2 (penyunting halaman wajib,
> [rencana](docs/rencana-fase-02.md)): langkah 1–7 selesai, termasuk halaman tambahan, impor Excel, dan tugas akhir;
> situs tayang di produksi `https://prodi.unsrat.ac.id` dengan prodi pilot. Fase 5 (versi bahasa Inggris,
> [rencana](docs/rencana-fase-05.md), disetujui) dikerjakan lebih dulu dari Fase 3 dan 4.
> Rencana: [docs/rencana-fase-01.md](docs/rencana-fase-01.md) · Keputusan: [docs/keputusan.md](docs/keputusan.md)

## Cara kerja singkat

- Data resmi prodi (nama, gelar, SKS, CPL, akreditasi) berasal dari www.unsrat.ac.id: diunggah superadmin (Excel
  ekspor program studi dari www, atau berkas JSON www). Prodi boleh mengubahnya sebagai timpaan per kolom (K-P16).
- Generator membangun halaman statis untuk setiap prodi dari data resmi itu ditambah isi yang diisi prodi.
- Admin (hanya dari jaringan/VPN UNSRAT) punya tiga peran: superadmin, admin prodi, operator.
- Produksi: stack Docker `prodi-unsrat` di VM sendiri, di-deploy admin UNSRAT dari GitHub (K-P17) mengikuti
  [docs/deploy.md](docs/deploy.md). Data www diunggah superadmin (K-P18); unggahan disimpan di VM (K-P19).

## Menjalankan uji

```bash
python3 -m venv .venv
.venv/bin/pip install -r platform/admin/requirements.txt -c platform/admin/constraints.txt
.venv/bin/python uji/jalankan-semua.py
```

## Menyiapkan data di komputer pengembang

Dengan repo www di folder sebelahnya (`../website-unsrat-2026`):

```bash
python3 platform/tarik_www.py --terapkan
python3 platform/registri.py --siapkan
.venv/bin/python platform/bangun/bangun.py
python3 -m http.server 8790 --bind 127.0.0.1 --directory publik
```

Lalu buka http://127.0.0.1:8790/. Tanpa repo www di sebelahnya, data awal yang ikut repo bisa dipakai:
`python3 platform/impor_www.py --isi-awal` (menerapkan `platform/data-awal/www/` dan daftar slug).

Admin (akun per orang, hanya dari jaringan UNSRAT; di komputer pengembang juga dari komputer itu sendiri):

```bash
python3 platform/admin/siapkan.py
.venv/bin/python platform/admin/siapkan.py --superadmin namaanda --nama-lengkap "Nama Anda"
.venv/bin/python platform/admin/app.py
```

Kata sandi sementara ada di `rahasia/.kredensial-namaanda.txt`; buka http://127.0.0.1:8791/, masuk, buat kata sandi
sendiri, lalu hapus berkas itu. Hasilnya di `data/`, `riwayat/`, `publik/`, dan `nginx-buatan/` (tidak masuk Git).

Stack Docker lengkap di komputer sendiri: [docs/deploy.md §13](docs/deploy.md#13-mencoba-di-komputer-sendiri-pengembang).

## Urutan Fase 1

| Langkah | Isi | Status |
|---|---|---|
| 1 | Kerangka repo, dokumen, modul aman dari www, uji slug | selesai |
| 2 | Model data + tarik data www | selesai |
| 3 | Template induk + generator | selesai |
| 3b | Pengumuman dan berita | selesai |
| 3c | Bagian depan beranda per prodi | selesai |
| 4 | Akun & peran | selesai |
| 5 | Superadmin | selesai |
| 5b | Data prodi bisa diubah (termasuk CPL), bentrok dengan www ditandai | selesai |
| 6 | Admin prodi | selesai |
| 7 | Docker & deploy di VM sendiri | selesai |
| 8 | Uji menyeluruh + log fase | selesai (digabung ke `main`, PR #1) |

## Urutan Fase 2

| Langkah | Isi | Status |
|---|---|---|
| 0 | Rencana Fase 2 | disetujui |
| 1 | Model data dan templat isi 22 halaman wajib + 2 opsional, tampilan di situs | selesai |
| 2 | Penyunting di admin: formulir dari templat, unggah PDF/foto, draf, pratinjau | selesai |
| 3 | Alur ajukan/terbitkan/kembalikan/tarik, riwayat per halaman, kelengkapan (dasbor, superadmin, CSV) | selesai |
| 4 | Dokumen Akreditasi (di halaman Akreditasi) dan label kriteria (draf untuk LPMPP, [panduan](docs/kriteria-akreditasi.md)) | selesai |
| 5 | [Panduan admin prodi](docs/panduan-admin-prodi.md) (juga di admin), menu Masukan, [persiapan pilot](docs/pilot-fase-02.md) | selesai |
| 5b | Tautan dosen 94 prodi (dosen.unsrat.ac.id) di data awal VM baru (K-P31) | selesai, menunggu tinjauan |
| 6 | Pilot 3 prodi | berjalan (staging, lalu produksi) |
| 7 | Pilihan tambahan: impor Excel, halaman tambahan dan sematan, tugas akhir, masukan pilot (7–7e) | selesai |
| 8 | Uji menyeluruh + log fase | — |

## Urutan Fase 5 (versi bahasa Inggris)

| Langkah | Isi | Status |
|---|---|---|
| 0 | [Rencana Fase 5](docs/rencana-fase-05.md) (K-P37) | disetujui |
| 1 | Kerangka bahasa di situs: teks dan label Inggris, `/<slug>/en/` dari data resmi, tombol bahasa, `hreflang`, sitemap, saklar superadmin | selesai |
| 2a | Isi Inggris di penyunting: tab English, alur dan riwayat, tanda perlu diperbarui, kolom English, kelengkapan | selesai |
| 2b | Teks Inggris lainnya: bagian depan beranda, label menu, nama halaman tambahan, label kriteria | selesai |
| 3 | Terjemahan mesin (DeepL) dengan istilah tetap, pemeriksaan hasil, dan batas pemakaian | selesai |
| 4 | Pengumuman berbahasa Inggris: isian Inggris dan terjemahan mesin di formulir pengumuman, menu News di versi Inggris | selesai |
| 5 | Panduan dan prodi berversi Inggris: kotak versi Inggris di Ringkasan prodi, [persiapan enam prodi](docs/versi-inggris-prodi.md), batas CPL Data prodi | selesai; menunggu deploy |
| 5a | Terjemahkan semua: satu tombol untuk semua halaman dan pengumuman, di latar; saringan dan tombol "… dan buka berikutnya" untuk memeriksa | selesai, menunggu tinjauan |
| 5b | Versi Inggris hanya untuk prodi akreditasi internasional (K-P38): saklar superadmin mengatur juga penyunting, isian, dan terjemahan mesin | selesai, menunggu tinjauan |
| 6 | Uji menyeluruh + log fase | — |
