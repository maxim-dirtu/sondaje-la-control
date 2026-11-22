# MVP pollster selection: scorecard and feasibility check

**Task:** [T-006](../../tasks/T-006-select-mvp-pollsters.md) · **Date:** 2026-11-22 ·
**Status:** input for the draft ADR [draft-mvp-pollsters.md](../decisions/draft-mvp-pollsters.md);
awaiting owner approval.

This report scores **every pollster in the T-005 registry**
([`data/registry/pollsters.csv`](../../data/registry/pollsters.csv), 15 houses)
on the T-006 criteria. It is also the feasibility check for poll collection:
for each house it records where the original publications are and in which
format, so that T-011 knows which extraction paths it must support.

Selection is about **data availability and transparency only**. Accuracy,
house effects, and affiliation records play no role here (affiliations feed
M-5.1d later). Wording follows [ADR-0003](../decisions/0003-neutral-language.md).

---

## 1. Method

### 1.1 Windows

| Election | Election day | Final window (M-1.3, `window_days` = 21): `fieldwork_end` from … to … | 120-day campaign window (M-3.2): `fieldwork_end` from … |
|---|---|---|---|
| `parl-2024-cd` | 2024-12-01 | 2024-11-10 … 2024-11-30 | 2024-08-03 |
| `pres-2025-r1` | 2025-05-04 | 2025-04-13 … 2025-05-03 | 2025-01-04 |
| `pres-2025-r2` | 2025-05-18 | 2025-04-27 … 2025-05-17, **and** `fieldwork_start` after 2025-05-04 (R-84) | after 2025-05-04 (R-84) |

R-84 means that Dan–Simion head-to-heads asked before round 1 are not
`pres-2025-r2` polls, even when their fieldwork ends inside the 21-day window
(e.g. AtlasIntel 28 Apr–1 May, MKOR 24–27 Apr, Noi, Cetățenii 24–30 Apr).
"Gap" below = election day − `fieldwork_end`, in days.

### 1.2 Sources used (all retrieved 2026-11-22)

- **Discovery indexes** (not sources, AGENTS.md §6): EN/RO Wikipedia
  opinion-polling pages for both elections (wikitext parsed) and the
  structured poll lists embedded in the 31 `sondajeromania.ro/institute/<slug>`
  pages plus `sondajeromania.ro/sondaje/2024`.
- **Gap searches** beyond the indexes: web searches for every house without
  a final-window poll in the indexes; the WordPress post lists of curs.ro
  (2024-10-25…12-02, 2025-03-25…05-19) and inscop.ro (2024-11, 2025-04…05);
  the own-site poll pages of AtlasIntel and BCS.
- **Originals opened** for every final-window poll of the houses that are
  candidates for selection, and for the nearest poll of CURS, Verifield and
  Avangarde. PDFs were downloaded and their text layer was checked
  (`pypdf`); chart pages were rendered (`pypdfium2`) and read. Web Archive
  availability was checked for the key originals. Scratch files stayed in the
  git-ignored `build/` folder; no data file was changed.

### 1.3 Scoring scale

| Criterion | Scale |
|---|---|
| 1. Coverage (required) | ✓ / ✗ per election: at least one poll in the final window. Count of polls in the 120-day windows (approximate). |
| 2. Full topline | **Full**: every option incl. undecided / non-response on at least one base. **Expressed**: complete on the expressed-option base (parties + "other" sum to 100), but undecided / non-response not shown as options. **Partial**: only some options. |
| 3. Transparency | Number of the 7 M-5.3 items published for the final-window poll(s): sample size (n), fieldwork dates (D), mode (M), exact question wording (Q), weighting description (W), margin of error (E), client/sponsor or self-funding statement (S). Read as DATA_MODEL §6.11 would record them. |
| 4. Access & format | Where the original is (own site / media-hosted file / media article only) and its format: text PDF, chart-image PDF, HTML, image, Google Sheets, video. |
| 5. Popularity (rough) | **High / Medium / Low**, from (a) the number of polls in the three 120-day windows and (b) the national outlets that commissioned, first published, or widely republished them. Not a measured citation count. |

---

## 2. Summary scorecard

