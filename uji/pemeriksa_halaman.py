# -*- coding: utf-8 -*-
"""Checks every page of a built site (used by uji_bangun.py and uji_pengumuman.py; not a test suite itself):
one h1, lang, title and description, CSP, no inline styles or scripts or on* handlers, valid JSON-LD, heading order,
image alternatives, unique ids, anchors, aria-current pointing at the page itself, and every link or file reference
inside the site leading to a file that exists.
"""
from __future__ import print_function

import io
import json
import os
import re
from html.parser import HTMLParser


class Pengurai(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self, convert_charrefs=True)
        self.tag, self.judul, self.dalam_judul, self.ld = [], "", False, []
        self.dalam_ld = False

    def handle_starttag(self, tag, attrs):
        self.tag.append((tag, dict(attrs)))
        if tag == "title":
            self.dalam_judul = True
        if tag == "script" and dict(attrs).get("type") == "application/ld+json":
            self.dalam_ld = True
            self.ld.append("")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag == "title":
            self.dalam_judul = False
        if tag == "script":
            self.dalam_ld = False

    def handle_data(self, data):
        if self.dalam_judul:
            self.judul += data
        if self.dalam_ld:
            self.ld[-1] += data


def _tujuan(publik, rel_halaman, href):
    """Path of the file a link inside the site points to, or None for links that leave the site."""
    if re.match(r"^[a-z][a-z0-9+.-]*:", href) or href.startswith("//"):
        return None
    jalur = href.split("#")[0].split("?")[0]
    if not jalur:
        return None
    if jalur.startswith("/"):
        hasil = os.path.normpath(os.path.join(publik, jalur.lstrip("/")))
    else:
        hasil = os.path.normpath(os.path.join(publik, os.path.dirname(rel_halaman), jalur))
    if href.split("#")[0].split("?")[0].endswith("/") or os.path.isdir(hasil):
        hasil = os.path.join(hasil, "index.html")
    return hasil


def periksa_situs(publik, label):
    """Check every page in a built site. Returns (pages checked, [finding, ...])."""
    temuan, jumlah = [], 0
    for folder, _d, nama in os.walk(publik):
        for n in nama:
            if not n.endswith(".html"):
                continue
            jumlah += 1
            path = os.path.join(folder, n)
            rel = os.path.relpath(path, publik).replace(os.sep, "/")
            with io.open(path, encoding="utf-8") as f:
                teks = f.read()
            p = Pengurai()
            p.feed(teks)
            tag = p.tag
            html = [a for t, a in tag if t == "html"]
            if not html or html[0].get("lang") != "id":
                temuan.append((rel, "lang bukan id"))
            if sum(1 for t, _a in tag if t == "h1") != 1:
                temuan.append((rel, "jumlah h1 bukan 1"))
            if not p.judul.strip():
                temuan.append((rel, "judul kosong"))
            if not any(t == "meta" and a.get("name") == "description" and (a.get("content") or "").strip() for t, a in tag):
                temuan.append((rel, "meta description kosong"))
            if not any(t == "meta" and a.get("http-equiv") == "Content-Security-Policy" for t, a in tag):
                temuan.append((rel, "tanpa CSP"))
            for t, a in tag:
                if "style" in a:
                    temuan.append((rel, "atribut style pada <%s>" % t))
                if any(k.startswith("on") for k in a):
                    temuan.append((rel, "atribut on* pada <%s>" % t))
                if t == "script" and a.get("type") != "application/ld+json":
                    temuan.append((rel, "skrip selain JSON-LD"))
                if t == "img" and "alt" not in a:
                    temuan.append((rel, "gambar tanpa alt"))
            for ld in p.ld:
                try:
                    json.loads(ld)
                except ValueError:
                    temuan.append((rel, "JSON-LD tidak sah"))
            tingkat = [int(t[1]) for t, _a in tag if re.match(r"^h[1-6]$", t)]
            for a, b in zip(tingkat, tingkat[1:]):
                if b > a + 1:
                    temuan.append((rel, "heading melompat h%d -> h%d" % (a, b)))
                    break
            ids = [a["id"] for _t, a in tag if "id" in a]
            if len(ids) != len(set(ids)):
                temuan.append((rel, "id ganda"))
            for _t, a in tag:
                if a.get("aria-current") == "page" and a.get("href"):
                    if os.path.normpath(_tujuan(publik, rel, a["href"]) or "") != os.path.normpath(path):
                        temuan.append((rel, "aria-current=page menunjuk ke halaman lain: %s" % a["href"]))
            for t, a in tag:
                for atr in ("href", "src"):
                    href = a.get(atr)
                    if not href:
                        continue
                    if href.startswith("#"):
                        if href[1:] and href[1:] not in ids:
                            temuan.append((rel, "anker %s tidak ada" % href))
                        continue
                    tujuan = _tujuan(publik, rel, href)
                    if tujuan and not os.path.isfile(tujuan):
                        temuan.append((rel, "tautan mati %s" % href))
    hasil = ["%s %s: %s" % (label, rel, m) for rel, m in temuan[:30]]
    if len(temuan) > 30:
        hasil.append("%s: ... dan %d temuan lain" % (label, len(temuan) - 30))
    return jumlah, hasil
