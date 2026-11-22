# Storyboard

**Task:** T-031 · **Status:** concept, for owner review · **Related:** ADR-0003,
ADR-0007, ADR-0008, ADR-0009, [visual-language.md](visual-language.md),
[design-references.md](design-references.md)

For each key screen: the single question it answers for a non-expert, an
example headline in plain Romanian, what is visible at first glance versus on
click (progressive disclosure), and how the screen looks when certainty is low
or data is missing. Mock-ups are in [`mockups/`](mockups/index.html) (open
`index.html` in a browser; light mode; fictitious data).

All names and numbers are **fictitious** ("Institutul Alfa", "Beta Research",
"Gamma Data", "Delta Opinion", "Partidul A–E", "Alegerea 1–3"). The Romanian
copy is a first draft for tone; the final wording belongs to T-051.

## 0. The reader and the journey

**Reader:** someone who sees a poll in the news and wonders whether to believe
it. They know what a poll is, not what a house effect is. Most arrive on a
phone, from a link to one pollster or one election.

**Disclosure layers, the same on every screen:**

| Layer | What it contains | Where |
|---|---|---|
| 1. Answer | The question, the serif headline finding (magnitude + direction), the grade if any | Always visible |
| 2. Picture | One chart with its legend and a one-line caption | Always visible |
| 3. Reading help | "Cum citesc…?" disclosure | One click |
| 4. Details | Per-election breakdown, score components, patterns | One click |
| 5. Evidence | "Datele": polls used, sources, archived reports, CSV | One click |
| 6. Method | "Detalii tehnice" with formula and M-IDs → "Cum măsurăm" | One click / link |
| Always | "Ce nu spunem" box and, while the MVP lasts, "Rezultate preliminare" | Visible near the bottom of the first view |

**Typical journey (storyboard frames):**

1. A reader follows a link to **Clasament** and sees that nobody stands out
   yet and that results are preliminary.
2. They tap **Institutul Alfa** and land on its **card**: one sentence says
   Alfa overestimated Partidul A in all 3 elections by about 3 p.p.
3. They open "Cum citesc graficul?" and understand the bar is measured
   against the other pollsters.
4. Curious whether this is a one-off, they open **Alegerea 1 în detaliu**
   (target plot) and see that *everyone* missed Partidul B, but only Alfa was
   far off on Partidul A.
5. They check the **campaign timeline** to see whether Alfa was off all
   campaign or only at the end.
6. Finally, **Cum măsurăm** explains, with one example per idea, why the
   comparison is fair and what it does not say.

Entry points are the leaderboard, a pollster card (shared links), and an
election page. A home page is out of scope here; if added, it leads with 2–3
findings and the leaderboard, never with a feed of the latest polls (ADR-0009).

---

## 1. Leaderboard ("Clasament")

Mock-up: [leaderboard.html](mockups/leaderboard.html) · Methodology: M-5,
M-2.6, M-5.3

**Question:** *Pe care institute mă pot baza mai mult și pe care mai puțin?*
(Which pollsters can I rely on more, and which less?)

**Headline example:**
> Deocamdată, niciun institut nu iese clar în față. Institutul Alfa și Gamma
> Data au nota C, Beta Research nota D, iar Delta Opinion nu are încă destule
> date. Cu doar 3 alegeri analizate, notele sunt provizorii.

**First view:** the headline, the "Rezultate preliminare" callout (it also
says the highest grade possible today is B), and a table **grouped by grade**:
grade badge with certainty, the largest deviation (party chip + signed value,
or "≈ … neclar"), average error, elections covered, transparency, patterns.
Inside a grade group the order is alphabetical; there are no ranks 1, 2, 3.

**On click:** "Ce înseamnă notele?" (five components, the A–F scale, A shown
hatched as unreachable for now), "De ce nu există locul 1, locul 2…?", "Ce
înseamnă certitudine scăzută?"; each row opens the pollster card; the
"apropiere la final" tag opens the timeline.

**Low certainty:** the row keeps its grade but with the dashed badge,
"provizorie", and one certainty dot (Gamma Data). Its largest deviation is
shown as "≈ +2,2 p.p. · neclar" if the interval includes zero.

