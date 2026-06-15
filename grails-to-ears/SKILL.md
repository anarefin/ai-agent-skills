---
name: grails-to-ears
description: Reverse engineer a Grails 2.5.x project into a 100% complete EARS (Easy Approach to Requirements Syntax) specification file. Use this skill when the user wants to extract business requirements from an existing Grails codebase — including single controllers, single action services, multiple controllers/action services, or an entire plugin directory — and produce a standalone, code-free .md EARS file that can serve as a source of truth for regenerating the system in any architecture (DDD, CQRS, Event Sourcing, etc.). The skill also auto-resolves its own Open Questions on the first pass (Step 6.5): a fresh read-only subagent chases each question's breadcrumb footer and folds confident answers back into the spec as finalised statements, leaving only genuinely unresolvable items as [NEEDS REVIEW] — so a separate /resolve-open-questions run is usually unnecessary. Each module and content subsection is annotated with a `> **Source files:**` line listing the full project-relative paths it was extracted from, so a developer can cross-check the spec against the codebase (the EARS statements themselves stay code-free).
---

# Grails → EARS Reverse Engineering Skill

You are performing **lossless business requirement extraction** from a Grails 2.5.x codebase (Groovy 2.4 / JDK 1.8). Your output is a standalone EARS specification `.md` file. Readers of this file have **zero knowledge** of the source project. Every business rule, validation, workflow, access-control constraint, and exception behaviour must be expressed as a self-contained EARS statement — no code references, no class names, no method names, no annotations, no framework terminology in the statement text. The **sole** exceptions, both outside statement prose, are the per-heading `> **Source files:**` annotation that lets a developer cross-check each section against the codebase (Rule 14) and the Open Questions breadcrumb footers (Rule 8).

Completeness is **gap-free by construction**, not by luck: every large file is read under a structural-index + rule-site ledger (Step A-2.1) that maps each `if`/`case`/`throw`/`render`-rejection to the statement it produced, and a subagent verification pass (Step 6) independently confirms `0` uncovered rule-sites before the spec is final — so a follow-up gap-fix run would find nothing missing.

**This project's shape.** A monolithic Grails application (`mainapp/`) plus **15 local plugins** under `plugins/` (`accounting`, `admin`, `applicationCommon`, `mf`, `hrm`, `finance`, `Procurement`, `Inventory`, `fixedAsset`, `budget`, `etender`, `ProposalTracking`, `complaintManagement`, `bitsjasperreports`, `bitsSpringSession`). Two base packages coexist: `com.docu.*` (legacy/applicationCommon) and `com.bits.gerp.*` (newer modules). Business logic lives mostly in **action services**, not controllers — see the two action patterns below.

**Output file location:** `docs/ears/<DomainName>-EARS-Specification.md` (project-relative). Overwrite any existing file with the same name.

---

## The Two Action Patterns (read this before anything else)

Grails controllers in this project are thin. The real business logic lives in **action services / action classes**, in one of two patterns. You must recognise both, because tracing the controller alone yields almost nothing.

**Legacy `IAction` pattern** (used by `applicationCommon` and older modules):
- Location: `plugins/<module>/src/groovy/com/docu/.../*Action.groovy`.
- A Spring `@Component("xxxAction")` class implementing the `IAction` interface with `preCondition(params)`, `execute(params, object)`, `postCondition(object)`. Each returns a `Map` carrying a `Message` (SUCCESS / ERROR) built by `UserMessageBuilder.createMessage(...)`.
- Controllers call these directly: `def object = xxxAction.preCondition(params); if (msg.type == Message.SUCCESS) { xxxAction.execute(null, object) }; render msg as JSON`.
- Example: `plugins/finance/src/groovy/com/docu/esp/CreateEspOrganizationAction.groovy`, `plugins/applicationCommon/src/groovy/com/docu/rabbitmq/action/SendRabbitMessageAction.groovy`.

**Current `ActionInterface` + `BaseService` pattern** (used by `admin`, `accounting`, and newer plugins):
- Location: `plugins/<module>/grails-app/services/com/bits/gerp/<module>/action/.../*ActionService.groovy`.
- Extends `BaseService` and implements `ActionInterface` (`plugins/admin/src/groovy/com/bits/gerp/common/ActionInterface.groovy`): `executePreCondition(Map)`, `execute(Map)`, `executePostCondition(Map)`, `buildSuccessResult(Map)`, `buildFailureResult(Map)` — all pass and mutate a single result `Map`.
- Controllers extend `BaseController` (`plugins/admin/grails-app/controllers/com/bits/gerp/admin/BaseController.groovy`) and call `renderOutput(actionService, params)`. Its `getServiceResponse(...)` runs `executePreCondition → execute → executePostCondition → buildSuccessResult`, short-circuiting to `buildFailureResult` whenever the result Map's `isError` is `true`.
- `BaseService` (`plugins/admin/grails-app/services/com/bits/gerp/admin/BaseService.groovy`) supplies raw-SQL helpers `executeSelectSql(query, params)` (returns `List<GroovyRowResult>`), `executeInsertSql`, `executeUpdateSql`, and `getBusinessDay(officeId)` (delegates to `accountingPluginConnector`).
- Example: `plugins/accounting/grails-app/services/com/bits/gerp/accounting/action/accpaymentsubtype/ListAccPaymentSubTypeActionService.groovy`.

Whenever this skill says "action service" or "action class" below, it means **either** pattern. Whenever it says "the action lifecycle", it means preCondition/execute/postCondition (legacy) or executePreCondition/execute/executePostCondition/build* (current). An `isError == true` short-circuit or a `Message.ERROR` return is the Grails equivalent of a thrown exception — each one is an Unwanted Behaviour EARS statement.

---

## Output Formatting Rules (Non-Negotiable)

These rules govern the *form* of every EARS statement and every section. They override any contrary instinct from reading other EARS examples.

### Rule 1 — Domain-scoped system name

The subject of every EARS statement is `the <DomainName> system`, where `<DomainName>` is the business domain of the module being extracted — not the project name.

- ✅ `the Subsidiary Ledger system`
- ✅ `the Member Onboarding system`
- ✅ `the Voucher Posting system`
- ❌ `the system` (too generic — fails the "standalone reader" test)
- ❌ `SBICloud BD` / `BRAC ERP` / `the GERP system` (project name — not domain-scoped)
- ❌ `the application` / `the service` / `the plugin`

Derive the domain name from the controller / action-service cluster being extracted (e.g., `AccSubsidiaryLedgerController` + `CreateAccSubsidiaryLedgerActionService`, `ListAccSubsidiaryLedgerActionService` → "Subsidiary Ledger"). If multiple distinct domains are extracted in one run, each module section may use its own domain-scoped name. Use the same name consistently within a module.

State the chosen name explicitly in the front-matter block at the top of the file: `> **System name used in statements:** the <DomainName> system`.

### Rule 2 — Plain prose paragraphs, no IDs, no bullets

Every EARS statement is a complete standalone sentence, written as a paragraph separated from neighbours by a blank line. Do **not** prefix statements with IDs (`UB-AUD-1.`, `EV-CRE-2.`), do not use bullet points, do not use numbered lists for statements.

- ✅ `When an actor submits a new subsidiary ledger for a branch, the Subsidiary Ledger system shall verify that the branch's business day is currently open before proceeding with any processing.`
- ❌ `- **UB-AUD-1.** The system shall…`
- ❌ `1. The system shall…`

Numbered lists are reserved for the **Business Rules Summary** and **Open Questions** sections only.

### Rule 3 — Each rejection branch is its own paragraph

A validator / action with N rejection branches produces N separate paragraphs. Do not collapse, do not summarise, do not group. A "rejection branch" is any `if`/`else if`/`case` that returns a `Message.ERROR`, sets `isError = true`, returns a constraint `'error.key'`, or otherwise stops the happy path. If two consecutive paragraphs differ only in the field name being validated, both stay — they are distinct requirements.

### Rule 4 — Name the exact entity that supplies the reference value

When an EARS statement compares the request against a domain record, the entity named in the statement must match the actual source field. A check against `loanProductDetails.durationInMonths` says "loan product **details**", not "loan product". A check against `accProjectSetup.maximumAmount` says "project **setup**". Related domain classes (e.g. `ChartOfAccounts` vs `AccSubsidiaryLedger` vs `AccProjectCoaSubledgerMapping`) are distinct records with distinct fields; conflating them in requirement text makes the spec ambiguous. In Grails, the source is a GORM domain property (`obj.someField`), a `GroovyRowResult` column from a raw-SQL row, or a `Command`/cache value — name the record it came from.

### Rule 5 — Quote i18n messages verbatim where they exist

