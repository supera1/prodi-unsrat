# prodi-unsrat — Platform Website Program Studi UNSRAT

Situs ke-97 program studi Universitas Sam Ratulangi di `https://prodi.unsrat.ac.id/<slug>/`, dengan template seragam
yang mengikuti kriteria akreditasi dan bisa disesuaikan oleh tiap prodi.

> **Status 27 Oktober 2026:** Fase 1 selesai dan digabung ke `main` (PR #1): 97 situs prodi, data resmi dari www yang
> diuji sama persis, admin tiga peran, stack Docker untuk VM sendiri ([log](docs/log/fase-01.md), panduan admin VM:
> [docs/deploy.md](docs/deploy.md)). Fase 2 (penyunting halaman wajib dan pilot 3 prodi): rencana menunggu tinjauan,
> [docs/rencana-fase-02.md](docs/rencana-fase-02.md).
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
