/* The search on the root page (prodi.unsrat.ac.id/, K-P39). Without JavaScript the form is hidden (akar-tanpa-js.css
   in <noscript>) and the whole line map is there to read. With it, typed words must all appear in a stop's name,
   degree, faculty or level (letter case and accents ignored); stops that do not match are hidden, a level or a line
   left empty folds away and its badge dims, the stops found light up once, and the count is announced. When one
   programme is left, the map gives way to it: its stop, grown, on its line, with one door. The words typed stay in
   the address (?q=) so a search can be shared or reloaded. */
(function () {
	"use strict";

	var form = document.getElementById("cari");
	var tiba = document.getElementById("tiba");
	if (!form || !tiba || !String.prototype.normalize) {
		return;
	}
	var masukan = document.getElementById("cari-prodi");
	var status = document.getElementById("cari-status");
	var ulang = document.getElementById("cari-ulang");
	var semua = Array.prototype.slice.call(document.querySelectorAll(".halte"));
	var kelompok = Array.prototype.slice.call(document.querySelectorAll(".jalur__kelompok"));
	var jalur = Array.prototype.slice.call(document.querySelectorAll(".jalur"));
	var peta = document.getElementById("peta");
	var lencana = {};
	Array.prototype.forEach.call(document.querySelectorAll(".lencana"), function (a) {
		lencana[a.getAttribute("href").slice(1)] = a;
	});

	function normal(teks) {
		return (teks || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase()
			.replace(/[^a-z0-9]+/g, " ").trim();
	}

	var teks = semua.map(function (h) { return " " + normal(h.getAttribute("data-cari")) + " "; });

	function kelasJalur(el) {
		var k = Array.prototype.filter.call(el.classList, function (c) { return c.indexOf("jalur--") === 0; });
		return k.length ? k[0] : "";
	}

	function isiTiba(h) {
		var a = h.querySelector(".halte__nama");
		var gelar = h.querySelector(".halte__gelar");
		var akr = h.querySelector(".halte__akreditasi, .halte__status");
		var j = h.closest(".jalur");
		tiba.className = "tiba wadah-akar " + kelasJalur(j);
		tiba.querySelector(".tiba__fakultas").textContent = j.querySelector(".jalur__nama").textContent;
		tiba.querySelector(".tiba__nama").textContent = a.textContent;
		tiba.querySelector(".tiba__gelar").textContent = gelar ? gelar.textContent : "";
		var tag = tiba.querySelector(".tiba__akreditasi");
		var status = !!akr && akr.classList.contains("halte__status");
		/* a grade reads "Akreditasi Unggul"; a status reads as itself, without the screen-reader prefix */
		tag.textContent = !akr ? "" : status ? akr.lastChild.textContent.trim() : akr.textContent.trim();
		/* the panel keeps the stop's encoding: top grade filled, other grades outlined, a status as plain text */
		tag.classList.toggle("tiba__akreditasi--puncak", !!akr && akr.classList.contains("halte__akreditasi--puncak"));
		tag.classList.toggle("tiba__akreditasi--status", status);
		tiba.querySelector(".tiba__buka").href = a.href;
		tiba.hidden = false;
	}

	function saring(isi) {
		var kata = normal(isi).split(" ").filter(Boolean);
		var cocok = [];
		semua.forEach(function (h, i) {
			var ya = kata.every(function (k) { return teks[i].indexOf(k) !== -1; });
			h.hidden = !ya;
			if (ya) {
				cocok.push(h);
			}
		});
		kelompok.forEach(function (k) {
			k.hidden = !k.querySelector(".halte:not([hidden])");
		});
		var tiba_ = kata.length > 0 && cocok.length === 1;
		jalur.forEach(function (j) {
			var kosong = tiba_ || !j.querySelector(".halte:not([hidden])");
			var badge = lencana[j.id];
			j.hidden = kosong;
			if (badge) {
				badge.classList.toggle("lencana--redup", kosong);
				if (kosong) {
					badge.setAttribute("aria-disabled", "true");
					badge.setAttribute("tabindex", "-1");
				} else {
					badge.removeAttribute("aria-disabled");
					badge.removeAttribute("tabindex");
				}
			}
		});
		if (!kata.length) {
			status.textContent = "";
		} else if (!cocok.length) {
			status.textContent = "Tidak ada program studi yang cocok dengan “" + isi.trim() +
				"”. Coba satu kata saja, misalnya Informatika atau Hukum.";
		} else {
			status.textContent = cocok.length + " program studi cocok.";
		}
		ulang.hidden = !(kata.length && !cocok.length);
		if (tiba_) {
			isiTiba(cocok[0]);
		} else {
			tiba.hidden = true;
		}
		peta.hidden = tiba_;
		semua.forEach(function (h) { h.classList.remove("halte--nyala"); });
		if (kata.length && !tiba_ && cocok.length) {
			void document.body.offsetWidth;   /* one reflow, so the light-up restarts on every keystroke */
			cocok.forEach(function (h) { h.classList.add("halte--nyala"); });
		}
		try {
			history.replaceState(null, "", kata.length ? "?q=" + encodeURIComponent(isi.trim()) : location.pathname);
		} catch (e) {
			/* an address that cannot change (a local file) only loses the shareable search */
		}
		return cocok;
	}

	masukan.addEventListener("input", function () { saring(masukan.value); });
	form.addEventListener("submit", function (e) {
		e.preventDefault();
		var cocok = saring(masukan.value);
		if (cocok.length === 1) {
			location.href = cocok[0].querySelector(".halte__nama").href;
		} else if (cocok.length) {
			cocok[0].querySelector(".halte__nama").focus();
		}
	});
	ulang.addEventListener("click", function () {
		masukan.value = "";
		saring("");
		masukan.focus();
	});

	var awal = new URLSearchParams(location.search).get("q");
	if (awal) {
		masukan.value = awal;
		saring(awal);
	}
}());
