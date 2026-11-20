# -*- coding: utf-8 -*-
"""The front section (hero) of a programme's home page, as its admin sets it (langkah 3c, K-P15).

Settings live in prodi/<kode>/situs.json:

    "tagline": "..."                         the sentence under the title (pengantar)
    "beranda": {
      "latar": {"jenis": "pucat" | "utama" | "warna" | "foto", "warna": "#RRGGBB", "foto": <media.simpan_foto_hero>},
      "label": "", "judul": "", "subjudul": "",            empty: the default from the official data
      "kartu": {"akreditasi": {"label": "...", "sembunyi": false, "urutan": 0}, "gelar": {...}, "sks": {...},
                "internasional": {...}},
      "kartu_tambahan": [{"label": "Mahasiswa aktif", "nilai": "812", "keterangan": "Oktober 2026"}]   at most 2
    }
    "en": {                                  the English home page (Fase 5, K-P37); empty: the English defaults
      "label": "", "judul": "", "subjudul": "", "tagline": "",
      "kartu": {"akreditasi": {"label": "..."}, ...},                                  labels of the official cards
      "kartu_tambahan": [{"label": "Active students", "nilai": "", "keterangan": ""}]   the extra cards, in the same
    }                                        order; a card without an English label is not on the English page, an
                                             empty value is the Indonesian one

What the admin may change (decision of 26 October 2026): the label line, the title, the subtitle and the sentence;
the background (pale or full programme colour, any colour that keeps text readable, or a photo); and the fact cards'
labels, order and visibility, plus two cards of its own. The VALUES of the official cards (accreditation, degree,
credits, international accreditation) always come from the programme's data (www's, with the changes made on the
Data prodi page, K-P16), never from these settings, so every figure on the site comes from one place.

Readability: every background is checked before use. A chosen colour gets white or dark text, whichever reaches 4.5:1;
a colour where neither does is refused. A photo gets an overlay of the programme's dark colour strong enough that white
text reaches 4.5:1 even over a white part of the photo.

Until the admin exists (langkah 6), from the command line:

    python3 platform/tampilan_prodi.py lihat --prodi 55201
    python3 platform/tampilan_prodi.py atur --prodi 55201 --berkas beranda.json   ({"tagline": ..., "beranda": {...}})
    .venv/bin/python platform/tampilan_prodi.py foto --prodi 55201 --berkas latar.jpg --fokus tengah
then rebuild: .venv/bin/python platform/bangun/bangun.py --prodi 55201
"""
from __future__ import print_function

import argparse
import io
import json
import os
import re
import sys

PLATFORM = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PLATFORM)
sys.path.insert(0, os.path.join(PLATFORM, "bangun"))
sys.path.insert(0, os.path.join(PLATFORM, "pemantau"))

import lokasi  # noqa: E402
import saringan_spam  # noqa: E402
import warna as warna_mod  # noqa: E402

JENIS_LATAR = ("pucat", "utama", "warna", "foto")
# social media a programme may link to (footer of its site), with the addresses each one accepts
MEDIA_SOSIAL = {
    "instagram": ("Instagram", r"^https://(www\.)?instagram\.com/[A-Za-z0-9_.]{1,60}/?$"),
    "facebook": ("Facebook", r"^https://(www\.|m\.|web\.)?facebook\.com/[^\s\"'<>\\]{1,200}$"),
    "youtube": ("YouTube", r"^https://(www\.)?(youtube\.com/(@|channel/|c/)[A-Za-z0-9_.\-]{1,100}|youtu\.be/[A-Za-z0-9_\-]{1,40})/?$"),
    "tiktok": ("TikTok", r"^https://(www\.)?tiktok\.com/@[A-Za-z0-9_.]{1,60}/?$"),
    "x": ("X (Twitter)", r"^https://(www\.)?(x|twitter)\.com/[A-Za-z0-9_]{1,30}/?$"),
    "linkedin": ("LinkedIn", r"^https://(www\.)?linkedin\.com/(company|school|in)/[A-Za-z0-9_.\-%]{1,100}/?$"),
}
MAKS_MEDIA_SOSIAL = 6
KUNCI_SITUS = ("tagline", "beranda", "palet", "logo", "media_sosial", "menu", "en")
KARTU_RESMI = ("akreditasi", "gelar", "sks", "internasional")
MAKS = {"label": 80, "judul": 100, "subjudul": 120, "tagline": 300, "kartu_label": 30, "kartu_nilai": 24,
        "kartu_keterangan": 40}
