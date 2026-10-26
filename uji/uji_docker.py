# -*- coding: utf-8 -*-
"""Step 7 of phase 1: the Docker stack (Dockerfile, docker/, docker-compose.yml), checked without Docker.

- the CSP header of Nginx is the CSP of the pages (bangun.py) plus frame-ancestors;
- the filter of the web container (50-prodi-pantau.sh) passes exactly the redirect lines the builder writes and no
  other directive (checked with Python's re, and with grep -E when the machine has it);
- the stack: the admin is never published, secrets are mounted in the admin container only, the web and pemantau
  containers mount everything read only, the image never gets a developer's data or secrets (.dockerignore);
- every variable of the stack is in .env.example and in docs/deploy.md; the shell scripts parse (sh -n).

The stack itself is tried with Docker as described in docs/deploy.md (§ Mencoba di komputer sendiri).
"""
from __future__ import print_function

import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

AKAR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for sub in ("platform", "platform/bangun"):
    sys.path.insert(0, os.path.join(AKAR, *sub.split("/")))

try:
    import jinja2  # noqa: F401
except ImportError:
    print("uji_docker: paket admin belum terpasang; jalankan dengan .venv/bin/python (lihat README)")
    sys.exit(1)

import bangun  # noqa: E402

if not os.path.isfile(os.path.join(AKAR, "docker-compose.yml")):
    # inside the admin image (Dockerfile): the files of the stack are what the image was built from, not in it
    print("uji_docker: berkas stack tidak ada di sini (di dalam image), dilewati")
    sys.exit(0)

gagal = []


def cek(kondisi, pesan):
    if not kondisi:
        gagal.append(pesan)


def baca(rel):
    with io.open(os.path.join(AKAR, *rel.split("/")), encoding="utf-8") as f:
        return f.read()


# --- the CSP header is the pages' CSP
header = baca("docker/nginx/header-keamanan.conf")
m = re.search(r'add_header Content-Security-Policy "([^"]+)" always;', header)
cek(m and m.group(1) == bangun.CSP + "; frame-ancestors 'self'", "CSP Nginx harus sama dengan CSP bangun.py + frame-ancestors")
for h in ("Strict-Transport-Security", "X-Content-Type-Options", "X-Frame-Options", "Referrer-Policy", "Permissions-Policy"):
    cek(h in header, "header %s harus ada" % h)
situs = baca("docker/nginx/lokasi-situs.conf")
for blok in re.findall(r"location [^{]+\{(?:[^{}]|\{[^{}]*\})*\}", situs):
    if "deny all; }" in blok and "limit_except" not in blok:
        continue                                        # location ~ /\. { deny all; }
    cek("header-keamanan.conf" in blok, "setiap location situs harus memuat header keamanan: %s" % blok.split("{")[0])

# --- the redirect filter: exactly the builder's lines
skrip = baca("docker/nginx/50-prodi-pantau.sh")
pola = re.search(r"^POLA='([^']+)'$", skrip, re.M).group(1)
saring = re.compile(pola)
registri = [{"kode_pddikti": "55201", "slug": "s1informatika", "slug_lama": ["s1ti", "s1teknikinformatika"]},
            {"kode_pddikti": "20201", "slug": "s1elektro", "slug_lama": []},
            {"kode_pddikti": "11901", "slug": "profesidokter", "slug_lama": ["profdokter"]}]
buatan = bangun.Pembangun.konfigurasi_redirect(None, registri).splitlines()
rewrite = [b for b in buatan if b.startswith("rewrite")]
cek(len(rewrite) == 3, "tiga pengalihan dari registri: %r" % buatan)
cek(all(saring.match(b) for b in rewrite), "semua baris buatan generator harus lolos saringan: %r" % rewrite)
jahat = [
    "location /x { alias /etc/nginx/tls/; }",
    "include /etc/nginx/tls/privkey.pem;",
    "rewrite ^/s1ti(/.*)?$ https://contoh-judi.example/$1 permanent;",
    "rewrite ^/s1ti(/.*)?$ /s1informatika$1 permanent; location /k { alias /etc/; }",
    "rewrite ^/s1ti(/.*)?$ /s1informatika$1 permanent;\nreturn 302 https://contoh.example;",
    "rewrite ^/S1TI(/.*)?$ /s1informatika$1 permanent;",
    "rewrite ^/s1ti(/.*)?$ /../etc$1 permanent;",
    "rewrite ^/s1ti(/.*)?$ /s1informatika$1 redirect;",
    " rewrite ^/s1ti(/.*)?$ /s1informatika$1 permanent;",
    "proxy_pass http://contoh.example;",
    "set $admin http://contoh.example;",
]
for baris in jahat:
    cek(not all(saring.match(b) for b in baris.split("\n")), "saringan harus menolak: %r" % baris)
