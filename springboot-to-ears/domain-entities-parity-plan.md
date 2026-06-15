# Implementation Plan — Bring `/springboot-to-ears` Domain-Entity handling to parity with `/grails-to-ears`

## Context

`/grails-to-ears` was hardened so its **Rule 13 — Domain Entities and Properties** forces *every* entity (in-scope and externally-owned/cross-module alike) to be catalogued with its **complete** declared-field set, transitively to closure, with a verifiable closeout inventory. `/springboot-to-ears` is weaker on six primary points and carries several secondary defects (including a self-contradiction). This plan adopts **all** of them into `~/.claude/skills/springboot-to-ears/SKILL.md`, adapted to JPA/Spring wording.

**Scope:** edits to exactly one file — `~/.claude/skills/springboot-to-ears/SKILL.md`. No other file changes. The grails skill is the reference; it is **not** edited.

**Decision already taken by user:** adopt *all* gaps including gap #6 (audit/version rows appear in every entity table — switch springboot from its current "note once, omit per entity" policy to grails' "row in every table, lifecycle semantics referenced once").

---

## Edit set (7 edits, all in `springboot-to-ears/SKILL.md`)

### Edit 1 — Rule 13 body (springboot lines ~146–162): add the 5 hardening bullets + flip audit policy

**Where:** the `### Rule 13 — Domain Entities and Properties catalog` block.

**Changes:**

