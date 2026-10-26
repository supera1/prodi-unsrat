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
| `platform/pemantau/cek_integritas.py` | `site/pemantau/cek_integritas.py` | `bc4054cb67d2` | — (langkah 7: jalur diberikan lewat `--folder`/`--manifes` di `docker/pemantau.sh`; `HOST_BOLEH` asal www sedikit lebih longgar dari CSP prodi, tetapi CSP halaman tetap memblokir host itu) |
| `platform/template/aset/css/tokens.css` | `site/mockup/assets/css/tokens.css` | `74db4639f6a5` | — (warna per prodi tidak mengubah berkas ini: `prodi.css` memakai variabel `--prodi-*` dari `<slug>/warna.css`) |

## Diadaptasi

Disalin lalu diubah untuk platform ini. SHA-256 di sini adalah sidik **asalnya** saat disalin; uji memberi peringatan
bila asal di www berubah sesudahnya, supaya perbaikan keamanannya bisa diterapkan juga di sini.

| Berkas di repo ini | Asal di www | SHA-256 asal | Perubahan |
|---|---|---|---|
| `platform/riwayat.py` | `site/admin/riwayat.py` | `b95f8fb1351c` | Langkah 2: dipindah dari `platform/admin/`; jalur dan nama berkas yang sah diambil dari `lokasi.py` |
| `platform/admin/requirements.txt`, `constraints.txt` | `site/admin/` | — |
| `docker/nginx/40-prodi-jaringan.sh` | `docker/nginx/40-unsrat-jaringan.sh` | `7a5699c62f22` | Langkah 7: berkas di `/etc/nginx/prodi`. Semua nilai (jaringan dipisah koma, spasi, atau tab; `ADMIN_AWALAN`) diperiksa di skrip utama sebelum ada berkas yang ditulis, bukan di dalam `$(...)`: di asal www, `exit` di dalam subshell tidak menghentikan start, sehingga nilai yang salah diam-diam menutup admin bagi semua orang atau memotong daftar `PROKSI_DEPAN`; `set -f`. Perbaikan yang sama untuk www ada di branch lokal www `fase/praproduksi-cek-jaringan` (`5db66ff`, sidik `bb47958f29d1`), belum digabung |
| `docker/nginx/header-keamanan.conf` | `docker/nginx/header-keamanan.conf` | `8f57181066a5` | Langkah 7: CSP = CSP halaman prodi (`bangun.py`, tanpa `unsafe-inline`, tanpa wasm/YouTube/peta) + `frame-ancestors`; `uji_docker.py` menjaga keduanya sama |
| `docker/nginx/lokasi-situs.conf` | `docker/nginx/situs.conf` | `355c84fde6d3` | Langkah 7: dipecah menjadi `prodi.conf`, `lokasi-situs.conf`, `lokasi-admin.conf`, `tls.conf` (HTTPS di VM); cache setahun hanya untuk alamat ber-`?v=`; `/unggahan/`; `/sehat`; tantangan Let's Encrypt; pengalihan slug lama lewat saringan `50-prodi-pantau.sh` (K-P21) |
| `docker/admin-mulai.sh` | `docker/admin-mulai.sh` | `df974352766b` | Langkah 7: tidak menunggu akun (situs dibangun lebih dulu); data awal VM baru (`impor_www.py --isi-awal`); `waitress-serve --call app:buat_app` |
| `Dockerfile` | `Dockerfile` | `3d7b59ffe27a` | Langkah 7: seluruh uji dijalankan saat build (K-P20); kode hanya-baca bagi pengguna admin; lokasi data lewat `PRODI_*` |
| `docker/web.Dockerfile` | `docker/web.Dockerfile` | `5e1454690184` | Langkah 7: folder volume bersama dimiliki uid 10001 (juga `prodi-nginx`); tzdata; health check `/sehat` + situs sudah dibangun |
| `docker-compose.yml` | `docker-compose.yml` | `6d5e9d6fa2dc` | Langkah 7: tanpa kunci GCS; port HTTPS di VM; `prodi-nginx` hanya-baca di web; pemantau memeriksa ulang temuan sesaat (`docker/pemantau.sh`) |
| `docs/deploy.md` | `docs/deploy-portainer.md` | `6f73433af077` | Langkah 7: untuk VM sendiri (K-P17): data awal, unggah data www, HTTPS di load balancer atau di VM, skrip cadangan/pulihkan | `imageio-ffmpeg` dibuang (tidak ada video hero) |
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

Memeriksa apakah salinan masih sama:

```bash
shasum -a 256 platform/admin/gambar_aman.py ../website-unsrat-2026/site/admin/gambar_aman.py
```
