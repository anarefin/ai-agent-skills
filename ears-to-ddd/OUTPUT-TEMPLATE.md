# Output Template — DDD/CQRS/ES EARS Specification

Use this template to generate the output file. Replace all `{placeholders}`.
Every section heading and REQ numbering pattern must be followed exactly.
Requirements are numbered `DDD-REQ-NNN` sequentially across all sections.

---

## File Header

```markdown
# {Domain Name} — DDD/CQRS/Event-Sourcing Business Requirements Specification (EARS)

> **Format:** Easy Approach to Requirements Syntax (EARS) — DDD/CQRS/ES Edition
> **Source:** Converted from layered-architecture EARS spec `{original-file-name}`
> **Architecture:** bits.ddd command-side service (Spring Boot {version}, Java {version})
> **Aggregate:** `{AggregateName}` — MongoDB document, `{collection_name}` collection
> **Traceability:** Every DDD-REQ cites the original REQ-NNN(s) it was derived from.

---

## Document Conventions

| Marker | Meaning |
|--------|---------|
| `[INFERRED]` | Required by bits.ddd pattern; no explicit requirement in source EARS |
| `[SOURCE: REQ-NNN]` | Derived from original requirement REQ-NNN |
| `[CONSOLIDATED: REQ-NNN, REQ-MMM]` | Derived from multiple original requirements |
| `[UNCHANGED]` | Copied verbatim from the original EARS (cross-cutting concern) |
| `[PSEUDOCODE]` | Java-adjacent pseudocode block — describes behaviour without full implementation syntax |
| `[READ-MODEL]` | CQRS query-side requirement — search-index projection / read service / query endpoint |
| `[ASYNC]` | Asynchronous side effect — projection-and-publish, pipeline replay, backfill, or integrity traversal |
```

---

## Section 1 — Cross-Cutting Requirements

Copy each cross-cutting requirement from the original EARS verbatim.
Renumber as `DDD-REQ-001`, `DDD-REQ-002`, etc. Add `[UNCHANGED]` and source
citation.

```markdown
## Cross-Cutting Requirements

### DDD-REQ-001 — {Title from original REQ}

{Original requirement text, copied verbatim.}

> 📎 Source: REQ-NNN [UNCHANGED]

---

### DDD-REQ-002 — {Title from original REQ}
...
```

---

## Section 2 — Domain Layer

### 2a — Aggregate Root

```markdown
## Domain Layer

### DDD-REQ-NNN — Aggregate Root: {AggregateName}

The {Domain} system shall implement `{AggregateName}` as the aggregate root,
extending `AggregateRoot<String>` from `com.bits.ddd.domain.aggregate`. The
aggregate shall be annotated with `@Document(collection = "{collection_name}")`.
Its identity shall be a UUID string generated at creation time.

The aggregate shall own the following fields:
- `{fieldName}` — `{type}` — {description}
- ... (one bullet per aggregate field)

**Behaviour — create(creationData):** [PSEUDOCODE]

```pseudocode
create(creationData):
  id = UUID.generate()
  // populate all aggregate fields from creationData

  context = new {AggregateName}ValidationContext(creationData.{sourceEntityA}, creationData.{sourceEntityB}, ...)
  errors = validateInvariants(context)
  IF errors is not empty THEN
    failureEvent = {AggregateName}FailedEvent.validationError(creationData.traceId, errors)
    THROW {AggregateName}SourceDataValidationException(failureEvent)
  END IF

  this.status = DomainStatus.CREATED
  addEvent({AggregateName}EventMapper.toCreatedEvent(this))
  RETURN this
```

**Behaviour — update(updateData):** [PSEUDOCODE]

```pseudocode
update(updateData):
  context = new {AggregateName}ValidationContext(updateData.{sourceEntityA}, updateData.{sourceEntityB}, ...)
  errors = validateInvariants(context)
  IF errors is not empty THEN
    failureEvent = {AggregateName}FailedEvent.validationError(updateData.traceId, errors)
    THROW {AggregateName}SourceDataValidationException(failureEvent)
  END IF

  // merge non-null fields from updateData into existing aggregate fields
  this.{valueObject} = this.{valueObject}.partialUpdate(updateData.{fields})
  this.{simpleField} = updateData.{field} != null ? updateData.{field} : this.{simpleField}
  this.status = DomainStatus.UPDATED
  this.modificationAudit = new ModificationAudit(updateData.updatedBy, now())
  addEvent({AggregateName}EventMapper.toUpdatedEvent(this))
```

**Behaviour — {operation}({operationData}):** [PSEUDOCODE] — one block per additional state-transition operation the input defines

For every operation the input describes beyond create/update/delete, emit a block following
the same **guard → mutate → set status → emit event** shape:

```pseudocode
{operation}({operationData}):
  IF this.status NOT IN {ALLOWED_FROM_STATES} THEN  // HANDLER_GUARD
    THROW validationError({operationData}.traceId, {OPERATION}_FAILED, {operationData}.id)
  END IF
  // any additional precondition guards the input states for this operation
  IF {extraGuardCondition} THEN
    THROW validationError({operationData}.traceId, {GUARD_FAILED_KEY}, {operationData}.id)
  END IF

  // mutate the fields this operation changes
  this.{field} = {operationData}.{field}
  this.status = {RESULT_STATE}        // standard DomainStatus value, or a local {AggregateName}Status value
  this.modificationAudit = new ModificationAudit({operationData}.{actorField}, now())
  addEvent({AggregateName}EventMapper.to{Operation}Event(this))
