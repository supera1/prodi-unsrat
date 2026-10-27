# Audit pra-produksi: bug, tautan rusak, dan keamanan (27 Oktober 2026)

Branch: `fase/praproduksi-keamanan` (bercabang dari `main` `5b897d9`). Permintaan pengguna: pengecekan menyeluruh
sebelum pra-produksi (bug, tautan rusak, terutama keamanan: diserang, deface, pencurian data, disusupi pinjol, diambil
alih), lalu perbaikannya. Keputusan baru: **K-P32 (menunggu tinjauan)**.

Server lokal dimatikan sebelum audit. Tidak ada perintah yang dijalankan ke server staging atau produksi. Satu-satunya
akses keluar adalah permintaan GET biasa ke situs publik yang ditautkan, untuk memeriksa tautan.

## Temuan dan perbaikan

| # | Temuan | Dampak | Perbaikan |
|---|---|---|---|
| 1 | `Dockerfile` menyalin `docs/panduan-admin-prodi.md` (Fase 2 langkah 5), tetapi `.dockerignore` mengecualikan seluruh `docs/` kecuali `asal-modul.md` | **Build image gagal**, sehingga deploy staging berhenti di langkah build | Berkas itu dikecualikan dari pengecualian. Uji baru: setiap `COPY` di kedua Dockerfile harus ada di konteks build |
| 2 | Saringan spam hanya mengenal istilah judi | Promosi pinjol, jual ijazah, atau obat terlarang bisa disimpan lewat admin, dan tidak dilaporkan pemantau | Bahasa jualannya ditolak (K-P32); pesan menyebut jenisnya |
| 3 | `ADMIN_IP_BOLEH` menerima jaringan seluas apa pun, mis. `0.0.0.0/0`, di admin maupun Nginx | Satu salah isi membuka admin ke seluruh internet | Paling luas `/8` (IPv4) atau `/32` (IPv6); start berhenti dengan pesan |
| 4 | `PROKSI_DEPAN` menerima jaringan seluas apa pun | Siapa pun di jaringan itu bisa menyebut alamat kampus di `X-Forwarded-For` dan lolos `ADMIN_IP_BOLEH` (pengambilalihan bila sandi juga bocor) | Paling luas `/16` atau `/48` |
| 5 | Mode produksi bisa berjalan dengan admin lewat HTTP | Kata sandi dan kuki sesi lewat jaringan tanpa enkripsi, misalnya Wi-Fi kampus | `PRODI_MODE=produksi` tanpa `ADMIN_HTTPS=1` membuat admin berhenti. Pengaturan diperiksa sebelum situs dibangun |
| 6 | Isi bertanda `[CONTOH]` (`isi_halaman.py contoh`, pengumuman contoh) ikut terbit di mode produksi | VM staging menjadi VM produksi (deploy §11): isi rekaan tayang di situs resmi. Terbukti di data lokal: 15 berkas rakitan produksi memuat `[CONTOH]` | Rakitan produksi melewatinya dengan `PERINGATAN`; staging tetap menampilkannya |
| 7 | Kontainer tanpa `no-new-privileges` dan tanpa `cap_drop` | Pertahanan berlapis bila ada celah di proses kontainer | `no-new-privileges` di ketiganya; admin dan pemantau (pengguna 10001) `cap_drop: ALL` |
| 8 | Dua tautan di halaman Kalender ke-97 prodi menjawab 404: `www.unsrat.ac.id/kalender-akademik.html` dan `/pengumuman.html` | Pengunjung mendapat halaman rusak | Alamat www dipetakan ke alamat yang tayang sekarang: `/kalender-akademik/` dan `/category/pengumuman/` (keduanya 200, isinya diperiksa) |
| 9 | Admin hanya memisah `ADMIN_IP_BOLEH` dengan koma, padahal Nginx juga menerima spasi dan tab | Nilai yang dipisah spasi diterima Nginx, tetapi admin berhenti dengan galat | Admin memisah dengan koma, spasi, atau tab, seperti Nginx |
| 10 | `fisip.unsrat.ac.id` menjawab 500 (ditautkan dari situs prodi FISIP) | Tautan fakultas rusak | Di luar repositori ini: laporkan ke pengelola situs FISIP |

