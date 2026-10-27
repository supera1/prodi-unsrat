# Persiapan pilot Fase 2 — tiga prodi di staging

**Status (27 Oktober 2026):** aplikasinya siap. Pilot menunggu staging tayang (admin VM, [docs/deploy.md](deploy.md))
dan dua prodi pilot dari pengguna. Rencana: [rencana Fase 2](rencana-fase-02.md) §6; keputusan K-P26.

Panduan untuk peserta: [docs/panduan-admin-prodi.md](panduan-admin-prodi.md), juga terbuka di admin lewat menu
**Panduan**. Dokumen ini untuk superadmin UPA TIK dan pengguna yang memimpin pilot.

## Prodi pilot

Tiga prodi dengan jenjang, fakultas, dan lembaga akreditasi berbeda, dan koordinatornya siap (rencana §6).

| No | Prodi | Jenjang · fakultas · lembaga (data www) | Alamat staging | Admin prodi | Operator |
|---|---|---|---|---|---|
| 1 | S1 Teknik Informatika (55201) | S1 · Fakultas Teknik · LAM-Infokom | `/s1informatika/` | (diisi) | (diisi) |
| 2 | (menunggu pengguna) | | | | |
| 3 | (menunggu pengguna) | | | | |

## Sebelum pilot

Dikerjakan superadmin UPA TIK, bersama admin VM untuk butir 1.

1. **Staging tayang.** Pemeriksaan di `docs/deploy.md` §5 sudah dijalankan: situs staging menampilkan pita "Pratinjau
   staging", admin terbuka dari jaringan UNSRAT (dari luar jaringan 403), kontainer *healthy*, dan pemantau mencatat
   0 temuan. Sudah ada minimal dua akun superadmin.
2. **Data www terbaru diunggah** di menu **Data www** (pratinjau, lalu terapkan).
3. **Prodi pilot siap** di menu **Prodi**: aktif, slugnya benar, dan tautan dosennya terisi. Kesiapan per prodi terlihat
   di Ringkasan prodi, bagian **Kesiapan situs**.
4. **Akun.** Untuk setiap prodi pilot, buat satu akun admin prodi (koordinator) dan satu atau dua operator di menu
   **Akun** → buat akun (peran, prodi). Setelah itu admin prodi juga bisa membuat operatornya sendiri.
   - Kata sandi sementara hanya tampil sekali di layar. Sampaikan langsung atau lewat telepon kepada pemiliknya, jangan
     lewat grup percakapan atau surel.
   - Saat pertama masuk, setiap pengguna wajib membuat kata sandinya sendiri.
5. **Uji masuk.** Pastikan setiap peserta bisa membuka admin dari tempat kerjanya (jaringan kampus atau VPN) sebelum sesi
   pengenalan.
6. **Label kriteria** tetap draf sampai LPMPP mengonfirmasi ([docs/kriteria-akreditasi.md](kriteria-akreditasi.md)).
   Ini tidak menghalangi pilot.

## Sesi pengenalan (±90 menit)

Lebih baik dilakukan langsung di depan komputer peserta, dengan staging terbuka.

| Waktu | Materi |
|---|---|
| 10 menit | Masuk, membuat kata sandi, peran admin prodi dan operator |
| 10 menit | Keliling admin: Ringkasan, Isi halaman, Panduan, Masukan |
| 25 menit | Praktik bersama halaman **Sejarah**: paragraf, dua baris linimasa, satu foto dengan teks alternatif; simpan draf, pratinjau |
| 20 menit | Alur: operator mengajukan → admin prodi mengembalikan dengan catatan → operator memperbaiki dan mengajukan lagi → admin prodi menerbitkan; lihat hasilnya di situs staging |
| 10 menit | Riwayat halaman: menjadikan versi lama sebagai draf; menarik dari situs |
| 15 menit | Data pribadi dan keamanan, cara mengirim masukan, target pilot, tanya jawab |

## Masa pengisian

Usul tiga minggu; pengguna yang menentukan.

- **Target per prodi:** paling sedikit 15 dari 22 halaman wajib terbit, tanpa bantuan pengembang (rencana §6).
- **Setiap minggu (superadmin):**
  - unduh CSV di menu **Kelengkapan** dan simpan, sebagai catatan kemajuan;
  - baca **Masukan pengguna** dan tanggapi setiap masukan: ditindaklanjuti atau ditunda, dengan tanggapan yang dibaca
    pengirimnya;
  - periksa acak beberapa halaman yang baru terbit: tidak ada data pribadi, tidak ada isi aneh.
- **Perbaikan dari masukan** dikerjakan pengembang per langkah kecil (`fase/02-6a-…`, `fase/02-6b-…`), dan setiap
  langkah ditinjau sebelum dipasang di staging.

## Ukuran keberhasilan dan cara melihatnya

| Ukuran (rencana §6) | Cara melihat |
|---|---|
| Setiap prodi pilot menerbitkan ≥15 dari 22 halaman wajib | Menu **Kelengkapan**, kolom "Wajib terbit"; CSV mingguan |
| Tanpa bantuan pengembang | Masukan berjenis Kendala yang memerlukan pengembang, dan catatan sesi |
| Tidak ada masalah keamanan atau data pribadi yang tayang | Pemeriksaan acak mingguan dan laporan pemantau integritas |
| Setiap masukan tercatat dan ditindaklanjuti atau ditunda | **Masukan pengguna**: di akhir pilot tidak ada lagi yang berstatus Baru; CSV masukan |

## Sesudah pilot

- Pengembang menulis ringkasan hasil di `docs/log/fase-02-pilot.md`:
  - angka kelengkapan per prodi;
  - masukan per jenis beserta statusnya;
  - perubahan templat isi yang diusulkan.
- Templat isi bisa direvisi tanpa menghapus isi yang sudah ada, karena kunci yang tidak dikenal templat tetap disimpan
  (K-P23).
- Uji penerimaan Fase 2 (`uji/uji_fase2.py`) dan log fase ditulis di langkah 8.
