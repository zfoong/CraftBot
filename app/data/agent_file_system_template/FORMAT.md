# Formatting Standards

Agent reads this before generating any file. Edit to customize.
`## global` = universal. `## <filetype>` = type-specific overrides.

---

## global

### Colors
- Base: `#141517` (deep grey — primary background/text on light)
- Surface: `#1E1F22` (card/panel bg in dark contexts)
- Muted: `#6B6E76` (secondary text, captions, borders)
- Border: `#2E2F33` (dividers, table lines, rules)
- White: `#FFFFFF` (bg on light, text on dark)
- Light grey: `#F4F4F5` (alt row shading, subtle bg)
- Highlight: `#FF4F18` (accent — sparingly: key stats, active states, CTAs, emphasis)
- Highlight hover: `#E64615` (darker variant for pressed/hover states)

**Usage rules:**
- Highlight is for emphasis only — never large fills, never body text color.
- Max 1–2 highlight elements per page/slide/section.
- Body text is always base or white depending on bg.

### Typography
- Font family: Roboto (all weights). Fallback: Arial, Helvetica, sans-serif.
- Weights: 300 (Light), 400 (Regular), 500 (Medium), 700 (Bold).

| Role | Size | Weight | Color | Spacing |
|---|---|---|---|---|
| Display / hero | 32–40pt | 700 | base or white | line-height 1.1, letter-spacing -0.5px |
| H1 | 22–26pt | 700 | base or white | line-height 1.2, margin-bottom 16px |
| H2 | 16–18pt | 700 | base or white | line-height 1.25, margin-bottom 12px |
| H3 | 13–14pt | 500 | base or muted | line-height 1.3, margin-bottom 8px |
| Body | 11pt | 400 | base | line-height 1.5, paragraph spacing 10px |
| Small / caption | 9–10pt | 300 or 400 | muted | line-height 1.4 |
| Code / mono | 10pt | 400 | base | font: Roboto Mono, line-height 1.45 |

### Writing & Content
- Sentence case for all headings. Never ALL CAPS except single-word labels (e.g., "NOTE").
- Em dashes (—) not hyphens. Curly quotes not straight.
- Left-align body. Never justify (causes uneven word spacing).
- One idea per paragraph. Max 4 sentences per paragraph.
- Prefer active voice. No filler ("It is important to note that…" → cut).
- Numbers: spell out one–nine, digits for 10+. Always digits for units (3 kg, 5 min).

### General Layout
- Whitespace is a design element — do not fill every gap.
- Visual hierarchy: size → weight → color. Not decoration.
- Max content width: 7" (print), 720px (screen).
- Consistent internal padding: 12–20px or 0.2–0.3" in print contexts.

---

## pptx

### Slide setup
- 16:9 widescreen (13.333" × 7.5"). No 4:3.
- Safe margins: 0.5" all sides. Keep all content inside.
- Grid: mentally divide slides into 12 columns for alignment.

### Color application
- Title/section slides: base `#141517` full-bleed bg, white text, highlight accent stripe or element.
- Content slides: white bg, base text. Highlight for one focal element only.
- Charts/graphs: use base, muted, light grey as series colors. Highlight for the one key series.

### Typography (slide-specific)
| Role | Size | Weight |
|---|---|---|
| Slide title | 32–36pt | 700 |
| Subtitle / section | 18–22pt | 300 or 400 |
| Bullet text | 16–18pt | 400 |
| Data callout / stat | 44–56pt | 700, highlight color |
| Source / footnote | 9–10pt | 300, muted |

### Content rules
- DO NOT excessively use list of 3–5 bullet points per slide, which is a common LLM mistake.
- Max 6 words per bullet headline. Supporting text below if needed (12–14pt, muted).
- One key message per slide. If you can't state it in one sentence, split.
- Ideally, every slide should have a visual: chart, diagram, icon, image, or shape block. No text-only slides.
- Trying using varying layout or blocks across the deck/slice: full-bleed image, two-column, stat callout, comparison grid, timeline.

### Common mistakes to avoid (unless specify otherwise)
- **Over use of bullet points:** Using 3-5 bullets for every pages.
- **Uniform layout:** every slide is title + bullets. Fix: alternate layouts every 2–3 slides.
- **Oversized tables:** tables with 5+ columns or 8+ rows are unreadable. Fix: simplify, show top 5, or use a chart.
- **Missing visual hierarchy:** all text same size/weight. Fix: title ≠ body ≠ caption.
- **Image bleeds off slide or wrong aspect ratio:** always set image dimensions explicitly within safe area. Never stretch.
- **Orphan slides:** a single-bullet slide or a slide that only says "Thank you." Combine or enrich.
- **Inconsistent alignment:** elements randomly placed. Fix: snap to grid, align to slide's left margin.
- **Overusing highlight color:** more than 2 highlight elements per slide dilutes emphasis.

