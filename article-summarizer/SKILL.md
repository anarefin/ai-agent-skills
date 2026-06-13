---
name: article-summarizer
description: >
  Deep-read any article, blog post, or web page and produce a structured expert analysis:
  concise summary, key bullet points, reader action items, and domain-adaptive expert commentary.
  Use this skill whenever the user shares a URL
  (Medium, Substack, dev.to, HN, any blog) or pastes article/post content and asks to
  "summarize", "analyse", "break down", "review", "read this", "what do you think of this",
  "give me the key points", "TL;DR this", or similar. Also trigger when the user drops a
  raw URL without any instruction — assume they want the full analysis. Works for any domain:
  engineering, product, finance, science, design, business, etc.
---

# Article Lens Skill

Produce a fast, deep, expert analysis of any article or web page. Target reading time for
the output: **2–3 minutes** (shoot for this; 5 minutes is a hard ceiling — cut ruthlessly).

---

## Step 0 — Acquire the Content

**If a URL is provided:**
- Call `web_fetch` on the URL immediately. Do not ask the user to paste the text.
- If `web_fetch` fails (paywalled, bot-blocked): tell the user briefly and ask them to paste the text. Do not stall.

**If raw text is pasted:**
- Use it directly. Do not call `web_fetch`.

**If both URL and pasted text exist:** use the pasted text (it may already be the cleaned body).

---

## Step 1 — Domain Detection & User Confirmation (interactive)

After acquiring content, infer the following **silently** (do not output this block):

1. **Author's apparent expertise level** — practitioner, academic, journalist, enthusiast
2. **Target audience the author wrote for** — beginner, intermediate, senior practitioner
3. **Content type** — opinion/essay, tutorial/how-to, news/announcement, research summary, case study, listicle

Then infer **2–5 candidate domain labels** that best describe the article's subject matter.
Think in terms of specific, meaningful domains — not vague categories.

**Good domain label examples:**
- Distributed Systems, Event-Driven Architecture, Consensus Algorithms
- LLM Fine-tuning, Retrieval-Augmented Generation, AI Agents
- SaaS Pricing Strategy, Product-Led Growth, Churn Analysis
- Kubernetes Internals, eBPF, Platform Engineering
- DeFi Protocols, Tokenomics, Smart Contract Security
- Organizational Design, Engineering Management, Team Topologies

**Then STOP and present the domain candidates to the user** using the `ask_user_input_v0` tool:
- Question: "Which domain lens should I use for the Expert Lens? (pick one or more)"
- Type: `multi_select`
- Options: your 2–5 inferred domain labels + one fallback option: "General / Let Claude decide"
- Include a brief one-line context before the tool call, e.g.:
  "I detected this article touches on a few domains — pick the lens(es) you want the Expert commentary to use:"

**Wait for the user's selection before proceeding to Step 2.**

Once the user responds:
- Use the selected domain(s) to calibrate the Expert Lens persona and angle.
- If multiple domains are selected, address each briefly in the Expert Lens (still max 2 paragraphs total — be tighter per domain).
- If the user picks "General / Let Claude decide", use the primary inferred domain.
- Do not re-state the user's selection back to them — just proceed directly to the output.

---

## Step 2 — Output Structure

Render the following sections **in order**, in markdown, inline in chat.
Use a horizontal rule (`---`) between sections. Keep the whole response tight.

**Before the first section**, output a single metadata line:

> 📖 **Reading time:** X min · *Article title or inferred topic*

Calculate reading time from the source article word count at ~238 words/minute (average adult).
Round to the nearest half-minute. Format: "3 min", "4.5 min", "7 min". Do not show the word count.

---

### 🧭 Summary
*One tight paragraph. 4–6 sentences max.*

- Lead with **what** the article argues or demonstrates — the core thesis.
- Include the **so-what**: why this matters in context of the domain.
- Note any significant **caveats or gaps** the author acknowledges.
- Do NOT list bullet points here. Pure prose.

---

### 🔑 Key Points
*5–9 bullets. Each bullet is 1–2 sentences — substantive, not paraphrased headers.*

Rules:
- Each bullet must carry information that would be **lost** if removed — no filler.
- Preserve nuance: if the author made a qualified claim, preserve the qualification.
- Order by importance, not by article order.
- If the article is a listicle, distill and synthesize — do not echo the list.

---

### ⚡ Actions & Suggestions

- 2–4 concrete, specific actions the reader should consider taking after reading this.
- Calibrated to someone senior in the domain — skip "learn the basics" type suggestions.
- Ground each action in something specific from the article.

---

### 🧠 Expert Lens
*Adopt the persona of a seasoned expert in the **user-selected domain(s)**. One sharp, opinionated take —
not a book report.*

Pick **exactly one** of the following angles per selected domain (the most revealing for this article):

- **Production/real-world gap**: What breaks down when this hits reality at scale?
- **Unstated assumptions**: What must be true for this to hold? Are those assumptions safe?
- **Trade-off glossed over**: What did the author sacrifice to make the argument clean?
- **Dissenting position**: How would a credible expert who disagrees frame their objection?
- **Historical context**: Has this been tried before? What actually happened?

Write **1–2 paragraphs total** regardless of how many domains were selected. If multiple domains,
weave them together or address each in a tight sentence or two — do not write separate blocks per domain.
Dense, not padded. Cut if it isn't adding something the other sections missed.

---

## Formatting Rules

- **No nested sub-bullets** — two levels max, and use second level sparingly.
- Use `**bold**` for key terms or named concepts only — not for decoration.
- No headers beyond the sections above (Reading time, Summary, Key Points, Actions, Expert Lens).
- Do not add a preamble ("Here is my analysis of…") or a closing ("I hope this helps…").
- Do not re-state the user's domain selection or narrate the skill's internal process.
- If the article is thin (< 400 words or a pure announcement), say so briefly before the summary
  and scale down Key Points to 3–5 bullets; skip the Expert Lens or note it's not warranted.

---

## Length Calibration

| Content type       | Target output length |
|--------------------|----------------------|
| Short post / essay | 350–500 words        |
| Standard article   | 500–750 words        |
| Long-form / deep   | 750–1000 words       |
| Research summary   | 750–1000 words       |

Stay under 800 words for the full output in almost all cases. If you're going over, cut from
Key Points and Expert Lens first — preserve the Actions section.

---

## Edge Cases

- **Paywall / fetch failure**: Say "Couldn't fetch the page — paste the article text and I'll run the analysis." Nothing more.
- **Non-article URL** (e.g., GitHub repo, docs page, landing page): Adapt gracefully. Note the content type at the top of Summary.
- **Very technical paper** (arXiv, academic): Expert Lens should lean into methodology critique and replication concerns.
- **Opinion/hot-take piece**: Weight the "Dissenting position" angle in Expert Lens.
- **Multi-language content**: Respond in the same language as the user's message, not the article's language, unless the user asks otherwise.