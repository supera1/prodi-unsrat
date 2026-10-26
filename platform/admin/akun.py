# -*- coding: utf-8 -*-
"""Accounts of the admin (langkah 4): one account per person, in SQLite (<PRODI_RAHASIA>/akun.sqlite).

Roles (K-P2):
    super     UPA TIK; every programme; manages every account
    admin     a programme's coordinator; the programmes listed for the account; manages its operators
    operator  writes content for the programmes listed for the account (content editing comes in langkah 6)

Passwords (K-P10, no 2FA): argon2; at least SANDI_MIN characters with letters and digits, not a common password, not
containing the user name, the person's name or a name of the account's programmes, and different from the previous
one. A new or reset account gets a temporary password that must be changed at the first login. There is no e-mail
(K-P12): the owner changes it, the superadmin may reset anyone's, a programme admin its operators'.

Who may manage whom (boleh_kelola): the superadmin anyone; a programme admin an operator all of whose programmes
are among its own. Nobody deactivates their own account, and the last active superadmin cannot be deactivated.
"""
from __future__ import print_function

import datetime
import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import sys
import threading

PLATFORM = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PLATFORM)
sys.path.insert(0, os.path.join(PLATFORM, "pemantau"))

from argon2 import PasswordHasher  # noqa: E402
from argon2.exceptions import InvalidHash, VerificationError, VerifyMismatchError  # noqa: E402

import lokasi  # noqa: E402
import saringan_spam  # noqa: E402

PERAN = ("super", "admin", "operator")
NAMA_PERAN = {"super": "Superadmin", "admin": "Admin prodi (koordinator)", "operator": "Operator prodi"}
SANDI_MIN = {"super": 16, "admin": 12, "operator": 12}
SANDI_MAKS = 512
POLA_NAMA = re.compile(r"^[a-z][a-z0-9._-]{2,31}$")
POLA_KODE = re.compile(r"^[0-9A-Za-z]{3,12}$")
VERSI_SKEMA = 1

# whole passwords and pieces that make a password easy to guess (checked in lower case, without spaces)
UMUM = {"password", "passw0rd", "password1", "password123", "qwerty", "qwertyuiop", "asdfghjkl", "iloveyou",
        "admin123", "administrator", "welcome", "letmein", "monkey", "dragon", "sunshine", "princess", "football",
        "abc123", "1q2w3e4r", "zaq12wsx", "bismillah", "sayangku", "indonesia", "rahasia", "katasandi",
        "unsrat", "unsrat123", "manado", "sulut", "samratulangi"}
POTONGAN_UMUM = ("password", "passw0rd", "qwerty", "asdf", "123456", "654321", "abcdef", "unsrat", "admin", "rahasia",
                 "katasandi", "sandi", "manado", "bismillah", "iloveyou", "sayang", "12345678")

_hasher = PasswordHasher()
_HASH_SEMU = _hasher.hash(secrets.token_urlsafe(24))   # checked for unknown names, so they take as long
_kunci = threading.Lock()


class GagalAkun(ValueError):
    pass


def _sekarang():
    return datetime.datetime.now().isoformat(timespec="seconds")


# ------------------------------------------------------------------ database

def path_db():
    return os.path.join(lokasi.rahasia(), "akun.sqlite")


def sambung():
    """A connection with foreign keys on; creates the database and its tables on first use."""
    os.makedirs(lokasi.rahasia(), exist_ok=True)
    baru = not os.path.isfile(path_db())
    db = sqlite3.connect(path_db(), timeout=10, isolation_level=None)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    db.execute("PRAGMA journal_mode = WAL")
    if baru:
        os.chmod(path_db(), 0o600)
    db.executescript("""
        CREATE TABLE IF NOT EXISTS meta (kunci TEXT PRIMARY KEY, nilai TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS akun (
            id INTEGER PRIMARY KEY,
            nama TEXT NOT NULL UNIQUE,
            nama_lengkap TEXT NOT NULL,
            peran TEXT NOT NULL CHECK (peran IN ('super', 'admin', 'operator')),
            hash TEXT NOT NULL,
            wajib_ganti INTEGER NOT NULL DEFAULT 1,
            aktif INTEGER NOT NULL DEFAULT 1,
            dibuat TEXT NOT NULL,
            dibuat_oleh TEXT NOT NULL,
            diubah TEXT NOT NULL,
            sandi_diubah TEXT NOT NULL,
            masuk_terakhir TEXT
        );
        CREATE TABLE IF NOT EXISTS anggota (
            akun_id INTEGER NOT NULL REFERENCES akun(id) ON DELETE CASCADE,
            kode_prodi TEXT NOT NULL,
            PRIMARY KEY (akun_id, kode_prodi)
        );
    """)
    db.execute("INSERT OR IGNORE INTO meta (kunci, nilai) VALUES ('versi_skema', ?)", (str(VERSI_SKEMA),))
    return db


