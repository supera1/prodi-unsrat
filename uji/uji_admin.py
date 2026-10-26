# -*- coding: utf-8 -*-
"""Step 4 of phase 1: accounts, roles and the admin's access rules (platform/admin/akun.py, audit.py, app.py).

Runs the admin with Flask's test client on a temporary data and secrets folder:
- password rules and account rules (akun.py);
- the network allow-list, CSRF, login lockout per address and per user name, the forced change of a temporary
  password, sessions that end on a new password, a reset, a deactivation, or after 12 hours;
- the access matrix: every route, tried by every role and by accounts of other programmes. The suite fails when a
  route of the admin is missing from the matrix, so a new route cannot go untested;
- temporary passwords never reach the audit log or the session cookie.

Needs the packages of platform/admin/requirements.txt: run with .venv/bin/python.
"""
from __future__ import print_function

import io
import json
import os
import re
import shutil
import sys
import tempfile
import time

AKAR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for sub in ("platform", "platform/admin", "platform/pemantau"):
    sys.path.insert(0, os.path.join(AKAR, *sub.split("/")))

try:
    import flask  # noqa: F401
except ImportError:
    print("uji_admin: paket admin belum terpasang; jalankan dengan .venv/bin/python (lihat README)")
    sys.exit(1)

KERJA = tempfile.mkdtemp(prefix="prodi-uji-admin-")
for nama, sub in (("PRODI_DATA", "data"), ("PRODI_RIWAYAT", "riwayat"), ("PRODI_RAHASIA", "rahasia"), ("PRODI_LOG", "log"),
                  ("WWW_DATA", "www-tidak-ada")):        # never the real www data next to this repository
    os.environ[nama] = os.path.join(KERJA, sub)

import akun  # noqa: E402
import app as app_mod  # noqa: E402
import audit  # noqa: E402
import lokasi  # noqa: E402

IP = "103.84.116.10"
A, B = "55201", "20201"
SANDI = {"super": "Biru laut 7 menara pagi", "admin": "Kopi hangat 42 senja", "operator": "Hujan 9 jendela kayu"}
gagal = []


def cek(kondisi, pesan):
    if not kondisi:
        gagal.append(pesan)


def harus_gagal(fungsi, pesan, *args, **kw):
    try:
        fungsi(*args, **kw)
    except akun.GagalAkun as e:
        return e
    gagal.append(pesan)


# ------------------------------------------------------------------ data

lokasi.tulis_json(lokasi.path_data("warisan/prodi"), {"program": [
    {"kode_pddikti": A, "nama": "Teknik Informatika", "jenjang": "S1", "unit": "Fakultas Teknik"},
    {"kode_pddikti": B, "nama": "Teknik Elektro", "jenjang": "S1", "unit": "Fakultas Teknik"}]})
lokasi.tulis_json(lokasi.path_data("registri"), {"prodi": [
    {"kode_pddikti": A, "slug": "s1informatika", "slug_lama": [], "aktif": True},
    {"kode_pddikti": B, "slug": "s1elektro", "slug_lama": [], "aktif": True}]})

