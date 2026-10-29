# Fase 2 langkah 7d — Masukan staging: bagan organisasi dan tautan RSS

Tanggal: 29 Oktober 2026. Branch: `fase/02-7d-tampilan`.

## Latar
Masukan pertama pengguna setelah staging tayang di VM (situs S1 Teknik Informatika):
1. Bagan di halaman Struktur Organisasi terlalu kecil dan harus diklik; seharusnya besar tanpa perlu diklik.
2. Tautan "Langganan lewat RSS" di bawah daftar pengumuman tidak perlu ada.

Nomor 3 dari masukan yang sama (sematan di halaman bawaan) dikerjakan di langkah 7e.

## Yang dikerjakan
- **Bagan organisasi.** Dulu bagian ini memakai tampilan galeri foto: kotak 4:3 selebar ±150 px yang memotong gambar
  (bagian bawah bagan hilang) dan harus diklik. Kini memakai tampilan baru `gambar` (`isi_halaman.gambar_daftar`,
  `_isi.html`):
  - setiap gambar utuh, tidak dipotong, dan bukan tautan;
  - selebar kolom isi (±770 px), atau selebar aslinya bila lebih sempit, karena gambar yang diperbesar membuat
    tulisannya buram. Browser memilih ukuran tersimpan yang cocok (`srcset` 400/800/1600);
  - di bawahnya tautan "Buka gambar ukuran penuh" untuk memperbesar di ponsel;
  - di penyunting: tombol **Tambah gambar** dan keterangan "unggah gambar selebar 1600 piksel atau lebih".

  Data tersimpan tidak berubah (kunci `berkas` dan `keterangan` sama), jadi bagan yang sudah diunggah langsung tampil
  besar tanpa unggah ulang. Galeri lain (Sejarah, Ruang, halaman tambahan) tetap galeri.
- **Pengumuman.** Baris "Langganan lewat RSS" dihapus. Bagian Arsip tetap, dan bagian bawah tidak dibuat bila tidak
  ada arsip. Umpan `rss.xml` tetap dibuat dan diumumkan lewat `<link rel="alternate">` di kepala halaman (tidak
  terlihat pengunjung), untuk pembaca umpan dan situs www.
- **Panduan admin prodi:** bagan organisasi dan tombol Tambah gambar.

## Uji
- `.venv/bin/python uji/jalankan-semua.py`: 22 rangkaian lulus.
- `uji_isi_halaman.py`: bagan tampil sebagai `figure.isi-gambar`; gambarnya bukan tautan; `srcset` 400/800/1200w;
  lebar dan tinggi asli di atribut; tautan ukuran penuh mengarah ke berkas yang diterbitkan; halaman tanpa galeri.
- `uji_pengumuman.py`: daftar tanpa tautan RSS dan umpan tetap diumumkan di kepala; prodi tanpa arsip tidak punya
  bagian bawah kosong.
- **Dilihat di browser** (situs sementara dengan gambar bagan dari pengguna, 621 × 571 piksel):
  - layar 1280 px: bagan tampil utuh 621 px (sebelumnya ±150 px terpotong) dan bukan tautan;
  - layar 375 px: selebar layar, tanpa gulir datar;
  - daftar pengumuman hanya menyisakan Arsip.

## Catatan
- Gambar bagan pengguna hanya 621 piksel lebarnya. Tulisannya akan lebih tajam bila bagan diekspor ulang selebar
  1600 piksel atau lebih.
- Tidak ada paket Python baru, variabel stack baru, atau migrasi data.
