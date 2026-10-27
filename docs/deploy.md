# Deploy prodi.unsrat.ac.id di VM sendiri

Panduan untuk admin VM UNSRAT yang memasang platform situs program studi dari GitHub (`supera1/prodi-unsrat`) di VM
UNSRAT tersendiri dengan `docker compose` (K-P17; tanpa Portainer). Pengembang tidak menjalankan apa pun di server;
semua langkah di bawah dikerjakan admin VM, dari folder repositori di VM (di panduan ini `/opt/prodi-unsrat`).

## 1. Gambaran

Stack Docker `prodi-unsrat` berisi tiga kontainer:

| Kontainer | Isi | Dibuka ke luar? |
|---|---|---|
| `web` | Nginx: situs ke-97 prodi (port `PORT_SITUS`) dan admin (port `PORT_ADMIN`, hanya jaringan UNSRAT/VPN) | ya |
| `admin` | Flask + generator situs. Membangun semua situs ke volume `prodi-publik` saat mulai, setelah setiap perubahan, dan setiap hari pukul 02.30 | tidak |
| `pemantau` | Cek integritas situs publik setiap 10 menit (halaman diubah, berkas tanaman, teks judi atau pinjol) | tidak |

Nama stack tetap `prodi-unsrat` (ditulis di `docker-compose.yml`), jadi kontainernya `prodi-unsrat-admin-1`,
`prodi-unsrat-web-1`, `prodi-unsrat-pemantau-1`, dan volumenya diawali `prodi-unsrat_` (mis. `prodi-unsrat_prodi-data`):

| Volume | Isi | Dicadangkan? |
|---|---|---|
| `prodi-data` | data prodi, riwayat versi, log audit, unggahan foto/logo/PDF | **ya, setiap hari** |
| `prodi-rahasia` | akun (hash kata sandi) dan kunci sesi | **ya, setiap hari**, simpan terbatas |
| `prodi-publik` | situs hasil bangun | tidak (dibangun ulang saat admin mulai) |
| `prodi-nginx` | pengalihan slug lama buatan generator | tidak |
| `prodi-tls`, `prodi-acme` | hanya untuk HTTPS di VM (§7B) | tidak |

Kebutuhan: VM Linux dengan Docker Engine, plugin compose (`docker compose`, versi 2), dan `git`. Platform ini kecil:
admin ±40 MB RAM saat diam, situs ±60 MB, image 320 MB + 100 MB. 2 vCPU, 2–4 GB RAM, dan 20 GB disk sudah cukup;
unggahan prodi (foto, PDF) menambah isi `prodi-data` dari waktu ke waktu.

## 2. Yang disiapkan

1. **VM** UNSRAT dengan Docker Engine, plugin compose, dan `git`. Zona waktu kontainer sudah Asia/Makassar.
2. **Firewall:**
   - `PORT_SITUS` (situs) hanya dari load balancer, atau dari internet bila HTTPS dipasang di VM (§7B, port 80 dan 443);
   - `PORT_ADMIN` (admin) hanya dari jaringan UNSRAT/VPN dan dari load balancer. Admin juga menolak sendiri alamat di
     luar `ADMIN_IP_BOLEH`.
3. **Akses GitHub** bila repositori privat, salah satu (keduanya hanya-baca, jangan beri hak tulis):
   - **kunci deploy** (disarankan untuk VM): buat kunci SSH di VM, kirim kunci publiknya ke pemilik repositori untuk
     ditambahkan di GitHub (repositori → Settings → Deploy keys, tanpa *Allow write access*):

     ```bash
     sudo ssh-keygen -t ed25519 -N "" -C "deploy prodi-unsrat" -f /root/.ssh/prodi-unsrat
     sudo cat /root/.ssh/prodi-unsrat.pub
     ```

     Perintah `git clone` dengan kunci ini ada di §3;
   - *fine-grained token* untuk repositori ini dengan izin **Contents: Read-only**, diketik saat `git` memintanya.
