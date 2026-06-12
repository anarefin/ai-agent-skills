---
name: fix-dev-reviews
description: Fourth-pass closer for an EARS specification file produced by /grails-to-ears. Consumes the two developer-review sections a human filled in directly in the spec — `## Review by Developer (code)` (source-code pointers to rules — or whole entities/enums — missing from the spec) and `## Review by Developer (business requirements)` (business decisions needing a human answer). For each unchecked entry it investigates the referenced code, writes a reviewable report, and — only after the user approves — folds confident findings in as code-free EARS statements, adds any missing entity/enum-state as a new `### <Name>` block (with all properties) in Domain Entities / Domain Concepts, and turns ambiguous findings and all business-requirement entries into [NEEDS REVIEW] Open Questions, then checks the entry off and annotates where it landed (module/subsection, entity/concept block, or Open Question) plus the EARS line number. Each `## Module:` and content `### Subsection` in the input carries a `> **Source files:**` annotation (grails-to-ears Rule 14) which this skill preserves, uses as a supplemental locate hint, and keeps accurate. Trigger when the user types `/fix-dev-reviews <path-to-EARS-file>` (entry-point (controller / action service) path(s) may be passed as an optional override).
---

# Fix Developer Reviews Skill (apply human review findings to an EARS file)

You are closing the gap between what a **developer found by reviewing an EARS file against the
codebase** and the EARS specification itself. After `/grails-to-ears` produced the spec, a
developer read it next to the source and recorded findings the extraction missed — directly in the
EARS file, inside two dedicated sections:

- `## Review by Developer (code)` — backticked **source-code pointers** to things that exist in the
  code but are missing from the spec (file, `file#method`, or `file:line-range`), each with an
  optional note and an optional `→ Module:` placement override. A code entry asserts either that a
  **rule** is missing (→ a new EARS statement) or that a whole **entity / enum-state** is missing
  (→ a new `### <Name>` block in Domain Entities / Domain Concepts, plus any rule-bearing fields as
  statements).
- `## Review by Developer (business requirements)` — **business decisions/requirements** the
  developer wants captured that need a human answer (no code expected); optional `| context:`
  pointer and optional `→ Module:` override.

This skill reads those two sections, investigates each unchecked entry, proposes resolutions, and —
**only after the user approves** — applies them and marks each entry done. The EARS **statements**
stay code-free (grails-to-ears Rule 2): no inline citations, no class/method names in statement
prose. File paths do, however, legitimately appear in the body as the per-heading
`> **Source files:**` blockquote annotation that every `## Module:` and content `### Subsection`
carries (grails-to-ears Rule 14) — this skill **preserves** those annotations, consults them as
a supplemental locate hint, and keeps them **accurate** when it inserts new content. The developer's
source pointers themselves live only in the review sections (developer input) and in this skill's
report file.

This skill does **two tasks in two gated phases**:

1. **Find** — parse both review sections, investigate each unchecked entry against the code (driven
   by its pointer), and write a `DEV-REVIEW REPORT` proposing a resolution per entry. Then **STOP**
   and wait for the user.
2. **Fix** — only on the user's approval, apply the approved entries to the EARS file (confident rule
   findings as new code-free EARS statements; confident **structural** findings as a new
   `### <Name>` block — full property/state table — in Domain Entities / Domain Concepts, plus any
   rule-bearing fields as statements; ambiguous findings and all business-requirement entries as
   `[NEEDS REVIEW]` Open Questions), check each applied entry off (`- [ ]` → `- [x]`) with a
   `→ resolved:` annotation that names the landing location **and the EARS line number**, then
   refresh the Extraction Summary.

**Scope is developer-seeded only.** This skill acts on the entries the developer wrote in the two
review sections — nothing else. It does **not** re-scan the whole entry-point call chain to discover
new gaps (that is `ears-gap-fix`), and it does **not** report orphan EARS statements or value
mismatches.