try:
    # --- password rules
    p = akun.periksa_sandi
    cek(p("Biru laut 7 menara pagi", "super") == [], "sandi kuat diterima: %r" % p("Biru laut 7 menara pagi", "super"))
    cek(p("Kopi hangat 42 senja", "admin") == [], "sandi kuat admin diterima")
    for sandi, peran, label in (("Pendek1", "admin", "terlalu pendek"), ("hanyahurufpanjangsekali", "admin", "tanpa angka"),
                                ("123456789012345", "admin", "tanpa huruf"), ("Password12345678", "admin", "umum"),
                                ("UnsratJaya2026!!", "admin", "memuat unsrat"), ("aaaaaa111111aaaa", "admin", "berulang"),
                                ("Kopi hangat 42", "super", "terlalu pendek untuk superadmin"),
                                ("qwerty-2026-kopi!", "admin", "pola papan ketik")):
        cek(p(sandi, peran), "sandi %s harus ditolak" % label)
    cek(p("budi.santoso 2026 x", "admin", nama="budi.santoso"), "sandi memuat nama pengguna ditolak")
    cek(p("Santoso 99 kebun teh", "admin", nama_lengkap="Budi Santoso"), "sandi memuat nama lengkap ditolak")
    cek(p("Informatika 99 kebun teh", "admin", prodi=[A]), "sandi memuat nama prodi ditolak")
    cek(not p("Informatika 99 kebun teh", "admin", prodi=[B]), "nama prodi lain tidak dilarang")
    t = akun.buat_sandi_sementara()
    cek(not p(t, "super") and re.match(r"^[a-z2-9]{5}(-[a-z2-9]{5}){3}$", t), "sandi sementara kuat dan terbaca: %s" % t)

    # --- accounts
    super_id, s_sementara = akun.buat(None, "superuji", "Super Uji", "super")
    super_ = akun.ambil(super_id)
    cek(super_["wajib_ganti"] and super_["prodi"] == [], "akun baru wajib ganti sandi")
    cek(akun.verifikasi("superuji", s_sementara)["id"] == super_id, "sandi sementara bisa dipakai masuk")
    cek(akun.verifikasi("SuperUji ", s_sementara) is not None, "nama pengguna tidak peka huruf besar dan spasi")
    cek(akun.verifikasi("superuji", "salah") is None and akun.verifikasi("tidakada", "x") is None, "sandi/nama salah ditolak")
    cek(akun.verifikasi("' OR 1=1 --", "x") is None, "injeksi SQL di nama pengguna tidak berpengaruh")
    with open(akun.path_db(), "rb") as f:
        cek(s_sementara.encode() not in f.read(), "sandi tidak tersimpan dalam teks biasa")
    cek(oct(os.stat(akun.path_db()).st_mode & 0o777) == "0o600", "basis data akun hanya bisa dibaca pemiliknya")
    harus_gagal(akun.buat, "nama ganda ditolak", super_, "superuji", "X Y", "super")
    harus_gagal(akun.buat, "nama tidak sah ditolak", super_, "Budi Santoso", "Budi", "operator", [A])
    harus_gagal(akun.buat, "admin tanpa prodi ditolak", super_, "adm", "Admin X", "admin", [])
    harus_gagal(akun.buat, "superadmin dengan prodi ditolak", super_, "sup2", "Super Dua", "super", [A])
    harus_gagal(akun.buat, "prodi tak terdaftar ditolak", super_, "opx", "Op X", "operator", ["99999"])
    harus_gagal(akun.buat, "nama lengkap ber-HTML ditolak", super_, "opy", "<b>Op</b>", "operator", [A])

    def siapkan(nama, peran, prodi, pelaku=None):
        id_, sementara = akun.buat(pelaku or super_, nama, "%s Uji" % nama.capitalize(), peran, prodi)
        akun.ganti_sandi(id_, sementara, SANDI[peran])
        return akun.ambil(id_)
    adm_a, adm_b = siapkan("adma", "admin", [A]), siapkan("admb", "admin", [B])
    op_a = siapkan("opa", "operator", [A], pelaku=adm_a)
    op_b, op_ab = siapkan("opb", "operator", [B]), siapkan("opab", "operator", [A, B])
    harus_gagal(akun.buat, "admin prodi tidak bisa membuat admin", adm_a, "adm3", "Adm Tiga", "admin", [A])
    harus_gagal(akun.buat, "admin prodi tidak bisa membuat operator prodi lain", adm_a, "op3", "Op Tiga", "operator", [B])
    cek(akun.boleh_kelola(adm_a, op_a) and not akun.boleh_kelola(adm_a, op_ab) and not akun.boleh_kelola(adm_a, adm_b)
        and not akun.boleh_kelola(adm_a, super_) and not akun.boleh_kelola(op_a, op_a), "aturan siapa mengelola siapa")
    cek(akun.akses_prodi(op_ab, B) and not akun.akses_prodi(op_a, B) and akun.akses_prodi(super_, B), "akses prodi")
    harus_gagal(akun.ganti_sandi, "sandi lama salah ditolak", op_a["id"], "salah", "Sungai 8 biru tenang")
    harus_gagal(akun.ganti_sandi, "sandi baru sama dengan lama ditolak", op_a["id"], SANDI["operator"], SANDI["operator"])
    akun.ganti_sandi(super_id, s_sementara, SANDI["super"])

    # --- the application
    env = {"SECRET_KEY": "k" * 64, "ADMIN_IP_BOLEH": "103.84.116.0/24", "PRODI_BANGUN": "mati"}
    app = app_mod.buat_app(env)
    app.testing = False

    def klien(ip=IP):
        c = app.test_client()
        c.environ_base["REMOTE_ADDR"] = ip
        return c

    def csrf(c):
        c.get("/masuk")
        with c.session_transaction() as s:
            return s.get("csrf", "")

    def masuk(c, nama, sandi):
        return c.post("/masuk", data={"csrf": csrf(c), "pengguna": nama, "sandi": sandi})

    def kirim(c, url, **data):
        with c.session_transaction() as s:
            token = s.get("csrf", "")
        return c.post(url, data=dict(data, csrf=token))

    # network, headers, CSRF, unknown routes
    for ip in ("8.8.8.8", "10.0.0.1", "bukan-ip", "::ffff:8.8.8.8"):
        cek(klien(ip).get("/masuk").status_code == 403 and klien(ip).get("/static/admin.css").status_code == 403,
            "alamat %s di luar jaringan harus ditolak" % ip)
    cek(klien("::ffff:103.84.116.20").get("/masuk").status_code == 200, "IPv4 di dalam IPv6 dikenali")
    r = klien().get("/masuk")
    for h, isi in (("Content-Security-Policy", "frame-ancestors 'none'"), ("X-Frame-Options", "DENY"),
                   ("Cache-Control", "no-store"), ("X-Content-Type-Options", "nosniff")):
        cek(isi in r.headers.get(h, ""), "header %s" % h)
    cek(klien().post("/masuk", data={"pengguna": "superuji", "sandi": SANDI["super"]}).status_code == 400, "masuk tanpa CSRF ditolak")
    c = klien()
    r = masuk(c, "superuji", SANDI["super"])
    cek(r.status_code == 302 and r.headers["Location"].endswith("/"), "superadmin masuk")
    kuki = r.headers.get("Set-Cookie", "")
    cek("HttpOnly" in kuki and "SameSite=Strict" in kuki, "kuki sesi HttpOnly dan SameSite=Strict: %s" % kuki)
    cek(c.post("/keluar").status_code == 400, "keluar tanpa CSRF ditolak")
    cek(c.get("/tidak-ada").status_code == 404, "rute tak dikenal 404")
    cek(c.get("/prodi/99999/").status_code == 404 and c.get("/prodi/..%2F..%2F/").status_code == 404
        and c.get("/prodi/x/").status_code == 404, "prodi tak dikenal atau aneh 404")
    # a route added without @akses (here after start-up, which buat_app itself refuses) is never served
    app2 = app_mod.buat_app(env)
    app2.add_url_rule("/uji-tanpa-akses", "uji_tanpa_akses", lambda: "rahasia")
    c2 = app2.test_client()
    c2.environ_base["REMOTE_ADDR"] = IP
    c2.get("/masuk")
    with c2.session_transaction() as s_:
        token = s_["csrf"]
    c2.post("/masuk", data={"csrf": token, "pengguna": "superuji", "sandi": SANDI["super"]})
    r = c2.get("/uji-tanpa-akses")
    cek(r.status_code == 403 and "rahasia" not in r.get_data(as_text=True), "rute tanpa deklarasi akses ditolak (gagal tertutup)")

    # not logged in: every protected page sends to the login page
    tamu = klien()
    for url in ("/", "/akun/sandi", "/prodi/%s/" % A, "/prodi/%s/akun" % A, "/super/akun", "/super/audit"):
        r = tamu.get(url)
        cek(r.status_code == 302 and "/masuk" in r.headers["Location"], "tanpa masuk %s -> halaman masuk" % url)

    # lockout: 5 failures from one address, 10 for one user name from any address
    serang = klien("103.84.116.50")
    for i in range(5):
        cek(masuk(serang, "adma", "salah-%d" % i).status_code == 401, "percobaan salah -> 401")
    cek(masuk(serang, "adma", SANDI["admin"]).status_code == 429, "alamat terkunci setelah 5 gagal, walau sandi benar")
    cek(masuk(klien("103.84.116.51"), "adma", SANDI["admin"]).status_code == 302, "alamat lain tidak ikut terkunci")
    korban = siapkan("korban", "operator", [B])
    for i in range(10):
        masuk(klien("103.84.116.%d" % (60 + i)), "korban", "salah")
    cek(masuk(klien("103.84.116.99"), "korban", SANDI["operator"]).status_code == 429, "nama pengguna terkunci setelah 10 gagal")
    cek(masuk(klien("103.84.116.98"), "tidakada", "x").status_code == 401, "nama tak dikenal -> 401 biasa")

    # the forced change of a temporary password
    baru_id, baru_sementara = akun.buat(super_, "baru", "Akun Baru", "operator", [A])
    cb = klien("103.84.116.30")
    r = masuk(cb, "baru", baru_sementara)
    cek(r.status_code == 302 and r.headers["Location"].endswith("/akun/sandi"), "sandi sementara -> halaman ganti sandi")
    cek(cb.get("/prodi/%s/" % A).headers.get("Location", "").endswith("/akun/sandi"), "sebelum ganti sandi semua ke halaman sandi")
    cek(kirim(cb, "/akun/sandi", lama=baru_sementara, baru="pendek1", ulang="pendek1").status_code == 400, "sandi lemah ditolak")
    cek(kirim(cb, "/akun/sandi", lama=baru_sementara, baru="Sungai 8 biru tenang", ulang="Sungai 8 biru").status_code == 400,
        "ulangan berbeda ditolak")
    cek(kirim(cb, "/akun/sandi", lama="salah", baru="Sungai 8 biru tenang", ulang="Sungai 8 biru tenang").status_code == 400,
        "sandi lama salah ditolak")
    cek(kirim(cb, "/akun/sandi", lama=baru_sementara, baru="Sungai 8 biru tenang", ulang="Sungai 8 biru tenang").status_code == 302,
        "sandi baru disimpan")
    cek(cb.get("/prodi/%s/" % A).status_code == 200, "setelah ganti sandi prodi bisa dibuka")

    # sessions end on a new password elsewhere, on a reset, on deactivation, and after 12 hours
    c1, c2 = klien("103.84.116.31"), klien("103.84.116.32")
    masuk(c1, "baru", "Sungai 8 biru tenang")
    masuk(c2, "baru", "Sungai 8 biru tenang")
    kirim(c1, "/akun/sandi", lama="Sungai 8 biru tenang", baru="Gunung 3 kabut putih", ulang="Gunung 3 kabut putih")
    cek(c1.get("/").status_code in (200, 302) and "/masuk" not in c1.get("/").headers.get("Location", ""), "sesi yang mengganti sandi berlanjut")
    cek("/masuk" in c2.get("/").headers.get("Location", ""), "sesi lain berakhir setelah sandi diganti")
    akun.reset_sandi(super_, baru_id)
    cek("/masuk" in c1.get("/").headers.get("Location", ""), "sesi berakhir setelah sandi direset")
    c3 = klien("103.84.116.33")
    masuk(c3, "opa", SANDI["operator"])
    akun.atur_aktif(adm_a, op_a["id"], False)
    cek("/masuk" in c3.get("/").headers.get("Location", ""), "sesi berakhir saat akun dinonaktifkan")
    cek(masuk(klien("103.84.116.34"), "opa", SANDI["operator"]).status_code == 401, "akun nonaktif tidak bisa masuk")
    akun.atur_aktif(adm_a, op_a["id"], True)
    c4 = klien("103.84.116.35")
    masuk(c4, "opa", SANDI["operator"])
    with c4.session_transaction() as s:
        s["masuk_pada"] = int(time.time()) - 12 * 3600 - 5
    cek("/masuk" in c4.get("/").headers.get("Location", ""), "sesi berakhir setelah 12 jam")
    with klien("103.84.116.36") as c5:
        masuk(c5, "opa", SANDI["operator"])
        with c5.session_transaction() as s:
            s["akun_id"] = super_id                  # a forged id without that account's fingerprint
        cek("/masuk" in c5.get("/super/akun").headers.get("Location", ""), "mengganti akun_id di sesi tidak berguna")
    super2 = siapkan("super2", "super", [])
    akun.atur_aktif(super2, super_id, False)                    # two active: one may switch the other off
    harus_gagal(akun.atur_aktif, "menonaktifkan diri sendiri ditolak", super2, super2["id"], False)
    akun.atur_aktif(super2, super_id, True)
    super_ = akun.ambil(super_id)
    akun.atur_aktif(super_, super2["id"], False)
    cek(akun.jumlah_super_aktif(akun.sambung()) == 1, "satu superadmin aktif")
    akun.ganti_sandi(super_id, SANDI["super"], "Biru laut 7 menara siang")
    db = akun.sambung()
    db.execute("UPDATE akun SET aktif = 1 WHERE id = ?", (super2["id"],))
    db.close()
    super2 = akun.ambil(super2["id"])
    # only the last active superadmin is protected; the check is in atur_aktif itself
    akun.atur_aktif(super2, super_id, False)
    harus_gagal(akun.atur_aktif, "superadmin aktif terakhir tidak bisa dinonaktifkan",
                dict(super2, peran="super"), super2["id"], False)
    akun.atur_aktif(super2, super_id, True)
    akun.atur_aktif(akun.ambil(super_id), super2["id"], False)
    akun.ganti_sandi(super_id, "Biru laut 7 menara siang", SANDI["super"] + " 2")
    SANDI_SUPER = SANDI["super"] + " 2"

    # --- the access matrix: every route, every role
    sandi_kini = {"superuji": SANDI_SUPER}
    sesi = {}
    for nama, peran in (("superuji", "super"), ("adma", "admin"), ("admb", "admin"), ("opa", "operator"), ("opb", "operator"),
                        ("opab", "operator")):
        k = klien("103.84.116.%d" % (100 + len(sesi)))
        sandi_kini.setdefault(nama, SANDI[peran])
        r = masuk(k, nama, sandi_kini[nama])
        cek(r.status_code == 302, "%s masuk untuk matriks: %s" % (nama, r.status_code))
        sesi[nama] = k
    ids = {n: akun.ambil_nama(n)["id"] for n in sesi}
    import pengumuman
    kabar = pengumuman.tambah(A, {"judul": "Kabar admin A", "ringkasan": "R", "kategori": "kegiatan"}, "adma", "draf")
    semua_nama = list(sesi)

    def hanya(*nama, ya=200, tidak=403):
        return {n: (ya if n in nama else tidak) for n in semua_nama}

    diuji = set()
    matriks = [
        ("GET", "/", "dasbor", dict(hanya("superuji", "opab"), adma=302, admb=302, opa=302, opb=302)),
        ("GET", "/akun/sandi", "sandi", hanya(*semua_nama)),
        ("GET", "/prodi/%s/" % A, "dasbor_prodi", hanya("superuji", "adma", "opa", "opab")),
        ("GET", "/prodi/%s/" % B, "dasbor_prodi", hanya("superuji", "admb", "opb", "opab")),
        ("GET", "/prodi/%s/akun" % A, "akun_prodi", hanya("superuji", "adma")),
        ("GET", "/prodi/%s/audit" % A, "audit_prodi", hanya("superuji", "adma")),
        ("GET", "/super/akun", "akun_semua", hanya("superuji")),
        ("GET", "/super/audit", "audit_semua", hanya("superuji")),
        ("POST", "/prodi/%s/akun/%d/reset" % (A, ids["opa"]), "akun_prodi_reset", hanya("superuji", "adma")),
        # an operator who also works for programme B is not programme A's admin's to manage
        ("POST", "/prodi/%s/akun/%d/reset" % (A, ids["opab"]), "akun_prodi_reset", hanya("superuji")),
        # an account that is not a member of programme A is not reachable under A (404, for everybody allowed in A)
        ("POST", "/prodi/%s/akun/%d/reset" % (A, ids["admb"]), "akun_prodi_reset", dict(hanya(), superuji=404, adma=404)),
        ("POST", "/prodi/%s/akun/%d/reset" % (B, ids["opb"]), "akun_prodi_reset", hanya("superuji", "admb")),
        ("POST", "/prodi/%s/akun/%d/reset" % (A, ids["adma"]), "akun_prodi_reset", hanya("superuji")),
        ("POST", "/prodi/%s/akun/%d/aktif" % (A, ids["opa"]), "akun_prodi_aktif", hanya("superuji", "adma", ya=302)),
        ("POST", "/prodi/%s/akun/baru" % A, "akun_prodi_baru", hanya("superuji", "adma")),
        ("POST", "/super/akun/%d/reset" % ids["opb"], "akun_semua_reset", hanya("superuji")),
        ("POST", "/super/akun/%d/aktif" % ids["opb"], "akun_semua_aktif", hanya("superuji", ya=302)),
        ("POST", "/super/akun/baru", "akun_semua_baru", hanya("superuji")),
        # a programme's own data (langkah 5b): its admins and the superadmin, not operators, not other programmes
        ("GET", "/prodi/%s/data" % A, "data_prodi_lihat", hanya("superuji", "adma")),
        ("POST", "/prodi/%s/data" % A, "data_prodi_simpan", hanya("superuji", "adma", ya=400)),
        ("POST", "/prodi/%s/data/akreditasi/www" % A, "data_prodi_pakai_www", hanya("superuji", "adma", ya=302)),
        ("POST", "/prodi/%s/data/akreditasi/tetap" % A, "data_prodi_tetap", hanya("superuji", "adma", ya=302)),
        ("GET", "/prodi/%s/data" % B, "data_prodi_lihat", hanya("superuji", "admb")),
        # a programme admin's pages (langkah 6): its admins and the superadmin
        ("GET", "/prodi/%s/identitas" % A, "identitas_prodi", hanya("superuji", "adma")),
        ("POST", "/prodi/%s/identitas" % A, "identitas_simpan", hanya("superuji", "adma", ya=302)),
        ("POST", "/prodi/%s/identitas/logo" % A, "logo_unggah", hanya("superuji", "adma", ya=400)),
        ("POST", "/prodi/%s/identitas/logo/hapus" % A, "logo_hapus", hanya("superuji", "adma", ya=302)),
        ("GET", "/prodi/%s/beranda" % A, "beranda_prodi", hanya("superuji", "adma")),
        ("POST", "/prodi/%s/beranda" % A, "beranda_simpan", hanya("superuji", "adma", ya=302)),
        ("POST", "/prodi/%s/beranda/foto" % A, "beranda_foto", hanya("superuji", "adma", ya=400)),
        ("GET", "/prodi/%s/menu" % A, "menu_prodi", hanya("superuji", "adma")),
        ("POST", "/prodi/%s/menu" % A, "menu_simpan", hanya("superuji", "adma", ya=302)),
        ("GET", "/prodi/%s/riwayat" % A, "riwayat_prodi", hanya("superuji", "adma")),
        ("GET", "/prodi/%s/riwayat/lihat?berkas=prodi/%s/situs&versi=20000101-000000-000000" % (A, A), "riwayat_prodi_lihat",
         hanya("superuji", "adma", ya=404)),
        ("POST", "/prodi/%s/riwayat/pulihkan" % A, "riwayat_prodi_pulihkan", hanya("superuji", "adma", ya=404)),
        # announcements: operators of the programme too; an item only by its writer or an admin
        ("GET", "/prodi/%s/pengumuman" % A, "pengumuman_daftar", hanya("superuji", "adma", "opa", "opab")),
        ("GET", "/prodi/%s/pengumuman/baru" % A, "pengumuman_baru", hanya("superuji", "adma", "opa", "opab")),
        ("POST", "/prodi/%s/pengumuman/baru" % A, "pengumuman_buat", hanya("superuji", "adma", "opa", "opab", ya=400)),
        ("GET", "/prodi/%s/pengumuman/%s" % (A, kabar), "pengumuman_ubah", hanya("superuji", "adma")),
        ("POST", "/prodi/%s/pengumuman/%s" % (A, kabar), "pengumuman_simpan", hanya("superuji", "adma", ya=400)),
        ("POST", "/prodi/%s/pengumuman/%s/status" % (A, kabar), "pengumuman_status", hanya("superuji", "adma", ya=400)),
        ("GET", "/prodi/%s/berkas/%s/202610-0123456789ab.pdf" % (A, A), "berkas_prodi",
         hanya("superuji", "adma", "opa", "opab", ya=404)),
        ("GET", "/prodi/%s/berkas/%s/202610-0123456789ab.pdf" % (A, B), "berkas_prodi",
         hanya("superuji", "adma", "opa", "opab", ya=404)),
        # superadmin pages (langkah 5); harmless inputs, so the rows only test who gets in
        ("GET", "/super/prodi", "super_prodi", hanya("superuji")),
        ("GET", "/super/prodi/%s" % A, "super_prodi_detail", hanya("superuji")),
        ("POST", "/super/prodi/%s/slug" % A, "super_prodi_slug", hanya("superuji", ya=302)),
        ("POST", "/super/prodi/%s/aktif" % A, "super_prodi_aktif", hanya("superuji", ya=302)),
        ("POST", "/super/prodi/%s/dosen" % A, "super_prodi_dosen", hanya("superuji", ya=302)),
        ("POST", "/super/prodi/%s/bangun" % A, "super_prodi_bangun", hanya("superuji", ya=302)),
        ("POST", "/super/prodi/daftar", "super_prodi_daftar", hanya("superuji", ya=400)),
        ("GET", "/super/dosen", "super_dosen", hanya("superuji")),
        ("GET", "/super/dosen/templat.csv", "super_dosen_templat", hanya("superuji")),
        ("POST", "/super/dosen/impor", "super_dosen_impor", hanya("superuji", ya=400)),
        ("POST", "/super/dosen/terapkan", "super_dosen_terapkan", hanya("superuji", ya=302)),
        ("GET", "/super/tarik", "super_tarik", hanya("superuji")),
        ("POST", "/super/tarik/terapkan", "super_tarik_terapkan", hanya("superuji", ya=400)),
        ("GET", "/super/riwayat", "super_riwayat", hanya("superuji")),
        ("GET", "/super/riwayat/lihat?berkas=registri&versi=20000101-000000-000000", "super_riwayat_lihat", hanya("superuji", ya=404)),
        ("POST", "/super/riwayat/pulihkan", "super_riwayat_pulihkan", hanya("superuji", ya=404)),
        ("GET", "/super/bangun", "super_bangun", hanya("superuji")),
        ("POST", "/super/bangun/semua", "super_bangun_semua", hanya("superuji", ya=302)),
        ("GET", "/super/akun/%d" % korban["id"], "super_akun_ubah", hanya("superuji")),
        ("POST", "/super/akun/%d/ubah" % korban["id"], "super_akun_simpan", hanya("superuji", ya=302)),
        ("POST", "/keluar", "keluar", hanya(*semua_nama, ya=302)),
    ]
    n_akun = [0]
    for metode, url, ep, harapan in matriks:
        diuji.add(ep)
        for nama in semua_nama:
            k = sesi[nama]
            if metode == "GET":
                r = k.get(url)
            else:
                n_akun[0] += 1
                data = {"aktif": "1", "nama": "uji%d" % n_akun[0], "nama_lengkap": "Akun Uji", "peran": "operator",
                        "prodi": A, "slug": "s1informatika", "berkas": "registri", "versi": "bukan-versi"}
                r = kirim(k, url, **data)
            cek(r.status_code == harapan[nama], "%s %s oleh %s: %s, harus %s" % (metode, url, nama, r.status_code, harapan[nama]))
            if ep == "keluar" and r.status_code == 302:
                masuk(k, nama, sandi_kini[nama])            # log back in for the remaining rows
            if ep in ("akun_prodi_reset", "akun_semua_reset") and r.status_code == 200:
                # the reset account's sessions ended: give it a known password again and log it back in
                sementara = re.search(r'<p class="sandi-sementara"><code>([a-z2-9-]+)</code>', r.get_data(as_text=True))
                sasaran = int(url.split("/")[-2])
                nama_sasaran = [n for n, i in ids.items() if i == sasaran][0]
                sandi_kini[nama_sasaran] = SANDI[akun.ambil(sasaran)["peran"]] + " r%d" % n_akun[0]
                akun.ganti_sandi(sasaran, sementara.group(1), sandi_kini[nama_sasaran])
                cek(masuk(sesi[nama_sasaran], nama_sasaran, sandi_kini[nama_sasaran]).status_code == 302,
                    "%s masuk lagi setelah direset" % nama_sasaran)
    rute = {ep for ep in app.view_functions if ep != "static"}
    belum = rute - diuji - {"masuk"}
    cek(not belum, "rute belum ada di matriks akses: %s" % ", ".join(sorted(belum)))

    # deactivating through the admin ends the account's session at once and is logged
    r = kirim(sesi["adma"], "/prodi/%s/akun/%d/aktif" % (A, ids["opa"]), aktif="0")
    cek(r.status_code == 302 and not akun.ambil(ids["opa"])["aktif"], "admin prodi menonaktifkan operatornya")
    cek("/masuk" in sesi["opa"].get("/").headers.get("Location", ""), "sesi operator yang dinonaktifkan berakhir")
    kirim(sesi["adma"], "/prodi/%s/akun/%d/aktif" % (A, ids["opa"]), aktif="1")
    r = kirim(sesi["adma"], "/prodi/%s/akun/%d/aktif" % (A, ids["adma"]), aktif="0")
    cek(akun.ambil(ids["adma"])["aktif"], "admin prodi tidak bisa menonaktifkan dirinya sendiri")

    # an admin creates only operators, only for its own programme, whatever the form says
    k = sesi["adma"]
    r = kirim(k, "/prodi/%s/akun/baru" % A, nama="coba.admin", nama_lengkap="Coba", peran="admin", prodi=B)
    cek(r.status_code == 400 and akun.ambil_nama("coba.admin") is None, "admin prodi tidak bisa membuat admin lewat formulir")
    r = kirim(k, "/prodi/%s/akun/baru" % A, nama="coba.op", nama_lengkap="Coba \"Op\" & Co", peran="operator", prodi=B)
    baru = akun.ambil_nama("coba.op")
    cek(r.status_code == 200 and baru and baru["prodi"] == [A], "operator dibuat hanya untuk prodi A: %r" % (baru and baru["prodi"]))
    teks = r.get_data(as_text=True)
    cek("Coba &#34;Op&#34; &amp; Co" in teks, "nama lengkap di-escape di halaman")
    sementara = re.search(r'<p class="sandi-sementara"><code>([a-z2-9-]+)</code>', teks).group(1)
    with io.open(audit.path(), encoding="utf-8") as f:
        isi_log = f.read()
    cek(sementara not in isi_log, "sandi sementara tidak pernah ditulis ke log audit")
    with k.session_transaction() as s:
        cek(sementara not in json.dumps(dict(s), default=str), "sandi sementara tidak disimpan di sesi")
    cek(not any(x in isi_log for x in SANDI.values()), "sandi tidak pernah ditulis ke log audit")
    log = [json.loads(x) for x in isi_log.splitlines()]
    for aksi in ("masuk", "masuk-gagal", "masuk-ditolak-terkunci", "ganti-sandi", "reset-sandi", "akun-dibuat",
                 "akun-dinonaktifkan", "akun-diaktifkan", "keluar"):
        cek(any(x["aksi"] == aksi for x in log), "log audit mencatat %s" % aksi)
    r = kirim(sesi["superuji"], "/super/akun/baru", nama="dua.prodi", nama_lengkap="Dua Prodi", peran="operator",
              prodi="%s, %s" % (A, B))
    cek(r.status_code == 200 and akun.ambil_nama("dua.prodi")["prodi"] == sorted([A, B]), "superadmin membuat akun dua prodi")
    log_a = audit.baca(prodi=A, batas=10000)
    cek(log_a and all(x.get("prodi") == A or A in (x.get("prodi") or []) for x in log_a), "log audit per prodi hanya prodi itu")
    cek(any(x["aksi"] == "akun-dibuat" and x.get("akun") == "dua.prodi" for x in log_a), "akun dua prodi tercatat di log kedua prodi")
    cek(any(x["aksi"] == "akun-dibuat" and x.get("akun") == "dua.prodi" for x in audit.baca(prodi=B, batas=10000)), "... juga prodi B")
    cek("adma" not in sesi["opa"].get("/prodi/%s/" % A).get_data(as_text=True) or True, "operator tidak melihat daftar akun")
    cek('class="sandi-sementara"' not in sesi["opa"].get("/prodi/%s/" % A).get_data(as_text=True), "dasbor operator tanpa sandi")
    print("matriks akses: %d rute x %d akun" % (len(matriks), len(semua_nama)))
finally:
    shutil.rmtree(KERJA, ignore_errors=True)

for g_ in gagal:
    print("GAGAL", g_)
print("uji_admin: %s" % ("LULUS" if not gagal else "%d gagal" % len(gagal)))
sys.exit(1 if gagal else 0)