4. **Port** disepakati dengan pengembang (K-P13). Bawaan: situs `8080`, admin `8081`.

## 3. Ambil kode dan nyalakan

```bash
sudo git clone --branch main https://github.com/supera1/prodi-unsrat /opt/prodi-unsrat   # branch yang disepakati
cd /opt/prodi-unsrat
sudo cp .env.example .env          # isi nilai yang berbeda dari bawaan (§4); untuk uji pertama cukup port dan ADMIN_IP_BOLEH
sudo docker compose up -d --build
sudo docker compose ps             # web dan admin harus "healthy" (±1–5 menit setelah start)
```

Repositori privat dengan kunci deploy (§2): ganti baris `git clone` di atas dengan

```bash
sudo GIT_SSH_COMMAND="ssh -i /root/.ssh/prodi-unsrat -o IdentitiesOnly=yes" \
     git clone --branch main git@github.com:supera1/prodi-unsrat.git /opt/prodi-unsrat
sudo git -C /opt/prodi-unsrat config core.sshCommand "ssh -i /root/.ssh/prodi-unsrat -o IdentitiesOnly=yes"
```

(baris terakhir supaya `git pull` berikutnya juga memakai kunci itu).

Variabel stack disimpan di `/opt/prodi-unsrat/.env` (tidak ikut `git pull`, tidak memuat rahasia). Log:
`sudo docker compose logs -f admin` (atau `web`, `pemantau`).

Build pertama memakan beberapa menit: mengunduh image Python dan Nginx, memasang pustaka, lalu **menjalankan seluruh
uji otomatis di dalam image** (±1–3 menit). Bila satu uji saja gagal, build berhenti dan stack lama (bila ada) tetap
berjalan; kirim log build ke pengembang.

## 4. Variabel stack

Diisi di `/opt/prodi-unsrat/.env` (salinan `.env.example`). Semua boleh dikosongkan; yang kosong memakai bawaan.
Perubahan berlaku setelah `sudo docker compose up -d`.

| Variabel | Bawaan | Arti |
|---|---|---|
| `PRODI_MODE` | `staging` | `staging`: pita "Pratinjau staging" dan `noindex` di setiap halaman. `produksi`: tanpa itu, dengan `sitemap.xml` dan alamat kanonik (§11) |
| `PRODI_ALAMAT` | `https://prodi.unsrat.ac.id` | Alamat resmi situs: untuk alamat kanonik, sitemap, RSS, dan tautan "Lihat situs" di admin |
| `ADMIN_IP_BOLEH` | `103.84.116.0/24` | Jaringan yang boleh membuka admin, dipisah koma (mis. jaringan kampus dan VPN). Paling luas `/8` (IPv4) atau `/32` (IPv6); yang lebih luas, mis. `0.0.0.0/0`, ditolak |
| `PORT_SITUS` | `8080` | Port situs (HTTP) di VM |
| `PORT_ADMIN` | `8081` | Port admin (HTTP) di VM |
| `PROKSI_DEPAN` | kosong | Jaringan load balancer/reverse proxy di depan stack, dipisah koma; tanpanya admin melihat alamat proksi dan menolak semua orang (§7A). Paling luas `/16` (IPv4) atau `/48` (IPv6): setiap alamat di dalamnya dipercaya menyebut alamat pengunjung (`X-Forwarded-For`) |
| `ADMIN_HTTPS` | `0` | `1` bila admin dibuka lewat HTTPS (cookie aman + HSTS). Wajib `1` untuk §7B dan untuk `PRODI_MODE=produksi`: tanpa itu admin tidak mau berjalan (§11) |
| `ADMIN_AWALAN` | kosong | Jalur admin bila admin dibuka di bawah alamat bersama, mis. `/admin` untuk `https://prodi.unsrat.ac.id/admin` (awalan dibuang di load balancer) |
| `PRODI_BANGUN_HARIAN` | `02:30` | Jam bangun ulang harian (JJ:MM, WITA), supaya pengumuman yang lewat masa berlakunya turun dari situs |
| `HTTPS_DI_VM` | `0` | `1`: TLS dipasang di VM ini sendiri (§7B) |
| `TLS_FOLDER` | volume `prodi-tls` | Folder di VM berisi `fullchain.pem` dan `privkey.pem` (§7B) |
| `ACME_FOLDER` | volume `prodi-acme` | Folder di VM untuk tantangan Let's Encrypt (`certbot --webroot`, §7B) |
| `PORT_SITUS_HTTPS` | `8443` | Port situs HTTPS di VM (§7B: biasanya `443`). Tanpa `HTTPS_DI_VM=1` tidak ada yang mendengarkan di sana |
| `PORT_ADMIN_HTTPS` | `8444` | Port admin HTTPS di VM (§7B) |
| `UJI_SAAT_BUILD` | `1` | `0` melewati uji saat build. **Hanya** untuk perbaikan darurat; jalankan uji sesudahnya (§8) |

