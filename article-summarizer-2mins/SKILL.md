---
name: article-summarizer-2mins
description: >
  Fast 2-minute read of any article, blog post, or web page: a tight summary, the most
  critical key points, and 1–2 sharp actions — all strictly from the content, delivered
  instantly with no back-and-forth. Use this skill when the user wants a rapid digest and
  says things like "quick summary", "TL;DR", "2 min version", "give me the gist",
  "what's the takeaway", "brief breakdown", or drops a URL and wants fast signal.
  Also triggers when the user just shares a URL or article text with no instruction
  and speed or brevity is implied. Works for any domain.
---

# Article Lens Quick — 2-Minute Read Skill

Produce the sharpest possible digest of any article. Hard ceiling: **2 minutes of reading**
(~480 words at average adult reading speed). Every word earns its place or gets cut.

---

## Step 0 — Acquire the Content

**If a URL is provided:**
- Call `web_fetch` immediately. Do not ask the user to paste the text.
- If fetch fails (paywall, bot-block): say "Couldn't fetch the page — paste the article text and I'll run the digest." Stop.

**If raw text is pasted:**
- Use it directly. No `web_fetch`.

**If both exist:** use the pasted text.

---

## Step 1 — Pre-flight (internal, silent)

Before writing, silently note:
- **Content type** — opinion/essay, tutorial, announcement, research summary, case study, listicle
- **Author expertise** — practitioner, academic, journalist, enthusiast
- **Target audience** — beginner, intermediate, senior practitioner

Do not output this. Do not ask anything. Proceed directly to output.

---

## Step 2 — Output Structure

Three sections, in order, separated by `---`. No preamble, no closing.

**Before the first section**, one metadata line:

> 📖 **2 min read** · *Article title or inferred topic*

Do not calculate — always show "2 min read" as the fixed label. This is the quick variant.

---

### 🧭 Summary
*3 sentences maximum. No exceptions.*

Sentence 1: the core thesis — what the article argues or shows.
Sentence 2: why it matters or what problem it addresses.
Sentence 3: the key caveat or constraint the author acknowledges (skip if none).

Pure prose. No bullets.

---

### 🔑 Key Points
*3–5 bullets. One sentence each — no second sentences.*

- Highest-signal points only. If a point could be inferred from another, cut it.
- Order by importance, not article order.
- No qualifications unless they change the meaning materially.
- Strictly from the article. No external context.

---

### ⚡ Actions & Suggestions
*1–2 bullets. One sentence each.*

- The single most actionable takeaway from the article for a senior reader.
- A second only if it's genuinely distinct and high-value. If in doubt, cut it.
- Grounded in something the article explicitly says or demonstrates.

---

## Hard Limits

- **480 words total maximum** — count ruthlessly, cut from Key Points first if over.
- **No nested bullets** at any level.
- **No bold** except for named concepts or terms.
- **No headers** beyond the three section headers.
- **No editorializing** — every claim traces back to the article.
- Thin article (< 400 words): note it in one line before Summary, reduce Key Points to 2–3.

---

## Edge Cases

- **Non-article URL** (repo, docs, landing page): adapt, note content type beside the title in the metadata line.
- **Multi-language content**: respond in the user's message language.