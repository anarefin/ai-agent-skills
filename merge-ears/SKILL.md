---
name: merge-ears
description: Build a catalog (index / inventory / manifest) of every Grails action or Spring Boot endpoint found across one or more EARS (Easy Approach to Requirements Syntax) specification .md files, with the source-code reference, module/domain, and originating EARS file for each. Use this whenever the user wants to list, catalog, index, inventory, or tabulate the actions/endpoints described by their EARS specs — e.g. "catalog the actions in these EARS files", "build an action/endpoint index from docs/ears/", "list every endpoint across these specs with its source file", "make a manifest of all controller actions in my EARS specs", or any request to enumerate the entry points of a set of EARS specifications into a single table. Accepts individual EARS files (paths or globs) OR a directory of EARS files — no pre-merging required. Works on any EARS files that follow the standard reverse-engineered layout, Grails or Spring Boot, not just one codebase.
---

# EARS Action / Endpoint Catalog

You read **one or more EARS specification `.md` files** and produce **one markdown catalog file**
that lists every **action** (Grails) / **endpoint** (Spring Boot) those specs describe. Each catalog
row carries five facts:

1. **Action / Endpoint** — the action or endpoint name (e.g. `create`, `save`, `approveMemberAdmission`).
2. **Purpose** — a one-line, plain-language summary of what that action does, so a reader can see the
   whole picture across every EARS file at a glance.
3. **Module / Domain** — the module or domain it belongs to within its EARS file.
4. **Source Code Reference** — the source file path the EARS file records for it.
5. **Originating EARS File** — which input `.md` file it came from.

You work **primarily from the EARS `.md` files** — the front-matter, module annotations, and content
subsections already record everything you need: the entry points, the action/operation breakdown, the
source paths, and the prose that describes each operation's purpose. "Source-code reference" means the
path strings the EARS file already records, not paths you re-derive by reading source. The one
exception is the **last-resort fallback** in Step 1: if a controller is named with *no* enumerable
actions anywhere in the spec, you may open that one source file to list its real action methods rather
than emit a vague placeholder. You are **project-neutral**: hardcode nothing about any codebase,
framework, or domain. You handle both Grails (actions) and Spring Boot (endpoints) layouts.

## Governing principles

1. **One row per entry point.** Every action/endpoint named in an input becomes its own row. If a
   controller exposes `create` and `save`, that is two rows. A standalone action/API class is its
   own endpoint, hence its own row.
2. **Enumerate every individual action — never lump.** A controller is a bucket of distinct
   operations; the catalog must show each one as its own row, never a single `(all actions)` summary.
   When the front-matter names a controller without listing its actions, recover the individual
   operations from the spec's content (its `## Module:` subsections and the action-class file names
   those subsections cite — see Step 1). Only if a controller has *nothing* enumerable anywhere in the
   spec do you fall back: open that one source file to read its real action methods, and if even that
   yields nothing, record a single `(all actions)` row as the absolute last resort. Never guess action
   names that no source supports.
3. **Every row gets a Purpose.** Synthesize a short, code-free one-liner from the operation's EARS
   subsection (its heading plus the statements/scope describing it). The Purpose column is what lets a
   reader grasp the whole picture across many EARS files at once, so it must be specific to the action,
   not a generic restatement of its name.
4. **Never drop an entry point.** Every source file named in an input's entry-point header must
   surface in the catalog. The self-check (Step 4) enforces this.
5. **Don't merge or dedupe across files.** Unlike a spec merge, the catalog is a faithful inventory:
   the same controller appearing in two EARS files yields rows for both, each tagged with its
   originating file. Do not consolidate, renumber, or rewrite statement prose.

---

## Workflow

### Step 0 — Gather inputs (do not assume)

- **Which inputs.** Take the EARS sources from the user's request or arguments. They may be:
  - explicit file paths or globs (e.g. `docs/ears/GroupCreation-EARS-Specification.md`), or
  - a **directory** — in which case glob it recursively for `*-EARS-Specification.md` (fall back to
    `*.md`) and treat every match as an input.
  If nothing was given, list the candidate `.md` files and ask which to catalog.
