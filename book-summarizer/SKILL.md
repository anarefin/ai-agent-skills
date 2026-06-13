---
name: book-summarizer
description: >
  Use this skill whenever a user uploads a PDF book (technical or otherwise) and wants
  a beginner-friendly summary, study guide, or chapter breakdown. Triggers on phrases like:
  "summarize this book", "explain this book for beginners", "extract key takeaways",
  "make this book easier to understand", "chapter summary", "study guide for this book",
  "break down each chapter", "simplify this book", "explain the concepts in this book".
  Also trigger when a user uploads a PDF and asks anything like "help me understand this"
  or "what is this book about" — even if they don't explicitly say "summarize".
  Produces a polished single-file HTML document with a chapter nav sidebar, dark/light
  mode toggle, and a standardized beginner-friendly layout for every chapter.
---

# Book Summarizer Skill

Produces a single self-contained HTML file summarising every chapter of a PDF book.
Target audience: **complete beginners** — assume zero domain knowledge.

---

## Step 0 — Gather user preferences (ALWAYS do this first)

Before touching the PDF, ask the user two things in a single message:

```
1. Where would you like the output file saved?
   Default: /mnt/user-data/outputs/book_summary.html
   (You can give a full path, or just a filename — I'll place it in the outputs folder.)

2. Are there any chapters you'd like to skip or prioritise?
   Default: process all chapters in order.
```

Wait for their reply. If they don't specify a path, use the default.
Sanitise the path: if they give a bare filename (e.g. `my_book.html`), prepend
`/mnt/user-data/outputs/`. Ensure the extension is `.html`.

Store the resolved path as `OUTPUT_PATH` — use it everywhere in Steps 3 and 6.

---

## Step 1 — Read the PDF

First, run a content inventory:

```bash
pdfinfo /mnt/user-data/uploads/<filename>.pdf
pdffonts /mnt/user-data/uploads/<filename>.pdf
pdftotext -f 1 -l 1 /mnt/user-data/uploads/<filename>.pdf - | head -30
```

Then extract all text:

```bash
pdftotext -layout /mnt/user-data/uploads/<filename>.pdf /tmp/book_text.txt
```

If `pdffonts` shows no fonts (scanned PDF), rasterize pages instead:

```bash
pdftoppm -jpeg -r 150 /mnt/user-data/uploads/<filename>.pdf /tmp/page
# then view each image for OCR-level reading
```

Read `/tmp/book_text.txt` (or rasterized pages) to understand:
- The **book title, author, and domain**
- The **table of contents** — chapter titles and page ranges
- The **tone and depth** of writing (beginner, intermediate, advanced)

While reading the table of contents, collect for each chapter:
- Title and page range
- Approximate page count → used to estimate reading time (assume 200 words/page, 200 wpm)
- Subjective difficulty signal: scan opening paragraphs for jargon density → assign
  `Beginner` / `Intermediate` / `Advanced` badge

---

## Step 2 — Analyse each chapter

For each chapter (respecting any skip/prioritise choices from Step 0):

```bash
pdftotext -f <start_page> -l <end_page> -layout /mnt/user-data/uploads/<filename>.pdf /tmp/ch_N.txt
```

Process each chapter through this analytical lens:

| Question | Purpose |
|---|---|
| What is the chapter **trying to teach**? | Central thesis |
| What are the **3–7 most important ideas**? | Key takeaways |
| What **new words or terms** does it introduce? | Glossary |
| What **real-world thing** behaves like this concept? | Analogy candidates |
| Why would a beginner **care about this**? | "Why it matters" hook |
| What are **3 questions** to test understanding? | Review questions |
| Which concepts in **earlier chapters** does this build on? | Concept connections |

**For math/formula/code-heavy chapters:** Do NOT reproduce the formulas or code.
Instead, explain what the formula or algorithm *achieves* and *why it matters*
in plain English. Focus on the intuition, not the mechanics.

**Concept connection tracking:** Maintain a running list of key terms introduced
per chapter (e.g. `{ch1: ["model", "training", "loss function"], ch2: [...], ...}`).
When a later chapter uses a term from an earlier one, note it — this powers
the "Builds on" cross-reference links in the sidebar and chapter headers.

---

## Step 3 — Build the HTML output

Generate a single self-contained HTML file at `OUTPUT_PATH`.

