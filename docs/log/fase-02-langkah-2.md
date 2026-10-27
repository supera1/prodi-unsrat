# Fase 2 · Langkah 2 — Penyunting di admin (27 Oktober 2026)

Branch: `fase/02-2-penyunting` (bercabang dari `fase/02-1-isi`). Rencana: [rencana Fase 2](../rencana-fase-02.md) §3.1–§3.5
dan §5, keputusan K-P23, K-P24, dan **K-P27 (baru, menunggu tinjauan)**.

## Yang dikerjakan
- **Menu prodi "Isi halaman"** (`platform/admin/isi_admin.py`), untuk admin prodi dan operator:
  - **Daftar halaman**: ke-24 halaman per kelompok menu dengan keadaannya (belum diisi, draf, terbit, ada draf; kapan
    dan oleh siapa). Halaman opsional yang disembunyikan di menu ditandai.
  - Baris dasbor prodi "halaman wajib menunggu isi (Fase 2)" kini berbunyi "*n* dari 22 halaman wajib akreditasi
    sudah berisi di situs" dan menautkan daftar itu. Kelengkapan lengkap tetap langkah 3.
- **Penyunting per halaman**: formulir dibentuk dari templat isi (`platform/admin/penyunting.py`, adaptasi
  `editor.py` www, dicatat di `docs/asal-modul.md`):
  - satu kartu per bagian halaman;
  - paragraf dengan petunjuk markah;
  - daftar baris (misi, tujuan) satu isian per baris;
  - baris tabel dan kartu sebagai butir yang bisa dilipat (`<details>`), dengan tombol Naik, Turun, Hapus, dan Tambah,
    tanpa JavaScript.
- **Unggah PDF dan foto** di baris mana pun:
  - PDF diperiksa `media.periksa_pdf`; foto dikodekan ulang ke 1600/800/400 px dan wajib berteks alternatif;
  - berkas yang ada tampil (tautan PDF dengan jumlah halaman dan ukuran, foto kecil) beserta kotak "Lepas";
  - judul PDF mengikuti barisnya ("Bukti kerja sama: Universitas X"), dipakai sebagai teks tersembunyi tautan PDF di
    tabel situs.
- **Simpan draf**, **Simpan dan pratinjau**, dan **Buang draf** (kembali ke isi terbit). Situs tetap menampilkan isi
  terbit; menerbitkan draf adalah langkah 3.
- **Isian yang belum sah tidak hilang** (K-P27):
  - tahun "20o5" atau persen "abc" disimpan apa adanya di draf;
  - isian itu ditandai (`aria-invalid`, pesan di bawahnya), dan ringkasan di atas formulir menautkan setiap isian yang
    perlu diperbaiki ("Daftar kerja sama baris 2, Tahun mulai: harus angka bulat");
  - baris yang baru ditambah dan masih kosong tidak ditandai, lalu dibuang saat Simpan draf;
  - butir yang baru dihapus bisa dikembalikan (tombol "Kembalikan baris itu") sampai simpanan berikutnya.
- **Isian yang diketik dibaca dengan wajar**: angka dengan titik ribuan, persen dengan koma ("87,5"), jeda baris Word
  menjadi baris baru, karakter kendali dibuang. Pilihan yang tidak lagi ditawarkan templat tetap tampil sampai diganti.
- **Pratinjau**: draf ditampilkan dengan makro `_isi.html` dan CSS situs (`prodi.css`, warna prodi), di admin saja.
  Isian yang belum sah dilewati dan jumlahnya disebut.
