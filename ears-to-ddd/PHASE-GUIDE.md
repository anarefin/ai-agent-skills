# Phase Guide — EARS → DDD/CQRS/ES

Detailed decision logic, heuristics, and question templates for each phase.
Read the relevant section before executing that phase.

---

## Phase 1 — EARS Parsing Heuristics

### What to extract

**Entities (Table A)**
Scan every EARS statement for domain nouns. Include:
- Subject of a requirement (the noun the requirement is *about*)
- Objects referenced in validation rules (the nouns a rule checks)
- Data structures named in source citations

Exclude infrastructure nouns: `JWT`, `Filter`, `Logger`, `Scheduler`, `Queue`.

**Operations (Table B)**
Scan WHEN/IF clauses and REST/queue entry points for verbs:
- CRUD verbs: `Create`, `Update`, `Delete`, `Retrieve`
- Business operations: any other state-transition verb the input uses (`{Verb}`)
- Each distinct business operation becomes one row in Table B

**Validation Rules (Table C)**
Extract every EARS statement of the form:
- `If [condition], then the system shall reject / respond with error`
- `Where [pre-condition], the system shall verify`
- Guard clauses: `If already in {STATE} status … reject`

Number them V-001, V-002, … for traceability in Phase 6.

**Cross-cutting (no DDD transformation needed)**

Bucket whatever cross-cutting requirements the input contains into these generic
categories (skip any category the input does not populate):

- **Audit & Record Lifecycle** — create/update audit, soft delete, optimistic-lock
  version, id generation, time-zone handling.
- **Authentication & Authorisation** — token/identity requirements, device or
  human-verification checks, path-and-role access control, exempt public paths.
- **Request Handling** — request/response logging, correlation/trace id, payload-size
  limits, CORS, session policy.
- **Operational Cross-Cuts** — pre-condition gates, distributed locks, exception logging.
- **Error Response Format** — the error payload shape, and any error-condition →
  HTTP-status mapping table (**copy such a table verbatim** into the output — do not
  paraphrase it).

These map to filters, interceptors, `@PrePersist`/`@PreUpdate`, aspect/advice, and the
global exception handler — not to aggregates, commands, or specifications.

> **ILLUSTRATIVE ONLY — derive real values from the input EARS.** A loan/KYC input might
> populate the categories as: soft-delete + optimistic-lock + distributed id +
> business-number generation + Asia/Dhaka zone (Audit); OAuth2 bearer + device-id +
> reCAPTCHA + access-control (AuthN/AuthZ); trace id + 200 KB max-post-size + CORS +
> stateless (Request); open-business-day check + scheduler lock + async exception logging
> (Operational); bilingual EN/BN payload + a ~30-row status table (Error Format). Another
> domain populates them with entirely different requirements — always use the input's own.

---

## Phase 2 — Aggregate Design Heuristics

### How to suggest roles before asking the user

Apply these rules to form suggestions, then batch-confirm with the user:

| Signal | Suggested role |
|--------|---------------|
| Entity has a full lifecycle (created, updated, approved, rejected…) | `AGGREGATE_ROOT` |
| Entity is only referenced as a field on another entity and never persisted alone | `ENTITY` |
| Entity has no identity, is never mutated after assignment, is a data snapshot | `VALUE_OBJECT` |
| Entity is looked up from another service/collection using an ID from the command | `SOURCE_DATA` |
| Entity is a static master-data / reference record read at command time | `SOURCE_DATA` |
| Entity is a list of child items stored inside the aggregate document | `ENTITY` (embedded) |

### Example batch question format (present as a table, not individual questions)

Build the table from the entities **you extracted from the input EARS** (Table A), one row
per entity, with your suggested role and the four options. Shape:

