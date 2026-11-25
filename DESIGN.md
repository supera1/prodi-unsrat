---
name: Peta Jalur Fakultas (prodi.unsrat.ac.id root directory)
description: The root directory of the 97 UNSRAT programme sites as a transit line map, one faculty-flag line per faculty and one stop per programme.
colors:
  putih: "#ffffff"
  tinta: "#15123b"
  tinta-lembut: "#4b4966"
  garis: "#e3e2ec"
  sorot: "#f3f2f8"
  # Faculty flag data (not design choices): ground and computed lettering per line, as generated into
  # publik/aset/css/jalur.css by bangun.warna_jalur from www's unit data. Refresh when www changes a flag.
  bendera-ft: "#000099"
  bendera-ft-teks: "#FFFF00"
  bendera-fk: "#013300"
  bendera-fk-teks: "#FFFF00"
  bendera-faperta: "#00FF01"
  bendera-faperta-teks: "#3500FF"
  bendera-fapet: "#663200"
  bendera-fapet-teks: "#FFFF00"
  bendera-fpik: "#0000FE"
  bendera-fpik-teks: "#00FFFF"
  bendera-feb: "#C6C6C6"
  bendera-feb-teks: "#3500FF"
  bendera-fh: "#FE0002"
  bendera-fh-teks: "#000000"
  bendera-fisip: "#FF8500"
  bendera-fisip-teks: "#15123B"
  bendera-fib: "#9A00FF"
  bendera-fib-teks: "#FFFF00"
  bendera-fmipa: "#FFFFFF"
  bendera-fmipa-teks: "#3500FF"
  bendera-fkm: "#381873"
  bendera-fkm-teks: "#FFFF00"
  bendera-pps: "#503003"
  bendera-pps-teks: "#FFFFFF"
typography:
  display:
    fontFamily: "Overpass, ui-sans-serif, system-ui, Segoe UI, Roboto, sans-serif"
    fontSize: "clamp(1.75rem, 1.3rem + 1.6vw, 2.5rem)"
    fontWeight: 800
    lineHeight: 1.2
    letterSpacing: "-0.015em"
  headline:
    fontFamily: "Overpass, ui-sans-serif, system-ui, Segoe UI, Roboto, sans-serif"
    fontSize: "clamp(1.5rem, 1.2rem + 1.2vw, 2.125rem)"
    fontWeight: 800
    lineHeight: 1.2
    letterSpacing: "-0.01em"
  title:
    fontFamily: "Overpass, ui-sans-serif, system-ui, Segoe UI, Roboto, sans-serif"
    fontSize: "1rem"
    fontWeight: 800
    lineHeight: 1.25
  body:
    fontFamily: "Overpass, ui-sans-serif, system-ui, Segoe UI, Roboto, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.4
  body-strong:
    fontFamily: "Overpass, ui-sans-serif, system-ui, Segoe UI, Roboto, sans-serif"
    fontSize: "1rem"
    fontWeight: 600
    lineHeight: 1.3
  brand:
    fontFamily: "Overpass, ui-sans-serif, system-ui, Segoe UI, Roboto, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 800
    lineHeight: 1.15
  button-large:
    fontFamily: "Overpass, ui-sans-serif, system-ui, Segoe UI, Roboto, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 800
  body-note:
    fontFamily: "Overpass, ui-sans-serif, system-ui, Segoe UI, Roboto, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 400
    lineHeight: 1.4
  body-caption:
    fontFamily: "Overpass, ui-sans-serif, system-ui, Segoe UI, Roboto, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.15
  badge:
    fontFamily: "Overpass, ui-sans-serif, system-ui, Segoe UI, Roboto, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 800
    lineHeight: 1.2
  body-small:
    fontFamily: "Overpass, ui-sans-serif, system-ui, Segoe UI, Roboto, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 400
    lineHeight: 1.4
  label:
    fontFamily: "Overpass, ui-sans-serif, system-ui, Segoe UI, Roboto, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 800
    lineHeight: 1.2
  mono-level:
    fontFamily: "Overpass Mono, ui-monospace, SFMono-Regular, Menlo, monospace"
    fontSize: "0.6875rem"
    fontWeight: 600
    letterSpacing: "0.08em"
  mono-count:
    fontFamily: "Overpass Mono, ui-monospace, SFMono-Regular, Menlo, monospace"
    fontSize: "0.75rem"
    fontWeight: 600
    fontFeature: "tnum"
