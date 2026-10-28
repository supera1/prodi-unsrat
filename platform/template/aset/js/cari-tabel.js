/* A search box above every long table of a programme's page (a table the builder marks with data-cari, 30 rows or
   more: final projects, publications, courses). Added here, so without JavaScript the whole table stays as it is.
   Typed words must all appear in a row (letter case and accents ignored); the number of rows shown is announced. */
(function () {
	"use strict";

	function normal(teks) {
		return teks.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
	}

	var wadah = document.querySelectorAll(".tabel-gulir[data-cari]");
	Array.prototype.forEach.call(wadah, function (w, i) {
		var tabel = w.querySelector("table");
		if (!tabel || !tabel.tBodies.length) {
			return;
		}
		var baris = Array.prototype.slice.call(tabel.tBodies[0].rows);
		var teks = baris.map(function (r) { return normal(r.textContent); });
		var kotak = document.createElement("div");
		var label = document.createElement("label");
		var masukan = document.createElement("input");
		var info = document.createElement("p");
		var tunda = null;

		kotak.className = "cari-tabel";
		masukan.type = "search";
		masukan.id = "cari-tabel-" + (i + 1);
		masukan.autocomplete = "off";
		label.htmlFor = masukan.id;
		label.textContent = "Cari di tabel ini";
		info.className = "cari-tabel__info";
		info.setAttribute("aria-live", "polite");

		function jumlah(n) {
			info.textContent = n === baris.length ? baris.length + " baris" : n + " dari " + baris.length + " baris";
		}

		function saring() {
			var kata = normal(masukan.value).split(/\s+/).filter(Boolean);
			var n = 0;
			baris.forEach(function (r, j) {
				var cocok = kata.every(function (k) { return teks[j].indexOf(k) !== -1; });
				r.hidden = !cocok;
				if (cocok) {
					n += 1;
				}
			});
			jumlah(n);
		}

		masukan.addEventListener("input", function () {
			window.clearTimeout(tunda);
			tunda = window.setTimeout(saring, 150);
		});
		jumlah(baris.length);
		kotak.appendChild(label);
		kotak.appendChild(masukan);
		kotak.appendChild(info);
		w.parentNode.insertBefore(kotak, w);
	});
}());
