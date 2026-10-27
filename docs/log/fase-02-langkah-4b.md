# Fase 2 langkah 4b — Label kriteria akreditasi diisi admin prodi (K-P33)

Tanggal: 27 Oktober 2026. Branch: `fase/02-4b-kriteria-admin`.

## Latar
Pengguna memutuskan label kriteria tidak menunggu konfirmasi LPMPP: admin prodi mengisi dan memperbaruinya sendiri.
Sebelumnya (K-P25, K-P29) label hanya tampil untuk lembaga yang dikonfirmasi LPMPP di `platform/template/kriteria.json`,
dan belum ada satu pun. Ketiga prodi pilot (LAM-Infokom, LAM-PTKes, LAM-Teknik) tidak akan punya label selama pilot.

## Yang dikerjakan
- **Menu prodi "Kriteria akreditasi"** (`platform/admin/kriteria_admin.py`, `templates/prodi_kriteria.html`):
  - nama lembaga (terisi dari data resmi) dan instrumen (opsional);
  - daftar kriteria, paling banyak 20 (nomor dan nama), tiga baris kosong untuk tambahan, tanpa JavaScript;
  - tabel centang halaman × kriteria, per kelompok menu; halaman opsional yang disembunyikan diberi tanda;
  - **Isi formulir dari usulan**: lembaga di berkas bersama yang punya daftar kriteria (sekarang draf BAN-PT IAPS 4.0).
    Formulir terisi, tetapi belum ada yang disimpan;
  - **Kosongkan kriteria**: label hilang dari situs, versi sebelumnya di Riwayat;
  - admin prodi dan superadmin mengubah; operator melihat tanpa formulir.
- **Data:** `data/prodi/<kode>/kriteria.json`, lewat `lokasi.tulis` (riwayat prodi, "kriteria akreditasi"), dicatat di log
  audit, lalu situs prodi dibangun ulang.
- **Pemeriksaan** (`kriteria.periksa_prodi`): nama lembaga 1–60 karakter, instrumen ≤150, nomor kriteria unik
  (`[0-9A-Za-z.]{1,8}`), nama kriteria 1–150, tanpa `< >` dan karakter kendali, tanpa teks spam (judi, pinjol, ijazah,
  obat); halaman yang dicentang harus halaman templat dan nomor yang ada. Centang untuk nomor yang diubah atau dihapus
  dibuang saat menyimpan.
- **Situs** (`kriteria.untuk_prodi`): kriteria prodi didahulukan; bila kosong, lembaga yang dikonfirmasi di berkas
  bersama (K-P29); bila tidak ada, tanpa label. Kriteria prodi yang rusak (mis. diubah di luar admin) tidak tampil dan
  generator mencatat peringatan. Baris instrumen di halaman Akreditasi hanya tampil bila diisi.
- **Penyunting isi halaman** menampilkan label yang sama dengan situs.
- **Kelengkapan superadmin**: kolom "Kriteria akreditasi" (jumlah kriteria) di layar dan `kriteria_akreditasi` di CSV.
- **Dokumen:** K-P33 (K-P25 dan K-P29 diberi catatan), panduan admin prodi (bagian baru "Kriteria akreditasi"),
  `docs/kriteria-akreditasi.md`, `docs/pilot-fase-02.md`, rencana Fase 2 §3.7 dan §8, CLAUDE.md, keterangan di
  `kriteria.json`.

## Uji
- `.venv/bin/python uji/jalankan-semua.py`: 19 rangkaian lulus.
- `uji_akreditasi.py` menambah: pemeriksaan berkas kriteria prodi (9 kasus ditolak, tepat 20 kriteria diterima),
  penolakan teks spam tanpa menyimpan, label prodi saat berkas bersama masih draf dan saat ada lembaga yang
  dikonfirmasi, berkas rusak, alur admin (usulan tanpa simpan, nomor ganda, teks judi, simpan, label di penyunting,
  operator hanya melihat dan ditolak menyimpan, CSV kelengkapan, kosongkan, riwayat).
- `uji_admin.py`: 4 rute baru di matriks peran × rute. `uji_pilot.py`: menu baru disebut panduan dan tampil di admin.
- **Uji mutasi:** 11 aturan baru dimatikan satu per satu; setiap kali ada uji yang gagal.

  | Mutasi | Uji yang gagal |
  |---|---|
  | kriteria prodi diabaikan generator | 6 |
  | tanpa saringan spam | 4 |
  | nomor ganda diterima | 2 |
  | batas 20 kriteria | 1 |
  | operator mendapat formulir | 1 |
  | operator boleh menyimpan | 2 |
  | centang nomor yang hilang ikut disimpan | 7 |
  | usulan langsung disimpan | 3 |
  | kriteria prodi rusak tanpa peringatan | 1 |
  | kelengkapan tanpa jumlah kriteria | 1 |
  | baris instrumen kosong tampil | 1 |

- **Dilihat di browser** (cuplikan dari platform sementara, desktop dan 375 px): formulir, tabel centang, tampilan
  operator, dan peta kriteria di halaman Akreditasi; tanpa scroll horizontal halaman.

## Catatan
- Kriteria LAM tidak diisi pengembang; admin prodi mengetiknya dari instrumen lembaganya. Bila LPMPP mengirim daftar LAM,
  daftar itu bisa ditambahkan ke berkas bersama sebagai usulan.
- Tidak ada paket Python baru, variabel stack baru, atau migrasi data.
