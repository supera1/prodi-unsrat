# Fase 2 · Langkah 4 — Dokumen Akreditasi dan label kriteria (27 Oktober 2026)

Branch: `fase/02-4-akreditasi` (bercabang dari `fase/02-3-alur`). Rencana: [rencana Fase 2](../rencana-fase-02.md) §3.7,
keputusan K-P25, K-P28 (disetujui), dan **K-P29 (baru, menunggu tinjauan)**.

## Yang dikerjakan
- **Dokumen Akreditasi** (K-P29) menjadi bagian dokumen di halaman **Akreditasi** yang sudah ada (`profil/akreditasi`),
  bukan halaman baru. Templat Fase 1 halaman itu memang sudah menjanjikan "Sertifikat akreditasi sedang dilengkapi oleh
  Program Studi".
  - **Templat isi `akreditasi`** (`platform/isi_halaman.py`):
    - daftar dokumen (judul, tahun, keterangan, PDF wajib; paling banyak 20), dengan petunjuk: sertifikat, SK, dan
      ringkasan hasil yang boleh dipublikasikan, tanpa LED, LKPS, atau dokumen berdata pribadi;
    - keterangan dan bagian tambahan.
  - **Di situs**: status resmi tetap di atas (dari data www), lalu dokumen, lalu keterangan. Tanpa dokumen, catatan
    "Sertifikat akreditasi sedang dilengkapi" tetap tampil.
  - **Di admin**: halaman Akreditasi masuk daftar Isi halaman dengan jenis "Pelengkap" dan memakai alur K-P24 seperti
    halaman lain. Penyuntingnya menyebut status resmi yang tampil otomatis (diubah lewat Data prodi, bukan di sini).
    Hitungan halaman wajib tetap 22; di CSV kelengkapan kolomnya "Akreditasi (pelengkap)".
  - Deskripsi halaman di menu induk: "… beserta sertifikat dan SK akreditasinya."
