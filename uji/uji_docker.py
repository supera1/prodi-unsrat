# -*- coding: utf-8 -*-
"""Step 7 of phase 1: the Docker stack (Dockerfile, docker/, docker-compose.yml), checked without Docker.

- the CSP header of Nginx is the CSP of the pages (bangun.py) plus frame-ancestors;
- the filter of the web container (50-prodi-pantau.sh) passes exactly the redirect lines the builder writes and no
  other directive (checked with Python's re, and with grep -E when the machine has it);
- the stack: the admin is never published, secrets are mounted in the admin container only, the web and pemantau
  containers mount everything read only, no container can gain rights (no-new-privileges) and those running as user
  10001 have no Linux capability, the image never gets a developer's data or secrets (.dockerignore);
- the start of the web container refuses networks that are not networks or are too wide (40-prodi-jaringan.sh), and
  the start of the admin stops on a setting the admin refuses (production without HTTPS) before any site is built;
- every variable of the stack is in .env.example and in docs/deploy.md; the shell scripts parse (sh -n).

The stack itself is tried with Docker as described in docs/deploy.md (§ Mencoba di komputer sendiri).
"""
from __future__ import print_function

import fnmatch
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
for nama, isi in (("admin", admin), ("web", web), ("pemantau", pemantau)):
    cek(re.search(r"^    security_opt:\n      - no-new-privileges:true\s", isi, re.M),
        "%s: tidak ada proses yang bisa menambah haknya sendiri (no-new-privileges)" % nama)
for nama, isi in (("admin", admin), ("pemantau", pemantau)):
    cek(re.search(r"^    cap_drop:\n      - ALL\s", isi, re.M), "%s: tanpa kapabilitas Linux (berjalan sebagai 10001)" % nama)
# Nginx starts as root: of all capabilities it keeps only those it needs then (tried with Docker, docs/log), so e.g. no
# NET_RAW, no DAC_OVERRIDE
tambah = re.search(r"^    cap_add:[^\n]*\n((?:      - [A-Z_]+[^\n]*\n)+)", web, re.M)
cek(re.search(r"^    cap_drop:\n      - ALL\s", web, re.M) and tambah
    and sorted(re.findall(r"^      - ([A-Z_]+)", tambah.group(1), re.M)) == ["CHOWN", "NET_BIND_SERVICE", "SETGID", "SETUID"],
    "web: semua kapabilitas Linux dibuang kecuali CHOWN, SETUID, SETGID, NET_BIND_SERVICE")
cek(re.search(r"^USER prodi$", baca("Dockerfile"), re.M), "image admin berjalan sebagai pengguna prodi, bukan root")
nama_stack = re.search(r"^name: (\S+)$", compose, re.M)
cek(nama_stack and nama_stack.group(1) == "prodi-unsrat", "nama stack ditetapkan di docker-compose.yml: prodi-unsrat")
for rel in ("docker/cadangan-prodi.sh", "docker/pulihkan-prodi.sh"):
    cek('STACK="${STACK:-prodi-unsrat}"' in baca(rel), "%s memakai nama stack docker-compose.yml" % rel)
cek("8791" in baca("docker/nginx/lokasi-admin.conf") and "PORT=8791" in baca("Dockerfile"), "port admin sama di semua tempat")
ignore = baca(".dockerignore").split()
for x in (".git", ".venv", "data/", "rahasia/", "log/", "unggahan/", "publik/", ".env", ".kredensial*", "*.sqlite"):
    cek(x in ignore, ".dockerignore harus memuat %s" % x)


def diabaikan(rel):
    """Whether .dockerignore leaves a path of the repository out of the build context (the last matching pattern
    wins, "!" takes a path back in; a pattern also matches the folders above the path)."""
    hasil = False
    for pola in [p for p in ignore if not p.startswith("#")]:
        balik = pola.startswith("!")
        pola = pola.lstrip("!").rstrip("/")
        bagian = rel.split("/")
        jalur = ["/".join(bagian[:i]) for i in range(1, len(bagian) + 1)]
        if pola.startswith("**/"):
            jalur += ["/".join(bagian[i:j]) for i in range(len(bagian)) for j in range(i + 1, len(bagian) + 1)]
            pola = pola[3:]
        if any(fnmatch.fnmatchcase(j, pola) for j in jalur):
            hasil = not balik
    return hasil


