---
name: ears-gap-fix
description: Third-pass gap closer for an EARS specification file produced by /springboot-to-ears. Given just the EARS file, reads the controller path(s) from the file's own `Source Controller(s)` header, re-walks the controller's full call chain, and finds anything that exists in the source code but is MISSING from the EARS file — business rules AND data-model elements (entity properties, enum states). It writes a reviewable GAP REPORT and — only after the user approves — applies fixes: unambiguous rules become code-free EARS statements in the right module; a missing entity/property or enum-state becomes a new or extended `### <Name>` block in Domain Entities / Domain Concepts (plus any rule-bearing fields as statements); ambiguous ones become [NEEDS REVIEW] Open Questions in the resolve-open-questions footer format. Each `## Module:` and content `### Subsection` carries a `> **Source files:**` annotation (springboot-to-ears Rule 14) which this skill reads, uses as a supplemental locate hint, preserves, and keeps accurate; it also refreshes the Extraction Summary including its rule-site coverage rows and per-file ledger. Trigger when the user types `/ears-gap-fix <path-to-EARS-file>` (controller path(s) may be passed as an optional override).
---

# EARS Gap-Fix Skill (find + fix missing-from-EARS business rules)

You are closing the coverage gap between a Spring Boot controller's source code and an EARS
specification file that was reverse-engineered from it by `/springboot-to-ears`. The EARS file is
**deliberately code-free** in its body (no inline citations, no source-file index), but its header
preamble records the controller(s) it was generated from in a `> **Source Controller(s):**` line.
This skill reads that header to recover the controller path(s) and re-walks the code to find every
business rule — and every data-model element — the EARS file failed to capture. (The user may still
pass controller path(s) at invocation to override the header.)

The input EARS file follows the **current `/springboot-to-ears` output format**: every `## Module:`
heading and content `### Subsection` carries a `> **Source files:**` blockquote annotation (Rule 14);
the data model lives in dedicated `## Domain Entities and Properties` and `## Domain Concepts and
States` reference sections (each a set of `### <Name>` blocks); the file ends with a richer
`## Extraction Summary`, a `## Business Rules Summary`, and the two `## Review by Developer` sections
that belong to `fix-dev-reviews`. The EARS **statements** stay code-free — file paths appear in the
body **only** inside `> **Source files:**` annotations and Open-Question footers.

This skill does **two tasks in two gated phases**:

1. **Find** — scan the controller's full call chain, build an inventory of every business rule and
   every catalog element (entity property, enum state), diff it against the EARS prose and the
   Domain Entities/Concepts blocks, and write a `GAP REPORT` of items present in code but **missing**
   from the spec. Then **STOP** and wait for the user.
2. **Fix** — only on the user's approval, apply the approved gaps to the EARS file (confident rules as
   new code-free EARS statements; confident structural gaps as a new/extended `### <Name>` block plus
   rule-bearing fields as statements; ambiguous ones as `[NEEDS REVIEW]` Open Questions), then refresh
   the Extraction Summary.

**Scope is missing-only.** This skill reports rules **and data-model elements** that are in the code
but have **no** corresponding EARS statement or catalog row. It does **not** report "orphan" EARS
statements (in spec, not in code) and does **not** report value "mismatches" (a statement that exists
but cites a wrong constant). Those are explicitly out of scope.

