---
name: springboot-to-ears
description: Reverse engineer a Java Spring Boot project into a 100% complete EARS (Easy Approach to Requirements Syntax) specification file. Use this skill when the user wants to extract business requirements from an existing Spring Boot codebase — including single controllers, multiple controllers, or an entire project directory — and produce a standalone, code-free .md EARS file that can serve as a source of truth for regenerating the system in any architecture (DDD, CQRS, Event Sourcing, etc.). The skill also auto-resolves its own Open Questions on the first pass (Step 6.5): a fresh read-only subagent chases each question's breadcrumb footer and folds confident answers back into the spec as finalised statements, leaving only genuinely unresolvable items as [NEEDS REVIEW] — so a separate /resolve-open-questions run is usually unnecessary. Each module and content subsection is annotated with a `> **Source files:**` line listing the full project-relative paths it was extracted from, so a developer can cross-check the spec against the codebase (the EARS statements themselves stay code-free).
---

# Spring Boot → EARS Reverse Engineering Skill

You are performing **lossless business requirement extraction** from a Java Spring Boot codebase. Your output is a standalone EARS specification `.md` file. Readers of this file have **zero knowledge** of the source project. Every business rule, validation, workflow, access-control constraint, and exception behaviour must be expressed as a self-contained EARS statement — no code references, no class names, no method names, no annotations, no framework terminology in the statement text. The **sole** exceptions, both outside statement prose, are the per-heading `> **Source files:**` annotation that lets a developer cross-check each section against the codebase (Rule 14) and the Open Questions breadcrumb footers (Rule 8).

Completeness is **gap-free by construction**, not by luck: every large file is read under a structural-index + rule-site ledger (Step A-2.1) that maps each `if`/`case`/`throw` to the statement it produced, and a subagent verification pass (Step 6) independently confirms `0` uncovered rule-sites before the spec is final — so a follow-up `/ears-gap-fix` run would find nothing missing.

**Output file location:** `docs/ears/<DomainName>-EARS-Specification.md` (project-relative). Overwrite any existing file with the same name.

---

## Output Formatting Rules (Non-Negotiable)

These rules govern the *form* of every EARS statement and every section. They override any contrary instinct from reading other EARS examples.

### Rule 1 — Domain-scoped system name

The subject of every EARS statement is `the <DomainName> system`, where `<DomainName>` is the business domain of the module being extracted — not the project name.

- ✅ `the Loan Proposal system`
- ✅ `the Member Onboarding system`
- ✅ `the Loan Approval system`
- ❌ `the system` (too generic — fails the "standalone reader" test)
- ❌ `Smart MF` / `the Smart MF system` (project name — not domain-scoped)
- ❌ `the application` / `the service` / `the platform`

Derive the domain name from the controller cluster being extracted (e.g., `LoanProposalOtcRestController`, `LoanApproveOtcRestController` → "Loan Proposal"). If multiple distinct domains are extracted in one run, each module section may use its own domain-scoped name. Use the same name consistently within a module.

State the chosen name explicitly in the front-matter block at the top of the file: `> **System name used in statements:** the <DomainName> system`.

### Rule 2 — Plain prose paragraphs, no IDs, no bullets

Every EARS statement is a complete standalone sentence, written as a paragraph separated from neighbours by a blank line. Do **not** prefix statements with IDs (`UB-AUD-1.`, `EV-CRE-2.`), do not use bullet points, do not use numbered lists for statements.

- ✅ `When an actor submits a new loan proposal for a branch via the OTC channel, the Loan Proposal system shall verify that the branch's business day is currently open before proceeding with any processing.`
- ❌ `- **UB-AUD-1.** The system shall…`
- ❌ `1. The system shall…`

Numbered lists are reserved for the **Business Rules Summary** and **Open Questions** sections only.

### Rule 3 — Each `if`-branch is its own paragraph

A validator with N rejection branches produces N separate paragraphs. Do not collapse, do not summarise, do not group. If two consecutive paragraphs differ only in the field name being validated, both stay — they are distinct requirements.

### Rule 4 — Name the exact entity that supplies the reference value

When an EARS statement compares the request against a domain record, the entity named in the statement must match the actual source field. A check against `loanProductDetailsDto.getDurationInMonths()` says "loan product **details**", not "loan product". A check against `loanProductPolicyDto.getPolicyMaximumLoanAmount()` says "loan product **policy**". Related entities (loan product vs. loan product details vs. loan product policy) are distinct records with distinct active-date ranges and distinct field sets; conflating them in requirement text makes the spec ambiguous.

### Rule 5 — Quote i18n messages verbatim where they exist

If the codebase contains a user-facing message for an error (in `messages.properties`, `messages_bn.properties`, or as a string literal in `throwError(...)`), include it in the Unwanted Behaviour statement in double quotes:

> `If the proposal monitoring date range exceeds 24 hours, the Loan Proposal system shall reject the request with the message "Date range should not exceed 24 hours."`

Do not paraphrase messages that exist verbatim in the codebase. If only a Bengali message exists, include the English back-translation alongside.

### Rule 6 — Field-level validation goes in a dedicated subsection

After the main happy-path and state-guard statements of a functional area, add a dedicated `**Field-level validation — <RequestName>:**` block. Each field-level rule is a separate `If <field>… the <DomainName> system shall reject the request.` paragraph. Do not mix field-level validation into the main flow.

### Rule 7 — Lifecycle-driven module derivation (no fixed skeleton, no empty placeholders)

Modules are derived from the controllers actually being processed and the content thresholds they produce. **Do not** force a fixed 6-module skeleton. Sibling lifecycle controllers are **discovered and confirmed with the user** in Step 1.5; the resulting user-confirmed set is the scope that drives module derivation — never silently expanded beyond it, never silently narrowed to ignore a discovered sibling.

**Primary module(s):** one per controller, named after the controller's domain and lifecycle role:
- CRUD-style controller (create / update / delete / get / list) → `Module: <Domain> — <Channel> (Proposal Management)` (or equivalent — "Member Management", "Account Management").
- Approval/Workflow-style controller (approve / reject / forward / backward) → `Module: <Domain> — <Channel> Approval`.
- Disbursement-style controller → `Module: <Domain> — Disbursement`.
- Callback/notification consumer → `Module: <Domain> — Callbacks` or `Module: <Domain> — Notifications`.
- Monitoring/reporting endpoint cluster → `Module: <Domain> Monitoring`.

**Additional cross-cutting modules** — include each ONLY when the content threshold is met in the controllers being processed:

| Module | Inclusion threshold |
|--------|---------------------|
| `Module: <Domain> Validation Rules` | The traced controllers invoke a business-rule validator with more than 5 distinct `if`-branch rules. |
| `Module: Sub-Validators` | Two or more specialised sub-validator classes (e.g., Migration, Fire Insurance, Digital Disbursement, Bank Mode of Payment) are invoked. If only one, fold it into Validation Rules. |
| `Module: Async and Queue Processing` | The controllers fire any asynchronous side effects (queue publishing, search indexing, async event listener). |
| `Module: External System Integrations` | The controllers make any outbound call to an external system (Feign client, ERP database, third-party HTTP, search engine, payment middleware). |

**Shared-validator deduplication:** if the user names multiple controllers in one run and they all invoke the same business-rule validator, produce a single consolidated `Module: <Domain> Validation Rules`. Do not repeat the rules per controller. Each per-controller module's "Proposal Creation" / "Approval" subsections may reference the validator's invocation point but the rules themselves live in the consolidated Validation Rules module.

**No empty placeholder modules.** If a cross-cutting module has zero content, omit it entirely — do not write "No <X> behaviour was identified."

### Rule 8 — Open Questions must carry codebase references (two-line footer)

Every `[NEEDS REVIEW]` item in the Open Questions section ends with two italicised footer lines that show the reviewer exactly where the agent looked and where the answer most likely lives. Format:

```
1. **[NEEDS REVIEW]** <The precise question, phrased so a domain expert can answer it.>
   *Where agent looked:* `<relative/file/path.java>:<line>` — <what was examined>. `<another/file.java>:<line>` — <what was examined>.
   *Hint for reviewer:* Likely answer in `<probable/file.java>` (<one-sentence reasoning>). Try `<grep or graphify command>` to locate.
```

Both lines are mandatory. A question without these footers is rejected by Step 7 and must be either resolved or re-investigated until the footers can be filled.

### Rule 9 — Mandatory pre-conditions before any `[NEEDS REVIEW]` is allowed

`[NEEDS REVIEW]` is not a shortcut. It is the last resort. Before marking any item `[NEEDS REVIEW]`, all of the following must have been attempted and recorded:

1. **Enum source file lookup.** If the question concerns an enum value, code, or named constant (e.g., `BufferLoanPreValidationMessage.L_216`, `LoanProposalStatus.PENDING`, `LoanApprover.DM`): the file `lib/shared-dto/.../<EnumName>.java` (or equivalent enum source) must have been read. Every value's display name / message text must have been listed in Domain Concepts and States.
2. **Validator implementation lookup.** If the question concerns a method whose name is known (e.g., `checkLoanInterestRate`, `checkParallelGeneralAndRemittanceLoanPreValidation`): the implementation file must have been opened with `Read` and the method body extracted. Naming a method without reading it is not enough.
3. **Sub-validator dependency lookup.** If the question concerns a referenced sub-validator (`digitalDisbursementLoanProposalValidator`, `loanProposalCommonValidation`, `loanProposalAgeLimitValidation`): the concrete `*Impl` file must have been opened and Procedure A applied.
4. **Access-control DAO lookup.** If the question concerns roles, permissions, or endpoint authorisation: the access-control DAO implementation and the relevant Flyway migration seed-data must have been read. Procedure D applies.
5. **Queue-consumer entry-point lookup.** If the question concerns whether a method is a Kafka listener, REST endpoint, or scheduled task: grep for `@KafkaListener`, `@PostMapping`, `@Scheduled`, `Consumer<` bean definitions on that method name. State the result.
6. **ID/sequence-generator lookup.** If the question concerns the format of a generated identifier (proposal number, account number, reference string): the generator interface and its concrete implementation must have been opened.
7. **Delegated rule-object / specification lookup.** If the question concerns a dispatcher over a collection/chain of rule or strategy objects (e.g. the four `Cloc*Rule` objects behind `ClocLoanValidatorServiceImpl`): every dispatched `*Rule` / `*Specification` class must have been opened and its predicate method read (Step A-6). Naming the dispatcher is not enough.
8. **Dynamic-message / mapping-service lookup.** If the question concerns a rejection whose message text is returned by a called service rather than written in the validator: the service's concrete `*Impl` and its backing mapping/seed data must have been opened (Step A-7).

Only after all applicable lookups in 1–8 above have been performed AND have failed to yield a definitive answer may the item be marked `[NEEDS REVIEW]`. The two-line footer (Rule 8) then records *which files were checked* and *which file the reviewer should consult next*.

### Rule 10 — No Table of Contents

Do not generate a Table of Contents. The output file starts with the title, then the header preamble block, then the Document Conventions table. Readers navigate by Markdown heading.

### Rule 11 — Mandatory front-matter and skeleton sections

Every output file must contain these top-level sections in this exact order. None may be omitted:

1. Title (`# <Domain> — <Channel> Business Requirements Specification (EARS)`)
2. Header preamble block (the `>` quoted lines with Format / Source / Source Controller(s) / System name / Purpose / Note)
3. Document Conventions table
4. System Overview (single rich paragraph)
5. Cross-Cutting Requirements (with exactly five subsections: Audit and Record Lifecycle / Authentication and Authorisation / Request Handling / Operational Cross-Cuts / Error Response Format)
6. One or more `Module:` sections (per Rule 7)
7. Domain Entities and Properties (per Rule 13)
8. Domain Concepts and States
9. Business Rules Summary
10. Open Questions (with Rule 8 footers)
11. Extraction Summary
12. Review by Developer (code) — emitted as an empty placeholder for the developer to fill; consumed by `/fix-dev-reviews`
13. Review by Developer (business requirements) — emitted as an empty placeholder; consumed by `/fix-dev-reviews`

If a top-level section would have no content (e.g., no validation rules were extracted), the section is still present with a single-paragraph explanation of why. The two `Review by Developer` sections are always emitted as empty placeholders (with their format-instruction comment) even on a fresh extraction — the developer fills them in later.

### Rule 12 — Domain Concepts uses Markdown tables, not bullet lists

Every enum, role hierarchy, sub-type list, and status taxonomy is rendered as a Markdown table with at minimum two columns (e.g., `| State Name | Business Meaning |`). Bullet lists are not acceptable for these concepts. State transition tables use three columns (`| From State | To State | Triggered by |`).

When listing an enum, list **every value** found in the enum source file, in business-logical order. If the codebase has 22 status values, all 22 appear in the table. Do not list only the values referenced in the EARS statements — that defeats the standalone-reader test.

### Rule 13 — Domain Entities and Properties catalog (every entity, every property)

The output file carries a dedicated `## Domain Entities and Properties` top-level section, positioned immediately **before** `## Domain Concepts and States`. It catalogs **every** entity reached by the traced call chain (Step 2c) so a reader regenerating the system knows the full data model — not just the enum states. This includes **every entity referenced via an association / foreign-key property** (a `Reference to <Entity>` or `List of <Entity>`): each referenced entity is catalogued with its **own full set of properties**, recursed **transitively with no depth limit** (if A references B and B references C, all of A, B, and C are catalogued) and **deduplicated** (an entity that is referenced from several places is catalogued once). A referenced entity is catalogued even when it is not otherwise exercised by business logic — being named in another entity's property is sufficient. (Enums are **not** reference entities — they stay in `## Domain Concepts and States` per Rule 12.)