grep = shutil.which("grep")
if grep:
    kerja = tempfile.mkdtemp(prefix="prodi-uji-docker-")
    try:
        path = os.path.join(kerja, "slug-lama.conf")
        semua = "\n".join(buatan + jahat).split("\n")
        with io.open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(semua) + "\n")
        hasil = subprocess.run([grep, "-E", pola, path], capture_output=True, text=True).stdout.splitlines()
        cek(hasil == [b for b in semua if saring.match(b)] and hasil[:3] == rewrite
            and all(b.startswith("rewrite ^/") and b.endswith(" permanent;") and "{" not in b for b in hasil),
            "grep -E harus sama dengan saringan Python: %r" % hasil)
    finally:
        shutil.rmtree(kerja, ignore_errors=True)

# --- the stack
compose = baca("docker-compose.yml")


def layanan(nama):
    m = re.search(r"^  %s:\n((?:    .*\n|\n)+)" % nama, compose, re.M)
    return m.group(1) if m else ""


admin, web, pemantau = layanan("admin"), layanan("web"), layanan("pemantau")
cek(admin and web and pemantau, "tiga layanan: admin, web, pemantau")
cek("ports:" not in admin and "ports:" not in pemantau, "admin dan pemantau tidak pernah dibuka ke luar")
cek("prodi-rahasia" in admin and "prodi-rahasia" not in web + pemantau, "volume rahasia hanya di kontainer admin")
for nama, isi in (("web", web), ("pemantau", pemantau)):
    volume = re.findall(r"^      - (\S+)$", isi.split("volumes:")[1], re.M) if "volumes:" in isi else []
    cek(volume and all(v.endswith(":ro") for v in volume), "semua volume %s harus hanya-baca: %r" % (nama, volume))
cek('PROXY_TERPERCAYA: "1"' in admin, "admin hanya di belakang satu proksi (Nginx)")
cek("8791" in baca("docker/nginx/lokasi-admin.conf") and "PORT=8791" in baca("Dockerfile"), "port admin sama di semua tempat")
ignore = baca(".dockerignore").split()
for x in (".git", ".venv", "data/", "rahasia/", "log/", "unggahan/", "publik/", ".env", ".kredensial*", "*.sqlite"):
    cek(x in ignore, ".dockerignore harus memuat %s" % x)
variabel = sorted(set(re.findall(r"\$\{([A-Z_]+)", compose)))
contoh = baca(".env.example")
panduan = baca("docs/deploy.md") if os.path.isfile(os.path.join(AKAR, "docs", "deploy.md")) else ""
for v in variabel:
    cek(re.search(r"^%s=$" % v, contoh, re.M), "%s harus ada (tanpa nilai) di .env.example" % v)
    cek("`%s`" % v in panduan, "%s harus dijelaskan di docs/deploy.md" % v)
cek(not re.search(r"^[A-Z_]+=\S", contoh, re.M), ".env.example tanpa nilai")

# --- the shell scripts parse
sh = shutil.which("sh")
for rel in ("docker/admin-mulai.sh", "docker/pemantau.sh", "docker/nginx/40-prodi-jaringan.sh",
            "docker/nginx/45-prodi-https.sh", "docker/nginx/50-prodi-pantau.sh"):
    path = os.path.join(AKAR, *rel.split("/"))
    cek(os.access(path, os.X_OK), "%s harus dapat dijalankan (chmod +x)" % rel)
    if sh:
        r = subprocess.run([sh, "-n", path], capture_output=True, text=True)
        cek(r.returncode == 0, "%s: %s" % (rel, r.stderr.strip()))

for g in gagal:
    print("GAGAL", g)
print("uji_docker: %d variabel stack, %s" % (len(variabel), "LULUS" if not gagal else "%d gagal" % len(gagal)))
sys.exit(1 if gagal else 0)