**Companion skills (all in this project's `.claude/skills/`):**
- `springboot-to-ears` — produced the EARS file. This skill reuses its extraction rules by
  reference. Read `.claude/skills/springboot-to-ears/SKILL.md` for the cited Steps/Rules/Procedures.
  Note: that skill now auto-resolves its *own* Open Questions on the first pass (its Step 6.5), so a
  fresh EARS file usually arrives here with only genuinely-unresolvable `[NEEDS REVIEW]` residue.
- `resolve-open-questions` — the manual/later-pass resolver. It consumes the `[NEEDS REVIEW]` Open
  Questions **this** skill adds (and any human-added breadcrumbs); run it after this skill's Phase 2
  to chase the new questions.
- `fix-dev-reviews` — the developer-seeded counterpart. Where this skill *discovers* missing rules
  and data-model elements by re-walking the controller, `fix-dev-reviews` applies findings a
  developer recorded by hand in the spec's two `## Review by Developer` sections. It reuses this
  skill's Step 1 gates and Step 2a large-file protocol by reference; this skill **reciprocally
  mirrors** its structural `### <Name>` block building (its Step 3) and its Rule 14 `> **Source
  files:**` annotation upkeep (its Step 5). This skill never reads, consumes, or modifies the two
  `## Review by Developer` sections — those belong to `fix-dev-reviews`.

Never read or rely on skills outside this repository.

---

## Step 1 — Invocation Contract & Validation Gates

**Invocation:**

```
/ears-gap-fix <path-to-EARS-file.md> [<Controller.java> ...]
```

The first (and only required) argument is the EARS file. Any trailing arguments are controller
source files passed as an **optional override**; when supplied, they replace the header-parsed set
entirely. Validate before doing any work and exit early with the matching message. Do **not**
auto-discover or guess a controller when none can be resolved.

**Resolve the controller set (after the EARS file/`.md` gates pass, before scanning):**

1. If the user passed one or more controller arguments, that arg list **is** the controller set —
   use it verbatim and ignore the header.
2. Otherwise, locate the `> **Source Controller(s):**` line in the EARS header preamble and extract
   every backtick-wrapped, comma-separated project-relative path. That list is the controller set.
3. Never scan the repo to guess a controller. If the header line is absent (and no args were
   given), or any resolved path does not exist on disk, exit with the matching message below.

| Condition | Exit message |
|-----------|--------------|
| No arguments at all | `Usage: /ears-gap-fix <path-to-EARS-file.md> [<Controller.java> ...]` |
| EARS path missing or not a file | `EARS file not found: <path>` |
| EARS path is not a `.md` file | `Expected a Markdown EARS file; got <path>` |
| EARS file has no `> **Source Controller(s):**` header line, and no controller args were supplied | `<path> has no "Source Controller(s)" header — cannot determine which controller to gap-check. Pass one explicitly: /ears-gap-fix <EARS.md> <Controller.java>` |
| A resolved controller path (from the header or from args) does not exist on disk | `Controller file not found: <path>` |
| EARS file has no `## Module:` section AND no `## Extraction Summary` | `<path> does not look like a /springboot-to-ears output (no Module / Extraction Summary section) — nothing to gap-check.` |

When the gates pass, read the EARS file end-to-end once so you know exactly which rules it already
states and which `## Module:` / `###` subsections exist. While reading, also record:

- the `## Domain Entities and Properties` and `## Domain Concepts and States` reference sections and
  the `### <Name>` blocks already under them (and which properties / states each block lists) — this
  is the baseline for **structural** gap detection (Step 3);
- every `> **Source files:**` blockquote annotation on each `## Module:` heading, content
  `### Subsection`, and `### <Name>` reference block (springboot-to-ears Rule 14) — these are a
  supplemental locate hint (Step 2/3), a placement cross-check (Step 3), and the annotation-upkeep
  target (Step 5);
- the location of the two `## Review by Developer` sections — this skill **never** reads their entries
  or modifies them (it re-walks the controller; it does not consume developer-seeded findings).

Derive `<Domain>` from the EARS title
(e.g. `# Loan Proposal — OTC Business Requirements Specification (EARS)` → `Loan Proposal — OTC`).

---

## Step 2 — Phase 1: Build the Expected-Requirement Inventory (the scan)

Trace each resolved controller's complete call chain and enumerate every business rule the system
enforces. **Reuse `springboot-to-ears` methodology — do not invent a parallel one.** Apply, by
reference, against the resolved controller set (Step 1) only — not their siblings:

- **`Step 0` orientation**, for the parts that lie in this controller's call chain only: abstract
  base entities (`Step 0b`), `@ControllerAdvice` handlers (`0c`), aspects (`0d`), filters (`0e`),
  security config + access-control library (`0f`, Procedure D), i18n message files (`0h`), the
  **full enum scan** (`0l`), and ID/number generators (`0m`).
- **`Step 2a–2i`** to follow endpoints → services (read the `*Impl`, not the interface) → lib
  validators (Procedure A) → injected sub-validators (recursively, Procedure A-4) → JPA repos /
  JDBC DAOs (Procedure C / Step 2d) → row mappers → Feign/ERP/external calls → ApplicationEvents →
  DTO field-level constraints (`Step 2h`).
- **`graphify`** (a `graphify-out/` graph exists): run `graphify query "<concept>"` /
  `graphify path "<A>" "<B>"` to confirm call edges cheaply **before** deep-reading a file, so you
  follow the real chain and don't miss a delegate.
- The **per-heading `> **Source files:**` annotations** the spec already carries (Rule 14) are a
  cheap cross-check: a module/subsection's listed files tell you which source feeds which section,
  which both confirms your chain-walk reached the right files and pre-resolves where a found gap
  belongs (Step 3 placement). Treat them as a supplemental hint, never as the authoritative chain.
- The **catalog baseline**: the spec's `## Domain Entities and Properties` and `## Domain Concepts
  and States` blocks are the data-model the extraction already captured. As you read each entity
  (`Step 2c`) and run the full enum scan (`Step 0l`) the call chain already requires, hold the catalog
  alongside so Step 3 can diff persisted fields and enum values/states against it.
- The **"named-not-read" prohibition (`Step 2i`)**: if you name a method, helper, validator,
  sub-validator, enum, or generator, you must open and read its body before relying on it.

**Inventory item shape.** Each item is **one atomic, rule-bearing construct** — never collapse or
summarize (springboot-to-ears Rule 3). For each, record:

- `source` — `file:line` (or `file:start-end`) where the rule lives;
- `kind` — one of: rejection/guard (`if`/`else if`/`case` that throws or returns an error),
  endpoint, field-constraint, state-transition, async-side-effect, integration-call, access-rule,
  generated-id-format, **catalog-element** (a persisted entity property, or an enum value/state —
  the unit of a structural gap, Step 3);
- `condition` — the exact code condition / trigger;
- `message` — the verbatim i18n message or string literal if the rule produces one (Rule 5);
- `entity` — the exact reference entity/field that supplies the comparison value (Rule 4, e.g.
  "loan product **details**" vs "loan product **policy**" — they are distinct records).

For a `catalog-element` item, also record the owning entity/enum class and the business-term name of
the property or state (Rule 4: "Proposed loan amount", never `proposedLoanAmount`), its business type
(Amount / Text / Number / Boolean / Date / Reference / Enum / List), and any rule-bearing trait (a
default, a required/optional constraint, a computed/derived value, an enum-state default).

`message` and `entity` are your strongest matching anchors in Step 3, because the EARS file quotes
i18n messages verbatim and names the exact reference entity.

### Step 2a — Large-File Extraction Strategy (MANDATORY; files up to ~10,000 LOC)

This is the heart of the skill. The whole reason it exists is that large validators
(e.g. `BufferLoanProposalValidatorImpl`, `StandardBufferLoanProposalValidatorImpl`) get partially
read and rules get silently dropped. A large file must be read **in full** with **zero skipped
rules**. Use this *structural-index-first, ledger-verified* protocol (it extends
`springboot-to-ears` Step A-2.1, which is the floor):

**i. Measure first — always, before the first `Read`.** Run `wc -l <file>` and record total `T`.
   State it in your notes. Any file with `T > 500` enters this protocol; `T > ~1500` (the
   single-`Read` truncation point) makes it non-negotiable.

**ii. Build a structural index with one cheap grep pass (no reading yet).** This makes coverage
   deliberate instead of luck-based:
   ```
   grep -nE 'public |private |protected | void | boolean |^\s*(if|else if|case|default)\b|throwError|throwErrorByMessage|throw new |return (false|null)|@(Get|Post|Put|Delete|Request|Patch)Mapping|@Scheduled|@KafkaListener' <file>
   ```
   From the output build two maps, each with line numbers:
   - **method map** — the start line of every method (the modifier/signature lines);
   - **rule-site map** — every `if` / `else if` / `case` / `throw` / `throwError` line.
   These two maps are the file's completeness baseline.

**iii. Read by method range, not by arbitrary windows.** Walk the method map in order; for each
   method, `Read` from its start line to the next method's start line, plus a ~30-line overlap so a
   body that closes just past the boundary is still fully seen. Only when method boundaries are
   genuinely unclear, fall back to fixed windows — and then overlap them by ~50 lines and extend
   the schedule until a chunk includes line `T`.

**iv. Recurse with no depth limit.** When a method calls a private helper, read that helper fully
   (Procedure A-3). When it delegates to an injected sub-validator/sub-service, open that concrete
   `*Impl` and run this same protocol on it (Procedure A-4). A helper or `validate()` defined in a
   **superclass in another file** is a separate-file lookup — open that file and run the protocol
   there. "Lives beyond the read window" is never a valid reason while unread lines remain (see vi).

**v. Keep a completeness ledger per file.** Maintain a checklist:
   - every **method-map** entry marked `READ`;
   - every **rule-site-map** line marked either `EXTRACTED → inventory item #N` or
     `EXTRACTED → not a rule` (e.g. a guard that branches but never rejects/throws).
   The file's scan is **not done** until *every* rule-site line is accounted for **and** your last
   read reaches the class's closing brace at/after line `T`. Carry the ledger totals into the GAP
   REPORT header, e.g. `BufferLoanProposalValidatorImpl: 412 rule-sites · 412 accounted · 0 unread`.

**vi. Hard prohibition.** It is forbidden to raise a `[NEEDS REVIEW]` (or skip a rule) with a
   reason like "method body beyond the read window", "file too large to fully extract", or
   "could not be read in one pass" while the file still has unread lines. The truncation reminder
   is a paging instruction ("Call Read with offset=N…"), not a stopping point. Read more chunks.

**vii. Context-safety option for the largest files.** If several ~10K-line files would otherwise
   swamp your context, you MAY delegate **one large file per subagent** (Agent tool) whose sole job
   is to return that file's structured inventory (`file:line` · kind · condition · verbatim message
   · reference entity) **plus its completeness ledger**. Give the subagent this exact protocol
   (ii–vi) and require the ledger back so you can trust coverage without re-reading. Keep the
   diff-against-EARS step (Step 3) in the main agent. This is an efficiency lever only — it never
   licenses skipping lines, and a subagent that returns `unread > 0` must be sent back to finish.