- **Label kriteria akreditasi** (`platform/template/kriteria.json`, `platform/kriteria.py`, K-P25, K-P29):
  - **Isi berkas, per lembaga**: nama, instrumen, daftar kriteria, pemetaan halaman → kriteria, dan alias, yaitu nilai
    `lembaga_akreditasi` di data resmi yang berarti lembaga itu.
  - **Pemeriksaan**: id, nama tanpa markah, alias yang hanya diklaim satu lembaga (huruf besar-kecil dan spasi
    diabaikan), halaman dan nomor kriteria yang ada. Lembaga yang dikonfirmasi wajib menyebut oleh siapa dan
    tanggalnya.
  - **Hanya lembaga berstatus `dikonfirmasi` yang tampil.** Draf tidak pernah tampil, baik di situs maupun di
    penyunting. Berkas yang rusak tidak memunculkan label apa pun dan menimbulkan peringatan bangun.
  - **Draf yang disiapkan**: BAN-PT (IAPS 4.0, 9 kriteria) dengan usulan pemetaan 23 halaman. Tujuh LAM (LAM-PTKes,
    LAM-SPAK, LAMEMBA, LAM Teknik, LAMSAMA, LAM-Infokom, LAM-PTIP) hanya didaftar nama dan aliasnya, tanpa kriteria,
    supaya tidak ada yang dikarang.
  - **Tampilan setelah dikonfirmasi**:
    - halaman yang dipetakan menyebut kriterianya di bawah judul ("Kriteria akreditasi BAN-PT: Kriteria 3, Mahasiswa;
      Kriteria 9, Luaran dan Capaian Tridharma");
    - halaman Akreditasi memuat "Halaman menurut kriteria akreditasi BAN-PT", dengan tautan ke halaman yang ada di situs
      prodi itu (halaman opsional yang disembunyikan tidak ikut);
    - penyunting admin juga menyebut kriterianya.
  - **Baris perintah**: `python3 platform/kriteria.py periksa | tabel`.
- **[Panduan untuk LPMPP](../kriteria-akreditasi.md)** (`docs/kriteria-akreditasi.md`): tujuannya, apa yang diminta dari
  LPMPP, nilai lembaga di data www yang perlu diputuskan, cara menyalakan label, dan tabel pemetaan sekarang. Uji
  memastikan tabel itu sama dengan isi berkas.

## Verifikasi
```bash
.venv/bin/python uji/jalankan-semua.py
```
Hasil: 17 rangkaian, 0 gagal. Rangkaian baru `uji/uji_akreditasi.py` memeriksa:
- **`kriteria.json` di repo**: sah, draf BAN-PT berisi 9 kriteria, dan `docs/kriteria-akreditasi.md` memuat tabelnya
  yang sekarang;
- **15 bentuk berkas yang salah ditolak**, termasuk alias ganda, halaman tidak dikenal (mis. "keuangan"), markah di
  nama, dan lembaga yang dikonfirmasi tanpa nama pengonfirmasi atau tanggal;
- **lembaga sebuah prodi**: alias LAM-Tek/LAM-Teknik; huruf dan spasi diabaikan; draf, nilai kosong,
  `BAN-PT / LAM-PTIP`, dan lembaga tak dikenal tanpa label;
- **situs tiga prodi** (BAN-PT, LAM-Tek, kosong):
  - selama semua draf, tidak ada label maupun peta di 70+ halaman;
  - setelah dikonfirmasi: label di halaman yang dipetakan (dua kriteria pada satu halaman), tidak ada di halaman tanpa
    kriteria; peta di halaman Akreditasi dengan tautan dan tanpa halaman yang disembunyikan; nama kriteria di-escape;
    prodi berlembaga kosong tanpa apa pun;
  - dokumen akreditasi di bawah status resmi (urutan: status, dokumen, peta), dan catatan sertifikat bila belum ada
    dokumen;
  - pemeriksaan halaman bersama;
  - berkas rusak atau bukan JSON: tidak ada label, ada peringatan;
- **admin**: daftar halaman (akreditasi sebagai pelengkap), penyunting akreditasi menyebut status resmi, label di
  penyunting hanya setelah dikonfirmasi, kolom CSV kelengkapan dengan 22 halaman wajib tetap.

Rangkaian lama disesuaikan:
- `uji_isi_halaman.py`: templat isi = halaman wajib/opsional + akreditasi;
- `uji_penyunting.py` dan `uji_admin.py`: halaman tanpa templat isi kini dicontohkan dengan kalender akademik.

Uji mutasi (setiap aturan dimatikan sementara):

| Aturan yang dimatikan | Uji yang gagal |
|---|---|
| Draf tidak pernah tampil | 25 |
| Label di halaman wajib | 3 |
| Alias tanpa peduli huruf dan spasi | 1 |
| Halaman yang tidak dikenal ditolak | 2 |
| Berkas rusak tidak dipakai generator | 2 |
| Dokumen di halaman Akreditasi | 1 (bangun berhenti: `isi_bagian` tidak terdefinisi) |
| Halaman tersembunyi tidak ikut di peta | 2 (juga tautan mati di pemeriksaan halaman) |
| Penyunting: label hanya setelah dikonfirmasi | 1 |
| Nama tanpa markah | 2 |

Diperiksa di browser (situs contoh dengan BAN-PT dikonfirmasi hanya di salinan sementara `kriteria.json`; berkas repo
tetap draf):
- halaman Akreditasi: status resmi, dua dokumen, keterangan, peta 9 kriteria;
- label dua kriteria di Organisasi dan Prestasi;
- penyunting Akreditasi dan daftar halaman di admin;
- ketujuh halaman pada 320 px tanpa gulir ke samping.

## Perlu diketahui
- **K-P29** memindahkan "halaman Dokumen Akreditasi" (rencana §3.7: "misalnya `profil/dokumen-akreditasi`") ke halaman
  Akreditasi yang sudah ada. Mohon ditinjau. Bila Anda tetap ingin halaman terpisah, templatnya tinggal dipindah ke id
  baru di menu induk.
- **Label belum tampil di mana pun**: semua lembaga masih draf. Untuk menyalakannya diperlukan:
  - konfirmasi atau koreksi LPMPP atas pemetaan BAN-PT;
  - daftar kriteria setiap LAM;
  - keputusan untuk 3 prodi bertanda `BAN-PT / LAM-PTIP` dan 7 prodi tanpa lembaga (diperbaiki di data www).

  Semua ini tercantum di [docs/kriteria-akreditasi.md](../kriteria-akreditasi.md), yang bisa diteruskan ke LPMPP.
- Pemetaan BAN-PT adalah usulan pengembang untuk diperiksa, bukan ketentuan BAN-PT. Contohnya, Survei Kepuasan saya
  petakan ke Kriteria 9; LPMPP mungkin menambahkan Kriteria 3 atau 6 untuk survei mahasiswa.

## Langkah berikutnya
Langkah 5 — panduan admin prodi dan persiapan pilot (`docs/panduan-admin-prodi.md`; akun prodi pilot dibuat
superadmin di staging). Langkah 5–6 menunggu staging tayang dan dua prodi pilot dari Anda.