rounded:
  pill: "999px"
  arrival: "0.875rem"
  control: "0.75rem"
  line-head: "0.625rem"
  stop: "0.5rem"
  tag: "0.375rem"
  terminus: "0.1875rem"
spacing:
  tepi-akar: "clamp(1rem, 4vw, 4rem)"
  lebar-luas: "1376px"
components:
  search-box:
    backgroundColor: "{colors.putih}"
    textColor: "{colors.tinta}"
    rounded: "{rounded.control}"
    padding: "0 1.125rem"
    height: "3.75rem"
  line-badge:
    rounded: "{rounded.pill}"
    padding: "0.5rem 0.8rem 0.35rem"
    typography: "{typography.badge}"
  line-head:
    rounded: "{rounded.line-head}"
    padding: "0.8rem 1rem 0.6rem"
    typography: "{typography.title}"
  stop:
    textColor: "{colors.tinta}"
    rounded: "{rounded.stop}"
    height: "3rem"
  stop-hover:
    backgroundColor: "{colors.sorot}"
  grade-tag:
    textColor: "{colors.tinta}"
    rounded: "{rounded.tag}"
    padding: "0.25rem 0.5rem 0.15rem"
    typography: "{typography.label}"
  grade-tag-top:
    backgroundColor: "{colors.tinta}"
    textColor: "{colors.putih}"
    rounded: "{rounded.tag}"
    padding: "0.25rem 0.5rem 0.15rem"
  button-open:
    backgroundColor: "{colors.tinta}"
    textColor: "{colors.putih}"
    rounded: "{rounded.control}"
    padding: "0.75rem 1.75rem 0.55rem"
    height: "3.5rem"
  button-reset:
    backgroundColor: "{colors.putih}"
    textColor: "{colors.tinta}"
    rounded: "{rounded.stop}"
    padding: "0.625rem 1rem 0.5rem"
  button-reset-hover:
    backgroundColor: "{colors.sorot}"
---

# Design System: Peta Jalur Fakultas

**Scope.** This system governs the root directory page of prodi.unsrat.ac.id only (`platform/template/halaman/akar.html`, styled by `aset/css/akar.css`, `aset/css/akar-tanpa-js.css` and the generated `aset/css/jalur.css`). It does not restyle the 97 programme sites: those keep their own older system in `platform/template/aset/css/prodi.css` and `tokens.css`, and nothing here should be copied into them. `akar.css` loads after `prodi.css` on the root page alone and redirects a few shared variables (`--unsrat-abu-900`, `--prodi-utama`, `--prodi-aksen`) to the ink so the shared top bar and footer join this world.

## Overview

**Creative North Star: "The Faculty Line Map"**

The directory reads as a transit map. Each faculty (and the Program Pascasarjana) is one line drawn in its own flag colour, each programme is a stop on that line, and the search box is the destination. The page is white paper with one indigo-black ink. All colour comes from the faculty flags, drawn from www's unit data, and appears only as line material: the thick rail, the solid line head band, the jump badge.

Density is a printed timetable's, not an office table's. Every stop keeps a fixed column order (stop dot, name over degree, grade tag on the right), so a visitor scans down a line without reading across. Levels change on a line through a small monospaced label, like a zone marker. Overpass, the highway-sign family, sets everything, and Overpass Mono sets level labels and counts.

