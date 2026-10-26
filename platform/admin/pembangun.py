# -*- coding: utf-8 -*-
"""Rebuilding the published sites after a change in the admin (langkah 5).

The admin asks for a rebuild of one programme (its pages and the root pages) or of everything; the builder
(platform/bangun/bangun.py) runs in its own process, one build at a time. Requests that arrive during a build are
merged and run once it is done: several programmes become one full build when there are more than BATAS_SATUAN of
them, and a full build covers every programme request.

PRODI_BANGUN chooses how builds run:
    latar    (default) in a background thread, so a form answers at once; the dashboard shows the status
    sinkron  inside the request (tests)
    mati     not at all (tests of the access rules, which change data without building)

PRODI_BANGUN_HARIAN ("HH:MM", local time; empty: none) adds a full rebuild every day (Penjadwal), so announcements
whose "berlaku sampai" date has passed leave the sites even when nobody changes anything.
"""
from __future__ import print_function

import datetime
import os
import re
import subprocess
import sys
import threading
import time

ADMIN = os.path.dirname(os.path.abspath(__file__))
PLATFORM = os.path.dirname(ADMIN)
sys.path.insert(0, ADMIN)

import audit  # noqa: E402

BANGUN_PY = os.path.join(PLATFORM, "bangun", "bangun.py")
BATAS_SATUAN = 5
BATAS_DETIK = 900
MODE = ("latar", "sinkron", "mati")
POLA_JAM = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


class Antrean(object):
    def __init__(self, mode="latar"):
        if mode not in MODE:
            raise ValueError("PRODI_BANGUN harus salah satu dari: %s" % ", ".join(MODE))
        self.mode = mode
        self._kunci = threading.Lock()
        self._menunggu = set()            # programme codes; None = everything
        self._berjalan = False
        self.status = {"berjalan": False, "ok": True, "pesan": "Belum ada pembangunan ulang sejak admin dimulai.",
                       "waktu": None, "cakupan": "", "durasi": None, "peringatan": [], "keluaran": "",
                       "menunggu": 0}

    def minta(self, kode=None, oleh="-"):
        """Ask for a rebuild of programme `kode` (None: everything)."""
        with self._kunci:
            if self.mode == "mati":
                self.status.update(pesan="Bangun ulang dimatikan (PRODI_BANGUN=mati).", cakupan=kode or "semua")
                return
            self._menunggu.add(kode)
            self.status["menunggu"] = len(self._menunggu)
            if self._berjalan:
                return                    # the running worker takes it after the current build
            self._berjalan = True
        if self.mode == "sinkron":
            self._kerja(oleh)
        else:
            threading.Thread(target=self._kerja, args=(oleh,), name="bangun-ulang", daemon=True).start()

    def _ambil(self):
        with self._kunci:
            if not self._menunggu:
                self._berjalan = False
                self.status["menunggu"] = 0
                return None
            tugas = [None] if None in self._menunggu or len(self._menunggu) > BATAS_SATUAN else sorted(self._menunggu)
            self._menunggu.clear()
            self.status["menunggu"] = 0
            return tugas

    def _kerja(self, oleh):
        while True:
            tugas = self._ambil()
            if tugas is None:
                return
            for kode in tugas:
                self._satu(kode, oleh)

    def _satu(self, kode, oleh):
        cakupan = kode or "semua"
        perintah = [sys.executable, BANGUN_PY] + (["--prodi", kode] if kode else [])
        self.status.update(berjalan=True, cakupan=cakupan, pesan="Sedang membangun ulang (%s)…" % cakupan)
        mulai = time.time()
        try:
            hasil = subprocess.run(perintah, capture_output=True, text=True, timeout=BATAS_DETIK, env=os.environ.copy())
            ok, keluaran = hasil.returncode == 0, (hasil.stdout or "") + (hasil.stderr or "")
        except subprocess.TimeoutExpired:
            ok, keluaran = False, "Bangun ulang dihentikan: lebih dari %d detik." % BATAS_DETIK
        except OSError as e:
            ok, keluaran = False, "Bangun ulang tidak dapat dijalankan: %s" % e
        baris = [b for b in keluaran.splitlines() if b.strip()]
        peringatan = [b[len("PERINGATAN "):] for b in baris if b.startswith("PERINGATAN ")]
        ringkas = [b for b in baris if not b.startswith("PERINGATAN ")]
        durasi = round(time.time() - mulai, 1)
        self.status.update(berjalan=False, ok=ok, cakupan=cakupan, durasi=durasi, peringatan=peringatan[:100],
                           keluaran="\n".join(baris[-80:]), waktu=datetime.datetime.now().isoformat(timespec="seconds"),
                           pesan=(ringkas[-1] if ringkas else "Selesai.") if ok else "Bangun ulang GAGAL (%s)." % cakupan)
        audit.catat("bangun-selesai" if ok else "bangun-gagal", oleh=oleh, prodi=kode, cakupan=cakupan, detik=durasi,
                    peringatan=len(peringatan))


class Penjadwal(object):
    """A full rebuild every day at `jam` ("HH:MM", local time; the containers run in Asia/Makassar), through the same
    queue as the admin's own rebuilds. Started by app.py when PRODI_BANGUN_HARIAN is set and builds run in the
    background."""

    def __init__(self, antrean, jam):
        m = POLA_JAM.match(jam or "")
        if not m:
            raise ValueError("PRODI_BANGUN_HARIAN harus berbentuk JJ:MM, mis. 02:30")
        self.antrean, self.jam, self.menit = antrean, int(m.group(1)), int(m.group(2))
        self.terakhir = None

    def berikutnya(self, sekarang=None):
        """When the next daily rebuild runs."""
        sekarang = sekarang or datetime.datetime.now()
        hari_ini = sekarang.replace(hour=self.jam, minute=self.menit, second=0, microsecond=0)
        return hari_ini if hari_ini > sekarang else hari_ini + datetime.timedelta(days=1)

    def mulai(self):
        threading.Thread(target=self._jalan, name="bangun-harian", daemon=True).start()
        return self

    def _jalan(self):
        while True:
            jadwal = self.berikutnya()
            # short sleeps, so a changed clock (or a VM that was paused) does not move the rebuild by hours
            while datetime.datetime.now() < jadwal:
                time.sleep(min(60, max(1, (jadwal - datetime.datetime.now()).total_seconds())))
            try:
                self.bangun(jadwal)
            except Exception as e:            # the thread must live on to the next day; the container log shows it
                print("PERINGATAN: bangun ulang harian %s tidak dapat dimulai: %s" % (jadwal, e), flush=True)

    def bangun(self, jadwal=None):
        """The daily rebuild itself."""
        self.terakhir = (jadwal or datetime.datetime.now()).isoformat(timespec="minutes")
        audit.catat("bangun-terjadwal", oleh="penjadwal", cakupan="semua")
        self.antrean.minta(None, "penjadwal")
