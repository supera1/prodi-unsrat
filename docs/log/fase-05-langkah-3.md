# Fase 5 langkah 3 — Terjemahan mesin (DeepL) (K-P37)

Tanggal: 20 November 2026. Branch: `fase/05-3-terjemah-mesin`.

## Latar
Langkah 3 [rencana Fase 5](../rencana-fase-05.md) (§3.5): draf terjemahan mesin dari versi Indonesia untuk penyunting
versi Inggris, supaya prodi tidak menerjemahkan dari nol. Pengguna sudah punya kunci API DeepL. Kunci itu tidak dikirim
lewat chat dan tidak dipakai pengembang: uji memakai penyedia tiruan, dan admin VM memasang kuncinya di `.env`.

## Yang dikerjakan
- **`platform/terjemah_mesin.py`:**
  - penyedia **DeepL** dengan pustaka standar Python, tanpa paket baru: `POST /v2/translate`, kunci di header
    `Authorization`, host `api-free.deepl.com` untuk kunci berakhiran `:fx` dan `api.deepl.com` untuk yang lain, Indonesia
    ke Inggris (`EN-US`), paling banyak 50 teks atau ±100 KB per permintaan;
  - penyedia **tiruan** untuk uji dan untuk mencoba penyunting tanpa akun; ditolak di produksi;
  - setiap galat (kunci ditolak, kuota habis, terlalu banyak permintaan, DeepL tidak terjangkau, jawaban tidak lengkap)
    menjadi pesan untuk admin prodi, tanpa pernah memuat kuncinya;
  - **istilah tetap** dari data resmi (nama Inggris prodi dan fakultas, nama universitas, gelar, lembaga akreditasi,
    UNSRAT) dikunci di dalam `<keep>`, sehingga keluar persis seperti data resmi;
  - **markah dilindungi:** tautan menjadi `<a href>` (alamatnya tidak pernah diterjemahkan), huruf tebal menjadi `<b>`,
    dan alamat polos menjadi `<keep>`. Teks dikirim per baris, lalu daftar "- " dan paragraf disusun kembali;
  - hasil yang tidak kembali utuh (tautan berubah, markah asing) atau ditolak saringan spam dibuang dan dilaporkan;
  - **pemakaian** dihitung dalam karakter teks Indonesia yang dikirim (`prodi/<kode>/terjemah-pemakaian.json`):
    batas per prodi per hari dan batas semua prodi per bulan.
- **Penyunting versi Inggris:**
  - kotak **Terjemahan mesin** dengan perkiraan jumlah teks dan karakter serta sisa batas hari ini;
  - tombol **Terjemahkan dari versi Indonesia** mengisi isian yang kosong lalu menyimpannya sebagai draf. Ada pilihan
    **terjemahkan ulang** (menimpa) dan, di halaman Tugas Akhir, pilihan menerjemahkan judul tabel Excel;
  - hasil mesin ditandai per isian. Isian yang diubah orang dianggap sudah diperiksa. Pengajuan dan penerbitan ditolak
    sampai **Saya sudah memeriksa terjemahan mesin di halaman ini** dicentang, dan `isi_halaman` juga menolak
    menerbitkan versi Inggris yang masih bertanda mesin;
  - penyedia yang gagal tidak mengubah apa pun selain menyimpan ketikan, dan tidak dihitung sebagai pemakaian;
  - setiap terjemahan mesin tercatat di log audit (`isi-en-terjemahan-mesin`, jumlah teks dan karakter).
- **Dasbor superadmin:** pemakaian bulan ini untuk semua prodi dan batasnya.
- **Stack:** `TERJEMAH_PENYEDIA`, `TERJEMAH_KUNCI`, `TERJEMAH_BATAS_HARIAN` (bawaan 50.000), dan
  `TERJEMAH_BATAS_BULANAN` (bawaan 500.000, sama dengan kuota DeepL API Free) ada di `docker-compose.yml`,
  `.env.example` (tanpa nilai), dan `docs/deploy.md` §4–§4A, dengan cara memasang kunci dan menggantinya bila bocor.
  Pengaturan yang tidak sah membuat admin berhenti dengan pesan.
- **Panduan admin prodi:** cara memakai terjemahan mesin di bagian "Versi bahasa Inggris".

## Uji
- `.venv/bin/python uji/jalankan-semua.py`: 26 rangkaian lulus.
- **`uji/uji_terjemah_mesin.py`** (baru):
  - markah bolak-balik, istilah tetap, karakter khusus, tautan non-https ditolak, hasil rusak atau berjudi dibuang,
    pembagian permintaan;
  - DeepL dengan jaringan tiruan: host Free dan Pro, header, isi permintaan, galat 403/429/456/lainnya dan jaringan
    putus beserta pesannya, kunci tidak pernah muncul di pesan;
  - pengaturan dan batas; pemakaian harian, bulanan, dan disimpan 31 hari;
  - admin: tanpa penyedia tanpa tombol, perkiraan, draf terisi dan bertanda, ketikan sendiri tetap, pengajuan ditolak
    sebelum dicentang, isian yang diubah dianggap diperiksa, terjemahkan ulang, judul tabel Excel hanya bila dipilih,
    penyedia gagal, tanpa teks yang perlu diterjemahkan, batas harian, log audit, dasbor superadmin, dan kunci API tidak
    tampil di halaman admin.
- **Uji mutasi:** enam aturan dimatikan satu per satu (belum diperiksa tidak terbit, batas harian, tautan hanya https,
  saringan spam hasil mesin, diubah berarti diperiksa, istilah tetap), dan setiap kali ada uji yang gagal.
- `uji_docker.py`: 19 variabel stack terdokumentasi. `uji_pilot.py`: label terjemahan mesin di panduan tampil di admin.
- **Dilihat di browser** (admin sementara dengan penyedia tiruan): kotak terjemahan mesin dengan perkiraan; sesudah
  ditekan, isian terisi dan bertanda, dan sisa batas harian berkurang.

## Catatan
- Belum dicoba dengan akun DeepL sungguhan. Uji di image memakai penyedia tiruan. Percobaan pertama dengan kunci asli
  dilakukan setelah admin VM memasangnya (`docs/deploy.md` §4A), atau di komputer pengembang dengan kunci di
  `rahasia/.env` yang diisi pemilik kunci sendiri.
- Tidak ada paket Python baru. Ada variabel stack baru (empat di atas), tetapi tanpa migrasi data. Tanpa
  `TERJEMAH_PENYEDIA`, admin berjalan seperti sebelumnya.