| Pollster | 1. Final window parl / r1 / r2 | Polls in 120-day windows (parl + r1 + r2) | 2. Topline | 3. M-5.3 items (final-window polls) | 4. Main access & format | 5. Popularity |
|---|---|---|---|---|---|---|
| **atlasintel** | ✓ / ✓ / ✓ | 1 + 6 + 2 = 9 | Full | 5–6 / 7 | Own-site PDF (text layer, values in chart images) + HotNews HTML/images | High |
| **sociopol** | ✓ / ✓ / ✓ | 1 + 12 + 1 = 14 | Expressed (no undecided) | 3–6 / 7 | Media only: România TV HTML + broadcast screenshots | High |
| curs | ✗ (26 d) / ✗ (24 d) / ✓ | 3 + 3 + 1 = 7 | Expressed | 6 / 7 | Own-site text PDF + slide PNGs; r2 media only (TVR Info) | High |
| verifield | ✗ (53 d) / ✗ (37 d) / ✓ | 1–2 + 2 + 1 = 4–5 | Full (r2 PDF) | 5 / 7 | Media-hosted text PDF (r2); media articles | Medium |
| mkor | ✗ (no poll) / ✓ / ✓ | 0 + 3 + 1 = 4 | Full | 7 / 7 | Own-site HTML report with PNG charts | Medium |
| irsop | ✗ (no poll) / ✓ / ✓ | 0 + 1 + 1 = 2 | Expressed | 5–6 / 7 | Press-release images in HotNews | Medium |
| noi-cetatenii | ✗ (no poll) / ✓ / ✓ | 0 + 3 + 1 = 4 | Not verified (values in charts) | 6 / 7 | Google Sheets (values in embedded charts) | Low |
| inscop | ✓ / ✗ (none) / ✗ (none) | 3 + 0 + 0 = 3 | Expressed (two bases) | 6 / 7 | Own-site text PDF | High |
| ara | ✗ (none) / ✓ / ✗ (exit poll only) | 0 + 5 + 0 = 5 | Expressed (+ footnote shares) | 5 / 7 | Media (Antena 3 CNN, broadcast video, Libertatea); unattributed text PDF | Medium |
| bcs | ✓ / ✗ / ✗ | 3 + 0 + 0 = 3 | Full | 7 / 7 | Own-site text PDF | Medium |
| cira | ✓ / ✗ / ✗ | 2 + 0 + 0 = 2 | Partial | 6 / 7 | Media article (Newsweek) | Low |
| flashdata | ✗ / ✓ / ✗ | 0 + 4 + 0 = 4 | Full | 6 / 7 | Media (Agerpres HTML) | Medium |
| dataecho | ✗ / ✓ / ✗ | 0 + 2 + 0 = 2 | Not verified (values in images) | 3–4 / 7 | Image PDF, site offline (Web Archive) | Low |
| avangarde | ✗ / ✗ (42 d) / ✗ (exit poll only) | 0 + 2 + 0 = 2 | Not checked | 6–7 / 7 (Mar 2025, outside window) | Media-hosted text PDF (Libertatea) | Medium |
| snap-market-research | ✗ / ✗ / ✗ | 0 + 0 + 0 = 0 | Not checked | not assessed | Press release (Oficiul de Știri) | Low |

**Only AtlasIntel and Sociopol meet the required coverage** (a final-window
poll in all three elections). This corrects the T-005 working note
("AtlasIntel, CURS and Verifield appear in all three"): that holds for the
120-day windows, but CURS's and Verifield's latest `parl-2024-cd` and
`pres-2025-r1` polls end before the 21-day window. Sociopol qualifies through a
`parl-2024-cd` poll (20–22 Nov 2024) that **is not in any discovery index**;
it was found through a gap search.

---

## 3. Criterion 1: coverage, with evidence

### 3.1 Final-window polls found

**`parl-2024-cd`** (window 2024-11-10 … 11-30)

| Pollster | Fieldwork | Gap | n | Evidence |
|---|---|---|---|---|
| atlasintel | 26–28 Nov 2024 | 3 | 2,116 | Own page <https://atlasintel.org/poll/romania-national-2024-11-28>, report <https://cdn.atlasintel.org/68075413-7a7e-4f1d-aea3-bdcc03fbdfde.pdf>; HotNews <https://hotnews.ro/ultimul-mare-sondaj-inainte-de-alegerile-parlamentare-de-duminica-surpriza-uriasa-in-varful-ierarhiei-1848186> |
| sociopol | 20–22 Nov 2024 | 9 | 1,000 | România TV <https://www.romaniatv.net/sondaj-sociopol-pe-cine-prefera-romanii-la-alegerile-parlamentare-psd-conduce-detasat_8633323.html>, broadcast graphic <https://www.romaniatv.net/wp-content/uploads/2024/11/sondaj-3.jpg> |
| cira | 9–13 Nov 2024 | 18 | 1,040 | Newsweek România <https://newsweek.ro/politica/exclusiv-un-nou-sondaj-care-da-o-finala-ciolacu-ciuca-urmeaza-simion-si-lasconi-scorul-partidelor> |
| inscop | 7–12 Nov 2024 | 19 | 1,100 | <https://www.inscop.ro/wp-content/uploads/2024/11/15.11.-Sondaj-INSCOP-LIBERTATEA.-Partea-a-II-a-Alegeri-Parlamentare.pdf> |
| bcs | 7–10 Nov 2024 | 21 | 1,157 | <https://bcs.com.ro/sondaj/barometru-politic-national-7-10-noiembrie-2024/>, report <https://bcs.com.ro/wp-content/uploads/2024/11/Barometru-BCS-noiembrie2024.pdf> |