**Companion skills (all in this project's `.claude/skills/`):**
- `grails-to-ears` — produced the EARS file and emits the two empty review-section placeholders.
  This skill reuses its output rules by reference; read
  `.claude/skills/grails-to-ears/SKILL.md` for the cited Rules/Steps/Procedures.
- `ears-gap-fix` — the agent-discovered gap closer. This skill reuses its **Step 1 gates** and its
  **Step 2a large-file extraction protocol** by reference; read
  `.claude/skills/ears-gap-fix/SKILL.md`.
- `resolve-open-questions` — the breadcrumb resolver. Run it after this skill's Phase 2 to chase any
  new `[NEEDS REVIEW]` Open Questions the business-requirement entries produced. This skill reuses
  its Extraction-Summary refresh mechanics (its Step 6) by reference.

Never read or rely on skills outside this repository.

---

## Step 1 — Invocation Contract & Validation Gates

**Invocation:**

```
/fix-dev-reviews <path-to-EARS-file.md> [<EntryPoint.groovy> ...]
```

The first (and only required) argument is the EARS file. Any trailing arguments are entry-point
source files — controllers **or** action services / action classes — passed as an **optional
override** for the entry-point set (used only to scope smart auto-locate, Step 3); when supplied,
they replace the header-parsed set entirely.

**Resolve the entry-point set** exactly as `ears-gap-fix` Step 1 does: if entry-point args were
passed, that list is the set; otherwise read the `> **Source Entry Point(s):**` line in the EARS
header preamble and extract every backtick-wrapped project-relative path. Never scan the repo to
guess an entry point.

Validate before doing any work and exit early with the matching message:

| Condition | Exit message |
|-----------|--------------|
| No arguments at all | `Usage: /fix-dev-reviews <path-to-EARS-file.md> [<EntryPoint.groovy> ...]` |
| EARS path missing or not a file | `EARS file not found: <path>` |
| EARS path is not a `.md` file | `Expected a Markdown EARS file; got <path>` |
| EARS file has no `## Module:` section AND no `## Extraction Summary` | `<path> does not look like a /grails-to-ears output (no Module / Extraction Summary section) — nothing to do.` |
| Neither `## Review by Developer (code)` nor `## Review by Developer (business requirements)` section exists | `<path> has no Review-by-Developer sections — run /grails-to-ears to add the placeholders, or add the sections manually.` |
| Both review sections exist but contain zero entries, or every entry in both is already `- [x]` | `No unprocessed Review-by-Developer entries in <path> — nothing to do.` |
| A resolved entry-point path (header or args) does not exist on disk — *only checked if a note-only / smart-locate entry needs it* | `Entry-point file not found: <path>` |

When the gates pass, read the EARS file end-to-end once so you know which `## Module:` / `###`
subsections exist (including the `## Domain Entities and Properties` and `## Domain Concepts and
States` reference sections and the `### <Name>` blocks already under them) and where the two review
sections sit. Note that each `## Module:` heading and every content `### Subsection` carries a
`> **Source files:**` blockquote line (grails-to-ears Rule 14); **record those lists** — they
are a supplemental locate hint (Step 3), a placement cross-check (Step 3), and the annotation-upkeep
target (Step 5). Derive `<Domain>` from the EARS title (e.g. `# Loan Proposal — OTC … (EARS)` →
`Loan Proposal — OTC`).

---

## Step 2 — Phase 1: Parse Both Review Sections

Within each review section, every list item matching `^- \[[ x]\] ` is one entry. **Skip every entry
already marked `- [x]`** (done on a prior run — do not re-investigate). For each **unchecked**
(`- [ ]`) entry, build a record:

| Field | Source |
|-------|--------|
| `section` | `code` or `business` |
| `pointer` | the backticked code pointer (code section) or the `| context:` pointer (business section), if any. One of: `File.groovy`, `File.groovy#method`, `File.groovy:start-end`, or **none** |
| `note` | the free-text after the pointer / the decision sentence |
| `override` | the module/subsection named after a trailing `→ Module: <Module> › <Subsection>`, if present |
| `kind` | (code entries only) `rule` or `structural` — see the classification below; `structural` is further sub-typed `entity` or `concept` |

Multi-line entries are allowed (the developer may wrap a note); the entry runs until the next
`- [ ]` / `- [x]` line or the next `## ` heading. Record entries in document order. Number them
`DR-001`, `DR-002`, … for the report.

A **code** entry asserts one of two things; classify each by **note wording with a class-shape
fallback**:

- **rule** (default) — "a real rule lives here and is missing from the spec." Produces a new EARS
  statement.
- **structural** — "a whole entity or enum/state is missing from the spec." Treat a code entry as
  `structural` when **either** the note signals a missing entity / domain class / command object or
  enum / state / concept (words like "entity", "domain class", "command object", "enum", "status",
  "states", "add … with its fields/properties"), **or** the `pointer` resolves to a class whose shape
  is structural — a GORM domain class (under `grails-app/domain/`, typically with a `static
  constraints { }` / `static mapping { }` block), a `Command` object that is just fields +
  constraints, or an `enum` / state type (under `.../enums/` or legacy `com/docu/commons/`) — **and**
  no `### <Name>` block for it already exists under `## Domain Entities and Properties` /
  `## Domain Concepts and States`. Sub-type it `entity` (GORM domain class / `Command` object) or
  `concept` (enum / state type). If a matching `### <Name>` block already exists, it is **not**
  structural — handle it as a `rule` entry (a missing field/rule on an existing block), never a
  duplicate block.

A **business** entry asserts "this decision/requirement must be captured", is never structural
(structure is code-discoverable), and is always destined for a `[NEEDS REVIEW]` Open Question.

---

## Step 3 — Phase 1: Investigate Each Entry

Drive the investigation off the entry's `pointer`. **Reuse `ears-gap-fix` Step 2a (the large-file
structural-index + rule-site-ledger protocol) and the `grails-to-ears` "named-not-read"
prohibition (Step 2i) — do not invent a parallel method.**