The interaction belongs to the map too. Typing filters the stops. Lines left empty fold away and their badges dim. Matching stops light once. When one programme is left, its stop grows into an arrival panel on its own line, with a single door, "Buka situs".

**Key Characteristics:**
- Three inks besides the flags: white ground, ink `#15123b`, soft ink `#4b4966`; two quiet tints for hairlines and hover.
- Faculty colour lives only in line material, never in running text.
- Thick rails (0.625rem) with white stops ringed in ink.
- A fixed stop row: dot column 3.25rem, name and degree, grade tag.
- Flat; depth comes from lines and solid bands, not shadows.
- Works without JavaScript: the whole map is always in the HTML, and search only narrows it.

## Colors

One ink on white. Faculty flags supply all the colour, and they are data, not tokens.

### Primary
- **Indigo Ink** (`tinta`): all text, the search box border, stop rings, focus outlines, the filled top-grade tag, the "Buka situs" button, the selection colour, and the fallback line colour for any unit without a usable flag. 16.9:1 on white.

### Neutral
- **Paper White** (`putih`): the page ground, stop centres, the search field, the reset button.
- **Soft Ink** (`tinta-lembut`): secondary text such as degree, status line, level labels, the header's unit line, the placeholder and the count sentence. 8.6:1 on white.
- **Hairline Lilac** (`garis`): the 1px rules under the header and under the badge row. Never used for text.
- **Pointer Wash** (`sorot`): the background of a stop under the pointer and the reset button's hover. The ink on it is 15.6:1.

### Line colours (faculty flag data)
The `bendera-*` entries in the frontmatter record each line's ground (`bendera-<unit>`) and computed lettering (`bendera-<unit>-teks`) exactly as the current build ships them in `publik/aset/css/jalur.css`: FT, FK, Faperta, Fapet, FPIK, FEB, FH, FISIP, FIB, FMIPA, FKM and Pascasarjana (`pps`). They are data, not design choices. Their source of truth is the flag (`bendera.dasar`, `bendera.tulisan`) in www's unit data, passed through `bangun.warna_jalur`. The build follows www when a flag changes, and these entries then need a refresh. Two lettering values are computed, not the flag's own: FH's black (`#000000`, the only candidate reaching 4.5:1 on its red) and FISIP's ink (`#15123B`). The edge colour (`--jalur-tepi`) is not listed separately: it is the ground itself, or `tinta` for the pale grounds of Faperta, FEB, FISIP and FMIPA.

Each line carries three custom properties, `--jalur`, `--jalur-teks` and `--jalur-tepi`, written by `bangun.py` (`warna_jalur`, `css_jalur`) into `aset/css/jalur.css` as `.jalur--<unit code>` rules. The CSP forbids inline styles, which is why the flag colours arrive in a generated stylesheet rather than as `style` attributes. The rules:
- `--jalur` is the flag's ground colour (`bendera.dasar`).
- `--jalur-teks` is the flag's own lettering colour (`bendera.tulisan`) when it reaches 4.5:1 on the ground. Otherwise it is the first of white, ink or black that does, or failing all three, the best of them.
- `--jalur-tepi` is the ground itself when the ground reaches 3:1 against white. A paler line (white MIPA, light Pertanian green, grey FEB, orange FISIP) is edged in ink instead.
- No usable flag, or a code that is not a plain lowercase word: the line stays ink, with white text (the `:where(.jalur, .lencana, .tiba)` default in `akar.css`).

### Named Rules
**The Flags Only On Lines Rule.** A faculty colour fills only line material: the rail, the line-head band, the jump badge, the arrival band and rail, and a stop's light-up. Text, tags and buttons stay in ink.

**The Computed Lettering Rule.** Never hand-pick a text colour for a line. It comes from `warna_jalur`'s contrast ladder, so the next faculty flag from www lands legibly with no design work.