Nilai yang salah atau terlalu longgar (mis. `ADMIN_IP_BOLEH` bukan alamat jaringan atau `0.0.0.0/0`, produksi tanpa
`ADMIN_HTTPS=1`) membuat kontainer `web` atau `admin` berhenti dengan pesan di log yang menyebut variabelnya. Admin
memeriksa pengaturannya sebelum membangun situs; situs tetap menyajikan hasil bangun terakhir.

## 5. Nyalakan pertama kali

Saat pertama kali, kontainer admin dengan sendirinya:
1. membuat kunci sesi di volume `prodi-rahasia`;
2. memakai **data awal** (salinan data www, lihat `platform/data-awal/www/asal.json`) dan mendaftarkan 97 prodi dengan
   slug yang disetujui (`platform/data-awal/slug.csv`), beserta tautan dosennya di dosen.unsrat.ac.id
   (`platform/data-awal/dosen.csv`, K-P31);
3. membangun semua situs (log: `Bangun semua (staging): … 3688 halaman`), lalu menjalankan admin
   (`Serving on http://0.0.0.0:8791`).

Langkah 2 hanya terjadi sekali; setelah itu data dan registri di volume yang dipakai. VM yang registrinya sudah ada
sebelum tautan dosen masuk data awal: superadmin mengunggah `platform/data-awal/dosen.csv` di menu **Tautan dosen**
(pratinjau, lalu terapkan).

**Buat akun superadmin** (sekali): `cd /opt/prodi-unsrat && sudo docker compose exec admin /bin/bash`, lalu di dalam
kontainer:

```bash
python platform/admin/siapkan.py --superadmin <nama> --nama-lengkap "Nama Lengkap"
cat /srv/prodi-rahasia/.kredensial-<nama>.txt     # kata sandi sementara
```

Masuk ke admin dengan kata sandi sementara itu; admin langsung meminta kata sandi baru (superadmin minimal 16
karakter, tidak memuat nama). Setelah itu hapus berkasnya:

```bash
rm /srv/prodi-rahasia/.kredensial-<nama>.txt
```

Akun lain (superadmin kedua, admin prodi) dibuat di admin, menu **Akun**. Buat minimal dua superadmin, supaya yang satu
bisa mereset kata sandi yang lain (tidak ada surel, K-P12).

**Periksa:**
- situs: `http://<IP-VM>:<PORT_SITUS>/` menampilkan daftar prodi dengan pita "Pratinjau staging";
- admin: `http://<IP-VM>:<PORT_ADMIN>/` dari jaringan UNSRAT menampilkan halaman masuk; dari luar jaringan **403**;
- kontainer `web` dan `admin` berstatus *healthy*;
- log `pemantau` setelah ±5 menit: `… 0 temuan`.

## 6. Data dari www

Data resmi prodi (nama, gelar, SKS, CPL, akreditasi, dll.) berasal dari www.unsrat.ac.id dan **diunggah superadmin**
(K-P18): admin → **Data www** → unggah berkas → periksa pratinjau → **Terapkan**.