---

## Step 3 — Phase 1: Diff the Inventory Against the EARS File (missing-only)

For each inventory item, decide whether the EARS file already expresses it. The EARS file is
code-free prose, so matching is **semantic**, anchored on the signals springboot-to-ears
guarantees, in priority order:

1. **Verbatim i18n message** — if the item has a `message`, search the EARS text for that exact
   quoted string. A match is near-conclusive that the rule is captured.
2. **Exact reference entity + condition** — match the `entity` (Rule 4 precision: "loan product
   details" ≠ "loan product policy") together with the condition direction (exceeds / below /
   missing / duplicate) and the response verb (reject / set status / require role).
3. **Behavioural paraphrase** — for rules without a message, look for a statement whose trigger and
   response mean the same thing, even if worded differently.

A rule inventory item with **no** expressing statement anywhere in the file is a **MISSING gap**.
(If a statement exists but looks value-wrong, that is a mismatch — **out of scope**; do not report
it. If an EARS statement has no code behind it, that is an orphan — **out of scope**.)

**Structural diff (catalog-element items).** In parallel, diff the data model the code actually
defines against the spec's reference sections:

- for each entity reached, compare its persisted fields against the matching `### <Name>` block in
  `## Domain Entities and Properties` — **excluding** the shared audit, soft-delete, and
  optimistic-locking fields, which are described once under Cross-Cutting → Audit and Record
  Lifecycle and are deliberately not repeated per entity;
