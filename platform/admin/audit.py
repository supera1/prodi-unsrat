# -*- coding: utf-8 -*-
"""Audit log of the admin: one JSON line per action in <PRODI_LOG>/audit.jsonl.

Every line has "waktu", "aksi", "oleh" (user name or "-"), "ip", and "prodi" when the action concerns programmes
(a code, or a list of codes for an account of several programmes), plus details. Passwords, temporary ones
included, are never written here.
"""
from __future__ import print_function

import datetime
import io
import json
import os
import sys
import threading

PLATFORM = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PLATFORM)

import lokasi  # noqa: E402

_kunci = threading.Lock()
DILARANG = ("sandi", "password", "hash", "csrf")


def path():
    return os.path.join(lokasi.log(), "audit.jsonl")


def catat(aksi, oleh="-", ip="-", prodi=None, **data):
    for k in list(data):
        if any(x in k.lower() for x in DILARANG):
            del data[k]
    data.update({"waktu": datetime.datetime.now().isoformat(timespec="seconds"), "aksi": aksi, "oleh": oleh, "ip": ip})
    if prodi:
        data["prodi"] = prodi if isinstance(prodi, str) else (sorted(prodi)[0] if len(prodi) == 1 else sorted(prodi))
    os.makedirs(lokasi.log(), exist_ok=True)
    with _kunci, io.open(path(), "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False, sort_keys=True) + "\n")


def baca(prodi=None, batas=200):
    """Newest first; prodi: only that programme's lines."""
    if not os.path.isfile(path()):
        return []
    with io.open(path(), encoding="utf-8") as f:
        baris = [json.loads(x) for x in f if x.strip()]
    if prodi:
        baris = [b for b in baris if b.get("prodi") == prodi or (isinstance(b.get("prodi"), list) and prodi in b["prodi"])]
    return list(reversed(baris))[:batas]
