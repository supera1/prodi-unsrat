---
version: 1
slug: "platform-template-halaman-akar-html"
primary_target: "platform/template/halaman/akar.html"
related_targets: []
---

# Direktori akar prodi.unsrat.ac.id

Scope: halaman akar `prodi.unsrat.ac.id/` saja (template `akar.html`); situs ke-97 prodi tidak berubah.
Mode: Operate. Visitor job: menemukan satu prodi di antara 97, terutama dengan mengetik namanya, lalu masuk ke situsnya.
Audience: campuran merata (calon mahasiswa, mahasiswa, alumni, asesor, pengguna lulusan); banyak ponsel, koneksi terbatas.
Content per prodi visible without opening: nama, jenjang, gelar lulusan, akreditasi (data www apa adanya; "belum" tidak tampil sebagai lencana).
Constraints: lambang UNSRAT dan warna bendera fakultas wajib; WCAG 2.1 AA; tetap berfungsi tanpa JavaScript (daftar lengkap selalu ada, pencarian hanya penyaring progresif dari berkas JS sendiri); CSP tanpa skrip dan gaya inline; tanpa carousel; 320 px tanpa scroll horizontal.
Must not feel like: tabel kantor (padat, kaku, sulit dipindai).

## Direction contract

THESIS: Direktori sebagai peta jalur: setiap fakultas satu jalur berwarna benderanya, setiap prodi satu halte, dan kotak cari adalah tujuan. Menolak susunan bawaan kategori: pahlawan, chip saringan, lalu kisi kartu.

OWN-WORLD: Dasar putih, tinta indigo tua; warna bendera fakultas hanya sebagai garis jalur tebal dan pita kepala jalur berwarna penuh dengan teks warna tulisan benderanya (bendera putih atau sangat terang mendapat rel bergaris tepi); halte lingkaran putih bercincin tinta; Overpass (keluarga huruf rambu jalan) dengan Overpass Mono untuk kode jenjang dan angka; akreditasi sebagai tag bergaris atau terisi tinta. Tidak ada warna lain di luar bendera, dasar, dan tinta.

STORY: Pengunjung langsung melihat bahwa ia bisa mengetik nama prodi; melihat 97 prodi di 12 jalur; menyaring dengan mengetik atau melompat lewat lencana jalur; membaca jenjang, gelar, dan akreditasi tanpa membuka; lalu membuka situs prodi lewat nama halte.

FIRST VIEWPORT: Bilah atas: lambang, "Program Studi" dan "Universitas Sam Ratulangi", tautan www.unsrat.ac.id. Lalu judul "Pencarian Program Studi" (revisi pengguna 27 November 2026; semula "Mau ke program studi mana?") dengan kotak cari lebar ±720 px (aksi utama) dan angka 97 besar di kanan. Lalu deretan 12 lencana jalur (singkatan fakultas + jumlah, warna bendera) sebagai tautan lompat. Lalu jalur-jalur: empat kolom di desktop, satu kolom di ponsel; tiap jalur berpita kepala warna penuh dan halte berisi nama, gelar, dan tag akreditasi di kolom tetap; pergantian jenjang ditandai label mono kecil di jalur. Signature: halte pada garis jalur berwarna bendera. Signature interaction: mengetik menyaring halte, jalur yang kosong runtuh dan lencananya meredup; bila tinggal satu prodi, haltenya membesar menjadi panel tiba dengan satu tombol besar "Buka situs". Motion grammar: halte yang cocok menyala sesaat; tanpa gerak bila prefers-reduced-motion.

FORM: Peta jalur fakultas, posisi 4 dari tujuh calon arah yang diurutkan; seed: cb2df9ad24ff7604.
Raises: (dari ubin metro) warna bendera mengisi seluruh pita kepala jalur sebagai bidang penuh; (dari dompet tiket) kolom tetap: jenjang, nama, gelar, akreditasi selalu di posisi yang sama; (dari satu prodi satu layar) panel tiba saat pencarian tinggal satu; (dari medan data) dua tinta saja di luar warna jalur.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

Chosen sketch: .impeccable/mocks/decision/assigned.html (code-led).
Unresolved: urutan jalur (menurut jumlah prodi atau urutan fakultas di www); penempatan Program Pascasarjana (29 prodi S2/S3) sebagai jalur terpanjang.
