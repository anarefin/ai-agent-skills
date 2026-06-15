---
name: merge-ears
description: Merge, combine, or consolidate two or more EARS (Easy Approach to Requirements Syntax) specification .md files into a single coherent EARS spec. Use this whenever the user wants to unify several requirement/EARS spec files — e.g. "merge these EARS specs", "combine the Member and Group specifications into one", "consolidate docs/ears/*.md into a single document", or any request to fold multiple per-domain/per-controller spec files into one. The skill deduplicates overlapping cross-cutting rules, entities, concepts, error-message rows and business rules (preserving every source reference), flags genuine conflicts for review instead of silently dropping them, and is project-neutral — it works on any set of EARS files that follow the standard section layout, not just one codebase.
---

# Merge EARS Specifications

You merge **two or more EARS specification `.md` files** into **one** standalone EARS spec.
The output must read as if it were authored as a single document — not a stapled-together pile of
files — while losing **nothing**: every business rule, entity, concept, error message, and source
reference from every input survives the merge.

You are **structure-aware but project-neutral**. You assume the input files follow the standard
EARS section layout (described in `references/section-taxonomy.md`), but you hardcode nothing about
any particular codebase, framework, or domain. Whatever domains the inputs describe, you merge them
faithfully.

## The four governing decisions

1. **Consolidate & dedupe, but keep every reference.** Overlapping content (shared cross-cutting
   rules, shared entities, repeated concepts, identical error rows, identical business rules) is
   merged into a single copy — but the surviving copy's `> **Source files:**` annotation is the
   **union** of the source-file lists from every copy it absorbed. Origin information is never lost.
2. **Ask for the merged system name.** Each input scopes its statements to its own subject (e.g.
   "the Group Management system", "the Member Management system"). Ask the user what the merged
   system should be called, then rewrite **every** statement's subject to that one name.
3. **Flag conflicts, never drop them.** When two inputs genuinely disagree (same entity described
   with different property types/constraints, contradictory rules, same error condition mapped to
   different messages), keep **both** versions and annotate them with a `[NEEDS REVIEW]` marker that
   names the conflicting sources. Guessing a winner is forbidden.
4. **Bias toward lossless.** When you cannot confidently tell whether two statements express the
   *same* rule, keep both. Over-keeping is a minor cosmetic cost; silently dropping a real
   requirement corrupts the source of truth.

---

## Workflow

### Step 0 — Gather inputs (do not assume)

- **Which files.** Take the EARS files to merge from the user's request or arguments (paths or
  globs). If none were given, list the candidate `.md` files (e.g. in `docs/ears/`) and ask which
  to combine. You need **at least two**.
- **Merged system name.** Ask the user for the system name every merged statement should use (e.g.
  "the Member & Group Management system"). This is decision #2 — do not invent it silently.
- **Output path.** Default to `docs/ears/<MergedName>-EARS-Specification.md`, derived from the
  system name, in the same directory as the inputs. Confirm or let the user override. Overwrite an
  existing file of that name.

Read every input file **in full** before writing anything. You cannot merge what you have not read.

### Step 1 — Parse each input into canonical sections

Split each file by its markdown headings into the canonical section taxonomy. Read
`references/section-taxonomy.md` for the full section list and the exact merge rule for each one.
The taxonomy, in order:

1. Title + front-matter blockquote
2. Document Conventions
3. System Overview
4. Cross-Cutting Requirements (sub-blocks: Audit and Record Lifecycle; Authentication and
   Authorisation; Request Handling; Operational Cross-Cuts; Error Response Format + its
   error-condition→message table)
5. `Module:` sections (one or many; each may contain subsections, `> **Source files:**`
   annotations, and `**Field-level validation — …:**` blocks)
6. Domain Entities and Properties
7. Domain Concepts and States
8. Business Rules Summary (numbered)
9. Open Questions
10. Extraction Summary (metrics table + per-file ledger)
11. Review by Developer (code)
12. Review by Developer (business requirements)

Any heading you encounter that does not map to the taxonomy is **carried through**, never dropped —
collect such content and emit it under an `## Additional Sections` heading near the end (before the
Review-by-Developer sections), noting which input it came from.

### Step 2 — Merge section by section

Apply `references/section-taxonomy.md`'s per-section rules. Summary:

- **Title / front-matter.** New title: `<MergedName> Business Requirements Specification (EARS)`.
  In the blockquote, set `> **System name used in statements:** the <MergedName> system`; set
  `> **Source Entry Point(s):**` to the union of all inputs' entry points; add
  `> **Merged from:**` listing the input filenames and the merge date. Keep the standard
  Format/Purpose/Note boilerplate.
- **Document Conventions.** Identical across well-formed inputs — emit once. If an input adds a
  marker the others lack, include it.
- **System Overview.** Write **one** cohesive overview spanning all merged domains. Do not paste
  the inputs' overviews back to back; synthesize a unified narrative that still names each domain's
  distinct responsibilities.
