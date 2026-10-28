# -*- coding: utf-8 -*-
"""Admin of prodi.unsrat.ac.id: accounts and roles (langkah 4), superadmin pages (langkah 5, superadmin.py).

    python3 platform/admin/siapkan.py                                    first time: session key in <PRODI_RAHASIA>/.env
    python3 platform/admin/siapkan.py --superadmin nama --nama-lengkap "Nama"   first superadmin (password in a file)
    .venv/bin/python platform/admin/app.py                               local admin at http://127.0.0.1:8791/

Never exposed to the internet: only addresses in ADMIN_IP_BOLEH (UNSRAT's network, or its VPN) get anything at all,
and in production only over HTTPS (PRODI_MODE=produksi does not start without ADMIN_HTTPS=1) behind the web container.
Patterns taken from the www admin (site/admin/app.py): network allow-list, lockout per address and per user name,
sessions bound to the password, CSRF on every form, strict security headers, no debugger.

Access is declared on every route with @akses(...) (akses.py) and checked in one place (periksa_akses) before any
view runs. A route without a declaration is refused (fail closed); uji/uji_admin.py tries every route with every role.
Changes that affect the published sites are followed by a rebuild (pembangun.py, PRODI_BANGUN).
"""
from __future__ import print_function

import hmac
import io
import ipaddress
import os
import re
import secrets
import sys
import threading
import time

ADMIN = os.path.dirname(os.path.abspath(__file__))
PLATFORM = os.path.dirname(ADMIN)
sys.path.insert(0, PLATFORM)
sys.path.insert(0, ADMIN)
sys.path.insert(0, os.path.join(PLATFORM, "bangun"))

from flask import Flask, abort, flash, g, redirect, render_template, request, session, url_for  # noqa: E402

import akun as akun_mod  # noqa: E402
import audit  # noqa: E402
import lokasi  # noqa: E402
import data_prodi  # noqa: E402
import impor_tabel  # noqa: E402
import isi_admin  # noqa: E402
import kriteria_admin  # noqa: E402
import masukan_admin  # noqa: E402
import panduan  # noqa: E402
import pembangun  # noqa: E402
import pengumuman_admin  # noqa: E402
import prodi_admin  # noqa: E402
import registri  # noqa: E402
import superadmin  # noqa: E402
import tambahan_admin  # noqa: E402
from akses import akses  # noqa: E402

SESI_MENIT = 120              # a session ends after this long without activity...
SESI_MAKS_JAM = 12            # ...and at the latest this long after logging in
GAGAL_MAKS_IP = 5             # failed logins from one address within the window
GAGAL_MAKS_AKUN = 10          # failed logins for one user name, from any address, within the window
KUNCI_MENIT = 15
MAKS_TANPA_LOGIN = 64 * 1024  # largest request accepted before logging in (the login form)
IP_BOLEH_BAWAAN = "103.84.116.0/24"
# the shortest prefix of a network in ADMIN_IP_BOLEH, per IP version: a wider one opens the admin to a large part of the
# internet (0.0.0.0/0 to everybody); docker/nginx/40-prodi-jaringan.sh refuses the same
AWALAN_MIN = {4: 8, 6: 32}
PENGATURAN_LINGKUNGAN = ("ADMIN_IP_BOLEH", "ADMIN_HTTPS", "PROXY_TERPERCAYA", "ADMIN_AWALAN", "PORT", "PRODI_ALAMAT_PUBLIK",
                         "PRODI_BANGUN", "PRODI_BANGUN_HARIAN", "PRODI_MODE")
POLA_NAMA_AKUN = re.compile(r"^([a-z][a-z0-9._-]{2,31}|-|baris-perintah)$")
POLA_AKSI = re.compile(r"^[a-z][a-z-]{1,40}$")
POLA_KODE = re.compile(r"^[0-9A-Za-z]{3,12}$")

HALAMAN_LUAR_JARINGAN = (
    '<!DOCTYPE html>\n<html lang="id">\n<head>\n<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1">\n<meta name="robots" content="noindex, nofollow">\n'
    '<title>Tidak dapat dibuka — Admin situs prodi UNSRAT</title>\n</head>\n<body>\n<main>\n'
    '<h1>Halaman admin tidak dapat dibuka dari jaringan ini</h1>\n'
    '<p>Admin situs program studi UNSRAT hanya dapat dibuka dari jaringan kampus UNSRAT. Bila Anda berada di luar '
    'kampus, sambungkan dulu ke VPN UNSRAT, lalu muat ulang halaman ini.</p>\n'
    '</main>\n</body>\n</html>\n')


