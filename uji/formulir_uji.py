# -*- coding: utf-8 -*-
"""Helpers shared by the suites of the page editor (uji_penyunting.py, uji_alur_isi.py): sample files, a programme of
www's data, and Formulir, which reads a form the way a browser sends it. Not a suite itself (no uji_ prefix)."""
from __future__ import print_function

import io
from html.parser import HTMLParser

from PIL import Image
from werkzeug.datastructures import MultiDict


def gambar(lebar, tinggi):
    buf = io.BytesIO()
    Image.new("RGB", (lebar, tinggi), (20, 60, 160)).save(buf, "JPEG")
    return buf.getvalue()


def pdf():
    isi = b"BT /F1 24 Tf 72 720 Td (Dokumen) Tj ET"
    objek = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
             b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
             b"<< /Length %d >>\nstream\n" % len(isi) + isi + b"\nendstream", b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    keluar, letak = bytearray(b"%PDF-1.4\n"), []
    for i, o in enumerate(objek, 1):
        letak.append(len(keluar))
        keluar += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    xref = len(keluar)
    keluar += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objek) + 1) + b"".join(b"%010d 00000 n \n" % x for x in letak)
    keluar += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objek) + 1, xref)
    return bytes(keluar)


def prodi(kode, nama):
    return {"kode_pddikti": kode, "nama": nama, "nama_en": "", "jenjang": "S1", "gelar": "S.Kom.", "sks": 144, "unit_kode": "ft",
            "unit": "Fakultas Teknik", "website": "", "surel": "p@unsrat.ac.id", "bidang_kerja": "B.", "bidang_kerja_en": "",
            "akreditasi": "Unggul", "lembaga_akreditasi": "LAM-Infokom", "berlaku_hingga": "", "internasional": "", "slug": "x",
            "slug_en": "", "cpl": [{"kode": "CPL 1", "isi": "Capaian.", "isi_en": "", "kurikulum": "2025/2026"}]}


class Formulir(HTMLParser):
    """What a browser sends for a form (no button pressed), and what the page holds for checks: ids, labels, the
    controls that need a label. semua: every field of the document (a form's fields without their <form>)."""

    def __init__(self, html, semua=False):
        HTMLParser.__init__(self, convert_charrefs=True)
        self.isian, self.berkas, self.id, self.label_for, self.kontrol = [], [], [], set(), []
        self.dalam, self._area, self._pilih = semua, None, None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.id.append(a["id"])
        if tag == "form" and "formulir--sunting" in (a.get("class") or ""):
            self.dalam = True
        if not self.dalam:
            return
        if tag == "label" and a.get("for"):
            self.label_for.add(a["for"])
        if tag == "input":
            jenis = a.get("type", "text")
            if jenis in ("text", "hidden"):
                self.isian.append((a["name"], a.get("value", "")))
            elif jenis == "checkbox" and "checked" in a:
                self.isian.append((a["name"], a.get("value", "on")))
            elif jenis == "file":
                self.berkas.append(a["name"])
            if jenis != "hidden" and a.get("id"):
                self.kontrol.append(a["id"])
            elif jenis not in ("hidden", "checkbox"):
                self.kontrol.append(None)
        elif tag == "textarea":
            self._area = [a["name"], ""]
            self.kontrol.append(a.get("id"))
        elif tag == "select":
            self._pilih = [a["name"], None, None]
            self.kontrol.append(a.get("id"))
        elif tag == "option" and self._pilih is not None:
            if self._pilih[1] is None:
                self._pilih[1] = a.get("value", "")
            if "selected" in a:
                self._pilih[2] = a.get("value", "")

    def handle_data(self, data):
        if self._area is not None:
            self._area[1] += data

    def handle_endtag(self, tag):
        if tag == "form":
            self.dalam = False
        elif tag == "textarea" and self._area is not None:
            nama, isi = self._area
            # a browser's parser drops the first new line of a text area, and sends line ends as CRLF
            self.isian.append((nama, (isi[1:] if isi.startswith("\n") else isi).replace("\n", "\r\n")))
            self._area = None
        elif tag == "select" and self._pilih is not None:
            nama, pertama, pilih = self._pilih
            self.isian.append((nama, pilih if pilih is not None else pertama))
            self._pilih = None

    def data(self, ubah=None, aksi=None):
        isian = MultiDict(self.isian)
        for k, v in (ubah or {}).items():
            if v is None:
                isian.poplist(k)
            else:
                isian[k] = v
        if aksi:
            isian["aksi"] = aksi
        return isian
