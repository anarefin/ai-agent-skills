# EARS File Anatomy — Where Actions/Endpoints and Source References Live

EARS specs produced by the reverse-engineering skills (`grails-to-ears`, `springboot-to-ears`) share
a fixed shape. To build the action/endpoint catalog you only need two parts of each file: the
**front-matter entry-point header** and the **module section blockquotes**. This guide describes both
and the exact forms you must parse. Everything else in the spec (statements, entities, rules) is
irrelevant to the catalog and should be ignored.

---

## 1. Front-matter entry-point header (primary source)

Near the top of every file, inside the leading `>` blockquote, is the authoritative entry-point line.
Two header names exist depending on framework:

- **Grails:** `> **Source Entry Point(s):**`
- **Spring Boot:** `> **Source Controller(s):**`

Treat either header identically. Its value is a list of entry points. **Split on `;` first, then on
commas that separate distinct backtick-quoted paths.** Each entry point is a backtick path optionally
followed by a parenthesised qualifier naming the specific actions/endpoints.

### Qualifier forms (each named action/endpoint → one catalog row)

| Form in the file | Source file | Actions/endpoints extracted |
|---|---|---|
| `` `.../GroupInfoController.groovy` (create + save actions only) `` | that controller | `create`, `save` |
| `` `.../DcsMemberAdmissionBufferController.groovy` (actions `approveMemberAdmission`, `approveMemberUpdate`) `` | that controller | `approveMemberAdmission`, `approveMemberUpdate` |
| `` `.../CreateMemberAdmissionApiAction.groovy` `` (standalone action/API class, no qualifier) | that class | the class name as one endpoint (e.g. `CreateMemberAdmissionApiAction`) |
| `` `.../MemberInfoController.groovy` `` (controller, no qualifier) | that controller | defer to module step (§2) — enumerate one row per operation from the module's subsections; `(all actions)` only as a last resort |
| Spring Boot: `` `.../MemberController.java` (GET /members, POST /members) `` | that controller | `GET /members`, `POST /members` |

Rules of thumb:
- Backtick-quoted paths are the **Source Code Reference** values — copy them verbatim.
- Parse action names from inside the parentheses, whether introduced by `actions`, written as
  `create + save actions only`, or listed as HTTP `METHOD /path` pairs.
- A path that is itself an action/API class (name ends in `...Action`, `...ApiAction`, or the spec
  describes it as a standalone entry point) is one endpoint named by its class.
- A bare controller path with no qualifier means "enumerate actions elsewhere" — go to §2.

Multiple entry points appear separated by `;` or `,`. Example with three:

```
> **Source Entry Point(s):** `plugins/.../DcsMemberAdmissionBufferController.groovy` (actions `approveMemberAdmission`, `approveMemberUpdate`), `plugins/.../CreateMemberAdmissionApiAction.groovy`, `plugins/.../UpdateMemberAdmissionApiAction.groovy`
```

→ four rows: `approveMemberAdmission` + `approveMemberUpdate` (the controller), `CreateMemberAdmissionApiAction`, `UpdateMemberAdmissionApiAction`.

---

## 2. Module sections (Module/Domain + action refinement)

Each spec has one or more module sections shaped like:

```markdown
## Module: Group Creation

> **Domain:** Microfinance Group (VO) Creation
> **Scope:** ...
> **Entry Points:** Grails controller actions (create, save), backed by the create action class and the group service.
> **Source files:** `plugins/.../GroupInfoController.groovy`, `plugins/.../CreateGroupInfoAction.groovy`, `plugins/.../GroupService.groovy`
```

Use module sections for two purposes:

