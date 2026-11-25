# Fase 6 langkah 1 — Halaman akar sebagai peta jalur fakultas (K-P39)

Tanggal: 25 November 2026. Branch: `fase/06-1-direktori-akar`.

## Latar
Pengguna meminta desain baru yang bersih dan modern untuk halaman utama `prodi.unsrat.ac.id/`, lewat skill desain
Impeccable. Proyek belum punya konteks produk, jadi dimulai dengan wawancara singkat (`PRODUCT.md`). Jawaban pengguna:
- **Cakupan:** halaman akar saja; situs ke-97 prodi tidak berubah.
- **Pengunjung:** campuran merata.
- **Wajib dipertahankan:** lambang UNSRAT dan warna bendera fakultas.
- **Cara mencari:** prodi paling sering dicari dengan mengetik namanya.
- **Isi setiap prodi:** akreditasi dan gelar terlihat tanpa membuka situsnya.
- **Yang dihindari:** kesan "tabel kantor".

Impeccable mengundi arah desain dari tujuh calon yang diturunkan dari dunia pengunjung. Hasilnya disajikan sebagai
empat kartu dengan sketsa tampilan pertama, ditambah satu standar kategori. Pengguna memilih **Peta jalur fakultas**.

## Yang dikerjakan
- **Halaman akar** (`platform/template/halaman/akar.html`):
  - bilah lambang dengan teks "Program Studi" dan "Direktori situs program studi";
  - judul "Mau ke program studi mana?" dengan kotak cari;
  - 12 lencana jalur sebagai tautan lompat;
  - satu jalur per fakultas dan Program Pascasarjana, berurutan seperti data unit www. Setiap jalur berpita kepala
    warna bendera, dengan rel berwarna bendera dan halte prodi berurutan S1 → S2 → S3 → Profesi → Spesialis, berlabel
    jenjang. Setiap halte memuat nama, gelar, dan akreditasi.
  - Peringkat (Unggul, Baik Sekali, Baik, A, B, C) tampil sebagai tag, dan peringkat tertinggi (Unggul, A) terisi
    tinta. Status lain (Terakreditasi, Terakreditasi sementara, Akreditasi minimum, Menunggu akreditasi prodi baru)
    tampil sebagai teks setelah gelar. Nilai "belum" tidak tampil.
- **Warna jalur** (`bangun.warna_jalur`, `css_jalur` → `aset/css/jalur.css`):
  - dibuat saat bangun dari `bendera` di data unit www, karena CSP melarang gaya inline;
  - teks memakai warna tulisan bendera bila kontrasnya mencapai 4,5:1, selain itu putih, tinta, atau hitam (merah
    Fakultas Hukum hanya mencapai 4,5:1 dengan hitam);
  - bendera di bawah 3:1 terhadap putih (Pertanian, FEB, FISIP, MIPA) diberi tepi tinta.
- **Pencarian** (`aset/js/cari-prodi.js`):
  - menyaring halte saat mengetik; jenjang dan jalur yang kosong runtuh, lencananya meredup, jumlah hasil diumumkan;
  - halte yang cocok menyala sesaat (tanpa gerak bila `prefers-reduced-motion`);
  - tidak ada hasil: pesan dan tombol "Tampilkan semua program studi";
  - satu hasil: peta digantikan panel tiba, berisi halte besar di atas jalurnya dan tombol **Buka situs**; Enter
    langsung membuka situsnya;
  - kata yang diketik tersimpan di alamat (`?q=`).
- **Tanpa JavaScript:** `akar-tanpa-js.css` di dalam `<noscript>` menyembunyikan kotak cari. Seluruh peta dan lencana
  tetap ada. Dengan JavaScript, kotak cari ada sejak tampilan pertama, jadi halaman tidak bergeser saat skrip dimuat.
- **Gaya hanya di akar** (`aset/css/akar.css`):
  - huruf Overpass dan Overpass Mono (Google Fonts, sudah diizinkan CSP) lewat `font` yang kini bisa diganti per
    halaman di `Pembangun.render`;
  - tinta #15123b untuk bilah atas dan kaki halaman akar;
  - tautan "Semua program studi" disembunyikan di akar (halaman itu sendiri);
  - `prodi.css` dan `dasar.html` tidak berubah, jadi situs prodi tetap sama.
- **Impeccable:**
  - `PRODUCT.md`;
  - kontrak desain `.impeccable/surfaces/platform-template-halaman-akar-html.md`;
  - `DESIGN.md` dan `.impeccable/design.json` ditulis dari hasil jadi.
- **Dokumen:** K-P39, README (bagian Fase 6), CLAUDE.md.

## Uji
- `.venv/bin/python uji/jalankan-semua.py`: 29 rangkaian lulus.
- **`uji_bangun.py`:**
  - setiap prodi tepat satu halte, dan jalur berurutan seperti unit www;
  - kelas warna fakultas ada, halte dikelompokkan per jenjang, dan kata pencarian halte lengkap;
  - tag akreditasi: peringkat tertinggi terisi, akreditasi kosong tanpa tag;
  - tanpa gaya atau skrip inline, kotak cari tersembunyi lewat `<noscript>`, dan Overpass hanya di akar;
  - `jalur.css`, `warna_jalur`, dan `kelas_jalur` (kode unit aneh menjadi `lain`);
  - setiap bendera fakultas asli lolos kontras 4,5:1 untuk teks, dan jalur pucat diberi tepi.
- **`uji_fase1.py`:** nama, gelar, dan akreditasi atau status ke-97 prodi di halaman akar sama dengan data www.
- **Uji mutasi:** empat aturan dimatikan satu per satu (fallback hitam, tepi jalur pucat, urutan unit, kotak cari
  tanpa JavaScript). Setiap kali ada uji yang gagal.
- **Detektor Impeccable** (`impeccable detect`): 60 temuan pertama sudah diperbaiki, yaitu padding tag akreditasi dan
  kontras hover tautan lewati. Hasil akhirnya 0 temuan.
- **Peninjau akhir Impeccable:**
  - putaran pertama berputusan *fix* dengan enam perbaikan: panel tiba tidak boleh menampilkan prodi dua kali, halte
    menyala, tag peringkat tertinggi terisi, status bukan peringkat sebagai teks, bilah atas dobel, dan pergeseran
    kotak cari;
  - verdict kedua: keenamnya *resolved*, dengan satu regresi di tag panel tiba;
  - setelah regresi itu diperbaiki, putusannya **ship**. Lingkupnya perbaikan yang dinilai, bukan tinjauan ulang
    seluruh halaman.
- Diperiksa langsung di browser pada 1440 × 900 dan 375 × 812: tanpa geser horizontal di 375 px; pencarian, hasil
  kosong, dan panel tiba berjalan.

## Catatan
- Tangkapan otomatis Impeccable (`first-viewport`) butuh Chrome, yang tidak terpasang. Tangkapan diambil dari browser
  di aplikasi.
- Tidak ada paket Python baru, variabel stack baru, atau migrasi data. Halaman akar dibangun ulang otomatis bersama
  setiap bangun.
- Folder `.claude/`, `.agents/`, dan `.cursor/` (instalasi Impeccable) tidak ikut di-commit sampai pengguna memutuskan.
