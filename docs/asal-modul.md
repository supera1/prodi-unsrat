# Asal modul yang disalin dari repo www

Modul berikut disalin dari `website-unsrat-2026` (GitHub `supera1/website-unsrat-2026`), commit
`37b5e6d` (26 Oktober 2026). Modul-modul ini sudah lolos audit keamanan pra-produksi www (21 Oktober 2026).

Bila salah satunya diperbaiki di www (terutama perbaikan keamanan), terapkan perubahan yang sama di sini dan perbarui
tabel ini. Sidik SHA-256 (12 digit pertama) dipakai untuk melihat apakah salinan masih sama dengan asalnya.

## Salinan utuh

Isi berkas sama persis dengan asalnya. `uji/uji_asal_modul.py` gagal bila salinan berubah tanpa tabel ini diperbarui,
dan memberi peringatan bila asalnya di www sudah berubah.

| Berkas di repo ini | Asal di www | SHA-256 | Perlu disesuaikan |
|---|---|---|---|
| `platform/admin/gambar_aman.py` | `site/admin/gambar_aman.py` | `03b9479bf413` | — (docstring masih menyebut runtime staging Python 3.7/Pillow 9.5; image ini Python 3.12/Pillow 13, sehingga WebP bisa diizinkan kemudian) |
| `platform/admin/svg_aman.py` | `site/admin/svg_aman.py` | `2ed9e44bcf84` | — |
| `platform/pemantau/saringan_spam.py` | `site/pemantau/saringan_spam.py` | `ee6c772608ab` | — |
| `platform/pemantau/cek_integritas.py` | `site/pemantau/cek_integritas.py` | `bc4054cb67d2` | Langkah 7: jalur folder publik dan manifes; daftar host skrip yang diizinkan |
| `platform/template/aset/css/tokens.css` | `site/mockup/assets/css/tokens.css` | `74db4639f6a5` | — (warna per prodi tidak mengubah berkas ini: `prodi.css` memakai variabel `--prodi-*` dari `<slug>/warna.css`) |

## Diadaptasi

Disalin lalu diubah untuk platform ini. SHA-256 di sini adalah sidik **asalnya** saat disalin; uji memberi peringatan
bila asal di www berubah sesudahnya, supaya perbaikan keamanannya bisa diterapkan juga di sini.

| Berkas di repo ini | Asal di www | SHA-256 asal | Perubahan |
|---|---|---|---|
| `platform/riwayat.py` | `site/admin/riwayat.py` | `b95f8fb1351c` | Langkah 2: dipindah dari `platform/admin/`; jalur dan nama berkas yang sah diambil dari `lokasi.py` |
| `platform/admin/requirements.txt`, `constraints.txt` | `site/admin/` | — | `imageio-ffmpeg` dibuang (tidak ada video hero) |
| `platform/media.py` | `site/admin/app.py` | `fe0f58774cc8` | Langkah 3b: `periksa_pdf` dan `konten_aktif_pdf` (PDF tanpa konten aktif) diambil; ditambah pemeriksaan teks judi di isi PDF, foto ke JPEG 1600/800/400, penyimpanan lokal/GCS tanpa menimpa |
| `platform/impor_www.py` | `site/admin/impor.py` | `90513c17680b` | Langkah 7: `periksa_xlsx` (ukuran, struktur zip, bom zip, makro), `nilai`, `tabel`/`lembar`, `baca_tanggal`, dan label kolom `KOLOM_PRODI`/`KOLOM_CPL` untuk membaca berkas Excel ekspor program studi dari superadmin www; hasilnya ditulis dalam format `prodi.json` www lalu diperiksa `tarik_www.py` |
| `platform/template/aset/img/lambang-128.png` | `site/mockup/assets/img/lambang-unsrat.png` | `ee6798d239da` | Langkah 3: diperkecil (juga `lambang-64.png` dan `lambang-192.png`) dan dikuantisasi ke 128 warna dengan Pillow (3–13 KB; SVG aslinya 147 KB) |

Akan dipakai sebagai pola (ditulis ulang, bukan disalin) di langkah berikutnya:
- `site/mockup/_rakit-publik.py` — mode staging/produksi, versi aset `?v=`, manifes SHA-256: dipakai di `platform/bangun/bangun.py` (langkah 3).
- `site/admin/app.py` — penguncian login, batas sesi, CSRF, pembatasan IP, CSP, halaman luar jaringan: ditulis ulang
  di `platform/admin/app.py` (langkah 4) untuk akun per orang; `siapkan.py` mengikuti pola berkas kredensial sekali
  pakai dari www.
- `site/admin/pratinjau_warna.py` dan `modul_situs/tampilan.py` — uji kontras warna: rumus WCAG ditulis ulang di `platform/bangun/warna.py` (langkah 3); pratinjau di admin (langkah 6).
- `site/admin/media.py` dan unggahan GCS di `app.py` — logo ke GCS (langkah 6).
- `docker/`, `docker-compose.yml`, `docs/deploy-portainer.md` — stack terpisah (langkah 7).

Memeriksa apakah salinan masih sama:

```bash
shasum -a 256 platform/admin/gambar_aman.py ../website-unsrat-2026/site/admin/gambar_aman.py
```