```

> ILLUSTRATIVE ONLY — derive real operations from the input EARS. A loan input might define
> `approve` (guard CREATED/UPDATED; set an ApprovalInfo value object + extra "approved amount
> ≤ proposed amount" guard; status → APPROVED; emit ApprovedEvent), `reject` (guard
> CREATED/UPDATED; set a remarks field; status → REJECTED; emit RejectedEvent), and `disburse`
> (guard APPROVED; status → DISBURSED from the local enum; emit DisbursedEvent). Another domain
> defines completely different operations, or none beyond create/update/delete.

**Behaviour — delete(deletionData):** [PSEUDOCODE] (soft delete; include only if the input has a delete op)

```pseudocode
delete(deletionData):
  IF this.{businessStatus} != {REQUIRED_STATE} THEN  // HANDLER_GUARD (local-enum business status)
    THROW validationError(deletionData.traceId, DELETE_FAILED, this.{businessStatus})
    // message text comes from the input's own delete-rejection requirement
  END IF

  this.deleted = true
  this.deletionAudit = new DeletionAudit(deletionData.deletedBy, now())
  this.domainStatus = INACTIVE       // domain status inactive
  addEvent({AggregateName}EventMapper.toDeletedEvent(this))  // projection handler minimises read record
```

> 📎 Source: {REQ-NNN} [SOURCE: REQ-NNN]

---

### DDD-REQ-NNN — Value Object: {ValueObjectName}

The {Domain} system shall model `{ValueObjectName}` as an immutable Java
`record` in `domain/value/`. It shall contain the following components:
- `{fieldName}` — `{type}`
- ...

Where a `LocalDateTime` field is present, it shall be annotated with
`@JsonFormat(shape = JsonFormat.Shape.STRING)`.

{If the value object supports partial update (like ProposalInfo):}
The record shall expose a `partialUpdate(...)` method that returns a new
instance merging non-null incoming values with existing values.

> 📎 Source: {REQ-NNN}

---

### DDD-REQ-NNN — Value Object: {AnotherValueObjectName}

...same pattern...

---
```

### 2b — Status Lifecycle

```markdown
### DDD-REQ-NNN — Status Lifecycle: {AggregateName}

The {AggregateName} aggregate shall track its lifecycle through the following
states using `DomainStatus` from `com.bits.ddd.shared.domain.enums`:

| State | Trigger | Previous States |
|-------|---------|-----------------|
| `CREATED` | `{AggregateName}.create(...)` | — (initial) |
| `UPDATED` | `{AggregateName}.update(...)` | CREATED, UPDATED |
| `{RESULT_STATE}` | `{AggregateName}.{operation}(...)` | {ALLOWED_FROM_STATES} |
| … | … | … |

One row per operation the input defines. `{RESULT_STATE}` is either a standard `DomainStatus`
value (`APPROVED`/`REJECTED`) or a local `{AggregateName}Status` value.

> ILLUSTRATIVE ONLY — derive real transitions from the input EARS. A loan input might add:
> `APPROVED` via `.approve(...)` from CREATED/UPDATED; `REJECTED` via `.reject(...)` from
> CREATED/UPDATED; `DISBURSED` via `.disburse(...)` from APPROVED.

{If any domain-specific states exist:}
The system shall also define a local `{AggregateName}Status` enum in
`domain/enums/` for domain-specific states not covered by `DomainStatus`:
- `{DOMAIN_SPECIFIC_STATE}` — {description}

> 📎 Source: {REQ-NNN, REQ-NNN}

---
```

### 2c — Validation Context

```markdown
### DDD-REQ-NNN — Validation Context: {AggregateName}ValidationContext

The {Domain} system shall define a `{AggregateName}ValidationContext` record
in `domain/specification/context/` implementing the following context interfaces:
- `{ContextInterface1}` — requires `{field}: {Type}`
- `{ContextInterface2}` — requires `{field}: {Type}`, `{field}: {Type}`

The context shall be instantiated by the aggregate before running domain
specifications on every `create(...)` and `update(...)` call.

> 📎 Source: {REQ-NNN} [INFERRED]

---
```

### 2d — Domain Specifications (one **composite per validation category** from Phase 6, when the chain is large; otherwise one per rule)

