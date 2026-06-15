# EARS Spec Section Taxonomy & Per-Section Merge Rules

This is the canonical section layout that standard EARS specification files follow, with the exact
rule for merging each section. Read the section name from the markdown heading; apply the rule.

The inputs are produced by an EARS reverse-engineering process, so they share this shape. If a
particular input is missing a section, simply skip it for that input. If an input has an extra
heading not listed here, carry it through under `## Additional Sections` (never drop it).

---

## 1. Title + front-matter blockquote

**Shape.** A single `#` title `<Domain> Business Requirements Specification (EARS)`, followed by a
`>`-blockquote of metadata lines: `**Format:**`, `**Source:**`, `**Source Entry Point(s):**`,
`**System name used in statements:**`, `**Purpose:**`, `**Note:**`.

**Merge rule.**
- Title → `<MergedName> Business Requirements Specification (EARS)`.
- `**Format:**`, `**Purpose:**` → keep the common boilerplate (they are identical across inputs).
- `**Source:**` → keep the common description; if inputs differ, keep the shared parts and union
  the rest.
- `**Source Entry Point(s):**` → **union** of all inputs' entry points.
- `**System name used in statements:**` → `the <MergedName> system` (the name the user gave).
- `**Note:**` → keep the shared note; merge in any unique clauses.
- **Add** `**Merged from:**` → bullet/inline list of the input filenames and the merge date.

---

## 2. Document Conventions

**Shape.** A markdown table of markers (`[NEEDS REVIEW]`, `[UNRESOLVED: X]`, `[INFERRED]`,
`[DISABLED]`, `[TEST-HINT]`, `Review by Developer`, …) and their meanings.

**Merge rule.** Emit **once**. Take the union of marker rows across inputs (some inputs may define a
marker others omit). Identical rows collapse to one.

---

## 3. System Overview

**Shape.** One or more plain-prose paragraphs describing the domain, its scope, integrations, and
enforcement layers.

**Merge rule.** Write **one** unified overview covering all merged domains. Do **not** paste the
inputs' overviews end to end. Synthesize a single narrative that still names each domain's distinct
responsibilities and the shared infrastructure they all touch. Aim for cohesion, not a digest.

---

## 4. Cross-Cutting Requirements

**Shape.** `## Cross-Cutting Requirements` with these `###` sub-blocks (some inputs omit some):
`Audit and Record Lifecycle`, `Authentication and Authorisation`, `Request Handling`,
`Operational Cross-Cuts`, `Error Response Format`. Each sub-block is plain-prose EARS statements.
`Error Response Format` additionally contains a **table** mapping error conditions to verbatim
message text (plus columns like "Bengali present?").

**Merge rule — statement sub-blocks.** For each sub-block, gather every statement from every input,
normalize the subject to the merged system name, then dedupe rules that say the same thing (see
SKILL.md "How to decide two statements are the same rule"). Keep one copy of each distinct rule.
Where two rules cover the same topic but differ substantively, keep both; if they contradict, append
`[NEEDS REVIEW: <SourceA> vs <SourceB>]`.

**Merge rule — error table.** Union all rows. Collapse identical `(condition, message)` pairs to one.
If the **same condition** maps to **different messages** across inputs, keep a row per distinct
message and tag with `[NEEDS REVIEW: <SourceA> vs <SourceB>]`. Preserve the verbatim message text
and the "Bengali present?" (or equivalent) column. Keep the explanatory sentence above the table,
merged to one.

---

## 5. Module sections (`## Module: <Name>`)

**Shape.** One or many `## Module:` headings. Each may carry a header blockquote (`> **Domain:**`,
`> **Scope:**`, `> **Entry Points:**`, `> **Source files:**`), then `###` subsections of EARS
statements, and `**Field-level validation — <Request>:**` blocks (each a run of
`If <field>… shall reject the request.` paragraphs).