**The Ink Edge Rule.** A line under 3:1 against white gets an ink edge (an inset 2px ring in `--jalur-tepi`), so a white or near-white flag still reads as a line.

## Typography

**Display Font:** Overpass (fallback ui-sans-serif, system-ui, Segoe UI, Roboto, sans-serif), weights 400 / 600 / 800
**Label/Mono Font:** Overpass Mono, weight 600

Both are loaded from Google Fonts on the root page only (`FONT_AKAR` in `bangun.py`, passed as `font` to `dasar.html`). The programme sites keep Plus Jakarta Sans.

**Character:** Road-sign lettering. It is plain, open and built to be read at a glance, with heavy 800 for names and heads and a monospace for the codes and counts a timetable would print.

### Hierarchy
- **Display** (800, clamp(1.75rem → 2.5rem), 1.2, -0.015em, balanced wrap): the single question h1, "Mau ke program studi mana?".
- **Headline** (800, clamp(1.5rem → 2.125rem), -0.01em): the programme name in the arrival panel.
- **Count figure** (800, 2.5rem, line-height 1, tabular numbers, desktop only from 64rem): the "97" beside the search.
- **Brand** (800, 1.25rem, 1.15): the header's "Program Studi" beside the emblem.
- **Button large** (800, 1.125rem): the "Buka situs" button.
- **Title** (800, 1rem, 1.25): line-head band names.
- **Search input** (600, 1.1875rem / 1.2): what the visitor types. Its placeholder drops to 400 in soft ink.
- **Body-strong** (600, 1rem, 1.3): stop names, the links into each programme.
- **Body** (400, 1rem, 1.4): page base.
- **Body-note** (400, 0.9375rem, soft ink): the count sentence beside or under the search and the search status line; the reset button uses this size at 800.
- **Body-caption** (400, 0.875rem, 1.15, soft ink): the header's unit line, "Direktori situs program studi".
- **Body-small** (400, 0.8125rem, soft ink): degree and status under a stop name.
- **Badge** (800, 0.875rem, 1.2): faculty short names on the jump badges.
- **Label** (800, 0.75rem on stops, 0.8125rem in the arrival panel): grade tags.
- **Mono level** (Overpass Mono 600, 0.6875rem, 0.08em, uppercase, soft ink): the level marker on a line ("SARJANA", "MAGISTER").
- **Mono count** (Overpass Mono 600, 0.75rem in line heads, 0.8125rem in badges, tabular numbers): programme counts.

### Named Rules
**The Mono For Codes Rule.** Overpass Mono sets only level markers and counts, the timetable's codes. Names and sentences are never monospaced.

**The Heavy Names Rule.** Names a visitor is looking for carry weight: 800 for line heads, the arrival name and tags, 600 for stop names. Secondary facts stay 400 in soft ink.

## Layout

- **Container:** full width up to 1376px (`--unsrat-lebar-luas`), centred, with side gutters of `--tepi-akar` (clamp(1rem, 4vw, 4rem)). The header, the destination block, the badge row, the arrival panel and the map all share it.
- **Header:** a 4.5rem band with the UNSRAT emblem (48px) and a two-line name, ruled underneath with a hairline. The shared top bar of `dasar.html` sits above it in ink.
- **Destination block:** the h1 and search (search max 46rem wide) on the left. From 64rem the count figure sits right-aligned in a second column (`minmax(0,1fr) auto`, bottom-aligned). Below that width the count becomes a sentence under the search.
- **Badge row:** wrapping flex row of pills, 0.5rem gaps, closed by a hairline.
- **The map:** CSS multi-column, `columns: 4 17.5rem` with a 1.75rem gap. That gives four columns on wide desktop and one on phones, with no breakpoint code. Each line is `break-inside: avoid` and `display: inline-block` so it never splits across columns; lines are spaced 1.75rem apart.
- **The stop row:** a fixed three-column grid, 3.25rem dot column, flexible name column, auto tag column; minimum height 3rem (a full touch target).
- **Rhythm:** 0.5rem / 0.75rem / 1rem / 1.5rem / 1.75rem recur; the map starts 1.5rem below the badges and ends with 3rem.
- **Order of lines** follows www's unit data order; each line lists programmes by level, then name.
- **Minimum width:** 320px with no horizontal scroll.