```
I found these domain entities. Please confirm or override the suggested role for each:

| Entity                 | Suggested Role  | Options                                              |
|------------------------|-----------------|------------------------------------------------------|
| {AggregateName}        | AGGREGATE_ROOT  | AGGREGATE_ROOT / ENTITY / VALUE_OBJECT / SOURCE_DATA |
| {ValueObjectName}      | VALUE_OBJECT    | AGGREGATE_ROOT / ENTITY / VALUE_OBJECT / SOURCE_DATA |
| {EmbeddedEntityName}   | ENTITY          | AGGREGATE_ROOT / ENTITY / VALUE_OBJECT / SOURCE_DATA |
| {ReferenceDataName}    | SOURCE_DATA     | AGGREGATE_ROOT / ENTITY / VALUE_OBJECT / SOURCE_DATA |
| …                      | …               | …                                                    |
```

> **ILLUSTRATIVE ONLY — derive the real entities from the input EARS.** A loan input might
> yield: `LoanProposal` (AGGREGATE_ROOT); `ProposalInfo`/`ApprovalInfo`/`ModeOfPayment`/
> `FireInsuranceDetails` (VALUE_OBJECT); `Nominee`/`Guardian`/`CoBorrower`/`SecondInsurer`/
> `Guarantor` (ENTITY); `Member`/`LoanProduct`/`Scheme`/`Project`/`Branch`/`Office`/
> `InsuranceProduct`/`LoanAccount`/`Country`/`Bank` (SOURCE_DATA). A different input yields a
> completely different entity set — never reuse this list.

Use the `AskQuestion` tool with `allow_multiple: false` per entity, or present
the whole table as a single message and ask the user to reply with overrides.

---

## Phase 3 — Command Design Heuristics

### Naming convention

```
{Verb}{AggregateName}Command
{Verb}{AggregateName}CommandHandler
```

`{Verb}` is whatever the input's operation is named. Common CRUD verbs: `Create`, `Update`,
`Delete`. Any other state-transition verb the input uses is also a `{Verb}`.

### Auto-suggest rules

| EARS operation pattern | Suggested command | HTTP method |
|------------------------|------------------|-------------|
| "create / submit a new X" | `CreateXCommand` | `POST /api/xs` |
| "update / modify an existing X" | `UpdateXCommand` | `PUT /api/xs/{id}` |
| "delete X" (soft delete) | `DeleteXCommand` | `DELETE /api/xs/{id}` |
| "{verb} X" (any other state-transition op) | `{Verb}XCommand` | `PUT /api/xs/{id}/{verb}` |

`DeleteXCommand` (emit only if the input has a delete/remove op) is a **soft delete**: load
the aggregate, run the same status guard the input requires for modify, mark it deleted,
set its domain status to inactive, persist, and emit `XDeletedEvent` so the projection
handler removes/minimises the read record. Every row above appears in the output **only
when the input spec contains that operation** — never assume a command the input does not
describe.

> ILLUSTRATIVE ONLY — derive real operations from the input EARS. A loan input might add
> `"approve X" → ApproveXCommand → PUT …/{id}/approve`, similarly `reject`, `disburse`,
> `cancel`, `settle`. Another domain adds different verbs, or none beyond create/update/delete.

### Entry point detection

- If the EARS references a REST controller → add REST entry point
- If the EARS references a queue consumer or async notification → add RabbitMQ entry point
- Both can exist for the same command

### Handler anatomy (use as reference when generating REQs)

```java
@RegisterCommandHandler
public class CreateXCommandHandler implements CommandHandler<CreateXCommand> {
    // 1. sourceDataService.getSourceData(entityTypeMap)    — fetch snapshots
    // 2. {AggregateName}DataMapper.toCreationData(cmd, src) — assemble param object
    // 3. X.create(creationData)                            — mutate aggregate
    // 4. persistenceService.persist(x)                     — save
    // 5. messagingProcessor.publish(x.getEvents())         — publish events
}
```

For update/delete and any other load-first handler (any operation that acts on an existing
aggregate), step 0 is:
```java
// 0. queryService.fetchByIdOrHandleFailure(id, traceId) — load aggregate
```

---

## Phase 4 — Event Design Heuristics

### Naming convention

```
{AggregateName}{PastTenseVerb}Event
```

Examples (parameterized): `{AggregateName}CreatedEvent`, `{AggregateName}UpdatedEvent`,
and one past-tense event per other command the input actually has.