MAKS_KARTU_TAMBAHAN = 2
REDUP = "#635459"          # unsrat-abu-600, the subtitle on the pale background
KONTRAS_MIN = 4.5


class GagalTampilan(ValueError):
    pass


def _teks(label, nilai, maks, masalah, wajib=False):
    if nilai is None:
        nilai = ""
    if not isinstance(nilai, str):
        masalah.append("%s harus berupa teks" % label)
        return
    if wajib and not nilai.strip():
        masalah.append("%s wajib diisi" % label)
    if len(nilai.strip()) > maks:
        masalah.append("%s terlalu panjang (maksimal %d karakter)" % (label, maks))
    if re.search(r"[<>\x00-\x1f]", nilai):
        masalah.append("%s memuat karakter terlarang (< > atau karakter kendali)" % label)
    istilah = saringan_spam.cari(nilai)
    if istilah:
        masalah.append("%s memuat istilah terlarang (“%s”)" % (label, istilah))


def teks_untuk_latar(hex_):
    """(text colour, ratio) for a background colour: white or dark, whichever reads better; None if neither
    reaches KONTRAS_MIN."""
    calon = sorted(((warna_mod.kontras(t, hex_), t) for t in (warna_mod.PUTIH, warna_mod.GELAP)), reverse=True)
    rasio, teks = calon[0]
    return (teks, round(rasio, 2)) if rasio >= KONTRAS_MIN else None


def lapisan_foto(gelap):
    """Opacity of an overlay in colour `gelap` that keeps white text at KONTRAS_MIN over the lightest possible photo
    (white). The overlay is drawn over the photo, so over white it makes campur(white, gelap, a)."""
    a = 0.30
    while a < 0.95:
        if warna_mod.kontras(warna_mod.PUTIH, warna_mod.campur(warna_mod.PUTIH, gelap, a)) >= KONTRAS_MIN + 0.05:
            return round(a, 2)
        a += 0.01
    return 0.95


def periksa(beranda, tagline=""):
    """Problems with a programme's home-page settings (empty list when they can be used)."""
    masalah = []
    _teks("Kalimat pengantar", tagline, MAKS["tagline"], masalah)
    if beranda in (None, {}):
        return masalah
    if not isinstance(beranda, dict):
        return masalah + ["pengaturan beranda harus berupa objek"]
    tidak_dikenal = set(beranda) - {"latar", "label", "judul", "subjudul", "kartu", "kartu_tambahan"}
    if tidak_dikenal:
        masalah.append("pengaturan tidak dikenal: %s" % ", ".join(sorted(tidak_dikenal)))
    for k in ("label", "judul", "subjudul"):
        _teks({"label": "Label", "judul": "Judul", "subjudul": "Subjudul"}[k], beranda.get(k), MAKS[k], masalah)
    latar = beranda.get("latar") or {"jenis": "pucat"}
    if not isinstance(latar, dict) or latar.get("jenis") not in JENIS_LATAR:
        masalah.append("jenis latar harus salah satu dari %s" % ", ".join(JENIS_LATAR))
    elif latar["jenis"] == "warna":
        hex_ = latar.get("warna") or ""
        if not warna_mod.HEX.match(hex_):
            masalah.append("kode warna latar tidak sah (contoh: #1A2B3C)")
        elif teks_untuk_latar(hex_) is None:
            masalah.append("warna latar %s membuat teks putih maupun gelap sulit dibaca (kontras %.2f dan %.2f, minimal "
                           "%.1f); pilih warna yang lebih gelap atau lebih terang" % (
                               hex_, warna_mod.kontras(warna_mod.PUTIH, hex_), warna_mod.kontras(warna_mod.GELAP, hex_),
                               KONTRAS_MIN))
    elif latar["jenis"] == "foto":
        import media
        foto = latar.get("foto")
        if not isinstance(foto, dict) or foto.get("jenis") != "hero" or set(foto.get("varian", {})) != set(media.VARIAN_HERO):
            masalah.append("foto latar belum diunggah atau tidak sah")
        elif not all(media.url_sah(v.get("url")) if "url" in v else media.jalur_sah(v.get("jalur"))
                     for v in foto["varian"].values()):
            masalah.append("alamat foto latar tidak sah")
    kartu = beranda.get("kartu") or {}
    if not isinstance(kartu, dict):
        masalah.append("kartu harus berupa objek")
        kartu = {}
    for id_, atur in kartu.items():
        if id_ not in KARTU_RESMI:
            masalah.append("kartu %r tidak dikenal" % id_)
            continue
        if not isinstance(atur, dict) or set(atur) - {"label", "sembunyi", "urutan"}:
            masalah.append("kartu %s: hanya label, sembunyi, dan urutan yang bisa diatur (nilainya dari data resmi)" % id_)
            continue
        _teks("Label kartu %s" % id_, atur.get("label"), MAKS["kartu_label"], masalah)
        if "urutan" in atur and (not isinstance(atur["urutan"], int) or isinstance(atur["urutan"], bool)
                                 or not 0 <= atur["urutan"] <= 9):
            masalah.append("kartu %s: urutan harus angka 0-9" % id_)
        if not isinstance(atur.get("sembunyi", False), bool):
            masalah.append("kartu %s: sembunyi harus ya/tidak" % id_)
    tambahan = beranda.get("kartu_tambahan") or []
    if not isinstance(tambahan, list) or len(tambahan) > MAKS_KARTU_TAMBAHAN:
        masalah.append("kartu tambahan paling banyak %d" % MAKS_KARTU_TAMBAHAN)
        tambahan = []
    for i, k in enumerate(tambahan, 1):
        if not isinstance(k, dict) or set(k) - {"label", "nilai", "keterangan", "urutan"}:
            masalah.append("kartu tambahan ke-%d tidak sah" % i)
            continue
        _teks("Label kartu tambahan ke-%d" % i, k.get("label"), MAKS["kartu_label"], masalah, wajib=True)
        _teks("Nilai kartu tambahan ke-%d" % i, k.get("nilai"), MAKS["kartu_nilai"], masalah, wajib=True)
        _teks("Keterangan kartu tambahan ke-%d" % i, k.get("keterangan"), MAKS["kartu_keterangan"], masalah)
        if "urutan" in k and (not isinstance(k["urutan"], int) or isinstance(k["urutan"], bool) or not 0 <= k["urutan"] <= 9):
            masalah.append("kartu tambahan ke-%d: urutan harus angka 0-9" % i)
    return masalah


