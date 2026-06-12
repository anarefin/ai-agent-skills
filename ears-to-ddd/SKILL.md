---
name: ears-to-ddd
description: >-
  Converts ANY EARS (Easy Approach to Requirements Syntax) specification from a
  layered-architecture project into a new DDD/CQRS/Event-Sourcing EARS file
  using the bits.ddd command-side patterns. The skill is domain-agnostic: it reads
  whatever concrete EARS file it is given as-is and derives the aggregate, commands,
  events, source data, validation, and status lifecycle from that input. Guides the
  user through batched architectural decisions then generates the output file. Use
  when the user says "convert EARS to DDD", "generate DDD EARS from <file>",
  "/ears-to-ddd <file>", or "map this EARS spec to DDD architecture".
disable-model-invocation: true
---

# EARS → DDD/CQRS/ES Skill

Converts a layered-architecture EARS spec into a DDD/CQRS/ES EARS spec using the
**bits.ddd** command-side patterns. Decisions are collected in batches, then a
single output `.md` file is generated.

> **Domain-agnostic contract.** This skill must work for ANY input EARS document
> (Orders, Claims, Shipments, Loans — anything). Everything in this skill and its
> supporting files is expressed with `{AggregateName}`-style placeholders and
> generic heuristics. **The input EARS file is concrete and read as-is — never
> parameterized, never modified.** The skill *extracts* the real domain (entities,
> operations, validation rules, statuses, async ops) from the concrete input and
> *fills* the placeholder templates with those extracted values. Any concrete name
> appearing in this skill is inside a block clearly labeled
> `ILLUSTRATIVE ONLY — derive real values from the input EARS`; never treat such an
> example as a default or assume the input is about that domain.

## Quick Start

1. User provides the path to the input EARS file.
2. Read the file in full.
3. Execute Phases 1–10 in order. Do **not** skip a phase. Phases whose subject is
   absent from the input (e.g. no delete op, no read/query ops, no async ops) are
   simply marked "not present in source" and produce no REQs — see each phase's gate.
4. Write the output file at `docs/{domain-name}-DDD-EARS.md` (or the path the
   user specifies) using the template in [OUTPUT-TEMPLATE.md](OUTPUT-TEMPLATE.md).

For detailed decision logic and question templates read
[PHASE-GUIDE.md](PHASE-GUIDE.md) before each phase.

---

## Architecture Anchor

This skill maps everything to the **bits.ddd command-side service pattern**
documented in `AGENTS.md` and `docs/blueprint/ARCHITECTURE-RULES.md`.
Key contracts at a glance:

| Concern | bits.ddd pattern |
|---------|-----------------|
| Aggregate | `extends AggregateRoot<String>`; `@Document` |
| Command handler | `implements CommandHandler<C>`; `@RegisterCommandHandler`; `@Service` |
| Persistence | `@PersistDomain DomainPersistenceService<A, String>` |
| Source data | `SourceDataService<SourceDataDTO>.getSourceData(entityTypeMap)` |
| Messaging | `MessageProcessor.publish(aggregate.getEvents())` |
| Query | `DomainRepository<A, String>` via `@MongoDomainRepo` |
| Failure | `{AggregateName}FailedEvent` + `{AggregateName}SourceDataValidationException` (exact names per target project convention) |
| Validation | `Specification<ValidationContext>` chain in aggregate |
| Value objects | Immutable Java `record`; `@JsonFormat` on `LocalDateTime` |
| Status | `DomainStatus` + optional domain-specific enum extension |
| Read model | Search-index projection document + projection handler on domain events |
| Soft delete | `aggregate.delete()` → domain-status inactive; minimal projection |

---

## Phase 1 — Parse EARS

Read the entire input EARS file. Extract and present three tables to the user
before asking any questions:

**Table A — Entities** — every domain noun the input names (subjects of requirements,
objects in validation rules, data structures in source citations).

**Table B — Operations** — every verb / use-case the input describes (CRUD plus any
business operations the document actually contains).

**Table C — Validation Rules** — every IF/WHEN…SHALL reject/fail clause in the input.