Nearest polls outside the window: CURS 30 Oct–5 Nov (gap 26,
<https://curs.ro/wp-content/uploads/2024/11/Prezentare-national-noiembrie-2024-public.pdf>);
Verifield 7–9 Oct (gap 53, <https://www.digi24.ro/alegeri-prezidentiale-2024/marcel-ciolacu-si-george-simion-in-turul-doi-la-prezidentiale-sondaj-comandat-de-usr-2968707>).
Checked and **not** parliamentary: Verifield's 1–6, 8–14 and 20–21 Nov 2024
polls report only presidential vote intention
(<https://www.g4media.ro/sondaj-la-comanda-usr-marcel-ciolacu-conduce-cu-245-urmat-de-george-simion-si-elena-lasconi-cu-19-calin-georgescu-surpriza-de-pe-locul-patru-peste-mircea-geoana-si-nicolae-ciuca.html>,
<https://www.b1tv.ro/politica/sondaj-verifield-lupta-stransa-intre-elena-lasconi-si-george-simion-pentru-a-intra-intr-un-tur-2-cu-marcel-ciolacu-la-prezidentiale-1529584.html>).
curs.ro has no poll post between 7 Nov and 1 Dec 2024; CURS's next
publication is the 1 Dec exit poll. No final-window poll was found for
Avangarde, ARA, Snap Market Research, or the five houses that first appear
in 2025.

**`pres-2025-r1`** (window 2025-04-13 … 05-03)

| Pollster | Fieldwork (gap) | Evidence (latest poll first) |
|---|---|---|
| atlasintel | 1–3 May (1; **published 5 May**, after election day), 28 Apr–1 May (3), 17–22 Apr (12), 10–13 Apr (21) | <https://www.atlasintel.org/poll/romania-national-hotnews-2025-05-05> → <https://cdn.atlasintel.org/47acc363-47bb-498d-becc-a0caabc92b0c.pdf>; <https://hotnews.ro/exclusiv-ultimul-mare-sondaj-inainte-de-primul-tur-al-alegerilor-prezidentiale-2025-de-duminica-lupta-extrem-de-stransa-pentru-finala-prezidentiala-1961609>; <https://hotnews.ro/exclusiv-sondaj-atlasintel-cu-11-zile-inainte-de-alegerile-prezidentiale-george-simion-recupereaza-din-diferenta-fata-de-posibilii-contracandidati-din-turul-2-lupta-in-marja-de-eroare-pentru-al-doi-1954095>; <https://hotnews.ro/sondaj-atlasintel-pentru-hotnews-george-simion-favorit-sa-castige-alegerile-prezidentiale-intr-un-singur-scenariu-crestere-puternica-pentru-crin-antonescu-1947856> |
| sociopol | 28–30 Apr (4), 24–26 Apr (8), 21–23 Apr (11), 14–17 Apr (17) | România TV <https://www.romaniatv.net/ultimul-sondaj-sociopol-inainte-de-vot-simion-si-ponta-intra-in-turul-al-doilea-candidatii-lui-soros-se-prabusesc_8904838.html> (graphic <https://www.romaniatv.net/wp-content/uploads/2025/05/sondaj-sociopol.jpg>); client named in <https://adevarul.ro/alegeri-prezidentiale-2025/sondaje-inainte-de-vot-candidatul-favorit-in-2440126.html>; earlier: <https://www.romaniatv.net/exclusiv-sondaj-sociopol-finala-george-simion-victor-ponta-crin-antonescu-si-nicusor-dan-se-bat-la-locul-3_8899270.html>, <https://www.romaniatv.net/sondaj-sociopol-finala-intre-george-simion-35-si-victor-ponta-22-ce-procente-au-crin-antonescu-si-nicusor-dan_8890711.html> |
| ara | 23–28 Apr (6), 21–25 Apr (9), 15–19 Apr (15), 9–13 Apr (21) | 23–28 Apr: Antena 3 broadcast (Facebook video, per RO Wikipedia); 21–25 Apr: <https://cugetliber.ro/upload/static/sondaj-prezident-1745830970.pdf> (pollster not named in it); 15–19 Apr: <https://www.libertatea.ro/stiri/sondaj-ara-george-simion-crin-antonescu-nicusor-dan-alegeri-prezidentiale-2025-5281629>; 9–13 Apr: <https://www.antena3.ro/politica/sondaj-george-simion-si-crin-antonescu-la-doar-jumatate-de-procent-distanta-inaintea-alegerilor-prezidentiale-742935.html> |
| noi-cetatenii | 24–30 Apr (4) | <https://docs.google.com/spreadsheets/d/e/2PACX-1vRTH-eC8N9hQFYKdoEzvOT5J60ZWRqLIM-A95tWf2W4IZ8gAx8VvSep0ByTsKA0cHUxn5jkvc911GBF/pubhtml?gid=244820692&single=true> |
| mkor | 24–27 Apr (7) | <https://mkor.ro/studii/romania-electorala-mai-2025/> |
| flashdata | 24–26 Apr (8) | <https://agerpres.ro/social/2025/04/28/prezidentiale2025-sondaj-flashdata-george-simion---29-crin-antonescu---26-nicusor-dan---23--1443786> |
| dataecho | 22–24 Apr (10) | <http://web.archive.org/web/20250430235238/https://results.dataecho.ro/22-24_aprilie.pdf> |
| irsop | 4–14 Apr (20) | <https://hotnews.ro/cel-mai-recent-sondaj-irsop-ii-da-ca-finalisti-la-alegerile-prezidentiale-pe-george-simion-si-nicusor-dan-1949270> |

Nearest outside: CURS 3–10 Apr (gap 24,
<https://curs.ro/sondaj-de-opinie-la-nivel-national-aprilie-2025/>, report
<https://curs.ro/wp-content/uploads/2025/04/Omnibus-aprilie-2025.pdf>); curs.ro
has no other post before the 4 May exit poll. Verifield 24–28 Mar (gap 37,
<https://www.libertatea.ro/stiri/sondaj-verifield-alegeri-prezidentiale-2025-la-comanda-lui-nicusor-dan-george-simion-favorit-5252884>).
Avangarde 19–23 Mar (gap 42,
<https://www.libertatea.ro/stiri/sondaj-avangarde-george-simion-crin-antonescu-nicusor-dan-alegeri-prezidentiale-2025-5244880>).
INSCOP published no pre-election vote intention for 2025 (its April–May 2025
posts are an attitudes survey, an election-day survey, and exit-poll
comparisons).

**`pres-2025-r2`** (fieldwork after 2025-05-04, ending by 2025-05-17)

| Pollster | Fieldwork (gap) | n | Evidence |
|---|---|---|---|
| atlasintel | 13–15 May (3); 9–12 May (6) | 5,628; 3,995 | <https://atlasintel.org/poll/romania-national-15-05-2025> → <https://cdn.atlasintel.org/bd21857c-f16e-4be6-96cf-67d5c41ebf78.pdf>; <https://atlasintel.org/poll/romania-national-13-05-2025> → <https://cdn.atlasintel.org/16c3663d-7712-4a7f-8353-64b38a0f8857.pdf>; HotNews <https://hotnews.ro/exclusiv-ultimul-mare-sondaj-inainte-de-turul-doi-al-alegerilor-prezidentiale-de-duminica-18-mai-avans-foarte-mic-pentru-unul-dintre-candidati-in-marja-de-eroare-suspansul-continua-1976328> |
| noi-cetatenii | 11–15 May (3) | 1,460 | <https://docs.google.com/spreadsheets/d/e/2PACX-1vS37t4Ob9IQo3aWrI3QFUuM2lz3tSpBV5UHdM7ZjSNaPn8nr9kBwrT-toASpxqGvQfBxrT0AsNfJX-x/pubhtml?gid=244820692&single=true> |
| mkor | 8–14 May (4) | 3,357 | <https://mkor.ro/studii/sondaj-prezidentiale-tur-2/> |
| irsop | 10–13 May (5) | 951 | <https://hotnews.ro/primul-sondaj-in-care-nicusor-dan-conduce-in-fata-lui-george-simion-care-este-avansul-potrivit-irsop-1975212> |
| sociopol | 10–12 May (6) | 1,024 | <https://www.romaniatv.net/exclusiv-mirel-palada-director-sociopol-cursa-dintre-nicusor-dan-si-george-simion-e-din-ce-in-ce-mai-stransa_8926885.html> (dates, n, client stated verbally on air); <https://www.romaniatv.net/mirel-palada-director-sociopol-in-momentul-de-fata-avem-george-simion-53-nicusor-dan-47_8923399.html> |
| curs | 8–11 May (7) | 3,042 | TVR Info <https://tvrinfo.ro/noul-sondaj-curs-george-simion-52-nicusor-dan-48-inaintea-turului-doi-al-alegerilor-prezidentiale/> (CURS slides as PNG); not posted on curs.ro |
| verifield | 6 May (12) | 944 | <https://hotnews.ro/wp-content/uploads/2025/05/Raport-ND13-6-Mai-Val-1.pdf> |

ARA, Avangarde, CURS and Sociopol also published round-2 exit polls; INSCOP
published an election-day survey. These are out of scope (R-81).

### 3.2 Polls in the 120-day windows (approximate)

Counts merge the indexes and this check's findings; they are for sizing the
collection work, not data. Same-survey scenarios count once.

| Pollster | parl | r1 | r2 | Notes |
|---|---|---|---|---|
| atlasintel | 1 | 6 | 2 | r1: 21–24 Feb, 13–15 Mar, 10–13 Apr, 17–22 Apr, 28 Apr–1 May, 1–3 May. |
| sociopol | 1 (+1 undated) | 12 | 1 | parl: the 20–22 Nov article also quotes an earlier "penultimate" party ranking without dates. r1: two March entries (17–18 and 17–21 Mar) may be one survey. |
| curs | 3 | 3 | 1 | parl: 13–27 Aug, 11–16 Oct, 30 Oct–5 Nov. |
| verifield | 1–2 | 2 | 1 | parl: Aug 2024 (no exact dates), 7–9 Oct. |
| inscop | 3 | 0 | 0 | parl: 11–16 Sep, 11–18 Oct, 7–12 Nov. |
| bcs | 3 | 0 | 0 | 26–29 Sep and 7–10 Nov are on the own site only, not in the indexes. |
| cira | 2 | 0 | 0 | 24–30 Aug (B1TV), 9–13 Nov. |
| ara | 0 | 5 | 0 | 21–25 Apr is attributed to ARA by the indexes only. |
| flashdata | 0 | 4 | 0 | |
| mkor | 0 | 3 | 1 | |
| noi-cetatenii | 0 | 3 | 1 | |
| dataecho | 0 | 2 | 0 | |
| irsop | 0 | 1 | 1 | |
| avangarde | 0 | 2 | 0 | |
| snap-market-research | 0 | 0 | 0 | Its 2024 poll (3–8 Jan) is outside every window. |

---

## 4. Criteria 2–5 per pollster

Transparency letters as in §1.3: n, D, M, Q, W, E, S.

### atlasintel
- **Coverage:** ✓ / ✓ / ✓ (§3.1).
- **Topline: Full.** Each report has a "[Toți alegătorii]" page (all
  respondents, incl. "Vot nul / alb" and "Nu știu") and a "[Voturi valide]"
  page. Parl 26–28 Nov: 17 parties/options + null/blank 0.5% + don't know
  3.3% (report p. 4); r1 28 Apr–1 May: 8 candidates + other + "Nu știu" +
  "Vot nul / Nu votez" (HotNews slide); r2 13–15 May: Dan, Simion, null/blank
  1.8%, don't know 1.7% (report p. 4). HotNews's parliamentary chart shows
  only the valid-vote base.
- **Transparency:** parl 5/7 (n, D, M, E, S; no question text on the
  parliamentary page; weighting only as a generic "calibration" statement in
  the firm's boilerplate); r1 and r2 6/7 (question text shown; no
  poll-specific weighting description). Mode: "Recrutare digitală aleatorie
  (Atlas RDR)", online questionnaire. Client: "Sondaj Atlas-HotNews" in the
  report footers.
- **Access:** own site (one page per poll, linking a PDF on
  cdn.atlasintel.org) + HotNews articles with chart images. The PDFs have a
  **text layer for titles, methodology and questions, but the values are
  inside chart images** → manual double-entry (or OCR). The Web Archive has the
  PDFs checked. The own page for the 28 Apr–1 May poll was not located
  (HotNews carries its slides).
- **Popularity: High.** HotNews partner for most polls; republished by other
  outlets (e.g. Euronews România, Realitatea, G4Media).
- **Notes for the data task:** (1) the 1–3 May 2025 poll was published on
  5 May, after round 1 (R-83 warning; see the ADR's open questions); (2) the
  MoE differs between sources for the parliamentary poll (report ±2 pp,
  HotNews ±3%); DATA_MODEL §6.11 says to use the pollster's report; (3)
  universe "Electoratul din România"; HotNews and Euronews state that the
  round-2 figures include the diaspora → `target_scope` must be decided per
  poll (M-1.4).

### sociopol
- **Coverage:** ✓ / ✓ / ✓ (parl found outside the indexes).
- **Topline: Expressed.** Parl 20–22 Nov: PSD, AUR, PNL, USR, SOS, UDMR +
  "Alții 11%" = 100 on the broadcast graphic; no undecided. r1 28–30 Apr: five
  candidates + "Alți candidați – sub 1%" (a `lt` value, OI-2). r2 10–12 May:
  Simion 53 / Dan 47, stated verbally on air. **Inconsistency:** for the
  parliamentary poll the article text gives USR 15% while the broadcast graphic
  shows 13%.
- **Transparency:** parl 5/7 (n, D, CATI, Q on the graphic, E; client not
  stated for this poll); r1 6/7 (n, D, CATI, Q, E, S = România TV); r2 3/7
  (n, D, S, from the director's statement on air; no mode, question, MoE, or
  weighting). No weighting description was found for any poll.
- **Access:** **media only.** No own website (registry). Originals are
  România TV articles (HTML), broadcast screenshots (JPG), and live
  statements reported in articles. The Web Archive has the three articles and
  the parliamentary graphic.
- **Popularity: High** (the most frequent house in r1, with 12 polls;
  broadcast by România TV; republished by Adevărul, Tomis News and others).

### curs
- **Coverage:** ✗ / ✗ / ✓. The latest parl poll ends 26 days before the
  election and the latest r1 poll 24 days before; both are inside the 120-day
  windows.
- **Topline: Expressed.** Vote intention among "VOTAT" respondents, incl.
  "Altul"; no undecided share on the vote-intention slide (other questions
  show NS/NR). r2: two candidates (52 / 48).
- **Transparency: 6/7** for all three polls checked (n, D, M, Q, W = weighted
  by age in Nov 2024 and Apr 2025, by round-1 vote in May 2025, E). No client
  or self-funding statement in the reports (sondajeromania.ro: "beneficiar
  nedeclarat"; RO Wikipedia: "autofinanțat", unsourced).
- **Access:** own site posts (HTML with slide PNGs) + **text PDF**
  presentations (PowerPoint exports) on curs.ro. The r2 poll is **not on
  curs.ro**; TVR Info carries its slides (PNG). Mode changes: face-to-face
  (Oct–Nov 2024 report), CATI (Oct 2024, Apr and May 2025). The Nov 2024 PDF
  had no Web Archive snapshot on 2026-11-22.
- **Popularity: High** (ProTV, TVR, Digi24, Romania Insider and others).

### verifield
- **Coverage:** ✗ / ✗ / ✓ (parl 7–9 Oct, gap 53; r1 24–28 Mar, gap 37; r2
  6 May).
- **Topline: Full (r2).** Total-sample base with "Anulez votul",
  "Nu știu / Nu m-am hotărât", "Nu m-aș duce la vot", "NR", plus two
  expressed bases.
- **Transparency:** r2 5/7 (n, D = a single day, CATI, Q, E; no weighting;
  no client in the PDF; media state that Nicușor Dan presented it). Media
  reports of the earlier polls name the clients (USR; the teams of Crin
  Antonescu and Nicușor Dan; see the registry affiliations).
- **Access:** r2 = **text PDF hosted by HotNews**; the others = media articles
  (Digi24, Libertatea, G4Media, B1TV) and client Facebook posts. The own site
  shows only a title page.
- **Popularity: Medium.**

### mkor
- **Coverage:** ✗ (no 2024 parliamentary poll) / ✓ / ✓.
- **Topline: Full** (r2: Dan 34.2, Simion 32.0, "Nu știu / Indeciși" 4.5,
  refuse 12.6, won't vote / will spoil 6.8; plus redistributed and modelled
  figures; r1 publishes an "exclus NS-NR" list and states the undecided share).
- **Transparency: 7/7** (CAWI own panel; weighting by gender, age, residence,
  education, round-1 vote; MoE; question; self-funding statement).
- **Access:** own-site **HTML** report with PNG charts; a full report download
  is offered.
- **Popularity: Medium** (HotNews, Romania Insider).

### irsop
- **Coverage:** ✗ (no 2024 parliamentary poll) / ✓ (4–14 Apr, gap 20) / ✓.
- **Topline: Expressed** (r1 table: five candidates + "Alții" = 100; r2:
  52 / 48 "among likely voters").
- **Transparency:** r1 6/7, r2 5/7 (n, D, telephone, E, S = self-funded; the
  question is on the r1 table; no weighting).
- **Access:** press-release **images** (PNG) embedded in HotNews; the own site
  has no poll reports.
- **Popularity: Medium** (HotNews).

### noi-cetatenii
- **Coverage:** ✗ (no 2024 parliamentary poll) / ✓ / ✓.
- **Topline: not verified.** The published Google Sheets show methodology
  and question text in cells, but the vote shares are in embedded charts; the
  CSV export contains no shares.
- **Transparency: 6/7** (n, D, Q, weighting stated as "ponderate" /
  "echilibrare statistică", E, self-funded; the mode is "recrutare digitală
  extinsă", with the interview channel not named).
- **Access:** **Google Sheets** (pubhtml; charts). Universe "Electoratul din
  România și Diaspora" → `target_scope = total`.
- **Popularity: Low** (Adevărul roundup; Wikipedia).

### inscop
- **Coverage:** ✓ / ✗ / ✗ (no 2025 pre-election vote intention).
- **Topline: Expressed, two bases** (voters choosing a party, N = 898; and
  those also certain to vote, N = 639), incl. "Independent" and "Altul"; the
  share choosing no party is given only in the base description (81.7%).
- **Transparency: 6/7** (n, D, CATI, Q, E, S = Libertatea; no weighting
  description).
- **Access:** own-site **text PDF** + own-site HTML press list.
- **Popularity: High** (Libertatea partner; inscop.ro lists 10 outlets that
  covered the November poll on the day of release).

### ara
- **Coverage:** ✗ (no 2024 poll in window) / ✓ / ✗ (round-2 exit poll only).
- **Topline: Expressed** (21–25 Apr PDF: six candidates + "Alții", with a
  footnote that 21% do not want to vote and 19% of likely voters are undecided).
- **Transparency: 5/7** (n, D, CATI/RDD, E, S = Antena 3 CNN or Cuget Liber;
  question and weighting not shown in the sources read).
- **Access:** Antena 3 CNN articles and a broadcast video (Facebook);
  Libertatea; a text PDF published by Cuget Liber that does not name the
  pollster.
- **Popularity: Medium.**

### bcs
- **Coverage:** ✓ (7–10 Nov, gap exactly 21) / ✗ / ✗.
- **Topline: Full** (parties + "Alt partid" + "Absenteiști și nehotărâți 26.7%").
- **Transparency: 7/7** (weighting by education; client Newsweek on the own
  page). The trend chart labels the wave "7-11 noiembrie" while the title says
  7–10.
- **Access:** own-site **text PDF**. **Popularity: Medium** (the own page lists
  12 outlets citing the November poll).

### cira
- **Coverage:** ✓ / ✗ / ✗. **Topline: Partial** (six parties, 89% in total).
- **Transparency: 6/7** (no weighting). **Access:** Newsweek article only
  (HTML); cira.ro shows no political poll reports. **Popularity: Low.**

### flashdata
- **Coverage:** ✗ / ✓ (24–26 Apr) / ✗ (only pre-round-1 head-to-heads).
- **Topline: Full** (undecided 2%, don't know / no answer 1%).
- **Transparency: 6/7** (online questionnaire, weighting by gender and age;
  no client statement). **Access:** Agerpres article (HTML).
  **Popularity: Medium.**

### dataecho
- **Coverage:** ✗ / ✓ (22–24 Apr) / ✗. **Topline:** not verified (values in
  images). **Transparency: 3–4/7** (D, E, mode only as "recrutare digitală
  aleatorie"; "Respondenți 2,607" vs "Eșantion 1,200" is ambiguous).
  **Access:** Google-Slides **image PDF**; results.dataecho.ro offline, Web
  Archive copy. **Popularity: Low.**

### avangarde
- **Coverage:** ✗ / ✗ (19–23 Mar, gap 42) / ✗ (exit poll only).
- **Transparency** of the March 2025 report: 6–7/7 (n, D, CATI, weighting by
  gender and education, E; self-funded per Libertatea; the vote question page
  was not checked). **Access:** text PDF hosted by Libertatea; the own site
  lists older reports. **Popularity: Medium.**

### snap-market-research
- No poll in any MVP 120-day window. Not assessed further.
  **Access:** press release (Oficiul de Știri). **Popularity: Low.**

---

## 5. Publication formats per house (for T-011)

| Pollster | Formats found | Extraction path needed |
|---|---|---|
| atlasintel | Own-site PDF (cdn.atlasintel.org): text for titles/method/question, **values in chart images**; HotNews HTML with chart JPG/PNG (incl. WhatsApp images) | `manual_double_entry` from rendered PDF pages (needs page rendering); optional OCR |
| sociopol | Media HTML (România TV) with numbers in text; broadcast screenshots (JPG); verbal statements reported in HTML | `html` for text values; `manual_double_entry` from images |
| curs | Own-site HTML posts with slide PNGs; **text PDF** (PowerPoint export); media HTML + PNG slides (r2) | `pdf_text`; `manual_double_entry` from PNG |
| verifield | **Text PDF** hosted by media (r2); media HTML; client Facebook posts | `pdf_text`; `html` |
| mkor | Own-site **HTML** with PNG charts; full report download | `html`; `manual_double_entry` from PNG |
| irsop | PNG press-release slides inside media HTML | `manual_double_entry` (image) |
| noi-cetatenii | **Google Sheets** pubhtml; values in embedded charts (not in CSV cells) | Sheet snapshot + `manual_double_entry` from charts |
| inscop | Own-site **text PDF** + HTML | `pdf_text` |
| ara | Media HTML; broadcast video; text PDF via a client (pollster unnamed) | `html`; `pdf_text`; video frames would need a new `format` value or `other` |
| bcs | Own-site **text PDF** (embedded viewer) + HTML abstract | `pdf_text` |
| cira | Media HTML | `html` |
| flashdata | Media HTML | `html` |
| dataecho | Image PDF (Web Archive) | `manual_double_entry` |
| avangarde | Text PDF hosted by media; media HTML | `pdf_text`; `html` |
| snap-market-research | Press-release HTML | `html` |

Summary for T-011: `pdf_text`, `html`, and **manual double entry from images
and rendered PDF pages** are all required for any MVP selection that includes
AtlasIntel or Sociopol. Google Sheets charts and broadcast video appear only
with houses that are not proposed.

---

## 6. Criterion 6: diversity of the set

Described factually; no inference about intent (ADR-0003).

| Pollster | Mode(s) in the MVP elections | Client profile in the MVP elections (as published) | Population note |
|---|---|---|---|
| atlasintel | Online questionnaire after random digital recruitment | Online news outlet (HotNews); one poll published by a candidate (registry) | Universe "Electoratul din România"; round-2 figures reported as including the diaspora |
| sociopol | CATI | TV station (România TV) | Resident adults (as stated for its Nov 2024 poll) |
| curs | Face-to-face (late 2024), CATI (Oct 2024, 2025) | No client stated | Resident adults |
| verifield | CATI | A party and two candidates' teams (USR; Crin Antonescu, Nicușor Dan; registry) | Not stated beyond "representative" |
| mkor | CAWI, own panel | Self-funded | Residents; diaspora excluded |
| irsop | Telephone | Self-funded | Residents 18+ |
| noi-cetatenii | Digital recruitment, channel not stated | Self-funded civic NGO | Residents + diaspora |
| inscop | CATI | Daily newspaper (Libertatea); think tank (ILD) | Residents |

The proposed set AtlasIntel + Sociopol + CURS (see the draft ADR) spans three
collection modes (online, telephone, face-to-face/telephone) and three client
situations (online outlet, TV station, no client stated). The reserves add a
party/candidate-client profile (Verifield) and a self-funded online panel
(MKOR).

---

## 7. Other findings for the data tasks

- **Polls missing from the discovery indexes:** Sociopol 20–22 Nov 2024
  (parliamentary); BCS 26–29 Sep and 7–10 Nov 2024; AtlasIntel 1–3 May 2025
  (listed only in RO Wikipedia's trust table). The data tasks must search
  beyond the indexes (own sites, client outlets).
- **Source disagreements:** AtlasIntel parl MoE (±2 pp report vs ±3% HotNews);
  Sociopol parl USR (15% text vs 13% graphic); BCS wave dates (7–10 vs 7–11
  Nov); DataEcho sample size (2,607 vs 1,200).
- **Publication after election day:** AtlasIntel's 1–3 May 2025 poll was
  published on 5 May. R-81 allows it; R-83 warns. Whether such a poll can be a
  house's "final poll" (M-1.3) is a methodology question (ADR open question).
- **Diaspora:** AtlasIntel (round 2, per media) and Noi, Cetățenii include the
  diaspora (M-1.4 `target_scope`).

## 8. Limitations

- Counts are approximate (§3.2). Gap searches covered every registered house
  but cannot prove that no other poll exists.
- Transparency was read from the sources opened; the data tasks may find an
  item in a document not opened here (§6.11 says to use the pollster's report).
- Popularity is a qualitative indicator, not a citation count.
- Exit polls and election-day surveys were not scored (out of scope, R-81).