---

## docx

### Page setup
- US Letter 8.5" × 11". Margins: 1" top/bottom, 1" left/right.
- Header: 0.5" from top edge. Footer: 0.5" from bottom edge.
- Page numbers: bottom-center, Roboto 9pt, muted color.

### Typography (doc-specific)
| Role | Size | Weight | Color | Extra |
|---|---|---|---|---|
| Title (doc) | 26pt | 700 | base | 24px below, optional highlight underline |
| H1 | 18pt | 700 | base | 18px above, 10px below, border-bottom 1px muted |
| H2 | 14pt | 700 | base | 14px above, 8px below |
| H3 | 11pt | 700 | base | 12px above, 6px below |
| Body | 11pt | 400 | base | line-height 1.5, 10px paragraph spacing |
| Blockquote | 11pt | 400 italic | muted | left border 3px highlight, 12px left padding |
| Table header | 10pt | 700 | white on base bg | |
| Table cell | 10pt | 400 | base | alt row: light grey bg |

### Structure rules
- **Max heading depth: 3 levels.** Never use H4+. If you need it, restructure.
- **Sections:** Do not over-segment. A 2-page doc should not have 10 headings. A section should have more paragraphs rather than just 2-3 sentences. Otherwise, merge sections.
- **Paragraph length:** Must not have less than 2–5 sentences.
- **Lists:** Do not over-use list.
- **Tables:** use only for genuinely tabular data (rows × columns). Do not use tables for layout or for simple lists.
- **Table sizing:** max 5 columns. More than 5 → rotate to vertical layout or split. Column widths must be set explicitly — never auto-width with overflow.
- **Horizontal rules:** use sparingly to separate major sections. Max 2–3 per document.