Also note cross-cutting concerns found — these do NOT need DDD decisions; document them
as infrastructure/presentation concerns in the output. Bucket whatever the input contains
into these generic categories (omit a category if the input has nothing for it):

- **Audit & Record Lifecycle** — create/update audit, soft delete, optimistic-lock
  version, id generation, time-zone handling.
- **Authentication & Authorisation** — token/identity requirements, device or
  human-verification checks, path-and-role access control, exempt public paths.
- **Request Handling** — request/response logging, correlation/trace id, payload-size
  limits, CORS, session policy.
- **Operational Cross-Cuts** — any pre-condition gates (e.g. open-period checks),
  distributed locks, exception logging.
- **Error Response Format** — the error payload shape and any error-condition →
  HTTP-status mapping table (copy such a table verbatim into the output).

> **ILLUSTRATIVE ONLY — derive real values from the input EARS.** A loan/KYC input might
> populate these as: proposal-number generation + Asia/Dhaka time zone (Audit); OAuth2 +
> device-id + reCAPTCHA + access-control (AuthN/AuthZ); 200 KB max-post-size (Request);
> business-day validation + scheduler lock (Operational); bilingual EN/BN payload +
> ~30-row status table (Error Format). An Orders input would populate them completely
> differently. Use the input's own content, not this example.

See [PHASE-GUIDE.md § Phase 1](PHASE-GUIDE.md) for extraction heuristics.

---

## Phase 2 — Aggregate Design (batched)

Present Table A to the user. For **each** entity ask them to assign one role:

| Role | Meaning | bits.ddd mapping |
|------|---------|-----------------|
| `AGGREGATE_ROOT` | Top-level consistency boundary; persisted independently | `extends AggregateRoot<String>`; `@Document` |
| `ENTITY` | Owned by an aggregate; has identity but no independent lifecycle | field on aggregate |
| `VALUE_OBJECT` | Immutable, no identity | Java `record` in `domain/value/` |
| `SOURCE_DATA` | Fetched from another service/collection at command time; never mutated | document + repo in infra; factory entry |

Use `AskQuestion` for each entity (or a grouped batch if the list is large).
Record decisions in a working map before continuing.

See [PHASE-GUIDE.md § Phase 2](PHASE-GUIDE.md) for heuristics on inferring
likely roles.

---

## Phase 3 — Command Design (batched)

Present Table B to the user. For each operation collect:

- **Command class name** — convention: `{Verb}{AggregateName}Command`
  (e.g. `Create{AggregateName}Command`). Comes from `com.bits.ddd.contracts.{domain}.command.*` — do NOT define locally.
- **Target aggregate root** — which aggregate this command acts on.
- **Handler class name** — `{Verb}{AggregateName}CommandHandler` in
  `application/commandhandler/`.
- **Entry points** — REST (`POST`/`PUT`/`DELETE`) and/or RabbitMQ listener.
- **HTTP method + path** — `{HTTP_METHOD} /api/{resource-path}`.

**Generate one command per operation actually present in Table B — nothing more.**
`{Verb}` is whatever verb the input uses. If the input describes a delete/remove
operation, emit `Delete{AggregateName}Command` as a **soft delete** (mark deleted,
set domain status inactive, project a minimal read record rather than physically
removing it). Emit every other `{Verb}{AggregateName}Command` **only** when the input
contains that operation. Do not assume any command exists that the input does not
describe.

> ILLUSTRATIVE ONLY — derive real operations from the input EARS. A loan input might add
> `approve`, `reject`, `disburse`, `cancel`, `settle` commands; another domain adds different
> ones, or none beyond create/update/delete.

Use `AskQuestion` to confirm or override the auto-suggested names.

---

## Phase 4 — Event Design (batched)

For each command from Phase 3, collect the domain event emitted on success.
Convention: `{AggregateName}{PastTenseVerb}Event` (e.g. `{AggregateName}CreatedEvent`,
`{AggregateName}UpdatedEvent`, and one `{AggregateName}{Operation}Event` per other command
the input has). Every command, including a soft-delete command, emits exactly one success
event consumed by the read-model projection handler.

