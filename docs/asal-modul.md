# Asal modul yang disalin dari repo www

Modul berikut disalin **apa adanya** dari `website-unsrat-2026` (GitHub `supera1/website-unsrat-2026`), commit
`37b5e6d` (26 Oktober 2026). Modul-modul ini sudah lolos audit keamanan pra-produksi www (21 Oktober 2026).

Bila salah satunya diperbaiki di www (terutama perbaikan keamanan), terapkan perubahan yang sama di sini dan perbarui
tabel ini. Sidik SHA-256 (12 digit pertama) dipakai untuk melihat apakah salinan masih sama dengan asalnya.

| Berkas di repo ini | Asal di www | SHA-256 | Perlu disesuaikan |
|---|---|---|---|
| `platform/admin/gambar_aman.py` | `site/admin/gambar_aman.py` | `03b9479bf413` | — (docstring masih menyebut runtime staging Python 3.7/Pillow 9.5; image ini Python 3.12/Pillow 13, sehingga WebP bisa diizinkan kemudian) |
| `platform/admin/svg_aman.py` | `site/admin/svg_aman.py` | `2ed9e44bcf84` | — |
| `platform/admin/riwayat.py` | `site/admin/riwayat.py` | `b95f8fb1351c` | Langkah 2: jalur data (`MOCK`) diganti ke folder data platform; nama berkas per prodi (`prodi/<kode>/situs`) |
| `platform/pemantau/saringan_spam.py` | `site/pemantau/saringan_spam.py` | `ee6c772608ab` | — |
| `platform/pemantau/cek_integritas.py` | `site/pemantau/cek_integritas.py` | `bc4054cb67d2` | Langkah 7: jalur folder publik dan manifes; daftar host skrip yang diizinkan |
| `platform/template/aset/css/tokens.css` | `site/mockup/assets/css/tokens.css` | `74db4639f6a5` | Langkah 3: warna utama/aksen menjadi variabel per prodi dari palet |
| `platform/admin/requirements.txt`, `constraints.txt` | `site/admin/` | — | Sudah: `imageio-ffmpeg` dibuang (tidak ada video hero) |

Akan dipakai sebagai pola (ditulis ulang, bukan disalin) di langkah berikutnya:
- `site/mockup/_rakit-publik.py` — folder publik dari *allow-list*, manifes SHA-256, mode staging/produksi (langkah 3).
- `site/admin/app.py` — penguncian login, batas sesi, CSRF, pembatasan IP, CSP (langkah 4).
- `site/admin/pratinjau_warna.py` dan `modul_situs/tampilan.py` — uji kontras warna (langkah 3 & 6).
- `site/admin/media.py` dan unggahan GCS di `app.py` — logo ke GCS (langkah 6).
- `docker/`, `docker-compose.yml`, `docs/deploy-portainer.md` — stack terpisah (langkah 7).

Memeriksa apakah salinan masih sama:

```bash
shasum -a 256 platform/admin/gambar_aman.py ../website-unsrat-2026/site/admin/gambar_aman.py
```
