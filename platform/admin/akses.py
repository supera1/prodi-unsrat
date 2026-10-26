# -*- coding: utf-8 -*-
"""Access declarations of the admin's routes, checked in one place by app.py (periksa_akses) before any view runs:

    akses("umum")               no login (the login page)
    akses("masuk")              any logged-in account
    akses("super")              superadmin only
    akses("prodi")              /prodi/<kode>/...: the superadmin, or an account of that programme
    akses("prodi", "admin")     the same, but not an operator

A route without a declaration is refused (fail closed), and the admin refuses to start with one.
"""

JENIS = ("umum", "masuk", "super", "prodi")
MINIMAL = ("operator", "admin")


def akses(jenis, minimal="operator"):
    """Declare who may open a route."""
    assert jenis in JENIS and minimal in MINIMAL

    def hias(fungsi):
        fungsi.akses = (jenis, minimal)
        return fungsi
    return hias