All failure paths share one failure event: `{AggregateName}FailedEvent`.
This is always from `com.bits.ddd.contracts.{domain}.event.*` — never define locally.

### Event mapper pattern

```java
// domain/mapper/{AggregateName}EventMapper.java
public class {AggregateName}EventMapper {
    public static {AggregateName}CreatedEvent toCreatedEvent({AggregateName} a) { ... }
    public static {AggregateName}UpdatedEvent toUpdatedEvent({AggregateName} a) { ... }
    // one toXxxEvent per command the input contains
}
```

The aggregate calls `addEvent(mapper.toXxxEvent(this))` at end of each state
transition method. Handler calls `messagingProcessor.publish(aggregate.getEvents())`.

---

## Phase 5 — Source Data Heuristics

### EntityType key conventions

Source data entities are fetched via `SourceDataService.getSourceData(Map<String,String>)`.
The map key is an `EntityType` string constant; the value is the fetch ID.

Build one key per `SOURCE_DATA` entity (from Phase 2), naming the key after the entity in
`UPPER_SNAKE_CASE` and mapping it to the command field that supplies its id:

| EntityType key | Fetch ID source |
|---------------|-----------------|
| `"{ENTITY_NAME}"` | `command.get{EntityName}Id()` |
| `"{REFERENCE_NAME}"` | hardcoded constant (for fixed reference data) |
| … | … |

> **ILLUSTRATIVE ONLY — derive real keys from the input EARS.** A loan input's keys might be
> `"MEMBER"` → `command.getMemberId()`, `"LOAN_PRODUCT"` → `command.getLoanProductId()`,
> `"BRANCH"` → `command.getBranchId()`, `"COUNTRY"` → hardcoded `"BD"`, etc. Other domains
> have entirely different keys; derive them from the SOURCE_DATA entities you found.

### Conditional fetch (Update pattern)

For update commands, only include a source entity in the map when its
corresponding command field is non-null:

```java
Map<String, String> map = new HashMap<>();
putIfNonNull(map, EntityType.{ENTITY_A}, command.get{EntityA}Id());
putIfNonNull(map, EntityType.{ENTITY_B}, command.get{EntityB}Id());
// ...
return Map.copyOf(map);
```

Ask the user: for this domain's update command, which source entities are
conditionally fetched vs. always required?

### Source data error pattern

If any fetch fails, the source data service throws:
```java
{AggregateName}FailedEvent.sourceDataError(traceId, {ErrorCode}.SOURCE_DATA_ERROR, errors)
// → wrapped in {AggregateName}SourceDataValidationException
```

---

## Phase 6 — Validation Decision Tree

For each validation rule V-NNN, ask the user to classify using this tree:

```
Is the rule about INPUT FORMAT (field required, regex, range)?
  YES → PRESENTATION_VALID (@NotNull / @NotBlank / @Pattern on request record)

Is the rule about AGGREGATE STATE (must be in status X before this operation)?
  YES → HANDLER_GUARD (if-check at start of aggregate method)

Is the rule about DOMAIN INVARIANT (business rule that applies on every
  create AND update, involving data from source snapshots)?
  YES → DOMAIN_SPECIFICATION (Specification<ValidationContext>)
```

### Group DOMAIN_SPECIFICATION rules by category when the chain is large

If the input has many domain rules, generating one `Specification` class per rule is
unmanageable. Instead, assign every `DOMAIN_SPECIFICATION` rule to **one composite category
specification**, deriving the categories from **the input spec's own rule
headings/sections**. One `{Category}Specification` per heading:

| Category specification | Bundles rules from the input section |
|------------------------|--------------------------------------|
| `{Category1}Specification` | rules under the input's "{Section heading 1}" |
| `{Category2}Specification` | rules under the input's "{Section heading 2}" |
| … | … |

Each composite's `validate()` runs its bundled sub-rules and accumulates all violations
into one error map. The aggregate `.and()`-chains the composites (see Specification
Composition in the output template). When asking the user, present the categories (not every
rule) and let them re-bucket any rule. When the input has only a handful of rules, skip the
grouping and emit one `Specification` per rule.

