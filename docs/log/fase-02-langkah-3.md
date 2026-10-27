# Fase 2 · Langkah 3 — Alur dan kelengkapan (27 Oktober 2026)

Branch: `fase/02-3-alur` (bercabang dari `fase/02-2-penyunting`). Rencana: [rencana Fase 2](../rencana-fase-02.md) §3.4,
§3.6, dan §7, keputusan K-P24, K-P27 (disetujui), dan **K-P28 (baru, menunggu tinjauan)**.

## Yang dikerjakan
- **Alur isi halaman** (`platform/isi_halaman.py`, K-P24, K-P28). Draf berstatus draf, menunggu, atau dikembalikan:
  - **Ajukan** (operator): hanya isi yang lolos semua pemeriksaan dan tidak kosong; pengajunya dicatat. Draf yang
    menunggu tetap bisa disunting dan tetap menunggu.
  - **Batalkan pengajuan** (operator): kembali menjadi draf biasa.
  - **Kembalikan dengan catatan** (admin prodi): catatan wajib, paling banyak 500 karakter, diperiksa saringan judi.
    Catatan tampil di penyunting sampai draf diajukan lagi.
  - **Terbitkan** (admin prodi): draf yang diajukan, atau perubahan admin sendiri secara langsung. Draf selesai,
    pengajunya disimpan bersama isi terbit, dan situs prodi dibangun ulang.
  - **Tarik dari situs** (admin prodi): halaman kembali "sedang dilengkapi"; isinya menjadi draf bila belum ada draf.
    Situs dibangun ulang.
  - **Buang draf**: admin kapan saja; operator tidak untuk draf yang sedang menunggu.
  - Setiap tindakan memeriksa versi asal formulir: tindakan dari versi lama ditolak dengan nama pengubah dan waktunya,
    tanpa menulis apa pun. Semua tindakan masuk riwayat versi dan log audit (`isi-diajukan`,
    `isi-pengajuan-dibatalkan`, `isi-dikembalikan`, `isi-diterbitkan`, `isi-ditarik`, `isi-versi-dipakai`).
- **Penyunting** (`platform/admin/isi_admin.py`, `halaman_sunting.html`):
  - kartu keadaan halaman (terbit kapan dan oleh siapa; draf, pengaju, catatan dari admin);
  - tombol menurut peran: operator melihat Ajukan atau Batalkan pengajuan, admin melihat Terbitkan dan kotak catatan
    Kembalikan bila draf menunggu. Tarik dan Buang ada di bagian bawah;
  - setiap tombol menyimpan dulu isi formulir; tombol pertama tetap "Simpan draf";
  - operator yang mengirim Terbitkan, Kembalikan, atau Tarik ditolak di server (403), apa pun isi formulirnya.
- **Riwayat per halaman** (`/prodi/<kode>/halaman/<id>/riwayat`):
  - 50 versi terbaru dengan perubahan sesudahnya ("Diajukan", "Dikembalikan dengan catatan", "Diterbitkan", …),
    pelakunya, dan isinya (isi terbit, draf beserta statusnya);
  - setiap versi bisa dipratinjau dengan gaya situs, lalu **dijadikan draf**; versi lama tidak pernah langsung ke situs
    (K-P28). Operator juga boleh, karena hanya mengubah draf.
- **Kelengkapan** (rencana §3.6):
  - **daftar halaman**: saringan Menunggu persetujuan, Dikembalikan, Draf, Terbit, Belum diisi beserta jumlahnya;
    halaman terbit yang punya draf tampil dengan keduanya;
  - **dasbor prodi**: kartu "Isi halaman" (*n* dari 22 halaman wajib terbit; menunggu, dikembalikan, draf, belum diisi).
    Admin melihat pesan "*n* halaman menunggu persetujuan Anda", operator melihat halaman yang dikembalikan;
  - **superadmin** (`/super/kelengkapan`, menu "Kelengkapan"): tabel 97 prodi (wajib terbit, menunggu, dikembalikan,
    draf, terakhir diubah) dan ringkasannya. Unduhan CSV untuk LPMPP memuat keadaan setiap halaman per prodi
    ("terbit 2026-10-27", "menunggu persetujuan", "belum diisi", dan sebagainya), ber-BOM untuk Excel, dengan sel rumus
    dinetralkan.
  - Yang dihitung adalah halaman wajib yang terbit dan tampil (lolos pemeriksaan).
- **Diubah dari langkah 2**:
  - nilai tombol "Buang draf" menjadi `buang`, dan tombol mengembalikan butir yang baru dihapus menjadi
    `pulihkan-butir`, karena `kembalikan` sekarang berarti mengembalikan draf ke penulis;
  - perbandingan "ada perubahan?" mengabaikan isian kosong, sehingga membuka lalu menyimpan halaman tanpa perubahan
    tidak membuat draf.
- **Perbaikan sampingan**:
  - `impor_dosen.aman_csv` (dulu `_aman`) menulis angka 0 sebagai sel kosong; kini tetap "0" (ditemukan uji CSV
    kelengkapan);
  - di admin, teks panjang tanpa spasi (jalur berkas di dasbor superadmin) kini terbungkus, tidak lagi melebarkan halaman.

## Verifikasi
```bash
.venv/bin/python uji/jalankan-semua.py
```
Hasil: 16 rangkaian, 0 gagal. `uji_admin.py`: matriks 81 rute × 6 akun (6 baris baru: riwayat halaman, pratinjau dan
penggunaan versi lama untuk prodi sendiri dan prodi lain, kelengkapan dan CSV-nya).

