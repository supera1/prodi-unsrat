# -*- coding: utf-8 -*-
"""Clean an uploaded SVG so that it can never run code on the website.

An SVG is a document, not just a picture: opened on its own it can run scripts with the site's
rights. Only drawing elements and attributes from an allow-list are kept. Scripts, event
handlers (on...), links, foreignObject, animation, external references (http:, file:, other
files), and editor metadata (Inkscape, Illustrator) are dropped. A file with entities or an
internal DTD subset is refused outright (defusedxml), which also stops XXE and "billion laughs".
"""
from __future__ import print_function

import re
from xml.etree import ElementTree as ET

from defusedxml import ElementTree as DET

SVG = "http://www.w3.org/2000/svg"
XLINK = "http://www.w3.org/1999/xlink"
XMLNS = "http://www.w3.org/XML/1998/namespace"
MAKS_SVG = 5 * 1024 * 1024

ELEMEN = {
    "svg", "g", "defs", "symbol", "use", "title", "desc", "path", "rect", "circle", "ellipse", "line", "polyline",
    "polygon", "text", "tspan", "textPath", "linearGradient", "radialGradient", "stop", "clipPath", "mask", "pattern",
    "marker", "filter", "feGaussianBlur", "feOffset", "feBlend", "feColorMatrix", "feComposite", "feFlood", "feMerge",
    "feMergeNode", "feMorphology", "feDropShadow", "feComponentTransfer", "feFuncA", "feFuncR", "feFuncG", "feFuncB",
    "style", "image",
}
ATRIBUT = {
    "id", "class", "style", "d", "x", "y", "x1", "y1", "x2", "y2", "cx", "cy", "r", "rx", "ry", "fx", "fy", "fr",
    "width", "height", "viewBox", "preserveAspectRatio", "points", "transform", "gradientTransform", "gradientUnits",
    "patternUnits", "patternContentUnits", "patternTransform", "clipPathUnits", "maskUnits", "maskContentUnits",
    "spreadMethod", "offset", "stop-color", "stop-opacity", "fill", "fill-opacity", "fill-rule", "clip-rule", "stroke",
    "stroke-width", "stroke-opacity", "stroke-linecap", "stroke-linejoin", "stroke-miterlimit", "stroke-dasharray",
    "stroke-dashoffset", "opacity", "clip-path", "mask", "filter", "color", "display", "visibility", "font-family",
    "font-size", "font-weight", "font-style", "font-variant", "font-stretch", "text-anchor", "dominant-baseline",
    "alignment-baseline", "baseline-shift", "letter-spacing", "word-spacing", "text-decoration", "writing-mode", "dx",
    "dy", "rotate", "textLength", "lengthAdjust", "version", "baseProfile", "markerWidth", "markerHeight", "refX", "refY",
    "orient", "markerUnits", "marker-start", "marker-mid", "marker-end", "in", "in2", "result", "stdDeviation", "mode",
    "type", "values", "operator", "k1", "k2", "k3", "k4", "flood-color", "flood-opacity", "radius", "slope", "intercept",
    "amplitude", "exponent", "tableValues", "overflow", "enable-background", "mix-blend-mode", "isolation", "paint-order",
    "vector-effect", "shape-rendering", "image-rendering", "text-rendering", "color-interpolation",
    "color-interpolation-filters", "startOffset", "method", "spacing", "side", "primitiveUnits", "filterUnits",
    "x-height", "href", "data-name", "role", "aria-label", "aria-labelledby", "aria-describedby", "aria-hidden",
    "focusable", "lang",
}
BOLEH_HREF = {"use", "textPath", "linearGradient", "radialGradient", "pattern", "image", "filter"}
GAMBAR_DATA = re.compile(r"^data:image/(png|jpeg|gif|webp);base64,[A-Za-z0-9+/=\s]+$")
BERBAHAYA = re.compile(r"javascript:|vbscript:|data:|expression\s*\(|@import|behavior\s*:|-moz-binding|</", re.I)
URL = re.compile(r"url\(\s*(['\"]?)([^)'\"]*)\1\s*\)", re.I)


def _nama(tag):
    """(namespace, local name) of an ElementTree tag or attribute name."""
    if tag.startswith("{"):
        ns, _, nama = tag[1:].partition("}")
        return ns, nama
    return "", tag