def _baris_ke_akun(db, r):
    if r is None:
        return None
    akun = dict(r)
    akun["prodi"] = [x["kode_prodi"] for x in db.execute(
        "SELECT kode_prodi FROM anggota WHERE akun_id = ? ORDER BY kode_prodi", (akun["id"],))]
    akun["aktif"] = bool(akun["aktif"])
    akun["wajib_ganti"] = bool(akun["wajib_ganti"])
    return akun


def ambil(id_):
    db = sambung()
    try:
        return _baris_ke_akun(db, db.execute("SELECT * FROM akun WHERE id = ?", (id_,)).fetchone())
    finally:
        db.close()


def ambil_nama(nama):
    db = sambung()
    try:
        return _baris_ke_akun(db, db.execute("SELECT * FROM akun WHERE nama = ?", ((nama or "").strip().lower(),)).fetchone())
    finally:
        db.close()


def semua():
    db = sambung()
    try:
        return [_baris_ke_akun(db, r) for r in db.execute("SELECT * FROM akun ORDER BY peran = 'operator', peran, nama")]
    finally:
        db.close()


def jumlah_super_aktif(db):
    return db.execute("SELECT COUNT(*) FROM akun WHERE peran = 'super' AND aktif = 1").fetchone()[0]


# ------------------------------------------------------------------ passwords

def nama_prodi(kode):
    p = {x["kode_pddikti"]: x for x in (lokasi.baca("warisan/prodi") or {}).get("program", [])}.get(kode)
    return p["nama"] if p else ""


def periksa_sandi(sandi, peran, nama="", nama_lengkap="", prodi=(), hash_lama=None):
    """Problems with a new password (empty list when it may be used)."""
    masalah = []
    if not isinstance(sandi, str) or not sandi:
        return ["Kata sandi wajib diisi."]
    minimal = SANDI_MIN.get(peran, 12)
    if len(sandi) < minimal:
        masalah.append("Kata sandi minimal %d karakter." % minimal)
    if len(sandi) > SANDI_MAKS:
        masalah.append("Kata sandi terlalu panjang.")
    if not re.search(r"[A-Za-z]", sandi) or not re.search(r"[0-9]", sandi):
        masalah.append("Kata sandi harus memuat huruf dan angka.")
    rapat = re.sub(r"\s+", "", sandi.lower())
    if len(set(rapat)) < 6:
        masalah.append("Kata sandi terlalu banyak mengulang karakter yang sama.")
    if rapat in UMUM or re.sub(r"[^a-z]", "", rapat) in UMUM or any(p in rapat for p in POTONGAN_UMUM):
        masalah.append("Kata sandi terlalu mudah ditebak (memuat kata atau pola yang umum).")
    kata = set()
    if nama and len(nama) >= 3:
        kata.add(nama.lower())
    for sumber in [nama_lengkap] + [nama_prodi(k) for k in prodi]:
        kata.update(w for w in re.findall(r"[a-z]+", (sumber or "").lower()) if len(w) >= 4)
    ketemu = sorted(w for w in kata if w in rapat)
    if ketemu:
        masalah.append("Kata sandi tidak boleh memuat nama pengguna, nama Anda, atau nama prodi (%s)." % ", ".join(ketemu))
    if hash_lama:
        try:
            if _hasher.verify(hash_lama, sandi[:SANDI_MAKS]):
                masalah.append("Kata sandi baru harus berbeda dari yang lama.")
        except (VerifyMismatchError, VerificationError, InvalidHash):
            pass
    return masalah


def buat_sandi_sementara():
    """A random password that passes periksa_sandi for any role: four groups of letters and digits."""
    huruf = "abcdefghjkmnpqrstuvwxyz23456789"          # no 0/o, 1/l/i: read off a screen and typed again
    while True:
        sandi = "-".join("".join(secrets.choice(huruf) for _ in range(5)) for _ in range(4))
        if not periksa_sandi(sandi, "super"):
            return sandi


