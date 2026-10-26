# Fase 1 · Langkah 3c — Bagian depan beranda per prodi (26 Oktober 2026)

Branch: `fase/01-3c-beranda` (bercabang dari `fase/01-3b-pengumuman`). Keputusan: K-P15.

## Yang dikerjakan
- **Pengaturan** `platform/tampilan_prodi.py` → `prodi/<kode>/situs.json` (`tagline` + `beranda`).
  - Latar: `pucat` (bawaan), `utama` (warna prodi penuh), `warna` (kode warna bebas), atau `foto`.
  - Teks: label kecil, judul, subjudul, kalimat pengantar; kosong = bawaan dari data resmi.
  - Kartu fakta: label, urutan, dan tampil/sembunyi kartu resmi; maksimal 2 kartu tambahan (label, nilai, keterangan).
    **Nilai kartu resmi tidak bisa ditimpa** — pengaturan yang mencoba menimpanya ditolak.
  - Semua teks: panjang dibatasi, tanpa `< >`/karakter kendali, tanpa teks judi.
  - Pengaturan yang tidak sah (mis. ditulis tangan melewati pemeriksaan) diabaikan saat bangun, dengan peringatan;
    situs memakai bawaan, jadi tidak pernah terbit.
- **Keterbacaan**: warna pilihan mendapat teks putih atau gelap yang mencapai 4,5:1 (contoh ditolak: `#808080`,
  kontras 3,95 dan 3,78). Foto mendapat lapisan warna gelap prodi; opasitasnya dihitung (FT: 0,57) agar teks putih
  ≥ 4,5:1 bahkan di atas bagian foto yang putih.
- **Foto latar** `media.olah_hero` / `simpan_foto_hero`: JPEG/PNG ≤ 15 MB, minimal 2400 × 800 px; dipotong 3:1
  (2400 × 800, 1600 × 533) dan 4:3 (1200 × 900, ponsel) di sekitar titik fokus; dikodekan ulang tanpa EXIF.
  Petunjuk untuk formulir admin: `media.PETUNJUK_HERO`.
- **Generator**: warna latar dan foto ditulis ke `<slug>/warna.css` (variabel `--hero-*` dan `background-image` per
  lebar layar), sehingga CSP tetap tanpa gaya *inline*. Foto latar menjadi gambar pratinjau tautan beranda. Bila berkas
  fotonya hilang, beranda memakai latar bawaan dengan peringatan.
- Urutan pilihan admin kini menang bila angkanya sama dengan posisi bawaan (kartu dan menu).
- Perintah baris sementara: `tampilan_prodi.py lihat | atur | foto`.
- `uji/uji_beranda.py`; `uji_bangun.py` disesuaikan (tagline bermarkah kini ditolak, bukan sekadar di-escape).

## Verifikasi
```bash
.venv/bin/python uji/jalankan-semua.py
```
Hasil: 6 rangkaian, 0 gagal. `uji_beranda` memeriksa aturan pengaturan (17 kasus ditolak, termasuk URL yang mencoba
keluar dari `url("...")` CSS), kontras keempat jenis latar untuk 9 palet dan 12 warna fakultas, ukuran dan titik fokus
potongan foto, serta hasil bangun tiga prodi contoh (foto, kuning, dan pengaturan yang tidak sah).

Diperiksa di browser dengan data contoh lokal: S1 Teknik Informatika dengan foto latar terang dan ramai (teks tetap
terbaca), S1 Ilmu Politik dengan warna pilihan, label kartu diganti, kartu SKS disembunyikan, dan satu kartu tambahan,
Profesi Dokter dengan warna utama penuh; tampilan ponsel memakai potongan 4:3 tanpa gulir horizontal.

## Catatan untuk langkah 6 (formulir admin prodi)
- Tampilkan `media.PETUNJUK_HERO`, pratinjau hasil potongan 3:1 dan 4:3, dan pilihan titik fokus.
- Pemilih warna dengan pesan kontras langsung (pesan yang sama dengan `tampilan_prodi.periksa`).
- Kartu resmi: hanya label/urutan/tampil; tampilkan nilainya sebagai teks tetap dengan keterangan "dari data resmi".