def _css_aman(teks):
    # a backslash starts a CSS escape (@\69mport is @import) and @ starts an at-rule; drawing styles need neither
    if BERBAHAYA.search(teks) or "\\" in teks or "@" in teks:
        return False
    return all(m.group(2).strip().startswith("#") for m in URL.finditer(teks))


def _bersihkan(el, dibuang):
    for anak in list(el):
        ns, nama = _nama(anak.tag) if isinstance(anak.tag, str) else ("", "")
        if ns != SVG or nama not in ELEMEN:
            el.remove(anak)
            dibuang.add(nama or "komentar")
            continue
        if nama == "style" and not _css_aman(anak.text or ""):
            el.remove(anak)
            dibuang.add("style berbahaya")
            continue
        _bersihkan(anak, dibuang)
        if nama == "image" and not any(_nama(k)[1] == "href" for k in anak.attrib):
            el.remove(anak)   # an image without a safe (embedded) source
            dibuang.add("image luar")
    _, nama_el = _nama(el.tag)
    for kunci in list(el.attrib):
        ns, nama = _nama(kunci)
        nilai = el.attrib[kunci]
        ok = False
        if ns == XMLNS and nama == "space":
            ok = True
        elif ns in ("", XLINK) and nama == "href":
            ok = nama_el in BOLEH_HREF and (nilai.startswith("#") or (nama_el == "image" and GAMBAR_DATA.match(nilai)))
        elif ns == "" and nama in ATRIBUT:
            ok = _css_aman(nilai) if nama == "style" or "url(" in nilai.lower() else not BERBAHAYA.search(nilai)
        if not ok:
            del el.attrib[kunci]
            dibuang.add("@" + nama)


def _angka(teks):
    m = re.match(r"^\s*([0-9]*\.?[0-9]+)\s*(px)?\s*$", teks or "")
    return float(m.group(1)) if m else None


def bersihkan(data):
    """Clean SVG bytes. Returns (clean bytes, width, height, list of what was removed);
    ValueError for a file that is not a usable SVG."""
    if len(data) > MAKS_SVG:
        raise ValueError("Berkas SVG terlalu besar (maksimal 5 MB).")
    teks = data.decode("utf-8-sig", errors="strict") if isinstance(data, bytes) else data
    # a plain public DOCTYPE (Illustrator) is harmless; one with an internal subset can define entities
    if re.search(r"<!DOCTYPE[^>]*\[", teks, re.I):
        raise ValueError("SVG berisi definisi DOCTYPE/entitas. Ekspor ulang sebagai SVG biasa.")
    teks = re.sub(r"<!DOCTYPE[^>]*>", "", teks, flags=re.I)
    try:
        akar = DET.fromstring(teks.encode("utf-8"), forbid_dtd=True, forbid_entities=True, forbid_external=True)
    except Exception:
        raise ValueError("Berkas bukan SVG yang sah atau berisi bagian yang tidak diizinkan.")
    if akar.tag != "{%s}svg" % SVG:
        raise ValueError("Berkas bukan gambar SVG (elemen utamanya bukan <svg>).")
    dibuang = set()
    _bersihkan(akar, dibuang)
    if not any(_nama(e.tag)[1] in ("path", "rect", "circle", "ellipse", "line", "polyline", "polygon", "text", "image", "use")
               for e in akar.iter() if isinstance(e.tag, str)):
        raise ValueError("SVG tidak berisi gambar apa pun setelah dibersihkan.")
    lebar, tinggi = _angka(akar.get("width")), _angka(akar.get("height"))
    vb = (akar.get("viewBox") or "").replace(",", " ").split()
    if (not lebar or not tinggi) and len(vb) == 4:
        try:
            lebar, tinggi = float(vb[2]), float(vb[3])
        except ValueError:
            pass
    if not lebar or not tinggi:
        raise ValueError("Ukuran SVG tidak diketahui; beri atribut viewBox atau width/height.")
    ET.register_namespace("", SVG)
    ET.register_namespace("xlink", XLINK)
    hasil = ET.tostring(akar, encoding="unicode")
    return hasil.encode("utf-8"), int(round(lebar)), int(round(tinggi)), sorted(dibuang)