- One `###` sub-block per entity: a one-line plain-language description of what the entity represents, followed by a four-column Markdown table:

  ```
  | Property | Type | Meaning | Constraints |
  ```

- List **every field declared in the entity class** — the table is a complete mirror of the JPA entity's field list, **not** just the fields the traced call chain happened to touch. List a field even when no traced behaviour, validation, or requirement references it: this section reflects the full data model, not the subset exercised by the code path you followed. Embedded `@Embeddable` / JSON-column structured objects, child entities, **and entities reached through a `Reference to <Entity>` / `List of <Entity>` property** each get their **own** `###` sub-block (or a clearly-labelled nested table) — do not flatten or omit them.
- **Complete field set — full expansion (every entity, in-scope and externally-owned alike).** Each entity's `###` sub-block must contain **one row per field declared in its source class**. This applies uniformly: the primary in-scope entities and every externally-owned / cross-module referenced entity are all expanded the same way. A table that lists only a subset of the source class's fields (e.g. only the fields the traced code read or wrote) is **incomplete and rejected** — open the entity class file and enumerate **all** its declared fields. Externally-owned entities are **not** abbreviated; their module ownership is noted only in the description sentence, never used as a reason to list fewer fields.
- **Type** is a business-level type, never a Java type: `Amount`, `Money`, `Percentage`, `Date`, `Timestamp`, `Identifier`, `Text`, `Boolean`, `Enum (<EnumName>)`, `Reference to <Entity>`, `List of <Entity>`.
- **No reference left uncataloged (transitive closure).** Every property whose Type is `Reference to <Entity>` or `List of <Entity>` requires that entity to have its **own** `###` sub-block with a full `| Property | Type | Meaning | Constraints |` table somewhere in this section. This applies **transitively**: an entity reached only because another referenced entity points to it is itself cataloged, and so on, until no referenced entity remains without its own sub-block. No entity may appear merely as a `Reference to <Entity>` / `List of <Entity>` type with its properties absent.
- **No grouped "externally-owned" sections.** Never merge multiple referenced entities into a single `###` section (e.g. `### Externally-owned reference entities`). Every entity that appears as a `Reference to <Entity>` or `List of <Entity>` Type anywhere in the entity tables — regardless of which module/service owns it — must have its own dedicated `###` sub-block with a complete `| Property | Type | Meaning | Constraints |` table. Module ownership belongs only in the entity's description sentence ("Externally owned by the member domain; …"), not in the block structure. A single grouped prose block is never a valid substitute for individual property tables.
- **Mandatory reference-closure inventory before finalizing.** After writing all entity blocks, build a checklist in working notes: collect every distinct entity name appearing as a `Reference to <Entity>` or `List of <Entity>` Type in any row of any entity table; for each one, confirm a `###` sub-block exists somewhere in this section. Any gap must be resolved by opening the owning entity class file, reading its properties, and filling the block — before Step 7 runs. Zero gaps allowed.
- **Catalog once, then cite.** Each entity gets exactly **one** `###` sub-block, written at its first reach; every later `Reference to <Entity>` / `List of <Entity>` mention simply names it (the reader follows the single catalog block). Pervasively-shared infrastructure entities (the actor/user record, office/branch, organization) are cataloged once on first reach like any other entity and thereafter only named — they are **not** exempt from being cataloged, but they are **not** repeated.
- **Enum types must resolve too.** Every property Type written as `Enum (<EnumName>)` must have its **complete** value table present in `## Domain Concepts and States` (Rule 12). No enum may be named as a property type without its full value set existing there. The property's Type cites the enum by name; the values live in the cross-referenced Domain Concepts table (do not re-list them here). (Enums are **not** reference entities — they stay in `## Domain Concepts and States`, never as their own entity sub-block.)
- **Constraints** records: required vs. optional, value ranges or limits, uniqueness, default value, relationship cardinality, and the governing enum where the property is an enum.
- Shared audit / soft-delete / optimistic-locking fields (created/updated by + at, soft-delete flag, version) **are** listed as rows in **every** entity table — they are part of the complete field set and are not exempt. What is stated once (not re-explained per entity) is their detailed **lifecycle semantics**: the top-of-section note and the `Meaning` column point the reader to Cross-Cutting Requirements → Audit and Record Lifecycle (Step 0b) for how they behave, while the rows themselves still appear in each table.
- **Property column — exact codebase field name.** The `Property` column carries the **exact field name as written in the source code** (camelCase, e.g. `proposalNumber`, `proposedLoanAmount`), so the catalog is directly traceable to the entity class. The plain-English description goes in the **Meaning** column. Do **not** translate the field name into prose in the Property column ("Proposed loan amount" belongs in Meaning, not Property). This catalog's `Property` column is the **one and only** place an exact code identifier is permitted in the spec body — it is an explicit carve-out from Rule 2. Rule 2's code-free mandate still governs **all EARS statement prose**, and Rule 4 entity references in statements stay business-worded. (The `Type`, `Meaning`, and `Constraints` columns remain code-free / business-level.)

This section is reference data (like Domain Concepts and States), not a set of EARS statements — so its tables do not take the `the <DomainName> system shall …` form.

### Rule 14 — Per-heading source-file annotation (developer cross-check)

So a developer can cross-check the spec against the codebase, every `## Module:` heading and every **content** `###` subsection carries a `> **Source files:**` blockquote line that lists the source files the section's content was extracted from. This is the **only** place file paths appear in the body of the spec (the other being Open Questions footers); the EARS **statements themselves stay code-free** — no per-statement file references, no class/method/annotation names in statement prose.

**Where it goes:**
- For a `## Module:` block: append the line to the existing `> **Domain:** / **Scope:** / **Entry Points:**` blockquote.
- For a content `###` subsection: a standalone `> **Source files:** …` blockquote line directly under the heading, **before** the first EARS statement (or, for reference sections, before the first table).

**What it lists:** a comma-separated list of the **full project-relative paths** of every source file whose rule-sites or content produced a statement (or table row) in that section, each backtick-quoted. Order them by relevance (primary entry-point/service first, then validators, then DTOs/enums/entities). Derive the list from the per-file completeness ledger (Step A-2.1) and the traced call chain (Step 2), which already record which file each statement came from — do **not** invent paths or list a file you did not open.

```
### Proposal Creation

> **Source files:** `src/main/java/com/bracits/kyc/service/buffer/LoanProposalServiceImpl.java`, `lib/shared-validation/.../BufferLoanProposalValidator.java`

When an operator submits a new loan proposal for a branch via the OTC channel, the Loan Proposal system shall …
```

**Scope — which headings get the line:**
- ✅ Every `## Module:` heading.
- ✅ Every content `###` subsection inside a module: functional areas (e.g. Proposal Creation, Proposal Update), validation concerns, sub-validator subsections, Async/Queue pipelines, External integration subsections.
- ✅ Every `###` entity sub-block in `## Domain Entities and Properties` and every `###` enum/state sub-block in `## Domain Concepts and States` (cite the entity/enum source file(s)).
- ❌ **Excluded** — these are meta or globally-sourced and do **not** carry the line: the header preamble (it already has `> **Source Controller(s):**`), Document Conventions, System Overview, all five **Cross-Cutting Requirements** subsections (each is sourced from many global infrastructure files), Business Rules Summary, Open Questions (uses Rule 8 footers instead), Extraction Summary, and the two Review by Developer sections.

A content subsection that is missing its `> **Source files:**` line is rejected by Step 7 and must have the line added from the section's ledger entries.

---

## Step 0 — Project Orientation (Always Run First)

Before examining any controller, perform a one-time project-wide orientation. This prevents missed requirements from shared infrastructure.

### 0a. Identify project structure type
- Single-module (`src/main/java/...`) or multi-module (e.g., `lib/`, `modules/`, sub-projects with own `build.gradle` / `pom.xml`)?
- If multi-module: list every module and its stated purpose. Mark which ones contain business logic vs. pure infrastructure.

### 0b. Read every abstract base entity
- Find base entity classes (e.g., `AbstractBaseEntity`, `AbstractAuditableEntity`, `AbstractRejectableBaseEntity`).
- Extract shared fields from each: audit timestamps, soft-delete flags, optimistic locking version fields, status fields.
- These produce **Ubiquitous** requirements that apply to every entity in the system — write them once in Cross-Cutting Requirements, not per-module.
- Key patterns to capture: soft delete, audit trail, optimistic locking, init defaults (deleted flag false, version zero).

### 0c. Read every `@ControllerAdvice` / global exception handler
- Read the full handler class before processing any controllers.
- For every `@ExceptionHandler` method: identify which exception type it handles, what HTTP status it returns, and what error payload it sends.
- Build a complete **condition → HTTP status** mapping table. Every exception class must appear in this table.
- Also capture: the standard error payload structure (trace ID, timestamp, English message, Bengali message, path, field details list) — this becomes the "Error Response Format" subsection.

### 0d. Read every cross-cutting `@Aspect` class
- Read each aspect fully. Extract pointcut, pre-condition, success/failure behaviour.
- Translate each into Ubiquitous or Optional requirements:
  - Captcha aspect → "Where the human-verification feature is enabled, …"
  - Business-date aspect → "Where the business-date validation feature is enabled, …"
  - Distributed-scheduler-lock aspect → "Where a scheduled operation is configured with a distributed scheduler lock, …"
  - Exception-logging aspect → "The Loan Proposal system shall record the details of every unhandled exception…"

### 0e. Read every global filter (`OncePerRequestFilter`, `HandlerInterceptor`)
- Read each filter fully: which paths, what it validates, what it rejects.
- Translate into Ubiquitous, Optional, or Unwanted Behaviour requirements:
  - Device-ID filter → "Where the device-identity verification feature is enabled, …"
  - Request-size filter → "If an incoming request carries a JSON body that exceeds N bytes, …"
  - Logging filter → "The <Domain> system shall record the details of every incoming request and outgoing response…"
  - Trace-ID filter → "The <Domain> system shall embed a unique trace identifier in every API response header."
  - CORS config → "The <Domain> system shall apply CORS policy to all API endpoints, permitting access from configured origins."

### 0f. Read every security configuration
- Read `SecurityFilterChain` beans and any profile-conditional security configurations.
- Identify protected URL patterns, public patterns, required roles/scopes per pattern.
- Read all `@Secured`, `@PreAuthorize`, `@RolesAllowed` annotations — group them by role family (e.g., "Manager + Admin + Developer", "Support + Admin + Developer") and record which operations each family covers.
- Identify Spring profile guards (`@Profile("security-enabled")`) — these become `Where … enabled, …` Optional requirements.
- A shared access-control library with database-driven role/path mappings → describe its mechanism in plain language: "The <Domain> system shall also enforce database-driven path and role access rules managed by the unified access control service. If the actor's assigned role does not have permission for the requested API path according to the access control registry, the <Domain> system shall reject the request before any business logic is executed."

### 0g. Read every shared library module — classify first, then extract

Do not treat `lib/` or sub-module directories as black boxes. Begin by classifying every module into one of four types, then apply the corresponding extraction procedure.

#### Lib module classification

| Type | Characteristics | Examples | Action |
|------|----------------|---------|--------|
| **Business-logic** | Contains concrete implementations with domain rules, validators, SQL queries, or workflow engines | `shared-validation`, `shared-approval`, `shared-service-impl`, `access-control` | Full extraction — apply procedures A–D below |
| **Interface-only** | Defines interfaces or abstract contracts; concrete implementations live in the main application | `queue-consumer`, `shared-service` | Catalog every interface; mark for follow-up |
| **Pure infrastructure** | Provides technical plumbing with no domain rules | `redis-service`, `ftp-client`, `shared-logging`, `shared-mapper` | No extraction needed; note why |
| **Shared DTO / Enum** | Data transfer objects, enums, constants, message keys | `shared-dto`, `shared-dto-v2` | Extract all enum values (→ Step 0l) and all DTO field-level validation annotations (→ Step 2h) |

#### Procedure A — Business-logic validators

**Step A-1 — Discovery (broader than name patterns)**
- Do not rely solely on class-name endings. Scan **every class in every package** of the lib module.
- Primary targets: classes whose name ends in `Validator`, `ValidatorImpl`, `ValidationImpl`, `ValidationAbstract`, `Rule`, `ValidationRule`, `EligibilityValidation`, or that implement a `*Validator` / `*Validation` interface.
- **Specification / strategy rule-objects:** classes named `*Rule`, `*Validation`, `*Spec`, `*Specification`, or exposing a predicate method (`isSatisfiedBy`, `test`, `check`, `apply`, `evaluate`) that are **dispatched from a delegating `*ValidatorService` / `*Service`** (often by iterating a `List<…Rule>` or calling each rule in turn). Each dispatched rule-object's predicate body is a **separate Procedure A scope** — follow it per Step A-6.
- Secondary targets: any class that calls `ErrorUtil.throwError`, `ErrorUtil.throwErrorByMessage`, `throwError`, or throws a domain-specific exception — regardless of its name or package.

**Step A-2 — Read ALL public methods in the class, not just `validate()`**
- A validator class often exposes multiple public methods, each representing a distinct business flow (`validate()`, `loanApprovalValidate()`, `validateGoodLoan()`). Each is a separate extraction target with its own complete set of Unwanted Behaviour requirements.

**Step A-2.1 — Large-file multi-pass protocol (mandatory for ANY source file > 500 lines, no exceptions)**