- **Data prodi dan CPL:** di superadmin www, menu Impor Excel → Program studi → *Unduh templat (.xlsx)*. Unggah berkas itu
  apa adanya.
- **Fakultas, kalender akademik, identitas universitas** (jarang berubah): berkas JSON dari volume data www, diambilkan
  admin VM www, mis.:

  ```bash
  # di VM www
  for f in unit kalender situs; do sudo docker cp unsrat-web-admin-1:/srv/unsrat/mockup/data/$f.json ./$f.json; done
  ```

Unggahan pertama sesudah deploy sebaiknya Excel terbaru dari www, karena data awal adalah salinan saat repositori
dibuat. Dasbor superadmin menampilkan kapan data www terakhir diperbarui dan mengingatkan bila lebih dari 30 hari.

## 7. Domain dan HTTPS

### A. Di belakang load balancer (bawaan)

Stack melayani HTTP; sertifikat dipegang load balancer (seperti www).
- **Situs:** `prodi.unsrat.ac.id` → backend VM port `PORT_SITUS`. Health check HTTP ke `/sehat` (jawab `ok`).
  Pengalihan `http://` → `https://` diatur di load balancer.
- **Admin:** nama sendiri ke `PORT_ADMIN`, atau jalur di alamat yang sama (mis. `/admin`, awalan dibuang load balancer,
  lalu `ADMIN_AWALAN=/admin`). Health check port admin pakai **TCP**, bukan HTTP: admin menjawab 403 kepada alamat
  load balancer, sehingga health check HTTP menganggap backend mati. Bila admin dibuka lewat HTTPS: `ADMIN_HTTPS=1`.
  Di produksi admin wajib dibuka lewat HTTPS (sertifikat di load balancer, atau §7B), supaya kata sandi tidak pernah
  lewat jaringan tanpa enkripsi: `PRODI_MODE=produksi` tanpa `ADMIN_HTTPS=1` membuat kontainer `admin` berhenti.
- **`PROKSI_DEPAN`:** rentang alamat asal permintaan load balancer, ditambah alamat depan load balancer itu sendiri.
  Untuk load balancer Google: `130.211.0.0/22,35.191.0.0/16,<IP depan load balancer>`. Tanpanya admin melihat alamat
  load balancer dan menolak semua orang (403); log Nginx juga mencatat alamat yang salah.

### B. HTTPS di VM ini sendiri

