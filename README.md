# prodi-unsrat — Platform Website Program Studi UNSRAT

Situs ke-97 program studi Universitas Sam Ratulangi di `https://prodi.unsrat.ac.id/<slug>/`, dengan template seragam
yang mengikuti kriteria akreditasi dan bisa disesuaikan oleh tiap prodi.

> **Status 26 Oktober 2026:** Fase 1 langkah 2 (model data + tarik data www). Belum ada situs yang bisa dijalankan.
> Rencana: [docs/rencana-fase-01.md](docs/rencana-fase-01.md) · Keputusan: [docs/keputusan.md](docs/keputusan.md)

## Cara kerja singkat

- Data resmi prodi (nama, gelar, SKS, CPL, akreditasi) dibaca dari data www.unsrat.ac.id dan tidak diubah di sini.
- Generator membangun halaman statis untuk setiap prodi dari data resmi itu ditambah isi yang diisi prodi.
- Admin (hanya dari jaringan/VPN UNSRAT) punya tiga peran: superadmin, admin prodi, operator.
- Produksi: stack Docker `prodi-unsrat` di VM yang sama dengan www, lewat Portainer.

## Menjalankan uji

```bash
python3 uji/jalankan-semua.py
```

## Menyiapkan data di komputer pengembang

Dengan repo www di folder sebelahnya (`../website-unsrat-2026`):

```bash
python3 platform/tarik_www.py --terapkan
python3 platform/registri.py --siapkan
```

Hasilnya di `data/` dan `riwayat/` (tidak masuk Git).

## Urutan Fase 1

| Langkah | Isi | Status |
|---|---|---|
| 1 | Kerangka repo, dokumen, modul aman dari www, uji slug | selesai |
| 2 | Model data + tarik data www | selesai, menunggu tinjauan |
| 3 | Template induk + generator | — |
| 4 | Akun & peran | — |
| 5 | Superadmin | — |
| 6 | Admin prodi | — |
| 7 | Docker & deploy staging | — |
| 8 | Uji menyeluruh + log fase | — |
