# Visual language

**Task:** T-031 · **Status:** concept, for owner review · **Related:** ADR-0003,
ADR-0008, ADR-0009, [design-references.md](design-references.md),
[storyboard.md](storyboard.md)

A small design system for the prototype (T-030) and the public site (T-052).
It has two parts: **tokens** (CSS custom properties in
[`mockups/tokens.css`](mockups/tokens.css)) and a **component inventory**
(styles in [`mockups/components.css`](mockups/components.css), specimen in
[`mockups/components.html`](mockups/components.html)). Every mock-up uses
these two files and nothing else.

**Light mode is the primary theme** (ADR-0009). Everything is designed and
reviewed in light mode. Dark mode is an optional mapping of the same tokens
(§9); it is not a launch requirement and there are no dark mock-ups.

## 1. Principles

1. **Calm and credible, not a template.** A cool off-white page, white cards,
   hairline rules, generous spacing. No gradients, glass effects, glow, emoji,
   or decorative icons. Credibility comes from restraint and precise numbers.
2. **Colour is reserved for data.** The UI chrome is ink and greys. Links are
   ink with an underline; the active navigation item is ink with an underline.
   The only UI colours outside data are the focus ring and the yellow notice
   (fictitious data, preliminary results).
3. **Answer first.** The serif headline finding is the most prominent text on
   every screen. Charts support it; they don't replace it.
4. **Uncertainty is drawn, not footnoted.** Every number that has an interval
   shows it, and every data state (§6) has its own visual.
5. **Never by colour alone.** Direction is always also given by a sign, a
   position, and a word. Pollsters are told apart by shape and label.

## 2. Tokens

All values live in `tokens.css`. Components reference tokens only, never raw
hex values.

### 2.1 Colour: neutral UI

| Token | Value | Use | Contrast (on surface / on bg) |
|---|---|---|---|
| `--color-bg` | `#f4f5f7` | Page background | — |
| `--color-surface` | `#ffffff` | Cards, tables, charts | — |
| `--color-surface-sunken` | `#eef0f3` | Table headers, wells, default callout | — |
| `--color-border` | `#dde1e6` | Hairlines, card outline | — |
| `--color-border-strong` | `#b8bfc8` | Axes, inputs, dashed outlines | — |
| `--color-gridline` | `#e9ecef` | Chart gridlines | — |
| `--color-text` | `#1a1f29` | Body text, headings, the house in focus | 16.5:1 / 15.1:1 |
| `--color-text-muted` | `#4e5866` | Secondary text | 7.2:1 / 6.6:1 |
| `--color-text-subtle` | `#5f6875` | Captions, axis labels, meta | 5.6:1 / 5.2:1 |
| `--color-focus` | `#2563eb` | Focus ring only | 5.2:1 |
| `--color-notice-bg` / `-text` | `#fff4cc` / `#6b5300` | Fictitious-data banner, preliminary callout | 6.7:1 |

### 2.2 Colour: data

| Token | Value | Meaning | Contrast on white |
|---|---|---|---|
| `--color-under` | `#c8651b` | Bar fill: underestimates | 3.9:1 (graphic ≥ 3:1) |
| `--color-under-strong` | `#9a4a0e` | Text: underestimates | 6.3:1 |
| `--color-under-soft` | `#f8e3d2` | Area tint: below the market | — |
| `--color-over` | `#2e6db4` | Bar fill: overestimates | 5.3:1 |
| `--color-over-strong` | `#1f5594` | Text: overestimates | 7.5:1 |
| `--color-over-soft` | `#dce8f5` | Area tint: above the market | — |
| `--color-result` | `#1a1f29` | Official result (the zero line, the result tick) | 16.5:1 |
| `--color-market` | `#8a939f` | Market / other houses / industry mean | 3.1:1 (graphic) |
| `--color-market-soft` | `#e3e6ea` | Market interval band; ±1 pp target ring | — |
| `--color-house` | `#1a1f29` | The house in focus | 16.5:1 |
| `--color-window` | `#f1ede4` | The final 21-day accuracy window (M-1.3) | — |
| `--color-hatch` | `#c5cbd3` | Hatching for insufficient data | — |
| `--heat-under-1…5`, `--heat-zero`, `--heat-over-1…5` | see file | Heatmap ramp. Steps 1–3 carry ink text (≥ 6.7:1), steps 4–5 white text (≥ 4.5:1). | — |

### 2.3 Typography