The `Read` tool silently truncates output at roughly 1,100–1,500 lines or 25,000 tokens. When this happens, you receive a `<system-reminder>` like `[Truncated: PARTIAL view — showing lines 1-1153 of 3498 total]`. **This reminder is not a stopping point — it is a paging instruction.** A 3,498-line validator read in one pass shows only its first third. Every public method, private helper, and inner class that opens after the truncation point is entirely invisible and will produce zero requirements unless you continue reading.

This protocol applies to validators, services, DAOs, mappers, controllers, configuration classes, entity classes — **any source file > 500 lines in the call chain**. It is not optional and it is not validator-specific.

Do not read by arbitrary windows and hope you caught everything. Make coverage *deliberate* with a structural-index-first, ledger-verified read plan. This is the heart of single-pass completeness: it is what lets the spec reach 0% gap without a second `/ears-gap-fix` walk.

1. **Measure first — ALWAYS, before the first `Read` call.** Run `wc -l <filename>`. Record the total line count `T`. State it in your working notes: "File X has T lines." Any file with `T > 500` enters this protocol; `T > ~1500` (the single-`Read` truncation point) makes it non-negotiable.

2. **Build a structural index with one cheap grep pass — before reading any body.** This makes coverage provable instead of luck-based. Run:
   ```
   grep -nE 'public |private |protected | void | boolean |^\s*(if|else if|case|default)\b|throwError|throwErrorByMessage|throw new |return (false|null)|@(Get|Post|Put|Delete|Request|Patch)Mapping|@Scheduled|@KafkaListener' <filename>
   ```
   From the output build two line-numbered maps:
   - **method-map** — the start line of every method (the modifier/signature lines);
   - **rule-site-map** — every `if` / `else if` / `case` / `throw` / `throwError` line.
   These two maps are the file's completeness baseline. Every rule-site line must eventually be accounted for in the ledger (point 5).

3. **Read by method range, not by arbitrary windows.** Walk the method-map in order; for each method, `Read` from its start line to the next method's start line, plus a ~30-line overlap so a body that closes just past the boundary is still fully seen. Only when method boundaries are genuinely unclear, fall back to fixed windows — and then overlap them by ~50 lines and extend the schedule until a chunk includes line `T`. Do not stop after the chunk that contained the method you were originally hunting for — there are more rule-sites after it.

4. **When you see a `PARTIAL view` system-reminder, treat it as a hard signal to continue.** The reminder literally tells you "Call Read with offset=N limit=M for the next page." Do exactly that. Do NOT mark anything as `[NEEDS REVIEW]` or "beyond the read window" while unread lines remain in the file. The window expands as you keep reading.

5. **Keep a completeness ledger per file — extended all the way to the written statement.** Maintain a checklist:
   - every **method-map** entry marked `READ`;
   - every **rule-site-map** line marked either **`EXTRACTED → EARS statement "<first ~6 words of the statement you wrote>"`** or **`EXTRACTED → not a rule`** (a guard that branches but never rejects/throws/sets a state). Naming the produced statement — not merely "noted" — is what guarantees the rule actually reached the output file. A rule-site may be left `not a rule` only when the branch genuinely never rejects, throws, or changes a domain state.
   The file's scan is **not done** until *every* rule-site line is accounted for **and** your last read reaches the class's closing brace at/after line `T`. Retain this ledger: it feeds the Step 6 verification pass and the Extraction Summary ledger totals.

6. **Recurse with no depth limit.** A method that opens in chunk K and closes in chunk K+1 is read across both. A private helper called from any method is read fully (Procedure A-3). An injected sub-validator/sub-service opens a new Procedure A scope on its concrete `*Impl` — run this same protocol there (Procedure A-4). A helper or `validate()` defined in a **superclass in another file** is a separate-file lookup — open that file and run the protocol there.

**Hard prohibition.** It is forbidden to:
- Raise a `[NEEDS REVIEW]` Open Question that says "method body lives beyond the read window", "could not be read in one pass", "file is too large to fully extract", or any equivalent. The read window is not a property of the file — it is a property of how many chunks you chose to read. Read more chunks.
- Stop reading a file because a partial-view reminder appeared. The reminder is a continuation instruction, not a halt.
- Claim a private helper `foo()` is "called at file.java:1247 but its implementation is past the read window" while the file still has unread lines. The file's unread tail is your responsibility, not the reviewer's.

If a method's body genuinely lives in a *different* file (e.g., inherited from a superclass in another module), that is a separate-file lookup — not a "beyond window" problem — and Procedure A still applies: open that file and read it.

**Step A-3 — Recursively follow private / package-private helper methods**
- When a public method calls a private helper, read that helper fully and extract every `if`-branch as a separate Unwanted Behaviour requirement.
- This recursion has **no depth limit**.

**Step A-4 — Follow injected sub-validator and sub-service dependencies**
- A lib validator frequently delegates through constructor injection. Each such call opens a **new Procedure A extraction scope**: find the concrete implementation, apply Steps A-2 through A-4 recursively.
- **Scan the ENTIRE method body — top to bottom — for sub-validator calls.** Calls can appear on line 10 or line 270. After reading any public method, perform a deliberate scan of every line for `this.fieldName.someMethod(...)` patterns.

**Step A-5 — Extract every `if`-branch as a separate requirement**
- Every `if` / `else if` that throws or returns an error is a distinct Unwanted Behaviour EARS statement.
- **Name the exact entity whose fields supply the reference value** (see Rule 4 above).
- Special patterns: date-range validity per entity (loan product, loan product details, loan product policy — three separate statements), policy amount-range (min and max — two statements), parallel-loan rules per product combination (one per combination), time-based approver restrictions (one per threshold branch), co-borrower applicability (required-present AND not-required-absent — two statements).

**Step A-6 — Delegated rule-object dispatch (specification/strategy pattern — no deferral while locatable)**

A validator (or a `*ValidatorService`) frequently does not contain the rules inline — it **dispatches to a collection or chain of rule objects**, each implementing a predicate (`isSatisfiedBy`, `test`, `check`, …). Example: `ClocLoanValidatorServiceImpl` delegates to four `Cloc*Rule` objects.

- Open **every** dispatched rule class and read its predicate body in full (each is a Procedure A scope). Extract each rejection branch as its own Unwanted Behaviour statement, with the verbatim message (Rule 5).
- If a configuration list gates which rules fire (e.g. `CLOC_PRODUCT_ALLOWED_PRODUCT_TYPE_LIST`), read that setting via the Step 3a application-config source and state the gating condition.
- **Hard prohibition:** raising a single `[NEEDS REVIEW]` that stands in for "the N rules behind this dispatcher" — while those rule classes exist in the repo — is forbidden. Locate and open each one. Only a rule class that genuinely cannot be found after searching may become a `[NEEDS REVIEW]` item, and only with the Rule 8 footer recording the failed search.

**Step A-7 — Dynamic-message / mapping-service lookup**

When a validator rejects with a message that is **returned by a called service** rather than written as a literal/enum in the validator body (e.g. `checkMemberAllowedForCoExistingLoanProduct(...)` rejecting with whatever `CoExistingLoanProductMappingService` returns):

- Open that service's concrete `*Impl` **and** its backing data source — the mapping/lookup table (via the Flyway migration seed) or the enum that supplies the message.
- Recover both (a) the exact message text and (b) the disallowed-combination / decision logic, and express them as concrete Unwanted Behaviour statements — not an Open Question.
- A `[NEEDS REVIEW]` is permitted only if the service impl or its data genuinely cannot be located, recorded with the Rule 8 footer.

#### Procedure B — Rule-book / rule-engine modules

For rule-book frameworks (RuleBook `@Rule`, `@When`, `@Then`):

1. Find every `RuleBookRunner` instantiation. Note the scanned package.
2. Find every `@Rule` class. Sort by `order` attribute.
3. For each rule: extract `@When` guard (becomes State-Driven), `@Then` action (each branch is its own Event-Driven or State-Driven statement), and any abstract base-rule logic.
4. Read `RoleWiseApprovalService` / `RoleWiseApprovalLimitImpl` fully. Every `case` is a **critical business rule** that must appear with exact numeric values: "The Branch Manager may approve loan proposals with a requested amount between [min] and [max] units."
5. If a `runProcessFullFlowAtOnce` exists, read it — represents auto-approval and produces its own Event-Driven requirements.
6. Rule engines deserve their own `Module: Approval Workflow` section.

#### Procedure C — Shared DAO implementations

Lib DAO implementations are **first-class business logic sources** — treat identically to main-app DAOs (Step 2d):
- Read every SQL query. Extract filter conditions, sort order, JOINs, aggregations, dynamic WHERE clauses.
- Note which datasource each DAO uses (main, ERP, report) and label requirements accordingly.
- Inline row-mapper lambdas — read the mapper body for conditional mapping.
- `Collections.emptyList()` with commented-out logic → `[DISABLED]` requirement.

#### Procedure D — Access-control library
- Read the `@Filter` / `OncePerRequestFilter` to understand request-time decisions.
- Read the DAO that loads permissions. Extract the layered permission model from its SQL.
- Produce EARS statements describing: how the system resolves permitted operations, what happens when a user lacks permission, how feature-level groupings control access.
- This belongs in the `Authentication and Authorisation` subsection of Cross-Cutting Requirements.

#### Interface-only lib modules
- List every interface and its method signature.
- During Step 0i / Step 2b, locate the main-app implementation and trace it. Do not produce EARS statements from the interface alone.

### 0h. Read i18n message files
- Find `messages.properties`, `messages_bn.properties`, equivalents.
- These contain exact user-facing message wording. Apply Rule 5: quote messages verbatim.

### 0i. Identify all queue entry points (async consumers)
- Find every Spring Cloud Stream `Consumer<T>` bean, `@KafkaListener`, `@RabbitListener`, equivalent.
- Find every DLQ consumer — represents error-recovery business requirements.
- Find every queue producer (`StreamBridge`, `KafkaTemplate`, `RabbitTemplate`).

### 0j. Identify all scheduled operations
- Find every `@Scheduled` method (including manual-trigger REST endpoints).
- Commented-out `@Scheduled` methods → capture as Optional `[DISABLED]` requirements.

### 0k. Identify all external system integrations
- Find every Feign client, `RestTemplate` bridge, `WebClient`, ERP/third-party SDK call.
- For each: business operation, data sent, response expected, error/timeout handling (Resilience4j fallbacks, retries, circuit breakers).
- Read-only external datasources (e.g., ERP DB via JDBC) → integration requirement: "When [operation], the <Domain> system shall retrieve [data] from the ERP system."