### Common mistakes to avoid (unless specify otherwise)
- **Over-sectioning:** every paragraph gets its own heading. Fix: merge related short sections.
- **List abuse:** entire document is nested bullet lists. Fix: write in prose. Lists are for parallel items only.
- **Table for everything:** using a 2-column table instead of a definition list or bold+colon. Fix: use inline formatting.
- **Extra page breaks:** a section breaks mid-page awkwardly. 
- **Inconsistent spacing:** different gaps between headings and body. Fix: define and reuse paragraph styles.
- **Images not anchored:** images float to wrong page or overlap text. Fix: set inline positioning, explicit width (max 6.5" for full-width), and keep-with-next.
- **Image too large:** image exceeds printable area. Fix: max width = page width minus margins. Always set explicit dimensions.
- **Phantom empty paragraphs:** blank lines used for spacing. Fix: use paragraph spacing, not empty returns.
- **Font fallback failure:** Roboto not embedded → falls back to Times New Roman. Fix: embed fonts or use a guaranteed-available fallback.

---

## xlsx

### Sheet setup
- Default column width: 14 characters. Adjust per content.
- Freeze top row (header) and first column (labels) by default.
- Zoom: 100%. Never deliver at odd zoom levels.
- Print area: set explicitly if document may be printed.
- Sheet names: short, no spaces (use underscores), max 20 chars.

### Cell formatting
| Element | Font | Size | Color | Background |
|---|---|---|---|---|
| Header row | Roboto Bold | 11pt | white | base `#141517` |
| Data cell | Roboto Regular | 10pt | `#141517` | white |
| Alt row | Roboto Regular | 10pt | `#141517` | `#F4F4F5` |
| Total/summary row | Roboto Bold | 10pt | `#141517` | `#E8E8EA` border-top 2px |
| Highlight cell | Roboto Bold | 10pt | `#FF4F18` | — |

### Number formatting
- Currency: `$#,##0` (no decimals) or `$#,##0.00` (two decimals). Be consistent within a sheet.
- Percentages: `0.0%` (one decimal).
- Integers: `#,##0` with thousands separator.
- Negatives: parentheses `(1,234)` not minus `-1,234`. Red text optional.
- Dates: `YYYY-MM-DD`. Never `MM/DD/YY`.
- Don't mix formatted and unformatted numbers in same column.

### Financial model conventions
- Blue `#0000FF`: hardcoded inputs/assumptions.
- Black: calculated formulas.
- Green `#008000`: cross-sheet or external references.
- Yellow bg `#FFFF00`: key assumption cells.

### Structure rules
- **One topic per sheet.** Don't combine unrelated tables on one sheet.
- **Header row is row 1.** No merged title rows above data. Use sheet name for title.
- **No merged cells in data ranges.** Merged cells break sorting, filtering, and formulas.
- **No blank rows/columns** within data ranges. Blank rows break auto-detection.
- **Column order:** identifiers first (name, ID, date), then measures, then calculations, then notes.
- **Wrap text** for cells with >30 chars. Set explicit row height.

### Common mistakes to avoid (unless specify otherwise)
- **Merged cells:** breaks all data operations. Fix: never merge in data areas. Only merge in clearly decorative headers outside data range.
- **Formulas as values:** pasting values when formulas are needed. Fix: always verify formula references.
- **Inconsistent number formats:** same column has `$1,000` and `1000.00`. Fix: apply format to entire column.
- **Hidden data:** rows/columns hidden and forgotten. Fix: unhide all before delivery.
- **No header row:** data starts at A1 with no labels. Fix: always include descriptive headers.
- **Overly wide sheets:** 20+ columns requiring horizontal scroll. Fix: split into multiple sheets or pivot layout.
- **Print overflow:** data prints across 5 pages wide. Fix: set print area, fit to 1 page wide.
- **Circular references:** fix before delivery. If intentional, document in a Notes sheet.
- **Hard-coded numbers in formulas:** `=A1*0.08` instead of referencing a tax rate cell. Fix: externalize assumptions.

---

## pdf

### Page setup
- US Letter 8.5" × 11". Margins: 1" all sides.
- Header: base `#141517` bar (0.4" tall), white text left-aligned (document title, Roboto 9pt).
- Footer: centered page number, Roboto 9pt, muted `#6B6E76`.
- First page may omit header for a custom title block.

### Typography
- Same as docx standards. Body: Roboto 11pt, headings: Roboto Bold.
- Use ReportLab XML markup for superscripts, subscripts if applicable.
- Embed all fonts. Never rely on system fonts.

### Design
- Section dividers: 1px line in muted color, full content width.
- Callout boxes: light grey `#F4F4F5` bg, left border 3px highlight `#FF4F18`, 10px padding.
- Tables: same style as docx (base header bg, alt row shading).
- Cover page (if applicable): base bg full page, white title 32pt center, highlight accent line.

### Structure rules
- **Max heading depth: 3 levels.** Never use H4+. If you need it, restructure.
- **Sections:** Do not over-segment. A 2-page doc should not have 10 headings. A section should have more paragraphs rather than just 2-3 sentences. Otherwise, merge sections.
- **Paragraph length:** Must not have less than 2–5 sentences.
- **Lists:** Do not over-use list.
- **Tables:** use only for genuinely tabular data (rows × columns). Do not use tables for layout or for simple lists.
- **Table sizing:** max 5 columns. More than 5 → rotate to vertical layout or split. Column widths must be set explicitly — never auto-width with overflow.
- **Horizontal rules:** use sparingly to separate major sections. Max 2–3 per document.

### Common mistakes to avoid (unless specify otherwise)
- **Images not rendering:** wrong path, unsupported format, or not embedded. Fix: use absolute paths, embed images, verify format (PNG/JPG).
- **Image exceeds margins:** overflows into margin or off-page. Fix: set max width = page width − 2× margin. Always calculate available space.
- **Text overlaps elements:** manually positioned text collides with tables or images. Fix: use flowable layout, not absolute coordinates (unless precise placement is required).
- **Broken table across pages:** table starts near page bottom, header row orphaned. Fix: use repeatRows for header, allow table to split cleanly.
- **Wrong page size:** defaulting to A4 when US Letter expected. Fix: set explicitly.
- **Missing fonts:** tofu characters (□). Fix: embed TTF files, register before use.
- **Massive file size:** uncompressed images. Fix: resize images to display size before embedding. Max 150 DPI for screen, 300 DPI for print.
- **Raw markup in output:** PDF shows literal `## Heading` or `**bold**` instead of rendered formatting. Fix: ensure all markdown/markup is fully converted to native PDF elements (styled paragraphs, bold spans, etc.) before rendering. Never pass raw markdown text directly into PDF content.
- **Over-sectioning:** every paragraph gets its own heading. Fix: merge related short sections.
- **List abuse:** entire document is nested bullet lists. Fix: write in prose. Lists are for parallel items only.
- **Table for everything:** using a 2-column table instead of a definition list or bold+colon. Fix: use inline formatting.
- **Extra page breaks:** a section breaks mid-page awkwardly. 
- **Inconsistent spacing:** different gaps between headings and body. Fix: define and reuse paragraph styles.
- **Images not anchored:** images float to wrong page or overlap text. Fix: set inline positioning, explicit width (max 6.5" for full-width), and keep-with-next.
- **Image too large:** image exceeds printable area. Fix: max width = page width minus margins. Always set explicit dimensions.
- **Phantom empty paragraphs:** blank lines used for spacing. Fix: use paragraph spacing, not empty returns.
- **Font fallback failure:** Roboto not embedded → falls back to Times New Roman. Fix: embed fonts or use a guaranteed-available fallback.

---

## md

### Formatting
- ATX headings only (`#`, `##`, `###`). Max depth: 3 levels.
- One blank line before and after headings, code blocks, and block quotes.
- No trailing whitespace. No multiple consecutive blank lines.
- Fenced code blocks with language identifier: ` ```python `. Never indented code blocks.
- Links: inline `[text](url)` for fewer than 3 links. Reference-style `[text][id]` for 3+.
- Images: `![alt text](path)` — always include alt text.
- Bold: `**text**`. Italic: `_text_`. Never use `__` or `*` for these.

### Structure rules
- **Front matter:** if used, YAML only (`---` delimiters).
- **Heading hierarchy:** never skip levels (no H1 → H3).
- **Lists:** max 7 items. Nested lists max 2 levels. Use `-` for unordered (not `*`).
- **Tables:** max 5 columns. Always include header separator `|---|`. Align consistently.
- **Line length:** wrap at 100 characters for readability in raw form (unless the target is rendered-only).
- **Paragraphs:** 2–5 sentences. Single-sentence paragraphs only for emphasis.

### Content conventions
- **README files:** order sections as: title, description (1–2 lines), installation, usage, configuration, API/reference, contributing, license.
- **Documentation:** lead with what it does, then how to use it, then edge cases/details.
- **No HTML** in Markdown unless absolutely necessary (complex tables, embedded media).

### Common mistakes to avoid (unless specify otherwise)
- **Over-nesting lists:** 4+ indent levels. Fix: flatten or restructure into subsections.
- **Heading as formatting:** using `###` just to make text bold. Fix: use `**bold**`.
- **No blank lines around blocks:** heading immediately followed by text or code fence. Fix: always add blank lines.
- **Giant tables:** 10+ column tables in Markdown are unreadable raw. Fix: simplify or link to CSV.
- **Inconsistent list markers:** mixing `-`, `*`, `+`. Fix: use `-` everywhere.
- **Raw URLs:** bare `https://...` without link syntax. Fix: wrap in `<>` or `[label](url)`.
- **Over-use of emphasis:** every other word is **bold** or _italic_. Fix: emphasis means rare.

---

## html

### Setup
- DOCTYPE: `<!DOCTYPE html>`. Lang attribute set.
- Viewport meta: `<meta name="viewport" content="width=device-width, initial-scale=1.0">`.
- Charset: UTF-8.
- Use semantic tags: `<header>`, `<main>`, `<section>`, `<article>`, `<footer>`, `<nav>`.

### Typography (CSS)
```
body { font-family: 'Roboto', Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #141517; }
h1 { font-size: 2rem; font-weight: 700; margin: 1.5rem 0 1rem; }
h2 { font-size: 1.5rem; font-weight: 700; margin: 1.25rem 0 0.75rem; }
h3 { font-size: 1.125rem; font-weight: 500; margin: 1rem 0 0.5rem; }
small, .caption { font-size: 0.8rem; color: #6B6E76; }
```

### Color (CSS variables)
```
:root {
  --color-base: #141517;
  --color-surface: #1E1F22;
  --color-muted: #6B6E76;
  --color-border: #2E2F33;
  --color-white: #FFFFFF;
  --color-light: #F4F4F5;
  --color-highlight: #FF4F18;
  --color-highlight-hover: #E64615;
}
```

### Layout rules
- Max content width: 720px centered for articles/docs. Full-width for dashboards.
- Spacing scale: 4px base. Use multiples: 8, 12, 16, 24, 32, 48, 64.
- Responsive: mobile-first. Breakpoints at 640px, 1024px, 1280px.
- No inline styles. All styling in `<style>` block or external CSS.

### Common mistakes to avoid (unless specify otherwise)
- **Div soup:** nested `<div>` for everything. Fix: use semantic elements.
- **Missing alt text on images.** Fix: always provide descriptive alt.
- **Fixed pixel widths on responsive layouts:** images or containers overflow on mobile. Fix: use `max-width: 100%`.
- **Inaccessible color contrast:** muted text on dark bg. Fix: verify WCAG AA (4.5:1 for body text).
- **Missing viewport meta:** page not responsive on mobile. Fix: always include.
- **Script blocking render:** JS in `<head>` without `defer`. Fix: put scripts at end of body or use `defer`.
- **Missing `lang` attribute.** Fix: `<html lang="en">`.