def baca_env(path):
    data = {}
    if os.path.isfile(path):
        with io.open(path, encoding="utf-8") as f:
            for baris in f:
                baris = baris.strip()
                if baris and not baris.startswith("#") and "=" in baris:
                    k, v = baris.split("=", 1)
                    data[k.strip()] = v.strip()
    return data


def baca_jaringan(teks):
    """The networks of ADMIN_IP_BOLEH, separated by commas, spaces or tabs (as for Nginx, 40-prodi-jaringan.sh)."""
    hasil = []
    for bagian in re.split(r"[,\s]+", teks or ""):
        if bagian:
            try:
                n = ipaddress.ip_network(bagian, strict=False)
            except ValueError:
                raise ValueError("ADMIN_IP_BOLEH berisi alamat yang tidak sah: %s" % bagian)
            if n.prefixlen < AWALAN_MIN[n.version]:
                raise ValueError("ADMIN_IP_BOLEH berisi jaringan yang terlalu luas: %s (paling luas /%d untuk IPv4, /%d "
                                 "untuk IPv6)" % (bagian, AWALAN_MIN[4], AWALAN_MIN[6]))
            hasil.append(n)
    return hasil


def buat_app(env=None):
    """The admin application. env: settings (default: <PRODI_RAHASIA>/.env, overridden by the environment)."""
    if env is None:
        env = baca_env(os.path.join(lokasi.rahasia(), ".env"))
        env.update({k: os.environ[k] for k in PENGATURAN_LINGKUNGAN if os.environ.get(k)})
    if not env.get("SECRET_KEY") or len(env["SECRET_KEY"]) < 32:
        raise SystemExit("SECRET_KEY belum diisi: jalankan dulu python3 platform/admin/siapkan.py")
    https = env.get("ADMIN_HTTPS") == "1"
    if env.get("PRODI_MODE") == "produksi" and not https:
        raise SystemExit("PRODI_MODE=produksi memerlukan ADMIN_HTTPS=1: di produksi admin hanya dibuka lewat HTTPS, "
                         "supaya kata sandi dan sesi tidak pernah lewat jaringan tanpa enkripsi (docs/deploy.md §7)")
    proksi = int(env.get("PROXY_TERPERCAYA") or 0)
    awalan = (env.get("ADMIN_AWALAN") or "").rstrip("/")
    if awalan and not re.match(r"^(/[A-Za-z0-9._-]+)+$", awalan):
        raise SystemExit("ADMIN_AWALAN tidak sah: %s" % awalan)
    try:
        ip_boleh = baca_jaringan(env.get("ADMIN_IP_BOLEH") or IP_BOLEH_BAWAAN)
    except ValueError as e:
        raise SystemExit(str(e))
    alamat_publik = (env.get("PRODI_ALAMAT_PUBLIK") or "https://prodi.unsrat.ac.id").rstrip("/")

    app = Flask(__name__, template_folder=os.path.join(ADMIN, "templates"), static_folder=os.path.join(ADMIN, "static"))
    app.config.update(
        SECRET_KEY=env["SECRET_KEY"],
        MAX_CONTENT_LENGTH=40 * 1024 * 1024,       # the largest upload (a hero photo, 15 MB) with room for the form
        # the form of a page with every list full (a 300-row table of partnerships: about 2,700 fields; uji_penyunting
        # checks every template against this); Flask's default is 1,000
        MAX_FORM_PARTS=4000,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Strict",
        SESSION_COOKIE_SECURE=https,
        SESSION_COOKIE_NAME=("__Secure-prodi_admin" if awalan else "__Host-prodi_admin") if https else "prodi_admin",
        SESSION_COOKIE_PATH=awalan or "/",
        PERMANENT_SESSION_LIFETIME=SESI_MENIT * 60,
    )
    if proksi:
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=proksi, x_proto=proksi, x_prefix=proksi)

    antrean = pembangun.Antrean(env.get("PRODI_BANGUN") or "latar")
    penjadwal = None
    if env.get("PRODI_BANGUN_HARIAN"):
        try:
            penjadwal = pembangun.Penjadwal(antrean, env["PRODI_BANGUN_HARIAN"])
        except ValueError as e:
            raise SystemExit(str(e))
        if antrean.mode == "latar":            # tests build inside the request or not at all: no daily thread
            penjadwal.mulai()
    gagal = {}                     # "ip:<address>" / "akun:<name>" -> times of failed logins within the window
    kunci_gagal = threading.Lock()

    def ip_diizinkan(alamat):
        try:
            ip = ipaddress.ip_address((alamat or "").split("%")[0])
        except ValueError:
            return False
        if ip.version == 6 and ip.ipv4_mapped:
            ip = ip.ipv4_mapped
        return any(ip.version == n.version and ip in n for n in ip_boleh)

    def catat(aksi, prodi=None, **data):
        pelaku = g.get("akun")
        audit.catat(aksi, oleh=pelaku["nama"] if pelaku else "-", ip=request.remote_addr, prodi=prodi, **data)

    def token_csrf():
        if "csrf" not in session:
            session["csrf"] = secrets.token_urlsafe(32)
        return session["csrf"]

    def akun_sesi():
        """The account of a valid session, or None."""
        a = akun_mod.ambil(session.get("akun_id")) if isinstance(session.get("akun_id"), int) else None
        if not a or not a["aktif"] or not akun_mod.sidik_cocok(a, env["SECRET_KEY"], session.get("sidik")):
            return None
        if not 0 <= time.time() - session.get("masuk_pada", 0) < SESI_MAKS_JAM * 3600:
            return None
        return a

    def registri_per_kode():
        return {r["kode_pddikti"]: r for r in (lokasi.baca("registri") or {}).get("prodi", [])}

    def warisan_per_kode():
        return {p["kode_pddikti"]: p for p in (lokasi.baca("warisan/prodi") or {}).get("program", [])}

    def info_prodi(kode):
        r, p = registri_per_kode().get(kode), warisan_per_kode().get(kode)
        p = data_prodi.efektif(kode, p) if p else None          # with the programme's own changes
        if not r or not p:
            return None
        return {"kode": kode, "slug": r["slug"], "aktif": r["aktif"], "nama": registri.nama_tampil(p), "unit": p["unit"],
                "jenjang": p["jenjang"], "alamat": "%s/%s/" % (alamat_publik, r["slug"])}

    def kelompok_prodi():
        """Registered programmes grouped by faculty, for the programme checkboxes of the account forms."""
        kelompok = {}
        for kode in registri_per_kode():
            x = info_prodi(kode)
            if x:
                kelompok.setdefault(x["unit"], []).append(x)
        return [(unit, sorted(isi, key=registri.kunci_urut)) for unit, isi in sorted(kelompok.items())]

    def prodi_dari_formulir():
        """Programme codes from checkboxes (several fields "prodi") or a comma-separated field."""
        return [k.strip() for v in request.form.getlist("prodi") for k in re.split(r"[,\s]+", v) if k.strip()]

    # -------------------------------------------------------------- checks before every request

    @app.before_request
    def periksa_akses():
        # outside UNSRAT's network nothing is served: no login page, no styles, no session
        if not ip_diizinkan(request.remote_addr):
            return HALAMAN_LUAR_JARINGAN, 403, {"Content-Type": "text/html; charset=utf-8"}
        if request.content_length and request.content_length > MAKS_TANPA_LOGIN and not session.get("akun_id"):
            abort(413)
        if request.method == "POST":
            kirim = request.form.get("csrf", "")
            if not kirim or not hmac.compare_digest(kirim, session.get("csrf", "")):
                abort(400, "Formulir kedaluwarsa. Muat ulang halaman lalu coba lagi.")
        if request.endpoint is None:          # no such route: the 404 handler answers
            return None
        if request.endpoint == "static":
            return None
        aturan = getattr(app.view_functions.get(request.endpoint), "akses", None)
        if aturan is None:
            abort(403)                        # a route without an access declaration is never served
        jenis, minimal = aturan
        if jenis == "umum":
            return None
        a = akun_sesi()
        if a is None:
            ada = bool(session.get("akun_id"))
            session.clear()
            if ada:
                flash("Sesi berakhir. Silakan masuk lagi.", "galat")
            return redirect(url_for("masuk"))
        g.akun = a
        if a["wajib_ganti"] and request.endpoint not in ("sandi", "keluar"):
            flash("Ganti kata sandi sementara Anda sebelum melanjutkan.", "info")
            return redirect(url_for("sandi"))
        if jenis == "super" and a["peran"] != "super":
            abort(403)
        if jenis == "prodi":
            kode = (request.view_args or {}).get("kode", "")
            if not POLA_KODE.match(kode) or info_prodi(kode) is None:
                abort(404)
            if not akun_mod.akses_prodi(a, kode) or (minimal == "admin" and a["peran"] == "operator"):
                abort(403)
            g.prodi = info_prodi(kode)
        return None

    @app.after_request
    def header_keamanan(resp):
        # a route may set a stricter policy of its own (an uploaded SVG opened by itself, prodi_admin.berkas_prodi)
        resp.headers.setdefault("Content-Security-Policy", (
            "default-src 'self'; img-src 'self' data: https://storage.googleapis.com; style-src 'self'; "
            "script-src 'self'; object-src 'none'; frame-ancestors 'none'; form-action 'self'; base-uri 'none'"))
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = "same-origin"
        resp.headers["Cache-Control"] = "no-store"
        resp.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=(), usb=()"
        resp.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        resp.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        if https:
            resp.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return resp

    app.jinja_env.globals.update(token_csrf=token_csrf, NAMA_PERAN=akun_mod.NAMA_PERAN,
                                 akun_aktif=lambda: g.get("akun"), SANDI_MIN=akun_mod.SANDI_MIN)

    # -------------------------------------------------------------- logging in and out

    def sisa_kunci(kunci, maks, sekarang):
        terbaru = [t for t in gagal.get(kunci, []) if sekarang - t < KUNCI_MENIT * 60]
        return int(terbaru[-maks] + KUNCI_MENIT * 60 - sekarang) + 1 if len(terbaru) >= maks else 0

    def catat_gagal(kunci_kunci, sekarang):
        with kunci_gagal:
            if len(gagal) > 10000:            # many made-up names: forget those without recent failures
                for k in [k for k, v in gagal.items() if not [t for t in v if sekarang - t < KUNCI_MENIT * 60]]:
                    del gagal[k]
            for k in kunci_kunci:
                gagal[k] = [t for t in gagal.get(k, []) if sekarang - t < KUNCI_MENIT * 60][-50:] + [sekarang]

    @app.route("/masuk", methods=["GET", "POST"])
    @akses("umum")
    def masuk():
        if request.method == "GET":
            return render_template("masuk.html")
        sekarang = time.time()
        nama = request.form.get("pengguna", "")[:80].strip().lower()
        sandi = request.form.get("sandi", "")
        kunci_ip, kunci_akun = "ip:%s" % request.remote_addr, "akun:%s" % nama
        sisa = max(sisa_kunci(kunci_ip, GAGAL_MAKS_IP, sekarang), sisa_kunci(kunci_akun, GAGAL_MAKS_AKUN, sekarang))
        if sisa:
            audit.catat("masuk-ditolak-terkunci", ip=request.remote_addr, pengguna=nama[:60])
            flash("Terlalu banyak percobaan gagal. Coba lagi dalam %d menit." % (sisa // 60 + 1), "galat")
            return render_template("masuk.html"), 429
        a = akun_mod.verifikasi(nama, sandi)
        if a is None:
            catat_gagal([kunci_ip, kunci_akun], sekarang)
            audit.catat("masuk-gagal", ip=request.remote_addr, pengguna=nama[:60])
            flash("Nama pengguna atau kata sandi salah.", "galat")
            return render_template("masuk.html"), 401
        with kunci_gagal:
            gagal.pop(kunci_ip, None)
            gagal.pop(kunci_akun, None)
        session.clear()                       # a new session at every login (no session fixation)
        session.permanent = True
        session["akun_id"] = a["id"]
        session["sidik"] = akun_mod.sidik(a, env["SECRET_KEY"])
        session["masuk_pada"] = int(sekarang)
        token_csrf()
        akun_mod.catat_masuk(a["id"])
        audit.catat("masuk", oleh=a["nama"], ip=request.remote_addr, peran=a["peran"])
        return redirect(url_for("sandi") if a["wajib_ganti"] else url_for("dasbor"))

    @app.route("/keluar", methods=["POST"])
    @akses("masuk")
    def keluar():
        catat("keluar")
        session.clear()
        return redirect(url_for("masuk"))

    @app.route("/akun/sandi", methods=["GET", "POST"])
    @akses("masuk")
    def sandi():
        a = g.akun
        if request.method == "POST":
            baru, ulang = request.form.get("baru", ""), request.form.get("ulang", "")
            try:
                if baru != ulang:
                    raise akun_mod.GagalAkun("Ulangan kata sandi baru tidak sama.")
                akun_mod.ganti_sandi(a["id"], request.form.get("lama", ""), baru)
            except akun_mod.GagalAkun as e:
                flash(str(e), "galat")
                return render_template("sandi.html"), 400
            # this session continues with the new fingerprint; every other session of the account ends
            session["sidik"] = akun_mod.sidik(akun_mod.ambil(a["id"]), env["SECRET_KEY"])
            catat("ganti-sandi")
            flash("Kata sandi diganti. Sesi lain akun ini sudah diakhiri.", "ok")
            return redirect(url_for("dasbor"))
        return render_template("sandi.html")

    # -------------------------------------------------------------- dashboards

    def prodi_terlihat(a):
        semua = sorted((x for x in (info_prodi(k) for k in registri_per_kode()) if x), key=registri.kunci_urut)
        return semua if a["peran"] == "super" else [x for x in semua if x["kode"] in a["prodi"]]

    @app.route("/")
    @akses("masuk")
    def dasbor():
        daftar = prodi_terlihat(g.akun)
        if g.akun["peran"] == "super":
            return render_template("super_dasbor.html", r=alat.ringkasan(), masukan_baru=alat.jumlah_masukan_baru())
        if len(daftar) == 1:
            return redirect(url_for("dasbor_prodi", kode=daftar[0]["kode"]))
        return render_template("dasbor.html", daftar=daftar)

    @app.route("/prodi/<kode>/")
    @akses("prodi")
    def dasbor_prodi(kode):
        import pengumuman
        import tarik_www
        operator = g.akun["peran"] == "operator"
        butir = [b for b in pengumuman.baca(kode)["butir"] if not operator or b.get("oleh") == g.akun["nama"]]
        jumlah = {s: sum(1 for b in butir if b.get("status") == s) for s in pengumuman.STATUS}
        terbaru = sorted(butir, key=lambda b: b.get("diubah", ""), reverse=True)[:5]
        isi = alat.ringkasan_isi(kode)
        siap = []
        if not operator:
            situs = lokasi.baca("prodi/%s/situs" % kode) or {}
            r = registri_per_kode().get(kode, {})
            p = data_prodi.efektif(kode)
            kurang = tarik_www.kekurangan(p) if p else []
            operator_n = sum(1 for a in akun_mod.terlihat_oleh(g.akun, kode) if a["peran"] == "operator" and a["aktif"])
            siap = [
                (not kurang, "Data prodi lengkap" if not kurang else "Data prodi masih kosong: %s" % ", ".join(kurang),
                 url_for("data_prodi_lihat", kode=kode)),
                (bool(r.get("dosen_url")), "Tautan dosen tetap " + ("terpasang" if r.get("dosen_url") else
                                                                   "belum ada (diisi superadmin UPA TIK)"), None),
                (bool(situs.get("logo")), "Logo prodi " + ("terpasang" if situs.get("logo") else "belum ada (opsional)"),
                 url_for("identitas_prodi", kode=kode)),
                (bool(situs.get("beranda") or situs.get("tagline")), "Bagian depan beranda " + (
                    "sudah disesuaikan" if situs.get("beranda") or situs.get("tagline") else "masih bawaan (opsional)"),
                 url_for("beranda_prodi", kode=kode)),
                (operator_n > 0, "%d akun operator aktif" % operator_n, url_for("akun_prodi", kode=kode)),
                (isi["terbit"] == isi["wajib"], "%d dari %d halaman wajib akreditasi terbit" % (isi["terbit"], isi["wajib"]),
                 url_for("isi_daftar", kode=kode)),
            ]
        return render_template("prodi.html", p=g.prodi, jumlah=jumlah, terbaru=terbaru, siap=siap, operator=operator,
                               NAMA_STATUS=pengumuman_admin.NAMA_STATUS, isi=isi)

    # -------------------------------------------------------------- accounts

    def tampil_sandi(sasaran, sandi_baru, kembali):
        """The temporary password, shown once in this response only (never in a redirect, flash or log)."""
        return render_template("sandi_sementara.html", sasaran=sasaran, sandi=sandi_baru, kembali=kembali)

    def daftar_akun(kode=None):
        return render_template("akun.html", daftar=akun_mod.terlihat_oleh(g.akun, kode), kode=kode,
                               p=g.get("prodi"), kelompok=kelompok_prodi() if not kode else [],
                               boleh_kelola=lambda s: akun_mod.boleh_kelola(g.akun, s) and s["id"] != g.akun["id"])

    def buat_akun(kode=None):
        f = request.form
        peran = f.get("peran", "operator")
        prodi = [kode] if kode else prodi_dari_formulir()
        try:
            id_, sandi_baru = akun_mod.buat(g.akun, f.get("nama", ""), f.get("nama_lengkap", ""), peran, prodi)
        except akun_mod.GagalAkun as e:
            flash(str(e), "galat")
            return daftar_akun(kode), 400
        sasaran = akun_mod.ambil(id_)
        catat("akun-dibuat", prodi=sasaran["prodi"], akun=sasaran["nama"], peran=peran)
        return tampil_sandi(sasaran, sandi_baru, url_for("akun_prodi", kode=kode) if kode else url_for("akun_semua"))

    def sasaran_prodi(kode, id_):
        """An account shown under a programme must belong to it (no reaching other accounts through the URL)."""
        sasaran = akun_mod.ambil(id_)
        if not sasaran or kode not in sasaran["prodi"]:
            abort(404)
        return sasaran

    def reset_akun(sasaran, kode, kembali):
        try:
            sandi_baru = akun_mod.reset_sandi(g.akun, sasaran["id"])
        except akun_mod.GagalAkun as e:
            catat("reset-sandi-ditolak", prodi=sasaran["prodi"], akun=sasaran["nama"])
            abort(403, str(e))
        catat("reset-sandi", prodi=sasaran["prodi"], akun=sasaran["nama"])
        return tampil_sandi(sasaran, sandi_baru, kembali)

    def aktif_akun(sasaran, kode, kembali):
        aktif = request.form.get("aktif") == "1"
        try:
            akun_mod.atur_aktif(g.akun, sasaran["id"], aktif)
        except akun_mod.GagalAkun as e:
            if "berwenang" in str(e):
                abort(403, str(e))
            flash(str(e), "galat")
            return redirect(kembali)
        catat("akun-diaktifkan" if aktif else "akun-dinonaktifkan", prodi=sasaran["prodi"], akun=sasaran["nama"])
        flash("Akun %s %s." % (sasaran["nama"], "diaktifkan" if aktif else "dinonaktifkan"), "ok")
        return redirect(kembali)

    @app.route("/prodi/<kode>/akun", methods=["GET"])
    @akses("prodi", "admin")
    def akun_prodi(kode):
        return daftar_akun(kode)

    @app.route("/prodi/<kode>/akun/baru", methods=["POST"])
    @akses("prodi", "admin")
    def akun_prodi_baru(kode):
        return buat_akun(kode)

    @app.route("/prodi/<kode>/akun/<int:id_>/reset", methods=["POST"])
    @akses("prodi", "admin")
    def akun_prodi_reset(kode, id_):
        return reset_akun(sasaran_prodi(kode, id_), kode, url_for("akun_prodi", kode=kode))

    @app.route("/prodi/<kode>/akun/<int:id_>/aktif", methods=["POST"])
    @akses("prodi", "admin")
    def akun_prodi_aktif(kode, id_):
        return aktif_akun(sasaran_prodi(kode, id_), kode, url_for("akun_prodi", kode=kode))

    @app.route("/prodi/<kode>/audit")
    @akses("prodi", "admin")
    def audit_prodi(kode):
        return render_template("audit.html", baris=audit.baca(prodi=kode), p=g.prodi, saring=None)

    @app.route("/super/akun", methods=["GET"])
    @akses("super")
    def akun_semua():
        return daftar_akun()

    @app.route("/super/akun/baru", methods=["POST"])
    @akses("super")
    def akun_semua_baru():
        return buat_akun()

    @app.route("/super/akun/<int:id_>/reset", methods=["POST"])
    @akses("super")
    def akun_semua_reset(id_):
        sasaran = akun_mod.ambil(id_) or abort(404)
        return reset_akun(sasaran, None, url_for("akun_semua"))

    @app.route("/super/akun/<int:id_>/aktif", methods=["POST"])
    @akses("super")
    def akun_semua_aktif(id_):
        sasaran = akun_mod.ambil(id_) or abort(404)
        return aktif_akun(sasaran, None, url_for("akun_semua"))

    @app.route("/super/audit")
    @akses("super")
    def audit_semua():
        saring = {"prodi": request.args.get("prodi", ""), "oleh": request.args.get("oleh", ""), "aksi": request.args.get("aksi", "")}
        if (saring["prodi"] and not POLA_KODE.match(saring["prodi"])) or (saring["oleh"] and not POLA_NAMA_AKUN.match(saring["oleh"])) \
                or (saring["aksi"] and not POLA_AKSI.match(saring["aksi"])):
            abort(404)
        baris = audit.baca(prodi=saring["prodi"] or None, oleh=saring["oleh"] or None, aksi=saring["aksi"] or None, batas=500)
        return render_template("audit.html", baris=baris, p=None, saring=saring, jenis_aksi=audit.jenis_aksi(),
                               semua_prodi=prodi_terlihat(g.akun))

    # -------------------------------------------------------------- superadmin pages (superadmin.py)

    class Alat(object):
        pass
    alat = Alat()
    alat.catat, alat.antrean, alat.penjadwal, alat.info_prodi = catat, antrean, penjadwal, info_prodi
    alat.kelompok_prodi, alat.prodi_dari_formulir = kelompok_prodi, prodi_dari_formulir
    superadmin.pasang(app, alat)
    prodi_admin.pasang(app, alat)
    pengumuman_admin.pasang(app, alat)
    isi_admin.pasang(app, alat)
    impor_tabel.pasang(app, alat)
    kriteria_admin.pasang(app, alat)
    tambahan_admin.pasang(app, alat)
    panduan.pasang(app, alat)
    masukan_admin.pasang(app, alat)
    app.antrean, app.penjadwal = antrean, penjadwal

    # -------------------------------------------------------------- errors

    PESAN = {400: "Permintaan tidak dapat diproses.", 403: "Anda tidak berwenang membuka halaman ini.",
             404: "Halaman tidak ditemukan.", 405: "Cara membuka halaman ini tidak diizinkan.",
             413: "Berkas atau formulir terlalu besar.", 429: "Terlalu banyak permintaan."}

    def galat(e):
        kode = getattr(e, "code", 500)
        # a message given with abort(kode, "...") here is shown; Werkzeug's own (English) default text is not
        pesan = e.description if getattr(e, "description", None) and e.description != type(e).description else PESAN.get(kode, "")
        return render_template("galat.html", kode=kode, pesan=pesan), kode

    for k in PESAN:
        app.register_error_handler(k, galat)

    # every route must declare its access (checked here too, so a mistake shows at start-up, not in production)
    tanpa = [ep for ep, f in app.view_functions.items() if ep != "static" and not hasattr(f, "akses")]
    if tanpa:
        raise SystemExit("rute tanpa deklarasi akses: %s" % ", ".join(sorted(tanpa)))
    app.port = int(env.get("PORT") or 8791)
    return app


if __name__ == "__main__":
    from werkzeug.serving import WSGIRequestHandler
    # do not tell visitors which server and Python version run here
    WSGIRequestHandler.server_version, WSGIRequestHandler.sys_version = "prodi-admin", ""
    aplikasi = buat_app()
    # local only: never bind to 0.0.0.0, never turn on the debugger (it runs any code it is sent)
    aplikasi.run(host="127.0.0.1", port=aplikasi.port, debug=False)