### Rincian perbaikan
- **Saringan spam** (`platform/pemantau/saringan_spam.py`, kini "Diadaptasi" di `docs/asal-modul.md`):
  - `ISTILAH_PINJOL` (18 frasa, mis. "dana cepat cair", "pinjol tanpa KTP", "tanpa BI checking", "cair dalam 5
    menit") dan `ISTILAH_LAIN` (17 frasa, mis. "jual ijazah asli", "jasa pembuatan ijazah asli", "jual obat aborsi",
    "jual viagra");
  - normalisasi yang sama dengan istilah judi berlaku: huruf besar, angka sebagai huruf (`p1nj0l`), karakter tak
    terlihat, huruf lebar;
  - hanya frasa jualan, bukan kata topiknya. Daftar ini diuji pada 4.328 berkas teks (data dan situs repo ini, situs
    dan dokumen www) tanpa satu pun temuan;
  - `jenis(istilah)` memberi "judi", "pinjol", atau "terlarang". Pesan di isi halaman, catatan pengembalian, masukan,
    dan data www kini berbunyi mis. "memuat teks pinjol (dana cepat cair)".
- **Jaringan** (`platform/admin/app.py` `baca_jaringan`, `docker/nginx/40-prodi-jaringan.sh` `periksa`):
  - awalan `/` yang kosong, ganda, lebih dari 3 angka, atau di luar 0–32/0–128 juga ditolak sebagai "bukan alamat
    jaringan";
  - di admin, kesalahan pengaturan kini berhenti dengan pesan (`SystemExit`), bukan traceback.
- **Start admin** (`docker/admin-mulai.sh`): `app.buat_app()` dicoba dengan `PRODI_BANGUN=mati` sesudah kunci sesi
  dibuat dan sebelum situs dibangun. Pengaturan yang ditolak menghentikan start dengan pesan, situs tetap menyajikan
  hasil bangun terakhir, dan restart tidak membangun ulang 97 situs hanya untuk berhenti lagi. `PRODI_MODE` kini juga
  dibaca admin dari lingkungan stack.
- **Isi contoh** (`isi_halaman.bertanda_contoh`, `bangun.py`): halaman dan pengumuman yang memuat `[CONTOH]` dilewati
  di produksi. Log admin menulis `PERINGATAN prodi …: … bertanda [CONTOH], tidak diterbitkan di produksi`.
- **Kontainer** (`docker-compose.yml`): `docker compose config -q` lulus. Kontainer web belum diberi `cap_drop`:
  Nginx mulai sebagai root dan butuh beberapa kapabilitas (CHOWN, SETUID, SETGID, NET_BIND_SERVICE). Ini perlu dicoba
  dengan Docker lebih dulu, karena kalau salah, situs tidak mau start.
- **Tautan www** (`bangun.WWW_SEKARANG`, `bangun.alamat_www`): dipakai sumber halaman Kalender dan tautan relatif dalam
  teks dari data www. Saat www baru (website-unsrat-2026) tayang, tabel itu dikosongkan. www baru belum mengalihkan
  alamat WordPress lama, jadi disarankan ke tim www untuk menambah pengalihannya.
- **Dokumen**:
  - `docs/deploy.md`: batas jaringan, HTTPS wajib di produksi (§7A, §11), isi contoh, dan tiga baris baru di tabel
    masalah (§12);
  - `docs/panduan-admin-prodi.md`: teks yang ditolak;
  - `docs/asal-modul.md`, `CLAUDE.md`, K-P32.

