# Fase 1 · Langkah 1 — Kerangka repo (26 Oktober 2026)

Branch: `fase/01-1-kerangka` (lokal, belum di-push; remote GitHub belum dibuat).

## Yang dikerjakan
- Repo `prodi-unsrat` dibuat di samping `website-unsrat-2026`, dengan struktur `platform/`, `uji/`, `docs/`, `docker/`.
- `CLAUDE.md`, `README.md`, `docs/keputusan.md` (K-P1 … K-P13), `.gitignore`, `.gitattributes`.
- `docs/rencana-fase-01.md` diperbarui sesuai jawaban 26 Oktober: tanpa 2FA (sandi kuat), logo di GCS, tanpa SMTP,
  port menyusul.
- Daftar slug yang disetujui dipindah ke `platform/data-awal/slug.csv`.
- Modul aman disalin dari www commit `37b5e6d` dan dicatat di `docs/asal-modul.md`: `gambar_aman.py`, `svg_aman.py`,
  `riwayat.py`, `saringan_spam.py`, `cek_integritas.py`, `tokens.css`, `requirements.txt`/`constraints.txt`
  (tanpa `imageio-ffmpeg`).
- `platform/slug.py`: aturan slug (pola, awalan jenjang, alamat cadangan) dan pemeriksaan daftar — dipakai lagi oleh
  superadmin di langkah 5.
- Uji: `uji/uji_slug.py`, `uji/uji_asal_modul.py`, `uji/jalankan-semua.py`.

## Verifikasi
```bash
python3 uji/jalankan-semua.py
```
Hasil: 2 rangkaian, 0 gagal. `uji_slug` membandingkan 97 prodi dengan data www (kode PDDIKTI, nama, jenjang sama).
Uji ini cukup dengan pustaka standar Python; paket admin (Flask dll.) baru dibutuhkan mulai langkah 2/4.

## Catatan
- `uji_asal_modul` sempat menemukan dua sidik SHA-256 yang tertukar di tabel; sudah dibetulkan. Uji ini akan
  memperingatkan bila modul asal di www berubah sehingga perbaikan keamanan tidak tertinggal.

## Perlu dikonfirmasi manusia
- Siapa yang membuat repo GitHub `prodi-unsrat` (di akun `supera1`?) dan kapan di-push.

## Langkah berikutnya
Langkah 2 — model data + tarik data www (`tarik_www.py`, registri dari `slug.csv`, riwayat versi).