| Token | Value | Use |
|---|---|---|
| `--font-sans` | Inter (if installed), Segoe UI, system-ui, … | Everything except the finding |
| `--font-serif` | Source Serif 4, Charter, Sitka Text, Cambria, Georgia | **Only** the headline finding (`.finding`): it marks "this is the answer" |
| `--font-mono` | JetBrains Mono, Cascadia Mono, Consolas | Methodology IDs, formulas |
| `--fs-xs … --fs-2xl` | 12, 14, 16, 18, 22, 28, 36 px | Eyebrow/ticks, captions/tables, body, lead, card finding, page title, grade letter |
| `--lh-tight / -snug / -body` | 1.2 / 1.35 / 1.55 | Headings / findings / prose |
| `--tracking-eyebrow` | 0.08em | Uppercase eyebrow labels |

No web fonts are loaded in the mock-ups (no CDNs). If the public site
self-hosts fonts (T-050/T-052), one sans and one serif with full Romanian
coverage (ș ț with comma below) are enough. All figures are tabular
(`font-variant-numeric: tabular-nums`); the serif uses lining figures.

### 2.4 Spacing, radius, elevation, layout

| Group | Tokens |
|---|---|
| Spacing (4 px base) | `--space-1` 4 · `-2` 8 · `-3` 12 · `-4` 16 · `-5` 24 · `-6` 32 · `-7` 48 · `-8` 64 |
| Radius | `--radius-sm` 6 (chips, badges, heat cells) · `-md` 10 (callouts, inputs) · `-lg` 14 (cards) · `-pill` |
| Elevation | `--shadow-0` none · `-1` card (+ 1 px border) · `-2` hover/popover · `-3` modal (rare) |
| Layout | `--container-max` 72rem · `--measure` 40rem for prose |

Elevation is used sparingly: cards always have a hairline border, and the
shadow only lifts them slightly off the page.

## 3. Colour rules

### 3.1 Direction of deviation (the diverging encoding)

- **Left = underestimates, right = overestimates.** Zero (the result, or the
  market mean) is a solid ink line in the middle.
- **Orange = under, blue = over.** Blue/orange stays distinguishable under
  protanopia, deuteranopia, and tritanopia, and in greyscale the two sides
  differ by position anyway.
- Redundancy, always: the value has a sign (`+3,1`, `−2,9` with a real minus
  U+2212), the bar sits on one side of zero, and the axis carries the words
  "← subestimează" / "supraestimează →".
- The same blue/orange means the same thing everywhere: bars, heatmap cells,
  the gap between house and market on the timeline, value text.

### 3.2 No verdict colours

No red/green, no traffic lights, no colour on grades. A grade badge is ink on
white. "Good" and "bad" are words with numbers, not colours.

### 3.3 Party colours

- A party's colour appears **only as a small square chip** (0.7 rem) next to
  its name: in row labels, column headers, and titles.
- It is **never** used to encode a value, fill a bar, or colour a line. This
  avoids clashes with the over/under pair and between similar party colours,
  and it keeps charts readable for colour-blind readers.
- The name is always written next to the chip; the chip alone is never a label.
- Real party colours are stored per party in data (T-004). Before use, each is
  checked for ≥ 3:1 contrast against white; a failing colour gets a 1 px
  `--color-border-strong` outline.
- The mock-ups use a **placeholder palette** (`--party-a…e`: plum, olive, rose,
  slate, green) chosen away from blue/orange and away from real Romanian party
  colours, so that no fictitious party reads as a real one.

### 3.4 Pollsters

Pollsters are never colour-coded. The house in focus is ink; other houses
and the market are grey. When several houses share a chart (target plot),
they are told apart by **shape** (circle, square, triangle) and a legend, and
hovering one highlights it across rows.

## 4. Number and text formatting (Romanian UI)

| Rule | Example |
|---|---|
| Decimal comma, one decimal for pp | `3,1 p.p.` |
| Thousands with a dot | `1.100` respondenți |
| Real minus sign, explicit plus | `−2,9`, `+3,1` |
| "p.p." for percentage points; "%" only for shares | `32,0%` vs. `+2 p.p.` |
| "≈" prefix for values whose interval includes zero | `≈ −1,4` |
| Intervals as "between … and …" in prose, "…" in cells | "între +1,2 și +4,8 p.p.", `+1,2 … +4,8` |
| "±" only for real intervals, never for an average error | "2,1 p.p. eroare medie" |
| Diacritics with comma below | ș ț Ș Ț (not ş ţ) |

## 5. Chart conventions