- for each enum reached, compare its values/states against the matching `### <Name>` block in
  `## Domain Concepts and States`.

A persisted field or an enum value/state with **no** corresponding row is a **structural gap**:

- if a `### <Name>` block for that entity/enum **already exists**, the gap is a **row addition** to
  that block — never a duplicate block (mirror `fix-dev-reviews` Step 2);
- if **no** block exists for it, the gap is a **new `### <Name>` block** — sub-type `entity` (→
  Domain Entities) or `concept` (enum/state → Domain Concepts). If the target section is genuinely
  absent from the file, **downgrade the gap to ambiguous** (Open Question); never invent a top-level
  section.

Classify each gap, mirroring `fix-dev-reviews` Step 3:

- **confident rule** — the rule and its values/messages are unambiguous from the source. You can write
  a finished, code-free EARS statement now. Choose the EARS pattern via springboot-to-ears `Step 4`
  priority (Event-Driven > State-Driven > Unwanted Behaviour > Optional > Ubiquitous > Complex);
  most validator rejections are Unwanted Behaviour (`If …, the <Domain> system shall reject …`).
  Quote any i18n message verbatim. No IDs, no bullets, no code references (Rule 2).
- **confident structural** — the entity/enum is located and its shape is unambiguous. You can build a
  finished `### <Name>` block (full property/state table) or row addition now. Any **rule-bearing**
  field (a default, a required/optional constraint, a computed/derived value, an enum-state default)
  also yields a derived code-free statement; pure data-shape fields contribute only their table row.