**Insufficient data:** the pollster goes into a separate **"Fără notă încă"**
group at the bottom, with a hatched badge and the reason in words ("un singur
sondaj final, la o singură alegere"). It is never ranked last.

**Mobile:** each row becomes a compact card (name, badge, largest deviation);
the other columns move behind "detalii".

---

## 2. Pollster card ("Fișa institutului")

Mock-up: [pollster-card.html](mockups/pollster-card.html) · Methodology:
M-2.5, M-2.6, M-3.3, M-3.4, M-4, M-5

**Question:** *Cât mă pot baza pe sondajele acestui institut și în ce direcție
se abat?* (How far can I rely on this pollster's polls, and which way do they
lean?)

**Headline example:**
> Institutul Alfa a supraestimat Partidul A în toate cele 3 alegeri
> analizate: în medie cu 3,1 puncte procentuale mai mult decât celelalte
> institute.
>
> *Interval probabil: între +1,2 și +4,8 p.p. · La celelalte partide,
> abaterile sunt mici și nu se pot deosebi de zero.*

**First view:** headline + grade badge (letter, certainty dots and word,
number of elections); **one diverging bar chart**, one row per party (left =
underestimates, right = overestimates, whisker = 90% interval, hollow bar when
the interval includes zero); a stat strip (polls analysed, elections, average
error vs. the average of all pollsters, transparency x/7, campaign patterns);
"Ce nu spunem" and "Rezultate preliminare".

**On click:** "Cum citesc graficul?" (why we compare with the other pollsters);
"Pe fiecare alegere" (table: final poll timing, error, the deviation for the
headline party per election); "Cum s-a calculat nota" (five components,
weights, raw → shrunk score); "Date și metodă" (CSV, M-IDs); the pollster's
right-of-reply link in the footer.

**Low certainty** (Gamma Data, 2 elections): dashed card and badge, "Nota C
(provizorie)", a hedged headline ("pare să fi supraestimat … dar datele nu
sunt încă suficiente pentru o concluzie"), only the largest deviation shown,
with a dashed whisker that runs off the chart, and a callout "De ce
certitudine scăzută?".

**Insufficient data** (Delta Opinion, 1 election): no letter (hatched "–"
tile, "Fără notă încă"), no bars. A callout says what is missing and adds that
having no final poll is not an error by the pollster. A per-election strip
shows "fără sondaj final" / "1 sondaj final".

---

## 3. House × party heatmap ("Harta abaterilor")

Mock-up: [heatmap.html](mockups/heatmap.html) · Methodology: M-2.5 (final
polls), M-3.2 (whole campaign), M-4

**Question:** *Care institut dă sistematic mai mult sau mai puțin unui anumit
partid decât celelalte institute?* (Which pollster systematically gives a
particular party more or less than the others do?)

**Headline example:**
> Trei abateri ies clar în evidență: Institutul Alfa supraestimează Partidul A
> (+3,1 p.p.), iar Beta Research supraestimează Partidul B (+2,4 p.p.) și
> subestimează Partidul C (−2,9 p.p.). Celelalte diferențe sunt prea mici
> pentru a fi sigure.

**First view:** pollsters as rows, parties as columns. **Colour only where the
interval excludes zero**; all other cells are white with "≈" and a muted value,
so the eye lands on the clear findings. Each cell shows its interval in small
type. A segmented control switches "Sondajele finale" / "Toată campania". The
side panel shows the selected cell (by default the strongest finding).

**On click:** a cell fills the side panel (desktop) or a bottom sheet
(mobile): one sentence, a mini chart with the deviation per election and the
mean, links to the pollster card and the election. Disclosures: "Cum citesc
harta?", "De ce comparăm cu celelalte institute și nu cu rezultatul?",
"Toată campania față de Sondajele finale".

**Low certainty:** the whole row has dashed cell outlines and the row label
says "2 alegeri · certitudine scăzută". With wide intervals, such cells are
almost always "≈".

**Insufficient data:** one hatched cell spanning the row, with the reason in
words, no numbers. A "Puține institute, puține alegeri" callout explains that
the reference ("media institutelor") is built from only 4 pollsters (I-013).

---

## 4. Per-election target plot ("O alegere în detaliu")

Mock-up: [target-plot.html](mockups/target-plot.html) · Methodology: M-1.3,
M-2.1, M-2.2, M-2.5, M-4.1

**Question:** *La această alegere, cât de aproape au fost ultimele sondaje de
rezultat și au greșit toate în aceeași direcție?* (At this election, how close
were the final polls to the result, and did they all miss the same way?)

**Headline example:**
> Toate institutele au subestimat Partidul B, în medie cu 3,0 p.p.: o
> greșeală comună. Separat, Institutul Alfa a supraestimat Partidul A cu
> 4,2 p.p., mult peste media institutelor (+1,5).

**First view:** an election switcher; one row per party with its official
result in words ("rezultat: 32,0%"); the centre line is the result; grey
bands at ±1, ±3, ±5 p.p. form a 1-D "target"; each pollster's final poll is a
shape (circle, square, triangle) with its margin of error; a thick grey tick
shows the average of all pollsters. A side panel lists each pollster's average
error, and a "Greșeala comună" callout explains the shared miss.

**On click:** hovering a shape highlights that pollster in every row;
"Cum citesc ținta?", "Ce înseamnă semn gol?", "Datele: sondajele finale
folosite" (fieldwork end, sample, archived source).

**Low certainty:** a single poll cannot carry certainty levels; instead, a
**hollow shape** means the error is within that poll's margin of error. The
"Ce nu spunem" box says that conclusions about a pollster come only from
several elections (link to the heatmap).

**Insufficient data:** a pollster without a poll in the last 21 days is not
plotted; it appears in the side table as "fără sondaj final" and in the data
table with the date of its last poll ("cu 34 de zile înainte, în afara
ferestrei"). If fewer than 2 pollsters have a final poll, the industry-mean
tick and the "greșeală comună" callout are hidden and replaced by a callout
saying that a comparison is not possible.

---

## 5. Campaign timeline ("Campania")

Mock-up: [timeline.html](mockups/timeline.html) · Methodology: M-3.1, M-3.2,
M-3.3, M-3.4

**Question:** *A arătat acest institut altceva decât celelalte în timpul
campaniei, nu doar în ultima săptămână?* (Did this pollster show something
different from the others during the campaign, not just in the last week?)

**Headline example (convergence pattern):**
> Timp de trei luni, Beta Research a arătat Partidul A cu aproximativ 4 p.p.
> peste celelalte institute. În ultimele 3 săptămâni, cifrele sale s-au
> apropiat de ale celorlalte și de rezultat.

**First view:** selectors (pollster, party, election); one chart over 120
days: the pollster's polls (ink dots + line), the average of the *other*
pollsters (grey line + band), the result (ink tick at election day), the gap
tinted blue (above) or orange (below), the final 21-day window as a warm band.
A pattern tag ("apropiere de celelalte institute la final") and a stat strip
(whole campaign, first 3 months, last 21 days, number of polls).

**On click:** "Ce înseamnă apropiere la final?" (open by default when the flag
is raised: the rule in words and the alternative explanations); "Cum se
calculează media celorlalte institute?"; "Datele: cele 8 sondaje".

**Low certainty / few polls:** with fewer than 3 polls in the window the chart
shows dots only, with no line, no gap tint, and no campaign metric, plus a
sentence saying so (Delta Opinion example). Herding ("sondaje neobișnuit de
stabile") is never shown below 5 polls (M-3.4).

**Insufficient data (thin market):** when fewer than 2 other pollsters
published in a period, the grey band widens; proposed: hatch that period and
say "Media celorlalte institute e nesigură aici".

---

## 6. How we measure this ("Cum măsurăm")

Mock-up: [methodology.html](mockups/methodology.html) · Methodology: plain
version of M-1 to M-5

**Question:** *De unde vin cifrele de pe acest site și cât de mult mă pot baza
pe ele?* (Where do the numbers come from, and how much can I rely on them?)

**Headline example:**
> Comparăm ce au spus sondajele cu ce au votat oamenii. Apoi separăm
> greșelile pe care le-au făcut toate institutele de cele care țin de un
> singur institut și spunem de fiecare dată cât de siguri suntem.

**First view:** a table of contents (sticky on desktop) and seven short
sections, each answering one reader question: how far off was the poll; why
we compare with the other pollsters; what we track during the campaign; how
sure we are; how the grade is computed; what we do not claim; data and
sources. Each section = one plain paragraph + **one worked example with one
small diagram** (34% vs. 32% → +2 p.p.; −3,5 = −3,0 shared + −0,5 own; the
convergence shape; solid vs. hollow vs. hatched; shrinkage 64 → 54/57/60).

**On click:** "Ce facem cu cei nehotărâți?" (normalisation with an example),
"Detalii tehnice" in every section (formula, parameters, M-IDs), a link to the
full English METHODOLOGY.md, and the CSV download. Every "Mai multe" link on
other screens points to an anchor here (`#comparatie`, `#sigur`, `#nota`).

**Low certainty / insufficient data:** this page *defines* the states. The
"Cât de siguri suntem?" section shows the three visuals (solid, hollow,
hatched) and a table of certainty levels with how each looks on the site.

---

## 7. States at a glance

| State | Leaderboard | Card | Heatmap | Target plot | Timeline |
|---|---|---|---|---|---|
| Not distinguishable from zero | "≈ … neclar" | hollow bar, "≈" | white cell, "≈" | hollow shape | — (gap shown, metric with interval) |
| Low certainty (N < 3) | dashed badge, "provizorie" | dashed card, hedged headline | dashed cell outlines | n/a (single polls) | — |
| Insufficient data | "Fără notă încă" group | hatched badge, callout | hatched row | not plotted, "fără sondaj final" | dots only |
| Preliminary (MVP) | callout at top | callout | callout | — | — |
| Thin market | — | — | callout | mean hidden if < 2 houses | wider band, hatched period |

## 8. Open UX questions for the owner

1. **Grades while N ≤ 3.** With `N0 = 3` (M-5.2), no pollster can score above
   75 in the MVP, so A is unreachable and most grades cluster at C/D. Show
   letter grades during the MVP anyway (as mocked, with "provizorie" and a
   hatched A), or show only the findings and certainty until more elections
   are added?
2. **When is a pollster "not rated"?** Proposed: a grade needs final polls in
   at least 2 elections. M-5.2 alone would still compute a heavily shrunk
   score for N = 1.
3. **Headline by default: the strongest finding or a balanced summary?** The
   card leads with the largest clear deviation. That is the most informative
   choice, but it puts one party's name in the first line for every pollster
   with a finding. The alternative is a neutral summary first ("abateri mici
   la 4 din 5 partide; o abatere clară: …").
4. **Final polls vs. whole campaign as the default heatmap view.** Final polls
   are easier to explain; the whole campaign is closer to what readers
   actually saw.
5. **Working name.** The mock-ups use the repository name "Sondaje la control"
   as a placeholder brand (Q1 in PLAN.md).