# every file an image copies is in the build context: a COPY of a left-out file stops the build (and the deploy)
cek(diabaikan("data/prodi/x.json") and diabaikan("platform/x/__pycache__/a.pyc") and not diabaikan("docs/asal-modul.md")
    and diabaikan("docs/deploy.md"), "pembaca .dockerignore di uji ini")
for berkas in ("Dockerfile", "docker/web.Dockerfile"):
    for m in re.finditer(r"^COPY\s+(.+)$", baca(berkas).replace("\\\n", " "), re.M):
        for sumber in [x for x in m.group(1).split()[:-1] if not x.startswith("--")]:
            sumber = sumber.rstrip("/")
            cek(os.path.exists(os.path.join(AKAR, *sumber.split("/"))), "%s: COPY %s tidak ada" % (berkas, sumber))
            cek(not diabaikan(sumber), "%s: COPY %s dikecualikan .dockerignore, build akan gagal" % (berkas, sumber))
variabel = sorted(set(re.findall(r"\$\{([A-Z_]+)", compose)))
contoh = baca(".env.example")
panduan = baca("docs/deploy.md") if os.path.isfile(os.path.join(AKAR, "docs", "deploy.md")) else ""
for v in variabel:
    cek(re.search(r"^%s=$" % v, contoh, re.M), "%s harus ada (tanpa nilai) di .env.example" % v)
    cek("`%s`" % v in panduan, "%s harus dijelaskan di docs/deploy.md" % v)
cek(not re.search(r"^[A-Z_]+=\S", contoh, re.M), ".env.example tanpa nilai")
# deployed with docker compose on UNSRAT's VM, without Portainer (K-P17): the guide offers no other way
cek("portainer" not in (panduan + compose + contoh).lower().replace("tanpa portainer", "").replace("no portainer", ""),
    "panduan dan berkas stack tidak menawarkan Portainer (K-P17)")

# --- the start scripts of the web container, run with their paths moved to a temporary folder, in every POSIX shell
# this machine has (the image runs busybox sh): a wrong value must stop the start (exit 1, nothing written)
def jalankan(rel, env, kerja, shell):
    with io.open(os.path.join(AKAR, *rel.split("/")), encoding="utf-8") as f:
        skrip = f.read().replace("/etc/nginx", kerja)
    path = os.path.join(kerja, "skrip.sh")
    with io.open(path, "w", encoding="utf-8") as f:
        f.write(skrip)
    lingkungan = {"PATH": os.environ.get("PATH", "/usr/bin:/bin")}
    lingkungan.update(env)
    r = subprocess.run(shell + [path], env=lingkungan, capture_output=True, text=True)

    def isi(nama):
        p = os.path.join(kerja, *nama.split("/"))
        return io.open(p, encoding="utf-8").read() if os.path.isfile(p) else None
    return r.returncode, isi, r.stderr


TAB = "\t"
# wider than 40-prodi-jaringan.sh allows: ADMIN_IP_BOLEH at most /8 (IPv4) and /32 (IPv6), PROKSI_DEPAN /16 and /48
TERLALU_LUAS = {"ADMIN_IP_BOLEH": ("0.0.0.0/0", "103.84.116.0/24,0.0.0.0/1", "10.0.0.0/7", "::/0", "2000::/3"),
                "PROKSI_DEPAN": ("0.0.0.0/0", "10.0.0.0/8", "130.211.0.0/15", "2600:2d00::/32")}