| Chart | Encoding | Key rules |
|---|---|---|
| **Diverging bar** (pollster card) | One row per party; bar = point estimate of the relative house effect (M-2.5); whisker = 90% interval | Solid bar if the interval excludes zero; hollow (outline only) if not. Value at the right end of the row. Fixed symmetric axis (±5 pp) so cards are comparable. |
| **Heatmap** (house × party) | Cell fill from the 11-step ramp, by absolute value (<1, 1–2, 2–3, 3–4, ≥4 pp) | Colour only if the interval excludes zero; otherwise a white cell with `≈` and muted text. Interval printed small under the value. Dashed outline = low certainty. Hatched = insufficient data, no number. |
| **Target plot** (one election) | Rows per party; centre line = official result; vertical bands ±1/±3/±5 pp; one mark per house's final poll with its sampling interval (M-4.1); grey tick = industry mean error | Shapes per house; hollow mark if within the margin of error. The grey tick makes the shared miss visible before any single house is judged. |
| **Timeline** (one house, one party, one election) | House polls (ink dots + line), market without that house (grey line + band, M-3.1), result (ink tick at the right edge) | Gap tinted blue/orange; final 21-day window as a warm neutral band; direct labels instead of a legend where possible. |
| **Mini charts** (detail panels, methodology diagrams) | Same encodings, `max-width: 24rem` | One idea per diagram. |