Bila tidak ada load balancer, Nginx di kontainer `web` memegang sertifikat: port 443 melayani situs, 8443 admin, dan
port 80/8081 hanya mengalihkan ke HTTPS (kecuali `/sehat` dan tantangan Let's Encrypt).

1. Siapkan folder di VM: `sudo mkdir -p /srv/prodi-tls /srv/prodi-acme`.
2. Sertifikat, salah satu:
   - **sertifikat UNSRAT sendiri:** salin ke `/srv/prodi-tls/fullchain.pem` (sertifikat + rantai perantara) dan
     `/srv/prodi-tls/privkey.pem` (`chmod 600`);
   - **Let's Encrypt:** DNS `prodi.unsrat.ac.id` sudah menunjuk ke VM, port 80 terbuka. Deploy dulu dengan
     `PORT_SITUS=80` dan `ACME_FOLDER=/srv/prodi-acme` (masih `HTTPS_DI_VM=0`), lalu di VM:

     ```bash
     sudo apt install certbot
     sudo certbot certonly --webroot -w /srv/prodi-acme -d prodi.unsrat.ac.id
     sudo install -m 644 /etc/letsencrypt/live/prodi.unsrat.ac.id/fullchain.pem /srv/prodi-tls/fullchain.pem
     sudo install -m 600 /etc/letsencrypt/live/prodi.unsrat.ac.id/privkey.pem /srv/prodi-tls/privkey.pem
     ```

     Perpanjangan otomatis: simpan dua perintah `install` di atas sebagai
     `/etc/letsencrypt/renewal-hooks/deploy/prodi-tls.sh` (`chmod 755`). Timer certbot memperpanjang sendiri.
3. Variabel di `.env`: `HTTPS_DI_VM=1`, `TLS_FOLDER=/srv/prodi-tls`, `ACME_FOLDER=/srv/prodi-acme`, `PORT_SITUS=80`,
   `PORT_SITUS_HTTPS=443`, `PORT_ADMIN_HTTPS` (mis. `8444`), `ADMIN_HTTPS=1`, lalu `sudo docker compose up -d`.

Sertifikat yang diganti di `TLS_FOLDER` dipakai Nginx dalam 30 detik tanpa restart (log `web`:
`sertifikat TLS diperbarui`). Bila `HTTPS_DI_VM=1` tetapi sertifikat tidak ada, kontainer `web` berhenti dengan pesan
`… fullchain.pem tidak ada di TLS_FOLDER`.

## 8. Memperbarui ke versi baru

```bash
cd /opt/prodi-unsrat
sudo git pull
sudo docker compose up -d --build
```

Uji otomatis berjalan di setiap build; bila gagal, versi lama tetap berjalan. Volume tidak tersentuh oleh pembaruan.

Build memakai image dasar (Python, Nginx) yang sudah ada di VM. Sebulan sekali, dan setiap ada pengumuman keamanan
Python/Nginx/OpenSSL, bangun dengan image dasar terbaru: `sudo docker compose build --pull` lalu
`sudo docker compose up -d`.
Bila build terpaksa dilewati ujinya (`UJI_SAAT_BUILD=0`), jalankan uji sesudahnya; uji memakai folder sementara dan
tidak menyentuh volume:

```bash
sudo docker compose exec admin python uji/jalankan-semua.py
```

## 9. Cadangan harian dan pemulihan

Skrip `docker/cadangan-prodi.sh` menyalin volume `prodi-data` dan `prodi-rahasia` ke
`/srv/cadangan-prodi/<volume>-<tanggal>.tgz` (hanya bisa dibaca root) dan menghapus salinan yang lebih tua dari 14 hari.
Kontainer admin dihentikan beberapa detik selama penyalinan (situs tetap tayang) dan menyala lagi sendiri, juga bila
penyalinan gagal.

```bash
echo '30 1 * * * root /opt/prodi-unsrat/docker/cadangan-prodi.sh >> /var/log/cadangan-prodi.log 2>&1' | sudo tee /etc/cron.d/cadangan-prodi
sudo /opt/prodi-unsrat/docker/cadangan-prodi.sh     # sekali dengan tangan, untuk memastikan
```

Cron menjalankan skrip langsung dari folder repositori, jadi pembaruan skrip ikut dengan `git pull`. Lalu **salin
`/srv/cadangan-prodi` ke luar VM** secara berkala (mis. ke penyimpanan cadangan UPA TIK). Salinan `prodi-rahasia`
berisi hash kata sandi: simpan terbatas.

**Pemulihan** (mengganti seluruh isi kedua volume dengan cadangan tanggal itu; yang ditulis sesudahnya hilang):

```bash
sudo /opt/prodi-unsrat/docker/pulihkan-prodi.sh               # menampilkan tanggal cadangan yang ada
sudo /opt/prodi-unsrat/docker/pulihkan-prodi.sh 2026-11-01    # meminta konfirmasi "PULIHKAN"
```

Ketiga kontainer dihentikan selama pemulihan lalu dinyalakan lagi; admin membangun ulang semua situs saat mulai.
Variabel `TUJUAN` kedua skrip bisa diubah bila folder cadangan berbeda (dan `STACK` bila nama stack di
`docker-compose.yml` pernah diubah).

Untuk mengembalikan satu berkas data saja (mis. data satu prodi yang terhapus), tidak perlu pemulihan volume: pakai
admin → **Riwayat** (setiap berkas data punya versi sebelumnya).

## 10. Pemantauan dan log

- **Pemantau:** `sudo docker compose logs --tail 20 pemantau`. Normal: `… 3889 berkas diperiksa, 0 temuan` setiap
  10 menit. Temuan sesaat saat bangun ulang diperiksa ulang semenit kemudian dan tidak dilaporkan.
- **Log admin:** setiap bangun ulang, dan `PERINGATAN: bangun ulang gagal` bila gagal (situs tetap menyajikan hasil
  terakhir).
- **Log audit admin** (siapa mengubah apa): admin → Log audit, atau `prodi-data` → `log/audit.jsonl`. Tinjau mingguan.
- **Log Nginx** (`sudo docker compose logs web`): alamat pengunjung asli bila `PROKSI_DEPAN` benar.

### Bila pemantau menemukan sesuatu

Baris di atas `PEMANTAU: ADA TEMUAN` menyebut jenisnya: `BERUBAH` (halaman berbeda dari hasil bangun), `ASING`
(berkas yang tidak dibuat generator, mis. `.php`), `HILANG`, `SPAM` (teks judi, pinjol, jual ijazah, atau obat
terlarang), `SKRIP` (skrip/iframe dari luar).
1. Catat baris temuannya. Jangan langsung menghapus apa pun di VM.
2. Admin → Bangun ulang → **Bangun ulang semua situs**: hasil bangun menimpa halaman yang diubah dan menghapus berkas
   asing. Periksa log pemantau berikutnya (atau jalankan
   `sudo docker compose exec pemantau python /app/platform/pemantau/cek_integritas.py --folder /srv/publik --manifes /srv/prodi/manifes-publik.json`).
3. Bila `SPAM` ada di data (muncul lagi setelah bangun ulang): admin → Log audit dan Riwayat untuk melihat siapa
   mengubahnya; pulihkan versi sebelumnya, nonaktifkan akun yang dipakai, reset kata sandinya.
4. Laporkan ke UPA TIK; bila ada tanda VM disusupi (berkas asing muncul lagi tanpa jejak di log audit), pulihkan dari
   cadangan (§9) setelah VM diperiksa.

## 11. Tayang sebagai prodi.unsrat.ac.id

Setelah staging disetujui: `PRODI_MODE=produksi` dan `PRODI_ALAMAT=https://prodi.unsrat.ac.id` di `.env`, lalu
`sudo docker compose up -d`.
Pita "Pratinjau staging" dan `noindex` hilang, `sitemap.xml` dibuat, `robots.txt` mengizinkan mesin pencari. Pengalihan dari
situs prodi lama (mis. `informatika.unsrat.ac.id`) diatur di luar stack ini (K-P4).

- Admin harus sudah dibuka lewat HTTPS dengan `ADMIN_HTTPS=1` (§7). Tanpa itu kontainer `admin` berhenti dengan pesan
  `PRODI_MODE=produksi memerlukan ADMIN_HTTPS=1`, dan situs tetap menyajikan hasil bangun terakhir (masih bentuk
  staging) sampai admin berjalan.
- Isi bertanda `[CONTOH]` (isi contoh untuk melihat tampilan, `isi_halaman.py contoh`) tidak pernah diterbitkan di
  produksi. Log admin menyebutnya: `PERINGATAN … bertanda [CONTOH], tidak diterbitkan di produksi`. Ganti isinya di
  admin, atau tarik halamannya.

## 12. Bila ada masalah

| Gejala | Penyebab dan jalan keluar |
|---|---|
| Build gagal di langkah `uji/jalankan-semua.py` | Uji otomatis gagal di image ini. Versi lama tetap berjalan. Kirim log build ke pengembang |
| `web` berhenti: `40-prodi-jaringan: … bukan alamat jaringan` | `ADMIN_IP_BOLEH` atau `PROKSI_DEPAN` berisi yang bukan alamat/jaringan |
| `web` berhenti: `40-prodi-jaringan: … jaringan yang terlalu luas` | `ADMIN_IP_BOLEH` lebih luas dari `/8` (IPv6 `/32`), atau `PROKSI_DEPAN` lebih luas dari `/16` (IPv6 `/48`). Isi jaringan kampus/VPN atau subnet proksi yang sebenarnya |
| `admin` berhenti: `ADMIN_IP_BOLEH berisi …` | Sama seperti baris di atas: admin juga memeriksa `ADMIN_IP_BOLEH` |
| `admin` berhenti: `PRODI_MODE=produksi memerlukan ADMIN_HTTPS=1` | Buka admin lewat HTTPS (§7), lalu `ADMIN_HTTPS=1` di `.env` |
| `web` berhenti: `… fullchain.pem tidak ada di TLS_FOLDER` | `HTTPS_DI_VM=1` tanpa sertifikat (§7B) |
| Situs 404 semua, `web` *unhealthy* | Admin belum selesai membangun (lihat log admin) atau bangun gagal |
| Admin 403 "tidak dapat dibuka dari jaringan ini" atau 403 Nginx | Alamat Anda di luar `ADMIN_IP_BOLEH`; di belakang load balancer isi `PROKSI_DEPAN` (§7A) |
| Masuk admin selalu kembali ke halaman masuk | `ADMIN_HTTPS=1` tetapi admin dibuka lewat `http://` (cookie aman tidak dikirim browser) |
| Log admin: `PERINGATAN: bangun ulang gagal` | Situs tetap menyajikan hasil terakhir. Baca baris galat di atasnya; biasanya data yang tidak sah; pulihkan lewat Riwayat |
| Slug lama tidak dialihkan | Tunggu 30 detik; log `web` harus menulis `pengalihan slug lama diperbarui` |
| Data www tidak bisa diterapkan | Pesan di halaman Data www menyebut baris/berkas yang bermasalah; data tidak berubah sampai berkasnya benar |
| Semua superadmin lupa kata sandi | `sudo docker compose exec admin python platform/admin/siapkan.py --superadmin <nama-baru> ...` (§5), masuk, reset akun lama di menu Akun |
| Unggahan gagal "terlalu besar" | Batas per berkas: foto 10 MB, foto latar 15 MB, PDF 20 MB, logo 5 MB, data www 5 MB; per formulir 40 MB (Nginx menjawab 413) |

**Jangan:**
- membuka port admin ke internet;
- menaruh `.env`, berkas kredensial, atau cadangan `prodi-rahasia` di repositori atau tempat umum;
- menghapus volume `prodi-data` atau `prodi-rahasia` (seluruh data dan akun ada di sana);
- mengubah berkas di volume `prodi-publik` dengan tangan (pemantau akan melaporkannya, dan bangun ulang menimpanya).

## 13. Mencoba di komputer sendiri (pengembang)

Dengan Docker lokal, port yang tidak bentrok, dan jaringan Docker diizinkan membuka admin:

```bash
cat > /tmp/prodi-uji.env <<'EOF'
PORT_SITUS=18080
PORT_ADMIN=18081
PORT_SITUS_HTTPS=18443
PORT_ADMIN_HTTPS=18444
ADMIN_IP_BOLEH=103.84.116.0/24,172.16.0.0/12
PRODI_ALAMAT=http://127.0.0.1:18080
EOF
docker compose -p prodi-uji --env-file /tmp/prodi-uji.env up -d --build
docker compose -p prodi-uji exec admin python platform/admin/siapkan.py --superadmin penguji --nama-lengkap "Penguji"
docker compose -p prodi-uji down -v       # selesai: hapus kontainer dan volume uji
```

Situs di http://127.0.0.1:18080/, admin di http://127.0.0.1:18081/. Yang sudah dicoba dengan cara ini tercatat di
`docs/log/fase-01-langkah-7.md`.

Data awal untuk VM baru (`platform/data-awal/www/`) diperbarui pengembang setelah menarik data www terbaru di komputer
sendiri: `python3 platform/impor_www.py --tulis-data-awal --dari "www.unsrat.ac.id …, commit …"`.