def verifikasi(nama, sandi):
    """The active account whose name and password match, or None. Takes as long for an unknown name."""
    akun = ambil_nama(nama) if POLA_NAMA.match((nama or "").strip().lower()) else None
    hash_ = akun["hash"] if akun else _HASH_SEMU
    try:
        cocok = _hasher.verify(hash_, (sandi or "")[:SANDI_MAKS]) and len(sandi or "") <= SANDI_MAKS
    except (VerifyMismatchError, VerificationError, InvalidHash):
        cocok = False
    if not cocok or akun is None or not akun["aktif"]:
        return None
    if _hasher.check_needs_rehash(akun["hash"]):
        db = sambung()
        try:
            db.execute("UPDATE akun SET hash = ? WHERE id = ?", (_hasher.hash(sandi), akun["id"]))
        finally:
            db.close()
        akun = ambil(akun["id"])
    return akun


def sidik(akun, kunci_rahasia):
    """Fingerprint of the account's password hash and status, kept in the session at login: a new password or a
    deactivation ends every session of the account (a session cookie alone cannot be revoked)."""
    isi = "%s|%s|%s|%s" % (akun["id"], akun["hash"], akun["aktif"], kunci_rahasia)
    return hashlib.sha256(isi.encode("utf-8")).hexdigest()[:32]


def sidik_cocok(akun, kunci_rahasia, nilai):
    return bool(akun) and hmac.compare_digest(sidik(akun, kunci_rahasia), str(nilai or ""))


# ------------------------------------------------------------------ access

def akses_prodi(akun, kode):
    """May this account work on programme `kode` at all."""
    return bool(akun and akun["aktif"] and (akun["peran"] == "super" or kode in akun["prodi"]))


def boleh_kelola(pelaku, sasaran):
    """May `pelaku` reset the password of, or (de)activate, `sasaran`."""
    if not pelaku or not sasaran or not pelaku["aktif"]:
        return False
    if pelaku["peran"] == "super":
        return True
    return (pelaku["peran"] == "admin" and sasaran["peran"] == "operator" and bool(sasaran["prodi"])
            and set(sasaran["prodi"]) <= set(pelaku["prodi"]))


def terlihat_oleh(pelaku, kode=None):
    """Accounts `pelaku` may see: the superadmin all (or a programme's members); an admin itself and the operators
    and admins of its programmes (kode: one of them only)."""
    hasil = []
    for a in semua():
        if kode and kode not in a["prodi"]:
            continue
        if pelaku["peran"] == "super" or a["id"] == pelaku["id"] or (
                pelaku["peran"] == "admin" and set(a["prodi"]) & set(pelaku["prodi"])):
            hasil.append(a)
    return hasil


# ------------------------------------------------------------------ changes

def _periksa_isian(nama, nama_lengkap, peran, prodi):
    masalah = []
    if not POLA_NAMA.match(nama or ""):
        masalah.append("Nama pengguna 3-32 karakter: huruf kecil, angka, titik, garis bawah, atau tanda hubung; "
                       "diawali huruf.")
    nl = (nama_lengkap or "").strip()
    if not 2 <= len(nl) <= 100 or re.search(r"[<>\x00-\x1f]", nl):
        masalah.append("Nama lengkap 2-100 karakter, tanpa < atau >.")
    elif saringan_spam.cari(nl):
        masalah.append("Nama lengkap memuat istilah terlarang.")
    if peran not in PERAN:
        masalah.append("Peran tidak dikenal.")
    terdaftar = {r["kode_pddikti"] for r in (lokasi.baca("registri") or {}).get("prodi", [])}
    if peran == "super" and prodi:
        masalah.append("Superadmin tidak dibatasi pada prodi tertentu.")
    if peran in ("admin", "operator"):
        if not prodi:
            masalah.append("Admin prodi dan operator harus terhubung ke paling sedikit satu prodi.")
        for k in prodi:
            if not POLA_KODE.match(k) or k not in terdaftar:
                masalah.append("Prodi %s tidak terdaftar." % k)
    return masalah