def periksa_en(en):
    """Problems with the English texts of a programme's home page (empty list when they can be used)."""
    if en in (None, {}):
        return []
    if not isinstance(en, dict):
        return ["teks bahasa Inggris harus berupa objek"]
    masalah = []
    tidak_dikenal = set(en) - {"label", "judul", "subjudul", "tagline", "kartu", "kartu_tambahan"}
    if tidak_dikenal:
        masalah.append("teks bahasa Inggris tidak dikenal: %s" % ", ".join(sorted(tidak_dikenal)))
    for k, label in (("label", "Label (Inggris)"), ("judul", "Judul (Inggris)"), ("subjudul", "Subjudul (Inggris)"),
                     ("tagline", "Kalimat pengantar (Inggris)")):
        _teks(label, en.get(k), MAKS[k], masalah)
    kartu = en.get("kartu") or {}
    if not isinstance(kartu, dict):
        masalah.append("kartu (Inggris) harus berupa objek")
        kartu = {}
    for id_, atur in kartu.items():
        if id_ not in KARTU_RESMI or not isinstance(atur, dict) or set(atur) - {"label"}:
            masalah.append("kartu (Inggris) %r tidak sah: hanya labelnya yang diterjemahkan" % (id_,))
            continue
        _teks("Label kartu %s (Inggris)" % id_, atur.get("label"), MAKS["kartu_label"], masalah)
    tambahan = en.get("kartu_tambahan") or []
    if not isinstance(tambahan, list) or len(tambahan) > MAKS_KARTU_TAMBAHAN:
        masalah.append("kartu tambahan (Inggris) paling banyak %d" % MAKS_KARTU_TAMBAHAN)
        tambahan = []
    for i, k in enumerate(tambahan, 1):
        if not isinstance(k, dict) or set(k) - {"label", "nilai", "keterangan"}:
            masalah.append("kartu tambahan ke-%d (Inggris) tidak sah" % i)
            continue
        _teks("Label kartu tambahan ke-%d (Inggris)" % i, k.get("label"), MAKS["kartu_label"], masalah)
        _teks("Nilai kartu tambahan ke-%d (Inggris)" % i, k.get("nilai"), MAKS["kartu_nilai"], masalah)
        _teks("Keterangan kartu tambahan ke-%d (Inggris)" % i, k.get("keterangan"), MAKS["kartu_keterangan"], masalah)
    return masalah