## Yang diperiksa dan lulus
- **Halaman.**
  - 3.698 halaman (97 prodi + akar) lolos pemeriksa bersama `uji/pemeriksa_halaman.py`: tautan dan anker internal,
    CSP, tanpa skrip/gaya sebaris, `alt` gambar, dan urutan heading.
  - Rakitan produksi dari data lokal ke folder sementara:
    - `robots.txt` mengizinkan mesin pencari, dan `sitemap.xml` ada;
    - hanya ada berkas `.html/.xml/.txt/.css/.jpg/.png/.pdf`, tanpa berkas tersembunyi, `.py`, `.md`, `.env`, atau
      basis data;
    - tidak ada jalur komputer pengembang, `127.0.0.1`/`localhost`, `noindex`, pita staging, atau traceback;
    - sesudah perbaikan #6: 0 halaman `[CONTOH]`, cek integritas 3.893 berkas dengan 0 temuan.
- **Tautan luar.** 112 alamat unik (selain Google Fonts), masing-masing diminta sekali dengan curl:
  - 109 menjawab 200, termasuk 95 daftar dosen di dosen.unsrat.ac.id, yang semuanya berisi dosen;
  - 2 menjawab 404 (#8) dan 1 menjawab 500 (#10).
- **Admin.**
  - **Akses:** setiap rute wajib `@akses` (start gagal bila tidak), dengan matriks 87 rute × 6 akun.
  - **CSRF:** diperiksa dengan `hmac.compare_digest` di setiap POST.
  - **Keluaran:** Jinja2 autoescape tanpa `|safe` di templat. `Markup` hanya dipakai pengurai yang meng-escape lebih
    dulu (teks kaya, tautan www, panduan, formulir penyunting), dan untuk JSON-LD yang tidak bisa menutup `<script>`.
  - **SQL:** SQLite selalu berparameter.
  - **Masuk:**
    - sesi baru setiap login, dan waktu jawab yang sama untuk nama yang tidak ada;
    - kunci 15 menit setelah 5 gagal per alamat atau 10 gagal per nama;
    - pesan galat umum.
  - **Kuki dan header:**
    - kuki `HttpOnly` dan `SameSite=Strict`, ditambah `Secure` dan `__Host-` saat HTTPS;
    - header CSP, `frame-ancestors 'none'`, `nosniff`, `no-store`, dan HSTS saat HTTPS.
  - **Lain-lain:** debugger tidak pernah aktif, dan header Host tidak dipakai untuk membentuk alamat.
- **Pustaka** dikunci di `constraints.txt`, antara lain Flask 3.1.3, Werkzeug 3.1.9, Jinja2 3.1.6, pillow 13.0.0,
  pypdf 6.21.1, waitress 3.0.2, dan cryptography 50.0.2. Repo ini belum punya pemindai kerentanan otomatis (lihat
  "Perlu diketahui").
- **Nginx.**
  - `server_tokens off`, dan situs hanya menerima GET/HEAD.
  - Berkas tersembunyi ditolak, dan header keamanan ada di setiap `location`.
  - `X-Forwarded-For` ditimpa, tidak diteruskan dari pengunjung.
  - Admin hanya untuk `ADMIN_IP_BOLEH`, dan TLS memakai profil intermediate.
- **Docker.**
  - Admin dan pemantau berjalan sebagai pengguna 10001, dengan kode hanya-baca.
  - Volume web dan pemantau hanya-baca; volume rahasia hanya di admin.
  - Admin tidak dibuka ke luar.
  - Seluruh uji berjalan saat build.
- **Pemantau** (`cek_integritas.py`, salinan utuh dari www) mendeteksi `BERUBAH`, `ASING`, `HILANG`, `SPAM` (kini
  juga pinjol, ijazah, dan obat), dan `SKRIP`.

## Verifikasi
```bash
.venv/bin/python uji/jalankan-semua.py
```
- **Semua uji:** 19 rangkaian, 0 gagal, termasuk rangkaian baru `uji/uji_saringan_spam.py`. Isinya:
  - 91 istilah ditemukan apa adanya, dalam huruf besar, dan di tengah kalimat, dengan jenisnya;
  - 18 contoh spam tertangkap, sebagian disamarkan;
  - 12 kalimat penelitian dan peringatan lolos;
  - pesan isi halaman, masukan, data prodi, dan cek integritas menyebut jenisnya.
- **Tiruan image:** salinan yang hanya berisi berkas yang di-`COPY` Dockerfile, mengikuti `.dockerignore`, memberi 19
  rangkaian, 0 gagal. `uji_docker.py` menangkap bug #1 pada `.dockerignore` versi `main`.
- **Uji mutasi:** setiap aturan baru dimatikan sementara, dan setiap kali ada uji yang gagal.

| Aturan yang dimatikan | Uji yang gagal |
|---|---|
| Frasa pinjol dicari | 81 |
| Frasa ijazah/obat dicari | 59 |
| `jenis()` membedakan judi/pinjol/terlarang | 126 |
| Pesan isi halaman / masukan / data www menyebut jenis | 2 / 1 / 2 |
| Admin menolak jaringan terlalu luas | 11 |
| Admin memisah dengan spasi dan tab | 1 (rangkaian berhenti) |
| Admin produksi wajib HTTPS | 7 |
| Admin membaca `PRODI_MODE` dari lingkungan | 3 |
| Nginx menolak jaringan terlalu luas | 54 |
| `PROKSI_DEPAN` lebih sempit dari `ADMIN_IP_BOLEH` | 18 |
| Nginx menolak `/` kosong, ganda, atau di depan | 8 |
| Nginx menolak awalan lebih dari 3 angka | 4 |
| Start admin memeriksa pengaturan | 1 |
| ... sebelum situs dibangun | 8 |
| ... dan berhenti bila gagal | 5 |
| Web `no-new-privileges` / pemantau `cap_drop` | 1 / 1 |
| Panduan masuk konteks build | 1 |
| Halaman / pengumuman contoh tidak terbit di produksi | 1 / 1 |
| `[CONTOH]` dikenali | 2 |
| Pemetaan alamat www / sumber Kalender / tautan dalam teks | 3 / 1 / 1 |

## Perlu diketahui
- **Build image Docker sungguhan belum dijalankan** untuk Fase 2 maupun audit ini, karena Docker lokal mati. Bug #1
  menunjukkan risikonya. Saat admin VM membangun staging, seluruh uji berjalan lagi di image (K-P20). Pantau log build
  pertama.
- **Staging juga sebaiknya HTTPS** (`ADMIN_HTTPS=1`), karena akun pilot adalah akun orang sungguhan. Yang diwajibkan
  hanya produksi.
- **Admin VM perlu menyiapkan HTTPS untuk admin sebelum §11.** `PROKSI_DEPAN` harus berisi subnet proksi yang
  sebenarnya: rentang load balancer Google dalam `docs/deploy.md` masih diterima.
- **Istilah judi tetap ditolak seluruhnya** (kebijakan www). Judul pengabdian seperti "edukasi bahaya judi online"
  juga ditolak. Bila pilot memerlukannya, perlu keputusan terpisah.
- **Untuk www:** saringan baru dan pemeriksaan jaringan yang terlalu luas sebaiknya juga diterapkan di www (domain
  `.ac.id` yang sama). www juga sebaiknya mengalihkan alamat WordPress lama setelah www baru tayang. Repo ini tidak
  menulis ke www.
- **Belum ditambahkan:**
  - pembatasan laju Nginx (`limit_req`) untuk `/masuk`, karena admin sudah mengunci per alamat dan per nama, dan hanya
    terbuka untuk jaringan UNSRAT;
  - pemindai kerentanan pustaka (`pip-audit`), karena itu paket baru yang perlu persetujuan. Disarankan dijalankan
    berkala, mis. setiap pembaruan `constraints.txt`.
- **Isi contoh di komputer pengembang** (4 pengumuman `[CONTOH]` S1 Teknik Informatika) hanya ada di data lokal dan
  tidak ikut repositori maupun VM.
