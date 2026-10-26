# prodi-unsrat — Platform Website Program Studi UNSRAT

Situs ke-97 program studi Universitas Sam Ratulangi di `https://prodi.unsrat.ac.id/<slug>/`, dengan template seragam
yang mengikuti kriteria akreditasi dan bisa disesuaikan oleh tiap prodi.

> **Status 26 Oktober 2026:** Fase 1 langkah 3c (bagian depan beranda per prodi): 97 situs prodi lengkap dengan pengumuman dan bagian depan
> yang bisa disesuaikan, bisa dibangun dan dilihat di komputer pengembang.
> Rencana: [docs/rencana-fase-01.md](docs/rencana-fase-01.md) · Keputusan: [docs/keputusan.md](docs/keputusan.md)

## Cara kerja singkat

- Data resmi prodi (nama, gelar, SKS, CPL, akreditasi) dibaca dari data www.unsrat.ac.id dan tidak diubah di sini.
- Generator membangun halaman statis untuk setiap prodi dari data resmi itu ditambah isi yang diisi prodi.
- Admin (hanya dari jaringan/VPN UNSRAT) punya tiga peran: superadmin, admin prodi, operator.
- Produksi: stack Docker `prodi-unsrat` di VM yang sama dengan www, lewat Portainer.

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

Lalu buka http://127.0.0.1:8790/. Hasilnya di `data/`, `riwayat/`, `publik/`, dan `nginx-buatan/` (tidak masuk Git).

## Urutan Fase 1

| Langkah | Isi | Status |
|---|---|---|
| 1 | Kerangka repo, dokumen, modul aman dari www, uji slug | selesai |
| 2 | Model data + tarik data www | selesai |
| 3 | Template induk + generator | selesai |
| 3b | Pengumuman dan berita | selesai |
| 3c | Bagian depan beranda per prodi | selesai, menunggu tinjauan |
| 4 | Akun & peran | — |
| 5 | Superadmin | — |
| 6 | Admin prodi | — |
| 7 | Docker & deploy staging | — |
| 8 | Uji menyeluruh + log fase | — |