Emit one block per category specification. Each composite bundles all the sub-rules the
**input** spec lists under that category (derived from the input's own section headings) and
accumulates every violation.

```markdown
### DDD-REQ-NNN — Specification: {Category}Specification

The {Domain} system shall implement `{Category}Specification` in
`domain/specification/rules/`, implementing `Specification<ValidationContext>`. It bundles
the following sub-rules from the source spec's "{Category heading}" section:

| Sub-rule | Rejection message | Source |
|----------|-------------------|--------|
| {sub-rule 1 condition} | "{message}" | REQ-NNN |
| {sub-rule 2 condition} | "{message}" | REQ-NNN |
| … | … | … |

Each violated sub-rule shall add a `LocalizedMessage` to the error map using the
appropriate message key with dynamic arguments.

**Behaviour — validate(context):** [PSEUDOCODE]

```pseudocode
validate(context):
  errors = new HashMap
  ctx = ({ContextInterface}) context

  // null-safe: missing source data is handled upstream by the source-data service
  IF ctx.{primaryEntity}() is null THEN RETURN errors END IF

  // one IF per bundled sub-rule; all violations accumulate into the same map
  IF {subRule1 condition derived from EARS text} THEN
    errors.put(MessageKey.{KEY1}.getKey(), LocalizedMessage(key = ..., args = [...]))
  END IF
  IF {subRule2 condition} THEN
    errors.put(MessageKey.{KEY2}.getKey(), LocalizedMessage(key = ..., args = [...]))
  END IF
  // … remaining sub-rules of this category …

  RETURN errors
```

> 📎 Source: {REQ-NNN, REQ-MMM, …}   (cite every sub-rule REQ folded into this composite)

---

{Repeat the block above for each category derived from the input EARS' own rule sections.}

> ILLUSTRATIVE ONLY — derive real categories from the input EARS. A loan input might yield
> `MemberEligibilitySpecification`, `ProductDetailsPolicySpecification`,
> `AmountGrantExposureSpecification`, `FireInsuranceSpecification`, etc.; another domain
> yields entirely different composites.

---

### DDD-REQ-NNN — Specification Composition

The {AggregateName} aggregate shall compose the category specifications in the
order required by the input for all `create` and `update` operations (one `.and()` per
category):

```
new {Category1}Specification<>()
    .and(new {Category2}Specification<>())
    .and(new {Category3}Specification<>())
    // … one .and() per category derived from the input
```

If the composed specification returns any errors, the aggregate shall wrap them
in `{AggregateName}FailedEvent.validationError(traceId, errors)` and throw
`{AggregateName}SourceDataValidationException`.

> 📎 Source: {REQ-NNN, REQ-NNN} [INFERRED]

---
```

### 2e — Domain Events

```markdown
### DDD-REQ-NNN — Domain Events: {AggregateName}

The {AggregateName} aggregate shall emit the following domain events via
`addEvent(...)` at the end of each successful state transition:

| State Transition | Domain Event Class |
|-----------------|-------------------|
| create → CREATED | `{AggregateName}CreatedEvent` |
| update → UPDATED | `{AggregateName}UpdatedEvent` |
| delete → (soft-deleted) | `{AggregateName}DeletedEvent` |
| {operation} → {RESULT_STATE} | `{AggregateName}{Operation}Event` |
| … | … |

One row per operation the input defines (create/update plus delete and any other
state-transition operations). All event classes are sourced from
`com.bits.ddd.contracts.{domain}.event.*` and shall NOT be defined locally. Event mapping
shall be delegated to `{AggregateName}EventMapper` in `domain/mapper/`.

> ILLUSTRATIVE ONLY — derive real events from the input EARS. A loan input might add
> `approve → APPROVED` (`ApprovedEvent`), `reject → REJECTED` (`RejectedEvent`),
> `disburse → DISBURSED` (`DisbursedEvent`).

> 📎 Source: {REQ-NNN} [INFERRED]

---

### DDD-REQ-NNN — Failure Event: {AggregateName}FailedEvent

When any domain invariant or state-guard check fails, the {AggregateName}
aggregate shall construct a `{AggregateName}FailedEvent` from
`com.bits.ddd.contracts.{domain}.event.*` and throw it wrapped inside
`{AggregateName}SourceDataValidationException` from
`com.bits.ddd.presentation.exception.domain`.

Two failure factory methods shall be used:
- `{AggregateName}FailedEvent.validationError(traceId, errors)` — for domain
  invariant failures
- `{AggregateName}FailedEvent.sourceDataError(traceId, errorCode, errors)` —
  for source-data fetch failures

> 📎 Source: {REQ-NNN} [INFERRED]

---
```

### 2f — Message Keys

```markdown
### DDD-REQ-NNN — i18n Message Keys: {AggregateName}MessageKey

The {Domain} system shall define a local `{AggregateName}MessageKey` enum in
the top-level `enums/` package. Each enum constant shall carry a `getKey()`
method returning the i18n key string used in `LocalizedMessage` instances.

Required keys:
- `{ENTITY_KEY}` — entity identifier key (the camelCase aggregate name, e.g. `"{aggregateName}"`)
- `{NOT_FOUND}` — aggregate not found by ID
- one status-guard-failure key per guarded operation the input has (`{OPERATION}_FAILED`)
- {any domain-specific validation keys identified in Phase 6}

> 📎 Source: {REQ-NNN} [INFERRED]

---
```

---

## Section 3 — Application Layer

### 3a — Parameter Objects

```markdown
## Application Layer

### DDD-REQ-NNN — Parameter Object: {AggregateName}CreationData

The {Domain} system shall define `{AggregateName}CreationData` in
`domain/param/` as a data-transfer object carrying all data needed to
construct the aggregate. It shall include:
- All command fields mapped from `{AggregateName}CreateCommand`
- All source-data snapshots mapped from `{AggregateName}SourceData`
- `trace_id` — propagated from the command for failure event construction

> 📎 Source: {REQ-NNN} [INFERRED]

---

### DDD-REQ-NNN — Parameter Object: {AggregateName}UpdateData
### DDD-REQ-NNN — Parameter Object: {AggregateName}{Operation}Data

One parameter object per command the input defines (e.g. `{AggregateName}DeletionData`, and a
`{AggregateName}{Operation}Data` for each additional operation). ...same pattern for each...

---
```

### 3b — Source Data

```markdown
### DDD-REQ-NNN — Source Data DTO: {AggregateName}SourceData

The {Domain} system shall define `{AggregateName}SourceData` in
`application/dto/` holding optional snapshots for each `SOURCE_DATA` entity.
Fields shall be nullable; the source-data service populates only the entities
included in the request map.

Fields:
{- `{entityName}` — `{DomainModel}` — populated when EntityType `"{KEY}"` is requested}

> 📎 Source: {REQ-NNN, REQ-NNN} [INFERRED]

---

### DDD-REQ-NNN — Source Data Request Map: {AggregateName}SourceDataRequest

The {Domain} system shall define `{AggregateName}SourceDataRequest` in
`application/service/` with static factory methods:

**Create command map** — always includes:
{| `EntityType.{KEY}` | `command.get{FieldName}()` |}
{| `EntityType.COUNTRY` | `"BD"` (hardcoded) |}

**Update command map** — conditionally includes (non-null fields only):
{| `EntityType.{KEY}` | `command.get{FieldName}()` — only when non-null |}

> 📎 Source: {REQ-NNN} [INFERRED]

---

### DDD-REQ-NNN — Source Data Service: {AggregateName}SourceDataService

The {Domain} system shall implement `{AggregateName}SourceDataService`
implementing `SourceDataService<{AggregateName}SourceData>` in
`application/service/`. The service shall:

1. Read `trace_id` from `MDC.get("trace_id")`, falling back to `"no-trace-id"`.
2. Fan out fetch calls concurrently using `CompletableFuture` per entity in
   the request map.
3. Delegate each fetch to `{AggregateName}SourceDataFactory`.
4. On any fetch error, collect errors and throw
   `{AggregateName}FailedEvent.sourceDataError(...)` wrapped in
   `{AggregateName}SourceDataValidationException`.
5. Be annotated with `@Observed` for Micrometer tracing.

**Behaviour — getSourceData(entityTypeIdMap):** [PSEUDOCODE]

```pseudocode
getSourceData(entityTypeIdMap):
  traceId = MDC.get("trace_id") ?? "no-trace-id"

  futures = []
  FOR EACH (entityType, id) IN entityTypeIdMap DO
    future = CompletableFuture.supplyAsync(() -> factory.fetch(entityType, id))
    futures.add(future)
  END FOR
  // Always fetch Country with hardcoded "BD" regardless of command content
  futures.add(CompletableFuture.supplyAsync(() -> factory.fetch("COUNTRY", "BD")))

  CompletableFuture.allOf(futures).join()  // wait for all

  errors = []
  FOR EACH future IN futures DO
    IF future failed THEN
      errors.add(future.cause.message)
    END IF
  END FOR

  IF errors is not empty THEN
    failureEvent = {AggregateName}FailedEvent.sourceDataError(traceId, SOURCE_DATA_ERROR, errors)
    THROW {AggregateName}SourceDataValidationException(failureEvent)
  END IF

  RETURN assembleSourceData(futures.results)  // populate {AggregateName}SourceData fields
```

> 📎 Source: {REQ-NNN} [INFERRED]

---

### DDD-REQ-NNN — Source Data Factory: {AggregateName}SourceDataFactory

The {Domain} system shall implement `{AggregateName}SourceDataFactory` in
`application/service/`. In a `@PostConstruct` method it shall register a
snapshot creator per `EntityType` key, each delegating to its corresponding
infrastructure repository. Each snapshot creator converts the repository result
using `toModel()` + `JsonUtil.convert(...)`.

> 📎 Source: {REQ-NNN} [INFERRED]

---
```

### 3c — Command Handlers (one per command)

```markdown
### DDD-REQ-NNN — Command Handler: {Verb}{AggregateName}CommandHandler

The {Domain} system shall implement `{Verb}{AggregateName}CommandHandler` in
`application/commandhandler/`, annotated `@RegisterCommandHandler @Service`,
implementing `CommandHandler<{Verb}{AggregateName}Command>`.

**Responsibilities (in order):**
{For create:}
1. Fetch source data: `sourceDataService.getSourceData(SourceDataRequest.getSourceCollectionIdMap(command))`
2. Map to param object: `{AggregateName}DataMapper.toCreationData(command, sourceData)`
3. Create aggregate: `{AggregateName}.create(creationData)`
4. Persist: `persistenceService.persist(aggregate)`
5. Publish events: `messagingProcessor.publish(aggregate.getEvents())`

{For update / delete / any other state-transition operation — prepend:}
0. Load aggregate: `queryService.fetchByIdOrHandleFailure(command.get{Id}(), traceId)`

{For delete (soft delete) — no source data fetch:}
0. Load aggregate: `queryService.fetchByIdOrHandleFailure(command.get{Id}(), traceId)`
1. Map to param object: `{AggregateName}DataMapper.toDeletionData(command)`
2. Soft-delete aggregate: `aggregate.delete(deletionData)`  // status guard inside
3. Persist: `persistenceService.persist(aggregate)`
4. Publish events: `messagingProcessor.publish(aggregate.getEvents())`

**Injected dependencies:**
- `@PersistDomain DomainPersistenceService<{AggregateName}, String>`
- `SourceDataService<{AggregateName}SourceData>` (create/update only)
- `MessageProcessor`
- `{AggregateName}QueryService` (any load-first handler: update/delete/other operations)

> 📎 Source: {REQ-NNN}

---
```

### 3d — Query Service

```markdown
### DDD-REQ-NNN — Query Service: {AggregateName}QueryService

The {Domain} system shall implement `{AggregateName}QueryService` in
`application/service/`. It shall inject `DomainRepository<{AggregateName}, String>`
via `@MongoDomainRepo`.

The `fetchByIdOrHandleFailure(String id, String traceId)` method (annotated
`@Observed`) shall return the aggregate or throw
`{AggregateName}SourceDataValidationException` with a `{AggregateName}FailedEvent`
payload containing the localized not-found message.

**Behaviour — fetchByIdOrHandleFailure(id, traceId):** [PSEUDOCODE]

```pseudocode
fetchByIdOrHandleFailure(id, traceId):
  result = domainRepository.findById(id)  // Optional<{AggregateName}>

  IF result is empty THEN
    errors = Map.of(MessageKey.{ENTITY}.getKey(),
                    LocalizedMessage(key  = MessageKey.NOT_FOUND.getKey(),
                                     args = [id]))
    failureEvent = {AggregateName}FailedEvent.validationError(traceId, errors)
    THROW {AggregateName}SourceDataValidationException(failureEvent)
  END IF

  RETURN result.value
```

> 📎 Source: {REQ-NNN} [INFERRED]

---
```

### 3e — Application Mappers

```markdown
### DDD-REQ-NNN — Data Mapper: {AggregateName}DataMapper

The {Domain} system shall implement `{AggregateName}DataMapper` in
`application/mapper/` as a static utility class. It shall provide:
- `toCreationData(command, sourceData)` → `{AggregateName}CreationData`
- `toUpdateData(command, sourceData, existingAggregate)` → `{AggregateName}UpdateData`
- `toDeletionData(command)` → `{AggregateName}DeletionData` {if the input has a delete op}
- `to{Operation}Data(command)` → `{AggregateName}{Operation}Data` {one per other operation the input has}

> 📎 Source: {REQ-NNN} [INFERRED]

---

### DDD-REQ-NNN — Command Mapper: {AggregateName}CommandMapper

The {Domain} system shall implement `{AggregateName}CommandMapper` in
`application/mapper/` as a static utility class. It shall map each HTTP
request DTO to its corresponding command object:
- `toCreateCommand(traceId, CreateRequest)` → `Create{AggregateName}Command`
- `toUpdateCommand(traceId, id, UpdateRequest)` → `Update{AggregateName}Command`
- `toDeleteCommand(traceId, id)` → `Delete{AggregateName}Command` {if the input has a delete op}
- `to{Operation}Command(traceId, id, {Operation}Request)` → `{Operation}{AggregateName}Command` {one per other operation the input has}

> 📎 Source: {REQ-NNN} [INFERRED]

---
```

---

## Section 4 — Presentation Layer

```markdown
## Presentation Layer

### DDD-REQ-NNN — Request DTO: Create{AggregateName}Request

The {Domain} system shall define `Create{AggregateName}Request` as an
immutable Java `record` in `presentation/controller/dto/`.

Fields with `@NotNull` / `@NotBlank` constraints derived from Phase 6
`PRESENTATION_VALID` rules:
- `{fieldName}` — `{type}` — {validation annotation} — {source REQ}
- ...

> 📎 Source: {REQ-NNN}

---

### DDD-REQ-NNN — Request DTO: Update{AggregateName}Request
### DDD-REQ-NNN — Request DTO: {Operation}{AggregateName}Request

One request DTO per command the input defines. ...same pattern for each...

---

### DDD-REQ-NNN — REST Controller: {AggregateName}CommandController

The {Domain} system shall implement `{AggregateName}CommandController` in
`presentation/controller/`, extending `BaseApiController`. It shall inject
only `CommandBus`.

For each command endpoint the controller shall:
1. Read `trace_id` from `@RequestAttribute(MdcConstants.TRACE_ID)`.
2. Call `MDC.put("trace_id", trace_id)`.
3. Map the request to a command via `{AggregateName}CommandMapper`.
4. Dispatch via `commandBus.handle(command)`.
5. Return `ResponseEntity<ApiResponse>` with `HttpStatus.ACCEPTED` (202).

Endpoints:

| Method | Path | Command |
|--------|------|---------|
| POST | `/api/{resource-path}` | `Create{AggregateName}Command` |
| PUT | `/api/{resource-path}/{id}` | `Update{AggregateName}Command` |
| DELETE | `/api/{resource-path}/{id}` | `Delete{AggregateName}Command` (soft delete) — if the input has a delete op |
| {HTTP_METHOD} | `/api/{resource-path}/{id}/{operation}` | `{Operation}{AggregateName}Command` — one per other operation the input has |

One endpoint per command in the input. Where an operation takes a single scalar argument the
input may pass it as a `@RequestParam` rather than a request body.

> ILLUSTRATIVE ONLY — derive real endpoints from the input EARS. A loan input might add
> `PUT …/{id}/approve`, `PUT …/{id}/reject` (reason as `@RequestParam`), and
> `PUT …/{id}/disburse`.

> 📎 Source: {REQ-NNN, REQ-NNN}

---

### DDD-REQ-NNN — RabbitMQ Listener: {AggregateName}CommandListener

{Include only if the original EARS has queue-triggered operations.}

The {Domain} system shall implement `{AggregateName}CommandListener` in
`presentation/listener/`. For each queue-driven command it shall:
1. Annotate the handler method with `@RabbitListener(queues = RabbitMQConstants.{QUEUE})`.
2. Deserialize the message body: `JsonUtil.deserialize(message.getBody(), {Verb}{AggregateName}Command.class)`.
3. Dispatch: `commandBus.handle(command)`.

Exceptions shall NOT be caught here; RabbitMQ retry handles failures.

> 📎 Source: {REQ-NNN}

---
```

---

## Section 4.5 — Query / Read Model

CQRS read side. **Include this section only if the input EARS has retrieval / get / list /
search operations.** Emit these REQs after the Presentation layer.

```markdown
## Query / Read Model

### DDD-REQ-NNN — Read Model Projection: {AggregateName}SearchProjection [READ-MODEL]

The {Domain} system shall maintain a `{AggregateName}SearchProjection` in the full-text
search index as the read model. A projection handler (`{AggregateName}ProjectionHandler`)
shall subscribe to the domain events from the Domain layer and keep the projection current:

| Domain Event | Projection action |
|--------------|-------------------|
| `{AggregateName}CreatedEvent` | upsert full record into the index |
| `{AggregateName}UpdatedEvent` | upsert updated record into the index |
| `{AggregateName}DeletedEvent` | project the minimal record (mark inactive/removed) |
| `{AggregateName}{Operation}Event` | upsert status change (one row per other operation the input has) |

The handler shall also publish each event onto the data-synchronisation pipeline (see
Async section). Reads never query the command-side aggregate store.

> 📎 Source: {REQ-NNN} [READ-MODEL]

---

### DDD-REQ-NNN — Query Service: {AggregateName}ReadService [READ-MODEL]

The {Domain} system shall implement `{AggregateName}ReadService` in `application/query/`.
It shall read from the search index and enrich results. Methods:
- `getByIdEnriched(key, id)` — fetch one projection and apply the input's enrichment rules.
- `search(filter)` — filtered list/search over the index.

**Behaviour — getByIdEnriched(key, id):** [PSEUDOCODE]

```pseudocode
getByIdEnriched(key, id):
  record = searchIndex.findByKeyAndId(key, id)
  IF record is null THEN THROW notFound(id) END IF

  // one line per COMPUTED FIELD rule the input defines on a single fetch
  FOR EACH rule IN computedFieldRules DO record[rule.field] = rule.compute(record) END FOR
  // one block per STATUS-CONDITIONAL enrichment the input defines
  FOR EACH rule IN statusConditionalRules DO
    IF rule.appliesTo(record.status) THEN rule.enrich(record) END IF
  END FOR
  // one line per REFERENCE-DATA attachment the input defines
  FOR EACH ref IN referenceAttachments DO record.attach(ref.lookup(record)) END FOR
  RETURN record
```

**Behaviour — search(filter):** [PSEUDOCODE]

```pseudocode
search(filter):
  query = searchIndex.query()
            .applyFixedFilters({FIXED_FILTERS})          // always-on filters from the input
            .optional({OPTIONAL_FILTERS})                // applied when the parameter is present
  IF filter.{primaryFilter} is empty THEN
    query.exclude({DEFAULT_EXCLUDED})                    // input's default exclusions
  END IF
  RETURN query.sort({DEFAULT_SORT}).execute()
  // emit an alternate (v2) variant only if the input defines one
```

> ILLUSTRATIVE ONLY — derive real enrichment/filters from the input EARS. A loan input might
> compute credit-shield expiry = (disbursement date or branch last business date) + approved
> months − 1 day; enrich `DISBURSED` records from a loan account; attach term-savings/country/
> bank details; and filter "OTC-only, exclude good-loan types, default de-dupe sort." Other
> domains compute and filter completely different things.

> 📎 Source: {REQ-NNN} [READ-MODEL]

---

### DDD-REQ-NNN — Query Controller: {AggregateName}QueryController [READ-MODEL]

The {Domain} system shall implement `{AggregateName}QueryController` in
`presentation/controller/`, exposing one read endpoint per read operation in the input,
each delegating to `{AggregateName}ReadService`:

| Method | Path | Operation |
|--------|------|-----------|
| GET | `/api/{resource-path}/{key}/{id}` | single enriched record |
| GET | `/api/{resource-path}/{key}` | filtered list/search |
| GET | `/api/{resource-path}/{...}` | any additional read/lookup the input defines |

> 📎 Source: {REQ-NNN} [READ-MODEL]

---
```

---

## Section 5 — Infrastructure Layer

### 5a — MongoDB Documents

```markdown
## Infrastructure Layer

### DDD-REQ-NNN — MongoDB Document: {EntityName}Document

The {Domain} system shall define `{EntityName}Document` in
`infrastructure/persistence/document/`, annotated `@Document(collection = "{collection}")`.

It shall expose a `toModel()` method returning the shared domain model class
`{EntityName}` via `JsonUtil.convert(this, {EntityName}.class)`.

Fields shall use `@Field` with snake_case names where they differ from the
Java field name.

**Behaviour — toModel():** [PSEUDOCODE]

```pseudocode
toModel():
  // @Field annotations map snake_case Mongo field names to Java camelCase fields
  // JsonUtil.convert uses Jackson ObjectMapper internally
  RETURN JsonUtil.convert(this, {EntityName}.class)
  // Result: shared domain model used by specifications, aggregate, and data mapper
```

> 📎 Source: {REQ-NNN} [INFERRED]

---
```

One `DDD-REQ-NNN` per `SOURCE_DATA` entity identified in Phase 5.

### 5b — Repositories

```markdown
### DDD-REQ-NNN — Repository: {EntityName}Repository

The {Domain} system shall define `{EntityName}Repository` in
`infrastructure/persistence/repository/` extending
`MongoRepository<{EntityName}Document, String>`.

{Custom finder methods required by the source-data factory:}
- `{Optional<EntityNameDocument> findBy{Field}And{Condition}(...)}`

**Behaviour — repository query derivation:** [PSEUDOCODE]

```pseudocode
// Spring Data MongoDB derives queries from method names at startup

findById(id):
  RETURN db.{collection}.findOne({ _id: id })
  // Built-in from MongoRepository; returns Optional.empty() if not found

findBy{Field}(value):
  RETURN db.{collection}.findOne({ {field}: value })
  // Returns Optional<{EntityName}Document>

findBy{Field}And{Condition}(value, conditionValue):
  RETURN db.{collection}.findOne({ {field}: value, {condition}: conditionValue })
  // e.g. findByIdAndIsActiveTrue(id) → { _id: id, isActive: true }

findAll{EntityName}By{Field}(value):
  RETURN db.{collection}.find({ {field}: value })
  // Returns List<{EntityName}Document>; e.g. findAllBy{Field}(value)
```

> 📎 Source: {REQ-NNN} [INFERRED]

---
```

### 5c — Persistence Configuration

```markdown
### DDD-REQ-NNN — Persistence Configuration: {AggregateName}PersistenceConfig [INFERRED]

The {Domain} system shall define `{AggregateName}PersistenceConfig` in
`application/config/`. It shall declare a `@Primary @Bean` of type
`DomainPersistenceService<{AggregateName}, String>` using
`DefaultDomainPersistenceService`, providing the MongoDB collection name for
the aggregate.

This bean coexists with the `@PersistDomain`-annotated field on each handler.

> 📎 [INFERRED] — required by bits.ddd persistence wiring

---
```

### 5d — Messaging Configuration

```markdown
### DDD-REQ-NNN — Queue Configuration: {AggregateName}QueueConfig

The {Domain} system shall define `{AggregateName}QueueConfig` in
`infrastructure/messaging/config/`, declaring:

**Exchanges:**
- `{aggregate-name}.command.exchange` — topic exchange for inbound commands
- `{aggregate-name}.event.exchange` — fanout exchange for outbound domain events

**Queues (per event type):**
- `{aggregate-name}.created.queue` → bound to event exchange
- `{aggregate-name}.updated.queue` → bound to event exchange
- `{aggregate-name}.deleted.queue` → bound to event exchange
- `{aggregate-name}.failed.queue` → bound to event exchange
- `{aggregate-name}.{operation}.queue` → one per other operation the input defines
- Dead-letter queue per command queue

**RabbitMQRouteRegistry:** shall register routing keys for each domain event class.

> 📎 Source: {REQ-NNN} [INFERRED]

---
```

### 5e — Application Bootstrap

```markdown
### DDD-REQ-NNN — Bootstrap: {AggregateName}CommandApplication [INFERRED]

The {Domain} system shall define a `{AggregateName}CommandApplication` class
annotated `@SpringBootApplication`. The annotation-processor-driven bean
discovery shall ensure `@RegisterCommandHandler`, `@PersistDomain`, and
`@MongoDomainRepo` annotations are processed without requiring explicit
`scanBasePackages`.

> 📎 [INFERRED]

---
```

---

## Section 5.5 — Async, Pipeline & Integration

**Include this section only if the input EARS has async side-effects, outbound pipeline
publishing, replay/backfill, or data-integrity operations.** Emit only the REQs whose
operation the input actually describes, after the Infrastructure layer.

```markdown
## Async, Pipeline & Integration

### DDD-REQ-NNN — Projection-and-Publish on domain events [ASYNC]

After the write operations the input designates, the {Domain} system shall asynchronously
project the record into the read index and/or publish it onto the downstream pipeline. A
delete path shall project the **minimal** record.

> 📎 Source: {REQ-NNN} [ASYNC]

---

### DDD-REQ-NNN — Replay Service: {AggregateName}ReplayService [ASYNC]

The {Domain} system shall implement `{AggregateName}ReplayService` supporting one operation
per replay/re-sync variant the input defines, each with its selector and batching:

| Operation | Behaviour |
|-----------|-----------|
| {replay variant 1} | {selector + publish behaviour from the input} |
| {replay variant 2 — failed-only} | async, batches of N, re-publish previously-failed sends until none remain |
| {replay variant 3 — by range} | async, batches of N ordered by id, optional filters, until none remain |

**Behaviour — replayFailed():** [PSEUDOCODE]

```pseudocode
replayFailed():
  REPEAT
    batch = repo.findFailedSends(limit = N)
    FOR EACH r IN batch DO pipeline.publish(r) END FOR
  UNTIL batch is empty
```

> 📎 Source: {REQ-NNN} [ASYNC]

---

### DDD-REQ-NNN — External-System Backfill: {AggregateName}BackfillService [ASYNC]

The {Domain} system shall page records whose external data is not yet synchronised and, for
each, asynchronously retrieve the data from the external system, write it back, apply any
status marking the input requires, update the stored record, project the minimal read
record, and return the total processed.

**Behaviour — backfillFromExternal(key, batchSize):** [PSEUDOCODE]

```pseudocode
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

> 📎 Source: {REQ-NNN} [ASYNC]

---

### DDD-REQ-NNN — Data-Integrity Traversal: {AggregateName}IntegrityTraversalService [ASYNC]

The {Domain} system shall page through the collections the input names, persisting a
data-integrity error log (entity type, key, page number, error message, stack trace)
whenever a page raises an exception.

> 📎 Source: {REQ-NNN} [ASYNC]

---
```

> ILLUSTRATIVE ONLY — derive real async ops from the input EARS. A loan input might project to
> a search index and publish to a data-sync pipeline on every write; replay by ids/branch/bulk,
> failed-only in batches of 2,000, and by updated-at range; backfill loan accounts from an ERP
> (marking digitally-disbursed records ERP-disbursed); and traverse buffer members then buffer
> proposals logging integrity errors. Other domains have different (or no) async operations.

---

## Section 6 — Open Questions

```markdown
## Open Questions

List any requirements from the source EARS that could not be mapped to DDD
patterns, are ambiguous, or require domain expert clarification.

| ID | Source REQ | Question | Status |
|----|-----------|----------|--------|
| Q-1 | REQ-NNN | {Question text} | OPEN |
```

---

## Full File Skeleton

The generated output file shall have this top-level structure:

```markdown
# {Domain} — DDD/CQRS/ES EARS Specification

> [header block]

---

## Document Conventions
[conventions table]

---

## Cross-Cutting Requirements
[DDD-REQ-001 … DDD-REQ-NNN — unchanged cross-cutting REQs]

---

## Domain Layer
[DDD-REQ-NNN — Aggregate Root (create/update + delete and any other operations the input defines)]
[DDD-REQ-NNN — Value Object(s)]
[DDD-REQ-NNN — Status Lifecycle]
[DDD-REQ-NNN — Validation Context]
[DDD-REQ-NNN — Specification(s) — one composite per validation category]
[DDD-REQ-NNN — Specification Composition]
[DDD-REQ-NNN — Domain Events (incl. DeletedEvent)]
[DDD-REQ-NNN — Failure Event]
[DDD-REQ-NNN — Message Keys]

---

## Application Layer
[DDD-REQ-NNN — Parameter Objects (incl. DeletionData)]
[DDD-REQ-NNN — Source Data DTO]
[DDD-REQ-NNN — Source Data Request Map]
[DDD-REQ-NNN — Source Data Service]
[DDD-REQ-NNN — Source Data Factory]
[DDD-REQ-NNN — Command Handler(s) (incl. Delete handler)]
[DDD-REQ-NNN — Query Service (fetchByIdOrHandleFailure)]
[DDD-REQ-NNN — Data Mapper]
[DDD-REQ-NNN — Command Mapper]

---

## Presentation Layer
[DDD-REQ-NNN — Request DTO(s)]
[DDD-REQ-NNN — REST Controller (incl. DELETE endpoint)]
[DDD-REQ-NNN — RabbitMQ Listener (if applicable)]

---

## Query / Read Model
[DDD-REQ-NNN — Read Model Projection + Projection Handler]
[DDD-REQ-NNN — Read Service (getByIdEnriched, search)]
[DDD-REQ-NNN — Query Controller]

---

## Infrastructure Layer
[DDD-REQ-NNN — MongoDB Document(s)]
[DDD-REQ-NNN — Repository(ies)]
[DDD-REQ-NNN — Persistence Configuration]
[DDD-REQ-NNN — Queue Configuration]
[DDD-REQ-NNN — Application Bootstrap]

---

## Async, Pipeline & Integration
[DDD-REQ-NNN — Projection-and-Publish on domain events]
[DDD-REQ-NNN — Replay Service]
[DDD-REQ-NNN — External-System Backfill]
[DDD-REQ-NNN — Data-Integrity Traversal]

---

## Open Questions
[table]
```