Also confirm: all failure paths use `{AggregateName}FailedEvent`
(from `com.bits.ddd.contracts.{domain}.event.*`).

Use `AskQuestion` to confirm event names in a single batch.

---

## Phase 5 — Source Data (ask each)

For every entity marked `SOURCE_DATA` in Phase 2, ask the user:

1. **EntityType key** — the `UPPER_SNAKE_CASE` string constant used in the source-data
   map, named after the entity (e.g. `"{ENTITY_NAME}"`). Defined in local
   `application/service/EntityType.java` or the shared contracts.
2. **ID source** — does the fetch ID come from a command field (name the field)
   or is it hardcoded (give the value)?
3. **Repository name** — the `MongoRepository` that reads this entity
   (`{EntityName}Repository`).

Also ask: does this entity require a conditional fetch (only when the
corresponding command field is non-null, like the Update command pattern)?

---

## Phase 6 — Validation Mapping (ask each)

For every rule in Table C, present the rule text and ask the user to classify:

| Type | Where it lives | bits.ddd element |
|------|---------------|-----------------|
| `DOMAIN_SPECIFICATION` | Domain invariant checked on every create/update | `Specification<ValidationContext>` in `domain/specification/rules/` |
| `HANDLER_GUARD` | State/status pre-condition checked at start of aggregate method | `if (status != ...)` guard inside aggregate method |
| `PRESENTATION_VALID` | Input format / required field | `@NotNull`/`@NotBlank`/`@Valid` on request record DTO |

When the input has a **large** validation chain, group `DOMAIN_SPECIFICATION` rules
into one composite specification **per category**, not one class per rule — and derive
the categories from the input spec's own rule groupings/headings
(`{Category}Specification`). When the chain is small, one `Specification` per rule is
fine. Each composite's `validate()` runs its bundled sub-rules. Field-level
"If … reject" request rules map to `PRESENTATION_VALID`; a status pre-condition guard on
an operation maps to `HANDLER_GUARD`.

> **ILLUSTRATIVE ONLY — derive real categories from the input EARS.** A loan input with
> ~160 rules might yield categories like MemberEligibility, ProductDetailsPolicy,
> FireInsurance, etc.; an Orders input would yield entirely different categories. Use the
> input's own section headings.

See [PHASE-GUIDE.md § Phase 6](PHASE-GUIDE.md) for the decision tree and the
category-grouping mechanism.

---

## Phase 7 — Status Lifecycle (batched)

Present all status-related states found in the EARS. Ask the user:

1. Which states are standard `DomainStatus` values (`CREATED`, `UPDATED`,
   `APPROVED`, `REJECTED`)?
2. Which states are domain-specific extensions that need a local enum in
   `domain/enums/{AggregateName}Status.java`?
3. What are the valid state transitions (which commands move between which states)?

Keep the baked-in framework: standard `DomainStatus` (`CREATED`/`UPDATED`/
`APPROVED`/`REJECTED`) remains the technical bits.ddd transition marker, while
domain-specific business states found in the input go into the local
`{AggregateName}Status` enum.

> **ILLUSTRATIVE ONLY — derive real states from the input EARS.** A loan input's local
> enum might carry `PENDING`, `DISBURSED`, `AWAITING_DISBURSE`, `CLOSED`, …; another
> domain's states will differ. Populate the enum from the input's own status vocabulary.

See [PHASE-GUIDE.md § Phase 7](PHASE-GUIDE.md).

---

## Phase 8 — Query Side & Read Model (batched)

> **Gate: run this phase only if the input EARS contains retrieval / get-by-id / list /
> search operations.** If the input has no read operations, record "no read side in
> source" and skip to Phase 9.

CQRS read side. The read model is the **search-index projection** of the aggregate, kept
current by a projection handler subscribed to the domain events from Phase 4. Collect from
the user, deriving each from the input:

