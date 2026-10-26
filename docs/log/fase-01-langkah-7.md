# Fase 1 · Langkah 7 — Docker dan deploy di VM sendiri (26 Oktober 2026)

Branch: `fase/01-7-docker` (bercabang dari `fase/01-6b-vm-sendiri`).

## Yang dikerjakan
- **Unggah data www oleh superadmin** (K-P18, `platform/impor_www.py`, halaman **Data www**):
  - berkas **Excel ekspor program studi** dari superadmin www (lembar "Program studi" dan "CPL") dibaca seperti impor
    www sendiri (judul kolom www, tanggal, angka, pemeriksaan berkas `.xlsx`: ukuran, bom zip, makro), dan/atau berkas
    **JSON** www (`prodi.json`, `unit.json`, `kalender.json`, `situs.json`), dikenali dari isinya apa pun namanya;
  - unggahan dijadikan folder berformat www lalu dipratinjau dan diterapkan `tarik_www.py` seperti sebelumnya, dengan
    semua pemeriksaannya (termasuk saringan judi dan batas prodi yang hilang sekaligus). Yang tidak diunggah memakai
    salinan sekarang; kolom yang tidak ada di Excel dan lembar CPL yang tidak ada tidak mengubah apa pun;
  - unggahan hanya bisa diterapkan pengunggahnya, sekali, dalam 30 menit, dan **tidak** bila data resmi di platform
    berubah sesudah unggahan dibuat (berkas yang diambil dari salinan lama tidak boleh menimpa perubahan itu);
  - platform tanpa registri: registri 97 prodi dibuat dari `slug.csv` begitu data resmi diterapkan;
  - dasbor superadmin menampilkan sumber dan umur data www, dan mengingatkan bila lebih dari 30 hari.
- **Data awal VM baru** (K-P22): `platform/data-awal/www/` = salinan data www (commit www `37b5e6d`, format www).
  Kontainer admin menjalankan `impor_www.py --isi-awal` di setiap start; hanya berlaku sekali pada VM kosong.
- **Bangun ulang harian** (`PRODI_BANGUN_HARIAN`, bawaan 02:30 WITA) lewat antrean bangun admin; tampil di halaman
  Bangun ulang.
- **Stack Docker** (`Dockerfile`, `docker/web.Dockerfile`, `docker-compose.yml`, `docker/`):
  - `admin`: Python 3.12, pengguna 10001, kode hanya-baca, semua data di volume; waitress; **seluruh uji dijalankan
    saat image dibangun** (K-P20);
  - `web`: Nginx; situs dan admin (hanya `ADMIN_IP_BOLEH`, `PROKSI_DEPAN` untuk load balancer, `ADMIN_AWALAN`);
    header keamanan = CSP halaman + `frame-ancestors`; cache setahun hanya untuk aset ber-`?v=`; `/sehat`;
  - pengalihan slug lama: kontainer web hanya menyalin baris `rewrite` yang sah dari generator, memeriksa `nginx -t`,
    lalu memuat ulang sendiri (K-P21);
  - **HTTPS**: bawaan di load balancer; atau di VM (`HTTPS_DI_VM=1`): 443 situs, 8443 admin, 80/8081 hanya
    mengalihkan, tantangan Let's Encrypt, sertifikat yang diperpanjang dimuat ulang sendiri;
  - `pemantau`: cek integritas setiap 10 menit; temuan diperiksa ulang semenit kemudian supaya saat bangun ulang tidak
    dilaporkan.
- **Cadangan harian dan pemulihan**: `docker/cadangan-prodi.sh` (cron di VM; admin dihentikan beberapa detik supaya
  basis data akun tersalin utuh, menyala lagi sendiri juga bila gagal) dan `docker/pulihkan-prodi.sh`.
- **Panduan admin VM**: `docs/deploy.md` (Portainer atau `docker compose`, variabel, akun pertama, data www, HTTPS dua
  cara, pembaruan, cadangan/pemulihan, pemantauan, penanganan temuan, masalah umum).
- Keputusan baru K-P20–K-P22; K-P13 berisi bawaan port. Asal berkas yang diadaptasi dari www dicatat di
  `docs/asal-modul.md`.

## Verifikasi
```bash
.venv/bin/python uji/jalankan-semua.py
```
Hasil: 12 rangkaian, 0 gagal. Di dalam image (`docker compose build`): 12 rangkaian lulus saat build.
- `uji/uji_impor_www.py`: ekspor Excel tanpa perubahan terbaca tanpa selisih (juga dengan baris judul di atasnya, kode
  dan SKS berupa angka); sel berubah, prodi baru (kode unit huruf besar), prodi yang tidak ada di berkas, kolom dan lembar
  yang tidak ada; 9 macam baris salah dilaporkan sekaligus dengan nomor barisnya; 20 macam berkas salah ditolak (xls,
  xlsm, zip rusak, bom zip, makro, >5 MB, JSON rusak/bersarang dalam, dua sumber data yang sama, dll.) tanpa
  meninggalkan folder; teks judi ditolak; halaman admin: pratinjau, hanya pengunggah, pratinjau usang, sekali pakai,
  30 menit, token aneh, unggahan usang tidak menimpa perubahan sesudahnya, dasbor; platform kosong: data awal +
  registri 97 prodi, atau unggahan pertama.
- **Ekspor Excel asli** dibuat dengan kode www sendiri dari data www: 97 prodi dan seluruh CPL terbaca **tanpa satu pun
  selisih** dari `prodi.json` www (berjalan di komputer pengembang, saat repo www ada di sebelahnya).
