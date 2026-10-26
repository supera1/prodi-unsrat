# prodi-unsrat — Platform Website Program Studi UNSRAT

Situs ke-97 program studi Universitas Sam Ratulangi di `https://prodi.unsrat.ac.id/<slug>/`, dengan template seragam
yang mengikuti kriteria akreditasi dan bisa disesuaikan oleh tiap prodi.

> **Status 26 Oktober 2026:** Fase 1 langkah 6 (admin prodi): identitas, logo, bagian depan beranda, menu, pengumuman dengan alur operator → admin
> prodi, dan riwayat bisa dikelola dari admin. Berikutnya langkah 7: Docker dan deploy staging.
> Rencana: [docs/rencana-fase-01.md](docs/rencana-fase-01.md) · Keputusan: [docs/keputusan.md](docs/keputusan.md)

## Cara kerja singkat

- Data resmi prodi (nama, gelar, SKS, CPL, akreditasi) dibaca dari data www.unsrat.ac.id dan tidak diubah di sini.
- Generator membangun halaman statis untuk setiap prodi dari data resmi itu ditambah isi yang diisi prodi.
- Admin (hanya dari jaringan/VPN UNSRAT) punya tiga peran: superadmin, admin prodi, operator.
- Produksi: stack Docker `prodi-unsrat` di VM sendiri, di-deploy admin UNSRAT dari GitHub (K-P17). Data www diunggah
  superadmin (K-P18); unggahan disimpan di VM (K-P19).

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

Lalu buka http://127.0.0.1:8790/.

Admin (akun per orang, hanya dari jaringan UNSRAT; di komputer pengembang juga dari komputer itu sendiri):

```bash
python3 platform/admin/siapkan.py
.venv/bin/python platform/admin/siapkan.py --superadmin namaanda --nama-lengkap "Nama Anda"
.venv/bin/python platform/admin/app.py
```

Kata sandi sementara ada di `rahasia/.kredensial-namaanda.txt`; buka http://127.0.0.1:8791/, masuk, buat kata sandi
sendiri, lalu hapus berkas itu. Hasilnya di `data/`, `riwayat/`, `publik/`, dan `nginx-buatan/` (tidak masuk Git).

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
| 6 | Admin prodi | selesai, menunggu tinjauan |
| 7 | Docker & deploy staging | — |
| 8 | Uji menyeluruh + log fase | — |