> **ILLUSTRATIVE ONLY — derive real categories from the input EARS.** A loan input with ~160
> rules grouped under headings like *Member Eligibility*, *Product/Details/Policy*,
> *Amount/Grant/Exposure*, *Approval-Limit*, *Co-Borrower & Insurance*, *Special-Savings*,
> *Age Limits*, *Parallel-Loan*, *Product-Type Eligibility*, *Digital-Disbursement*,
> *Migration-Country*, and *Fire-Insurance* would yield one composite per heading
> (`MemberEligibilitySpecification`, `FireInsuranceSpecification`, …). Another domain's
> headings produce entirely different composites — always use the input's own sections.

### Domain Specification anatomy

```java
// domain/specification/rules/{Category}Specification.java
public class {Category}Specification<T extends ValidationContext>
        implements Specification<T> {

    @Override
    public Map<String, LocalizedMessage> validate(T context) {
        {Category}Context ctx = ({Category}Context) context;
        Map<String, LocalizedMessage> errors = new HashMap<>();
        if (/* rule violated */) {
            errors.put(MessageKey.ENTITY.getKey(),
                LocalizedMessage.builder()
                    .key(MessageKey.RULE_FAILED.getKey())
                    .args(new String[]{ /* dynamic values */ })
                    .build());
        }
        return errors;
    }
}
```

The category composites are composed in the aggregate's static `validateX` method —
one `.and()` per category, not per rule:
```java
Specification<ValidationContext> spec =
    new {Category1}Specification<>()
        .and(new {Category2}Specification<>())
        .and(new {Category3}Specification<>())
        // … one .and() per category derived from the input
    ;
return spec.validate(context);
```

### Validation context anatomy

```java
// domain/specification/context/{AggregateName}ValidationContext.java
public record {AggregateName}ValidationContext(
    {SourceEntityA} {sourceEntityA},
    {SourceEntityB} {sourceEntityB},
    /* all source-data entities needed by any spec */ )
    implements {ContextInterfaceA}, {ContextInterfaceB}, /* other context interfaces */ {}
```

Each context interface declares the subset of source-data entities it needs.

### Handler guard pattern

```java
public void {operation}({AggregateName}{Operation}Data data) {
    if (this.status != {ALLOWED_STATE_1} && this.status != {ALLOWED_STATE_2}) {
        FailureMessage failureEvent = {AggregateName}FailedEvent.validationError(
            data.getTrace_id(),
            Map.of(MessageKey.ENTITY.getKey(),
                LocalizedMessage.builder().key(MessageKey.INVALID_STATE.getKey()).build())
        );
        throw new {AggregateName}SourceDataValidationException(failureEvent);
    }
}
```

When the input's guard is on a **business status** held in the local status enum, test the
local-enum field instead of `DomainStatus`
(`if (this.{aggregate}Status != {AggregateName}Status.{REQUIRED_STATE}) throw …`), using the
input's own rejection message.

> **ILLUSTRATIVE ONLY — derive real states/messages from the input EARS.** A loan input's
> modify/delete guard is "while the proposal is not `Pending`, reject," with messages like
> "Failed to update. It is already approved." (modify) and "Only pending loan proposal can be
> deleted. Loan proposal Status: {status}" (delete). Other domains gate on different states
> and emit different messages.

---

## Phase 7 — Status Lifecycle Heuristics

### Standard DomainStatus values (from bits.ddd)

`CREATED`, `UPDATED`, `APPROVED`, `REJECTED`

These map directly to `DomainStatus` enum from `com.bits.ddd.shared.domain.enums`.
No local enum needed for these.

### Domain-specific extensions

Any status the input uses that is not in the standard set goes into a local enum, populated
from the input's own status vocabulary:

```java
// domain/enums/{AggregateName}Status.java
public enum {AggregateName}Status {
    {STATE_1},
    {STATE_2},
    {STATE_3}
    // … one constant per business status named in the input
}
```