General rules: direct labels over legends; light gridlines only at round
values; axis titles in plain words ("puncte procentuale față de media
institutelor"); one chart answers one question; every SVG has `role="img"`
with a `<title>` and a `<desc>` stating the numbers, and the same data is
available as a table under "Datele".

## 6. Uncertainty and data states

Each state has a distinct visual **and** a wording pattern. States combine
(e.g. low certainty + not distinguishable from zero).

| State | Trigger (methodology) | Visual | Wording pattern (RO) |
|---|---|---|---|
| **Clear deviation** | 90% interval excludes 0 (M-4) | Solid bar/mark; coloured heat cell | "a supraestimat Partidul A cu 3,1 p.p." |
| **Not distinguishable from zero** | Interval includes 0 | Hollow bar/mark; white cell; `≈` prefix; muted value | "abaterea e prea mică pentru a fi sigură" |
| **Low certainty** | N < 3 elections (M-5.2) | Dashed outline on card, badge, and cells; 1 of 3 certainty dots; dashed whisker | "pare să…", "indicii, nu concluzii", grade marked "provizorie" |
| **Medium / high certainty** | 3 ≤ N < 6 / N ≥ 6 | Solid outline; 2 or 3 dots | No hedge beyond the interval |
| **Preliminary** | MVP: at most 3 elections (ADR-0007) | Yellow `callout--preliminary` on every results screen | "Rezultate preliminare: …" |
| **Insufficient data** | No final poll in the window (M-1.3), or below a minimum count | Hatching, no number, no bar; `callout--insufficient` | "Nu avem încă destule date…"; "fără sondaj final" (never "inexact") |
| **Not rated** | Proposed: final polls in fewer than 2 elections | Hatched badge with "–", own group in the leaderboard | "Fără notă încă" |
| **Few polls in campaign** | < 3 polls in 120 days (proposed); < 5 for herding (M-3.4) | Dots only, no line, no gap tint, no campaign metric | "Cu doar 2 sondaje arătăm punctele…" |
| **Thin market** | < 2 other houses publishing in a period (I-013) | Wider grey band; proposed hatching of that period | "Media celorlalte institute e nesigură aici" |

The certainty meter (three dots) is always followed by the word
("certitudine scăzută/medie/ridicată"), never shown alone.

## 7. Component inventory

| Component | Class | Purpose and rules |
|---|---|---|
| Fictitious-data banner | `.fiction-banner` | Mandatory on every mock-up and on any page showing example data. |
| Site header / nav | `.site-header`, `.nav` | Sticky white bar; active item = ink + underline. |
| Page head | `.eyebrow`, `h1`, `.question`, `.finding` | The screen's question (prefixed "Întrebarea:") and the serif answer. |
| Card | `.card`, `.card__head`, `.card__section`, `.card__foot`, `.card--dashed` | White, radius-lg, border + shadow-1. Dashed variant for low-certainty/insufficient states. |
| Stat strip | `.stats`, `.stat` | Uppercase label + one number; unit and comparison in muted small text. |
| **Grade badge + certainty** | `.grade`, `.grade__letter`, `.certainty`; `.is-low`, `.is-unrated`, `.grade--sm` | Ink letter on white, never coloured. Low certainty: dashed + muted + "provizorie". Unrated: hatched tile with "–". |
| Party chip | `.party`, `.party--a…e` | Small square + name (§3.3). |
| **Diverging bar** | SVG `.db-over`, `.db-under`, `.is-ns`, `.whisker`, `.zero` | §5. |
| **Heatmap cell** | `.heat`, `.h-o1…5`, `.h-u1…5`, `.is-ns`, `.is-low`, `.is-insufficient` | Focusable; opens a detail panel. |
| **Interval marker** | SVG `.im-dot`, `.im-whisker`, `.is-ns`, `.is-muted` | Dot (or shape) + whisker; hollow when the interval includes zero. |
| **Callout** | `.callout`, `--caveat`, `--preliminary`, `--insufficient` | `--caveat` is the "Ce nu spunem" box (ADR-0003), present on every results screen. |
| **Table** | `.table`, `.group-row`, `.num` | Right-aligned tabular numbers; group rows for grade groups. |
| Disclosure | `details.disclosure` | The second layer: "Cum citesc…?", "Detalii", "Datele", "Detalii tehnice". |
| Tag | `.tag`, `.tag--method` | Behaviour patterns ("apropiere la final"); methodology IDs (`M-2.5`). |
| Segmented control | `.segmented` | Switch between views of the same data (final polls / whole campaign; elections). |
| Legend | `.legend`, `.ramp` | Only when direct labels are not possible. |
| Design note | `.annot` | Mock-up only; English notes for the team. Not part of the product. |

## 8. Tone of the copy

Neutral, precise, short ([ADR-0003](../decisions/0003-neutral-language.md)).
The final Romanian glossary and copy belong to T-051; these are the working
rules for the mock-ups.

- **Pattern for a finding:** *[Institut] a [supraestimat / subestimat]
  [partidul] [în N alegeri]: [cu X p.p.] [față de media institutelor /
  față de rezultat].* Add the interval in the line below.
- **Use:** "abatere sistematică", "înclinație statistică", "supraestimează",
  "subestimează", "s-a depărtat de", "se abate", "greșeală comună",
  "nu se poate deosebi de zero".
- **Never:** "manipulare", "manipulat", "măsluit", "trucat", "fals",
  "favorizează (intenționat)", "partidul favorizat", "minte". Also avoid
  "favorit" as a label for the party with the largest error.
- **Hedge by certainty, not by adjectives:** low certainty → "pare să",
  "indicii"; otherwise state the number and the interval.
- **Explain absence neutrally:** "fără sondaj final" means "nothing to
  measure", never "inaccurate".
- **Every results screen** carries a "Ce nu spunem" box: what the numbers do
  not show (cause, intent, future accuracy).
- Second person is fine for guidance ("Cum citesc graficul?"); findings stay
  impersonal.

## 9. Dark mode (optional token mapping)

Not used in the mock-ups. If T-052 offers dark mode, it remaps the **same
token names** under a `[data-theme="dark"]` selector (opt-in, plus
`prefers-color-scheme` only if the owner wants it). Semantics stay identical:
blue = over, orange = under, ink-equivalent for the house, grey for the market.

```css
[data-theme="dark"] {
  color-scheme: dark;
  --color-bg: #14171c;
  --color-surface: #1c2027;
  --color-surface-sunken: #232832;
  --color-border: #2f3540;
  --color-border-strong: #4a5260;
  --color-gridline: #262b34;
  --color-text: #e8eaee;          /* 13.6:1 on surface */
  --color-text-muted: #b4bac4;    /*  8.4:1 */
  --color-text-subtle: #9aa1ad;   /*  6.3:1 */
  --color-over: #6aa0de;          /*  6.0:1 */
  --color-over-strong: #8db8ea;   /*  7.9:1 */
  --color-over-soft: #1e3350;
  --color-under: #e08a45;         /*  6.1:1 */
  --color-under-strong: #f0a868;  /*  8.2:1 */
  --color-under-soft: #45301f;
  --color-result: #e8eaee;
  --color-house: #e8eaee;
  --color-market: #8a939f;        /*  5.3:1 */
  --color-market-soft: #2c323c;
  --color-window: #2a2620;
  --color-hatch: #3a414c;
  --color-notice-bg: #3a3214;
  --color-notice-text: #f3dc8a;   /*  9.4:1 */
  --shadow-1: none;               /* elevation by border and surface steps */
  /* Heatmap ramp and party chips must be re-derived and re-checked:
     dark party colours need a light 1 px outline to stay visible. */
}
```

## 10. Accessibility checklist

- Text contrast ≥ 4.5:1, graphical objects ≥ 3:1 (values in §2).
- Information is never carried by colour alone (§3.1, §3.4, §6).
- Visible focus ring (`--color-focus`); heat cells and disclosures are
  keyboard-reachable.
- Each chart: `role="img"`, `<title>`, `<desc>` with the numbers, and a data
  table behind "Datele".
- Touch targets ≥ 44 px on mobile for cells and disclosure rows (to verify in
  T-030).
- `lang="ro"` on public pages; Romanian diacritics with comma below.
- No motion is needed to understand anything; if animation is added later, it
  respects `prefers-reduced-motion`.