- **ambiguous** — the rule exists but its value/intent cannot be pinned from code alone (config- or
  profile-driven, seeded in Flyway/DB, depends on an external constant you could not locate after
  applying the Rule 9 gates), **or** a structural gap whose entity/enum class cannot be located or
  whose meaning cannot be pinned, **or** a structural gap whose target reference section is absent.
  Propose a `[NEEDS REVIEW]` Open Question with **both** Rule 8 footers.

For every gap also resolve its **target location**:

- a **confident rule** lands in the existing `## Module:` and `###` subsection where the statement
  belongs (honor springboot-to-ears Rule 7 placement — Validation Rules module for validator
  branches, Sub-Validators module for sub-validator rules, Async module for side effects, etc.); a
  cross-cutting concern lands in the matching `## Cross-Cutting Requirements` subsection (note these
  subsections carry **no** `> **Source files:**` line — a Rule 14 exclusion). Use a subsection's
  `> **Source files:**` list as the placement confirmation signal: the subsection whose listed files
  include the gap's source file is its natural home;
- a **confident structural** gap lands in `## Domain Entities and Properties` (entity) or `## Domain
  Concepts and States` (concept); its derived statements are placed by Rule 7 like any rule gap.

**Never invent a new top-level section.** If no subsection fits, prefer the closest existing one and
note it; do not create new module headings. `## Business Rules Summary` and the two `## Review by
Developer` sections are **not** edit targets.

---

## Step 4 — Phase 1: Write the GAP REPORT, then STOP at the approval gate

Write the report to `docs/ears/<Domain>-GAP-REPORT.md` (overwrite if present). Use this format:

```
# <Domain> — EARS Gap Report

Source EARS: <ears-path>
Controllers scanned: <controller path(s), comma-separated>
Generated: <Day, DD Month YYYY>

## Coverage
- Rules inventoried: <N>
- Already covered in EARS: <C>
- Missing (gaps below): <G>   (confident rule: <Gc> · confident structural: <Gs> · ambiguous: <Ga>)

## Large-file ledgers
- <File>.java (<T> LOC): <sites> rule-sites · <accounted> accounted · <unread> unread
- … one line per scanned file > 1500 LOC …

---

## GAP-001  [MISSING · rule · confident]
Target: Module: <…>  ›  ### <…>
Source: src/main/java/.../<File>.java:1820-1834
Code condition: if (dto.getX() > policyDetails.getMaxX()) throwError("<verbatim message>")
Proposed EARS statement:
> If the requested ... exceeds the configured maximum on the loan product details, the
> <Domain> system shall reject the request with the message "<verbatim message>".

## GAP-002  [MISSING · structural · confident]
Target: ## Domain Entities and Properties  ›  ### <Name>   (new block | row add)
Source: lib/shared-dto/src/main/java/.../<Name>Dto.java
Proposed entity/concept block:
> ### <Name>
> > **Source files:** `lib/shared-dto/src/main/java/.../<Name>Dto.java`
> <one-line description>
> | Property | Type | Meaning | Constraints |
> |----------|------|---------|-------------|
> | <… every property, audit/soft-delete/version fields excluded …> | | | |
Proposed derived statement(s) (rule-bearing fields only):
> When a new loan proposal is submitted, the <Domain> system shall … → Module: <…> › ### <…>

## GAP-003  [MISSING · ambiguous]
Target: Open Questions
Source: src/main/java/.../<File>.java:245
Why ambiguous: <one line — what value/intent could not be determined and which gates were tried>
Proposed Open Question:
> N. **[NEEDS REVIEW]** <concrete question a domain expert can answer in 1–2 sentences>
>    *Where agent looked:* `<file>:245` — <what was read and why insufficient>.
>    *Hint for reviewer:* Likely answer in `<probable/file>` (<reasoning>). Try `<grep/find/graphify command>`.

…
```