| Pointer form | How to investigate |
|--------------|--------------------|
| `File.groovy#method` | Resolve the file path (`find . -name File.groovy` / graphify if bare). Open it, jump to that method (or action-lifecycle stage — `preCondition`/`execute`/`postCondition` or `executePreCondition`/`execute`/`executePostCondition`/`build*`), read its full body and every private helper / injected sub-validator / `PluginConnector` call it delegates to (recursively, `grails-to-ears` Procedure A). |
| `File.groovy:start-end` | Read that line span plus the enclosing method, then any helpers it calls. |
| `File.groovy` (whole file) | Run the `ears-gap-fix` Step 2a protocol on the whole file: `wc -l`, build the rule-site map, read by method range, keep a ledger. |
| none (**smart auto-locate**) | Use `graphify query "<note nouns>"` / `grep` keyed on the note's distinctive nouns and any quoted message, with the resolved entry-point set's call chain (controllers → action services → helper services / validators) as the **primary** scope. If the entry has a `→ Module:` override (or its placement is otherwise obvious), additionally consult that section's `> **Source files:**` list as a **supplemental hint** for which files to read first. Read the matched method fully. |

For each entry capture, where applicable: the exact `file:line(-range)`, the precise code condition
/ trigger (an `if`-guarded `Message.ERROR` / `isError = true` return, or a `validator:` closure
rejection), the **verbatim** i18n message or string literal it produces (Rule 5 — the text passed to
`UserMessageBuilder.createMessage(...)` or the resolved message-catalogue key), and the **exact
reference entity/field** that supplies the comparison value (Rule 4 — a GORM domain property, a
`GroovyRowResult` column, or a `Command`/cache value; "loan product details" ≠ "loan product
policy"). These are the anchors for the proposed statement and the report's proof.

**For a `structural` entry, investigate the whole class instead of a single rule-site.** Resolve and
read the pointed class **in full** (reuse `ears-gap-fix` Step 2a large-file protocol if it is large;
obey the `grails-to-ears` "named-not-read" prohibition — never describe a field you did not
read). Capture **every** persisted/serialised field (GORM domain class / `Command` object) or
**every** value/state and transition (enum/state). Map each to **business terms** per
`grails-to-ears` Rule 4 (code-free naming): property names like "Proposed loan amount" — never
`proposedLoanAmount`; Types in business terms (Amount / Text / Number / Boolean / Date / Reference /
Enum / List), never Groovy/Java types. **Exclude** the shared audit, soft-delete, and
optimistic-locking fields (this project's `createdOn` / `createdBy` / `updatedOn` / `updatedBy`, any
soft-delete flag, and the GORM `version`) — they are described once under Cross-Cutting → Audit and
Record Lifecycle and are deliberately not repeated per entity (the Domain Entities section preamble
states this, per `grails-to-ears` Rule 13). While reading, also note any **rule-bearing** field — a
default, a required/optional constraint, a computed/derived value, an enum-state default — for the
derived-statements step.

**Classify each entry:**

- **confident** (`rule` code entries) — the rule and its values/messages are unambiguous from the
  source. You can write a finished, code-free EARS statement now. Choose the EARS pattern by
  `grails-to-ears` Step 4 (EARS Pattern Selection) priority (Event-Driven > State-Driven > Unwanted
  Behaviour > Optional > Ubiquitous > Complex); most action-service rejection branches are Unwanted
  Behaviour (`If …, the <Domain> system shall reject …`). Quote any i18n message verbatim. No IDs, no
  bullets, no code references (Rule 2).
- **confident structural** (`structural` code entries) — the class is located and its shape is
  unambiguous. You can build a finished `### <Name>` block now (full property/state table) plus any
  rule-bearing fields as code-free statements. See the structural build/place rules below.
- **ambiguous** — a `rule` code entry whose value/intent cannot be pinned from code alone
  (`Config.groovy` / `grailsApplication.config`-driven, seeded in a DB script, depends on an external
  constant not locatable after applying the Rule 9 gates), a `structural` entry whose class cannot be
  located or whose meaning
  cannot be pinned, **or** any **business** entry. These become a `[NEEDS REVIEW]` Open Question with
  **both** Rule 8 footers. For a business entry the `*Where agent looked:*` footer records whatever
  context the `| context:` pointer yielded; if there was no pointer, it records that the entry is a
  developer-supplied business decision with no code source.

**Build the structural block (confident `structural` entries).** Follow the reference-file shapes
exactly; each block is a content `### subsection`, so it **must** carry its own `> **Source files:**`
annotation (Rule 14):

- **entity** → target `## Domain Entities and Properties`:
  `### <Entity>` → `> **Source files:** <backticked path(s)>` → a one-line description →
  `| Property | Type | Meaning | Constraints |` table covering **all** properties (audit/soft-delete/
  version fields excluded).
- **concept** → target `## Domain Concepts and States`:
  `### <Concept>` → `> **Source files:** <backticked path(s)>` → an optional one-line description →
  `**<Label>:**` + `| <Name> | Business Meaning |` table, plus a `| From State | To State | Triggered
  by |` transitions table where the type encodes transitions.

**Derive rule-bearing fields into statements.** For every rule-bearing field noted during
investigation, additionally write a code-free EARS statement (Rule 2 prose, valid pattern, i18n quoted
verbatim) and place it in the correct module by Rule 7. Pure data-shape fields contribute only their
table row — no statement.

**Resolve each entry's target location.**
- `rule` / `confident` → if the entry has an `override` (`→ Module:`), use it — unless that
  module/subsection does not exist in the file, in which case fall back to the closest existing
  subsection and note the substitution in the report. Otherwise pick the target by
  `grails-to-ears` Rule 7 placement (`<Domain> Validation Rules` module for business-rule
  validator / check-method rejection branches, `Sub-Validators` for specialised sub-validator action
  services, the relevant async/integration module for post-condition side effects — Rabbit/Mercure
  publishing, automatic vouchers, etc.); use a subsection's `> **Source files:**` annotation as a
  confirmation signal — the subsection whose listed source files include the entry's pointer file is
  its natural home.
- `structural` → the block targets `## Domain Entities and Properties` (entity) or
  `## Domain Concepts and States` (concept); its derived statements are placed by Rule 7 like any
  rule entry. Both sections already exist in `grails-to-ears` output, so adding a `### <Name>`
  subsection is **not** a new top-level section. **If the relevant section is absent, downgrade the
  entry to ambiguous** (Open Question) rather than invent it.

**Never invent a new top-level section.** Ambiguous/business entries target `## Open Questions`.

---

## Step 4 — Phase 1: Write the DEV-REVIEW REPORT, then STOP at the approval gate

Write the report to `docs/ears/<Domain>-FIX-DEV-REVIEWS-REPORT.md` (overwrite if present). Use this
format:

```
# <Domain> — EARS Developer-Review Report

Source EARS: <ears-path>
Entry points in scope: <entry-point (controller / action service) path(s), comma-separated>
Generated: <Day, DD Month YYYY>

## Summary
- Entries found (unchecked): <N>   (code-rule: <Nr> · code-structural: <Ns> · business: <Nb>)
- Confident rule (→ EARS statement): <Gc>
- Confident structural (→ entity/concept block): <Gs>
- Ambiguous / business (→ Open Question): <Ga>

---

## DR-001  [code · rule · confident]
Entry: `CreateMemberInfoAction.groovy#preCondition` — passbook-number uniqueness not captured
Target: Module: <…>  ›  ### <…>     (developer override / agent-chosen)
Source: plugins/mf/src/groovy/com/docu/sbicloud/program/member/CreateMemberInfoAction.groovy:612-628
Code condition: if (existingPassbook) { msg = UserMessageBuilder.createMessage(Message.ERROR, "<verbatim message / key>") }
Proposed EARS statement:
> If the submitted passbook number is already in use by another member, the <Domain> system shall
> reject the registration with the message "<verbatim message>".

## DR-002  [code · entity · confident]
Entry: `Guarantor.groovy` — Guarantor entity missing from the spec
Target: ## Domain Entities and Properties  ›  ### Guarantor   (new block)
Source: plugins/mf/grails-app/domain/com/docu/sbicloud/program/member/Guarantor.groovy
Proposed entity block:
> ### Guarantor
> > **Source files:** `plugins/mf/grails-app/domain/com/docu/sbicloud/program/member/Guarantor.groovy`
> A loan guarantor attached to a member from the member's record.
> | Property | Type | Meaning | Constraints |
> |----------|------|---------|-------------|
> | <… every property from the GORM domain class, audit/soft-delete/version fields excluded …> | | | |
Proposed derived statement(s) (rule-bearing fields only):
> When a member's family-and-nominee information is submitted, the <Domain> system shall … → Module: <…> › ### <…>

## DR-003  [business · open question]
Entry: Should a member's category change be permitted while a write-off recovery is in progress?
Target: Open Questions
Why open: developer-supplied business decision; no single code source determines the intended policy.
Proposed Open Question:
> N. **[NEEDS REVIEW]** <concrete question a domain expert can answer in 1–2 sentences>
>    *Where agent looked:* `<context-file>:<line>` — <what was read> (or: developer-supplied business decision, no code source).
>    *Hint for reviewer:* Likely answer in `<probable/file>` (<reasoning>). Try `<grep/find/graphify command>`.

…
```

Then print a stdout summary (≤ 12 lines): the entry counts (code-rule vs code-structural vs
business), and the confident-rule / confident-structural / ambiguous split. **Do not edit the EARS
file in this phase.** End the turn by asking the user to
review `docs/ears/<Domain>-FIX-DEV-REVIEWS-REPORT.md` and reply with exactly one of:

- `apply all` — apply every entry in the report;
- `apply DR-003 DR-007 …` — apply only the listed entries;
- `abort` — make no changes.

Phase 2 runs only after the user gives one of these in the conversation.

---

## Step 5 — Phase 2: Apply the Approved Entries

Run only when the user has approved (all or a subset). Apply **only** approved entries. Mirror the
surgical editing discipline of `resolve-open-questions` (Step 5–6):

- **confident rule entry** → insert the proposed statement as a standalone prose paragraph (blank-line
  separated) into its target `###` subsection, in `grails-to-ears` Rule 2 style: complete
  sentence, subject `the <Domain> system`, no ID, no bullet, no code reference, i18n quoted
  verbatim. Place it logically (e.g. after related rejection paragraphs in the same subsection).
  Then, **annotation upkeep (Rule 14):** if the finding's source file is not already listed in that
  subsection's `> **Source files:**` blockquote, append it (comma-separated, backticked,
  project-relative, preserving existing order). Touch **only** the target subsection's annotation;
  never reorder or rewrite existing entries; never add a `> **Source files:**` line to a section that
  lacks one.