def buat(pelaku, nama, nama_lengkap, peran, prodi=()):
    """Create an account. Returns (id, temporary password); the password is shown once and never stored in clear.
    pelaku: the account doing it (None only for the first superadmin, from the command line)."""
    nama = (nama or "").strip().lower()
    prodi = sorted(set(prodi or ()))
    masalah = _periksa_isian(nama, nama_lengkap, peran, prodi)
    if pelaku is not None:
        if pelaku["peran"] == "admin":
            if peran != "operator":
                masalah.append("Admin prodi hanya dapat membuat akun operator.")
            if not set(prodi) <= set(pelaku["prodi"]):
                masalah.append("Admin prodi hanya dapat membuat operator untuk prodinya sendiri.")
        elif pelaku["peran"] != "super":
            masalah.append("Akun ini tidak dapat membuat akun.")
    if masalah:
        raise GagalAkun(" ".join(masalah))
    sandi = buat_sandi_sementara()
    waktu = _sekarang()
    db = sambung()
    try:
        with _kunci:
            if db.execute("SELECT 1 FROM akun WHERE nama = ?", (nama,)).fetchone():
                raise GagalAkun("Nama pengguna %s sudah dipakai." % nama)
            db.execute("BEGIN IMMEDIATE")
            cur = db.execute("INSERT INTO akun (nama, nama_lengkap, peran, hash, wajib_ganti, aktif, dibuat, dibuat_oleh, "
                             "diubah, sandi_diubah) VALUES (?, ?, ?, ?, 1, 1, ?, ?, ?, ?)",
                             (nama, nama_lengkap.strip(), peran, _hasher.hash(sandi), waktu,
                              pelaku["nama"] if pelaku else "baris-perintah", waktu, waktu))
            db.executemany("INSERT INTO anggota (akun_id, kode_prodi) VALUES (?, ?)", [(cur.lastrowid, k) for k in prodi])
            db.execute("COMMIT")
            return cur.lastrowid, sandi
    except sqlite3.Error:
        if db.in_transaction:
            db.execute("ROLLBACK")
        raise
    finally:
        db.close()


def ganti_sandi(akun_id, sandi_lama, sandi_baru):
    """The owner sets a new password (also the forced change after a temporary one)."""
    akun = ambil(akun_id)
    if not akun or not akun["aktif"]:
        raise GagalAkun("Akun tidak aktif.")
    try:
        _hasher.verify(akun["hash"], (sandi_lama or "")[:SANDI_MAKS])
    except (VerifyMismatchError, VerificationError, InvalidHash):
        raise GagalAkun("Kata sandi lama salah.")
    masalah = periksa_sandi(sandi_baru, akun["peran"], akun["nama"], akun["nama_lengkap"], akun["prodi"], akun["hash"])
    if masalah:
        raise GagalAkun(" ".join(masalah))
    db = sambung()
    try:
        db.execute("UPDATE akun SET hash = ?, wajib_ganti = 0, sandi_diubah = ?, diubah = ? WHERE id = ?",
                   (_hasher.hash(sandi_baru), _sekarang(), _sekarang(), akun_id))
    finally:
        db.close()


def reset_sandi(pelaku, sasaran_id):
    """A new temporary password for another account (shown once); every session of that account ends."""
    sasaran = ambil(sasaran_id)
    if not sasaran:
        raise GagalAkun("Akun tidak ditemukan.")
    if sasaran["id"] == pelaku["id"]:
        raise GagalAkun("Ganti kata sandi Anda sendiri lewat menu Kata sandi.")
    if not boleh_kelola(pelaku, sasaran):
        raise GagalAkun("Anda tidak berwenang atas akun ini.")
    sandi = buat_sandi_sementara()
    db = sambung()
    try:
        db.execute("UPDATE akun SET hash = ?, wajib_ganti = 1, sandi_diubah = ?, diubah = ? WHERE id = ?",
                   (_hasher.hash(sandi), _sekarang(), _sekarang(), sasaran_id))
    finally:
        db.close()
    return sandi


def atur_aktif(pelaku, sasaran_id, aktif):
    sasaran = ambil(sasaran_id)
    if not sasaran:
        raise GagalAkun("Akun tidak ditemukan.")
    if sasaran["id"] == pelaku["id"]:
        raise GagalAkun("Anda tidak dapat menonaktifkan akun sendiri.")
    if not boleh_kelola(pelaku, sasaran):
        raise GagalAkun("Anda tidak berwenang atas akun ini.")
    db = sambung()
    try:
        with _kunci:
            if not aktif and sasaran["peran"] == "super" and sasaran["aktif"] and jumlah_super_aktif(db) <= 1:
                raise GagalAkun("Superadmin aktif terakhir tidak dapat dinonaktifkan.")
            db.execute("UPDATE akun SET aktif = ?, diubah = ? WHERE id = ?", (1 if aktif else 0, _sekarang(), sasaran_id))
    finally:
        db.close()


def catat_masuk(akun_id):
    db = sambung()
    try:
        db.execute("UPDATE akun SET masuk_terakhir = ? WHERE id = ?", (_sekarang(), akun_id))
    finally:
        db.close()