def situs_inggris(situs):
    """The settings the English home page is made from (K-P37), in the shape susun() reads: the English texts and card
    labels ("en"), the background and the order and visibility of the cards of the Indonesian settings, and the extra
    cards that have an English label (an empty English value is the Indonesian one)."""
    beranda = situs.get("beranda") if isinstance(situs.get("beranda"), dict) else {}
    en = situs.get("en") if isinstance(situs.get("en"), dict) else {}
    hasil = {}
    if beranda.get("latar"):
        hasil["latar"] = beranda["latar"]
    for k in ("label", "judul", "subjudul"):
        if (en.get(k) or "").strip():
            hasil[k] = en[k].strip()
    label_en = {i: (a.get("label") or "").strip() for i, a in (en.get("kartu") or {}).items() if isinstance(a, dict)}
    kartu = {}
    for id_ in KARTU_RESMI:
        atur = (beranda.get("kartu") or {}).get(id_)
        x = {k: atur[k] for k in ("sembunyi", "urutan") if isinstance(atur, dict) and k in atur}
        if label_en.get(id_):
            x["label"] = label_en[id_]
        if x:
            kartu[id_] = x
    if kartu:
        hasil["kartu"] = kartu
    tambahan, en_t = [], en.get("kartu_tambahan") or []
    for i, k in enumerate(beranda.get("kartu_tambahan") or []):
        e = en_t[i] if i < len(en_t) and isinstance(en_t[i], dict) else {}
        if isinstance(k, dict) and (e.get("label") or "").strip():
            x = {"label": e["label"].strip(), "nilai": (e.get("nilai") or "").strip() or k.get("nilai", ""),
                 "keterangan": (e.get("keterangan") or "").strip()}
            if "urutan" in k:
                x["urutan"] = k["urutan"]
            tambahan.append(x)
    if tambahan:
        hasil["kartu_tambahan"] = tambahan
    return {"beranda": hasil, "tagline": (en.get("tagline") or "").strip()}


def periksa_identitas(situs):
    """Problems with a programme's palette, logo, social media and menu settings (empty list when usable)."""
    import media
    import menu as menu_mod
    masalah = []
    palet = situs.get("palet")
    if palet not in (None, warna_mod.BAWAAN) and palet not in {p["id"] for p in warna_mod.baca_palet()}:
        masalah.append("palet %r tidak dikenal" % (palet,))
    logo = situs.get("logo")
    if logo is not None:
        if not isinstance(logo, dict) or logo.get("jenis") != "logo" or logo.get("format") not in ("svg", "png") \
                or not isinstance(logo.get("varian"), dict) or not logo["varian"]:
            masalah.append("logo tidak sah")
        elif not all(media.url_sah(v.get("url")) if "url" in v else media.jalur_sah(v.get("jalur")) for v in logo["varian"].values()):
            masalah.append("alamat berkas logo tidak sah")
        elif not (isinstance(logo.get("lebar"), int) and isinstance(logo.get("tinggi"), int) and logo["tinggi"] > 0):
            masalah.append("ukuran logo tidak sah")
    medsos = situs.get("media_sosial") or []
    if not isinstance(medsos, list) or len(medsos) > MAKS_MEDIA_SOSIAL:
        masalah.append("media sosial paling banyak %d" % MAKS_MEDIA_SOSIAL)
        medsos = []
    for i, m in enumerate(medsos, 1):
        if not isinstance(m, dict) or m.get("jenis") not in MEDIA_SOSIAL:
            masalah.append("media sosial ke-%d tidak dikenal" % i)
        elif not re.match(MEDIA_SOSIAL[m["jenis"]][1], m.get("url") or ""):
            masalah.append("alamat %s ke-%d tidak sah (harus alamat https di situs %s)" % (
                MEDIA_SOSIAL[m["jenis"]][0], i, MEDIA_SOSIAL[m["jenis"]][0]))
    masalah += menu_mod.periksa_pengaturan(menu_mod.baca_templat(), situs.get("menu") or {})
    return masalah