- **confident structural entry** → insert the proposed `### <Name>` block into its target section
  (`## Domain Entities and Properties` for entity, `## Domain Concepts and States` for concept),
  placed logically (after related blocks) or appended at the section end. The block carries its own
  `> **Source files:**` annotation as built in Step 3. Then insert each **derived statement** into
  its module exactly like a confident rule entry above, applying the same per-subsection annotation
  upkeep for each.
- **ambiguous / business entry** → append a new numbered item to `## Open Questions`, continuing the
  existing numbering, with `**[NEEDS REVIEW]**` and **both** mandatory footers (`*Where agent
  looked:*` and `*Hint for reviewer:*`) exactly as `grails-to-ears` Rule 8 requires, so
  `/resolve-open-questions` can act on it next. (Open-Question entries touch no `> **Source files:**`
  annotation.)
- **Check off and annotate the entry (the audit feature).** After the statement/block/Open Question
  is in place, edit the originating review-section line: flip `- [ ]` → `- [x]` and append, on a
  continuation line indented under it, the resolution annotation:
  - confident rule → `      → resolved: Module: <Module> › <Subsection> (EARS line <N>)`
  - confident structural → `      → resolved: <Domain Entities|Domain Concepts> › <Name> (EARS line <N>)` and, on further continuation lines, one `      → also: Module: <Module> › <Subsection> (EARS line <N>)` per derived statement
  - ambiguous/business → `      → resolved: Open Question <N> (EARS line <M>)`
  Compute the EARS line number **after** the edit lands (so it points at the inserted paragraph,
  block, or new Open Question). When applying several entries, apply edits one at a time and recompute
  line numbers so earlier insertions don't make later annotations stale. The `(EARS line N)` is a
  convenience snapshot — it may drift if the file is later hand-edited.