JARINGAN = [  # (env, exit status, expected admin-ip.conf, expected real-ip.conf, expected admin-awalan.conf)
    ({}, 0, "allow 103.84.116.0/24;\ndeny all;\n", "", 'proxy_set_header X-Forwarded-Prefix "";\n'),
    ({"ADMIN_IP_BOLEH": "103.84.116.0/24, 10.0.0.0/8"}, 0, "allow 103.84.116.0/24;\nallow 10.0.0.0/8;\ndeny all;\n", "", None),
    ({"ADMIN_IP_BOLEH": "103.84.116.0/24" + TAB + "10.0.0.0/8"}, 0, "allow 103.84.116.0/24;\nallow 10.0.0.0/8;\ndeny all;\n", "", None),
    ({"ADMIN_IP_BOLEH": "2001:db8::/32,,103.84.116.0/24"}, 0, "allow 2001:db8::/32;\nallow 103.84.116.0/24;\ndeny all;\n", "", None),
    ({"ADMIN_IP_BOLEH": "103.84.116.5,10.8.0.0/16"}, 0, "allow 103.84.116.5;\nallow 10.8.0.0/16;\ndeny all;\n", "", None),
    ({"PROKSI_DEPAN": "130.211.0.0/22,35.191.0.0/16,103.157.55.250/32", "ADMIN_AWALAN": "/admin/"}, 0, None,
     "set_real_ip_from 130.211.0.0/22;\nset_real_ip_from 35.191.0.0/16;\nset_real_ip_from 103.157.55.250/32;\n"
     "real_ip_header X-Forwarded-For;\nreal_ip_recursive on;\n", 'proxy_set_header X-Forwarded-Prefix "/admin";\n'),
    ({"PROKSI_DEPAN": "2600:2d00:1:b029::/64"}, 0, None,
     "set_real_ip_from 2600:2d00:1:b029::/64;\nreal_ip_header X-Forwarded-For;\nreal_ip_recursive on;\n", None),
] + [({"ADMIN_IP_BOLEH": v}, 1, None, None, None) for v in (
    "1.2.3.4;include /etc/passwd", "*", ",", TAB, "," + TAB + ",", " ", "103.84.116.0/24 x", "103.84.116.0/24\nallow all",
    "10.0.0.0/", "/8", "10.0.0.0/8/9", "10.0.0.0/33", "10.0.0.0/0008", "2001:db8::/129") + TERLALU_LUAS["ADMIN_IP_BOLEH"]] + [
    ({"PROKSI_DEPAN": v}, 1, None, None, None) for v in ("10.0.0.0/8 x", "10.0.0.0/8,*") + TERLALU_LUAS["PROKSI_DEPAN"]] + [
    ({"ADMIN_AWALAN": v}, 1, None, None, None) for v in ('/admin";proxy_pass http://x', "admin", "/a//b")]
shell_ada = [[x] for x in ("sh", "dash") if shutil.which(x)] + ([["busybox", "sh"]] if shutil.which("busybox") else [])
for shell in shell_ada:
    for env, kode, admin_ip, real_ip, awalan in JARINGAN:
        kerja = tempfile.mkdtemp(prefix="prodi-uji-jaringan-")
        try:
            k, isi, galat = jalankan("docker/nginx/40-prodi-jaringan.sh", env, kerja, shell)
            label = "%s 40-prodi-jaringan %r" % (shell[0], env)
            cek(k == kode, "%s: kode keluar %s, harus %s (%s)" % (label, k, kode, galat.strip()))
            if kode:
                cek(galat.strip() and isi("prodi/admin-ip.conf") is None, "%s: harus berhenti dengan pesan, tanpa berkas" % label)
            for nama, harap in (("admin-ip.conf", admin_ip), ("real-ip.conf", real_ip), ("admin-awalan.conf", awalan)):
                if harap is not None:
                    cek(isi("prodi/" + nama) == harap, "%s: %s = %r" % (label, nama, isi("prodi/" + nama)))
            if any(env.get(k) in v for k, v in TERLALU_LUAS.items()):
                cek("terlalu luas" in galat, "%s: pesan harus menyebut jaringan terlalu luas: %s" % (label, galat.strip()))
        finally:
            shutil.rmtree(kerja, ignore_errors=True)

    def https(env, sertifikat=False, terkunci=False):
        """45-prodi-https.sh in a temporary folder; terkunci: a key that cannot be read (owned by another user)."""
        kerja = tempfile.mkdtemp(prefix="prodi-uji-https-")
        os.makedirs(os.path.join(kerja, "conf.d"))
        if sertifikat:
            os.makedirs(os.path.join(kerja, "tls"))
            for n in ("fullchain.pem", "privkey.pem"):
                with io.open(os.path.join(kerja, "tls", n), "w") as f:
                    f.write("uji\n")
            if terkunci:
                os.chmod(os.path.join(kerja, "tls", "privkey.pem"), 0)
        try:
            k, isi, galat = jalankan("docker/nginx/45-prodi-https.sh", env, kerja, shell)
            hasil = {n: isi(n) for n in ("prodi/port-80.conf", "prodi/port-8081.conf", "conf.d/https.conf")}
            hasil["galat"] = galat
            return k, hasil
        finally:
            shutil.rmtree(kerja, ignore_errors=True)
    k, isi = https({})
    cek(k == 0 and "lokasi-situs.conf" in isi["prodi/port-80.conf"] and "lokasi-admin.conf" in isi["prodi/port-8081.conf"]
        and isi["conf.d/https.conf"] is None, "%s 45-prodi-https: HTTP di belakang load balancer: %r" % (shell[0], isi))
    k, isi = https({"HTTPS_DI_VM": "1", "PORT_SITUS_HTTPS": "443", "PORT_ADMIN_HTTPS": "8444"}, sertifikat=True)
    cek(k == 0 and "return 301 https://$host$request_uri;" in isi["prodi/port-80.conf"]
        and "return 301 https://$host:8444$request_uri;" in isi["prodi/port-8081.conf"]
        and "listen 443 ssl;" in isi["conf.d/https.conf"] and "listen 8443 ssl;" in isi["conf.d/https.conf"],
        "%s 45-prodi-https: HTTPS di VM: %r" % (shell[0], isi))
    for env, sertifikat in (({"HTTPS_DI_VM": "1"}, False), ({"HTTPS_DI_VM": "ya"}, True),
                            ({"HTTPS_DI_VM": "1", "PORT_ADMIN_HTTPS": "84a"}, True)):
        cek(https(env, sertifikat)[0] == 1, "%s 45-prodi-https %r harus berhenti" % (shell[0], env))
    if os.geteuid() != 0:                 # root reads any file here; in the web container it does not (cap_drop)
        k, isi = https({"HTTPS_DI_VM": "1"}, sertifikat=True, terkunci=True)
        cek(k == 1 and "privkey.pem di TLS_FOLDER tidak bisa dibaca" in isi["galat"] and isi["conf.d/https.conf"] is None,
            "%s 45-prodi-https: kunci yang tidak terbaca menghentikan start dengan pesan: %r" % (shell[0], isi["galat"]))