1. **Module / Domain value.** Match an entry's source-file path against each module's
   `> **Source files:**` and `> **Entry Points:**` lines; the module whose annotations reference that
   path supplies the **Module / Domain** column (prefer the `## Module: <Name>` heading; the
   `> **Domain:**` value is an acceptable alternative). If multiple modules reference the path, list
   each. If none do, fall back to the spec's overall subject (its title / `System name used in
   statements`).

2. **Action enumeration — one row per individual operation.** When the front-matter listed a
   controller with **no** action qualifier, do *not* shortcut to `(all actions)`. Recover the
   individual operations in this order:

   a. **Module `> **Entry Points:**` line.** If it names concrete actions (e.g. "Grails controller
      actions (create, save)") → `create`, `save`, one row each.

   b. **Module content subsections (the usual case).** Each `### subsection` beneath the module is a
      distinct operation, and its `> **Source files:**` line names the action class that implements
      it. Emit one row per subsection, using the **action-class name verbatim** as the Action /
      Endpoint. Use the **controller path** (the entry point named in the front-matter) as the Source
      Code Reference — the action-class name in the Action column identifies the implementing class,
      and this keeps every row's source reference pointing at the real entry point (so the
      no-dropped-entry-point check still holds). For example, the Member Management module's
      subsections map like this:

      | Subsection heading | Action class in its `Source files:` | Action / Endpoint | Source Code Reference |
      |---|---|---|---|
      | `### Member Registration` | `CreateMemberInfoAction.groovy` | `CreateMemberInfoAction` | the controller path |
      | `### Member Edit Form Loading` | `EditMemberInfoAction.groovy` | `EditMemberInfoAction` | the controller path |
      | `### Member Profile Update` | `UpdateMemberInfoAction.groovy` | `UpdateMemberInfoAction` | the controller path |
      | `### Member Deletion` | `DeleteMemberInfoAction.groovy` | `DeleteMemberInfoAction` | the controller path |

      A subsection may cite more than one action class (e.g. `### Member Family Information` →
      `CreateMemberFamilyAction.groovy` + `UpdateFamilyInfoAction.groovy`); emit a row for each
      distinct action class. Skip the controller path itself and any plain domain/service class as a
      *separate* row — only action/`*Action` classes become rows here.

   c. **Last-resort source fallback.** Only when a controller has no qualifier, no concrete
      `Entry Points:` actions, and no subsection naming an action class, open that one source
      controller and list its real action methods (Grails `def <name>()` actions / Spring `@*Mapping`
      handlers). If even that yields nothing, emit a single `(all actions)` row. This is the *only*
      time the catalog reads source.

Note: `> **Source files:**` inside a module also lists domain/service/entity files. For the catalog
you care about these only to map a controller/action **to its module**, to recover the source path
for the entry point, and (in step b) to name the action classes — you do not create catalog rows for
plain domain or service classes.

---

## 2a. Where Purpose comes from

The **Purpose** column is a one-line, plain-language summary of what each action does — the column
that lets a reader take in the whole picture across many EARS files at a glance. It is always derived
from the EARS file, never from source. For each row, locate the operation's place in the spec and
distil it:

- **The operation's `### subsection`** is the primary source. Its heading names the operation and its
  EARS statements describe the behaviour (what it loads, validates, persists, changes, or rejects).
  Synthesise these into one specific phrase — e.g. `### Member Registration` whose statements cover
  loading the form, validating, persisting and assigning IDs → *"Loads form, validates & persists a
  new member, assigns IDs"*.
- **The module `> **Scope:**` line** gives fallback context when an operation has no dedicated
  subsection (e.g. an action named only in a qualifier). Narrow the module scope down to the single
  action — don't paste the whole scope verbatim for every row.
- **Describe behaviour, not the name.** "Deletes a member" restates the name; "Removes a member
  subject to lifecycle guards" tells the reader something. Keep it to roughly one line.

---

## 3. What to ignore

`## Domain Entities`, `## Domain Concepts`, `## Business Rules Summary`,
`## Cross-Cutting Requirements`, `## Open Questions`, `## Extraction Summary`, and the
`Review by Developer` sections contain no entry points and never become catalog rows. Module
subsection statements are not catalogued as rows either — but, unlike the above, you *do* read a
subsection's statements to write that operation's **Purpose** (see §2a).