The HTML must include everything inline (no external CDN dependencies) — fonts via
`@import` from Google Fonts is acceptable.

### Required structure per chapter section

Every chapter section must contain **all seven** of these blocks, in order:

1. **Chapter header** — number, title, one-sentence summary, difficulty badge,
   and estimated reading time (e.g. "~12 min read")
2. **Key Takeaways** — 3–7 bullet points, each a complete plain-English sentence
3. **Core Concepts Explained** — one subsection per major concept:
   - Concept name as a subheading
   - 2–4 paragraph plain-English explanation (no jargon without immediate definition)
   - A clearly labelled **Real-World Analogy** box for each concept
4. **Why It Matters** — a callout box: 2–3 sentences on practical relevance
5. **Builds On** — a compact row of pill-shaped links to earlier chapters whose
   concepts this chapter relies on (skip if chapter 1 or no dependencies)
6. **Mini Glossary** — key terms introduced in this chapter, defined in one sentence each,
   with a 📋 copy-to-clipboard button per term
7. **Review Questions** — exactly 3 questions a beginner should be able to answer,
   each in a `<details>` card with the answer hidden by default

### Required global structure

```
<progress bar>          ← thin reading-progress strip at very top of viewport
<sidebar>               ← chapter list with difficulty badges + read-time; scrollspy active state
<main content area>     ← book header, then all chapter sections sequentially
<dark/light toggle>     ← top-right fixed button, persists via localStorage
<back-to-top button>    ← bottom-right fixed, appears after 300px scroll
<search bar>            ← inside sidebar header; filters chapter list by keyword live
```

### Sidebar chapter list item structure

Each sidebar nav entry must show:
```
[difficulty badge]  Chapter N
                    Chapter title
                    ~N min read
```

Difficulty badge colours:
- `Beginner`     → green pill  (`#2D7A4F` bg, white text)
- `Intermediate` → amber pill  (`#B45309` bg, white text)
- `Advanced`     → red pill    (`#991B1B` bg, white text)

---

## Step 4 — HTML design spec

Read `/mnt/skills/public/frontend-design/SKILL.md` before writing a single line of CSS.
Then apply these constraints specific to this skill:

### Aesthetic direction
- **Feel:** Academic but warm. Like a well-designed university textbook meets a modern
  product documentation site. Not corporate, not hacker-dark.
- **Signature element:** Each "Real-World Analogy" block has a distinctive left-border
  colour accent and a subtle background tint — make this the most visually memorable
  repeated element in the document.

### Colour tokens (light mode)

```css
--bg-primary:     #FAFAF8;
--bg-secondary:   #F0EEE9;
--bg-accent:      #FFF8EE;
--text-primary:   #1A1A18;
--text-secondary: #5A584F;
--text-muted:     #8A8880;
--accent:         #C75B2A;
--accent-soft:    #E8936A;
--success:        #2D7A4F;
--warning:        #B45309;
--danger:         #991B1B;
--border:         #E0DDD6;
```

Dark mode (`prefers-color-scheme` + toggle class `.dark` on `<html>`):

```css
--bg-primary:   #18181A;
--bg-secondary: #222226;
--bg-accent:    #2A2416;
--text-primary:   #F0EEE9;
--text-secondary: #A8A69E;
--text-muted:     #6A6860;
--accent:       #E8936A;
--accent-soft:  #C75B2A;
--success:      #4AAF76;
--warning:      #D97706;
--danger:       #EF4444;
--border:       #333330;
```

### Typography

```css
font-family: 'Playfair Display', Georgia, serif;   /* chapter titles */
font-family: 'Source Serif 4', Georgia, serif;     /* body text */
font-family: 'Inter', system-ui, sans-serif;       /* UI, labels, glossary */
```

Import from Google Fonts at the top of `<style>`.

### Layout

- **Sidebar:** 260px fixed left, full viewport height, independently scrollable
- **Main:** `margin-left: 260px`, max-width 760px, auto side margins
- **Mobile (< 768px):** sidebar hidden behind hamburger toggle
- **Chapter sections:** separated by decorative large chapter number in `--text-muted` (opacity 0.18)

### Component specs

**Analogy block:**
```css
border-left: 4px solid var(--accent);
background: var(--bg-accent);
border-radius: 0 8px 8px 0;
padding: 1rem 1.25rem;
/* Label: "💡 Analogy" — Inter, 0.68rem, uppercase, letter-spacing 0.1em */
```