cek(shell_ada, "tidak ada shell POSIX untuk menguji skrip awal web")

sh = shutil.which("sh")

# --- the start of the admin checks its settings (app.buat_app) before building: the line of admin-mulai.sh, run as it
# is from the root of the code (/app in the image), with the session key of a new VM
mulai = baca("docker/admin-mulai.sh")
baris = [b for b in mulai.splitlines() if "app.buat_app()" in b and not b.lstrip().startswith("#")]
cek(len(baris) == 1 and mulai.index(baris[0]) < mulai.index("bangun.py") < mulai.index("waitress-serve"),
    "admin-mulai.sh memeriksa pengaturan admin sekali, sebelum situs dibangun: %r" % baris)
if baris and sh:
    kerja = tempfile.mkdtemp(prefix="prodi-uji-mulai-")
    try:
        with io.open(os.path.join(kerja, ".env"), "w", encoding="utf-8") as f:
            f.write("SECRET_KEY=%s\n" % ("k" * 64))
        dasar = {"PATH": os.path.dirname(sys.executable) + os.pathsep + os.environ.get("PATH", "/usr/bin:/bin"),
                 "PRODI_RAHASIA": kerja, "PRODI_DATA": os.path.join(kerja, "data"), "PRODI_LOG": os.path.join(kerja, "log"),
                 "PRODI_RIWAYAT": os.path.join(kerja, "riwayat"), "WWW_DATA": os.path.join(kerja, "www")}
        for env, kode, pesan in (({}, 0, ""), ({"PRODI_MODE": "produksi", "ADMIN_HTTPS": "1"}, 0, ""),
                                 ({"PRODI_MODE": "produksi"}, 1, "ADMIN_HTTPS=1"),
                                 ({"PRODI_MODE": "produksi", "ADMIN_HTTPS": "0"}, 1, "ADMIN_HTTPS=1"),
                                 ({"ADMIN_IP_BOLEH": "0.0.0.0/0"}, 1, "terlalu luas"),
                                 ({"ADMIN_IP_BOLEH": "103.84.116.0/24 bukan"}, 1, "tidak sah"),
                                 ({"PRODI_BANGUN_HARIAN": "25:99"}, 1, "PRODI_BANGUN_HARIAN")):
            r = subprocess.run([sh, "-c", "set -eu\n" + baris[0]], cwd=AKAR, env=dict(dasar, **env), capture_output=True,
                               text=True, timeout=120)
            cek(r.returncode == kode and pesan in r.stderr,
                "admin-mulai.sh %r: kode %s (harus %s), pesan %r" % (env, r.returncode, kode, r.stderr.strip()[-300:]))
    finally:
        shutil.rmtree(kerja, ignore_errors=True)

# --- the shell scripts parse
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
