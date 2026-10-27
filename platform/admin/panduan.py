# -*- coding: utf-8 -*-
"""The guide for programme admins and operators (docs/panduan-admin-prodi.md) as a page of the admin, /panduan (Fase 2
langkah 5): the repository is not open to them, the admin is.

The guide is written in a small part of Markdown, rendered here with every character escaped first, so a mistake in the
file can never put markup on the page: headings (#, ##, ###, with ids to link to), paragraphs, "- " and "1. " lists
(one level, and "  - " under an item), tables, "> " quotes, fenced code, **bold**, `code`, and links to #anchors of the
guide or to https:// addresses (anything else stays text).
"""
from __future__ import print_function

import html
import io
import os
import re
import sys

ADMIN = os.path.dirname(os.path.abspath(__file__))
AKAR = os.path.dirname(os.path.dirname(ADMIN))
sys.path.insert(0, ADMIN)

from flask import render_template  # noqa: E402
from markupsafe import Markup  # noqa: E402

from akses import akses  # noqa: E402

PANDUAN = os.path.join(AKAR, "docs", "panduan-admin-prodi.md")
URL_SAH = re.compile(r"^(#[a-z0-9-]{1,80}|https://[A-Za-z0-9.-]+(/[^\s\"'<>]*)?)$")
BUTIR = re.compile(r"^(\s*)(- |\d{1,2}\. )(.*)$")


def id_judul(teks):
    return re.sub(r"[^a-z0-9]+", "-", teks.lower()).strip("-")[:80] or "bagian"


def sebaris(teks):
    """One line of text: escaped, then `code`, **bold** and [links](#anchor or https://...)."""
    kode = []

    def simpan_kode(m):
        kode.append("<code>%s</code>" % html.escape(m.group(1), quote=True))
        return "\x00%d\x00" % (len(kode) - 1)
    t = re.sub(r"`([^`]+)`", simpan_kode, teks)       # code first, so nothing inside it becomes bold or a link
    t = html.escape(t, quote=True)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)

    def tautan(m):
        url = html.unescape(m.group(2))
        return '<a href="%s">%s</a>' % (html.escape(url, quote=True), m.group(1)) if URL_SAH.match(url) else m.group(0)
    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", tautan, t)
    return re.sub(r"\x00(\d+)\x00", lambda m: kode[int(m.group(1))], t)


def render(teks):
    """(html, [(id, heading)] of the "##" sections, title of the "#" heading)."""
    baris = teks.replace("\r\n", "\n").split("\n")
    hasil, daftar_isi, judul, dipakai = [], [], "", set()
    i, n = 0, len(baris)

    def daftar(i):
        """A list (and its one level of sub-items) from line i; returns (html, next line)."""
        jenis = "ol" if re.match(r"^\d", baris[i].strip()) else "ul"
        butir, sub = [], None                       # butir: [[text, [sub-items]]]
        while i < n and baris[i].strip():
            m = BUTIR.match(baris[i])
            if m and len(m.group(1)) == 0:
                butir.append([m.group(3), []])
            elif m and butir:
                butir[-1][1].append(m.group(3))
            elif butir and baris[i].startswith("  "):
                if butir[-1][1]:
                    butir[-1][1][-1] += " " + baris[i].strip()
                else:
                    butir[-1][0] += " " + baris[i].strip()
            else:
                break
            i += 1
        isi = "".join("<li>%s%s</li>" % (sebaris(t), "<ul>%s</ul>" % "".join("<li>%s</li>" % sebaris(x) for x in s) if s else "")
                      for t, s in butir)
        return "<%s>%s</%s>" % (jenis, isi, jenis), i

    while i < n:
        b = baris[i]
        if not b.strip():
            i += 1
            continue
        m = re.match(r"^(#{1,3}) (.+)$", b)
        if m:
            level, teks_j = len(m.group(1)), m.group(2).strip()
            if level == 1:
                judul = teks_j
            else:
                id_ = id_judul(teks_j)
                while id_ in dipakai:
                    id_ += "-2"
                dipakai.add(id_)
                if level == 2:
                    daftar_isi.append((id_, teks_j))
                hasil.append('<h%d id="%s">%s</h%d>' % (level, id_, sebaris(teks_j), level))
            i += 1
        elif b.startswith("```"):
            j = i + 1
            while j < n and not baris[j].startswith("```"):
                j += 1
            hasil.append("<pre><code>%s</code></pre>" % html.escape("\n".join(baris[i + 1:j]), quote=True))
            i = j + 1
        elif b.startswith("|"):
            j = i
            while j < n and baris[j].startswith("|"):
                j += 1
            sel = [[c.strip() for c in x.strip().strip("|").split("|")] for x in baris[i:j]]
            kepala, isi = sel[0], [r for r in sel[1:] if not all(re.match(r"^:?-+:?$", c) for c in r)]
            hasil.append('<div class="tabel-gulir"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (
                "".join('<th scope="col">%s</th>' % sebaris(c) for c in kepala),
                "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % sebaris(c) for c in r) for r in isi)))
            i = j
        elif BUTIR.match(b) and not BUTIR.match(b).group(1):
            html_daftar, i = daftar(i)
            hasil.append(html_daftar)
        elif b.startswith("> "):
            j = i
            while j < n and baris[j].startswith("> "):
                j += 1
            hasil.append("<blockquote><p>%s</p></blockquote>" % sebaris(" ".join(x[2:].strip() for x in baris[i:j])))
            i = j
        else:
            j = i
            while j < n and baris[j].strip() and not re.match(r"^(#{1,3} |```|\||> )", baris[j]) and not (
                    BUTIR.match(baris[j]) and not BUTIR.match(baris[j]).group(1)):
                j += 1
            hasil.append("<p>%s</p>" % sebaris(" ".join(x.strip() for x in baris[i:j])))
            i = j
    return Markup("\n".join(hasil)), daftar_isi, judul


def baca():
    with io.open(PANDUAN, encoding="utf-8") as f:
        return f.read()


def pasang(app, alat):

    @app.route("/panduan")
    @akses("masuk")
    def panduan():
        isi, daftar_isi, judul = render(baca())
        return render_template("panduan.html", isi=isi, daftar_isi=daftar_isi, judul=judul or "Panduan")