- **Refresh `## Extraction Summary`** (identical mechanics to `resolve-open-questions` Step 6):
  recount EARS statements by leading word — `If `→Unwanted, `When `/`After `→Event-Driven,
  `While `→State-Driven, `Where `→Optional, `The <Domain> system shall `→Ubiquitous,
  `While … when `→Complex — and recount the marker rows (`[NEEDS REVIEW]`, `[DISABLED]`,
  `[UNRESOLVED]`). Overwrite only the right-hand count cells; the `Total EARS statements` row must
  equal the sum of the pattern rows. Update the `**Extraction completed:**` line to today's date in
  `<Day, DD Month YYYY>` format. If the file has no `## Extraction Summary`, skip this. A new
  entity/concept **block** adds no EARS statement, so it does not move the pattern counts; its
  **derived statements** do, and are counted by their leading word like any other statement.

Print a stdout summary (≤ 12 lines): statements added (per target module), entity/concept blocks
added, Open Questions added, entries checked off, entries skipped because the user did not approve
them.

---

## Step 6 — Idempotency & Edge Cases

| Case | Behaviour |
|------|-----------|
| Re-run after applying | A `- [x]` entry is skipped in Step 2. Phase 1 is a no-op for already-applied entries; only `- [ ]` entries are processed. |
| Pointer's file/method can't be found (after `find`/graphify) | Treat the entry as **ambiguous**: propose a `[NEEDS REVIEW]` Open Question whose `*Where agent looked:*` footer states the failed search verbatim. Never crash, never silently drop. |
| `→ Module:` override names a module/subsection that doesn't exist | Place in the closest existing subsection and note the substitution in the report; never add a new top-level `## Module:` section. |
| Note-only (smart) entry can't be pinned confidently | Becomes an **ambiguous** `[NEEDS REVIEW]` Open Question — never a guessed statement. |
| Malformed entry (no recognisable pointer, note, or decision) | Report it under its own DR id as `[unparseable]`, leave it **unchecked**, and apply nothing for it. |
| Same rule referenced by two entries | Investigate once; in Phase 2 insert the statement once and annotate **both** entries pointing at the same EARS line. |
| Structural entry: class can't be located, or its shape/meaning can't be pinned | Treat as **ambiguous** — propose a `[NEEDS REVIEW]` Open Question; never emit a guessed/partial block. |
| Structural entry: target section (`## Domain Entities and Properties` / `## Domain Concepts and States`) is absent | Downgrade to **ambiguous** (Open Question); never invent the top-level section. |
| Structural entry: a `### <Name>` block already exists for it | Not structural — re-handle as a `rule` entry (a missing field/rule on the existing block); never insert a duplicate block. |
| User approves a subset | Apply exactly those DR ids; leave the rest reported but unchecked. |
| Unsafe shell during investigation (paths outside repo, destructive flags) | Never run it. Find another lead, or mark the entry ambiguous. |