Then print a stdout summary (≤ 12 lines): the coverage numbers, the ledger totals, and the count of
confident-rule vs. confident-structural vs. ambiguous gaps. **Do not edit the EARS file in this
phase.** End the turn by asking
the user to review `docs/ears/<Domain>-GAP-REPORT.md` and reply with exactly one of:

- `apply all` — apply every gap in the report;
- `apply GAP-003 GAP-007 …` — apply only the listed gaps;
- `abort` — make no changes.

Phase 2 runs only after the user gives one of these in the conversation.

---

## Step 5 — Phase 2: Apply the Approved Fixes

Run only when the user has approved (all or a subset). Apply **only** approved gaps. Mirror the
surgical editing discipline of `resolve-open-questions` (Step 5–6):

- **confident rule gap** → insert the proposed statement as a standalone prose paragraph (blank line
  separated) into its target `###` subsection, in springboot-to-ears Rule 2 style: complete
  sentence, subject `the <Domain> system`, no ID, no bullet, no code reference, i18n quoted
  verbatim. Place it logically (e.g. after related rejection paragraphs in the same subsection).
  Then, **annotation upkeep (Rule 14):** if the gap's source file is not already listed in that
  subsection's `> **Source files:**` blockquote, append it (comma-separated, backticked,
  project-relative, preserving existing order). Touch **only** the target subsection's annotation;
  never reorder or rewrite existing entries; never add a `> **Source files:**` line to a section that
  lacks one (the Cross-Cutting subsections and summary sections deliberately have none).
- **confident structural gap** → if the gap is a **new block**, insert the proposed `### <Name>`
  block (carrying its own `> **Source files:**` line) into its target section (`## Domain Entities
  and Properties` for entity, `## Domain Concepts and States` for concept), placed logically after
  related blocks or appended at the section end. If the gap is a **row addition** to an existing
  block, insert just the new `| Property | … |` / state row into that block's table (and append the
  gap's source file to the block's `> **Source files:**` line if missing). Then insert each
  **derived statement** into its module exactly like a confident rule gap above, applying the same
  per-subsection annotation upkeep for each.
- **ambiguous gap** → append a new numbered item to `## Open Questions`, continuing the existing
  numbering, with `**[NEEDS REVIEW]**` and **both** mandatory footers (`*Where agent looked:*` and
  `*Hint for reviewer:*`) exactly as springboot-to-ears Rule 8 requires, so `/resolve-open-questions`
  can act on it next. (Open-Question gaps touch no `> **Source files:**` annotation.)
- **Refresh `## Extraction Summary`** (the current table format). Overwrite only the right-hand count
  cells / ledger lines; never restructure the table:
  - **Statement pattern rows** — recount EARS statements by leading word against the current row
    labels: `When `/`After `→ `Event-Driven (`When` + `After`)`, `While `→ `State-Driven (`While`)`,
    `If `→ `Unwanted Behaviour (`If`)`, `Where `→ `Optional (`Where`)`,
    `The <Domain> system shall `→ `Ubiquitous (`The <Domain> system shall`)`,
    `While … when `→ `Complex (`While … when`)` — and update `Total EARS statements` accordingly.
  - **Marker rows** — recount `[NEEDS REVIEW] items`, `[DISABLED] items`, `[UNRESOLVED] items`.
  - **Rule-site coverage rows** — refresh `Rule-sites inventoried`, `Rule-sites covered by a
    statement`, and `Rule-sites uncovered` from **this run's** scan inventory and the gaps just
    applied (a confident gap applied moves a rule-site from uncovered to covered).
  - **Per-file coverage ledger** — update the `**Per-file coverage ledger**` bullet list from this
    run's large-file ledgers (one line per source file > ~500 LOC scanned), so its `accounted` /
    `uncovered` figures reflect the post-apply state.
  - A new entity/concept **block** (or row addition) adds no EARS statement, so it does not move the
    pattern counts; its **derived** statements do, counted by their leading word like any other.
  - Update the `**Extraction completed:**` line to today's date in `<Day, DD Month YYYY>` format.
  - If the file has no `## Extraction Summary`, skip this (do not invent one); refresh only the rows
    and ledger lines that actually exist.