Note (baked-in framework, kept): the aggregate still uses `this.status` (of type
`DomainStatus` from `AggregateRoot`) as the technical bits.ddd transition marker.
Domain-specific business states live in the local enum and drive reporting, listing filters,
and any status guard.

> **ILLUSTRATIVE ONLY — derive real states from the input EARS.** A loan input's local enum
> might carry ~20 values (`PENDING`, `APPROVED`, `REJECTED`, `DISBURSED`, `AWAITING_DISBURSE`,
> `CLOSED`, `VALIDATION_FAILED`, …), with create setting the business status to `PENDING`
> while `DomainStatus` advances `CREATED → UPDATED` on edits. Other domains have different
> states entirely.

### Transition table format to confirm with user

Generic baked-in lifecycle (only the rows for commands the input contains):

```
| From State        | Command / Event   | To State         |
|-------------------|-------------------|------------------|
| (new)             | CreateXCommand    | CREATED          |
| CREATED/UPDATED   | UpdateXCommand    | UPDATED          |
| CREATED/UPDATED   | DeleteXCommand    | (soft-deleted)   |
| {ALLOWED_FROM}    | {Verb}XCommand    | {RESULT_STATE}   |   ← one row per other operation the input has
```

`{RESULT_STATE}` is a standard `DomainStatus` value (`APPROVED`/`REJECTED`) or a local
`{AggregateName}Status` value.

> **ILLUSTRATIVE ONLY — derive real transitions from the input EARS.** A loan input might add
> `CREATED/UPDATED → ApproveXCommand → APPROVED`, `CREATED/UPDATED → RejectXCommand → REJECTED`,
> `APPROVED → DisburseXCommand → DISBURSED`; and on the local business-status enum:
> `(new) → PENDING` (create), `PENDING → PENDING` (update), `PENDING → soft-deleted` (delete),
> `DISBURSED → CLOSED` (an external undo event). Build the actual table from the input's own
> state-transition section.

---

## Phase 8 — Query Side & Read Model Heuristics

> **Run only if the input EARS has retrieval / get / list / search operations.**

### Read model = search-index projection

The read model is **not** the Mongo aggregate; it is the search-index record that a
projection handler keeps current by subscribing to the Phase-4 domain events
(`Created`/`Updated`/`Deleted`/…). Reads never touch the command-side aggregate store.

### Single-get enrichment rules to capture (as read-service `getByIdEnriched` behaviour)

From the input's get/retrieve operation, capture every derived or looked-up value it says to
compute on a single fetch. Classify each as one of:

- **Computed field** — a value calculated from record fields (e.g. a date offset, a sum).
- **Status-conditional enrichment** — extra data attached only in certain states, often
  pulled from a related record.
- **Reference-data attachment** — names/flags looked up from master data using ids on the
  record.

### List/search filters

From the input's list/search operation, capture the fixed filters (always applied), the
optional filters (applied when a parameter is present), the default sort, and any alternate
(v2) search variant.

### Read-service pseudocode templates (generic shape)

```pseudocode
getByIdEnriched(key, id):
  record = searchIndex.findByKeyAndId(key, id)   // read model
  IF record is null THEN THROW notFound(id) END IF
  FOR EACH rule IN computedFieldRules DO record[rule.field] = rule.compute(record) END FOR
  FOR EACH rule IN statusConditionalRules DO
    IF rule.appliesTo(record.status) THEN rule.enrich(record) END IF
  END FOR
  FOR EACH ref IN referenceAttachments DO record.attach(ref.lookup(record)) END FOR
  RETURN record

search(filter):
  query = searchIndex.query()
            .applyFixedFilters({FIXED_FILTERS})
            .optional({OPTIONAL_FILTERS})
            .sort({DEFAULT_SORT})
  RETURN query.execute()
```