User-facing error text in this project comes from `'error.key'` strings resolved against `messages.properties` / `messages_bn.properties` (in `mainapp/grails-app/i18n/` and each plugin's `grails-app/i18n/`), or from string literals passed to `UserMessageBuilder.createMessage(...)` / `getUserMessage(key)`. Resolve the key and include the exact text in the Unwanted Behaviour statement in double quotes:

> `If the subsidiary ledger code already exists for the chart of account, the Subsidiary Ledger system shall reject the request with the message "Code already exists."`

Do not paraphrase messages that exist verbatim. **Bengali is present** (`messages_bn.properties`) — if only a Bengali message exists, include the English back-translation alongside it; if both exist, the English text is authoritative and the Bengali presence is noted.

### Rule 6 — Field-level validation goes in a dedicated subsection

After the main happy-path and state-guard statements of a functional area, add a dedicated `**Field-level validation — <RequestName>:**` block. Each field-level rule is a separate `If <field>… the <DomainName> system shall reject the request.` paragraph. These come from the GORM domain `static constraints { }` block and any `Command` object constraints. Do not mix field-level validation into the main flow.

### Rule 7 — Lifecycle-driven module derivation (no fixed skeleton, no empty placeholders)

Modules are derived from the controllers / action services actually being processed and the content thresholds they produce. **Do not** force a fixed 6-module skeleton. Sibling lifecycle entry points are **discovered and confirmed with the user** in Step 1.5; the resulting user-confirmed set is the scope that drives module derivation — never silently expanded beyond it, never silently narrowed to ignore a discovered sibling.

**Primary module(s):** one per controller / action-service cluster, named after its domain and lifecycle role:
- CRUD-style cluster (create / update / delete / get / list action services) → `Module: <Domain> Management`.
- Approval/Workflow-style cluster (approve / reject / forward / backward) → `Module: <Domain> Approval`.
- Posting/Disbursement-style cluster → `Module: <Domain> Posting` (or `— Disbursement`).
- Async/Rabbit/Mercure consumer → `Module: <Domain> Notifications` or `— Messaging`.
- Quartz scheduled job → `Module: <Domain> Scheduled Processing`.
- Monitoring/reporting endpoint cluster → `Module: <Domain> Monitoring`.

**Additional cross-cutting modules** — include each ONLY when the content threshold is met in the entry points being processed:

| Module | Inclusion threshold |
|--------|---------------------|
| `Module: <Domain> Validation Rules` | The traced action services invoke a business-rule validator/check method (or a `validator:` closure cluster) with more than 5 distinct rejection branches. |
| `Module: Sub-Validators` | Two or more specialised sub-validator action services / validation services (e.g. business-day, duplicate-code, association-check) are invoked. If only one, fold it into Validation Rules. |
| `Module: Async and Scheduled Processing` | The entry points fire any asynchronous side effect (Rabbit publish, Mercure SSE, cache refresh) or a Quartz job acts on the same domain. |
| `Module: Cross-Plugin and External Integrations` | The entry points make any call across a plugin boundary via a `PluginConnector`, or any outbound call to an external system / second datasource (ERP, report DB). |

**Shared-validator deduplication:** if the user names multiple controllers/action services in one run and they all invoke the same business-rule validator or share the same core service, produce a single consolidated `Module: <Domain> Validation Rules`. Do not repeat the rules per entry point.

**No empty placeholder modules.** If a cross-cutting module has zero content, omit it entirely — do not write "No <X> behaviour was identified."

### Rule 8 — Open Questions must carry codebase references (two-line footer)

Every `[NEEDS REVIEW]` item in the Open Questions section ends with two italicised footer lines that show the reviewer exactly where the agent looked and where the answer most likely lives. Format:

```
1. **[NEEDS REVIEW]** <The precise question, phrased so a domain expert can answer it.>
   *Where agent looked:* `<relative/file/path.groovy>:<line>` — <what was examined>. `<another/file.groovy>:<line>` — <what was examined>.
   *Hint for reviewer:* Likely answer in `<probable/file.groovy>` (<one-sentence reasoning>). Try `<grep or graphify command>` to locate.
```

Both lines are mandatory. A question without these footers is rejected by Step 7 and must be either resolved or re-investigated until the footers can be filled.

### Rule 9 — Mandatory pre-conditions before any `[NEEDS REVIEW]` is allowed

`[NEEDS REVIEW]` is not a shortcut. It is the last resort. Before marking any item `[NEEDS REVIEW]`, all of the following must have been attempted and recorded:

1. **Enum source file lookup.** If the question concerns an enum value, code, or named constant (e.g., `PaymentType.MOBILE_BANKING`, `TransactionStatusType`, `ApplicationUserType`): the enum source file under `plugins/<m>/grails-app/domain/com/bits/gerp/<m>/enums/<EnumName>.groovy` (or `.java`, or a legacy `com/docu/commons/<Enum>.groovy`) must have been read. Every value's `displayName` / `code` must have been listed in Domain Concepts and States.
2. **Action / validator body lookup.** If the question concerns a method whose name is known (e.g., `checkAssociationOfSubledgerList`, `validateAndGetSeqFormat`): the action-service or service file must have been opened with `Read` and the method body extracted. Naming a method without reading it is not enough.
3. **Sub-action / sub-service dependency lookup.** If the question concerns a referenced sub-action, sub-service, or `*CacheService`: the concrete file must have been opened and Procedure A applied.
4. **Access-control lookup.** If the question concerns authentication, business-day gating, roles, permissions, or endpoint authorisation: `mainapp/grails-app/conf/sbicloud/SecurityFilters.groovy`, the relevant annotation in `plugins/applicationCommon/src/java/com/docu/commons/annotation/`, and the database-driven FeatureAction seed data (in `dbScripts/`) must have been read. Procedure D applies.
5. **Entry-point lookup.** If the question concerns whether a method is a Quartz job, a Rabbit consumer action, a controller action, or a plain service method: grep for `static triggers`, `IAction`, `ActionInterface`, `def <name> = {`/`def <name>(`, or a `UrlMappings` route on that name. State the result.
6. **ID/sequence-generator lookup.** If the question concerns the format of a generated identifier (voucher number, code, sequence): `DocumentSequenceIdService.groovy` and the relevant `*CodeGenerationService.groovy` must have been opened.
7. **Delegated rule-object / closure lookup.** If the question concerns a dispatcher over a collection/chain of rule objects or a set of `validator:` closures, every dispatched rule / closure must have been opened and read (Step A-6).
8. **Dynamic-message / mapping lookup.** If the question concerns a rejection whose message text is returned by a called service or resolved from a config/lookup table rather than written in the action body: the service's concrete implementation and its backing data (BootStrap seed, `dbScripts` INSERTs, or cache) must have been opened (Step A-7).

Only after all applicable lookups in 1–8 above have been performed AND have failed to yield a definitive answer may the item be marked `[NEEDS REVIEW]`. The two-line footer (Rule 8) then records *which files were checked* and *which file the reviewer should consult next*.

### Rule 10 — No Table of Contents

Do not generate a Table of Contents. The output file starts with the title, then the header preamble block, then the Document Conventions table. Readers navigate by Markdown heading.

### Rule 11 — Mandatory front-matter and skeleton sections

Every output file must contain these top-level sections in this exact order. None may be omitted:

1. Title (`# <Domain> Business Requirements Specification (EARS)`)
2. Header preamble block (the `>` quoted lines with Format / Source / Source Entry Point(s) / System name / Purpose / Note)
3. Document Conventions table
4. System Overview (single rich paragraph)
5. Cross-Cutting Requirements (with exactly five subsections: Audit and Record Lifecycle / Authentication and Authorisation / Request Handling / Operational Cross-Cuts / Error Response Format)
6. One or more `Module:` sections (per Rule 7)
7. Domain Entities and Properties (per Rule 13)
8. Domain Concepts and States
9. Business Rules Summary
10. Open Questions (with Rule 8 footers)
11. Extraction Summary
12. Review by Developer (code) — emitted as an empty placeholder for the developer to fill
13. Review by Developer (business requirements) — emitted as an empty placeholder

If a top-level section would have no content (e.g., no validation rules were extracted), the section is still present with a single-paragraph explanation of why. The two `Review by Developer` sections are always emitted as empty placeholders (with their format-instruction comment) even on a fresh extraction — the developer fills them in later.

### Rule 12 — Domain Concepts uses Markdown tables, not bullet lists

Every enum, role hierarchy, sub-type list, and status taxonomy is rendered as a Markdown table with at minimum two columns (e.g., `| State Name | Business Meaning |`). Bullet lists are not acceptable for these concepts. State transition tables use three columns (`| From State | To State | Triggered by |`).

When listing an enum, list **every value** found in the enum source file, in business-logical order, with its `displayName` (and `code` where it differs). If the codebase has 22 status values, all 22 appear in the table. Do not list only the values referenced in the EARS statements — that defeats the standalone-reader test.

### Rule 13 — Domain Entities and Properties catalog (every entity, every property)

The output file carries a dedicated `## Domain Entities and Properties` top-level section, positioned immediately **before** `## Domain Concepts and States`. It catalogs **every** domain class (GORM entity) reached by the traced call chain (Step 2c) so a reader regenerating the system knows the full data model — not just the enum states.

- One `###` sub-block per entity: a one-line plain-language description of what the entity represents, followed by a four-column Markdown table:

  ```
  | Property | Type | Meaning | Constraints |
  ```

- List **every field declared in the source class** — the table is a complete mirror of the domain class's field list, **not** just the fields the traced call chain happened to touch. List a field even when no traced behaviour, validation, or requirement references it: this section reflects the full data model, not the subset of fields exercised by the code path you followed. Embedded structured objects and child entities (`hasMany`/`belongsTo`/`hasOne`) each get their **own** `###` sub-block (or a clearly-labelled nested table) — do not flatten or omit them.
- **Complete field set — full expansion (every entity, in-scope and externally-owned alike).** Each entity's `###` sub-block must contain **one row per field declared in its source class**. This applies uniformly: the primary in-scope entities and every externally-owned / cross-module referenced entity are all expanded the same way. A table that lists only a subset of the source class's fields (e.g. only the fields the traced code read or wrote) is **incomplete and rejected** — open the domain class file and enumerate **all** its declared fields. Externally-owned entities are not abbreviated; their module ownership is noted only in the description sentence, never used as a reason to list fewer fields.
- **Type** is a business-level type, never a Groovy/Java type: `Amount`, `Money`, `Percentage`, `Date`, `Timestamp`, `Identifier`, `Text`, `Boolean`, `Enum (<EnumName>)`, `Reference to <Entity>`, `List of <Entity>`.
- **No reference left uncataloged (transitive closure).** Every property whose Type is `Reference to <Entity>` or `List of <Entity>` requires that entity to have its **own** `###` sub-block with a full `| Property | Type | Meaning | Constraints |` table somewhere in this section. This applies **transitively**: an entity reached only because another referenced entity points to it is itself cataloged, and so on, until no referenced entity remains without its own sub-block. No entity may appear merely as a `Reference to <Entity>` / `List of <Entity>` type with its properties absent.
- **No grouped "externally-owned" sections.** Never merge multiple referenced entities into a single `###` section (e.g. `### Externally-owned reference entities`). Every entity that appears as a `Reference to <Entity>` or `List of <Entity>` Type anywhere in the entity tables — regardless of which module owns it — must have its own dedicated `###` sub-block with a complete `| Property | Type | Meaning | Constraints |` table. Module ownership belongs only in the entity's description sentence ("Externally owned by the loan domain; …"), not in the block structure. A single grouped prose block is never a valid substitute for individual property tables.
- **Mandatory reference-closure inventory before finalizing.** After writing all entity blocks, build a checklist in working notes: collect every distinct entity name appearing as a `Reference to <Entity>` or `List of <Entity>` Type in any row of any entity table; for each one, confirm a `###` sub-block exists somewhere in this section. Any gap must be resolved by opening the owning domain class file, reading its properties, and filling the block — before Step 7 runs.
- **Catalog once, then cite.** Each entity gets exactly **one** `###` sub-block, written at its first reach; every later `Reference to <Entity>` / `List of <Entity>` mention simply names it (the reader follows the single catalog block). Pervasively-shared infrastructure entities (the actor/user record, office/branch, organization) are cataloged once on first reach like any other entity and thereafter only named — they are **not** exempt from being cataloged, but they are **not** repeated.
- **Enum types must resolve too.** Every property Type written as `Enum (<EnumName>)` must have its **complete** value table present in `## Domain Concepts and States` (Rule 12). No enum may be named as a property type without its full value set existing there. The property's Type cites the enum by name; the values live in the cross-referenced Domain Concepts table (do not re-list them here).
- **Constraints** records (from `static constraints { }`): required vs. optional (`nullable:`), value ranges or limits (`min:`/`max:`/`size:`/`maxSize:`), uniqueness (`unique:`), default value, relationship cardinality, and the governing enum where the property is an enum.
- Shared audit/version/soft-delete fields (this project's convention: `createdOn` / `createdBy` / `updatedOn` / `updatedBy`, plus any soft-delete flag and GORM `version` for optimistic locking) **are** listed as rows in **every** entity table — they are part of the complete field set and are not exempt. What is stated once (not re-explained per entity) is their detailed **lifecycle semantics**: the top-of-section note and the `Meaning` column point the reader to Cross-Cutting Requirements → Audit and Record Lifecycle (Step 0b) for how they behave, while the rows themselves still appear in each table.
- **Property names are exact Groovy field names.** Use the **exact camelCase field name** as declared in the domain class source — never capitalise, paraphrase, or rename it. `country` stays `country`; `branchOffice` stays `branchOffice`; `assignedCreditOfficer` stays `assignedCreditOfficer`; `chartOfAccountsId` stays `chartOfAccountsId`. The `Meaning` column is where the plain-English description goes — not the `Property` column.

This section is reference data (like Domain Concepts and States), not a set of EARS statements — so its tables do not take the `the <DomainName> system shall …` form.

### Rule 14 — Per-heading source-file annotation (developer cross-check)

So a developer can cross-check the spec against the codebase, every `## Module:` heading and every **content** `###` subsection carries a `> **Source files:**` blockquote line that lists the source files the section's content was extracted from. This is the **only** place file paths appear in the body of the spec (the other being Open Questions footers); the EARS **statements themselves stay code-free** — no per-statement file references, no class/method/annotation names in statement prose.

**Where it goes:**
- For a `## Module:` block: append the line to the existing `> **Domain:** / **Scope:** / **Entry Points:**` blockquote.
- For a content `###` subsection: a standalone `> **Source files:** …` blockquote line directly under the heading, **before** the first EARS statement (or, for reference sections, before the first table).

**What it lists:** a comma-separated list of the **full project-relative paths** of every source file whose rule-sites or content produced a statement (or table row) in that section, each backtick-quoted. Order them by relevance (primary controller/action service first, then sub-services/validators, then domain classes/enums). Derive the list from the per-file completeness ledger (Step A-2.1) and the traced call chain (Step 2) — do **not** invent paths or list a file you did not open.

```
### Subsidiary Ledger Creation

> **Source files:** `plugins/accounting/grails-app/services/com/bits/gerp/accounting/action/.../CreateAccSubsidiaryLedgerActionService.groovy`, `plugins/accounting/grails-app/services/com/bits/gerp/accounting/service/AccProjectCoaSubledgerMappingService.groovy`

When an operator submits a new subsidiary ledger for a chart of account, the Subsidiary Ledger system shall …
```

**Scope — which headings get the line:**
- ✅ Every `## Module:` heading.
- ✅ Every content `###` subsection inside a module: functional areas, validation concerns, sub-validator subsections, Async/Scheduled pipelines, cross-plugin/external integration subsections.
- ✅ Every `###` entity sub-block in `## Domain Entities and Properties` and every `###` enum/state sub-block in `## Domain Concepts and States` (cite the entity/enum source file(s)).
- ❌ **Excluded** — these are meta or globally-sourced and do **not** carry the line: the header preamble (it already has `> **Source Entry Point(s):**`), Document Conventions, System Overview, all five **Cross-Cutting Requirements** subsections (each is sourced from many global infrastructure files), Business Rules Summary, Open Questions (uses Rule 8 footers instead), Extraction Summary, and the two Review by Developer sections.

A content subsection that is missing its `> **Source files:**` line is rejected by Step 7 and must have the line added from the section's ledger entries.

---

## Step 0 — Project Orientation (Always Run First)

Before examining any controller or action service, perform a one-time project-wide orientation. This prevents missed requirements from shared infrastructure.

### 0a. Identify project structure and active plugins
- This is a multi-module Grails app: `mainapp/` plus 15 plugins under `plugins/`. Read `mainapp/grails-app/conf/BuildConfig.groovy` (or the active `BuildConfig-*.groovy.default` variant — `BuildConfig-all`, `-hr`, `-mf`, `-ffa`) to see which plugins are registered via `grails.plugin.location`. Each plugin has its own `grails-app/{controllers,services,domain,jobs,conf,i18n}` and often `src/groovy`.
- Classify every plugin: **business-logic** (`accounting`, `mf`, `hrm`, `finance`, `Procurement`, `Inventory`, `fixedAsset`, `budget`, `etender`, `ProposalTracking`, `complaintManagement`) vs **framework/shared** (`admin` — base controller/service, user/role; `applicationCommon` — shared domain, IAction framework, caching, integration connectors, annotations) vs **pure infrastructure** (`bitsSpringSession`, `bitsjasperreports`).

### 0b. Read the audit-field convention and any base domain class
- This project's domain classes carry manual audit fields: `createdOn` (Date), `createdBy` (`ApplicationUser`), `updatedOn` (Date), `updatedBy` (`ApplicationUser`). GORM also supplies an optimistic-locking `version`. Some domains carry a soft-delete / status flag.
- These produce **Ubiquitous** requirements that apply to every entity — write them once in Cross-Cutting Requirements → Audit and Record Lifecycle, not per-module. Capture: creation audit, update audit, optimistic locking, any soft-delete/status default. If a shared abstract domain or trait exists, read it and capture its fields once.

### 0c. Read the error / message model (replaces `@ControllerAdvice`)
- This project has no Spring Boot `@ControllerAdvice`. Errors are returned as a **`Message`** object (`SUCCESS` / `ERROR`, with title + body text) built by `UserMessageBuilder.createMessage(...)`, or as a result `Map` with `isError = true` produced by `buildFailureResult(...)` and rendered as JSON by `BaseController.renderOutput` / `getServiceResponse`.
- Read `UserMessageBuilder`, the `Message` class, and `BaseController.getServiceResponse` (`plugins/admin/grails-app/controllers/com/bits/gerp/admin/BaseController.groovy`). Build a complete **condition → message** mapping: what triggers a `Message.ERROR` / `isError`, what title/body text is returned, and which i18n key supplies it. This becomes the "Error Response Format" subsection (Rule 5 — quote text verbatim, note Bengali).

### 0d. Read cross-cutting interceptor logic (replaces `@Aspect`)
- Grails uses `def beforeInterceptor = { … }` on controllers (e.g. `sessionManagementService.setPluginName(...)`) and filter closures rather than AspectJ. Read every `beforeInterceptor` on the controllers in scope and translate each into a Ubiquitous or Optional requirement.

### 0e. Read every filter (replaces `OncePerRequestFilter` / `HandlerInterceptor`)
- Read `mainapp/grails-app/conf/sbicloud/SecurityFilters.groovy` fully and any other `*Filters.groovy`. Extract every `before`/`after`/`afterView` closure: which controllers/actions it targets, what it validates, what it rejects. Translate into Ubiquitous, Optional, or Unwanted Behaviour requirements:
  - Session/auth gate (`session.user == null`) → "If an unauthenticated actor invokes a protected operation, the <Domain> system shall redirect to the login flow / reject the request."
  - HTTP-method guard (`!(request.isPost() || request.isGet())`) → reject with method-not-allowed.
  - AJAX-without-session guard → reject unauthorised AJAX requests.
  - Business-day-open gate (`@RequiresBusinessDay` → `accountingPluginConnector.getInitiateBusinessDay`) → "Where an operation requires an open business day, if the branch's business day is not open, the <Domain> system shall reject the request with a business-day-closed message."
  - Any CSRF / request-size handling found → corresponding statement.

### 0f. Read the security/authorisation model
- Authentication and business-day gating are enforced reflectively in `SecurityFilters.groovy` by reading the `@RequiresAuthentication`, `@RequiresBusinessDay`, `@RequiresBusinessDayClose` annotations (defined in `plugins/applicationCommon/src/java/com/docu/commons/annotation/`) on the controller class and on the action field. `@Secured` (Spring Security) and `@PluginName` also appear.
- Role/permission access is **database-driven** via FeatureAction / feature-menu seed data, resolved through cache services and `SessionManagementService`. Describe the mechanism in plain language: "The <Domain> system shall enforce database-driven feature-and-action access rules. If the actor's assigned role does not have permission for the requested feature action, the <Domain> system shall reject the request before any business logic is executed."
- Environment/feature gates appear in `grailsApplication.config` (`Config.groovy`) and `environments { }` — these become `Where … enabled, …` Optional requirements.

### 0g. Classify each plugin in the call chain — then extract

Do not treat plugins or `src/groovy` directories as black boxes. Classify, then apply the matching procedure.

| Type | Characteristics | Examples | Action |
|------|----------------|---------|--------|
| **Business-logic** | Action services / IAction classes with domain rules, validators, raw SQL, cache logic | `accounting`, `mf`, `hrm`, `finance` action services | Full extraction — apply procedures A–D below |
| **Framework/shared** | Base classes, the action framework, connectors, common domain | `admin` (`BaseService`/`BaseController`/`ActionInterface`), `applicationCommon` (`IAction`, `PluginConnector`, caching) | Read the base contracts once; extract their cross-cutting behaviour (audit, error model, business-day) into Cross-Cutting |
| **Pure infrastructure** | Technical plumbing, no domain rules | `bitsSpringSession`, `bitsjasperreports` | No extraction needed; note why |
| **Enums / constants** | Enum domains and constants | `plugins/<m>/grails-app/domain/.../enums/`, `com/docu/commons/*Constants.groovy` | Extract all enum values (→ Step 0l) and constants used as thresholds |

#### Procedure A — Business-logic action services / validators

**Step A-1 — Discovery (broader than name patterns)**
- Scan **every class** in the action/service packages of the plugins in scope, in both patterns: `grails-app/services/com/bits/gerp/<m>/action/.../*ActionService.groovy` (and `.../service/*Service.groovy`) AND `src/groovy/com/docu/.../*Action.groovy`.
- Primary targets: classes ending in `ActionService` / `Action`, classes implementing `ActionInterface` or `IAction`, classes ending in `Service` that contain `if`-driven checks, and any GORM domain with `validator:` closures.
- Secondary targets: any method that returns `Message.ERROR`, sets `isError = true`, calls `UserMessageBuilder.createMessage(..., Message.ERROR, ...)`, returns an `'error.key'`, or throws — regardless of class name.

**Step A-2 — Read ALL public methods, not just `execute()`**
- An action service exposes the full lifecycle (`executePreCondition` / `execute` / `executePostCondition` / `build*`, or `preCondition` / `execute` / `postCondition`) plus helper methods. Each lifecycle stage can hold distinct validation. Read them all. A plain service (e.g. `AccProjectCoaSubledgerMappingService`) often exposes many public methods — each is a separate extraction target.

**Step A-2.1 — Large-file multi-pass protocol (mandatory for ANY source file > 500 lines, no exceptions)**

The `Read` tool silently truncates at roughly 1,100–1,500 lines or 25,000 tokens. When this happens you receive a `<system-reminder>` like `[Truncated: PARTIAL view — showing lines 1-1153 of 3498 total]`. **This reminder is not a stopping point — it is a paging instruction.** Every method, helper, and inner closure that opens after the truncation point is invisible and produces zero requirements unless you continue reading. This applies to action services, services, controllers, large domain classes, Quartz jobs — **any source file > 500 lines in the call chain**.

Make coverage *deliberate* with a structural-index-first, ledger-verified read plan:

1. **Measure first — ALWAYS, before the first `Read`.** Run `wc -l <file>`. Record `T`. Any file with `T > 500` enters this protocol; `T > ~1500` makes it non-negotiable.

2. **Build a structural index with one cheap grep pass — before reading any body.** Run:
   ```
   grep -nE 'def [a-zA-Z]|^\s*(if|else if|case|default)\b|Message\.ERROR|isError|return ['"'"'"]error|throw new |return (false|null)|render |static triggers|validator:\s*\{' <file>
   ```
   From the output build two line-numbered maps:
   - **method-map** — the start line of every `def`/method;
   - **rule-site-map** — every `if` / `else if` / `case` / `Message.ERROR` / `isError = true` / `'error.key'` return / `throw` / rejecting `render`.
   These two maps are the file's completeness baseline.

3. **Read by method range, not arbitrary windows.** Walk the method-map; for each method `Read` from its start to the next method's start, plus ~30 lines overlap. Do not stop after the chunk that held the method you were hunting — there are more rule-sites after it.

4. **A `PARTIAL view` reminder is a hard signal to continue.** Call `Read` with the next `offset`/`limit`. Do NOT mark anything `[NEEDS REVIEW]` or "beyond the read window" while unread lines remain.

5. **Keep a completeness ledger per file — extended to the written statement.** Mark every method-map entry `READ`; mark every rule-site **`EXTRACTED → EARS statement "<first ~6 words>"`** or **`EXTRACTED → not a rule`** (a guard that branches but never rejects/changes a domain state). The scan is **not done** until every rule-site is accounted for AND your last read reaches the closing brace at/after line `T`. Retain this ledger for Step 6 and the Extraction Summary.

6. **Recurse with no depth limit.** A method spanning two chunks is read across both. A private helper is read fully (A-3). An injected sub-action/sub-service opens a new Procedure A scope on its concrete file (A-4). A method inherited from a superclass in another file is a separate-file lookup — open that file.

**Hard prohibition.** It is forbidden to raise a `[NEEDS REVIEW]` saying "method body lives beyond the read window" / "file too large", to stop reading because a partial-view reminder appeared, or to claim a helper is "past the read window" while unread lines remain. The window is a property of how many chunks you read. Read more chunks.

**Step A-3 — Recursively follow private/helper methods.** Read each fully; extract every rejection branch as a separate Unwanted Behaviour. No depth limit.

**Step A-4 — Follow injected sub-action and sub-service dependencies.** Action services inject other services/`*CacheService`/sub-actions and `PluginConnector`s. Each call opens a **new Procedure A scope** — open the concrete implementation, apply A-2…A-4. **Scan the ENTIRE method body** for `someService.someMethod(...)` and `xxxConnector.yyy(...)` calls; they appear anywhere.

**Step A-5 — Extract every rejection branch as a separate requirement.** Every `if`/`else if`/`case` that returns `Message.ERROR`, sets `isError`, returns an `'error.key'`, or throws is a distinct Unwanted Behaviour. Name the exact entity whose fields supply the reference value (Rule 4). Special patterns: per-record date-range validity, min/max amount ranges (two statements), per-combination mapping rules, business-day gates, duplicate-code/association checks.

**Step A-6 — Delegated rule-object / closure dispatch.** When an action dispatches to a chain of rule objects or a set of GORM `validator:` closures, open **every** rule/closure and read it in full (each is a Procedure A scope). Extract each rejection with its verbatim message (Rule 5). Raising a single `[NEEDS REVIEW]` to stand in for N locatable rules/closures is forbidden.

**Step A-7 — Dynamic-message / mapping lookup.** When a rejection message is returned by a called service or resolved from a config/lookup/cache/seed table rather than written inline, open that service's implementation **and** its backing data (BootStrap seed, `dbScripts` INSERTs, or `*CacheService`). Recover the exact message and the decision logic; express as concrete Unwanted Behaviour statements, not an Open Question.

#### Procedure B — Rule-engine / workflow modules
If a rule-engine or staged-approval workflow exists (e.g. role-wise approval limits, workflow transaction URLs in `WorkflowTransactionUrl`): read each rule/stage in execution order, extract guards (State-Driven) and actions (Event-Driven). Hardcoded approval/amount limits are **critical business rules** stated with exact numeric values. Such workflows deserve their own `Module: <Domain> Approval`.

#### Procedure C — Raw-SQL data access
Raw SQL is a **first-class business logic source** in this project. Treat `new Sql(dataSource).rows(query, params)` / `executeSelectSql/executeInsertSql/executeUpdateSql` (from `BaseService`) identically to a DAO:
- Read every query string. Extract filter conditions, sort order, JOINs, aggregations, dynamic WHERE fragments.
- Note the datasource (main vs report vs ERP) and label requirements accordingly.
- Read any `eachRow` / `GroovyRowResult` mapping for conditional/derived fields.
- Also read GORM dynamic finders / criteria / HQL on domain classes — each filter is a precondition or business rule.

#### Procedure D — Security and access control
- Read `SecurityFilters.groovy` for request-time decisions (auth, business-day, method, AJAX).
- Read the FeatureAction / feature-menu access model and its seed data (`dbScripts` / BootStrap) to recover database-driven role/feature permissions.
- Produce EARS statements describing how the system resolves permitted operations, what happens when a user lacks permission, how feature groupings gate access. This belongs in Cross-Cutting Requirements → Authentication and Authorisation.

### 0h. Read i18n message files
- `mainapp/grails-app/i18n/messages.properties` (+ locale variants) and each in-scope plugin's `grails-app/i18n/messages.properties` / `messages_bn.properties`. These hold exact user-facing wording. Apply Rule 5: quote verbatim; note Bengali presence / back-translation.

### 0i. Identify async / messaging entry points
- Rabbit: `plugins/applicationCommon/grails-app/controllers/com/docu/RabbitController.groovy`, `SendRabbitMessageAction` / `MarkMessageAsReadAction`, topic/fanout exchanges (`RabbitMessagingService`).
- Mercure SSE: `MercureMessagePublisherService` / `src/groovy/com/docu/mercure/MessagePublisherService.groovy`.
- Treat any message-producing or message-consuming action as an entry point if it is in the traced domain or the user asks for it.

### 0j. Identify Quartz scheduled jobs
- `plugins/<m>/grails-app/jobs/.../*CronJob.groovy` / `*Job.groovy` with `static triggers { simple … }` and an `execute()` body, frequently gated by `grailsApplication.config.quartz.<job>.enable`. A job whose `enable` flag defaults off → capture as Optional `[DISABLED]`.

### 0k. Identify cross-plugin and external integrations
- Cross-plugin: calls through `PluginConnector` subclasses — abstract base `plugins/admin/src/groovy/com/bits/gerp/PluginConnector.groovy`, per-plugin abstract connectors `plugins/applicationCommon/src/groovy/com/docu/integration/*PluginConnector.groovy`, concrete impls `plugins/<m>/grails-app/services/com/docu/integration/*PluginConnectorService.groovy` (registered via static `setPlugin` in `@PostConstruct initialize()`). For each call: business operation, data sent, data returned, behaviour when the target plugin is not installed (`@Autowired(required=false)`).
- External / second datasource: any ERP/report DB query, third-party HTTP, payment middleware → integration requirement.

### 0l. Read all enum types — MANDATORY full enum scan
- Locate every enum: `find plugins -path '*/enums/*' \( -name '*.groovy' -o -name '*.java' \)` plus legacy enums under `com/docu/commons/`. Read the **full source** of every enum referenced (directly or transitively) by any controller, action service, service, domain, or command in the call chain. Capture each constant's: identifier (`MOBILE_BANKING`), numeric id if any, `displayName`, `code`, and Bengali label if present.
- These populate **Domain Concepts and States** as Markdown tables (Rule 12). If a statement says "set the status to <X>", `<X>` must be a value present in the status enum table.
- **Guessing display names is forbidden.** Read the enum source and use the exact `displayName`/`code` found there.

### 0m. Read all ID/number generators
- `plugins/admin/grails-app/services/com/bits/gerp/admin/DocumentSequenceIdService.groovy` (Redis `RedisAtomicLong`, per office+feature sequence, format tokens like `[YYYY]-[MM]-[SEQ_NUM]`) and per-module `*CodeGenerationService.groovy` (`AccountsCodeGenerationService`, `MfCodeGenerationService`, `HrCodeGenerationService`, …). Extract the format pattern (prefix, branch/office code, date encoding, sequence suffix), whether the value is global or office-scoped, and the sequence source. Express as a Ubiquitous or Event-Driven requirement — never a `[NEEDS REVIEW]`.

---

## Step 1 — Determine Input Mode

After completing Step 0, identify which input mode applies:

| Mode | Trigger | Action |
|------|---------|--------|
| **Single entry point** | User provides one controller `.groovy` file OR one action-service `.groovy` file | Process that file. If a controller, trace each action into its action services. If an action service, trace outward to its controller and inward to its dependencies. Then run **Step 1.5** to discover and confirm lifecycle siblings. |
| **Multiple entry points** | User provides a list of controller / action-service paths | Process each in order, then run **Step 1.5** for further siblings. |
| **Auto-discover** | User provides a directory path (a plugin, or a package within one) | Recursively find all `*Controller.groovy`, `*ActionService.groovy`, and `src/groovy/.../*Action.groovy` files under it. List them and confirm with the user before proceeding. (Step 1.5 is unnecessary — the directory already enumerates the scope.) |

Also list and confirm Quartz jobs (Step 0j) and Rabbit/Mercure actions (Step 0i) — but only if they belong to the traced domain's call chain or the user explicitly asks for them.

---

## Step 1.5 — Lifecycle Sibling Discovery (Discover + Confirm)

A single controller / action service rarely covers a domain's whole lifecycle. A `Create…ActionService` has sibling `Update…`, `Delete…`, `List…`, `Get…`, and often `Approve…` / `Reject…` action services, plus a Quartz job that acts on the same domain. Extracting only the named entry point produces a spec that silently omits half the domain. This step closes that gap **without** silently pulling in unrelated endpoints: discover the siblings, show them, and let the user confirm the scope.

**Skip this step only when** the input mode is Auto-discover or the user explicitly says "only the file(s) I named."

**1. Derive the domain root.** From each named controller/action service, strip the lifecycle verb and the `Controller`/`ActionService`/`Action` suffix to get the domain root — e.g. `CreateAccSubsidiaryLedgerActionService` → root `AccSubsidiaryLedger`, verb `Create`.

**2. Discover candidate siblings (deterministic, cheap sweep):**
   - **Same package + nested sub-packages** of the named file:
     ```
     find <action-dir> -maxdepth 2 \( -name '*ActionService.groovy' -o -name '*Action.groovy' -o -name '*Controller.groovy' \)
     ```
   - **Name-pattern match across the plugin** — the domain root paired with a lifecycle verb: `Create` / `Update` / `Delete` / `List` / `Get` / `Show` / `Approve` / `Reject` / `Forward` / `Post` / `Settle`:
     ```
     grep -rlE '(Create|Update|Delete|List|Get|Approve|Reject|Post)<DomainRoot>' plugins/<m>/grails-app plugins/<m>/src/groovy
     ```
   - **Strongest signal — shared core service / domain / connector.** Action services that invoke the **same core service**, operate on the **same GORM domain class**, or call the **same `PluginConnector`** as the named entry point are near-certainly the same domain's lifecycle stages. Grep for that service/domain/connector type across the plugin, or run `graphify query "<CoreService> callers"`. Cross-check `UrlMappings.groovy` for routes pointing at the same controller.

**3. Classify each candidate by lifecycle role** so the list is scannable: Management (create/update/delete/list/get) / Approval / Rejection / Posting / Scheduled / Messaging / Monitoring.

**4. Present + confirm via a checkbox multi-select.** Surface the candidates as an explicit **`AskUserQuestion` with `multiSelect: true`** so the user ticks the entry points to include — never as free-form prose.
   - **One checkbox option per candidate.** Option *label* = the class name; *description* = its lifecycle role plus the relevance signal (e.g. "Approval — shares `AccSubsidiaryLedgerService`", "Scheduled — `VoucherNoCreationCronJob` acts on the same domain").
   - **Recommend the core lifecycle set.** The named entry point plus its create/update/delete/list/get and approval/rejection siblings are the suggested default: append `(Recommended)` and **list them first**. State that the recommended set is the default and that unticked candidates (monitoring / scheduled / messaging) are optional add-ons. Always include the named entry point itself as a `(Recommended)` option.
   - **Option-count fallback** (`AskUserQuestion`: 2–4 options per question, up to 4 questions): ≤4 candidates → one multi-select question; >4 → split by lifecycle role, recommended roles first; if still >4 groups, fold the least-likely (monitoring/scheduled/messaging) into one "include these supporting entry points too" bundle.

**5. Lock the scope.** The user-confirmed set becomes "the entry points being processed" for all downstream steps: Rule 7 module derivation, the `Source Entry Point(s)` header line, and the Extraction Summary list. Shared-core entry points produce **one consolidated `Module: <Domain> Validation Rules`** per Rule 7 deduplication.

**No silent expansion, no silent omission.** Never extract a sibling the user did not confirm; never hide a discovered sibling. The user owns the scope decision.

---

## Step 2 — Build the Full Call Chain for Each Entry Point

An "entry point" is a controller action, an action service, a Quartz job's `execute()`, or a Rabbit consumer action. For **each** entry point, trace every dependency completely before writing a single EARS statement.

### 2a. Read the controller / action-service / job entry point
- **Controller:** for each action (closure `def x = { }` or method `def x()`) record: the action name, its `UrlMappings` route if any, `@PluginName` / `@RequiresAuthentication` / `@RequiresBusinessDay` / `@Secured` annotations, the `beforeInterceptor`, every action service it calls, and how it responds (`render … as JSON`, `renderOutput(action, params)`, a model map, or a redirect).
- **Action service:** identify the request inputs (the `params`/result `Map` keys or `Command` it reads), the lifecycle stages, and every service/connector/cache it calls.
- **Quartz job:** record the trigger (`static triggers`), the enable/log config gate, the domain it acts on, and the rule it enforces.
- **Rabbit consumer action:** record the payload, exchange/routing, and services called.

### 2b. Follow every service / action call
- Read the full **concrete** implementation (action service or plain service), not just an interface. If it lives in another plugin, read it there.
- Capture the action lifecycle (`BaseController.renderOutput` → pre/execute/post/build, short-circuit on `isError`) as the orchestration/atomicity model. `static transactional` / `@Transactional` → atomicity requirement.
- Every conditional rejection branch becomes its own Unwanted Behaviour statement (Procedure A).

### 2c. Follow every GORM domain access
- Read every dynamic finder (`findByX`, `findAllByXAndY`), criteria query, and HQL the service uses on a domain class.
- Read the domain class fully: properties, `static constraints { }`, `static mapping { }`, `static hasMany/belongsTo/hasOne`, `validator:` closures, enum fields.
- **Catalog every property into the Domain Entities and Properties section (Rule 13).** Reading a domain class is not done until **every field it declares** is a `| Property | Type | Meaning | Constraints |` row — a complete mirror of the source class, including fields no traced behaviour references. This is in addition to extracting `validator:`/constraint *rules* as Unwanted Behaviour statements.
- Child entities (`hasMany`) and embedded structured objects get their own catalog sub-block. Shared audit/version/soft-delete fields **are** listed as rows in each entity's table (they are part of the complete field set); only their lifecycle semantics are referenced once from the Step 0b note rather than re-explained per entity.
- **Recurse into every referenced/associated domain class (transitive closure).** For each property typed `Reference to <Entity>` / `List of <Entity>` (a `belongsTo`/`hasOne`/`hasMany`/association field), open that referenced domain class and catalog it (Rule 13) — not just `hasMany` children. Then repeat for any entity *it* references, continuing until the reference closure is exhausted. An entity already cataloged in this run is **not** re-read or re-cataloged (catalog once, then cite). Shared infrastructure entities (user/office/branch/organization) follow the same rule: read and catalog on first reach, then only name. Likewise, any enum named as a property type is read in full (Step 0l) so its complete value table exists in Domain Concepts and States.

### 2d. Follow every raw-SQL call
- Raw SQL is **first-class** (Procedure C). For `new Sql(dataSource).rows/executeInsert/executeUpdate` and `BaseService.executeSelectSql/executeInsertSql/executeUpdateSql`: extract filter conditions, sort, pagination, aggregations, JOINs, conditional SQL fragments. Identify the datasource and label requirements accordingly.

### 2e. Follow every row mapping
- Read `eachRow` / `GroovyRowResult` handling fully. Extract conditional mapping, derived/calculated fields, null-handling.

### 2f. Follow every PluginConnector / external call
- For each cross-plugin call (`accountingPluginConnector.getBusinessDay(...)`, etc.) and each external/second-datasource call: business trigger, data sent, expected response, and behaviour when the plugin is absent or the call fails.

### 2g. Follow every async publish / listener
- Rabbit publish (topic vs fanout), Mercure SSE publish, cache-refresh side effects. Identify sync vs async and post-commit semantics where present.

### 2h. Read supporting classes
- **Command / request objects & domain `constraints { }`:** every constraint (`blank:`, `nullable:`, `min:`, `max:`, `size:`, `maxSize:`, `matches:`, `unique:`, `validator:`) → one Unwanted Behaviour per constraint, placed in the dedicated field-level subsection (Rule 6). Resolve every `'error.key'` against the message bundle (Rule 5).
- **`validator:` closures:** read the body fully — the logic is a business rule.
- **Enums:** every value is a domain state — capture in Domain Concepts and States (Rule 12, Step 0l).
- **Message / exception text:** informs the Unwanted Behaviour wording.

### 2i. The "named-not-read" prohibition

If you mention a method, helper, action, sub-service, enum, connector, or generator name in your notes or in a draft `[NEEDS REVIEW]` item — you must have **opened the file and read the body** before finalising. Naming without reading is the single largest source of unnecessary `[NEEDS REVIEW]` items.

Concrete examples:
- Mention of `checkAssociationOfSubledgerList` → open the action service, read the method, extract its rules.
- Mention of `AccProjectCoaSubledgerMappingService` → open it, apply Procedure A.
- Mention of `PaymentType.MOBILE_BANKING` → open the enum, read its `displayName`/`code`.
- Mention of `getDocumentSequenceId` → open `DocumentSequenceIdService`, extract the format.

If reading genuinely fails (file not found after search, binary, etc.), record that verbatim in the Rule 8 footer: `*Where agent looked:* searched for `<glob>` — no matching file found.`

---

## Step 3 — Handle Ambiguity

### Step 3a.0 — Mandatory pre-NEEDS-REVIEW gates (Rule 9 enforcement)

Before any `[NEEDS REVIEW]` enters Open Questions, **all applicable gates** must have been performed. Record what was tried for the Rule 8 footer.

| Gate | When required | Action |
|------|---------------|--------|
| **Enum source** | Ambiguity names an enum value, code, or constant | Open `plugins/<m>/grails-app/domain/.../enums/<EnumName>.groovy\|.java`. List every value's `displayName`/`code`. |
| **Action/validator body** | Ambiguity names an action/check/validate method | Open the action service / service, read the method body. Apply Procedure A. |
| **Sub-service / connector** | Ambiguity names an injected service, `*CacheService`, or `PluginConnector` | Open the concrete impl. Apply Procedure A recursively. |
| **Access control** | Ambiguity concerns auth, business day, roles, permissions | Open `mainapp/grails-app/conf/sbicloud/SecurityFilters.groovy`, the annotation in `applicationCommon/.../annotation/`, and the FeatureAction seed in `dbScripts/`. |
| **Entry point** | Ambiguity concerns whether a method is a job, Rabbit consumer, controller action, or service | Grep for `static triggers`, `IAction`, `ActionInterface`, `def <name> = {`/`def <name>(`, or a `UrlMappings` route. |
| **ID/format generator** | Ambiguity concerns a generated identifier format | Open `DocumentSequenceIdService.groovy` and the relevant `*CodeGenerationService.groovy`. |
| **Delegated rule / closure** | Ambiguity concerns a chain of rule objects or `validator:` closures | Open every rule/closure, read it (Step A-6). |
| **Dynamic-message / mapping** | A rejection message comes from a service/lookup/seed, not the action body | Open the service impl + its backing data (BootStrap / `dbScripts` / cache) (Step A-7). |

Skipping a gate is not allowed. If a gate cannot resolve the ambiguity, say so explicitly in the Rule 8 `*Where agent looked:*` footer — quote the path and line range read.

### Step 3a — Resolve From Project Sources Before Asking the User

If the gates do not yield an answer, broaden the search (stop at the first that answers):

1. **Spock specs** — `mainapp/test/integration/sbicloud/*Spec.groovy`, `test/unit/`. Treat as **hints only** — read them to discover business scenarios, boundary values, and expected messages, but **confirm every rule against production code** before inclusion. Record as `[TEST-HINT]` with a verification note.
2. **Application config** — `Config.groovy` / `BuildConfig.groovy` and `environments { }` (feature flags, quartz enable, limits, timeouts).
3. **DB scripts** — `DB Scripts/` and `plugins/<m>/dbScripts/<year>/<JIRA-ID>/*.sql` (column constraints, unique indexes, document-sequence seeds, lookup INSERTs).
4. **BootStrap seed data** — `BootStrap.groovy` (mandatory startup records, status codes, default config).
5. **Constants** — `com/docu/commons/*Constants.groovy` and module constants (thresholds, exchange names).
6. **Domain / technical docs** — `docs/`, `BR/`, any `*.md` mapping files.
7. **Graphify knowledge graph** — `graphify-out/`. Use `graphify query "<concept>"`, `graphify path "<A>" "<B>"`, `graphify explain "<concept>"`.
8. **Git history** — `git log --all --oneline --grep="<keyword>"`, `git log -p -- <file>`.

Only after the gates AND all eight sources fail may an item be marked `[NEEDS REVIEW]`. Do not interrupt the user mid-extraction; collect all unresolved items and present them at the end with their Rule 8 footers.

### Step 3b — Interactive Questions (After Exhausting Project Sources)

For remaining ambiguities, pause and ask the user a precise question before writing the requirement. Group multiple questions together.

### Step 3c — Open Question authoring (Rule 8 format)

When an item must be `[NEEDS REVIEW]`, write it in the exact two-footer format:

```
N. **[NEEDS REVIEW]** <Concrete question a domain expert can answer in one or two sentences.>
   *Where agent looked:* `<relative/path.groovy>:<line>` — <what was read and why insufficient>. `<another/path.groovy>:<line>` — <same>.
   *Hint for reviewer:* Likely answer in `<probable/file.groovy>` (<one-sentence reasoning>). Try `<grep / find / graphify command>` to locate.
```

**Both footer lines are mandatory.** Bad: `1. **[NEEDS REVIEW]** What is the code format?` (no footers); `1. **[NEEDS REVIEW]** What is X? `generateX` was observed.` (named but not read). Good:

```
1. **[NEEDS REVIEW]** What is the exact format of the subsidiary ledger code generated for a new ledger? Does it encode the chart-of-account id and a sequence suffix?
   *Where agent looked:* `plugins/accounting/grails-app/services/com/bits/gerp/accounting/service/AccProjectCoaSubledgerMappingService.groovy:58` — `subledgerCodeSequence(chartOfAccountsId)` returns a max+1 integer but the surrounding format wrapper was not found here.
   *Hint for reviewer:* Likely assembled in `AccountsCodeGenerationService.groovy` or `DocumentSequenceIdService.groovy`. Run `grep -rn "subledgerCode\|getDocumentSequenceId" plugins/accounting plugins/admin` to confirm.
```

---

## Step 4 — EARS Pattern Selection

Apply in priority order. A single behaviour may produce multiple statements of different types.

### Priority 1 — Event-Driven
`When <trigger>, the <DomainName> system shall <response>.` — behaviour triggered by an actor, internal event, Quartz fire, or Rabbit message.

### Priority 2 — State-Driven
`While <state>, the <DomainName> system shall <response>.` — behaviour only while the system or an entity is in a particular state.

### Priority 3 — Unwanted Behaviour
`If <unwanted condition>, the <DomainName> system shall <response>.` — every validation rule, guard, `Message.ERROR`/`isError` rejection, constraint failure.

### Priority 4 — Optional
`Where <feature or condition is enabled>, the <DomainName> system shall <response>.` — config flags, `environments` gates, disabled Quartz jobs, plugin-presence guards.

### Priority 5 — Ubiquitous
`The <DomainName> system shall <response>.` — cross-cutting rules that always apply.

### Priority 6 — Complex
`While <state>, when <trigger>, the <DomainName> system shall <response>.` or `Where <feature>, when <trigger>, the <DomainName> system shall <response>.`

---

## Step 5 — Produce the EARS Output File

Write to `docs/ears/<DomainName>-EARS-Specification.md` (project-relative). **Overwrite** any existing file. Create `docs/ears/` if missing.

The top-level skeleton is fixed (Rule 11). The **Module sections are NOT fixed** — derived from the entry points per Rule 7. Never invent unrelated top-level sections. Never include a Table of Contents (Rule 10).

### Output File Template

The `> **Source Entry Point(s):**` line lists the full project-relative path of every controller and/or action service in the **confirmed Step 1.5 scope** — comma-separated. Never list a discovered sibling the user did not confirm.

```
# <DomainName> Business Requirements Specification (EARS)

> **Format:** Easy Approach to Requirements Syntax (EARS)
> **Source:** Reverse-engineered from existing codebase — SBICloud BD (BRAC ERP), Grails 2.5.x, base packages `com.docu.*` (legacy) and `com.bits.gerp.*` (current)
> **Source Entry Point(s):** `<relative/path/to/EntryPoint1.groovy>`[, `<relative/path/to/EntryPoint2.groovy>` …]
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
| `[TEST-HINT]` | Rule surfaced from a Spock spec and confirmed against production code |
| `Review by Developer` | Two sections at the end of this file where a developer records findings from reviewing this spec against the codebase |

---

## System Overview

<One rich domain narrative paragraph (5–8 sentences). Cover: what the system manages, the lifecycle scope, which plugin(s) it spans, what validation layers it enforces (field-level constraints, action-service checks, business-day gating, cross-plugin checks), and how it integrates with sibling plugins. Derived from controller/action names, domain names, plugin structure, docs. No code references.>

---

## Cross-Cutting Requirements

### Audit and Record Lifecycle

<Ubiquitous statements from the audit-field convention (Step 0b): creation audit (createdOn/createdBy), update audit (updatedOn/updatedBy), optimistic locking (version), any soft-delete/status default. One paragraph per rule.>

### Authentication and Authorisation

<Optional statements for annotation-gated security (@RequiresAuthentication, @RequiresBusinessDay) and any environment gates. Then the role/feature access control description (database-driven FeatureAction) as plain prose, and a per-operation access sub-list using `-` bullets where roles differ per operation:>

The <DomainName> system shall enforce the following access controls for all operations:

- When an actor <operation A>, the <DomainName> system shall require the actor to hold permission for <feature action>.

If an authenticated actor attempts an operation without the required feature-action permission, the <DomainName> system shall reject the request before any business logic executes.

### Request Handling

<Ubiquitous and Unwanted statements from SecurityFilters and beforeInterceptors: HTTP-method guard, AJAX-without-session guard, plugin-name binding, any CSRF/request handling. One paragraph per rule.>

### Operational Cross-Cuts

<Optional and Ubiquitous statements: business-day-open gate, any captcha/locking, exception logging, cache-refresh side effects. One paragraph per rule.>

### Error Response Format

The <DomainName> system shall return operation outcomes as a structured message payload containing: a result type (success or error), a message title, a message body, and — for validation failures — the list of field-level errors. Error messages are resolved from the message catalogue and are available in English and Bengali.

The <DomainName> system shall map error conditions to message text as follows:

| Error condition (plain English) | Message text (verbatim, English) | Bengali present? |
|----------------------------------|-----------------------------------|------------------|
| <condition> | "<exact message>" | yes / no |
| … one row per distinct Message.ERROR / isError / 'error.key' rejection found … |

When a rejection corresponds to an i18n message key, the <DomainName> system shall resolve the message in both English and Bengali from the message catalogue and include the localised text in the response.

---

<!--
  MODULE SECTIONS — derived per Rule 7 (lifecycle + cross-cutting thresholds). NOT a fixed skeleton.
  Per-entry-point primary modules — one per controller/action-service cluster, named after the lifecycle role:
    - CRUD cluster        → "Module: <Domain> Management"
    - Approval cluster    → "Module: <Domain> Approval"
    - Posting cluster     → "Module: <Domain> Posting"
    - Rabbit/Mercure      → "Module: <Domain> Messaging"
    - Quartz job          → "Module: <Domain> Scheduled Processing"
    - Monitoring          → "Module: <Domain> Monitoring"
  Cross-cutting modules — include ONLY if the threshold is met (Rule 7 table):
    - "Module: <Domain> Validation Rules"               (validator/check with >5 rejection branches)
    - "Module: Sub-Validators"                          (≥2 specialised sub-validators)
    - "Module: Async and Scheduled Processing"          (any async side effect or Quartz job on the domain)
    - "Module: Cross-Plugin and External Integrations"  (any PluginConnector / external / second-datasource call)
  Do NOT include empty placeholder modules. If multiple entry points share a validator, produce ONE consolidated Validation Rules module.
-->

## Module: <DomainName> Management

> **Domain:** <human-readable name>
> **Scope:** <1–2 sentences describing what this module covers>
> **Entry Points:** Grails controller action / action service [/ Quartz job / Rabbit action]
> **Source files:** `<relative/path/to/Controller.groovy>`, `<relative/path/to/ActionService.groovy>`, `<… every file feeding this module …>`

### <Functional Area, e.g. "Subsidiary Ledger Creation">

> **Source files:** `<relative/path/to/CreateXActionService.groovy>`, `<relative/path/to/XService.groovy>`, `<relative/path/to/XCommand.groovy>`

<Event-Driven happy-path paragraphs first, then State-Driven guards, then Unwanted Behaviour rejections. Each paragraph is a standalone EARS statement.>

**Field-level validation — <RequestName>:**

If <field> is not provided, the <DomainName> system shall reject the request.

<… one paragraph per constraint in the domain/command constraints block …>

### <Next Functional Area>
<EARS statements>

---

<!-- Include ONLY if a validator/check has >5 rejection branches (Rule 7). -->

## Module: <DomainName> Validation Rules

> **Domain:** Business Rule Validation — <Scope>
> **Scope:** All validation rules applied by the action services during the operations traced above. These rules execute after field-level constraint validation and before persistence. If multiple entry points share these rules, all share them.
> **Entry Points:** Invoked internally by the entry points above.
> **Source files:** `<relative/path/to/ValidatorOrService.groovy>`, `<… every validator/sub-service/enum file feeding these rules …>`

### <Validation Concern>

> **Source files:** `<relative/path/to/Service.groovy>`

<One paragraph per rejection branch.>

---

<!-- Include ONLY if ≥2 specialised sub-validators are invoked. -->

## Module: Sub-Validators

> **Domain:** Specialised Domain Validation — <list the concerns>
> **Scope:** Domain-specific validation rules applied as part of the main validation flow.
> **Source files:** `<…one per sub-validator file…>`

### <Sub-Validator>

> **Source files:** `<relative/path/to/SubValidatorService.groovy>`

<EARS statements>

---

<!-- Include ONLY if any async side effect fires or a Quartz job acts on the domain. -->

## Module: Async and Scheduled Processing

> **Domain:** Asynchronous and Scheduled Processing
> **Scope:** Asynchronous side effects (Rabbit publish, Mercure SSE, cache refresh) and scheduled jobs acting on this domain.
> **Source files:** `<relative/path/to/CronJob.groovy>`, `<relative/path/to/RabbitAction.groovy>`, `<relative/path/to/CacheService.groovy>`

### <Pipeline, e.g. "Voucher Number Generation Job">

> **Source files:** `<relative/path/to/VoucherNoCreationCronJob.groovy>`

<EARS statements, with [DISABLED] markers where the enable flag is off by default>

---

<!-- Include ONLY if the entry points make any cross-plugin / external / second-datasource call. -->

## Module: Cross-Plugin and External Integrations

> **Domain:** Cross-Plugin and External System Integrations
> **Scope:** All calls across plugin boundaries (via PluginConnector) and to systems outside this domain's ownership.
> **Source files:** `<relative/path/to/PluginConnectorService.groovy>`, `<relative/path/to/ErpQueryService.groovy>`

### <Integration, e.g. "Accounting Business-Day Lookup">

> **Source files:** `<relative/path/to/AccPluginConnectorService.groovy>`

<EARS statements, including behaviour when the target plugin is not installed.>

---

## Domain Entities and Properties

> Shared audit fields (creation/update by + on), optimistic-locking version, and any soft-delete flag are listed as rows in every entity table below (they are part of each entity's complete field set); their lifecycle semantics are described once under Cross-Cutting Requirements → Audit and Record Lifecycle and are not re-explained per entity.

<!--
  REFERENCE CLOSURE (Rule 13):
  - Every entity named as a `Reference to <Entity>` / `List of <Entity>` Type below — and, transitively, every entity those referenced entities point to — MUST have its own ### block here with a complete | Property | Type | Meaning | Constraints | table.
  - COMPLETE FIELD SET: every entity table — in-scope AND externally-owned alike — mirrors the FULL field list declared in its source class: one row per declared field, including audit/version/soft-delete fields, including fields no requirement references. A partial "only the fields the traced code touched" table is FORBIDDEN. Open the domain class and enumerate all declared fields.
  - FORBIDDEN: merging multiple referenced entities into a single "### Externally-owned reference entities" prose block. Each entity — regardless of which module owns it — gets its own ### sub-block. Module ownership goes in the entity's description sentence only and is never a reason to list fewer fields.
  - Catalog each entity ONCE (first reach); later mentions just name it. Shared infrastructure entities (user/office/branch/organization) are cataloged once like any other, never repeated, never skipped.
  - Property column uses the EXACT Groovy camelCase field name from the source (`country`, `branchOffice`, `assignedCreditOfficer`) — never a capitalised or paraphrased business name.
  - Every `Enum (<Name>)` Type must have its full value table in `## Domain Concepts and States`. No type may be named without its properties/values existing.
  - Before finalizing: run the reference-closure inventory — list every distinct entity named as Reference to / List of across all rows; confirm each has a ### block. Zero gaps allowed.
-->

### <Entity, e.g. "Subsidiary Ledger">

> **Source files:** `<relative/path/to/AccSubsidiaryLedger.groovy>`

<One plain-language sentence describing what this entity represents.>

| Property | Type | Meaning | Constraints |
|----------|------|---------|-------------|
| <exact Groovy field name from source> | <Amount / Date / Identifier / Text / Enum (<name>) / Reference to <Entity> / …> | <plain English description of what the field represents> | <required/optional, range, uniqueness, default, cardinality, governing enum> |
| … one row per field declared in the source class — every declared field, including audit/version/soft-delete and fields no requirement references … |

### <Child entity or embedded object>

> **Source files:** `<relative/path/to/ChildEntity.groovy>`

| Property | Type | Meaning | Constraints |
|----------|------|---------|-------------|
| … |

---

## Domain Concepts and States

### <Primary Entity>

> **Source files:** `<relative/path/to/StatusEnum.groovy>`, `<relative/path/to/Entity.groovy>`

<One paragraph describing the entity in plain business language.>

**<Entity> States:**

| State Name | Business Meaning |
|------------|-----------------|
| … one row per enum value, business-logical order … |

**State Transitions:**

| From State | To State | Triggered by |
|------------|----------|-------------|
| (new) | <state> | <business event> |
| … one row per transition discovered … |

### <Domain Type / Role / Sub-type Enum>

| Value | Display Name | Business Meaning |
|-------|--------------|-----------------|
| … |

<… one table per enum collected in Step 0l …>

---

## Business Rules Summary

<A flat numbered list of the most critical non-obvious business rules — approval/amount thresholds, eligibility criteria, date/business-day constraints, uniqueness rules, cross-plugin dependencies, key config values, code/sequence formats. 15–25 items for a typical large module. Each one or two sentences.>

1. <Rule>
2. <Rule>
…

---

## Open Questions

A numbered list of the `[NEEDS REVIEW]` items that **remained unresolved after the Step 6.5 auto-resolution pass**. Each carries the two mandatory Rule 8 footer lines.

1. **[NEEDS REVIEW]** <Concrete question.>
   *Where agent looked:* `<relative/path.groovy>:<line-range>` — <what was read and why insufficient>.
   *Hint for reviewer:* Likely answer in `<probable/file.groovy>` (<reasoning>). Try `<command>` to locate.

…

---

## Extraction Summary

| Metric | Count |
|--------|-------|
| Controllers processed | <N> (`<Name1>`, …) |
| Action services processed | <N> (`<Name1>`, …) |
| Quartz jobs processed | <N> |
| Rabbit / Mercure actions processed | <N> |
| Plugins traced | <N> (`<plugin1>`, …) |
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

- `<File>.groovy` (<T> LOC): <sites> rule-sites · <accounted> accounted · 0 uncovered
- … one line per large file in the call chain …

**Extraction completed:** <Day, DD Month YYYY> (use the runtime current date)

---

## Review by Developer (code)

<!-- Developer: after reviewing this spec against the codebase, list source-code references to rules
     that are MISSING from this spec. One finding per line. Pointer precision helps the agent:
       - [ ] `File.groovy#method`           — what rule is missing   (most precise)
       - [ ] `File.groovy:120-145`          — what rule is missing
       - [ ] `File.groovy`                  — what rule is missing   (whole file)
       - [ ] a plain note with no pointer   (agent auto-locates from the description)
     Optionally force placement by appending:  → Module: <Module> › <Subsection> -->

_None yet — add findings above._

---

## Review by Developer (business requirements)

<!-- Developer: list business decisions/requirements that need a human answer (no code expected).
     One per line; these become [NEEDS REVIEW] Open Questions.
       - [ ] <the business decision or requirement needed, one sentence>   | context: `File.groovy`
     Optionally append:  → Module: <Module> › <Subsection> -->

_None yet — add findings above._
```

### Counting and tallying rules
- Count statements by their leading EARS word. `After` (a post-commit/post-condition side effect) counts as Event-Driven.
- Bulleted access-control entries inside Cross-Cutting count toward Event-Driven if they begin with `When`.
- If a module exhausts a category with zero statements, still list the category with `0`.
- The `[DISABLED]` count should briefly name what is disabled (e.g., "1 (voucher-number Quartz job disabled by config)").

### Naming the file
- Single domain → `<DomainName>-EARS-Specification.md` (e.g., `SubsidiaryLedger-EARS-Specification.md`).
- Multiple unrelated domains in one run → `<DomainName1>-<DomainName2>-EARS-Specification.md`, or per-domain files if genuinely separate.

---

## Step 6 — Coverage Verification Pass (Subagent)

Step 5 produces a *draft* spec. Before it is final, independently prove that **every rule-site maps to a statement** — this is what makes the single pass gap-free *by construction*. Do not rely solely on the main agent's own ledger; re-derive coverage with fresh eyes.

**Mechanism.** For each large file in the call chain (any `> ~500` LOC source already read in Step 2 / Procedure A — action services, large services, raw-SQL DAOs, controllers, large domain classes), spawn **one subagent per large file** (Agent tool, `subagent_type: Explore`). Give each subagent: the source file path, the finished draft EARS file path, and the rule-site grep from Step A-2.1.

The subagent's sole job: rebuild the **rule-site-map** from grep, read the file in full under the Step A-2.1 protocol, and for each rule-site decide whether the EARS file already expresses it. Matching is **semantic**, anchored in priority order:
1. **Verbatim i18n message (Rule 5)** — search the EARS text for the exact quoted string; a match is near-conclusive.
2. **Exact reference entity (Rule 4) + condition direction + response verb** — distinct records stay distinct; exceeds / below / missing / duplicate; reject / set status / require permission.
3. **Behavioural paraphrase** — for rules with no message, a statement whose trigger and response mean the same thing.

**Return contract.** The subagent returns **only**: a list of **UNCOVERED** rule-sites (`file:line` · condition · verbatim message · reference entity) plus its ledger line. The subagent **must not edit** the EARS file.

**Main-agent loop.** For every uncovered rule-site reported, write the missing statement into the correct module (Rule 7 placement; quote any message verbatim; no IDs/bullets/code refs). Re-verify changed files until every subagent returns `uncovered == 0`.

**Discipline.** One large file per subagent. A subagent that returns `unread > 0` is sent back to finish — "beyond the read window" is never a valid stop while lines remain.

---

## Step 6.5 — Auto-Resolve Open Questions (Fresh Subagents, Breadcrumb-Only)

Step 5 may have produced `[NEEDS REVIEW]` Open Questions. By now you have already paid the expensive cost: the gates were run, the cited files read, the two-line footer written. **Resolution is therefore cheap — it is just *executing* those breadcrumbs.** This step chases every breadcrumb with a clean-context subagent and folds whatever resolves back into the spec *before* it is finalised.

**Skip-if-empty.** If Step 5 produced **zero** `[NEEDS REVIEW]` items, this step is a no-op — go straight to Step 7.

Resolved findings flow into the spec as **normal finalised EARS statements** (no `[NEEDS REVIEW]→[RESOLVED]` rewrite). The only marker a resolved statement carries is a trailing ` [Auto-resolved]` so a reviewer knows its value was *derived via a breadcrumb chase* and should be spot-checked.

### Mechanism

1. **Collect candidates from context — do NOT re-read the EARS file.** You already hold every drafted Open Question (text, `*Where agent looked:*` citations, `*Hint for reviewer:*` commands). Build the candidate list from working memory.

2. **Spawn read-only investigator subagents in parallel** (Agent tool, `subagent_type: Explore`), a small batch of questions each. Each subagent's job, per question: run each backticked hint command **verbatim**; `Read` the exact file:line spots named; stop the moment a definitive answer appears. The subagent **must not** re-trace the call chain, run broader greps, read unnamed siblings, or edit any file.

3. **Subagent return contract (read-only).** Per question, exactly one of:
   - `RESOLVED` — a definitive answer plus `Source: <file>:<line>` for every spot read. Definitive = a concrete value · a finite set/list (every member) · a finite range · a format pattern · a categorical fact.
   - `STILL OPEN` — one-line reason (cited file absent / command empty / matches ambiguous).

4. **Apply results (main agent is the sole writer).**
   - **RESOLVED** → write the value into the affected statement(s): strip vague placeholders, substitute the concrete value(s), quote verbatim any message/enum/constant, list every member of a set, name the exact reference entity (Rule 4). Append ` [Auto-resolved]`. Absorb newly revealed enum values / transitions / thresholds into Domain Concepts (Rule 12). **Remove the item from Open Questions.**
   - **STILL OPEN** → leave the item as `[NEEDS REVIEW]` with both footers byte-for-byte intact.

5. **Guards.**
   - **Contradiction guard.** If a resolution would contradict an existing statement, do **not** apply it; leave the item open and append one sentence to its `*Where agent looked:*`: `Investigation contradicted existing statement at <module/subsection>; resolution withheld for human review.`
   - **Unsafe-command guard.** Never run a hint command referencing paths outside the repo or destructive flags (`-delete`, `-exec rm`, `--force`). Skip just that command; fall back to cited reads.

6. **Update the Extraction Summary** — recompute pattern counts, the residual `[NEEDS REVIEW]` count, and the auto-resolved-in-pass tally.

---

## Step 7 — Quality Checklist (Run Before Finalising Output)

Before finalising, verify every item. A failed check means re-trace the relevant source or re-format the output.

### Coverage Completeness (Ledger + Verification)
- [ ] Every source file > 500 LOC in the call chain has a grep-built structural index (method-map + rule-site-map) made **before** reading bodies (Step A-2.1).
- [ ] Every rule-site line is accounted for in the per-file ledger — each marked `EXTRACTED → EARS statement "<…>"` or `EXTRACTED → not a rule`; none left unread.
- [ ] The Step 6 subagent verification pass ran for every large call-chain file and every subagent returned `uncovered == 0` (and `unread == 0`).
- [ ] Extraction Summary shows `Rule-sites uncovered: 0` and carries one per-file ledger line per file > ~500 LOC.

### Open-Question Auto-Resolution (Step 6.5)
- [ ] If Step 5 produced any `[NEEDS REVIEW]` items, Step 6.5 ran (read-only subagents fed the breadcrumbs in-prompt). If none, Step 6.5 was correctly skipped.
- [ ] Every auto-resolved question was removed from Open Questions and its answer folded in; each changed statement carries a trailing ` [Auto-resolved]`, with messages/literals quoted verbatim and every member of a set listed.
- [ ] Newly revealed enum values / transitions / thresholds were absorbed into Domain Concepts tables.
- [ ] Every residual `[NEEDS REVIEW]` item still carries both breadcrumb footers byte-for-byte; contradiction-withheld items have the one-sentence note.

### Formatting Compliance (Rules 1–14)
- [ ] **Rule 1:** Every statement uses `the <DomainName> system` — no bare "the system", no project name as subject.
- [ ] **Rule 2:** No statement is prefixed with an ID or uses a bullet/number — every statement is a plain paragraph.
- [ ] **Rule 3:** No two rejection branches merged into one paragraph. The Unwanted Behaviour count roughly matches the rejection-branch count of every traced action/validator.
- [ ] **Rule 4:** Every comparison statement names the exact record (domain class / row / cache value) supplying the reference value.
- [ ] **Rule 5:** Every Unwanted Behaviour whose action rejects with a message/`'error.key'` includes that text verbatim in double quotes (Bengali noted where relevant).
- [ ] **Rule 6:** Every functional area with field-level constraints has a dedicated `**Field-level validation — <RequestName>:**` subsection.
- [ ] **Rule 7:** Modules are lifecycle-derived. No fixed skeleton forced. Cross-cutting modules appear only if their threshold is met. No empty placeholders.
- [ ] **Rule 8:** Every `[NEEDS REVIEW]` has both footer lines citing concrete `.groovy` paths.
- [ ] **Rule 9:** No `[NEEDS REVIEW]` raised without the relevant Step 3a.0 gates attempted.
- [ ] **Rule 10:** No Table of Contents.
- [ ] **Rule 11:** All top-level sections present in order; the two Review-by-Developer placeholders emitted.
- [ ] **Rule 12:** Every enum/role/status taxonomy is a Markdown table with the full value set from the enum source. Transitions are a three-column table.
- [ ] **Rule 13:** Every entity table is a **complete mirror of its source class** — one row per declared field (audit/version/soft-delete fields included, fields no requirement references included), for in-scope and externally-owned entities alike; no partial "touched fields only" table. Every entity catalog uses the **exact Groovy camelCase field name** from the source (e.g. `country`, `branchOffice`) in the Property column — never a capitalised or paraphrased business name. Business-level types are used in the Type column. No property whose Type is `Reference to <Entity>` / `List of <Entity>` appears without that entity having its own `###` catalog block (transitively, to closure); no grouped "externally-owned" prose block substitutes for individual property tables. No `Enum (<Name>)` Type appears without that enum's full value table in Domain Concepts and States. Each entity cataloged once (shared infrastructure entities included), never repeated. Run the reference-closure inventory: list every distinct entity named as `Reference to` / `List of` across all entity tables and confirm each has a `###` block — zero gaps allowed.
- [ ] **Rule 14:** Every `## Module:` heading and every content `###` subsection carries a `> **Source files:**` line. Excluded sections do not. No statement text contains a file path or code reference.

### Section Completeness
- [ ] Header preamble has all six lines (Format / Source … base packages / Source Entry Point(s) / System name / Purpose / Note). The Source Entry Point(s) line matches the Extraction Summary.
- [ ] Document Conventions table present.
- [ ] System Overview is a single rich paragraph (5–8 sentences).
- [ ] Cross-Cutting Requirements has exactly five subsections in order: Audit and Record Lifecycle, Authentication and Authorisation, Request Handling, Operational Cross-Cuts, Error Response Format.
- [ ] Error Response Format includes the full condition→message table (one row per distinct rejection), with verbatim English text and Bengali-present flag.
- [ ] Domain Entities and Properties has a four-column table for **every** domain class in the call chain (incl. child entities) **and the transitive closure of every entity referenced by a `Reference to …` / `List of …` Type** — each cataloged exactly once (shared infrastructure entities included, not skipped, not repeated). Each table is a **complete mirror of its source class**: one row per declared field, including audit/version/soft-delete fields and including fields no requirement references, for in-scope and externally-owned entities alike (audit/version lifecycle *semantics* referenced once from Cross-Cutting → Audit and Record Lifecycle, but the field rows still appear in every table). Every enum named as a property Type has its full value table in Domain Concepts and States. No grouped "externally-owned" prose block replaces individual property tables — every referenced entity has its own `###` sub-block regardless of module ownership. Property column uses exact Groovy camelCase field names.
- [ ] Domain Concepts and States has a table for **every** enum referenced or implied, plus a state-transition table for the primary entity.
- [ ] Extraction Summary lists controller/action-service/plugin names verbatim; the breakdown sums to the total; the `**Extraction completed:**` line carries today's date.

### Entry Point Coverage
- [ ] Step 1.5 ran (unless Auto-discover or user-restricted): siblings discovered and presented as an `AskUserQuestion` multi-select with the full-lifecycle set `(Recommended)`; the processed scope matches the user-ticked set.
- [ ] Every controller action has at least one Event-Driven statement.
- [ ] Every action service's lifecycle stages were all read (pre/execute/post/build or preCondition/execute/postCondition).
- [ ] Every Quartz job (active or disabled) is captured.
- [ ] Every Rabbit/Mercure action in scope is captured.

### Validation and Error Coverage
- [ ] Every `if`/`else if`/`case` that rejects (Message.ERROR / isError / 'error.key' / throw) has a corresponding Unwanted Behaviour statement.
- [ ] Every domain/command constraint has a corresponding field-level statement.
- [ ] Every `validator:` closure body is captured.
- [ ] Every distinct error message / `Message.ERROR` is captured.
- [ ] Optimistic-locking conflict handling is captured if present.

### Plugin / Data-Access Coverage
- [ ] Every plugin in the call chain is classified (Step 0g).
- [ ] Every business-logic action service / service in scope is fully extracted (all public methods, not just `execute`).
- [ ] Every private helper called from any public method is read recursively.
- [ ] Every injected sub-service / `*CacheService` / `PluginConnector` call is traced into its concrete implementation.
- [ ] Every action/service file > 800 lines: `wc -l` run, read in chunks to the closing brace, full method list built before extraction.
- [ ] Every raw-SQL query (`new Sql` / `executeSelectSql/Insert/Update`) is read as a first-class data source (Procedure C); datasource labelled.
- [ ] Every GORM finder/criteria/HQL filter that affects authorisation or filtering is captured.
- [ ] Every `Collections.emptyList()` / stub / commented-out logic is captured as `[DISABLED]`.
- [ ] All enums from the enum packages are catalogued in Domain Concepts and States.
- [ ] Every delegated rule-object / `validator:` closure is opened and extracted (Step A-6); no `[NEEDS REVIEW]` stands in for a locatable set.
- [ ] Every rejection whose message comes from a service/lookup/seed has that source read (Step A-7).

### Cross-Cutting Coverage
- [ ] The audit-field convention is captured as Ubiquitous statements.
- [ ] Every `beforeInterceptor` on the in-scope controllers is represented.
- [ ] Every filter closure in `SecurityFilters.groovy` (and other `*Filters.groovy`) affecting the scope is covered.
- [ ] Every annotation-gated rule (@RequiresAuthentication / @RequiresBusinessDay / @Secured) has a statement.
- [ ] Every environment/config-gated behaviour is captured as Optional.
- [ ] The database-driven FeatureAction access model is captured.

### Open Questions Audit (Rule 8 + Rule 9)
- [ ] Every `[NEEDS REVIEW]` names a *concrete* question — not "needs investigation."
- [ ] Every item has the `*Where agent looked:*` footer with at least one path and line range.
- [ ] Every item has the `*Hint for reviewer:*` footer with at least one likely path AND a grep/find/graphify command.
- [ ] No item is raised whose answer is in an enum source not opened (Step 0l), an action body not read (Step 2i), the access-control model not opened (Procedure D), or a named-but-unopened file (Step 2i).

### Output Quality
- [ ] No statement contains a class name, method name, annotation, HTTP verb, URL path, SQL fragment, table name, or any other code artefact. (File paths appear only in `> **Source files:**` annotations and Open Questions footers.)
- [ ] Every statement is self-contained.
- [ ] All ambiguities were resolved or marked `[NEEDS REVIEW]` with Rule 8 footers.
- [ ] i18n message wording is verbatim in double quotes (Rule 5).
- [ ] Domain Concepts lists every enum, value, and transition (Rule 12).
- [ ] Business Rules Summary lists every threshold, limit, and eligibility criterion (15+ for a large module).

---

## Anti-Patterns to Avoid

| ❌ Wrong | ✅ Correct |
|----------|-----------|
| `- **UB-AUD-1.** The system shall record creation timestamps.` | `The Subsidiary Ledger system shall automatically record the identity of the actor who created a record and the precise timestamp of creation whenever a new record is first persisted.` |
| `When the save action is called, the system shall…` | `When an actor submits a new subsidiary ledger for a chart of account, the Subsidiary Ledger system shall verify that the branch's business day is currently open before proceeding.` |
| `The CreateAccSubsidiaryLedgerActionService.execute() method validates…` | `When a new subsidiary ledger is submitted, if the code already exists for the chart of account, the Subsidiary Ledger system shall reject the submission.` |
| `The nullable:false constraint ensures name is provided` | `If the ledger name is not provided, the Subsidiary Ledger system shall reject the request.` |
| `The system shall call rabbitMessagingService.sendMessage()` | `The Messaging system shall send a notification to the selected recipients.` |
| `While STATUS = 'PENDING'` | `While a record is in Pending status, the <Domain> system shall permit modification by the originating branch.` |
| `BRAC ERP shall verify…` / `the GERP system shall…` | `the Subsidiary Ledger system shall verify…` (domain name, not project name) |
| `the AccProjectCoaSubledgerMappingService executes a native query` | `The Subsidiary Ledger system shall list all subledgers for the chart of account within the actor's organization.` |
| `the static transactional flag wraps the method` | `The Voucher Posting system shall atomically persist the voucher and its line entries; if any step fails, all shall be rolled back.` |
| Collapsing 6 rejection branches into one statement | Six separate paragraphs, one per branch, each with its precise condition and verbatim message. |
| Treating the controller as the whole story | Trace into the action service (IAction or ActionInterface) — that is where the business logic lives. |
| Skipping raw SQL because "it's just a query" | Raw `new Sql(...).rows(...)` / `executeSelectSql` is a first-class business-logic source (Procedure C). |
| Listing only the enum values seen in code | List every value from the enum source file with its `displayName`/`code` (Rule 12 + Step 0l). |
| Guessing an enum display name | Open the enum source; use the exact `displayName`/`code` found there. |
| Error Response Format as an HTTP-status table | The condition→message table with verbatim text and a Bengali-present flag (this app uses the Message/JSON model, not HTTP status codes). |
| Domain Concepts as bullet lists | Markdown tables with at minimum two columns (Rule 12). |
| Listing enum states but omitting scalar properties, or omitting any field the source class declares | Every entity gets a `Property \| Type \| Meaning \| Constraints` table containing one row per declared field (Rule 13). |
| Listing only the fields the traced code touched (partial entity table), or abbreviating an externally-owned entity to a few fields | Open the source class and list **every** declared field — a complete data-model mirror, audit/version and unused fields included, in-scope and externally-owned alike (Rule 13). |
| Listing a property as `Reference to Office` with no Office block, or `Enum (PaymentType)` with no value table | Every referenced entity has its own catalog block here (transitively, to closure); every named enum has its full value table in Domain Concepts and States; each entity cataloged once (Rule 13). |
| `1. **[NEEDS REVIEW]** What is the code format?` (no footer) | Item ends with `*Where agent looked:*` and `*Hint for reviewer:*` (Rule 8). |
| Naming a check method in an open question without reading it | Open the file, read the method, extract the rules (Step 2i). |
| `[NEEDS REVIEW]` for "what roles are required" | Open `SecurityFilters.groovy` + the FeatureAction seed in `dbScripts/` (Procedure D + Rule 9). |
| Silently pulling in `Approve…ActionService` — or silently shipping a spec with no approval lifecycle | Discover siblings, present them grouped by role, recommend the full set, extract exactly what the user confirms (Step 1.5). |
| Forcing all cross-cutting modules even when empty | Omit any module that doesn't meet its threshold (Rule 7). |
| Capitalised or paraphrased property name in entity table (e.g. `Country`, `Branch office`, `Assigned credit officer`) | Exact Groovy camelCase field name as declared in the source (e.g. `country`, `branchOffice`, `assignedCreditOfficer`); the `Meaning` column carries the plain-English description |
| Grouping multiple externally-owned entities into a single `### Externally-owned reference entities` prose block | Each referenced entity — regardless of which module owns it — gets its own dedicated `###` sub-block with a complete four-column property table; module ownership belongs only in the entity description sentence |

---

## Important Reminders

1. **No requirement gaps are acceptable.** If a file in the call chain exists but seems unrelated to business logic, note it briefly and explain why it produced no requirements.
2. **Overwrite** the output file on every run.
3. **Ask all ambiguity questions for an entry point before writing that entry point's section.**
4. **The domain-scoped system name is mandatory** — derive from the controller/action cluster, not the project.
5. When in doubt whether something is a business rule, **include it**.
6. **Plugins are not black boxes.** Classify first (Step 0g), then apply the matching procedure.
7. **Raw SQL and GORM queries are equal in importance** — a missed query is a missed requirement.
8. **Action services are the primary unit of business logic — the controller is thin.** Trace both action patterns.
9. **Disabled features (e.g. config-gated Quartz jobs) must not be omitted** — capture as Optional / `[DISABLED]`.
10. **i18n messages define exact wording — quote verbatim in double quotes (Rule 5); note Bengali.**
11. **Each rejection branch is a separate paragraph** — an action with 6 reject branches produces 6 paragraphs.
12. **Hardcoded approval/amount limits are business rules** — numbers appear verbatim.
13. **An action service is not done when you finish `execute()`** — read every lifecycle stage and helper.
14. **A private method called from a lifecycle stage is just as mandatory as an inline `if`** — follow every helper to its leaf.
15. **Injected sub-services and `PluginConnector`s are first-class extraction targets** — scan the whole method body for `service.method(...)` / `connector.method(...)` calls.
16. **Large files must be read in multiple chunks** — always `wc -l` first; read to the closing brace; build a complete method list before extracting.
17. **Top-level section skeleton is fixed (Rule 11); Module sections are NOT** — modules are lifecycle-derived per Rule 7.
18. **The Extraction Summary lists controller/action-service/plugin names**, not just counts.
19. **`[NEEDS REVIEW]` is the last resort.** Step 3a.0 gates are mandatory; every item carries the Rule 8 two-line footer.
20. **Discover lifecycle siblings, then confirm scope with the user (Step 1.5)** via an `AskUserQuestion` multi-select with the full set `(Recommended)`; never silently expand or hide.
21. **No Table of Contents (Rule 10).**
22. **Domain Concepts uses Markdown tables, never bullet lists (Rule 12)** — every enum value from the source appears.
23. **Enum display names come from the enum source file** — never a guess.
24. **Domain Entities and Properties catalogs every domain class with all its properties (Rule 13)** — each entity table is a **complete mirror of its source class**: one row per declared field, including audit/version/soft-delete fields and including fields no requirement references, for in-scope and externally-owned entities alike (a partial "touched fields only" table is forbidden). Reading an entity is not done until every declared field is written there AND every entity/enum it references is itself cataloged: each `Reference to …` / `List of …` entity gets its own dedicated `###` sub-block here (never merged into a grouped "externally-owned" prose block), transitively to closure; each `Enum (<Name>)` Type gets its full value table in Domain Concepts and States. Catalog each entity once (shared infrastructure entities included, never skipped, never repeated); child entities get their own sub-blocks; audit/version field rows appear in every table while their lifecycle semantics are referenced once from Cross-Cutting → Audit and Record Lifecycle. **Property column uses the exact Groovy camelCase field name** from the source (`country`, `branchOffice`, `assignedCreditOfficer`) — never a capitalised or paraphrased business name. Run the reference-closure inventory before Step 7: list every entity named as `Reference to` / `List of` across all entity tables and confirm each has a `###` block.
25. **The error model is the Grails `Message`/`buildFailureResult` JSON payload, not HTTP status codes** — build the condition→message table accordingly (decision baked into Step 0c and the output template).