## Elevation & Depth

Flat. No surface casts a shadow. Depth and grouping come from line material: solid flag bands, 0.625rem rails, 2px ink borders and 1px hairlines. The only `box-shadow` in this world is `inset 0 0 0 2px var(--jalur-tepi)`, an inner edge that keeps pale flags visible on white. It is a border, not elevation.

### Named Rules
**The Line Is The Depth Rule.** Separate things with a rail, a band or a hairline, never a drop shadow or a raised card.

## Shapes

- **Circles** for stops: 1.25rem white dots with a 0.3125rem ink ring; 1.75rem with a 0.4rem ring in the arrival panel.
- **Rails:** 0.625rem bars in the line colour. Every rail ends in a terminus: a bar across the line, 1.5rem × 0.375rem, in `--jalur-tepi`, softly rounded (`terminus`, 0.1875rem, half its height).
- **Pills** (999px) for the jump badges only.
- **Gently rounded rectangles** elsewhere: line-head bands round only their top corners (0.625rem), and so does the arrival band (0.875rem), with the arrival body rounding its bottom corners to match. Controls use 0.75rem, stop hover areas and the reset button 0.5rem, grade tags 0.375rem.
- **Borders** are 2px ink for interactive containers (search box, reset button, arrival body), 1.5px ink for grade tags, and 1px `garis` for page rules.

## Components

### Search box (the destination)
The page's primary action, first in the reading order after the question.
- **Shape:** 0.75rem radius, 2px ink border, white fill, minimum height 3.75rem, 0.75rem gap between an inline SVG magnifier (22px, stroke 2.4) and the field.
- **Field:** borderless input, 600 at 1.1875rem; placeholder "Mis. Teknik Informatika" at 400 in soft ink.
- **Focus:** the whole box takes a 3px ink outline at 3px offset (`:focus-within`). The input itself shows no separate ring.
- **Status line:** a polite live region under the box, 0.9375rem soft ink, reserved at 1.5rem height so nothing jumps.
- **No results:** a reset button appears, "Tampilkan semua program studi", with a 2px ink border, 0.5rem radius and white fill, washing to `sorot` on hover.
- **Without JavaScript:** the form is hidden by `akar-tanpa-js.css` inside `<noscript>`. With JavaScript it is present from first paint.

### Line badges (jump links)
- **Style:** pill, filled with `--jalur`, text in `--jalur-teks`, 2px inset edge in `--jalur-tepi`; 800 at 0.875rem for the short name, Overpass Mono 600 at 0.8125rem for the count.
- **Hover:** lifts 2px (0.2s, `cubic-bezier(0.16, 1, 0.3, 1)`); no lift under reduced motion.
- **Focus:** 3px ink outline, 3px offset.
- **Dimmed:** when a search empties its line, opacity 0.28, `aria-disabled`, removed from the tab order, no pointer events.

### Line (signature component)
- **Head band:** a solid band in `--jalur` with `--jalur-teks` text, top corners rounded 0.625rem, the line name (Title) left and "N prodi" (Mono count) right.
- **Rail:** 0.625rem bar under the band from top to terminus, left offset 1.0625rem, inset edge in `--jalur-tepi`.
- **Level marker:** Mono level label set 3.25rem in, at each change of level along the line.
- **Fallback:** a unit with no flag draws in ink with white text.