### 0l. Read all enum types used by entities and DTOs — MANDATORY full enum scan
- **Locate and open every enum source file** under `lib/shared-dto/.../enumeration/` (or the project's equivalent enum folder). Use `find . -path "*shared-dto*" -name "*.java" -path "*enumeration*"` if the folder layout is unclear.
- For every enum referenced (directly or transitively) by any controller, service, DAO, validator, or DTO in the call chain — **read its full source file**. Capture every enum constant's:
  - Constant identifier (e.g., `PENDING`, `L_216`, `DM`)
  - Numeric ID, if any (e.g., `LoanProposalStatus.PENDING = 1`)
  - Display name / label string (e.g., "Divisional Manager", "Date range should not exceed 24 hours")
  - Bengali translation, if present
- These populate the **Domain Concepts and States** section as Markdown tables (Rule 12). Every enum used in any EARS statement, and every status value the entity can transition through, must appear there with its full business meaning — not just the values the agent happened to see in controller code.
- Common enum families to confirm coverage of: status enums (loan/member/account), approval workflow enums, payment mode sub-types, role/designation enums, channel/data-source enums, insurance type enums, age-group enums, error-message enums (`*Message`, `*PreValidationMessage`).
- If an EARS statement says "the Loan Proposal system shall set the proposal status to <X>", then `<X>` must be a value present in the status enum table.
- **Guessing display names is forbidden.** If the role short-code is `DM`, you must read the `LoanApprover.java` / `EmployeeDesignation.java` enum and use the exact name found there — never write "Deputy Managing Director" when the enum says "Divisional Manager".

### 0m. Read all ID generators and number-format generators
- Find every interface and impl named `*IdGenerator*`, `*NumberGenerator*`, `*SequenceGenerator*`, `Snowflake*`, or producing identifiers in the call chain (e.g., a service method called `generateLoanProposalNumber`, `generateAccountNumber`, `generateReferenceNumber`).
- Read the generator's implementation fully. Extract:
  - The format pattern (prefix, branch code, business-date encoding, sequence suffix)
  - Whether the value is globally unique or branch-scoped
  - The source of the sequence (database table, Redis counter, Snowflake node ID)
- Express the result as a Ubiquitous or Event-Driven requirement, never as a `[NEEDS REVIEW]` open question.

---

## Step 1 — Determine Input Mode

After completing Step 0, identify which input mode applies:

| Mode | Trigger | Action |
|------|---------|--------|
| **Single controller** | User provides one `.java` file path | Process that file, then run **Step 1.5** to discover and confirm its lifecycle siblings. |
| **Multiple controllers** | User provides a list of `.java` file paths | Process each in order, then run **Step 1.5** to discover and confirm any further lifecycle siblings. |
| **Auto-discover** | User provides a directory path | Recursively find all `*Controller.java` files under that directory. List them and confirm with the user before proceeding. (Step 1.5 is unnecessary here — the directory already enumerates the scope.) |

Also list and confirm all queue consumer entry points from Step 0i — but only if they belong to the controllers' call chain or the user explicitly asks for them.

---

## Step 1.5 — Lifecycle Sibling Controller Discovery (Discover + Confirm)

A single controller rarely covers a domain's whole lifecycle. `LoanProposalOtcRestController` handles create/update/delete/get/list, but approval, rejection, and good-loan decisions live in **sibling** controllers (`LoanApproveOtcRestController`, `goodloan/GoodLoanApprovalOtcRestController`, …). Extracting only the named controller produces a spec that silently omits the entire approval half of the domain. This step closes that gap **without** silently pulling in unrelated endpoints: discover the siblings, show them, and let the user confirm the scope.

**Skip this step only when** the input mode is Auto-discover (directory already enumerates everything) or the user explicitly says "only the controller(s) I named."

**1. Derive the domain root.** From each named controller, strip the channel/role/`RestController` suffix to get the domain root token and channel — e.g. `LoanProposalOtcRestController` → root `LoanProposal`, channel `Otc`.

**2. Discover candidate siblings (deterministic, cheap sweep):**
   - **Same directory + nested sub-packages** of the named controller. List the controller's own directory and its immediate sub-folders:
     ```
     find <controller-dir> -maxdepth 2 -name '*RestController.java' -o -name '*Controller.java'
     ```
     (e.g. `controller/otc/` plus `controller/otc/{goodloan,dcs,migration,report,...}/`).
   - **Name-pattern match across `controller/`** — the domain root token paired with a **lifecycle verb**: `Approve` / `Approval`, `Reject`, `Disburse` / `Disbursement`, `GoodLoan`, `Callback` / `Consumer`, `Monitor`, `Dedupe` (and other migration/tooling verbs):
     ```
     grep -rlE 'class .*(LoanProposal|LoanApprove|GoodLoan|Disburse|Reject|Monitor).*Controller' src/main/java/.../controller/
     ```
   - **Strongest signal — shared core validator/service.** Controllers whose call chain invokes the **same core validator/service** as the named controller (e.g. the buffer loan-proposal validator / buffer loan-proposal service) are near-certainly the same domain's lifecycle stages. Grep for that validator/service type across `controller/`, or run `graphify query "<CoreValidator> callers"`. A shared core validator is near-conclusive evidence of lifecycle membership and outranks name matching.

**3. Classify each candidate by lifecycle role** so the list is scannable: Proposal Management / Approval / Rejection / Disbursement / Good-Loan / Callbacks / Monitoring / Migration-tooling.

**4. Present + confirm via a checkbox multi-select.** Surface the discovered candidates as an explicit **`AskUserQuestion` with `multiSelect: true`** so the user ticks the controllers to include — never as free-form prose. Build the question as follows:

   - **One checkbox option per candidate controller.** Option *label* = the controller class name; option *description* = its lifecycle role plus the relevance signal that surfaced it (e.g. "Approval — shares the buffer loan-proposal validator", "Monitoring — name-pattern match in `controller/otc/report/`").
   - **Recommend the core lifecycle set.** The named controller plus its Approval, Rejection, and Good-Loan / Disbursement siblings (the set a reviewer expects a "loan proposal" spec to cover) are the suggested default: append `(Recommended)` to each of those option labels and **list them first**. State in the question text that the recommended set is the suggested default and that unticked candidates (monitoring / migration / callback) are optional add-ons. Always include the named controller itself as a `(Recommended)` option so the list is self-describing.
   - **Option-count fallback (`AskUserQuestion` allows 2–4 options per question, up to 4 questions per call).**
     - **≤ 4 candidates:** a single `multiSelect` question, one option per controller.
     - **> 4 candidates:** split into multiple `multiSelect` questions **grouped by the lifecycle role from item 3** (Proposal Management / Approval / Rejection / Disbursement / Good-Loan / Monitoring / Migration), recommended roles first, up to the 4-question limit. If the role-groups still exceed 4 questions, fold the least-likely groups (monitoring / migration / callback) into a single "include these supporting controllers too" bundle option on the last question.
   - The user's ticked options become the confirmed scope handed to item 5.

**5. Lock the scope.** The user-confirmed set becomes "the controllers being processed" for all downstream steps: Rule 7 module derivation, the `Source Controller(s)` header line, and the Extraction Summary controller list. Per Rule 7's shared-validator deduplication, controllers in the confirmed set that share a core validator produce **one consolidated `Module: <Domain> Validation Rules`** — not a repeated rule set per controller (this is exactly how a full-lifecycle spec is structured).

**No silent expansion, no silent omission.** Never extract a sibling the user did not confirm; never hide a discovered sibling from the user. The user owns the scope decision — Step 1.5 only makes the options visible and recommends the complete-lifecycle default.

---

## Step 2 — Build the Full Call Chain for Each Entry Point

An "entry point" is any REST controller endpoint **or** any queue consumer method. For **each** entry point, trace every dependency completely before writing a single EARS statement.

### 2a. Read the controller or consumer entry point
- **Controller:** For each endpoint method record HTTP verb, URL path, request body type, response type, security annotations, and every service it calls.
- **Queue consumer:** Identify payload type, queue/topic/exchange, services called.
- **DLQ consumer:** Note it handles failed messages — extract the retry/recovery logic.

### 2b. Follow every service call
- For each service class, read the full **implementation** (not just the interface).
- If the implementation is in a shared `lib/` module, read it from there.
- `@Transactional` → capture as an atomicity requirement.
- If the service calls a lib validator (Procedure A), trace it completely. Every conditional branch becomes its own Unwanted Behaviour statement.

### 2c. Follow every JPA repository call
- Read every `@Query` method and `Specification`.
- Read the entity fully: field-level constraints, relationships, `@PrePersist` / `@PreUpdate` hooks, enum fields.
- **Catalog every property into the Domain Entities and Properties section (Rule 13).** Reading an entity is not done until **every field it declares** is recorded there as a `| Property | Type | Meaning | Constraints |` row — a complete mirror of the JPA entity class, including fields no traced behaviour references — with the **exact codebase field name** in the `Property` column (Rule 13). This is in addition to extracting field-level *rules* as Unwanted Behaviour statements — the catalog captures the data model; the statements capture the rules.
- **Follow every association to another entity (`@ManyToOne`, `@OneToMany`, `@OneToOne`, `@ManyToMany`, or a foreign-key/reference property) and catalogue the referenced entity as its own `###` sub-block (Rule 13)** — recursively, with no depth limit. Then repeat for any entity *it* references, continuing until the reference closure is exhausted. An entity already cataloged in this run is **not** re-read or re-cataloged (catalog once, then cite). Shared infrastructure entities (user/office/branch/organization) follow the same rule: read and catalog on first reach, then only name. A referenced entity is catalogued in full even if no business rule reads it; being referenced is sufficient. Likewise, any enum named as a property type is read in full (Step 0l) so its complete value table exists in Domain Concepts and States.
- JSON column fields (structured JSON) → embedded domain objects with their own rules **and their own entity sub-block in the catalog** (Rule 13). Child entities are catalogued as their own sub-blocks too.
- Shared audit/soft-delete/version fields **are** listed as rows in each entity's table (they are part of the complete field set); only their lifecycle semantics are referenced once from the Step 0b note rather than re-explained per entity.

### 2d. Follow every JDBC DAO call
- DAOs are **first-class business logic sources**. Apply Procedure C.
- Extract filter conditions, sort order, pagination, aggregations, JOINs, conditional SQL fragments.
- Identify datasource (main / ERP / report / auxiliary) and label requirements accordingly.

### 2e. Follow every RowMapper call
- Read fully. Extract conditional mapping, derived/calculated fields, null-handling.

### 2f. Follow every Feign client and external HTTP integration call
- Extract: business trigger, data sent, expected response, Resilience4j fallback, retry config, circuit-breaker open-state behaviour.

### 2g. Follow every Spring ApplicationEvent publish and listener
- Identify event type, listener behaviour, sync vs. async, `@TransactionalEventListener(phase=AFTER_COMMIT)` semantics.

### 2h. Read supporting classes
- **DTOs / Request-Response objects:** Every field-level validation annotation (`@NotBlank`, `@Email`, `@Min`, `@Max`, `@Pattern`, `@Size`, `@NotNull`, custom `@ValidX`) → one Unwanted Behaviour per constraint, placed in the dedicated field-level subsection (Rule 6).
- **Custom `@ValidX` `ConstraintValidator.isValid()`:** Read fully; the logic is a business rule.
- **Enum types:** Every value is a domain state. Capture in Domain Concepts and States (per Rule 12 and Step 0l — full enum source must be read).
- **Exception classes:** Exception message informs the Unwanted Behaviour wording.

### 2i. The "named-not-read" prohibition

If at any point you mention a method name, helper name, validator name, sub-validator name, enum name, or generator name in your working notes or in a draft `[NEEDS REVIEW]` item — you must have **opened the file and read the body** before finalising the output. Naming without reading is the single largest source of unnecessary `[NEEDS REVIEW]` items.

Concrete examples:
- Mention of `checkLoanInterestRate` → open the validator file, read that method's body, extract its rules.
- Mention of `LoanProposalAgeLimitValidationImpl` → open that class, apply Procedure A in full.
- Mention of `BufferLoanPreValidationMessage.L_216` → open the enum file, read what `L_216` means.
- Mention of `generateLoanProposalNumber` → find and read the impl (Step 0m), extract the format.

If reading the file genuinely fails (file not found after search, file is a binary, etc.), record that failure verbatim in the Open Questions footer (Rule 8): `*Where agent looked:* searched for `<glob pattern>` — no matching file found.`

---

## Step 3 — Handle Ambiguity

### Step 3a.0 — Mandatory pre-NEEDS-REVIEW gates (Rule 9 enforcement)

Before any `[NEEDS REVIEW]` item is allowed to enter the Open Questions section, **all of these gates** must have been performed (each one that applies to the ambiguity). Record what was tried so it can be cited in the Rule 8 footer.

| Gate | When required | Action |
|------|---------------|--------|
| **Enum source** | Ambiguity names an enum value, message code, or numeric constant | Open `lib/shared-dto/.../<EnumName>.java`. List every value's label. |
| **Validator body** | Ambiguity names a validator method (`check*`, `validate*`, `is*Valid`) | Open the validator file, read the method body fully. Apply Procedure A. |
| **Sub-validator impl** | Ambiguity names an injected validator (`xxxValidator`, `xxxValidation`) | Open the `*Impl` class. Apply Procedure A recursively. |
| **Access-control DAO** | Ambiguity concerns roles, permissions, endpoint authorisation | Open `lib/access-control/.../AccessControlDaoImpl.java` + relevant Flyway migration. |
| **Queue/REST entry point** | Ambiguity concerns whether a method is consumer, listener, or REST | Grep for `@KafkaListener`, `@PostMapping`, `@Scheduled`, `Consumer<` over that method name. |
| **ID/format generator** | Ambiguity concerns the format of a generated identifier | Open the generator interface and impl. Read the format pattern. |
| **Delegated rule-object / specification** | Ambiguity concerns a dispatcher over a set/chain of rule or strategy objects (`*Rule`, `*Specification`, `isSatisfiedBy`/`test`) | Open every dispatched rule class, read its predicate body (Step A-6). |
| **Dynamic-message / mapping-service** | A rejection message is returned by a called service, not written in the validator | Open the service `*Impl` + its backing mapping/seed data (Step A-7). |

Skipping a gate is not allowed. If a gate genuinely cannot resolve the ambiguity (the file does not contain the answer), say so explicitly in the Rule 8 `*Where agent looked:*` footer — quote the file path and the line range read.

### Step 3a — Resolve From Project Sources Before Asking the User

If the Step 3a.0 gates do not yield an answer, broaden the search through these sources in order (stop at the first that answers):

1. **Test classes** — `src/test/`. Grep for the constant/concept name. Tests often assert the exact business value.
2. **Application config** — `src/main/resources/application*.yml` / `.properties`.
3. **Flyway migration files** — `src/main/resources/migration/`. Column constraints, lookup seed data, unique constraints.
4. **Shared DTO constants and enums** — `lib/shared-dto/` (most should already have been read in Step 0l).
5. **Domain documentation** — `DOMAIN_SUMMARY.md`, `loan/loan-poposal-data-mapping-*.md`.
6. **Technical documentation** — `doc/` folder.
7. **Graphify knowledge graph** — `graphify-out/`. Use `graphify query "<concept>"`, `graphify path "<A>" "<B>"`, `graphify explain "<concept>"`.
8. **Git history** — `git log --all --oneline --grep="<keyword>"`, `git log -p -- <file>`.

Only after the Step 3a.0 gates AND all eight broader sources fail may an item be marked `[NEEDS REVIEW]`. Do not interrupt the user mid-extraction; collect all unresolved items and present them at the end with their Rule 8 footers.

### Step 3b — Interactive Questions (After Exhausting Project Sources)

For remaining ambiguities that even Step 3a cannot resolve, pause and ask the user a precise question before writing the requirement. Group multiple questions together rather than asking one at a time.

### Step 3c — Open Question authoring (Rule 8 format)

When you decide an item must be `[NEEDS REVIEW]`, write it now in the exact two-footer format so the reviewer can pick up the trail:

```
N. **[NEEDS REVIEW]** <Concrete question phrased so a domain expert can answer in one or two sentences.>
   *Where agent looked:* `<relative/path.java>:<line>` — <what was read and why it was insufficient>. `<another/path.java>:<line>` — <same>.
   *Hint for reviewer:* Likely answer in `<probable/file.java>` (<one-sentence reasoning>). Try `<grep or graphify or find command>` to locate.
```

**Both footer lines are mandatory.** A `[NEEDS REVIEW]` item without both footers is rejected by Step 7 — either fix it by reading more files, or fill the footers with the literal record of what failed.

Bad examples (do not write these):
- `1. **[NEEDS REVIEW]** What is the format of the loan proposal number?`  ← no footers.
- `1. **[NEEDS REVIEW]** What is X? The method `generateX` was observed.`  ← method named but not read, no footer.

Good example:
```
1. **[NEEDS REVIEW]** What is the exact format of the loan proposal number generated for a new OTC proposal? Does it encode the branch code, business date, and a sequence suffix?
   *Where agent looked:* `src/main/java/com/bracits/kyc/service/buffer/LoanProposalServiceImpl.java:245` — calls `loanProposalNumberGenerator.generate(branchId, proposalId)` but the generator implementation could not be located. Searched `find . -name "LoanProposalNumberGenerator*Impl*.java"` — no match.
   *Hint for reviewer:* Likely answer in `lib/shared-service-impl/` under a class implementing `LoanProposalNumberGenerator`. Run `graphify query "LoanProposalNumberGenerator implementation"` or `grep -r "implements LoanProposalNumberGenerator" lib/ src/main/java/` to confirm.
```

---

## Step 4 — EARS Pattern Selection

Apply in priority order. A single behaviour may produce multiple statements of different types.

### Priority 1 — Event-Driven
**Syntax:** `When <trigger>, the <DomainName> system shall <response>.`
Use for behaviour triggered by an external actor, internal event, or queue message.

### Priority 2 — State-Driven
**Syntax:** `While <state>, the <DomainName> system shall <response>.`
Use when behaviour only occurs while the system or an entity is in a particular state.

### Priority 3 — Unwanted Behaviour
**Syntax:** `If <unwanted condition>, the <DomainName> system shall <response>.`
Use for every validation rule, guard clause, exception path. Every `if` that throws or returns an error becomes one of these.

### Priority 4 — Optional
**Syntax:** `Where <feature or condition is enabled>, the <DomainName> system shall <response>.`
Use for feature flags, Spring profiles, tenant/env config, disabled schedules.

### Priority 5 — Ubiquitous
**Syntax:** `The <DomainName> system shall <response>.`
Use for cross-cutting rules that always apply.

### Priority 6 — Complex
**Syntax:** `While <state>, when <trigger>, the <DomainName> system shall <response>.`
Or: `Where <feature>, when <trigger>, the <DomainName> system shall <response>.`

---

## Step 5 — Produce the EARS Output File

Write the output to `docs/ears/<DomainName>-EARS-Specification.md` (project-relative). **Overwrite** any existing file with the same name. If the `docs/ears/` directory does not exist, create it.

The top-level skeleton is fixed (per Rule 11). The **Module sections in the middle are NOT fixed** — they are derived from the controllers being processed per Rule 7 (lifecycle-driven, with content-threshold gates for cross-cutting modules). Never invent unrelated top-level sections. Never include a Table of Contents (Rule 10).

### Output File Template

The `> **Source Controller(s):**` line lists the full project-relative path of every controller in the **confirmed Step 1.5 scope** (the named controller(s) plus the lifecycle siblings the user confirmed) — comma-separated if more than one. Never list a discovered sibling the user did not confirm.

```
# <DomainName> — <Channel/Scope> Business Requirements Specification (EARS)

> **Format:** Easy Approach to Requirements Syntax (EARS)
> **Source:** Reverse-engineered from existing codebase — <Project Name> (`<gradle-name>`), base package `<base.package>`
> **Source Controller(s):** `<relative/path/to/Controller1.java>`[, `<relative/path/to/Controller2.java>` …]
> **System name used in statements:** the <DomainName> system
> **Purpose:** Standalone, architecture-neutral specification for system regeneration
> **Note:** All requirements are expressed in plain business language with no code references in the statement text. Each module and content subsection is annotated with a `> **Source files:**` line listing the source files it was extracted from, so a developer can cross-check the spec against the codebase.

---

## Document Conventions

| Marker | Meaning |
|--------|---------|
| `[NEEDS REVIEW]` | Ambiguous logic — verify with domain expert before use |
| `[UNRESOLVED: X]` | Referenced component X could not be fully located in the codebase |
| `[INFERRED]` | Behaviour inferred from standard framework convention; no explicit code found |
| `[DISABLED]` | Feature exists in the codebase but is currently switched off |
| `Review by Developer` | Two sections at the end of this file where a developer records findings from reviewing this spec against the codebase; consumed by `/fix-dev-reviews` |

---

## System Overview

<One rich domain narrative paragraph (5–8 sentences). Cover: what the system manages, the lifecycle scope, which channels it spans, what validation layers it enforces, how this channel differs from sibling channels (e.g., OTC's single-step branch approval vs. Smart PO's multi-stage escalation). Derived from controller names, entity names, package structure, domain summary files. No code references.>

---

## Cross-Cutting Requirements

### Audit and Record Lifecycle

<Ubiquitous statements from abstract base entity: creation audit, update audit, soft delete, optimistic locking, deleted-flag/version init defaults, Snowflake ID generation, timezone. One paragraph per rule.>

### Authentication and Authorisation

<Optional statements for profile-gated security (OAuth2, device identity, DCS client). Then the role-based access control matrix as a sub-list using `-` bullets:>

The <DomainName> system shall enforce the following role-based access controls for all <Channel> operations:

- When an actor <operation A>, the <DomainName> system shall require the actor to hold <role list>.
- When an actor <operation B>, the <DomainName> system shall require the actor to hold <role list>.

If an authenticated actor attempts to access an operation without the required role, the <DomainName> system shall reject the request with an access-denied error.

<Then the access-control library statement.>

### Request Handling

<Ubiquitous and Unwanted statements from filters: request/response logging, trace-ID header, payload size limit (with exact byte count), CORS policy. One paragraph per rule.>

### Operational Cross-Cuts

<Optional and Ubiquitous statements from aspects: business-date validation, captcha, distributed scheduler lock, unhandled exception logging. One paragraph per rule.>

### Error Response Format

The <DomainName> system shall return all error responses in a structured bilingual payload containing: <enumerate the actual fields — trace identifier, timestamp, HTTP status, English message, Bengali message, request path, field-level error details list>.

The <DomainName> system shall map error conditions to HTTP status codes as follows:

| Error condition | HTTP status |
|-----------------|-------------|
| <Plain-English condition name (NOT exception class name)> | <status code> |
| … one row per ExceptionHandler mapping found in @ControllerAdvice … |

If the error condition corresponds to an i18n message key, the <DomainName> system shall resolve the message in both English and Bengali from the message catalogue and include both translations in the error response.

---

<!--
  MODULE SECTIONS — derived per Rule 7 (lifecycle + cross-cutting thresholds).
  NOT a fixed skeleton. Only include the modules that the controllers actually produce.

  Per-controller primary modules — one per controller, named after the lifecycle role:
    - CRUD controller        → "Module: <Domain> — <Channel> (Proposal Management)"
    - Approval controller    → "Module: <Domain> — <Channel> Approval"
    - Disbursement controller→ "Module: <Domain> — Disbursement"
    - Callback consumer      → "Module: <Domain> — Callbacks" / "— Notifications"
    - Monitoring endpoints   → "Module: <Domain> Monitoring"

  Cross-cutting modules — include ONLY if the threshold is met (Rule 7 table):
    - "Module: <Domain> Validation Rules"            (validator with >5 if-branch rules)
    - "Module: Sub-Validators"                        (≥2 specialised sub-validators)
    - "Module: Async and Queue Processing"            (any async side effect fires)
    - "Module: External System Integrations"          (any outbound external call)

  Do NOT include empty placeholder modules. Omit entirely if no content.
  If multiple controllers share a validator, produce ONE consolidated Validation Rules module.
-->

## Module: <DomainName> — <Channel> (<Sub-Scope, e.g. Proposal Management>)

> **Domain:** <human-readable name>
> **Scope:** <1–2 sentences describing what this module covers>
> **Entry Points:** REST API
> **Source files:** `<relative/path/to/EntryPointController.java>`, `<relative/path/to/ServiceImpl.java>`, `<… every file feeding this module …>`

### <Functional Area, e.g. "Proposal Creation">

> **Source files:** `<relative/path/to/ServiceImpl.java>`, `<relative/path/to/Validator.java>`, `<relative/path/to/RequestDto.java>`

<Event-Driven happy-path paragraphs first, then State-Driven guards, then Unwanted Behaviour rejections. Each paragraph is a standalone EARS statement.>

**Field-level validation — <RequestName>:**

If <field> is not provided, the <DomainName> system shall reject the request.

If <field> is negative, the <DomainName> system shall reject the request.

<… one paragraph per field-level annotation in the request DTO …>

### <Next Functional Area>
<EARS statements>

---

<!-- Include the following module ONLY if Rule 7 threshold met:
     ≥ 6 if-branch validation rules invoked by the traced controllers. -->

## Module: <Proposal/Domain> Validation Rules

> **Domain:** Business Rule Validation — <Scope>
> **Scope:** All validation rules applied by the standard validator during the operations traced in the per-controller modules above. These rules execute after field-level request validation and before persistence. If multiple controllers share this validator, all share these rules.
> **Entry Points:** Invoked internally by the controllers above.
> **Source files:** `<relative/path/to/Validator.java>`, `<relative/path/to/ValidatorImpl.java>`, `<… every validator/sub-validator/enum file feeding these rules …>`

### <Validation Concern, e.g. "Member Eligibility and Identity">

> **Source files:** `<relative/path/to/Validator.java>`

<One paragraph per if-branch.>

### <Validation Concern, e.g. "Project, Policy, and Reference Data">

> **Source files:** `<relative/path/to/Validator.java>`

<EARS statements>

### <Validation Concern, e.g. "Loan Product, Details, Policy, and Frequency">
<EARS statements>

### <… one subsection per cohesive group of validation rules …>

---

<!-- Include ONLY if ≥ 2 specialised sub-validator classes are invoked.
     If only 1, fold it into Validation Rules as a subsection instead. -->

## Module: Sub-Validators

> **Domain:** Specialised Domain Validation — <list the actual sub-validator concerns, e.g. Migration Loans, Fire Insurance, Digital Disbursement, Bank Mode of Payment>
> **Scope:** Domain-specific validation rules applied as part of the main validation flow.
> **Source files:** `<relative/path/to/SubValidator1Impl.java>`, `<relative/path/to/SubValidator2Impl.java>`, `<… one per sub-validator class …>`

### <Sub-Validator, e.g. "Migration Country Validation">

> **Source files:** `<relative/path/to/MigrationCountryValidatorImpl.java>`

<EARS statements>

### <Sub-Validator, e.g. "Fire Insurance Validation">
<EARS statements>

### <… one subsection per sub-validator class traced in Procedure A …>

---

<!-- Include ONLY if any async side effect fires from the traced controllers
     (queue publish, search index update, async @TransactionalEventListener). -->

## Module: Async and Queue Processing

> **Domain:** Asynchronous Data Synchronisation
> **Scope:** All asynchronous side effects triggered after successful operations in the modules above — including full-text search indexing and message queue publishing.
> **Source files:** `<relative/path/to/SearchIndexService.java>`, `<relative/path/to/QueueProducer.java>`, `<relative/path/to/Listener.java>`

### <Pipeline, e.g. "Speed Search Indexing">

> **Source files:** `<relative/path/to/SearchIndexServiceImpl.java>`

<EARS statements>

### <Pipeline, e.g. "Kafka Data Pipeline">

> **Source files:** `<relative/path/to/KafkaPublisherImpl.java>`

<EARS statements, with [DISABLED] markers where the feature flag is off by default>

### <Recovery Path, e.g. "Failed Sync Recovery">

> **Source files:** `<relative/path/to/DlqConsumer.java>`

<EARS statements>

---

<!-- Include ONLY if the traced controllers make any outbound external call:
     Feign client, ERP DB JdbcTemplate call, third-party HTTP, search engine, payment middleware. -->

## Module: External System Integrations

> **Domain:** Third-Party and Internal System Integrations
> **Scope:** All outbound calls to systems outside the <DomainName> system's direct ownership.
> **Source files:** `<relative/path/to/FeignClient.java>`, `<relative/path/to/ErpDao.java>`, `<relative/path/to/MiddlewareClient.java>`

### <Integration, e.g. "ERP System (Read-Only)">

> **Source files:** `<relative/path/to/ErpDaoImpl.java>`

<EARS statements>

### <Integration, e.g. "Full-Text Search Engine (Speed Search / Elasticsearch)">

> **Source files:** `<relative/path/to/SearchEngineClient.java>`

<EARS statements>

### <Integration, e.g. "Digital Disbursement Middleware (Post-Approval)">

> **Source files:** `<relative/path/to/DigitalDisbursementClient.java>`

<EARS statements>

---

## Domain Entities and Properties

> Shared audit fields (creation/update by + at), optimistic-locking version, and any soft-delete flag are listed as rows in every entity table below (they are part of each entity's complete field set); their lifecycle semantics are described once under Cross-Cutting Requirements → Audit and Record Lifecycle and are not re-explained per entity. The `Property` column uses the exact codebase field name; plain English goes in `Meaning`.

<!--
  REFERENCE CLOSURE (Rule 13):
  - Every entity named as a `Reference to <Entity>` / `List of <Entity>` Type below — and, transitively, every entity those referenced entities point to — MUST have its own ### block here with a complete | Property | Type | Meaning | Constraints | table.
  - COMPLETE FIELD SET: every entity table — in-scope AND externally-owned alike — mirrors the FULL field list declared in its source class: one row per declared field, including audit/version/soft-delete fields, including fields no requirement references. A partial "only the fields the traced code touched" table is FORBIDDEN. Open the entity class and enumerate all declared fields.
  - FORBIDDEN: merging multiple referenced entities into a single "### Externally-owned reference entities" prose block. Each entity — regardless of which module/service owns it — gets its own ### sub-block. Module ownership goes in the entity's description sentence only and is never a reason to list fewer fields.
  - Catalog each entity ONCE (first reach); later mentions just name it. Shared infrastructure entities (user/office/branch/organization) are cataloged once like any other, never repeated, never skipped.
  - Property column uses the EXACT codebase camelCase field name from the source (`proposalNumber`, `proposedLoanAmount`) — never a capitalised or paraphrased business name.
  - Every `Enum (<Name>)` Type must have its full value table in `## Domain Concepts and States`. No type may be named without its properties/values existing.
  - Before finalizing: run the reference-closure inventory — list every distinct entity named as Reference to / List of across all rows; confirm each has a ### block. Zero gaps allowed.
-->

### <Entity, e.g. "Loan Proposal">

> **Source files:** `<relative/path/to/LoanProposalEntity.java>`

<One plain-language sentence describing what this entity represents.>

| Property | Type | Meaning | Constraints |
|----------|------|---------|-------------|
| <exactFieldName, e.g. proposalNumber> | <Amount / Date / Identifier / Text / Enum (<name>) / Reference to <Entity> / …> | <plain English> | <required/optional, range, uniqueness, default, relationship cardinality, governing enum> |
| … one row per domain-specific property … |

### <Embedded JSON object or child entity, e.g. "Loan Proposal Guarantor">

> **Source files:** `<relative/path/to/GuarantorEntity.java>`

<One plain-language sentence.>

| Property | Type | Meaning | Constraints |
|----------|------|---------|-------------|
| … |

### <Referenced entity, e.g. "Member" — reached via a `Reference to Member` property above; catalogued in full>

> **Source files:** `<relative/path/to/MemberEntity.java>`

<One plain-language sentence.>

| Property | Type | Meaning | Constraints |
|----------|------|---------|-------------|
| <exactFieldName> | <… (its own `Reference to <Entity>` properties recurse into further sub-blocks) …> | <plain English> | <…> |

### <… one sub-block per entity in the traced call chain AND per entity reached through a reference, deduplicated …>

---

## Domain Concepts and States

### <Primary Entity, e.g. "Loan Proposal">

> **Source files:** `<relative/path/to/LoanProposalStatus.java>`, `<relative/path/to/LoanProposalEntity.java>`

<One paragraph describing the entity in plain business language.>

**<Entity> States:**

| State Name | Business Meaning |
|------------|-----------------|
| Pending | <plain English> |
| Approved | <plain English> |
| … one row per enum value, in business-logical order, NOT enum-declaration order … |

**<Channel> State Transitions:**

| From State | To State | Triggered by |
|------------|----------|-------------|
| (new) | Pending | Actor submits a new <X> via the <channel> |
| Pending | <next state> | <business event> |
| … one row per transition discovered in the codebase … |

### Approval Status

| State Name | Business Meaning |
|------------|-----------------|
| <value> | <meaning> |

<Plus a paragraph noting how the ERP integration translates these values, if applicable.>

### Digital Disbursement Status

| State Name | Business Meaning |
|------------|-----------------|

### Approval Flow Status

| Value | Business Meaning |
|-------|-----------------|

### Loan Approver Role Chain (or equivalent role hierarchy)

| Role | Full Name | Scope |
|------|-----------|-------|
| BM | Branch Manager | <scope> |
| AM | Area Manager | <scope> |
| … |

<A paragraph explaining the chain — which path applies to which channel.>

### <Domain Type Enum, e.g. "Loan Proposal Type">

| Type Name | Business Meaning |
|-----------|-----------------|

### Data Source

| Source Name | Business Meaning |
|-------------|-----------------|

### <Operational Enum, e.g. "Mode of Payment Sub-types">

| Sub-type | Business Meaning |
|----------|-----------------|

<… one table per enum collected in Step 0l …>

---

## Business Rules Summary

<A flat numbered list of the most critical non-obvious business rules — approval thresholds, amount limits, eligibility criteria, date constraints, parallel-loan restrictions, channel-exclusion rules, key configuration values. Aim for 15–25 items for a typical large module. Each item is one or two sentences.>

1. <Rule>
2. <Rule>
3. <Rule>
…

---

## Open Questions

A numbered list of the `[NEEDS REVIEW]` items that **remained unresolved after the Step 6.5 auto-resolution pass** (items resolved in-pass are folded into the spec and do not appear here). Each item carries the two mandatory footer lines per Rule 8 — *Where agent looked* and *Hint for reviewer* — so the reviewer can pick up the trail without re-doing the trace.

1. **[NEEDS REVIEW]** <Concrete question a domain expert can answer in one or two sentences.>
   *Where agent looked:* `<relative/path.java>:<line-range>` — <what was read and why insufficient>. `<another/path.java>:<line>` — <same>.
   *Hint for reviewer:* Likely answer in `<probable/file.java>` (<one-sentence reasoning>). Try `<grep / find / graphify command>` to locate.

2. **[NEEDS REVIEW]** <Question>
   *Where agent looked:* …
   *Hint for reviewer:* …

…

---

## Extraction Summary

| Metric | Count |
|--------|-------|
| Controllers processed | <N> (`<ControllerName1>`, `<ControllerName2>`, …) |
| Queue consumers processed | <N> |
| Scheduled jobs processed | <N> |
| Lib modules traced | <N> (`<lib1>`, `<lib2>`, …) |
| Total EARS statements | <N> |
| Event-Driven (`When` + `After`) | <N> |
| State-Driven (`While`) | <N> |
| Unwanted Behaviour (`If`) | <N> |
| Optional (`Where`) | <N> |
| Ubiquitous (`The <DomainName> system shall`) | <N> |
| Complex (`While … when`) | <N> |
| Open Questions auto-resolved in-pass (Step 6.5) | <N> |
| [NEEDS REVIEW] items (residual, unresolved) | <N> |
| [UNRESOLVED] items | <N> |
| [DISABLED] items | <N> (briefly note what is disabled) |
| Rule-sites inventoried | <N> (across all files entering the Step A-2.1 protocol) |
| Rule-sites covered by a statement | <N> |
| Rule-sites uncovered | 0 (must be zero after Step 6 verification) |

**Per-file coverage ledger** (one line per source file > ~500 LOC entering Step A-2.1):

- `<File>.java` (<T> LOC): <sites> rule-sites · <accounted> accounted · 0 uncovered
- … one line per large file in the call chain …

**Extraction completed:** <Day, DD Month YYYY> (use the runtime current date)

---

## Review by Developer (code)

<!-- Developer: after reviewing this spec against the codebase, list source-code references to rules
     that are MISSING from this spec. One finding per line. Pointer precision helps the agent:
       - [ ] `File.java#method`            — what rule is missing   (most precise)
       - [ ] `File.java:120-145`           — what rule is missing
       - [ ] `File.java`                   — what rule is missing   (whole file)
       - [ ] a plain note with no pointer  (agent auto-locates from the description)
     Optionally force placement by appending:  → Module: <Module> › <Subsection>
     Run /fix-dev-reviews <this-file> to process; it checks each entry off and annotates where it landed. -->

_None yet — add findings above._

---

## Review by Developer (business requirements)

<!-- Developer: list business decisions/requirements that need a human answer (no code expected).
     One per line; these become [NEEDS REVIEW] Open Questions.
       - [ ] <the business decision or requirement needed, one sentence>   | context: `File.java`
     Optionally append:  → Module: <Module> › <Subsection> -->

_None yet — add findings above._
```

### Counting and tallying rules

- Count statements by their leading EARS word. `After` (a Spring `AFTER_COMMIT` listener) counts as Event-Driven.
- Bulleted role-based access entries inside Cross-Cutting also count toward Event-Driven if they begin with `When`.
- If a module exhausts a category with zero statements, still list the category with `0`.
- The `[DISABLED]` count should briefly name what is disabled (e.g., "1 (Kafka pipeline disabled by default)").

### Naming the file

Pick the file name from the dominant domain in the extracted scope:
- Single domain → `<DomainName>-EARS-Specification.md` (e.g., `LoanProposalOTC-EARS-Specification.md`).
- Multiple unrelated domains in one run → `<DomainName1>-<DomainName2>-EARS-Specification.md`, or per-domain files if the scope is genuinely separate.

---

## Step 6 — Coverage Verification Pass (Subagent)

Step 5 produces a *draft* spec. Before it is considered final, independently prove that **every rule-site maps to a statement** — this is what makes the single pass gap-free *by construction*, so that running `/ears-gap-fix` on the result afterwards would find zero missing rules.

Do not rely solely on the main agent's own ledger here — re-derive coverage with fresh eyes.

**Mechanism.** For each large file in the call chain (any `> ~500` LOC source already read in Step 2 / Procedure A — validators, large services, DAOs, controllers), spawn **one subagent per large file** (Agent tool, `subagent_type: Explore`). Give each subagent:
- the source file path,
- the finished draft EARS file path,
- the rule-site grep command from Step A-2.1.

The subagent's sole job: rebuild the **rule-site-map** from grep, read the file in full under the Step A-2.1 protocol, and for each rule-site decide whether the EARS file already expresses it. Matching is **semantic**, anchored on the signals this skill guarantees, in priority order:
1. **Verbatim i18n message (Rule 5)** — search the EARS text for the exact quoted string; a match is near-conclusive.
2. **Exact reference entity (Rule 4) + condition direction + response verb** — "loan product details" ≠ "loan product policy"; exceeds / below / missing / duplicate; reject / set status / require role.
3. **Behavioural paraphrase** — for rules with no message, a statement whose trigger and response mean the same thing.

**Return contract.** The subagent returns **only**: a list of **UNCOVERED** rule-sites (`file:line` · condition · verbatim message · reference entity) plus its ledger line (`<sites> rule-sites · <accounted> accounted · <uncovered> uncovered`). The subagent **must not edit** the EARS file — all editing stays with the main agent.

**Main-agent loop.** For every uncovered rule-site reported, write the missing statement into the correct module (Rule 7 placement; quote any i18n message verbatim; no IDs/bullets/code refs per Rule 2). Then re-verify the changed files until every subagent returns `uncovered == 0`.

**Discipline.** One large file per subagent (protects main context). A subagent that returns `unread > 0` is sent back to finish — "beyond the read window" is never a valid stop while lines remain. This pass checks rule-site *presence*, not a full semantic re-inventory, so it is far lighter than a separate `/ears-gap-fix` re-walk while giving the same 0%-gap guarantee.

---

## Step 6.5 — Auto-Resolve Open Questions (Fresh Subagents, Breadcrumb-Only)

Step 5 may have produced `[NEEDS REVIEW]` Open Questions. By the time you reach this step you have *already* paid the expensive cost: the Step 3a.0 gates were run, the cited files were read, and the two-line breadcrumb footer (`*Where agent looked:*` / `*Hint for reviewer:*`) was written for each item. **Resolution is therefore cheap — it is just *executing* those breadcrumbs, not a fresh codebase trace.** This step chases every breadcrumb with a clean-context subagent and folds whatever resolves back into the spec *before* it is finalised, so the common auto-resolvable case never reaches the user as an open question. Genuinely unresolvable items stay `[NEEDS REVIEW]` for `/resolve-open-questions`, `/ears-gap-fix`, or a human to pick up later.

**Skip-if-empty.** If Step 5 produced **zero** `[NEEDS REVIEW]` items, this step is a no-op — do not spawn anything. Go straight to Step 7.

This is a **resolve-before-finalise** design: resolved findings flow into the spec as **normal finalised EARS statements** (no `[NEEDS REVIEW]→[RESOLVED]` rewrite, no `*Answer:*`/`*Source:*` lines, no cross-invocation citation tags). The only marker a resolved statement carries is a trailing ` [Auto-resolved]` so a reviewer knows its value was *derived via a breadcrumb chase* rather than read directly from the call chain, and should be spot-checked.

### Mechanism

1. **Collect candidates from context — do NOT re-read the EARS file.** You already hold every drafted Open Question in working memory: the question text, the `*Where agent looked:*` file:line citations, and the `*Hint for reviewer:*` backticked command(s). Build the candidate list from that working memory. Re-parsing the just-written file is wasted cost.

2. **Spawn read-only investigator subagents in parallel** (Agent tool, `subagent_type: Explore`), mirroring the Step 6 one-unit-per-subagent pattern — here, a small batch of questions per subagent. Each subagent prompt embeds, inline, the full question text plus its two breadcrumb lines. The subagent's **entire job** is, per question:
   - run each backticked `*Hint for reviewer:*` command **verbatim** (do not modify flags, do not add or drop paths);
   - `Read` the exact file:line spots named in `*Where agent looked:*` and any "likely answer in" file named in the hint;
   - stop the moment a definitive answer appears.
   The subagent **must not** re-trace the call chain, run broader greps, read sibling files that weren't named, or edit any file. Breadcrumbs are intentionally narrow; if they don't lead anywhere, the correct outcome is "still open", not a wider hunt.

3. **Subagent return contract (read-only).** For each question the subagent returns exactly one of:
   - `RESOLVED` — a definitive answer plus `Source: <file>:<line(-range)>` for every spot actually read to derive it. A definitive answer is one of: a concrete value · a finite set/list (every member listed) · a finite range · a format pattern · a categorical fact (e.g. "yes, also invoked from `EveryNightScheduledServiceImpl:47`"). An answer that requires guessing or interpolating between ambiguous matches is **not** definitive.
   - `STILL OPEN` — one-line reason (cited file absent / command returned nothing / matches ambiguous).
   The subagent never edits the spec; all writing stays with you (single writer — no merge conflicts, exactly like Step 6).

4. **Apply results (main agent is the sole writer).**
   - **RESOLVED** → write the value into the affected EARS statement(s) directly: strip vague placeholders ("the configured X", "(placeholder {0})") and substitute the concrete value(s). **Quote verbatim** any string literal, i18n message, enum value, or constant. When the answer is a set, **list every member** — never "and others". Name the exact reference entity (Rule 4). Append ` [Auto-resolved]` to each statement whose content the answer changed. If the resolution surfaces a brand-new rule no statement covers, add it as a normal paragraph in the correct module (Rule 7 placement, Rule 2 prose). Absorb any newly revealed enum values, state transitions, or numeric thresholds into the `## Domain Concepts and States` tables (Rule 12). **Remove the resolved item from `## Open Questions`** — in resolve-before-finalise there is no lingering open entry for it.
   - **STILL OPEN** → leave the item in `## Open Questions` as `[NEEDS REVIEW]` with **both** breadcrumb footers byte-for-byte intact (Rule 8). Do not weaken the footers — they are the trail the next pass needs.

5. **Guards (ported from the resolution discipline).**
   - **Contradiction guard.** If a resolution would contradict an existing EARS statement, do **not** apply it. Leave the question `[NEEDS REVIEW]` and append exactly one sentence to its `*Where agent looked:*` line: `Investigation contradicted existing statement at <module/subsection>; resolution withheld for human review.`
   - **Unsafe-command guard.** Never run a hint command that references paths outside the repo or uses destructive flags (`-delete`, `-exec rm`, `--force`). Skip just that command, fall back to the cited file reads; if nothing else yields an answer, leave the item open.

6. **Update the Extraction Summary.** Recompute the EARS-pattern counts (the totals already get recomputed at finalisation) and the residual `[NEEDS REVIEW]` count (now only the unresolved set), and add the resolved-in-pass tally (see the new Summary row).

### Cost discipline (why this is cheap)

- **Breadcrumbs travel in the subagent prompt → no full-file re-read.** This is the single biggest saving over a standalone resolution pass, which must re-parse the whole EARS file to find the questions.
- **Targeted reads only.** Subagents touch the cited lines and run the cited commands — nothing else. Each subagent's context stays tiny.
- **Parallel, read-only investigators; one main-agent writer.** Wall-clock and per-agent context both stay small, and there are no concurrent writes to the file.
- **You never re-investigate.** You only *apply* answers handed back; the expensive trace was already done in Steps 2–5.
- **No write-then-rewrite.** Resolved findings are written once as finalised statements — not written as `[NEEDS REVIEW]` and then rewritten.

---

## Step 7 — Quality Checklist (Run Before Finalising Output)

Before finalising the file, verify every item. A failed check means re-trace the relevant source or re-format the output.

### Coverage Completeness (Ledger + Verification)
- [ ] Every source file > 500 LOC in the call chain has a grep-built structural index (method-map + rule-site-map) made **before** reading bodies (Step A-2.1).
- [ ] Every rule-site line is accounted for in the per-file ledger — each marked `EXTRACTED → EARS statement "<…>"` or `EXTRACTED → not a rule`; none left unread.
- [ ] The Step 6 subagent verification pass ran for every large call-chain file and every subagent returned `uncovered == 0` (and `unread == 0`).
- [ ] Extraction Summary shows `Rule-sites uncovered: 0` and carries one per-file ledger line per file > ~500 LOC.

### Open-Question Auto-Resolution (Step 6.5)
- [ ] If Step 5 produced any `[NEEDS REVIEW]` items, Step 6.5 ran (read-only subagents fed the breadcrumbs in-prompt; no full EARS re-read, no call-chain re-trace). If it produced none, Step 6.5 was correctly skipped.
- [ ] Every auto-resolved question was removed from `## Open Questions` and its answer folded into the spec; each statement whose content changed carries a trailing ` [Auto-resolved]` marker, with i18n/literals quoted verbatim and every member of a set listed (Rules 4, 5).
- [ ] Newly revealed enum values / state transitions / numeric thresholds were absorbed into `## Domain Concepts and States` tables (Rule 12).
- [ ] Every residual `[NEEDS REVIEW]` item still carries both breadcrumb footers byte-for-byte (Rule 8); any contradiction-withheld item has the one-sentence contradiction note appended to its `*Where agent looked:*` line.
- [ ] Extraction Summary records the in-pass auto-resolved count and a residual `[NEEDS REVIEW]` count reflecting only the unresolved set.

### Formatting Compliance (Rules 1–14)
- [ ] **Rule 1:** Every EARS statement uses `the <DomainName> system` — no instance of "the system" alone, no instance of the project name as subject.
- [ ] **Rule 2:** No statement is prefixed with an ID like `UB-AUD-1.` or `EV-CRE-2.`. No statement uses a bullet point or a number — every statement is a plain paragraph separated by blank lines.
- [ ] **Rule 3:** No two `if`-branches are merged into one paragraph. The Unwanted Behaviour count roughly matches the if-branch count of every traced validator.
- [ ] **Rule 4:** Every comparison statement names the exact entity record whose fields supply the reference value (loan product vs. loan product details vs. loan product policy, etc.).
- [ ] **Rule 5:** Every Unwanted Behaviour statement whose validator throws with a string literal includes that string verbatim in double quotes.
- [ ] **Rule 6:** Every functional area with field-level DTO validation has a dedicated `**Field-level validation — <RequestName>:**` subsection.
- [ ] **Rule 7:** Modules are lifecycle-derived. No fixed 6-module skeleton was forced. Cross-cutting modules (Validation Rules / Sub-Validators / Async / External) appear only if their content threshold is met. No empty placeholder modules exist.
- [ ] **Rule 8:** Every `[NEEDS REVIEW]` item in Open Questions has both mandatory footer lines: `*Where agent looked:*` and `*Hint for reviewer:*`, each citing concrete file paths.
- [ ] **Rule 9:** No `[NEEDS REVIEW]` was raised without first attempting the relevant Step 3a.0 gates (enum source / validator body / sub-validator impl / access-control DAO / queue entry point / ID generator).
- [ ] **Rule 10:** No Table of Contents was added.
- [ ] **Rule 11:** All top-level sections are present in order: Title, header preamble block, Document Conventions table, System Overview, Cross-Cutting Requirements, Module(s), Domain Entities and Properties, Domain Concepts and States, Business Rules Summary, Open Questions, Extraction Summary, Review by Developer (code), Review by Developer (business requirements). The two Review-by-Developer sections are emitted as empty placeholders with their format-instruction comment.
- [ ] **Rule 12:** Every enum, role hierarchy, and status taxonomy in Domain Concepts is a Markdown table (not a bullet list) with the full set of values from the enum source file. State transitions are a three-column table.
- [ ] **Rule 13:** Every entity table is a **complete mirror of its source class** — one row per declared field (audit/version/soft-delete fields included, fields no requirement references included), for in-scope and externally-owned entities alike; no partial "touched fields only" table. The Property column uses the **exact codebase field name** (camelCase, e.g. `proposalNumber`) — business-level types in the Type column, plain English in Meaning. No property whose Type is `Reference to <Entity>` / `List of <Entity>` appears without that entity having its own `###` catalog block (transitively, to closure); no grouped "externally-owned" prose block substitutes for individual property tables. No `Enum (<Name>)` Type appears without that enum's full value table in Domain Concepts and States. Each entity cataloged once (shared infrastructure entities included), never repeated. Run the reference-closure inventory: list every distinct entity named as `Reference to` / `List of` across all entity tables and confirm each has a `###` block — zero gaps allowed.
- [ ] **Rule 14:** Every `## Module:` heading and every content `###` subsection (functional areas, validation concerns, sub-validators, Async/External pipelines, Domain Entities entity blocks, Domain Concepts enum/state blocks) carries a `> **Source files:**` blockquote line listing the full project-relative paths of the files it was extracted from. Excluded sections (header preamble, Document Conventions, System Overview, all five Cross-Cutting subsections, Business Rules Summary, Open Questions, Extraction Summary, Review by Developer) do not carry it. No EARS statement text contains a file path or code reference — those live only in the source-file annotation and the Open Questions footers.

### Section Completeness
- [ ] Header preamble has all six lines: `> **Format:**`, `> **Source:** … base package`, `> **Source Controller(s):**`, `> **System name used in statements:**`, `> **Purpose:**`, `> **Note:**`. The `Source Controller(s)` line lists the full project-relative path of every controller named at invocation and matches the controllers in the Extraction Summary.
- [ ] Document Conventions table is present with all four markers (NEEDS REVIEW, UNRESOLVED, INFERRED, DISABLED).
- [ ] System Overview is a single rich paragraph (5–8 sentences) covering scope, lifecycle, channel comparison.
- [ ] Cross-Cutting Requirements contains exactly five subsections in this order: Audit and Record Lifecycle, Authentication and Authorisation, Request Handling, Operational Cross-Cuts, Error Response Format. No extra subsections per filter/aspect.
- [ ] Error Response Format includes the full condition→HTTP-status table as a Markdown table — one row per `@ExceptionHandler` method, with plain-English condition names (no exception class names).
- [ ] Domain Entities and Properties has a four-column `Property | Type | Meaning | Constraints` table for **every** entity in the traced call chain (incl. embedded JSON objects and child entities) **and the transitive closure of every entity referenced by a `Reference to …` / `List of …` Type** — each cataloged exactly once (shared infrastructure entities included, not skipped, not repeated). Each table is a **complete mirror of its source class**: one row per declared field, including audit/version/soft-delete fields and including fields no requirement references, for in-scope and externally-owned entities alike (audit/version lifecycle *semantics* referenced once from Cross-Cutting → Audit and Record Lifecycle, but the field rows still appear in every table). Every enum named as a property Type has its full value table in Domain Concepts and States. No grouped "externally-owned" prose block replaces individual property tables — every referenced entity has its own `###` sub-block regardless of module ownership. Property column uses exact codebase field names.
- [ ] Domain Concepts and States contains a table for **every** enum referenced or implied by any EARS statement, plus a state-transition table for the primary entity.
- [ ] Extraction Summary lists controller names and lib module names verbatim (not just counts). The breakdown by EARS pattern type sums to the total.
- [ ] Extraction Summary has the `**Extraction completed:**` line with today's runtime date in `<Day, DD Month YYYY>` format.

### Entry Point Coverage
- [ ] Step 1.5 ran (unless Auto-discover mode or the user restricted scope): lifecycle siblings were discovered and presented as an `AskUserQuestion` multi-select (checkbox) with the full-lifecycle set marked `(Recommended)`, and the processed scope matches the user-ticked set — recorded verbatim in the `Source Controller(s)` line and the Extraction Summary controller list.
- [ ] Every REST endpoint has at least one Event-Driven EARS statement.
- [ ] Every queue consumer has at least one Event-Driven statement.
- [ ] Every DLQ consumer's recovery logic is captured.
- [ ] Every `@Scheduled` method (active or disabled) is captured.
- [ ] Every manually triggered scheduler endpoint is captured.

### Validation and Error Coverage
- [ ] Every `if`/`else if` that throws or returns an error has a corresponding Unwanted Behaviour statement.
- [ ] Every field-level validation annotation in every DTO has a corresponding statement.
- [ ] Every custom `ConstraintValidator.isValid()` body is captured.
- [ ] Every `@ExceptionHandler` is captured.
- [ ] Every Resilience4j fallback and circuit-breaker open-state behaviour is captured.
- [ ] Optimistic locking conflict handling is captured.

### Lib Module Coverage
- [ ] Every lib module is classified (Step 0g table).
- [ ] Every business-logic lib module is fully extracted.
- [ ] Every lib validator's **all public methods** are read — not just `validate()`.
- [ ] Every **private helper method** called from any public validator method is read recursively.
- [ ] Every **injected sub-validator dependency** call (wherever it appears in the method body) is traced into its concrete implementation as a new Procedure A scope.
- [ ] For every validator file > 800 lines: `wc -l` was run, the file was read in chunks, the closing `}` of the outer class was reached, and a complete Public Methods List was produced before any extraction began.
- [ ] Every classed scanned across all packages of every business-logic lib module — not only `*Validator` / `*ValidatorImpl` patterns.
- [ ] Every `@Rule` class in every rule-book package is read in execution order. Hardcoded approval limits appear with exact numeric values.
- [ ] Every interface-only lib module's interfaces are catalogued; corresponding main-app implementations are traced.
- [ ] Every lib DAO implementation is read as a first-class DAO (Procedure C).
- [ ] Every `Collections.emptyList()` / stub / commented-out lib logic is captured as `[DISABLED]`.
- [ ] All enum types from shared DTO lib modules are catalogued in Domain Concepts and States.
- [ ] Every delegated rule-object / specification dispatched from a service (`*Rule`, `*Specification`, `isSatisfiedBy`/`test`) has each rule class opened and its predicate extracted (Step A-6); no `[NEEDS REVIEW]` stands in for a set of rule classes that exist in the repo.
- [ ] Every rejection whose message text comes from a called service rather than the validator body has that service impl and its backing mapping/seed data read (Step A-7).

### Cross-Cutting Coverage
- [ ] Every abstract base entity's shared fields are captured as Ubiquitous statements.
- [ ] Every `@Aspect` class's intercepted behaviour is represented.
- [ ] Every filter is covered.
- [ ] Every security access rule has a corresponding statement.
- [ ] Every Spring profile–gated behaviour is captured as Optional.
- [ ] The access-control library's database-driven rules are captured.

### Open Questions Audit (Rule 8 + Rule 9 enforcement)
- [ ] Every `[NEEDS REVIEW]` item names a *concrete* question — not "needs investigation."
- [ ] Every item has the `*Where agent looked:*` footer with at least one file path and line range.
- [ ] Every item has the `*Hint for reviewer:*` footer with at least one likely file path AND a grep/find/graphify command to run.
- [ ] No item is raised whose answer is in an enum source file that was not opened (Step 0l violation).
- [ ] No item is raised whose answer is in a validator method body that was not read (Step 2i violation).
- [ ] No item is raised whose answer is in an access-control DAO impl that was not opened (Procedure D violation).
- [ ] No item names a method/class/enum without having opened that file (Step 2i violation).

### Output Quality
- [ ] No EARS statement contains a class name, method name, annotation, HTTP verb, URL path, SQL fragment, table name, or any other code artefact. (File paths appear only in the per-heading `> **Source files:**` annotations (Rule 14) and the Open Questions footers (Rule 8) — never inside statement text.)
- [ ] Every EARS statement is self-contained.
- [ ] All ambiguities were either resolved interactively or marked `[NEEDS REVIEW]` with the Rule 8 footers populated.
- [ ] i18n message wording is used verbatim in double quotes (Rule 5).
- [ ] Domain Concepts and States lists every enum, every value, every state transition (Rule 12).
- [ ] Business Rules Summary lists every threshold, limit, and eligibility criterion as a numbered item (15+ items for a large module).
- [ ] Open Questions is a numbered list of every `[NEEDS REVIEW]` item left unresolved after Step 6.5, each with the two-line footer.

---

## Anti-Patterns to Avoid

| ❌ Wrong | ✅ Correct |
|----------|-----------|
| `- **UB-AUD-1.** The system shall record creation timestamps.` | `The Loan Proposal system shall automatically record the identity of the actor who created a record and the precise timestamp of creation whenever a new record is first persisted to the database.` |
| `When POST /api/loan-proposals is called, the system shall…` | `When an actor submits a new loan proposal for a branch via the OTC channel, the Loan Proposal system shall verify that the branch's business day is currently open before proceeding.` |
| `The LoanProposalServiceImpl.create() method validates…` | `When a new loan proposal is submitted, if the proposed loan amount exceeds the product policy maximum, the Loan Proposal system shall reject the submission.` |
| `The @NotBlank annotation ensures name is provided` | `If the member's full name is not provided, the Loan Proposal system shall reject the request.` |
| `The system shall call sendEmail()` | `The Loan Proposal system shall send a confirmation notification to the member.` |
| `While LOAN_STATUS = 'PENDING'` | `While a loan proposal is in Pending status, the Loan Proposal system shall permit modification by the originating branch.` |
| `Smart MF shall verify…` | `The Loan Proposal system shall verify…` (use the domain name, not the project name) |
| `the system shall reject the request` | `the Loan Proposal system shall reject the request` (always include the domain prefix) |
| `the BufferLoanProposalDao executes a native query` | `The Loan Proposal system shall filter draft proposals by branch, date range, and submission status.` |
| `the @Transactional annotation wraps the method` | `The Loan Proposal system shall atomically persist the proposal record and publish the submission event; if either step fails, both shall be rolled back.` |
| Collapsing 6 validator if-branches into one statement | Six separate paragraph statements, one per branch, each naming the precise condition and the precise error message. |
| `checkLoanInstalmentDuration(proposal, loanProductDetailsDto, rateDto)` written as "values in the **loan product**" | "values in the **loan product details** record" — the parameter is `loanProductDetailsDto`, not `loanProductDto`. |
| `Where queue-kafka profile is active` | `Where the Kafka-based loan update queue is configured as active` |
| Compressing field-level validation into one sentence inside the happy-path flow | Dedicated `**Field-level validation — Loan Proposal Create request:**` block, one paragraph per field rule. |
| Adding a Table of Contents at the top of the file | Skip it. Readers navigate by Markdown heading (Rule 10). |
| Cross-Cutting Requirements with 11 subsections (one per filter/aspect: `### CAPTCHA`, `### Business Day Validation`, `### Distributed Scheduler Lock`, …) | Exactly five subsections, in this order: Audit and Record Lifecycle / Authentication and Authorisation / Request Handling / Operational Cross-Cuts / Error Response Format. The aspects/filters become statements *inside* the appropriate subsection — not subsection headings of their own. |
| Listing only 6 loan-proposal status values (the ones seen in controller code) | List every value from the enum source file. If `LoanProposalStatus.java` has 22 values, all 22 appear in the table (Rule 12 + Step 0l). |
| Writing "DM = Deputy Managing Director" because that was the agent's guess | Open `LoanApprover.java` / `EmployeeDesignation.java`. The enum says "Divisional Manager" — use that. Guessing display names is a Step 0l violation. |
| Validation rules dumped as a `**Business Rule Validations:**` subsection inside the Create section | Validation rules belong in `Module: <Domain> Validation Rules` per Rule 7. The Create section says "the validation chain runs" and references the dedicated module. |
| Error Response Format as a bullet list ("- 400 Bad Request: …") | Markdown table with `\| Error condition \| HTTP status \|` columns, one row per `@ExceptionHandler` (Rule 12). |
| Domain Concepts as bullet lists ("- **PENDING** — proposal created") | Markdown tables with at minimum two columns (Rule 12). |
| Listing enum states but omitting the entity's scalar properties (amount, dates, identifiers, references) | Every entity gets a `Property \| Type \| Meaning \| Constraints` table in the Domain Entities and Properties section (Rule 13). |
| Listing only the fields the traced code touched (partial entity table), or abbreviating an externally-owned entity to a few fields | Open the source class and list **every** declared field — a complete data-model mirror, audit/version and unused fields included, in-scope and externally-owned alike (Rule 13). |
| Listing a property as `Reference to Member` with no Member block, or `Enum (LoanProposalStatus)` with no value table | Every referenced entity has its own catalog block here (transitively, to closure); every named enum has its full value table in Domain Concepts and States; each entity cataloged once (Rule 13). |
| Capitalised or paraphrased property name in entity table (e.g. `Proposed loan amount`, `Member`) | Exact codebase camelCase field name as declared in the source (e.g. `proposedLoanAmount`, `member`); the `Meaning` column carries the plain-English description (Rule 13). |
| Grouping multiple externally-owned entities into a single `### Externally-owned reference entities` prose block | Each referenced entity — regardless of which module/service owns it — gets its own dedicated `###` sub-block with a complete four-column property table; module ownership belongs only in the entity description sentence (Rule 13). |
| `1. **[NEEDS REVIEW]** What is the format of the loan proposal number?` (no footer) | Item must end with `*Where agent looked:* <file:line> — <what was read>` and `*Hint for reviewer:* <probable file> — <grep command>` (Rule 8). |
| Naming `checkLoanInterestRate` in an open question without reading the method body | Open the file, read the method, extract the rules. Method-named-but-not-read is the #1 source of unnecessary `[NEEDS REVIEW]` items (Step 2i). |
| `[NEEDS REVIEW]` for enum codes like `BufferLoanPreValidationMessage.L_216` | Open the enum source file. Every enum's display message is right there — no `[NEEDS REVIEW]` needed (Step 0l + Rule 9). |
| `[NEEDS REVIEW]` for "what access-control roles are required" | Open `lib/access-control/.../AccessControlDaoImpl.java` and the relevant Flyway migration seed file (Procedure D + Rule 9). |
| `[NEEDS REVIEW]` for "the four CLOC rules behind `ClocLoanValidatorServiceImpl`" | Open each `Cloc*Rule.isSatisfiedBy` and write one statement per rejection branch with its verbatim message (Step A-6 + Rule 9 gate 7). |
| `[NEEDS REVIEW]` for a rejection message returned by a mapping service (e.g. `CoExistingLoanProductMappingService`) | Open the service impl and its mapping/seed data; quote the message and the disallowed-combination logic (Step A-7 + Rule 9 gate 8). |
| Silently pulling in `LoanApproveOtcRestController` without telling the user — **or** silently omitting it and shipping a proposal spec with no approval/rejection lifecycle | Discover lifecycle siblings, present them grouped by role, recommend the full-lifecycle set, and extract exactly the set the user confirms (Step 1.5, Rule 7). |
| Forcing all 6 cross-cutting modules even when one would be empty | Omit any cross-cutting module that doesn't meet its content threshold. No empty placeholders (Rule 7). |

---

## Important Reminders

1. **No requirement gaps are acceptable.** If a file in the call chain exists but seems unrelated to business logic, note it briefly and explain why it produced no requirements.
2. **Overwrite** the output file on every run — do not append to a stale file.
3. **Ask all ambiguity questions for an entry point before writing that entry point's section** — do not write partial sections then ask.
4. **The domain-scoped system name is mandatory.** Derive it from the controller cluster, not the project. Use the same name throughout a module.
5. When in doubt whether something is a business rule, **include it**. Omission is always worse than inclusion for a source-of-truth document.
6. **Shared libraries are not black boxes.** Classify first (Step 0g), then apply the matching procedure. No lib module that contains business logic may be skipped.
7. **JDBC DAOs and RowMappers are equal in importance to JPA repositories.** A missed DAO method is a missed requirement.
8. **Queue consumers are entry points, not implementation details.**
9. **Disabled features must not be omitted.** Capture as Optional or `[DISABLED]`.
10. **i18n messages define exact user-facing wording — quote verbatim in double quotes (Rule 5).**
11. **Each conditional branch in a lib validator is a separate paragraph statement.** A validator with 6 `if` blocks produces 6 paragraphs — not one summary.
12. **Hardcoded approval limits are business rules, not implementation details.** Numbers must appear verbatim.
13. **A lib validator class is not done when you finish reading `validate()`.** Check every public method.
14. **A private method called from `validate()` is just as mandatory as an inline `if` block.** Follow every helper to its leaf.
15. **Injected validators are first-class extraction targets — wherever the call appears.** Scan top-to-bottom for `this.field.someMethod()` patterns. Every one opens a new Procedure A scope.
16. **Large validator files must be read in multiple chunks — never assume a single read covers the whole class.** Always `wc -l` first. Read until the closing `}` of the outer class is reached. Build a complete Public Methods List from all chunks before extracting.
17. **Top-level section skeleton is fixed (Rule 11); Module sections are NOT fixed.** Modules are lifecycle-derived per Rule 7. Cross-cutting modules appear only when their content threshold is met. Do not invent unrelated top-level sections.
18. **The Extraction Summary lists controller and lib module names**, not just counts — this gives the reader confidence the trace was complete.
19. **`[NEEDS REVIEW]` is the last resort, not a shortcut.** Step 3a.0 gates are mandatory: enum sources read (Step 0l), validator bodies read (Step 2i), sub-validator impls read (Procedure A), access-control DAOs read (Procedure D), queue/REST entry points grep-confirmed, ID generators read (Step 0m). Every `[NEEDS REVIEW]` item must carry the Rule 8 two-line footer.
20. **Discover lifecycle siblings, then confirm scope with the user (Step 1.5).** When the user names one controller, surface its lifecycle siblings (approval, rejection, disbursement, good-loan) as an `AskUserQuestion` multi-select (checkbox), with the full-lifecycle set marked `(Recommended)` and listed first — but never silently expand beyond what the user ticks, and never silently hide a discovered sibling. The user owns the scope decision; Step 1.5 only makes it visible.
21. **No Table of Contents at the top of the file** (Rule 10). The output starts with title → header preamble → Document Conventions → System Overview.
22. **Domain Concepts uses Markdown tables, never bullet lists** (Rule 12). Every enum value found in the enum source file appears in the table — not just the values the agent happened to use in EARS statements.
23. **Enum display names come from the enum source file** — never from the agent's guess. Reading `LoanApprover.java` is mandatory before writing "DM means …" anywhere in the spec.
24. **Domain Entities and Properties catalogs every entity with all its properties (Rule 13).** Each entity table is a **complete mirror of its source class**: one row per declared field, including audit/version/soft-delete fields and including fields no requirement references, for in-scope and externally-owned entities alike (a partial "touched fields only" table is forbidden). Reading an entity in Step 2c is not done until every declared field is written there AND every entity/enum it references is itself cataloged: each `Reference to …` / `List of …` entity gets its own dedicated `###` sub-block here (never merged into a grouped "externally-owned" prose block), transitively to closure; each `Enum (<Name>)` Type gets its full value table in Domain Concepts and States. Catalog each entity once (shared infrastructure entities — user/office/branch/organization — included, never skipped, never repeated); child entities and embedded JSON objects get their own sub-blocks; audit/version field rows appear in every table while their lifecycle semantics are referenced once from Cross-Cutting → Audit and Record Lifecycle. **Property column uses the exact codebase camelCase field name** from the source (`proposalNumber`, `proposedLoanAmount`) — never a capitalised or paraphrased business name. Run the reference-closure inventory before Step 7: list every entity named as `Reference to` / `List of` across all entity tables and confirm each has a `###` block — zero gaps.