**Why It Matters block:**
```css
border-left: 4px solid var(--success);
background: color-mix(in srgb, var(--success) 8%, var(--bg-primary));
border-radius: 0 8px 8px 0;
padding: 1rem 1.25rem;
/* Label: "✦ Why It Matters" */
```

**Builds On row:**
```css
/* Horizontal flex row of pill links */
/* Each pill: bg var(--bg-secondary), border var(--border), Inter 0.75rem */
/* On hover: border-color var(--accent), color var(--accent) */
/* Label above row: "🔗 Builds On" — muted, uppercase */
```

**Glossary:**
```css
/* Two-column grid on desktop, one column on mobile */
/* Term: Inter bold, var(--accent) */
/* Definition: Source Serif 4, var(--text-secondary) */
/* Copy button: small icon button, fades in on hover, shows "✓ Copied!" for 1.5s */
```

**Review question cards:**
```css
/* <details> element, bg var(--bg-secondary), border var(--border), border-radius 8px */
/* Q-prefix badge in var(--accent), answer revealed on open */
```

**Difficulty badge:**
```css
/* Inline pill: Inter 0.65rem bold, border-radius 20px, padding 0.15rem 0.5rem */
/* Colours per level: see Step 3 */
```

**Back-to-top button:**
```css
position: fixed; bottom: 1.5rem; right: 1.5rem;
/* Hidden until scrollY > 300; fade in/out */
/* Round button, bg var(--bg-secondary), border var(--border) */
```

### Print stylesheet

Include a `@media print` block that:
- Hides sidebar, progress bar, toggle, back-to-top, and search
- Sets `margin-left: 0` on main, removes fixed positioning
- Forces light-mode colours regardless of `.dark` class
- Adds chapter URL as footer via `content: attr(href)` on links
- Sets `page-break-before: always` on each `.chapter-section`

---

## Step 5 — JavaScript requirements (all inline)

```javascript
// 1. Dark/light toggle
//    localStorage('theme') → apply .dark to <html> on load
//    Toggle writes back to localStorage

// 2. Scrollspy
//    IntersectionObserver on each .chapter-section
//    Highlights matching sidebar link; rootMargin: '-20% 0px -60% 0px'

// 3. Reading progress bar
//    scroll → scrollY / (scrollHeight - innerHeight) * 100 → bar width

// 4. Sidebar mobile toggle
//    Hamburger at < 768px → toggles .sidebar-open on <body>
//    Close when nav link clicked

// 5. Sidebar search / filter
//    input event on search field → show/hide nav <li> items by matching
//    chapter title text (case-insensitive); show "No results" if all hidden

// 6. Glossary copy-to-clipboard
//    Each copy button → navigator.clipboard.writeText(term + ': ' + definition)
//    Button text changes to "✓" for 1500ms then resets

// 7. Back-to-top button
//    scroll → show/hide based on scrollY > 300
//    Click → window.scrollTo({ top: 0, behavior: 'smooth' })
```

---

## Step 6 — Quality checklist before saving

- [ ] User-specified `OUTPUT_PATH` is used (not hardcoded default if user gave a custom path)
- [ ] Every chapter has all 7 required blocks
- [ ] Chapter header shows difficulty badge + estimated reading time
- [ ] Builds On pills are present for chapters with concept dependencies; absent for ch1
- [ ] Sidebar search input is present and filters the chapter list
- [ ] Each glossary term has a working copy-to-clipboard button
- [ ] Back-to-top button is present and hidden initially
- [ ] Print stylesheet is included
- [ ] No unexplained jargon — every term is defined inline or in the glossary
- [ ] Analogy blocks use concrete everyday comparisons
- [ ] Math/formulas/code described in plain English only
- [ ] Dark mode colours pass WCAG AA contrast
- [ ] HTML file is fully self-contained

---

## Step 7 — Output

Save the file to `OUTPUT_PATH`, then call `present_files` with that path.

Tell the user:
- Book title, author, and total chapters processed
- The exact file path where the output was saved
- Any chapters skipped or that had extraction issues
- Tip: dark/light toggle top-right; sidebar search filters chapters; glossary terms are copyable; Ctrl+P / ⌘+P gives a clean print layout