### Stop
- **Row:** dot column, name (600, ink) over degree and status (0.8125rem soft ink, joined by " · "), grade tag right.
- **Dot:** white circle ringed in ink; it scales to 1.2 on hover or focus within (0.2s).
- **Hit area:** the whole row opens the programme (the name link's `::after` covers it). Hover washes the row in `sorot` and underlines the name 2px.
- **Focus:** a 3px ink outline drawn around the whole row (1px offset).
- **Light-up:** after a search, matching stops' dots fill with the line colour at 1.35 scale and settle back to white in 0.45s (`cubic-bezier(0.16, 1, 0.3, 1)`), once per keystroke. None under `prefers-reduced-motion: reduce`.

### Grade tag (accreditation)
- **Grades** (`PERINGKAT`: Unggul, Baik Sekali, Baik, A, B, C): outlined tag, 1.5px ink border, 0.375rem radius, 800 at 0.75rem, no wrap.
- **Top grade** (`PERINGKAT_PUNCAK`: Unggul, A): the same tag filled in ink with white text.
- **Any other status** (e.g. "Menunggu akreditasi prodi baru"): no tag; plain text in ink after the degree. An empty grade shows nothing; "belum" is never a badge.
- Screen readers hear "Akreditasi" before the grade (visually hidden prefix).

### Arrival panel
Shown only when a search leaves exactly one programme; the map hides and the panel takes its place.
- **Band:** the faculty name in a solid `--jalur` band, top corners 0.875rem.
- **Body:** 2px ink border without a top edge, bottom corners 0.875rem; the line's rail runs down its left side with a big stop on it (1.75rem white dot, 0.4rem ink ring).
- **Content:** programme name (Headline), degree and grade tag (same filled/outlined/status encoding as the stop), and one button.
- **Layout:** stacked on phones; from 48rem the name and details sit left and the button right.
- **Entrance:** slides up 0.75rem in 0.42s (`cubic-bezier(0.16, 1, 0.3, 1)`), movement only, never opacity. None under reduced motion.

### "Buka situs" button
- **Style:** ink fill, white 800 text at 1.125rem, 0.75rem radius, minimum height 3.5rem, trailing SVG arrow (22px, stroke 2.4).
- **Hover:** fill lightens to tinta-lembut (`#4b4966`, white on it 8.6:1). **Focus:** 3px ink outline at 3px offset.
- Pressing Enter in the search when one programme is left goes straight to its site.

### Navigation (header)
The emblem and "Program Studi" over "Direktori situs program studi" link home. The shared top bar's "Semua program studi" link is hidden here, because this page is that list.

## Do's and Don'ts

### Do:
- **Do** take every line colour from `aset/css/jalur.css` via `--jalur`, `--jalur-teks` and `--jalur-tepi`; add a faculty by updating www's unit data and rebuilding, not by writing CSS.
- **Do** keep faculty colour on line material only (rail, head band, badge, arrival band, light-up) and keep all text, tags and buttons in `tinta`.
- **Do** keep the stop row's fixed columns (3.25rem dot column, name over degree, tag right) on every line and at every width.
- **Do** use a 3px `tinta` outline at a 3px offset for keyboard focus (1px offset on stop rows).
- **Do** keep the full map in the HTML and treat search as a progressive filter from the separate `cari-prodi.js`; no inline scripts or styles.
- **Do** gate every movement (badge lift, dot scale, light-up, arrival slide) behind `prefers-reduced-motion`, and animate movement rather than opacity so a paused animation never hides content.

### Don't:
- **Don't** introduce a colour beyond white, `tinta`, `tinta-lembut`, `garis`, `sorot` and the generated flag colours. UNSRAT blue `#3500ff` and yellow `#f2b705` from `tokens.css` are not part of this world (they appear here only where a faculty flag's own lettering uses them).
- **Don't** put flag colour on running text, or rely on a flag colour alone to carry meaning.
- **Don't** add drop shadows or raised cards; separate with rails, bands, borders and hairlines.
- **Don't** monospace names or sentences; Overpass Mono is for level markers and counts.
- **Don't** apply this stylesheet, these fonts or these tokens to the programme sites.
