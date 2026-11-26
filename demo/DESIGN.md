<!-- SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0 -->
# SCALE demo: design plan (owner request, 2026-11-26)

## Subject, audience, job

- **Subject.** One small Python and SQLite server on one laptop, pushed by a load generator, in five arms: a full-scan baseline and four one-factor changes (cache, index, read batching, bounded concurrency). The study's world is the engineering drawing and the test bench: dimension lines, request lanes, a load gauge with a redline, the title block of a drawing.
- **Audience.** A curious technical reader who tunes services; an admissions committee reading quickly; a researcher who wants every ratio with its interval and label.
- **Primary job.** Say in one sentence which change moved peak goodput most (read batching, then the cache; bounded concurrency gave no meaningful effect; the index arm is excluded), show it as the study's own instrument (a load gauge of the ratios R), then give the evidence, the recorded-runs explorer, the limitations and how to reproduce.

## Colour (light only, an engineering drawing on drafting film)

| Name | Hex | Role |
|---|---|---|
| Drafting Film | `#EEF2F4` | page ground: a cool, grey-blue film, not cream |
| Sheet | `#F8FAFB` | raised surfaces: figures, tables, the title block |
| Prussian Ink | `#12306B` | headings, rules, outlines, the gauge, the confirmatory label |
| Graphite | `#26303B` | body text |
| Signal Yellow | `#F2B300` | requests in the illustration, the practical-equivalence band, owner-decision labels |
| Redline | `#C8202F` | limits: the generator ceiling, the excluded index arm, batch containers |

The five arms keep series colours with distinct dashes and markers (`#3A4450`, `#1F6FB2`, `#7A4FB0`, `#A85F00`, `#1B7A68`). Labels stay words with border styles: confirmatory solid ink, frozen sensitivity double rule, descriptive dotted, exploratory dashed amber, measured teal, design value dotted grey, owner decision on Signal Yellow.

Light only: a drawing is ink on film, and a dark variant would read as a blueprint cliché and collide with TOKEN's dark thermal page.

## Type

On 2026-11-26 both faces were replaced so that no two lab demos share a typeface (owner request; Barlow Condensed and Source Serif 4 now belong to other labs).

- **Antonio** (variable weight, latin; used at 600, and at 500 for the smallest labels): headings, labels, gauge numerals, table heads, the title block. A tall, tightly condensed grotesque with straight sides and a very high x-height, close to the stencilled and plotted lettering on engineering drawings and instrument dials. It has tabular figures, so gauge readings and legend values stay aligned.
- **Literata** (variable weight, latin; used at 400 and 700): body and table text, with tabular lining figures. A sturdy book serif drawn for long reading on screens; its firm wedge serifs and even colour suit the long methodological text and keep SCALE the one serif-bodied lab next to a condensed sans.

Tuning for the new faces, measured in Chrome: Antonio's cap height is 0.86 em against 0.70 for Barlow Condensed and it sets about 6 per cent wider at the same size and weight, so heading and large numeral sizes were multiplied by 0.86 and smaller display labels, chart ticks and gauge captions by 0.9 (cap heights stay equal or slightly taller, lines get shorter). The smallest labels (chart ticks, title-block keys, small dial captions) moved to weight 500 with 0.02 to 0.03 em tracking, because Antonio's 600 closes up at 12 px. Literata has a slightly higher x-height than Source Serif 4 (0.51 against 0.49 em) at about the same width, so the 17 px body stays and its line height went from 1.68 to 1.64.

## Layout

Left-aligned reading column (at most 70 characters), figures wider (up to 74 rem). Hero on a 24 px drafting grid: question and answer left, request-lane illustration right; on phones the illustration follows the answer.

```
+-------------------------------------------------------------+
| [gauge] SCALE        Result Experiments Explorer ... Reproduce| sticky bar, ink rule
+-------------------------------------------------------------+
| Cache, index, batching or      | <-- one laptop, one process --> |
| admission control: which ...   | gen [ ]---- [server] ■ ■ ■ ■ ■ ■ |
| Answer sentence from the data. | gen [ ]---- [server] [■■■][■■■]  |
|                                | Illustration, not study data     |
+-------------------------------------------------------------+
| Load gauge, log scale, needles A4 A1 A3 | legend with values  |
|   (A2: no needle, excluded)             |                     |
+-------------------------------------------------------------+
| Status, in short, owner decisions                            |
| Published results: effect plot, experiment panels            |
| Explorer, exploratory re-analysis, assumptions, method       |
| Reproduce                                                    |
| Footer as a drawing title block: study, author, status, rev  |
+-------------------------------------------------------------+
```

## Motion

- **One orchestrated hero moment: the batch overtakes.** On load, single requests travel one by one from the load generator through the server, while the batched lane carries three reads per container and finishes first (transform only, strong ease-out, 260 ms stagger for singles, 300 ms for containers, about 2 s in all). It plays once, carries no number and is labelled "Illustration, not study data".
- **Motion that answers the visitor.** The gauge needles sweep once from R = 1 to their confirmatory value when the gauge scrolls into view (WAAPI on transform, 1.1 s, 80 ms stagger); the explorer is unchanged in behaviour (instant redraw, since a visitor changes it many times). Hover colour on links and selects only for fine pointers. No `transition: all`.
- **Reduced motion.** No animation; everything is drawn in its final state.

## The one memorable thing

The load gauge: the study's confirmatory ratios as needles on a log-scale dial with its equivalence band and its redline-coloured logo twin, with the excluded index arm listed at the same weight as "no needle".

## Review against the frontend-design tells and the other demos

- **Broadsheet hairlines (tell 3).** The first draft used hairline rules and zero radius everywhere. Kept square corners (they belong to a drawing) but replaced hairlines on figures with 1.5 to 2 px ink outlines and used the rule weight to encode hierarchy (ink rules for the bar and hero, light rules between sections).
- **Cream background (tell 1).** Rejected in favour of a cool drafting-film grey-blue.
- **All-caps eyebrow and middle dots (tell 5).** The previous upper-case kicker and the "·" meta separators are removed.
- **Mono data labels (tell 5).** None; code paths only inside `<code>`.
- **SaaS cards (tell 4).** No shadows or rounded cards; panels are outlined frames, and the footer is a title block, a structure that carries real information.
- **Search tool output.** The UI/UX search proposed a generic dashboard system (Fira Code with Fira Sans); rejected.
- **Other demos.** TOKEN is the dark thermal page; FARE uses a departure board; MARKET a trading floor. SCALE is the only drawing-on-film page, the only serif-bodied one, and its signature is an instrument (the gauge) rather than an animation of the subject.

## Brand files

`public/brand/`: `scale-mark.svg`, `scale-mark-dark.svg`, `scale-mark-mono.svg`, `scale-wordmark.svg`, `scale-lockup.svg`, `scale-lockup-dark.svg`, `scale-lockup-mono.svg`, `favicon.svg`, `favicon-32.png`, `og.png` (1200 x 630). Mark: a load gauge (a half-ring dial with a separated redline segment), a needle and a square hub that doubles as a packed container. Wordmark: SCALE drawn from half-ring bowls and straight strokes on a 120-unit cap height. All paths drawn by hand; `svg_audit.py` scores 99 to 100 with no warning. The wordmark is not drawn from any typeface, so the 2026-11-26 typeface change left the mark, wordmark, lockups and favicon unchanged; `og.png` was re-exported with Antonio and Literata from `tools/og/og.html`.