def bawaan_dan_resmi(p, nama_unit, bahasa="id"):
    """(default texts, official cards) of a programme's front section, from its effective data (data_prodi.py). In
    English (K-P37) from the official English name, with the Indonesian name as the subtitle."""
    import bahasa as bahasa_mod
    import registri
    _ = bahasa_mod.penerjemah(bahasa)
    jenjang = bahasa_mod.jenjang_panjang(p["jenjang"], bahasa)
    bawaan = {"label": _("Program Studi %s · %s") % (jenjang, nama_unit), "judul": bahasa_mod.nama_tampil(p, bahasa),
              "subjudul": (registri.nama_tampil(p) if p.get("nama_en") else "") if bahasa == "en"
              else p.get("nama_en") or "",
              "pengantar": _("Program studi %s di %s, Universitas Sam Ratulangi, Manado.") % (jenjang.lower(), nama_unit)}
    resmi = []
    if registri.label_akreditasi(p.get("akreditasi")):
        resmi.append({"id": "akreditasi", "label": _("Akreditasi"),
                      "nilai": bahasa_mod.label_akreditasi(p["akreditasi"], bahasa),
                      "keterangan": p.get("lembaga_akreditasi") or "", "sorot": True})
    if p.get("gelar"):
        resmi.append({"id": "gelar", "label": _("Gelar"), "nilai": p["gelar"], "keterangan": "", "sorot": False})
    if p.get("sks"):
        resmi.append({"id": "sks", "label": _("Beban studi"), "nilai": _("%s SKS") % p["sks"], "keterangan": "",
                      "sorot": False})
    if p.get("internasional"):
        resmi.append({"id": "internasional", "label": _("Akreditasi internasional"), "nilai": p["internasional"],
                      "keterangan": "", "sorot": False})
    return bawaan, resmi


def susun(bawaan, kartu_resmi, situs, w):
    """What the builder shows. bawaan: {"label", "judul", "subjudul"} from the official data; kartu_resmi:
    [{"id", "label", "nilai", "keterangan", "sorot"}] for the official values that exist; w: warna.warna_prodi().
    Raises GagalTampilan when the settings are not valid (the builder then uses the defaults)."""
    beranda = situs.get("beranda") or {}
    tagline = (situs.get("tagline") or "").strip()
    masalah = periksa(beranda, tagline)
    if masalah:
        raise GagalTampilan("; ".join(masalah))
    hasil = {k: (beranda.get(k) or "").strip() or bawaan[k] for k in ("label", "judul", "subjudul")}
    hasil["subjudul_bawaan"] = not (beranda.get("subjudul") or "").strip()
    hasil["pengantar"] = tagline or bawaan["pengantar"]
    atur = beranda.get("kartu") or {}
    kartu = []
    for i, k in enumerate(kartu_resmi):
        a = atur.get(k["id"], {})
        if not a.get("sembunyi"):
            kartu.append((a.get("urutan", i), "urutan" not in a, i, dict(k, label=(a.get("label") or "").strip() or k["label"])))
    for j, k in enumerate(beranda.get("kartu_tambahan") or []):
        kartu.append((k.get("urutan", len(kartu_resmi) + j), "urutan" not in k, len(kartu_resmi) + j,
                      {"id": "tambahan-%d" % (j + 1), "label": k["label"].strip(), "nilai": k["nilai"].strip(),
                       "keterangan": (k.get("keterangan") or "").strip(), "sorot": False}))
    # an order the admin chose wins over a default position with the same number
    hasil["kartu"] = [x[3] for x in sorted(kartu, key=lambda x: x[:3])]
    latar = dict(beranda.get("latar") or {"jenis": "pucat"})
    if latar["jenis"] == "warna":
        latar["teks"] = teks_untuk_latar(latar["warna"])[0]
    elif latar["jenis"] == "foto":
        latar["lapisan"] = lapisan_foto(w["utama_gelap"])
    hasil["latar"] = latar
    return hasil