Print a stdout summary (≤ 12 lines): statements added (per target module), entity/concept blocks (or
rows) added, `> **Source files:**` annotations updated, Open Questions added, and gaps skipped
because the user did not approve them.

---

## Step 6 — Idempotency & Edge Cases

| Case | Behaviour |
|------|-----------|
| Re-run after applying fixes | A gap whose rule (or catalog row) is now expressed in the EARS file must **not** be reported again. Phase 1 is a no-op for already-closed gaps. |
| Controller's call chain can't be traced (impl genuinely not found after search) | Record it as an **ambiguous** gap with a Rule 8 footer that states the failed search verbatim — never crash, never silently drop. |
| Multiple controllers share one validator | Inventory that validator **once** (Rule 7 dedupe); do not double-report its rules per controller. |
| Gap's natural home is a module that doesn't exist in the file | Place it in the closest existing module/subsection and note the choice in the report; never add a new top-level `## Module:` section. |
| Structural gap whose `### <Name>` block already exists | Apply it as a **row addition** to that block — never insert a duplicate block. |
| Structural gap whose target section (`## Domain Entities and Properties` / `## Domain Concepts and States`) is absent | **Downgrade to ambiguous** (Open Question); never invent the top-level section. |
| Structural gap whose entity/enum class can't be located, or whose shape/meaning can't be pinned | Treat as **ambiguous** — propose a `[NEEDS REVIEW]` Open Question with a Rule 8 footer; never emit a guessed/partial block. |
| Unsafe shell during scanning (paths outside repo, destructive flags) | Never run it. Find another lead, or mark the item ambiguous. |
| Review by Developer sections present in the file | This skill never reads, consumes, or edits them (they belong to `fix-dev-reviews`). |
| User approves a subset | Apply exactly those GAP IDs; leave the rest reported but unapplied. |

---

## Step 7 — Self-Review Checklist (before ending each phase)

**Phase 1 (report):**
- [ ] Every scanned file > 1500 LOC has a ledger line with `accounted == sites` and `unread == 0`.
- [ ] Every gap has a `file:line` source proof and a target location.
- [ ] Every confident rule gap's proposed statement is code-free, uses a valid EARS pattern, and
      quotes any i18n message verbatim.
- [ ] Every confident structural gap names a valid target section, proposes either a full `### <Name>`
      block (all properties/states, audit/soft-delete/version fields excluded, with its own
      `> **Source files:**` line) or a single row addition, and lists rule-bearing fields as derived
      statements.
- [ ] Every ambiguous gap's proposed Open Question carries **both** Rule 8 footers.
- [ ] No orphan-EARS or value-mismatch items were reported (out of scope).
- [ ] The EARS file was **not** modified; the report was written; the approval prompt was shown.

**Phase 2 (fix):**
- [ ] Only user-approved gaps were applied.
- [ ] New statements are plain paragraphs in existing subsections (no IDs/bullets/code refs); new
      entity/concept blocks match the reference shape and carry their `> **Source files:**` line; new
      Open Questions are well-formed with both footers.
- [ ] Every applied statement's source file is present in its target subsection's `> **Source files:**`
      line (appended if it was missing); **no other** `> **Source files:**` annotation was modified,
      removed, or reordered.
- [ ] No new top-level sections were invented; the two `## Review by Developer` sections were not
      modified.
- [ ] `## Extraction Summary` reflects this run: statement pattern + marker counts, the rule-site
      coverage rows, and the per-file ledger were all refreshed, and `**Extraction completed:**` is
      today's date.
- [ ] The diff is additive and surgical — only new statements/blocks/rows, the source-file annotation
      appends, and the Summary refresh changed.