**Merge rule.** Concatenate all modules from all inputs. Order them so related domains sit together
(e.g. all of one domain's modules, then the next). Within each module:
- Keep the header blockquote, including `> **Source files:**`, **verbatim** (these are annotations,
  not statements — they retain their literal file paths).
- Keep `**Field-level validation — …:**` blocks intact.
- Rewrite only the statement-subject to the merged system name.
If two inputs define a module with the **same name**, merge their subsections under one heading and
flag any contradictory statements with `[NEEDS REVIEW: …]`.

---

## 6. Domain Entities and Properties

**Shape.** `## Domain Entities and Properties`, then one `###` per entity. Each entity has a
`> **Source files:**` annotation pointing to its domain class file, a short description, and a
property table (`Property | Type | Meaning | Constraints`).

**Merge rule.** Dedupe shared entities. **The dedupe key is the domain file path in
`> **Source files:**`, not the heading text** — the same entity recurs under different headings
across inputs (e.g. `Member`/`MemberInfo`, `Project`/`ProjectInfo`, `Domain Status`/`DomainStatus`,
`Branch Office`/`PhysicalOfficeInfo`) while pointing to the same source file.
- Same source file, identical property table → keep one copy; set `> **Source files:**` to the
  **union** of all copies' source files.
- Same source file, differing tables → emit the **superset** of property rows (union by property
  name). For any property whose Type/Meaning/Constraints disagree between inputs, keep both
  descriptions in the cell and append `[NEEDS REVIEW: <SourceA> vs <SourceB>]`. Union the source
  files. Prefer the fuller heading/description; you may note the alternate name parenthetically.
- Keep the intro note about shared audit fields (merged to one).

---

## 7. Domain Concepts and States

**Shape.** `## Domain Concepts and States`, then `###` per concept (status enumerations, state-
transition tables, constant catalogues, e.g. Applicable Gender, Member Status, Data/Domain Status,
Project Association Type).

**Merge rule.** Same dedupe-by-meaning approach as entities. Concepts recur across inputs. Identical
→ keep one + union any `> **Source files:**` refs. Differing (e.g. different identifier values or
state transitions for the "same" concept) → keep both + `[NEEDS REVIEW: …]`.

---

## 8. Business Rules Summary

**Shape.** `## Business Rules Summary`, a numbered list (`1.`, `2.`, …) of one-line rules.

**Merge rule.** Concatenate all rules across inputs, dedupe identical ones, then **renumber
contiguously from 1** with no gaps or repeats. Keep conflicting rules (both) and flag them.

---

## 9. Open Questions

**Shape.** `## Open Questions`, prose and/or `[NEEDS REVIEW]` items, sometimes with breadcrumb
footers pointing at source files.

**Merge rule.** Union and dedupe. Preserve breadcrumb footers verbatim. If every input reports
"none", keep a single "none" note.

---

## 10. Extraction Summary

**Shape.** `## Extraction Summary`, a metrics table (Controllers processed, Action services
processed, Total EARS statements, per-pattern tallies, plugins traced, [NEEDS REVIEW]/[UNRESOLVED]
counts, …) and a per-file coverage ledger, plus an "Extraction completed" date.

**Merge rule.** Produce one combined summary:
- **Sum** the numeric metrics across inputs.
- **Union** lists (plugins/areas traced).
- **Concatenate** the per-file coverage ledgers (one block per input, labelled by source).
- Add a line: `Merged on <date> from <N> source specifications: <filenames>`.
Note that post-merge counts may differ from the raw sum because of dedup — state the raw sum and,
where you can, the deduped figure.

---

## 11. Review by Developer (code)

**Shape.** `## Review by Developer (code)`, an HTML-comment instruction block, then findings or
"_None yet_".

**Merge rule.** Keep the section and its instruction comment once. Concatenate non-empty findings
from all inputs (label by source). If all empty, keep the single "_None yet_" placeholder.

---

## 12. Review by Developer (business requirements)

**Shape.** As above, for business-requirement findings.

**Merge rule.** Same as section 11.

---

## Additional Sections (fallback)

Any heading not matching sections 1–12 is **not dropped**. Collect such content and emit it under a
single `## Additional Sections` heading placed just before the Review-by-Developer sections, with a
sub-note identifying which input each block came from.