def css(latar, w, url_foto):
    """Lines for <slug>/warna.css that colour the hero. url_foto(rekam) gives an address relative to that file."""
    jenis = latar["jenis"]
    if jenis == "pucat":
        return ""
    if jenis == "utama":
        latar_, teks = w["utama"], warna_mod.PUTIH
    elif jenis == "warna":
        latar_, teks = latar["warna"].upper(), latar["teks"]
    else:
        latar_, teks = w["utama_gelap"], warna_mod.PUTIH
    baris = [":root {", "\t--hero-latar: %s;" % latar_, "\t--hero-teks: %s;" % teks, "\t--hero-label: %s;" % teks,
             "\t--hero-redup: %s;" % teks, "}"]
    if jenis == "foto":
        r, g, b = (int(w["utama_gelap"][i:i + 2], 16) for i in (1, 3, 5))
        lapis = "linear-gradient(rgb(%d %d %d / %s), rgb(%d %d %d / %s))" % (r, g, b, latar["lapisan"], r, g, b, latar["lapisan"])
        v = latar["foto"]["varian"]
        for media_q, kunci in ((None, "ponsel"), ("(min-width: 760px)", "1600"),
                               ("(min-width: 1600px), (min-width: 760px) and (min-resolution: 2dppx)", "2400")):
            aturan = '.pahlawan--foto {\n\tbackground-image: %s, url("%s");\n}' % (lapis, url_foto(v[kunci]))
            if media_q:
                aturan = "@media %s {\n\t%s\n}" % (media_q, aturan.replace("\n", "\n\t"))
            baris.append(aturan)
    return "\n".join(baris) + "\n"


# ------------------------------------------------------------------ command line

def _simpan(kode, situs, oleh, aksi):
    lokasi.tulis("prodi/%s/situs" % kode, situs, oleh, "Beranda", aksi)


def atur(kode, perubahan, oleh, aksi=None):
    """Replace settings of a programme (keys of KUNCI_SITUS) after checking them all."""
    if set(perubahan) - set(KUNCI_SITUS):
        raise GagalTampilan("pengaturan tidak dikenal: %s" % ", ".join(sorted(set(perubahan) - set(KUNCI_SITUS))))
    situs = lokasi.baca("prodi/%s/situs" % kode) or {}
    baru = dict(situs, **perubahan)
    masalah = periksa(baru.get("beranda"), baru.get("tagline") or "") + periksa_identitas(baru) + periksa_en(baru.get("en"))
    if masalah:
        raise GagalTampilan("; ".join(masalah))
    _simpan(kode, baru, oleh, aksi or "atur %s" % ", ".join(sorted(perubahan)))


def ganti_foto(kode, data, fokus, oleh):
    """Check, crop and store a background photo and make it the hero background."""
    import media
    foto = media.simpan_foto_hero(kode, data, fokus)
    situs = lokasi.baca("prodi/%s/situs" % kode) or {}
    beranda = dict(situs.get("beranda") or {})
    beranda["latar"] = {"jenis": "foto", "foto": foto}
    atur(kode, {"beranda": beranda}, oleh)
    return foto


def main(argv=None):
    import media
    ap = argparse.ArgumentParser(description="Bagian depan beranda prodi (sementara, sebelum admin tersedia)")
    sub = ap.add_subparsers(dest="perintah", required=True)
    l = sub.add_parser("lihat")
    l.add_argument("--prodi", required=True)
    a = sub.add_parser("atur", help='berkas JSON berisi {"tagline": ..., "beranda": {...}}')
    a.add_argument("--prodi", required=True)
    a.add_argument("--berkas", required=True)
    a.add_argument("--oleh", default="baris-perintah")
    f = sub.add_parser("foto", help=media.PETUNJUK_HERO)
    f.add_argument("--prodi", required=True)
    f.add_argument("--berkas", required=True)
    f.add_argument("--fokus", default="tengah", choices=media.FOKUS)
    f.add_argument("--oleh", default="baris-perintah")
    x = ap.parse_args(argv)
    if not lokasi.NAMA_SAH.match("prodi/%s/situs" % x.prodi):
        print("kode prodi tidak sah")
        return 1
    try:
        if x.perintah == "lihat":
            situs = lokasi.baca("prodi/%s/situs" % x.prodi) or {}
            print(json.dumps({"tagline": situs.get("tagline", ""), "beranda": situs.get("beranda", {})},
                             ensure_ascii=False, indent=2))
        elif x.perintah == "atur":
            with io.open(x.berkas, encoding="utf-8") as fb:
                atur(x.prodi, json.load(fb), x.oleh)
            print("Pengaturan beranda disimpan.")
        else:
            with open(x.berkas, "rb") as fb:
                ganti_foto(x.prodi, fb.read(), x.fokus, x.oleh)
            print("Foto latar disimpan.")
    except (GagalTampilan, ValueError, IOError) as e:
        print("GAGAL: %s" % e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