Rangkaian baru `uji/uji_alur_isi.py`:
- **fungsi alur**:
  - ajukan hanya isi yang lolos dan tidak kosong; status terbawa saat disunting;
  - catatan kosong, terlalu panjang, berkarakter kendali, atau berteks judi ditolak;
  - kembalikan dan batalkan hanya untuk draf yang menunggu;
  - terbitkan dari draf (draf selesai, pengaju dicatat); tarik (isi menjadi draf; draf yang ada tetap);
  - versi lama dijadikan draf; versi atau bagian yang tidak ada ditolak, termasuk jalur `../`;
  - setiap tindakan dari versi lama ditolak;
  - keadaan halaman, termasuk "terbit tetapi tidak tampil";
- **lewat admin, dengan bangun ulang sungguhan**:
  - operator: ajukan dengan isian salah (ditolak, ketikan menjadi draf), ajukan, sunting saat menunggu, batalkan;
    Terbitkan/Kembalikan/Tarik ditolak 403 tanpa menulis apa pun; tidak bisa membuang draf yang menunggu;
  - admin: kembalikan tanpa catatan ditolak, dengan catatan diterima (catatan di-escape di penyunting operator);
    diperbaiki dan diajukan lagi; menerbitkan dari versi lama ditolak (409); terbitkan (situs menampilkan isinya),
    terbitkan tanpa perubahan, terbitkan langsung, isi tidak lolos menjadi draf; buang; tarik (situs kembali "sedang
    dilengkapi");
  - riwayat halaman, pratinjau versi lama, versi lama dijadikan draf oleh operator (situs tidak berubah);
  - saringan daftar, dasbor admin dan operator, tabel kelengkapan dan CSV (kolom, jumlah, keadaan setiap halaman,
    semua prodi), hanya untuk superadmin; log audit.

`uji_penyunting.py` (langkah 2) tetap lulus dengan nilai tombol yang baru; pembantunya dipindah ke `uji/formulir_uji.py`
untuk dipakai kedua rangkaian.

Uji mutasi (setiap aturan dimatikan sementara):

| Aturan yang dimatikan | Uji yang gagal |
|---|---|
| Operator tidak boleh Terbitkan/Kembalikan/Tarik | 6 (alur berhenti) |
| Ajukan hanya isi yang lolos | 4 |
| Catatan wajib saat mengembalikan | 3 (alur berhenti) |
| Terbitkan dari draf menyelesaikan draf | 8 |
| Tarik menjadikan isi draf | 1 (alur berhenti) |
| Versi lama hanya menjadi draf (bukan langsung terbit) | 6 |
| Operator tidak membuang draf yang menunggu | 3 (alur berhenti) |
| Cek versi pada perubahan status | 3 (alur berhenti) |
| Status draf terbawa saat disunting | 2 (alur berhenti) |
| Kelengkapan hanya superadmin (`uji_admin.py`) | 5 |
| Angka 0 di CSV | 1 |

"Alur berhenti" berarti langkah berikutnya tidak bisa berjalan setelah aturan itu dilanggar. Rangkaian mencatat di mana
alur berhenti dan pemeriksaan yang gagal sebelumnya, bukan hanya traceback.

Diperiksa di browser (cuplikan statis dari klien uji, tanpa mengetik sandi):
- **desktop**:
  - penyunting admin untuk draf yang menunggu (kartu keadaan, Terbitkan, kotak catatan Kembalikan);
  - penyunting operator untuk draf yang dikembalikan (catatan dari admin, Ajukan);
  - daftar halaman dengan saringan; dasbor admin dan operator;
  - riwayat halaman; pratinjau versi lama; kelengkapan superadmin;
- **320 px**: kedua belas cuplikan tanpa gulir ke samping.

**Ditemukan dan diperbaiki** di browser:
- kotak teks paragraf duduk di samping lencana markah pada layar lebar; kini selalu di barisnya sendiri;
- angka di tabel kelengkapan bertumpuk, karena kelas `angka` sudah dipakai untuk daftar angka di dasbor; kini memakai
  kelas sendiri;
- dasbor superadmin melebar ke 508 px pada 320 px karena jalur berkas sumber data www yang panjang (masalah lama dari
  Fase 1).

## Perlu diketahui
- **K-P28** merinci aturan alur di dalam K-P24. Mohon ditinjau, terutama dua hal:
  - operator boleh menyunting draf yang sedang menunggu;
  - versi lama hanya bisa dijadikan draf.
- **Pemberitahuan** hanya lewat dasbor dan daftar halaman (tanpa SMTP, K-P12).
- **Riwayat per halaman** menampilkan 50 versi terbaru; versi yang lebih lama ada di menu Riwayat (admin prodi).
- **Kelengkapan superadmin** membaca 24 berkas per prodi pada setiap pembukaan, kira-kira 2.300 berkas kecil untuk 97
  prodi. Bila nanti terasa lambat di staging, hasilnya bisa disimpan sementara.
- **Langkah 4** (Dokumen Akreditasi dan label kriteria): halaman dokumen bisa dikerjakan; label kriteria menunggu daftar
  dari LPMPP (K-P25).

## Langkah berikutnya
Langkah 4 — Dokumen Akreditasi dan label kriteria (rencana §3.7).
