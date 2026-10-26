# Fase 2 · Langkah 1 — Model data dan templat isi halaman (27 Oktober 2026)

Branch: `fase/02-1-isi` (bercabang dari `fase/02-0-rencana`). Rencana: [rencana Fase 2](../rencana-fase-02.md) §3–§4,
keputusan K-P23.

## Yang dikerjakan
- **`platform/isi_halaman.py`**: isi halaman milik prodi (22 halaman wajib + 2 opsional).
  - **Templat isi** untuk ke-24 halaman, sesuai rencana §3.3. Setiap halaman berisi bagian-bagian (paragraf, daftar,
    tabel, kartu, dokumen, galeri foto, tautan) dan diakhiri bagian tambahan bebas.
    - Kosakata simpulnya sama dengan penyunting superadmin www (`teks`, `bilangan`, `url`, `pilihan`, `objek`,
      `daftar`, ditambah `persen`, `centang`, `dokumen`, `foto`), supaya `editor.py` www bisa diadaptasi di langkah 2.
  - **Pemeriksaan** (`periksa`): wajib diisi, panjang, tahun 1900–2100, persen 0–100 (dua desimal), pilihan, tautan
    hanya `https://`, markah teks hanya tautan `https://` dan huruf tebal, tanpa karakter kendali, saringan judi.
    - Berkas PDF dan foto harus berkas prodi itu sendiri; foto wajib berteks alternatif.
    - Setiap masalah menyebut tempatnya, mis. "Daftar kerja sama baris 1, Mitra: wajib diisi".
    - Kunci yang tidak dikenal templat disimpan, sehingga perubahan templat setelah pilot tidak menghapus isi.
  - **Tampilan** (`tampilan`): data bagian untuk generator. Teks di-escape di sini; hanya markah terbatas yang menjadi
    HTML: paragraf, daftar "- ", tautan, huruf tebal, dan alamat `https://`. Angka ditulis dengan pemisah ribuan.
    - Berkas yang hilang dihitung. Dokumen dan foto yang wajib melewatkan butirnya, sedangkan berkas opsional (bukti
      kerja sama, SOP laboratorium) hanya dilewatkan berkasnya.
  - **Penyimpanan** di `data/prodi/<kode>/halaman-<id>.json`: `terbit`, `draf` (dipakai mulai langkah 3), dan
    `versi`.
    - Setiap simpanan masuk riwayat. Simpanan dari versi lama ditolak ("baru saja diubah orang lain"), dan isi yang
      gagal diperiksa tidak menulis apa pun.
    - `tarik` mengembalikan halaman ke "sedang dilengkapi".
  - **Baris perintah** (sebelum penyunting ada): `daftar`, `contoh` (isi bertanda `[CONTOH]` hanya ke halaman kosong,
    ditolak di produksi), dan `tarik`.
- **Generator dan templat situs**:
  - `isi.html` menampilkan isi bila ada; bila belum, tetap deskripsi + "sedang dilengkapi".
  - `_isi.html` berisi makro untuk setiap jenis bagian:
    - tabel ber-`caption`, `th scope="col"`, dan wadah gulir yang bisa dicapai keyboard;
    - kartu dengan urutan judul h2 → h3 → h4;
    - dokumen dengan jumlah halaman, ukuran, dan tahun;
    - galeri dengan teks alternatif dan keterangan.
  - Berkas yang dirujuk diterbitkan lewat `terbitkan_media`. Isi yang gagal diperiksa tidak ditampilkan sama sekali,
    disertai peringatan bangun.
  - CSS-nya ada di bagian "a programme's own pages" di `prodi.css`.
- **Riwayat** menamai berkas isi halaman dengan nama halamannya ("S1 Teknik Informatika — halaman Sejarah").

## Verifikasi
```bash
.venv/bin/python uji/jalankan-semua.py
```
Hasil: 14 rangkaian, 0 gagal. Rangkaian baru `uji/uji_isi_halaman.py` memeriksa:
- **templat:** tepat satu untuk setiap halaman wajib/opsional di menu induk (22 wajib), bentuknya sah, dan bagian
  tambahan ada di akhir;
- **isi contoh:** isi contoh ke-24 halaman (dengan PDF dan foto sungguhan maupun tanpa berkas) lolos pemeriksaan dan
  tampil; isi kosong sah dan tidak tampil;
- **nilai salah ditolak, masing-masing dengan tempatnya:** 12 macam pada baris tabel, persen, tautan (`http://`,
  `javascript:`, spasi, tanda kutip, terlalu panjang, `//`), markah, foto tanpa teks alternatif atau milik prodi lain,
  dan PDF milik prodi lain atau berjalur aneh;
- **markah:** skrip, atribut, label tautan ber-HTML, dan `javascript:` tidak pernah menjadi HTML;
- **penyimpanan:** versi, simpanan saling menimpa ditolak, riwayat, tarik;
- **situs:**
  - semua bagian ke-24 halaman tampil; tabel 80 mata kuliah; angka `1.234.567`, persen `42,5%`;
  - escaping di sel tabel, judul kartu, dan paragraf;
  - PDF dan foto diterbitkan; berkas hilang; isi rusak tidak tampil; halaman opsional disembunyikan; halaman ditarik;
  - bangun satu prodi; pemeriksaan halaman bersama dan cek integritas bersih;
- **baris perintah.**

Uji mutasi (setiap aturan dimatikan sementara):

| Aturan yang dimatikan | Uji yang gagal |
|---|---|
| Escaping sel tabel | 7 |
| Escaping teks berpenanda | 10 |
| Alamat `http://` diizinkan | 2 |
| Berkas prodi lain diizinkan | 2 |

Diperiksa di browser (isi contoh dengan foto dan PDF, satu prodi):
- desktop: tabel kerja sama, kartu laboratorium, daftar visi-misi;
- ke-38 halaman prodi itu dimuat pada lebar 320 px.

**Ditemukan dan diperbaiki:** pada 320 px, halaman kurikulum dan kerja sama melebar hingga 558 px dan 766 px.
Penyebabnya teks tersembunyi untuk pembaca layar di tautan PDF dalam sel tabel (`.tersembunyi`, berposisi absolut)
yang lolos dari wadah gulir. `.tabel-gulir` kini menjadi wadah posisinya, dan ke-38 halaman tidak lagi bergulir ke
samping.

## Perlu diketahui
- Belum ada formulir: isi baru bisa dibuat lewat kode atau baris perintah `contoh`. Penyunting di admin adalah
  langkah 2, dan alur ajukan/terbitkan beserta kelengkapan di dasbor adalah langkah 3.
- Tabel lebar (kerja sama, 8 kolom) bergulir di dalam wadahnya di ponsel. Barisnya tinggi karena kolom sempit
  membungkus teks. Bentuk "kartu per baris" untuk layar sempit bisa dipertimbangkan bila pilot memintanya.
- Templat isi adalah draf rencana §3.3, dan akan disempurnakan dengan masukan pilot.

## Langkah berikutnya
Langkah 2 — penyunting di admin: formulir dari templat (adaptasi `editor.py` www), daftar dan tabel tanpa JavaScript,
unggah PDF dan foto, pratinjau, simpan draf.