- **Output location and file name (required from the user).** Gather the catalog's destination as
  two distinct values and combine them into the final path:
  - **Output location** — the directory the catalog is written to (e.g. `docs/ears/member/`).
  - **Output file name** — the catalog's file name (e.g. `EARS-Action-Endpoint-Catalog.md`).
  If the request already states a full path (e.g. "write it to `docs/ears/Catalog.md`"), split it
  into its location and file name and use both verbatim. Otherwise, **ask the user** for the output
  location and the output file name before producing the catalog — suggest `docs/ears/` (or the
  inputs' own directory) as the location and `EARS-Action-Endpoint-Catalog.md` as the file name,
  which they may accept. Combine the two into `<location>/<file name>`; do not write anywhere until
  the user supplies or confirms both. Overwrite an existing file of that name.

Read every input file **in full** before writing anything — you cannot catalog what you have not read.

### Step 1 — Extract entry points from each file

Read `references/ears-anatomy.md` for the exact locations and parsing forms. In brief, for each file:

- **Primary source: the front-matter entry-point header.** Grails specs use
  `> **Source Entry Point(s):**`; Spring Boot specs use `> **Source Controller(s):**`. Parse it into
  `(source-file path, [action/endpoint names])` pairs:
  - Split the line into entry points on `;` and on top-level `,` between backtick-quoted paths.
  - For each backtick path, read any trailing qualifier: `(create + save actions only)`,
    `(actions \`approveMemberAdmission\`, \`approveMemberUpdate\`)`, `(GET /members, POST /members)`, etc.
    Each named action/endpoint → one entry.
  - A standalone action/API class path (e.g. `CreateMemberAdmissionApiAction.groovy`) with no
    qualifier is itself one endpoint; use the class name as the action/endpoint.
  - A controller path with **no** qualifier → defer action enumeration to the module step below.
- **Refine with module sections — enumerate every individual action.** For a controller that had no
  explicit action qualifier, recover its individual operations from the spec itself, in this order:
  1. The matching `## Module:`'s `> **Entry Points:**` line, if it names concrete actions (e.g.
     "Grails controller actions (create, save)" → `create`, `save`).
  2. Otherwise, the module's **content subsections**. Each `### subsection` under the module is a
     distinct operation; its `> **Source files:**` line cites the action class that implements it
     (e.g. `### Member Registration` → `CreateMemberInfoAction.groovy`). Emit one row per such
     operation, using the **action-class name** as the Action / Endpoint value (verbatim, e.g.
     `CreateMemberInfoAction`). For the **Source Code Reference**, use the controller path the
     front-matter named as the entry point (the action-class name in the Action column already
     pinpoints the implementing class) — this keeps the source reference pointing at the real entry
     point and consistent with the qualified-action rows above. See `references/ears-anatomy.md` §2
     for the exact mapping.
  3. **Last-resort fallback only** — if a controller has no actions in its qualifier, no concrete
     `Entry Points:` actions, and no module subsections naming action classes, open that one source
     controller and list its real action methods (Grails `def <name>()` actions / Spring `@*Mapping`
     handlers). Note in your final report which controllers required this. If even the source yields
     nothing usable, record a single `(all actions)` row.

### Step 2 — Assign Module / Domain to each entry

Match each entry's source-file path to the `## Module:` whose `> **Source files:**` or
`> **Entry Points:**` references it, and use that module's heading name (or its `> **Domain:**`
value). If a source file maps to more than one module, list each module the action plausibly belongs
to. If no module references it, use the spec's overall subject (the title/`System name`).

### Step 2.5 — Write each action's Purpose

For every row, write a one-line Purpose from the EARS file (no source reading). Find the entry's
operation in the spec — the `### subsection` (or the action qualifier's flow) that describes it — and
distil what it does into a single specific phrase. Draw on the subsection heading, its EARS
statements, and the module `> **Scope:**` line. Keep it to roughly one line; describe the *behaviour*
(what it loads/validates/persists/changes), not just a reword of the action name. See
`references/ears-anatomy.md` "Where Purpose comes from" for the mapping.

### Step 3 — Emit the catalog

Write one markdown file. ALWAYS use this structure:

```markdown
# EARS Action / Endpoint Catalog

> **Generated:** <date>
> **Source EARS files (<N>):**
> - <relative/path/to/input-1.md>
> - <relative/path/to/input-2.md>
> **Note:** One row per Grails action / Spring Boot endpoint, extracted from the EARS files' own
> entry-point, module, and subsection annotations. <Add "No source code was read." only if no
> controller required the Step 1 last-resort source fallback; otherwise list the controllers that did.>

| # | Action / Endpoint | Purpose | Module / Domain | Source Code Reference | Originating EARS File |
|---|-------------------|---------|-----------------|-----------------------|-----------------------|
| 1 | create | Loads the group creation form with its reference data | Group Creation | `plugins/mf/.../GroupInfoController.groovy` | GroupCreation-EARS-Specification.md |
| 2 | save   | Validates and persists a submitted group, assigning its identifiers | Group Creation | `plugins/mf/.../GroupInfoController.groovy` | GroupCreation-EARS-Specification.md |
```

Sort rows by **originating file → module → action** so related entries sit together. Keep the source
path in backticks, verbatim from the EARS file. Number the `#` column contiguously from 1.

### Step 4 — Self-check before finishing

Run the bundled checker and fix anything it reports:

```bash
python3 ~/.claude/skills/merge-ears/scripts/check_catalog.py <output-file> \
  --inputs <input1> <input2> [...]
```

It verifies the structural invariants: the table has the five required columns (including
**Purpose**), every input file appears in the **Originating EARS File** column, no row is missing a
**Source Code Reference**, **Action / Endpoint**, or **Purpose**, and every source file named in each
input's entry-point header surfaces in the catalog (no dropped entry point). Treat its findings as a
checklist — resolve each before declaring the catalog done.

Then report to the user: the output path, how many EARS files were read, how many action/endpoint
rows were produced, any controller that required the Step 1 last-resort source fallback, and any
entry point that still yielded only an `(all actions)` row (so they know where the source spec was
genuinely under-specified).

---

## Anti-patterns (do not do these)

- **Merging or deduping.** This skill is an inventory, not a spec merge. The same controller in two
  EARS files appears as rows under both — do not consolidate, renumber statements, or rewrite prose.
- **Reading the codebase to enrich rows the spec already covers.** Module/Domain, Source Code
  Reference, and Purpose all come from the EARS `.md` files. Opening `.groovy`/`.java` source is
  permitted *only* as the documented Step 1 last-resort fallback — a controller with no enumerable
  actions anywhere in the spec — and never to embellish an action the spec already describes.
- **Lumping into `(all actions)`.** Don't collapse a controller into one placeholder row when the
  spec's subsections and action-class references let you list the individual operations. Reserve
  `(all actions)` for the genuine dead end where neither the spec nor the source yields anything.
- **Inventing actions.** Never list an action/endpoint that no source — spec or (in the fallback)
  controller — supports.
- **Dropping an entry point.** Every source file in an input's entry-point header must appear in the
  catalog. The checker fails the run if one is missing.