---

## Step 7 — Self-Review Checklist (before ending each phase)

**Phase 1 (report):**
- [ ] Every unchecked entry in **both** sections has a DR item; every `- [x]` entry was skipped.
- [ ] Every confident item has a `file:line` source proof and a resolved target location; placements
      were cross-checked against target subsections' `> **Source files:**` lists where available.
- [ ] Every confident rule item's proposed statement is code-free, uses a valid EARS pattern, and
      quotes any i18n message verbatim (Rules 2, 4, 5).
- [ ] Every confident **structural** item's proposed block covers **all** properties/states (audit/
      soft-delete/version fields excluded), carries a `> **Source files:**` annotation, names a valid
      target section, and lists any rule-bearing fields as derived statements.
- [ ] Every ambiguous/business item's proposed Open Question carries **both** Rule 8 footers.
- [ ] No new top-level section was proposed; the EARS file was **not** modified; the report was
      written; the approval prompt was shown.

**Phase 2 (fix):**
- [ ] Only user-approved entries were applied.
- [ ] New statements are plain paragraphs in existing subsections (no IDs/bullets/code refs); new
      entity/concept blocks match the reference shape and carry their `> **Source files:**` line; new
      Open Questions are well-formed with both footers.
- [ ] Every applied statement's source file is present in its target subsection's `> **Source files:**`
      line (appended if it was missing); **no other** `> **Source files:**` annotation was modified,
      removed, or reordered.
- [ ] Each structural block covers all properties/states with audit/soft-delete/version fields
      excluded; its derived statements are code-free, rule-bearing only, and correctly placed.
- [ ] Every applied entry was flipped to `- [x]` and annotated with `→ resolved: …` **and** an
      accurate `(EARS line N)` computed after the edit (structural entries also name each derived
      statement's location).
- [ ] No new top-level sections were invented; the two review sections themselves were not
      restructured (only entries checked off + annotated).
- [ ] `## Extraction Summary` counts sum correctly and `**Extraction completed:**` is today's date.
- [ ] The diff is additive and surgical — only new statements/blocks/Open Questions, the
      source-file annotation append, the entry check-off + annotation, and the Summary refresh
      changed.
