# -*- coding: utf-8 -*-
"""Open uploaded pictures safely.

Pillow tries every image decoder it has on a file it is given, whatever the file name says. Some decoders
have had memory-corruption flaws; the libwebp in the Pillow installed here (9.5.0, libwebp 1.3.0) has
CVE-2023-4863, a heap overflow that is exploited in the wild. Uploads are therefore opened with the JPEG
and PNG decoders only: a WebP, TIFF or any other file is refused before it is decoded. When the runtime is
upgraded (Python 3.12+ with a current Pillow), WebP can be allowed again here.
"""
from __future__ import print_function

import io

from PIL import Image, ImageOps

FORMAT = ("JPEG", "PNG")
TERIMA = "image/jpeg,image/png"   # accept= of the file inputs
TEKS_FORMAT = "JPG atau PNG"
MAKS_PIKSEL = 60 * 1000 * 1000


def buka(data, pesan_format="Gambar harus %s." % TEKS_FORMAT, maks_piksel=MAKS_PIKSEL):
    """A checked picture (PIL image, EXIF rotation applied) from uploaded bytes, or ValueError with a
    message for the admin."""
    try:
        with Image.open(io.BytesIO(data), formats=FORMAT) as uji:
            if uji.width * uji.height > maks_piksel:
                raise ValueError("Resolusi gambar terlalu besar.")
            uji.verify()
        im = Image.open(io.BytesIO(data), formats=FORMAT)
        im.load()
        return ImageOps.exif_transpose(im)
    except ValueError:
        raise
    except Image.UnidentifiedImageError:
        raise ValueError(pesan_format)
    except Exception:
        raise ValueError("Gambar rusak atau formatnya tidak dikenali.")


def buka_berkas(path, format_=("JPEG",)):
    """A picture the admin itself wrote earlier (e.g. a re-encoded JPEG), opened with that decoder only."""
    return Image.open(path, formats=format_)