1. **Read-model fields** — what the projection record carries (aggregate fields plus any
   denormalised lookups the input's read operations reference).
2. **Single-get enrichment** — derived/looked-up values the input says to compute when one
   record is fetched (any computed dates, status-conditional enrichment from related
   records, attached reference-data names/flags).
3. **List/search filters** — the filter set and ordering the input's list/search
   operations specify, plus any alternate (v2) search variant.

> **ILLUSTRATIVE ONLY — derive real enrichment/filters from the input EARS.** A loan input
> might compute credit-shield/fire-insurance expiry dates, enrich Disbursed proposals from
> a loan account, and filter list results to one channel excluding certain types; other
> domains compute and filter entirely different things.

See [PHASE-GUIDE.md § Phase 8](PHASE-GUIDE.md) for the read-service pseudocode templates.

---

## Phase 9 — Async, Pipeline & Integration (batched)

> **Gate: run this phase only if the input EARS contains asynchronous side-effects,
> outbound pipeline publishing, backfill/replay, or data-integrity operations.** If absent
> from the input, record "no async/integration side in source" and skip to Phase 10.

Asynchronous side effects and outbound integrations described by the input. Collect only
the ones the input actually has:

1. **Post-write projection** — after write operations, project to the read index and/or
   publish to a downstream pipeline (async).
2. **Replay / re-publish** — any replay or re-sync operations and their batching.
3. **External-system backfill** — paging un-synced records, fetching from an external
   system, writing back, status marking, projection.
4. **Data-integrity traversal** — any paged integrity sweep that logs errors.

> **ILLUSTRATIVE ONLY — derive real async ops from the input EARS.** A loan input might
> publish to a data-sync pipeline, replay failed sends in batches of 2,000, backfill loan
> accounts from an ERP, and traverse buffer records; other domains will have different (or
> no) async operations.

See [PHASE-GUIDE.md § Phase 9](PHASE-GUIDE.md) for details.

---

## Phase 10 — Generate DDD EARS Output

Using all collected decisions, write the output file. Follow the full template
in [OUTPUT-TEMPLATE.md](OUTPUT-TEMPLATE.md).

Rules:
- Every DDD requirement traces back to at least one original `REQ-NNN` via
  `📎 Source: REQ-NNN`.
- Cross-cutting concerns from Phase 1 are preserved verbatim under
  `## Cross-Cutting Requirements` (they need no DDD transformation).
- REQ numbering in the output is independent (starts fresh: `DDD-REQ-001`).
- Group requirements by layer: Domain → Application → Presentation → Query/Read →
  Infrastructure → Async/Integration.
- **Pseudocode is mandatory** for: aggregate method bodies (all `HANDLER_GUARD` checks
  and state transitions, including `delete()`), domain specification `validate()` bodies,
  source data service `getSourceData()`, query service `fetchByIdOrHandleFailure()`, the
  read-service `getByIdEnriched()` / `search()` bodies, the replay / backfill /
  integrity-traversal bodies, and infrastructure `toModel()` + repository finder methods.
  Use Java-adjacent style — no imports, no type declarations; readable keywords only:
  `IF/THEN/ELSE/END IF`, `FOR EACH`, `RETURN`, `THROW`. Tag each block with `[PSEUDOCODE]`
  in its heading.
- Query/Read and Async/Integration REQs must also cite `📎 Source: REQ-NNN`.
- Before writing the file, perform a **traceability completeness check** spanning all
  layers (Domain → Application → Presentation → Query/Read → Infrastructure →
  Async/Integration): list every REQ-NNN from the input EARS, then confirm each appears
  in at least one `📎 Source: REQ-NNN` citation somewhere in the output. For any REQ not
  yet covered, either append it to the nearest DDD-REQ's source list or create a new
  DDD-REQ for it. Do NOT write the file until coverage is 100%.
- If a REQ cannot be mapped to any DDD layer (e.g. purely infrastructure or third-party
  concern), add it to the **Open Questions** table with `Status: UNMAPPED` and the reason.

---

## Supporting Files

- [PHASE-GUIDE.md](PHASE-GUIDE.md) — heuristics, question templates, decision
  trees for each phase.
- [OUTPUT-TEMPLATE.md](OUTPUT-TEMPLATE.md) — complete output file structure
  and per-section REQ templates.