- `uji/uji_docker.py`: CSP Nginx sama dengan CSP halaman; saringan pengalihan slug meloloskan baris generator saja
  (11 baris jahat ditolak, diperiksa dengan `re` Python dan `grep -E`); admin dan pemantau tidak dibuka ke luar,
  volume rahasia hanya di admin, web dan pemantau hanya-baca; `.dockerignore`; 15 variabel stack ada di `.env.example`
  dan panduan; sintaks skrip.
- Matriks akses: 65 rute × 6 akun (rute unggah baru). Uji mutasi: mematikan pemeriksaan pemilik unggahan → 4 uji
  gagal; mematikan pemeriksaan "data berubah sejak diunggah" → 1 uji gagal.
- Uji data asli (`uji_bangun`, `uji_data`, `uji_beranda`, `uji_slug`) memakai salinan `data-awal/www/` bila repo www
  tidak ada, sehingga juga berjalan di dalam image.

**Stack dicoba utuh dengan Docker lokal** (Colima, Docker 29.5.2, 2 CPU) seperti `docs/deploy.md` §13:
- start pertama: data awal + registri 97 prodi, 3.688 halaman dibangun, `web` dan `admin` *healthy*; restart admin
  idempoten (0 berkas berubah, sesi tetap berlaku);
- situs: header keamanan, `no-cache` untuk halaman, setahun untuk aset ber-`?v=`, 403 untuk dotfile dan POST, halaman
  404 milik platform, pengalihan folder relatif, pita staging dan `noindex`;
- admin lewat Nginx: masuk, wajib ganti sandi (sandi yang memuat nama lengkap ditolak), dasbor dengan sumber data;
  unggah ekspor Excel www yang diubah satu kolom → pratinjau 1 perubahan → terapkan → bangun ulang → situs berubah;
  unggahan > 40 MB ditolak Nginx (413);
- ganti slug: pengalihan 301 aktif sendiri ±25 detik kemudian;
- di belakang load balancer (`PROKSI_DEPAN`): langsung 403, alamat luar 403, alamat UNSRAT 200, alamat UNSRAT palsu di
  depan `X-Forwarded-For` tetap 403; log Nginx mencatat alamat asli dengan waktu WITA;
- pemantau: halaman diberi teks judi dan berkas `.php` ditanam → 3 temuan, `PEMANTAU: ADA TEMUAN` setelah diperiksa
  ulang; volumenya hanya-baca; bangun ulang memulihkan (0 temuan);
- HTTPS di VM (sertifikat uji): pengalihan ke https, HTTP/2, TLS 1.1 ditolak, TLS 1.2 diterima, pengalihan slug lewat
  https, sertifikat yang diganti dipakai ±5 detik kemudian; tanpa sertifikat kontainer web berhenti dengan pesan jelas;
- cadangan (dijalankan di VM Linux Colima): dua arsip hanya-root, kepemilikan berkas terjaga, admin menyala lagi juga
  saat penyalinan gagal; pemulihan setelah registri, salinan www, dan basis data akun dihapus → semua kembali, situs
  200, sesi admin tetap berlaku.

Halaman Data www (pratinjau unggahan dan formulir unggah) dan dasbor juga diperiksa tampilannya di browser.

## Ditemukan dan diperbaiki selama langkah ini
- Parameter keterangan sumber di `tarik_www.baca_sumber` tertimpa variabel perulangan bernama sama (ditangkap uji).
- Volume bersama bisa diisi pertama kali oleh image web dengan pemilik root, sehingga admin tidak bisa menulis
  (bergantung urutan kontainer dibuat). Folder itu kini dimiliki uid 10001 di kedua image.
- Pemeriksaan `ADMIN_IP_BOLEH`/`PROKSI_DEPAN` di skrip awal web: `exit` di dalam `$(...)` hanya keluar dari subshell,
  sehingga nilai yang salah tidak menghentikan start (admin diam-diam tertutup untuk semua orang, atau daftar proksi
  terpotong). Diperbaiki di sini. **Skrip asal di www (`docker/nginx/40-unsrat-jaringan.sh`) punya cacat yang sama.**
- Skrip cadangan gagal mengatur izin berkas bila cron tidak berjalan sebagai root; izin kini diatur di dalam kontainer.

## Perlu diketahui / perlu dikonfirmasi
- **K-P20:** uji dijalankan di setiap build image (deploy ±1–3 menit lebih lama; build gagal bila uji gagal). Mohon
  dikonfirmasi.
- **Port (K-P13):** bawaan 8080 (situs) dan 8081 (admin); nilai akhir disepakati dengan admin VM.
- Data awal adalah salinan data www per commit `37b5e6d`; sesudah deploy, superadmin sebaiknya langsung mengunggah
  ekspor Excel terbaru dari www.
- `unit.json`, `kalender.json`, `situs.json` www tidak diterbitkan www; admin VM www yang mengambilkannya
  (`docker cp`, perintahnya di `docs/deploy.md` §6). Ketiganya jarang berubah.
- Belum dicoba: alur Portainer itu sendiri (yang dicoba `docker compose`, perintah yang sama dijalankan Portainer) dan
  Let's Encrypt sungguhan (perlu DNS dan VM publik; alurnya didokumentasikan).

## Langkah berikutnya
Langkah 8 — uji menyeluruh dan `docs/log/fase-01.md` (cara verifikasi manual, sisa pekerjaan, keputusan yang perlu
dikonfirmasi).