> **ILLUSTRATIVE ONLY — derive real rules from the input EARS.** A loan input's single-get
> enrichment might compute credit-shield expiry = (disbursement date or branch last business
> date) + approved months − 1 day; compute fire-insurance expiry the same way; enrich
> `DISBURSED` records from a linked loan account (realisable principal/interest, OTR%,
> overdue, outstanding); and attach term-savings/country/bank details. Its list filter might
> be "OTC-only, exclude good-loan types, default de-dupe sort, optional project/VO/member/
> product/scheme/date-range/statuses, excluding certain statuses when none specified." Other
> domains compute and filter completely different things.

---

## Phase 9 — Async, Pipeline & Integration Heuristics

> **Run only if the input EARS has async side-effects, outbound pipeline publishing,
> replay/backfill, or data-integrity operations.** Capture only the ones the input describes.

### Post-write projection

If the input says writes trigger async projection/publishing: after the relevant write
operations, project the record into the read index and/or publish it to a downstream
pipeline. A delete projects the **minimal** record (and sets domain status inactive).

### Replay / re-publish variants

Capture each replay/re-sync operation the input describes, with its selector (by id, by
parent key, by range, failed-only, …) and its batching.

### External-system backfill

If the input has a backfill: page records whose external data is not yet synchronised; for
each, async-fetch from the external system, write the data back, apply any status marking,
update the stored record, project the minimal read record, and return the count processed.

### Data-integrity traversal

If the input has an integrity sweep: page through the relevant collections and persist an
integrity error log (entity type, key, page number, error message, stack trace) whenever a
page raises an exception.

### Pseudocode template (generic shape)

```pseudocode
replayFailed():
  REPEAT
    batch = repo.findFailedSends(limit = N)
    FOR EACH r IN batch DO pipeline.publish(r) END FOR
  UNTIL batch is empty

backfillFromExternal(key, batchSize):
  count = 0
  FOR EACH page IN repo.pageUnsynced(key, batchSize) DO
    FOR EACH r IN page DO
      data = externalSystem.fetch(r) ASYNC
      r.apply(data)
      IF {STATUS_CONDITION} THEN r.status = {BACKFILLED_STATUS} END IF
      repo.update(r); searchIndex.projectMinimal(r); count = count + 1
    END FOR
  END FOR
  RETURN count
```

> **ILLUSTRATIVE ONLY — derive real async ops from the input EARS.** A loan input might
> publish to a data-sync pipeline on every write; replay by ids/branch/bulk, failed-only in
> batches of 2,000, and by updated-at range in batches of 2,000; backfill loan accounts from
> an ERP (marking digitally-disbursed ones ERP-disbursed); and traverse buffer members then
> buffer proposals logging integrity errors. Other domains have different (or no) async ops.

---

## Phase 10 — Output Generation Rules

### Step 0 — Traceability Audit (run before writing)

1. Collect all REQ-NNN identifiers from the input EARS file into a flat list.
2. Walk the draft DDD-REQ set and build a set of all cited REQ-NNNs.
3. Compute uncited = input list − cited set.
4. For each uncited REQ:
   a. If it maps to an existing DDD-REQ, append it to that REQ's source citation.
   b. If it needs a new DDD-REQ, create one now (assign the next DDD-REQ number).
   c. If it cannot be mapped (pure infra / third-party), add it to Open Questions
      with `Status: UNMAPPED` and a one-line reason.
5. Repeat until uncited set is empty. Only then proceed to write the file.

### Steps 1–7 — Writing the file

1. Read [OUTPUT-TEMPLATE.md](OUTPUT-TEMPLATE.md) in full before writing.
2. Use the DDD-REQ-NNN numbering scheme for all new requirements.
3. Every DDD requirement must cite at least one original `REQ-NNN` using
   `📎 Source: REQ-NNN` — use multiple citations when a DDD REQ consolidates
   several original REQs.
4. Cross-cutting requirements are copied verbatim from the original EARS
   (renumbered as `DDD-REQ-001` etc.) with `📎 Source: REQ-NNN`.
5. Do not invent requirements not traceable to the input EARS or to the
   mandatory bits.ddd infrastructure pattern.
6. Mandatory infrastructure REQs (that bits.ddd always requires but may not be
   explicitly in the EARS) are added and marked `[INFERRED]`.
7. Present the output file path to the user and confirm before writing.