- **Cross-Cutting Requirements.** Within each sub-block, gather every statement, normalize the
  subject to the merged name, then dedupe rules that are semantically the same. Surviving statements
  use the merged name. When two cross-cutting rules cover the same topic but differ in substance,
  keep both and flag (decision #3, #4).
- **Error-condition → message table.** Union all rows. Dedupe identical `(condition, message)`
  pairs. If the **same condition** maps to **different messages** across inputs, emit a row for each
  and append `[NEEDS REVIEW: <SourceA> vs <SourceB>]` so the divergence is visible.
- **Module sections.** Concatenate all `## Module:` sections from all inputs in a sensible order
  (group related domains together). Keep each module's `> **Source files:**` annotations and
  `**Field-level validation — …:**` blocks **intact and verbatim** (these are not statement prose,
  so they keep their original file paths). Rewrite only the statement-subject to the merged name.
  If two inputs define a module with the **same name**, merge their subsections under one heading
  and flag any contradictory statements.
- **Domain Entities and Properties.** Dedupe shared entities. **Match entities by the domain file
  in their `> **Source files:**` line, not by heading text** — the same entity often appears under
  different headings across inputs (e.g. "Member" vs "MemberInfo", "Project" vs "ProjectInfo",
  "Domain Status" vs "DomainStatus") while pointing to the same source file.
  - Same entity, identical property table → keep one copy; set its `> **Source files:**` to the
    **union** of every copy's source files (decision #1).
  - Same entity, differing tables → emit the **superset** of properties (union of rows). For any
    property whose Type/Meaning/Constraints **conflict** between inputs, keep both descriptions and
    append `[NEEDS REVIEW: <SourceA> vs <SourceB>]` to that row. Still union the source files.
  - Prefer the richer heading/description when names differ; you may note the alternate name.
- **Domain Concepts and States.** Same dedupe-by-meaning approach (e.g. Applicable Gender, Member
  Status, Data/Domain Status, Project Association Type recur across inputs). Identical → keep one +
  union refs; differing → keep both + flag.
- **Business Rules Summary.** Concatenate all rules, dedupe identical ones, then **renumber
  contiguously from 1**. Keep conflicting rules and flag them.
- **Open Questions.** Union and dedupe. Preserve any `[NEEDS REVIEW]` breadcrumb footers verbatim.
- **Extraction Summary.** Combine into one summary: **sum** the numeric metrics (controllers,
  action services, statement-type tallies, etc.), **union** plugins/areas traced, and **concatenate**
  the per-file coverage ledgers. Add a line: `Merged on <date> from <N> source specifications:
  <list>`.
- **Review by Developer (code)** and **Review by Developer (business requirements).** Keep both
  placeholder sections. Concatenate any non-empty findings from the inputs under the matching
  heading; if all inputs are empty, keep the single empty placeholder.

#### How to decide two statements are "the same rule"

Normalize away the system-name subject and trivial wording differences (articles, "shall"/"must"
phrasing, British/American spelling). If what remains is the same condition acting on the same
subject producing the same outcome, they are duplicates → keep one. If the condition, the subject
entity, the threshold, or the outcome differs in any substantive way, they are **not** duplicates →
keep both (and flag if they appear to contradict). When genuinely unsure, keep both (decision #4).

### Step 3 — Self-check before finishing

Run the bundled checker against your output and fix anything it reports:

```bash
python3 ~/.claude/skills/merge-ears/scripts/check_merged_spec.py <output-file> \
  --inputs <input1> <input2> [...] --system-name "<MergedName>"
```

It verifies the structural invariants: no duplicate entity headings, contiguous Business-Rules
numbering, no duplicate `(condition, message)` error rows, every `[NEEDS REVIEW]` marker names its
sources, and the merged system name is the subject used throughout (reporting any leftover original
subjects). Treat its findings as a checklist — resolve each before declaring the merge done.

Then report to the user: the output path, how many statements/entities/rules came in vs. went out
(showing what was deduped), and a list of every `[NEEDS REVIEW]` conflict you flagged so they know
what needs a human decision.

---

## Anti-patterns (do not do these)

- **Stapling files together.** Four overviews, four Cross-Cutting blocks, the Country entity four
  times — that is concatenation, not a merge. Consolidate.
- **Dropping a source reference during dedupe.** The whole point of decision #1: the surviving copy
  must carry the union of source files. A reader must still be able to trace any rule back.
- **Picking a winner in a conflict.** When inputs disagree, you flag — you never quietly choose.
- **Keeping mixed system-name subjects.** After the merge, every statement says the one merged
  system name. Leftover "the Group Management system" sentences are a bug.
- **Rewriting `> **Source files:**` paths into prose or "merged-name" form.** Those annotations are
  not statements; they keep their literal file paths (just unioned where entities were deduped).