- **Pembaca layar**: setiap label dan tombol butir menyebut barisnya ("Mitra, baris 3", "Hapus baris 3", "Tambah
  baris ke Daftar kerja sama"). Isian wajib bertanda "(wajib)". Tombol pertama formulir adalah "Simpan draf", sehingga
  Enter di sebuah isian tidak pernah menekan Hapus.
- **Draf** (`platform/isi_halaman.py`):
  - `simpan_draf`, `buang_draf`, `rapikan`, `isi_sah` (salinan untuk pratinjau), dan `daftar_masalah`/`periksa_jalur`
    (masalah per nama isian formulir);
  - setiap tulisan menaikkan `versi` dan mencatat `diubah` (oleh, waktu); semua tulisan berjalan di bawah satu kunci,
    sehingga dua simpanan bersamaan tidak bisa sama-sama lolos.
- **Riwayat**: Simpan draf, Buang draf, penerbitan, dan penarikan masuk riwayat versi. Tombol daftar dan pratinjau
  tidak (K-P27). Memulihkan versi lama kini meneruskan hitungan versi (`riwayat.pulihkan`), sehingga formulir yang
  dibuka sebelum pemulihan ditolak.
- **Keamanan**:
  - rute baru memakai `@akses("prodi")` (operator juga); `/aset-situs/<nama>` memakai `@akses("masuk")` dan hanya
    melayani `tokens.css` dan `prodi.css`. Semua masuk matriks akses (75 rute × 6 akun);
  - rekaman berkas tidak pernah diambil dari formulir;
  - draf yang merujuk berkas prodi lain ditolak, dan satu draf paling besar 2 MB;
  - batas bagian formulir dinaikkan ke 4.000 (bawaan Flask 1.000), karena formulir terbesar (kerja sama 300 baris) berisi
    2.725 bagian;
  - CSRF, tanpa skrip atau gaya sebaris, dan peringatan privasi di setiap formulir.
- **Simpanan bentrok**: simpanan dari versi lama ditolak (409) dengan nama pengubah dan waktunya ("halaman ini baru saja
  diubah oleh adma (…)"). Tidak ada yang ditulis, termasuk berkas, dan pengguna diarahkan ke tombol Kembali browser untuk
  menyalin ketikannya.
- **Perbaikan sampingan**: `bangun.lingkungan()` dipakai bersama generator dan pratinjau. `.tabel-gulir` admin menjadi
  wadah posisi; temuannya sama dengan langkah 1 di situs (teks tersembunyi di sel tabel melebarkan halaman).

## Verifikasi
```bash
.venv/bin/python uji/jalankan-semua.py
```
Hasil: 15 rangkaian, 0 gagal. `uji_admin.py`: matriks 75 rute × 6 akun (10 baris baru, termasuk prodi lain, halaman
tanpa templat isi, dan aset di luar daftar). Rangkaian baru `uji/uji_penyunting.py` memeriksa:
- **formulir ke-24 templat**, kosong dan berisi contoh dengan PDF/foto sungguhan:
  - id unik, setiap isian berlabel, tanpa skrip/gaya sebaris, di bawah batas bagian formulir;
  - formulir yang tidak diubah memberi kembali isi yang sama persis. Juga lewat admin untuk ke-24 halaman: simpan tanpa
    perubahan tidak menulis apa pun;
- **pembacaan isian**:
  - angka (`1.234`, `1.5` tetap apa adanya, `-2` ditandai) dan persen (`87,5`, `100%`, `87,555` tidak dibulatkan);
  - teks satu baris dan paragraf, karakter kendali, pilihan asing dan pilihan lama, kotak centang;
  - kunci asing disimpan; isian yang tidak dikirim tetap;
  - formulir tidak bisa memasang rekaman berkas atau menambah baris sendiri;
- **tombol daftar**: tambah, naik, turun, hapus dan kembalikan, daftar penuh; 14 bentuk tombol yang tidak ada di
  formulir ditolak (termasuk `../`, angka non-ASCII, jalur ke isian);
- **draf**:
  - versi, riwayat hanya untuk simpanan biasa, bentrok dengan nama pengubah;
  - 8 utas menyimpan bersamaan dari versi yang sama: tepat satu yang menang;
  - berkas prodi lain dan draf terlalu besar ditolak tanpa menulis apa pun;
  - buang draf, baris kosong dibuang, salinan pratinjau, pemulihan versi yang terus menghitung;
- **lewat admin**:
  - tambah baris lalu mengisinya, tahun salah ditandai di isian dan ringkasan, PDF diunggah dan dijuduli barisnya;
  - PDF rusak, foto tanpa teks alternatif, foto terlalu kecil, dan berkas bukan foto ditolak dengan tempatnya, tanpa
    berkas tersimpan;
  - ubah teks alternatif saja, lepas foto;
  - naik/hapus/kembalikan; tombol dan versi palsu (400);
  - operator dan admin menyunting halaman yang sama (409, tidak ada yang ditulis);
  - pratinjau: makro dan CSS situs, escaping, markah terbatas, nilai belum sah dilewati, foto/PDF lewat rute berkas admin;
  - aset dan warna untuk pratinjau; daftar penuh; isi terbit dengan draf di sampingnya;
  - situs tetap hanya menampilkan isi terbit; admin prodi lain ditolak; log audit (`isi-draf-disimpan`,
    `isi-berkas-diunggah`, `isi-draf-dibuang`).

Uji mutasi (setiap aturan dimatikan sementara):

| Aturan yang dimatikan | Uji yang gagal |
|---|---|
| Pemeriksaan versi | 7 |
| Escaping formulir | 2 |
| Formulir tidak boleh memasang rekaman berkas | 1 |
| Kunci tulis (dengan jeda 50 ms di antara baca dan tulis) | 1 |
| Berkas prodi lain di draf | 4 |
| Hitungan versi saat pemulihan | 2 |
| Pola nama isian pada tombol | 1 |
| Masalah di baris kosong tidak ditandai | 2 |
| `@akses("prodi")` pada simpan → `@akses("masuk")` (`uji_admin.py`) | 4 |

Diperiksa di browser (cuplikan statis dari klien uji, tanpa mengetik sandi):
- **desktop**: daftar halaman; penyunting kerja sama (ringkasan masalah, baris yang perlu diperbaiki, PDF terunggah,
  tawaran kembalikan); misi; foto sejarah; pratinjau tabel, kartu laboratorium dengan foto dan SOP; halaman bentrok;
- **320 px**: kesebelas cuplikan tanpa gulir ke samping (tabel daftar halaman bergulir di dalam wadahnya).

**Ditemukan dan diperbaiki** di browser:
- isian angka/pilihan tetap selebar penuh karena aturan lebarnya kalah spesifik; kini dibatasi lewat kotaknya, dan
  pilihan panjang ("Pengabdian kepada masyarakat") tidak terpotong;
- garis merah isian yang salah tidak muncul, juga karena spesifisitas;
- halaman daftar melebar ke 370 px pada layar 320 px karena teks tersembunyi tautan "Lihat" di tabel.

## Perlu diketahui
- **Belum bisa menerbitkan.** Ajukan, terbitkan, kembalikan, tarik, kelengkapan, dan riwayat per halaman adalah langkah 3.
  Sampai itu draf hanya terlihat lewat pratinjau.
- **Satu draf bersama per halaman.** Operator dan admin menyunting draf yang sama, dan simpanan bentrok ditolak.
  Langkah 3 bisa membatasi penyuntingan draf yang sedang diajukan.
- **K-P27** (riwayat hanya untuk simpanan sengaja, bukan setiap klik tombol daftar) lebih sempit dari bunyi rencana §3.4
  "setiap simpanan masuk riwayat". Mohon ditinjau.
- **Tabel besar menjadi formulir panjang** (kerja sama sampai 300 baris, publikasi 500): satu butir per baris yang bisa
  dilipat. Bila pilot merasa berat, impor Excel (rencana §3.8) bisa dikerjakan.
- **Batas unggahan:** satu kali simpan paling banyak 40 MB berkas (petunjuk ada di formulir). Bila lebih, admin menjawab
  "Berkas atau formulir terlalu besar", dan ketikan masih bisa diambil lewat tombol Kembali browser.
- **Foto:** foto tanpa teks alternatif ditolak; teks alternatif diisi sebelum memilih foto.
- **Pratinjau** memakai huruf sistem, karena CSP admin tidak memuat Google Fonts. Selebihnya sama dengan situs.

## Langkah berikutnya
Langkah 3 — alur dan kelengkapan: ajukan/terbitkan/kembalikan/tarik, riwayat isi halaman, kelengkapan di dasbor prodi
dan superadmin (dengan unduhan CSV).