1a. **Complete field set (gap #1 + #2).** Replace the existing "List **every** domain-specific property of the entity…" bullet (line ~156) with a "complete mirror of the entity class" bullet, and add an explicit external-entity-full-expansion clause:
> - List **every field declared in the entity class** — the table is a complete mirror of the JPA entity's field list, **not** just the fields the traced call chain happened to touch. List a field even when no traced behaviour, validation, or requirement references it. Embedded `@Embeddable` / JSON-column structured objects and child entities each get their **own** `###` sub-block.
> - **Complete field set — full expansion (every entity, in-scope and externally-owned alike).** Each entity's `###` sub-block must contain **one row per field declared in its source class**, uniformly for the primary in-scope entities and every externally-owned / cross-module referenced entity. A table listing only a subset (e.g. only the fields the traced code read or wrote) is **incomplete and rejected** — open the entity class and enumerate **all** declared fields. Externally-owned entities are **not** abbreviated; their module ownership is noted only in the description sentence, never used as a reason to list fewer fields.

1b. **Transitive closure as an explicit bullet (gap #4 part 1).** Add:
> - **No reference left uncataloged (transitive closure).** Every property whose Type is `Reference to <Entity>` or `List of <Entity>` requires that entity to have its **own** `###` sub-block with a full `| Property | Type | Meaning | Constraints |` table somewhere in this section — transitively (an entity reached only because another referenced entity points to it is itself catalogued), until no referenced entity remains without its own block. No entity may appear merely as a `Reference to <Entity>` / `List of <Entity>` type with its properties absent.

1c. **No grouped externally-owned section (gap #3).** Add:
> - **No grouped "externally-owned" sections.** Never merge multiple referenced entities into a single `### Externally-owned reference entities` block. Every entity appearing as a `Reference to <Entity>` / `List of <Entity>` Type — regardless of which module/service owns it — gets its own dedicated `###` sub-block with a complete property table. Module ownership belongs only in the entity's description sentence, never in the block structure. A grouped prose block is never a valid substitute for individual property tables.

1d. **Mandatory reference-closure inventory (gap #4 part 2).** Add:
> - **Mandatory reference-closure inventory before finalizing.** After writing all entity blocks, build a checklist in working notes: collect every distinct entity name appearing as a `Reference to <Entity>` or `List of <Entity>` Type in any row of any entity table; for each, confirm a `###` sub-block exists. Any gap is resolved by opening the owning entity class, reading its properties, and filling the block — before Step 7 runs. Zero gaps allowed.

1e. **Catalog once incl. shared infrastructure (gap #5).** Add:
> - **Catalog once, then cite.** Each entity gets exactly **one** `###` sub-block, written at first reach; later mentions just name it. Pervasively-shared infrastructure entities (the actor/user record, office/branch, organization) are catalogued once on first reach like any other entity and thereafter only named — they are **not** exempt from being catalogued, but they are **not** repeated.

1f. **Enum-type resolution binding (secondary).** Add:
> - **Enum types must resolve too.** Every property Type written as `Enum (<EnumName>)` must have its **complete** value table present in `## Domain Concepts and States` (Rule 12). No enum may be named as a property type without its full value set existing there. The Type cites the enum by name; the values live in the cross-referenced Domain Concepts table.

1g. **Flip the audit-field policy (gap #6).** Replace the current bullet (line ~159):
> *"Shared base-entity audit fields (created/updated by + at, soft-delete flag, optimistic-locking version) are **not** repeated per entity. State them once in a note…"*

with the grails policy:
> - Shared audit / soft-delete / optimistic-locking fields (created/updated by + at, soft-delete flag, version) **are** listed as rows in **every** entity table — they are part of the complete field set and are not exempt. What is stated once (not re-explained per entity) is their detailed **lifecycle semantics**: the top-of-section note and the `Meaning` column point the reader to Cross-Cutting Requirements → Audit and Record Lifecycle (Step 0b), while the rows themselves still appear in each table.

1h. Keep the existing "exact codebase field name in the Property column" bullet (line ~160) unchanged — it is already correct.

---

### Edit 2 — Step 2c (springboot lines ~463–467): full-mirror + transitive wording

**Where:** `### 2c. Follow every JPA repository call`.

- Change "Reading an entity is not done until each of its **domain-specific** properties is recorded there" → "Reading an entity is not done until **every field it declares** is recorded there as a `| Property | Type | Meaning | Constraints |` row — a complete mirror of the JPA entity class, including fields no traced behaviour references."
- In the association bullet, add the "catalog once / shared-infrastructure entities follow the same rule (read and catalogue on first reach, then only name)" clause and the "any enum named as a property type is read in full (Step 0l) so its complete value table exists" clause — mirroring grails Step 2c line 418.
- Change the audit-field sentence (line ~467) to match Edit 1g: audit/version rows **are** listed per entity; only lifecycle semantics referenced once.

---

### Edit 3 — Step 7, Rule 13 checklist line (springboot line ~1140): fix the self-contradiction + strengthen

**Where:** Formatting Compliance → Rule 13 checkbox.

Current (defective): *"Every entity catalog … uses business-language property names … no Java field names …"* — this **contradicts** Rule 13 body (exact codebase field name). Replace with the grails-equivalent self-consistent check:
> - [ ] **Rule 13:** Every entity table is a **complete mirror of its source class** — one row per declared field (audit/version/soft-delete and fields no requirement references included), for in-scope and externally-owned entities alike; no partial "touched fields only" table. The Property column uses the **exact codebase field name** (camelCase) — business-level types in the Type column, plain English in Meaning. No `Reference to <Entity>` / `List of <Entity>` property appears without that entity having its own `###` catalog block (transitively, to closure); no grouped "externally-owned" prose block substitutes for individual tables. No `Enum (<Name>)` Type appears without its full value table in Domain Concepts and States. Each entity catalogued once (shared infrastructure entities included). Reference-closure inventory run: every distinct entity named as `Reference to`/`List of` confirmed to have a `###` block — zero gaps.

---

### Edit 4 — Step 7, Section Completeness entity line (springboot line ~1149): require closure + full field set

Replace the existing "contains a `###` sub-block … for **every** entity in the traced call chain (including embedded JSON objects and child entities)" line with the grails-equivalent (line 965): add the transitive closure of every referenced entity, the complete-field-set/full-mirror requirement, externally-owned-alike, no grouped block, enum-table resolution, and catalog-once. Update its audit clause to match the flipped policy (rows present in every table, semantics referenced once).

---

### Edit 5 — Output template, Domain Entities section (springboot lines ~834–869): enforcement comment + audit-note flip

**Where:** the `## Domain Entities and Properties` template block.

- Replace the top `>` note so it states that audit/version/soft-delete are **listed as rows in every entity table** (semantics described once under Cross-Cutting), not omitted.
- Insert a grails-style `<!-- REFERENCE CLOSURE (Rule 13): … -->` HTML comment (mirroring grails template lines 724–733) restating: reference closure, complete field set / full mirror, forbidden grouped block, catalog-once incl. shared infra, exact field names, enum-resolution, and the pre-finalize reference-closure inventory.

---

### Edit 6 — Anti-Patterns table (springboot, near line ~1239): add 4 entity rows

Add rows mirroring grails 1041, 1042, 1048, 1049 (the existing "omitting scalar properties" row at 1239 stays):
- Partial entity table / abbreviated externally-owned entity → open the source class, list **every** declared field (in-scope and externally-owned alike).
- `Reference to <Entity>` with no entity block, or `Enum (<Name>)` with no value table → every referenced entity has its own block (transitively); every named enum has its full value table; each entity once.
- Capitalised/paraphrased property name (`Member Name`) → exact codebase field name (`memberName`); plain English goes in Meaning.
- Grouping referenced entities into one `### Externally-owned reference entities` prose block → each gets its own dedicated four-column table; ownership only in the description sentence.

---

### Edit 7 — Important Reminders (springboot, end of file ~1251+): add a dedicated entity reminder

Add a springboot equivalent of grails Reminder 24: a dense restatement that the Domain Entities catalog mirrors every entity's full declared-field set (audit/version included), transitively catalogues every referenced/external entity in its own block to closure, never uses a grouped block, catalogues each entity once (shared infra included), uses exact field names, and runs the reference-closure inventory before Step 7.

---

## Ordering & method

Apply edits 1→7 top-to-bottom (so earlier line numbers shift predictably). Use exact-string `Edit` calls anchored on the current text quoted above. Re-read each target block immediately before editing to capture the precise current string (line numbers in this plan are approximate and may have drifted).

## Verification

1. **Grep parity check** — every hardening clause now present in springboot:
   ```
   grep -nE "complete mirror|full expansion|externally-owned|No reference left uncataloged|reference-closure inventory|Catalog once|grouped .externally-owned" ~/.claude/skills/springboot-to-ears/SKILL.md
   ```
   Expect hits in: Rule 13 body, Step 2c, Step 7 (×2), template comment, Anti-Patterns, Reminders.
2. **Contradiction gone** — confirm no remaining "business-language property names" / "no Java field names" in the Rule 13 Step 7 line:
   ```
   grep -n "business-language property names" ~/.claude/skills/springboot-to-ears/SKILL.md   # expect: no output
   ```
3. **Audit-policy flip consistent** — confirm Rule 13 body, Step 2c, template note, and both Step 7 lines all say audit rows appear in every table (no lingering "not repeated per entity").
4. **Cross-skill diff** — diff the Rule 13 / Step 2c / Step 7 entity clauses against grails to confirm semantic equivalence (only framework wording should differ: JPA/`@ManyToOne` vs GORM/`hasMany`, `entity class` vs `domain class`).
5. **Optional behavioural check** — run `/springboot-to-ears` on one controller whose entity references a cross-module entity; confirm that entity gets its own full `###` block (not abbreviated, not grouped) and the reference-closure inventory is satisfied.

## Out of scope / notes

- Grails-specific constructs (`validator:` closures, `static constraints { }`, `messages_bn.properties`, `[TEST-HINT]`) are **not** ported — they have no Spring Boot equivalent. Only the entity-cataloguing semantics are mirrored, in JPA wording.
- No changes to Steps 0, 1, 1.5, 3, 4, 5 (module derivation), 6, 6.5 — these are already equivalent across the two skills.
