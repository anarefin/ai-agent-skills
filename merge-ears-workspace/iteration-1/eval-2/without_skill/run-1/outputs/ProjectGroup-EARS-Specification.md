# Project & Group Management — Business Requirements Specification (EARS)

> **Format:** Easy Approach to Requirements Syntax (EARS)
> **Source:** Reverse-engineered from existing codebase — SBICloud BD (BRAC ERP), Grails 2.5.x, base packages `com.docu.*` (legacy) and `com.bits.gerp.*` (current)
> **Source Entry Point(s) — Project system:** `plugins/applicationCommon/grails-app/controllers/com/docu/project/ProjectController.groovy` and all `CreateProjectAction`, `UpdateProjectAction`, `ShowProjectAction`, `EditProjectAction`, `ListProjectAction`, `AjaxProjectAction`, `ShowOfficeMappingAction`, `UpdateProjectOfficeMappingAction`, `ShowProjectMappingAction`, `UpdateOfficeWiseProjectMappingAction`, `CreateBulkProjectMappingAction` action classes under `plugins/applicationCommon/src/groovy/com/docu/project/action/`.
> **Source Entry Point(s) — Group Management system:** `plugins/mf/grails-app/controllers/com/docu/sbicloud/program/group/GroupInfoController.groovy` and all `CreateGroupInfoAction`, `UpdateGroupInfoAction`, `DeleteGroupInfoAction`, `ShowGroupInfoAction`, `EditGroupInfoAction`, `ListGroupInfoAction`, `AjaxGroupInfoAction`, `ChangeCollectionStartDateAction` action classes under `plugins/mf/src/groovy/com/docu/sbicloud/program/groupinfo/action/`.
> **System names used in statements:** "the Project system" (project domain) · "the Group Management system" (microfinance group domain)
> **Purpose:** Standalone, architecture-neutral specification for system regeneration — lossless merge of the two original EARS specs.
> **Note:** All requirements are expressed in plain business language with no code references in the statement text. A *group* is presented to end users as a *Village Organization (VO)*; the two terms are interchangeable in the group domain, and user-facing messages use the word "VO". Each module and content subsection is annotated with a `> **Source files:**` line listing the source files it was extracted from.

---

## Document Conventions

| Marker | Meaning |
|--------|---------|
| `[NEEDS REVIEW]` | Ambiguous logic — verify with domain expert before use |
| `[UNRESOLVED: X]` | Referenced component X could not be fully located in the codebase |
| `[INFERRED]` | Behaviour inferred from standard framework convention; no explicit code found |
| `[DISABLED]` | Feature exists in the codebase but is currently switched off |
| `[TEST-HINT]` | Rule surfaced from a Spock spec and confirmed against production code |
| `Review by Developer` | Four sections at the end of this file where a developer records findings (two per source spec) |

---

## System Overview

### Project System

The Project system manages the master data of operational projects for a multi-country microfinance and development organisation, together with the way each project is deployed across the office network. A project belongs to exactly one program and one country, carries setup, effective, start and end dates, financial commitment amounts in local and foreign currency, and a collection of operational flags that mark whether it runs microfinance, finance, smart-collection, Trendx or NGO-bureau activity. The system supports creating, updating, viewing and listing projects; mapping a project to many field offices (project-wise office mapping); mapping many projects to a single office (office-wise project mapping); and importing project-office mappings in bulk from a spreadsheet. It spans a single application module that holds the shared project data model, and it integrates with the human-resource domain by forwarding each saved project to two downstream services. Validation is layered: field-level constraints on the project and mapping records, action-level checks for duplicate project name, code and reference code, presence of a program, and per-office-code and per-group-category checks during bulk import. Project and mapping data is served largely from an in-memory cache that is refreshed after every change, and reference lists for grids, trees, division/office pickers and reports are produced by direct database queries. Every change records who made it and when, and a soft status flag (active or inactive) governs whether a record participates in lists and counts.

### Group Management System

The Group Management system maintains the lifecycle of microfinance groups — known operationally as Village Organizations (VOs) — within a branch office and a microfinance project. It covers the full set of operations exposed by a single operator-facing screen cluster: creating a new group, editing and updating an existing group, soft-deleting a group, viewing and listing groups, and separately changing a group's loan and savings collection start dates. A group binds together a branch office, a project, an assigned project officer, a meeting day and time, a loan collection plan and a savings collection plan, an applicable member gender, and an optional service territory and VO category. The system enforces several layers of validation: field-level constraints on the group record itself, action-level business rules (date gates against the branch business day, collection-frequency minimum gaps, meeting-day-must-be-a-working-day checks, alignment of collection days and frequencies, and uniqueness of the reserved "Wash" VO name within a project), member-aware guards that prevent gender or status changes while active members exist, and database-driven feature-and-role access control. The system spans primarily the microfinance plugin and depends on shared infrastructure (authentication, business-day state from the accounting domain, office and project reference data, code/sequence generation, and file storage for scanned survey forms). Every persisted change is audited with the acting user and timestamp and is guarded by optimistic locking. Group records are never physically deleted — deletion marks a group inactive only when it holds no active or expired members.

### Relationship Between the Two Systems

A group belongs to exactly one project (the `projectInfo` reference on the group record). A project must have a defined policy before any group can be created or updated against it. Groups are mapped to a branch office, which in turn participates in the project-office mapping maintained by the Project system. The Project system owns the canonical project and project-office-mapping records; the Group Management system reads project and office data as reference data and enforces project-policy presence as a guard.

---

## Cross-Cutting Requirements

### Audit and Record Lifecycle

> **Applies to:** both systems

The Project system shall record the identity of the actor who created a record and the timestamp of creation whenever a new project, project-change-log entry, or project-office mapping is first persisted.

The Project system shall record the identity of the actor who last modified a record and the timestamp of the modification whenever an existing project or project-office mapping is updated.

The Project system shall maintain an optimistic-locking version on each persisted record so that concurrent modifications to the same record are detected.

The Project system shall treat the active/inactive status flag carried by each project and each project-office mapping as a soft-status marker, and shall default a newly created project and a newly created mapping to active status.

Whenever a project is created or updated, the Project system shall also write a point-in-time copy of the project's prior values into a project-change-log record for historical tracking.

The Group Management system shall record, on every newly created group and related history record, the identity of the acting user as the creator and the system timestamp as the creation time.

The Group Management system shall record, on every update to a group or related record, the identity of the acting user as the last updater and the system timestamp as the last-updated time.

The Group Management system shall maintain a record version on each group and increment it on every persisted change, and shall reject a save whose version no longer matches the stored version so that a concurrent update by another user is not silently overwritten; the corresponding user-facing condition is "Another user has updated this VO Information while you were editing".

The Group Management system shall treat group deletion as a soft deletion: it shall set the group's data status to inactive and never physically remove the group record.

The Group Management system shall, when reading a group for editing, viewing, updating, or deletion, consider only groups whose data status is active.

### Authentication and Authorisation

> **Applies to:** both systems

Where authentication is required, the Project system shall reject any request to any project operation that does not originate from an authenticated session, before any project business logic executes.

The Project system shall bind every project operation to the shared application-common functional area so that request-time authorisation is evaluated against that area.

The Project system shall enforce database-driven feature-and-action access rules. If an authenticated actor attempts a project operation without the required feature-action permission, the Project system shall reject the request before any business logic is executed.

While building the program-and-project selection tree, where the actor's office is not a top-level institutional, country head, or head office, the Project system shall restrict the visible programs to those for which the actor's session holds authorised projects.

While building the program-and-project selection tree, where the actor's office is not a top-level institutional or country head office, the Project system shall restrict the visible projects to those present in the actor's authorised project list.

Where an operation is invoked, the Group Management system shall require the requester to hold an authenticated session and shall redirect an unauthenticated requester to the login flow before any group operation is processed.

Where a group creation, edit, save, or update operation is invoked, the Group Management system shall require the requesting branch's business day to be open and shall reject the operation with a business-day-must-be-opened indication when the branch business day is not open.

The Group Management system shall enforce database-driven feature-and-action access rules; if an authenticated requester's assigned role does not hold permission for the requested group feature action, the Group Management system shall reject the request before any business logic is executed.

While a requester is an internal user, when the requester views or edits a group, the Group Management system shall permit the operation only when the group's project is within the requester's authorised project set and either the requester has no office restriction or the group's branch is within the requester's authorised office set, except that a requester holding the microfinance programme administrator role or the finance programme administrator role shall be permitted regardless of project or office restriction.

While a requester is an external user, the Group Management system shall not apply project-or-office scoping to viewing or editing a group.

If a requester attempts to view or edit a group outside the requester's authorised project or office scope, the Group Management system shall reject the request with the message "You do not have authority to view this page. For further information please contact with you system administrator."

While editing a group, the Group Management system shall permit changing the service territory only when the requester holds the microfinance programme administrator role or the finance programme administrator role.

While a requester is an internal user, when the requester opens the create-group screen, the Group Management system shall offer only the group-association projects the requester is authorised for; otherwise it shall offer all group-association projects.

### Request Handling

> **Applies to:** both systems

The Project system shall accept the submission of a new project, the update of an existing project, the update of a project-wise office mapping, the update of an office-wise project mapping, and the bulk import of project-office mappings only when the request is sent as a form submission; any other transport method for these operations shall be rejected.

While serving a project detail tab over an asynchronous request, if the originating session is not valid, the Project system shall return an access-error indicator and store the access message for later display rather than rendering the requested tab.

The Project system shall associate each incoming project request with the current actor's working office and country drawn from the session, so that downstream lookups and code generation are scoped to that office and country.

The Group Management system shall accept the save-group and update-group operations only via an HTTP POST submission and the main group listing only via an HTTP GET request, and shall reject other request methods.

The Group Management system shall reject an asynchronous (AJAX) request that carries no authenticated session, unless the requested action is on the permitted-without-session list.

The Group Management system shall bind every group operation to the microfinance plugin context for the duration of request processing.

### Operational Cross-Cuts

After a project is created or updated, the Project system shall refresh the cached project data so that subsequent reads reflect the change.

After a project is created or updated, the Project system shall evict the cached accounting project-setup list and the cached collection-application project lists so that dependent areas rebuild them on next use.

After a project-office mapping or office-wise project mapping is saved, the Project system shall refresh the cached project-office mapping data.

When an administrator explicitly requests a project-office cache refresh, the Project system shall rebuild the project-office mapping, project, and physical-office caches and report whether the refresh succeeded or failed.

Whenever a database operation fails during persistence of a project or mapping, the Project system shall log the underlying error and surface a generic database-operation failure message rather than the raw technical error.

The Group Management system shall execute each group creation, update, deletion, and collection-start-date change as a single atomic unit of work, persisting the group record together with its dependent records (project-officer reassignment history, member reassignments, and loan-schedule adjustments) such that if any step fails the entire change is rolled back.

The Group Management system shall, on the main group listing screen, present country and branch selection only when the requester's office is the central head office or the global head office, and shall present office selection only when the requester's office is not a branch office.

The Group Management system shall log every rejected or failed group operation with its diagnostic detail.

---

## Error Response Format

### Project System Error Responses

> **Source files:** `plugins/applicationCommon/src/groovy/com/docu/project/action/CreateProjectAction.groovy`, `plugins/applicationCommon/src/groovy/com/docu/project/action/UpdateProjectAction.groovy`, `plugins/applicationCommon/src/groovy/com/docu/project/action/CreateBulkProjectMappingAction.groovy`

The Project system shall return operation outcomes as a structured message payload containing: a result type (success or error), a message title, a message body, and — for validation failures — the list of field-level errors. Error messages are resolved from the message catalogue; for this functional area the catalogue entries are present in English only.

The Project system shall map error conditions to message text as follows:

| Error condition (plain English) | Message text (verbatim, English) | Bengali present? |
|----------------------------------|-----------------------------------|------------------|
| Program not selected when saving a project | "Program Information not found" | no |
| Project field constraints not satisfied | HTML list of localised field-error messages (one item per failed field) | no |
| Project name already used by another project | "Project Name already exists" | no |
| Project code already used by another project | "Project Code already exists" | no |
| Project reference code already used by another project | "Project Ref Code already exists" | no |
| Project not found for an office mapping request | "projectInfo.projectNotFound" (catalogue entry absent; raw key surfaced) | no |
| Bulk import row has no office code | "Office Code can not be empty" | no |
| Bulk import office code not found | "Office not found for office code {office code}" | no |
| Bulk import group category not valid for the office | "Incorrect Group Category for office code {office code}" | no |
| Office-data validation: office code not found | "Invalid office code" | no |
| Office-data validation: group category not valid | "Invalid Group Category" | no |
| Any persistence failure during save | "Exception occurred in database operation" | no |
| Project created successfully | "Project has been saved successfully" | no |
| Project updated successfully | "Project has been updated successfully" | no |
| Project update committed (final confirmation) | "Project {project name} has updated successfully" | no |
| Office-wise project mapping updated | "Office {office name} has updated successfully" | no |
| Bulk office mapping committed | "Project {project name} has updated successfully" | no |
| Project cache refreshed after save | "Update Project Cache Successfully" | no |

When a rejection corresponds to a catalogue message key, the Project system shall resolve the message from the message catalogue; where the key has no catalogue entry, the system shall surface the supplied text or key as-is.

### Group Management System Error Responses

> **Source files:** `plugins/mf/grails-app/controllers/com/docu/sbicloud/program/group/GroupInfoController.groovy`, `plugins/mf/src/groovy/com/docu/sbicloud/program/groupinfo/action/CreateGroupInfoAction.groovy`, `plugins/mf/src/groovy/com/docu/sbicloud/program/groupinfo/action/UpdateGroupInfoAction.groovy`

The Group Management system shall return operation outcomes as a structured message payload containing a result type (success or error), a message title, and a message body; for field-level validation failures the body shall enumerate the offending fields. Group operations additionally return the affected group identifier alongside the message.

The Group Management system shall map error conditions to message text as follows. The microfinance message catalogue is maintained in English only; no Bengali catalogue is present for this domain.

| Error condition (plain English) | Message text (verbatim, English) | Bengali present? |
|----------------------------------|-----------------------------------|------------------|
| Project has no defined policy | "Project policy is not defined" | no |
| Reserved "Wash" VO name already used in the project | "VO name 'Wash' Already exists" | no |
| Orientation date earlier than the branch business day | "Orientation Date must be greater than Business Date" | no |
| Group creation date earlier than the branch business day | "VO Creation Date should not be later than Business Date" | no |
| Loan collection start date earlier than the branch business day | "Loan Collection Start Date can not be before business date" | no |
| Savings collection start date earlier than the branch business day | "Invalid Savings Collection Start Date" | no |
| Meeting day is not a working day for the configured country | "Meeting day must be a working Day" | no |
| Loan collection start date does not fall on the meeting day | "Meeting day does not match loan collection start date" | no |
| Savings collection start date does not fall on the meeting day | "Meeting day does not match savings collection start date" | no |
| Loan and savings collection frequencies differ | "Both loan and savings collection frequency should be same" | no |
| Group is already inactive when an update is attempted | "VO {0} can not be updated because of its inactive mode." | no |
| Group has active members when status change to inactive/closed is attempted | "This vo has active member. So vo status can not be inactive/closed" | no |
| Group has active members of the previous gender when gender change is attempted | "This vo has active member with previous VO Type.So you can not change this VO Type." | no |
| Group not found by identifier | "VO Information not found with id {0}" | no |
| New loan collection date not provided | "No Start Date found to update" | no |
| New savings collection date not provided | "New Saving Collection Start Date cannot be blank" | no |
| New loan collection date earlier than group creation date | "New Loan Collection start date should be later than VO Creation Date" | no |
| New savings collection date earlier than group creation date | "New Savings Collection start date should be later than VO Creation Date" | no |
| Collection start date changed on the group's own collection day | "VO collection start date can not be changed on VO collection date" | no |
| Requester lacks authority to view/edit the group | "You do not have authority to view this page. For further information please contact with you system administrator." | no |
| Concurrent edit detected (optimistic lock) | "Another user has updated this VO Information while you were editing" | no |
| Monthly loan/savings collection start date not on the configured week-of-month meeting date | (message key `groupInfo.loanCollectionStartDate.weekNo.error` is not defined in the catalogue; the raw key surfaces) | no |
| Daily / Quarterly / Six-Monthly / Yearly collection start date below the minimum gap from creation date | (message keys for these frequency-gap errors are not defined in the catalogue; the raw key surfaces) | no |
| Scanned survey form file could not be moved into group storage | "Could not move file" | no |

---

## Module: Project Management

> **Domain:** Project master-data management
> **Scope:** Creation, update, viewing, editing, and listing of projects, including the duplicate and program checks applied before a project is persisted and the downstream notifications fired afterward.
> **Entry Points:** Grails controller actions (`create`, `createProject`, `save`, `edit`, `editProject`, `updateProject`, `list`, `getGridDetailList`, `loadParentProjects`, `programWiseProjectList`, `syncProject`) delegating to the create/update/show/edit/list action services.
> **Source files:** `plugins/applicationCommon/grails-app/controllers/com/docu/project/ProjectController.groovy`, `plugins/applicationCommon/src/groovy/com/docu/project/action/CreateProjectAction.groovy`, `plugins/applicationCommon/src/groovy/com/docu/project/action/UpdateProjectAction.groovy`, `plugins/applicationCommon/src/groovy/com/docu/project/action/ShowProjectAction.groovy`, `plugins/applicationCommon/src/groovy/com/docu/project/action/EditProjectAction.groovy`, `plugins/applicationCommon/src/groovy/com/docu/project/action/ListProjectAction.groovy`, `plugins/applicationCommon/grails-app/services/com/docu/project/ProjectService.groovy`

### Project Creation Form

> **Source files:** `plugins/applicationCommon/grails-app/controllers/com/docu/project/ProjectController.groovy`, `plugins/applicationCommon/grails-app/services/com/docu/cache/ProgramInfoCacheService.groovy`

When an actor opens the new-project form, the Project system shall present the current business date, the current system date, the configured country, the actor's authorised projects as selectable parent projects, and the list of programs available for selection.

While presenting the new-project form, the Project system shall include in the program selection only those programs that are in active status.

When an actor requests the list of selectable parent projects, the Project system shall return only those projects that themselves have no parent project, ordered by project name.

When an actor requests the projects belonging to a chosen program, the Project system shall return the active projects whose program matches the chosen program.

### Project Creation

> **Source files:** `plugins/applicationCommon/src/groovy/com/docu/project/action/CreateProjectAction.groovy`, `plugins/applicationCommon/grails-app/services/com/docu/project/ProjectService.groovy`, `plugins/applicationCommon/grails-app/domain/com/docu/project/ProjectInfo.groovy`

When an actor submits a new project, the Project system shall default the project's country to Bangladesh if no country was supplied.

When an actor submits a new project, the Project system shall treat an absent source-of-fund as no source of fund, and shall treat an absent foreign amount or local amount as zero.

When an actor submits a new project, the Project system shall set the project's setup date to the current system date, set the project's effective date equal to its start date, default its status to active, and record the creating actor.

When a new project passes all validation, the Project system shall persist the project and confirm the outcome with the message "Project has been saved successfully".

If the program is not selected on a submitted project, the Project system shall reject the submission with the message "Program Information not found".

If a submitted project fails its field constraints, the Project system shall reject the submission and return the list of field-level error messages.

If the submitted project name matches the name of any other existing project, the Project system shall reject the submission with the message "Project Name already exists".

If the submitted project code matches the code of any other existing project, the Project system shall reject the submission with the message "Project Code already exists".

If the submitted project reference code matches the reference code of any other existing project, the Project system shall reject the submission with the message "Project Ref Code already exists".

If a database error occurs while persisting a new project, the Project system shall reject the submission with the message "Exception occurred in database operation".

**Field-level validation — Project submission:**

If the project name is not provided, the Project system shall reject the request.

If the country is not provided, the Project system shall reject the request.

If the project code is not provided, the Project system shall reject the request.

If the setup date is not provided, the Project system shall reject the request.

If the effective date is not provided, the Project system shall reject the request.

If the start date is not provided, the Project system shall reject the request.

If the end date is not provided, the Project system shall reject the request.

If the end date is earlier than the start date, the Project system shall reject the request.

If the microfinance-operation flag is not provided, the Project system shall reject the request.

### Project Update

> **Source files:** `plugins/applicationCommon/src/groovy/com/docu/project/action/UpdateProjectAction.groovy`, `plugins/applicationCommon/grails-app/services/com/docu/project/ProjectService.groovy`

When an actor submits changes to an existing project, the Project system shall load the project being edited, apply the submitted values, record the modifying actor, and validate before saving.

When an updated project passes all validation, the Project system shall persist the change and confirm the outcome with the message "Project {project name} has updated successfully".

If an updated project fails its field constraints, the Project system shall reject the update and return the list of field-level error messages.

If the updated project name matches the name of any other existing project, the Project system shall reject the update with the message "Project Name already exists".

If the updated project code matches the code of any other existing project, the Project system shall reject the update with the message "Project Code already exists".

If a database error occurs while persisting an updated project, the Project system shall reject the update with the message "Exception occurred in database operation".

### Project Viewing and Editing

> **Source files:** `plugins/applicationCommon/src/groovy/com/docu/project/action/ShowProjectAction.groovy`, `plugins/applicationCommon/src/groovy/com/docu/project/action/EditProjectAction.groovy`, `plugins/applicationCommon/grails-app/services/com/docu/project/ProjectService.groovy`

When an actor opens an existing project for viewing or editing, the Project system shall retrieve the project, its parent project where one exists, the configured country, the actor's authorised projects, and the list of active programs.

If retrieving a project for editing fails its precondition, the Project system shall return the actor to the project list with the failure message.

When an actor opens a project detail tab, the Project system shall assemble the data appropriate to the requested tab — the project record, its scheme mappings, its payment-mode view, or its office-mapping view.

While preparing the project-creation tab for an actor whose working office is the global head office, the Project system shall present a blank project; otherwise the Project system shall pre-fill the project with a newly generated project code scoped to the configured country.

### Project Listing

> **Source files:** `plugins/applicationCommon/src/groovy/com/docu/project/action/ListProjectAction.groovy`, `plugins/applicationCommon/grails-app/services/com/docu/project/ProjectService.groovy`

When an actor requests the project grid, the Project system shall return projects with their code, reference code, name, start date, end date, setup date, effective date, and a derived active/inactive status label.

While listing projects, where both a project identifier and a project code are supplied, the Project system shall return only the project matching both.

While listing projects, where only a project identifier is supplied, the Project system shall return only the project matching that identifier.

While listing projects, where only a project code is supplied, the Project system shall return only the project matching that code.

When an actor requests the active project list by name, the Project system shall return only active projects matching the supplied identifier.

When an actor requests the active project list by code, the Project system shall return only active projects whose code contains the supplied text.

While filtering the project list, where both a project code and a project identifier are supplied and the supplied code does not match the actual code of the identified project, the Project system shall return an empty result.

### Project Synchronisation

> **Source files:** `plugins/applicationCommon/grails-app/controllers/com/docu/project/ProjectController.groovy`, `plugins/applicationCommon/src/groovy/com/docu/project/action/CreateProjectAction.groovy`

When an actor requests a project synchronisation, the Project system shall refresh the project cache, evict the dependent accounting and collection caches, notify the human-resource domain, and confirm the outcome with the message "Update Project Cache Successfully".

---

## Module: Project–Office Mapping

> **Domain:** Mapping of projects to offices and offices to projects
> **Scope:** Project-wise office mapping, office-wise project mapping, and the bulk spreadsheet import of project-office mappings, including the office-code, group-category and per-mapping validation applied before mappings are persisted, plus the read endpoints that drive these screens.
> **Entry Points:** Grails controller actions (`projectWiseOfficeMapping`, `officeMapping`, `divisionWiseOffice`, `updateOfficeMapping`, `officeWiseProjectMapping`, `projectMapping`, `updateOfficeWiseProjectMapping`, `excelDataSave`, `downloadDefaultXls`, `validateData`, `validateOfficeData`) delegating to the office-mapping action services.
> **Source files:** `plugins/applicationCommon/grails-app/controllers/com/docu/project/ProjectController.groovy`, `plugins/applicationCommon/src/groovy/com/docu/project/action/ShowOfficeMappingAction.groovy`, `plugins/applicationCommon/src/groovy/com/docu/project/action/UpdateProjectOfficeMappingAction.groovy`, `plugins/applicationCommon/src/groovy/com/docu/project/action/ShowProjectMappingAction.groovy`, `plugins/applicationCommon/src/groovy/com/docu/project/action/UpdateOfficeWiseProjectMappingAction.groovy`, `plugins/applicationCommon/src/groovy/com/docu/project/action/CreateBulkProjectMappingAction.groovy`, `plugins/applicationCommon/grails-app/services/com/docu/project/ProjectService.groovy`, `plugins/applicationCommon/grails-app/domain/com/docu/project/ProjectOfficeMapping.groovy`

### Office Mapping Screens

> **Source files:** `plugins/applicationCommon/src/groovy/com/docu/project/action/ShowOfficeMappingAction.groovy`, `plugins/applicationCommon/src/groovy/com/docu/project/action/ShowProjectMappingAction.groovy`, `plugins/applicationCommon/grails-app/services/com/docu/project/ProjectService.groovy`

When an actor opens the project-wise office mapping screen for a project whose program operates through field offices, the Project system shall present the offices under the chosen administrative area together with their selectable parent offices, the available area types and branch-growth types, the available group categories, and the offices already mapped to the project.

When an actor opens the project-wise office mapping screen for a project whose program does not operate through field offices, the Project system shall present the screen without a field-office list.

When an actor opens the office-wise project mapping screen, the Project system shall present the offices in the configured country together with the offices already running microfinance for the chosen project.

When an actor opens the office-mapping spreadsheet-upload screen, the Project system shall present the chosen project.

When an actor requests the divisional office list, the Project system shall return the division-level offices.

When an actor requests the branch offices under a chosen administrative unit, the Project system shall return only branch-type offices, labelled by office type, code and name.

When an actor requests the default office-mapping spreadsheet template, the Project system shall deliver the stored template file as a download, and shall do nothing if the template file is not present.

### Project-wise Office Mapping Update

> **Source files:** `plugins/applicationCommon/src/groovy/com/docu/project/action/UpdateProjectOfficeMappingAction.groovy`, `plugins/applicationCommon/grails-app/services/com/docu/project/ProjectService.groovy`

When an actor submits the offices selected for a project, the Project system shall build a mapping for each selected office, set each mapping to active status, record the acting actor, validate every mapping, and on success replace the project's office mappings and confirm with the message "Project {project name} has updated successfully".

If the project identified for a project-wise office mapping update cannot be found, the Project system shall reject the request with the message "projectInfo.projectNotFound".

If any office mapping in a project-wise office mapping update fails its field constraints, the Project system shall reject the request and return the list of field-level error messages.

If a database error occurs while saving a project-wise office mapping, the Project system shall reject the request with the message "Exception occurred in database operation".

### Office-wise Project Mapping Update

> **Source files:** `plugins/applicationCommon/src/groovy/com/docu/project/action/UpdateOfficeWiseProjectMappingAction.groovy`, `plugins/applicationCommon/grails-app/services/com/docu/project/ProjectService.groovy`

When an actor submits the projects selected for an office, the Project system shall build a mapping for each selected project against that office, set each mapping to active status, record the acting actor, validate every mapping, and on success replace the office's project mappings and confirm with the message "Office {office name} has updated successfully".

If any mapping in an office-wise project mapping update fails its field constraints, the Project system shall reject the request and return the list of field-level error messages.

If a database error occurs while saving an office-wise project mapping, the Project system shall reject the request with the message "Exception occurred in database operation".

### Bulk Project-Office Mapping Import

> **Source files:** `plugins/applicationCommon/src/groovy/com/docu/project/action/CreateBulkProjectMappingAction.groovy`, `plugins/applicationCommon/grails-app/services/com/docu/project/ProjectService.groovy`

When an actor uploads a spreadsheet of office mappings for a project, the Project system shall, for each row, resolve the office by its office code, resolve the group category by its name, build a mapping in active status against the project, validate it, and on success replace the project's office mappings and confirm with the message "Project {project name} has updated successfully".

While importing a row, where an office is already mapped to the project, the Project system shall carry forward the existing parent office and replace the existing mapping rather than duplicate it.

If a bulk-import row has no office code, the Project system shall reject the import with the message "Office Code can not be empty".

If a bulk-import row's office code does not match any office, the Project system shall reject the import with the message "Office not found for office code {office code}".

If a bulk-import row's group category is not valid, the Project system shall reject the import with the message "Incorrect Group Category for office code {office code}".

If a constructed mapping in a bulk import fails its field constraints, the Project system shall reject the import and return the list of field-level error messages.

If any other error occurs while preparing the bulk import, the Project system shall reject the import and return the resulting error message.

If a database error occurs while committing the bulk import, the Project system shall reject the import and return the resulting error message.

**Field-level validation — Project-office mapping:**

If the branch-growth type is not provided, the Project system shall reject the request.

If the group category is not provided, the Project system shall reject the request.

### Pre-submission Office and Mapping Validation

> **Source files:** `plugins/applicationCommon/src/groovy/com/docu/project/action/AjaxProjectAction.groovy`, `plugins/applicationCommon/grails-app/services/com/docu/project/ProjectService.groovy`

When an actor asks to validate a batch of office codes, area types, branch-growth types and group categories before submission, the Project system shall return the list of office codes not found in the configured country, the list of unrecognised area types, the list of unrecognised branch-growth types, and the list of unrecognised group categories.

When an actor asks to validate a single office entry, if the office code does not match any office, the Project system shall respond with "Invalid office code".

When an actor asks to validate a single office entry, if the group category is not recognised, the Project system shall respond with "Invalid Group Category".

When a single office entry is valid, the Project system shall respond with an empty result indicating acceptance.

---

## Module: Project Lookup and Reporting

> **Domain:** Project reference lookups and reporting
> **Scope:** Read-only lookups that feed pickers, trees, search panels and auto-complete fields, and the project list spreadsheet export. Most lookups are served from the project cache or from direct database queries.
> **Entry Points:** Grails controller actions (`ajax`, `loadCountryProgramInfoByCountry`, `getEmployeeList`, `getGridDetailList`, `projectExcelReport`, `updateEmployeeProject`) and the asynchronous lookup methods of the AJAX action service.
> **Source files:** `plugins/applicationCommon/grails-app/controllers/com/docu/project/ProjectController.groovy`, `plugins/applicationCommon/src/groovy/com/docu/project/action/AjaxProjectAction.groovy`, `plugins/applicationCommon/grails-app/services/com/docu/project/ProjectService.groovy`, `plugins/applicationCommon/src/groovy/com/docu/util/report/ExcelExporter.groovy`

### Project Reference Lookups

> **Source files:** `plugins/applicationCommon/src/groovy/com/docu/project/action/AjaxProjectAction.groovy`, `plugins/applicationCommon/grails-app/services/com/docu/project/ProjectService.groovy`

When an actor requests projects for a chosen country, the Project system shall return the projects of that country labelled by code and name.

When an actor requests authorised projects for a chosen country as auto-complete entries, the Project system shall return the actor's authorised projects of that country labelled by code and name.

When an actor requests a new project code for a chosen country, the Project system shall generate a project code scoped to that country.

When an actor requests projects for the search panel, the Project system shall return only microfinance projects; for an external actor this shall be drawn from all microfinance projects, and for an internal actor from the actor's authorised microfinance projects, further narrowed to the chosen country when one is supplied.

When an actor requests the program-and-project selection tree, the Project system shall return a country node containing each core microfinance program that has at least one project, with each program expanded to its loan-bearing projects.

When an actor requests the employees matching a search term, the Project system shall return active employees whose name matches the term, ordered by name.

When an actor requests the offices mapped to a project, the Project system shall return those offices labelled by office code and name.

### Project List Export

> **Source files:** `plugins/applicationCommon/grails-app/controllers/com/docu/project/ProjectController.groovy`, `plugins/applicationCommon/src/groovy/com/docu/project/action/AjaxProjectAction.groovy`, `plugins/applicationCommon/src/groovy/com/docu/util/report/ExcelExporter.groovy`

When an actor requests the project list spreadsheet, the Project system shall produce a spreadsheet containing, for each project, its operation type, program type, program code and name, project code and name, reference code, setup, effective, start and end dates, status, finance-operation flag, entity category, and signing date.

If no projects are available when the project list spreadsheet is requested, the Project system shall return a report message of "No Data Found." instead of an empty spreadsheet.

When producing the project list spreadsheet, the Project system shall title the export "Project List", scope it to the actor's country, and record the actor's user name on the export.

### Operational Project Count

> **Source files:** `plugins/applicationCommon/grails-app/services/com/docu/project/ProjectService.groovy`

When the number of running projects is requested for a business date, the Project system shall count active projects whose period spans that date; for a head office the count covers all such projects (narrowed to the office's country for a country head office), and for any other office the count covers only the projects mapped to that office's permitted offices.

If no business date is available when the number of running projects is requested, the Project system shall return a count of zero.

---

## Module: Project Validation Rules

> **Domain:** Business Rule Validation — project and project-office mapping
> **Scope:** The consolidated business-rule checks applied by the action services across project creation, project update, and the three mapping flows. These rules execute after field-level constraint validation and before persistence and are shared by the entry points above.
> **Entry Points:** Invoked internally by the project and mapping entry points above.
> **Source files:** `plugins/applicationCommon/src/groovy/com/docu/project/action/CreateProjectAction.groovy`, `plugins/applicationCommon/src/groovy/com/docu/project/action/UpdateProjectAction.groovy`, `plugins/applicationCommon/src/groovy/com/docu/project/action/CreateBulkProjectMappingAction.groovy`, `plugins/applicationCommon/src/groovy/com/docu/project/action/UpdateProjectOfficeMappingAction.groovy`, `plugins/applicationCommon/src/groovy/com/docu/project/action/AjaxProjectAction.groovy`

### Uniqueness and Presence Rules

> **Source files:** `plugins/applicationCommon/src/groovy/com/docu/project/action/CreateProjectAction.groovy`, `plugins/applicationCommon/src/groovy/com/docu/project/action/UpdateProjectAction.groovy`

The Project system shall require that every project name is unique across all projects, evaluated by comparing the submitted name against every other project and rejecting any duplicate.

The Project system shall require that every project code is unique across all projects, evaluated by comparing the submitted code against every other project and rejecting any duplicate.

The Project system shall require that every project reference code is unique across all projects, evaluated when a new project is submitted by comparing the submitted reference code against every other project and rejecting any duplicate.

The Project system shall require that a program is selected on every project before it is persisted.

### Mapping Resolution Rules

> **Source files:** `plugins/applicationCommon/src/groovy/com/docu/project/action/CreateBulkProjectMappingAction.groovy`, `plugins/applicationCommon/src/groovy/com/docu/project/action/UpdateProjectOfficeMappingAction.groovy`, `plugins/applicationCommon/src/groovy/com/docu/project/action/AjaxProjectAction.groovy`

The Project system shall require that the project named in any office-mapping update exists before mappings are processed.

The Project system shall require that every office code used in a bulk mapping import resolves to a known office, that the office code is not blank, and that the group category resolves to a known category for that office.

The Project system shall reject any project-office or office-wise mapping whose constructed record does not satisfy its field constraints, returning the field-level error list.

---

## Module: Cross-Plugin and External Integrations (Project System)

> **Domain:** Cross-domain and external system integrations
> **Scope:** Notifications sent to the human-resource domain when a project is created or updated, and the outbound HTTP push of project data performed during save.
> **Source files:** `plugins/applicationCommon/src/groovy/com/docu/project/action/CreateProjectAction.groovy`, `plugins/applicationCommon/src/groovy/com/docu/project/action/UpdateProjectAction.groovy`, `plugins/applicationCommon/grails-app/services/com/docu/project/ProjectService.groovy`

### Human-Resource Project Notification

> **Source files:** `plugins/applicationCommon/src/groovy/com/docu/project/action/CreateProjectAction.groovy`, `plugins/applicationCommon/src/groovy/com/docu/project/action/UpdateProjectAction.groovy`

When a project is created or updated, the Project system shall forward the saved project to the human-resource integration service so that the project is reflected in the human-resource domain.

After a project is created, the Project system shall send a create-project notification to the human-resource enterprise-service-bus integration; after a project is updated, it shall instead send an update-project notification.

### Outbound Project Push

> **Source files:** `plugins/applicationCommon/grails-app/services/com/docu/project/ProjectService.groovy`

When a project is persisted, the Project system shall asynchronously push the project, and the project's department information, to the configured outbound endpoints without blocking the save outcome.

---

## Module: Async and Scheduled Processing (Project System)

> **Domain:** Asynchronous side effects and cache maintenance
> **Scope:** Cache refresh and eviction side effects fired after project and mapping changes, and the administrator-triggered cache refresh endpoint. No scheduled job operates on this domain.
> **Source files:** `plugins/applicationCommon/grails-app/controllers/com/docu/project/ProjectController.groovy`, `plugins/applicationCommon/src/groovy/com/docu/project/action/CreateProjectAction.groovy`, `plugins/applicationCommon/grails-app/services/com/docu/project/ProjectService.groovy`

### Cache Maintenance

> **Source files:** `plugins/applicationCommon/grails-app/controllers/com/docu/project/ProjectController.groovy`, `plugins/applicationCommon/grails-app/services/com/docu/project/ProjectService.groovy`

When an administrator triggers a project-office cache refresh, the Project system shall rebuild the project-office mapping, project, and physical-office caches and report success with the message "Project Info Redis cache updated successfully."

If the administrator-triggered cache refresh fails, the Project system shall report the failure with the underlying error description.

After every project save and every mapping save, the Project system shall refresh the affected project or mapping cache so that reads remain consistent with persisted data.

---

## Module: Group Management

> **Domain:** Microfinance Group (Village Organization) lifecycle
> **Scope:** Creation, update, soft-deletion, edit-form preparation, viewing, and listing of groups within a branch and project.
> **Entry Points:** Grails controller actions (`create`, `save`, `edit`, `update`, `delete`, `show`, `list`, `index`, listing/lookup feeds) delegating to legacy action classes.
> **Source files:** `plugins/mf/grails-app/controllers/com/docu/sbicloud/program/group/GroupInfoController.groovy`, `plugins/mf/src/groovy/com/docu/sbicloud/program/groupinfo/action/CreateGroupInfoAction.groovy`, `plugins/mf/src/groovy/com/docu/sbicloud/program/groupinfo/action/UpdateGroupInfoAction.groovy`, `plugins/mf/src/groovy/com/docu/sbicloud/program/groupinfo/action/DeleteGroupInfoAction.groovy`, `plugins/mf/src/groovy/com/docu/sbicloud/program/groupinfo/action/ShowGroupInfoAction.groovy`, `plugins/mf/src/groovy/com/docu/sbicloud/program/groupinfo/action/EditGroupInfoAction.groovy`, `plugins/mf/src/groovy/com/docu/sbicloud/program/groupinfo/action/ListGroupInfoAction.groovy`, `plugins/mf/grails-app/services/com/docu/sbicloud/program/group/GroupService.groovy`

### Group Creation

> **Source files:** `plugins/mf/src/groovy/com/docu/sbicloud/program/groupinfo/action/CreateGroupInfoAction.groovy`, `plugins/mf/grails-app/services/com/docu/sbicloud/program/group/GroupService.groovy`

When an operator submits a new group for a branch and project, the Group Management system shall validate the submission, persist the new group as active, and report success with the message "New VO {0} is created successfully" where {0} is the group code and name.

When a new group is created, the Group Management system shall set the group's branch office to the operator's current office, set the group's status to active, set the group's data status to active, set the last project-officer assignment date equal to the group creation date, and set the next collection date equal to the loan collection start date.

When a new group is created with an automatic group code, the Group Management system shall generate the group's permanent identifier and use that identifier as the group code.

When a new group is created, the Group Management system shall generate and assign a VO reference number derived from the group's branch office.

After a new group is successfully created with an attached scanned survey form, the Group Management system shall move the uploaded survey form file into the group's permanent storage location and rename it to the group's survey-form name; if the file cannot be moved, the Group Management system shall report the error "Could not move file".

If the selected project has no defined policy, the Group Management system shall reject the creation with the message "Project policy is not defined".

If the submitted group name is the reserved name "Wash" and a "Wash" group already exists for the selected project in the operator's branch, the Group Management system shall reject the creation with the message "VO name 'Wash' Already exists".

If the orientation date is earlier than the branch business day, the Group Management system shall reject the creation with the message "Orientation Date must be greater than Business Date".

If the group creation date is earlier than the branch business day, the Group Management system shall reject the creation with the message "VO Creation Date should not be later than Business Date".

If the loan collection start date is earlier than the branch business day, the Group Management system shall reject the creation with the message "Loan Collection Start Date can not be before business date".

While the loan collection frequency is monthly, if the loan collection start date does not coincide with the collection date computed for the chosen meeting day and week-of-month, the Group Management system shall reject the creation (the corresponding message key for this week-of-month mismatch is not defined in the catalogue).

While the loan collection frequency is daily, if fewer than one day separates the group creation date and the loan collection start date, the Group Management system shall reject the creation (the corresponding frequency-gap message key is not defined in the catalogue).

While the loan collection frequency is quarterly, if fewer than eighty-four days separate the group creation date and the loan collection start date, the Group Management system shall reject the creation (the corresponding frequency-gap message key is not defined in the catalogue).

While the loan collection frequency is six-monthly, if fewer than one hundred sixty-eight days separate the group creation date and the loan collection start date, the Group Management system shall reject the creation (the corresponding frequency-gap message key is not defined in the catalogue).

While the loan collection frequency is yearly, if fewer than three hundred sixty-five days separate the group creation date and the loan collection start date, the Group Management system shall reject the creation (the corresponding frequency-gap message key is not defined in the catalogue).

If the savings collection start date is earlier than the branch business day, the Group Management system shall reject the creation with the message "Invalid Savings Collection Start Date".

If the chosen meeting day is not a working day for the operator's configured country, the Group Management system shall reject the creation with the message "Meeting day must be a working Day".

If the loan collection start date does not fall on the chosen meeting day, the Group Management system shall reject the creation with the message "Meeting day does not match loan collection start date".

If the savings collection start date does not fall on the chosen meeting day, the Group Management system shall reject the creation with the message "Meeting day does not match savings collection start date".

If the loan collection frequency and the savings collection frequency are not the same, the Group Management system shall reject the creation with the message "Both loan and savings collection frequency should be same".

If the submitted group fails field-level validation, the Group Management system shall reject the creation and return the field-level errors.

If persisting the new group raises a data-access error, the Group Management system shall report the failure and not create the group.

**Field-level validation — Group:**

If the group name is not provided, the Group Management system shall reject the request.

If the group name is shorter than 2 characters or longer than 64 characters, the Group Management system shall reject the request.

If the group name begins with a digit or contains characters outside the permitted set of letters, digits, spaces, and a limited set of punctuation, the Group Management system shall reject the request.

If no assigned project officer is provided, the Group Management system shall reject the request.

If no meeting day is provided, the Group Management system shall reject the request.

If no meeting time is provided, the Group Management system shall reject the request.

If no loan collection frequency is provided, the Group Management system shall reject the request.

If no loan collection start date is provided, the Group Management system shall reject the request.

If no savings collection frequency is provided, the Group Management system shall reject the request.

If no savings collection start date is provided, the Group Management system shall reject the request.

If no group creation date is provided, the Group Management system shall reject the request.

If no orientation date is provided, the Group Management system shall reject the request.

If the orientation date is earlier than the group creation date, the Group Management system shall reject the request (the orientation date must be on or after the group creation date).

If the group reference number exceeds 25 characters, the Group Management system shall reject the request.

If no project is provided, the Group Management system shall reject the request.

If the spot address exceeds 255 characters, the Group Management system shall reject the request.

If the demarcation area exceeds 255 characters, the Group Management system shall reject the request.

If no group status is provided, the Group Management system shall reject the request.

If no applicable gender is provided, the Group Management system shall reject the request.

### Group Update

> **Source files:** `plugins/mf/src/groovy/com/docu/sbicloud/program/groupinfo/action/UpdateGroupInfoAction.groovy`, `plugins/mf/grails-app/services/com/docu/sbicloud/program/group/GroupService.groovy`

When an operator submits changes to an existing group, the Group Management system shall validate the changes, persist them atomically, and report success with the message "{0} VO is updated successfully" where {0} is the group code and name.

When a group update changes the assigned project officer, the Group Management system shall record a project-officer release history entry for the group, reassign every member of the group to the new project officer, record a project-officer release history entry for each reassigned member, and set the group's and members' last project-officer assignment date to the current business day.

When a group update does not change the assigned project officer, the Group Management system shall leave the members' project-officer assignment unchanged.

When a group update sets the group's data status to inactive, the Group Management system shall report success with the message "{0} VO is deleted successfully".

After a group update that replaces the scanned survey form, the Group Management system shall delete the previous survey-form file and move and rename the newly uploaded file into the group's storage location; if the file cannot be moved, the Group Management system shall report the error "Could not move file".

If the group to be updated is not found, the Group Management system shall reject the update with the message "VO Information not found with id {0}".

If the group to be updated is already inactive, the Group Management system shall reject the update with the message "VO {0} can not be updated because of its inactive mode.".

If the applicable gender is being changed to a value other than "both" and the group has active or expired members of the previous gender, the Group Management system shall reject the update with the message "This vo has active member with previous VO Type.So you can not change this VO Type.".

If the group has active or expired members and the update sets the group status to inactive or closed, the Group Management system shall reject the update with the message "This vo has active member. So vo status can not be inactive/closed".

If the update requests deletion (data status set to inactive) and the group has active or expired members, the Group Management system shall reject the update with the message "This vo has active member. So vo status can not be inactive/closed".

If the selected project has no defined policy, the Group Management system shall reject the update with the message "Project policy is not defined".

While the group has no members and a savings collection start date is supplied and the loan collection frequency is monthly, if the savings collection start date does not coincide with the collection date computed for the meeting day and week-of-month, the Group Management system shall reject the update (the corresponding week-of-month mismatch message key is not defined in the catalogue).

If the chosen meeting day is not a working day for the group's office country, the Group Management system shall reject the update with the message "Meeting day must be a working Day".

If the submitted group fails field-level validation, the Group Management system shall reject the update and return the field-level errors.

If the updated group name is the reserved name "Wash" and another "Wash" group already exists for the project in the operator's branch, the Group Management system shall reject the update with the message "VO name 'Wash' Already exists".

When a group whose status is set back to active is updated, the Group Management system shall clear any recorded close reason.

If persisting the group update raises a data-access error, the Group Management system shall report the failure and not apply the update.

### Group Deletion

> **Source files:** `plugins/mf/src/groovy/com/docu/sbicloud/program/groupinfo/action/DeleteGroupInfoAction.groovy`, `plugins/mf/grails-app/services/com/docu/sbicloud/program/group/GroupService.groovy`

When an operator requests deletion of a group, the Group Management system shall mark the group's data status inactive (a soft deletion), increment its version, and report success with the message "{0} VO is deleted successfully".

If the group to be deleted is not found, the Group Management system shall reject the deletion with the message "VO Information not found with id {0}".

If the group to be deleted is already inactive, the Group Management system shall reject the deletion with the message "VO {0} can not be updated because of its inactive mode.".

If the group has active or expired members, the Group Management system shall reject the deletion with the message "This vo has active member. So vo status can not be inactive/closed".

If the group fails field-level validation, the Group Management system shall reject the deletion and return the field-level errors.

If persisting the soft deletion raises a data-access error, the Group Management system shall report the failure and not delete the group.

### Group Viewing and Edit-Form Preparation

> **Source files:** `plugins/mf/src/groovy/com/docu/sbicloud/program/groupinfo/action/ShowGroupInfoAction.groovy`, `plugins/mf/src/groovy/com/docu/sbicloud/program/groupinfo/action/EditGroupInfoAction.groovy`, `plugins/mf/grails-app/controllers/com/docu/sbicloud/program/group/GroupInfoController.groovy`, `plugins/mf/grails-app/services/com/docu/sbicloud/program/group/GroupService.groovy`

When an operator opens a group for viewing, the Group Management system shall present the group together with its project policy, project, VO category, service territory, and applicable gender.

When an operator opens a group for editing, the Group Management system shall present the group together with its authorised group-association projects, applicable genders, meeting days, group statuses, VO category and service territory (where set), and the count of loan-holding and savings-holding sub-records for the group, and shall indicate whether any member exists for the group.

If the group requested for viewing or editing is not found, the Group Management system shall reject the request with the message "VO Information not found with id {0}".

If the requester is not authorised for the group's project or office scope, the Group Management system shall reject viewing or editing with the message "You do not have authority to view this page. For further information please contact with you system administrator.".

### Group Listing

> **Source files:** `plugins/mf/src/groovy/com/docu/sbicloud/program/groupinfo/action/ListGroupInfoAction.groovy`, `plugins/mf/grails-app/services/com/docu/sbicloud/program/group/GroupService.groovy`, `plugins/mf/src/groovy/com/docu/sbicloud/program/groupinfo/action/AjaxGroupInfoAction.groovy`

When an operator requests the group grid, the Group Management system shall return active groups, each with its branch office, group code, VO reference number, group name, assigned project officer, meeting day, VO category, and meeting time.

The Group Management system shall restrict the group grid to groups within the requester's authorised office set and project set, and shall further narrow the results by any supplied office, project, project country, country, gender, status, group code, group name, or meeting-day filter.

When an operator requests the automatically-closeable group list, the Group Management system shall return only active-status groups in the office that have no active members and no outstanding loan balance and no savings balance.

When an operator requests the active-group autocomplete, the Group Management system shall return active groups matching the supplied criteria.

When an operator requests the list of collection frequencies for a project, the Group Management system shall return the project's collection frequencies excluding the single (one-off) frequency.

---

## Module: Collection Schedule Management

> **Domain:** Group loan and savings collection-date scheduling
> **Scope:** Changing a group's loan and savings collection start dates and recomputing the next collection date according to the collection frequency and any existing loans.
> **Entry Points:** Grails controller actions (`changeCollectionStartDate`, `saveChangeCollectionStartDate`, `getNewCollectionDate`) delegating to a legacy action class.
> **Source files:** `plugins/mf/src/groovy/com/docu/sbicloud/program/groupinfo/action/ChangeCollectionStartDateAction.groovy`, `plugins/mf/grails-app/controllers/com/docu/sbicloud/program/group/GroupInfoController.groovy`, `plugins/mf/grails-app/services/com/docu/sbicloud/program/group/GroupService.groovy`

### Change Collection Start Date

> **Source files:** `plugins/mf/src/groovy/com/docu/sbicloud/program/groupinfo/action/ChangeCollectionStartDateAction.groovy`

When an operator submits new loan and savings collection start dates for a group, the Group Management system shall validate the dates, apply them, recompute the group's next collection date, and report success with the message "{0} VO is updated successfully" where {0} is the group code.

When the new collection start dates are applied and the group has no loan accounts, the Group Management system shall set the group's next loan collection date to the new loan collection start date and its next savings collection date to the new savings collection start date.

While the group's loan frequency is weekly and the group has at least one loan account, the Group Management system shall set the next loan and savings collection dates to the closest scheduled repayment dates on or after the last scheduled collection date for the branch business day.

While the group's loan frequency is bi-weekly and the group has at least one loan account, the Group Management system shall advance the new loan and savings collection start dates in fourteen-day steps until each is not earlier than the branch business day, and set those as the next collection dates.

While the group's loan frequency is monthly and the group has at least one loan account, the Group Management system shall select the next loan and savings collection dates from the candidate meeting dates within the month according to the configured week-of-month, and if the resulting date precedes the branch business day, shall advance to the next closest scheduled repayment date.

If the group is not found, the Group Management system shall reject the change with the message "VO Information not found with id {0}".

If the new loan collection date is not provided, the Group Management system shall reject the change with the message "No Start Date found to update".

If the new savings collection date is not provided, the Group Management system shall reject the change with the message "New Saving Collection Start Date cannot be blank".

If the new loan collection date is earlier than the group creation date, the Group Management system shall reject the change with the message "New Loan Collection start date should be later than VO Creation Date".

If the new loan collection date does not fall on the group's meeting day, the Group Management system shall reject the change with the message "Meeting day does not match loan collection start date".

If the new savings collection date is earlier than the group creation date, the Group Management system shall reject the change with the message "New Savings Collection start date should be later than VO Creation Date".

If the new savings collection date does not fall on the group's meeting day, the Group Management system shall reject the change with the message "Meeting day does not match savings collection start date".

If the group's current next collection date equals the branch business day (today is a collection day), the Group Management system shall reject the change with the message "VO collection start date can not be changed on VO collection date".

If the group fails field-level validation, the Group Management system shall reject the change and return the field-level errors.

If persisting the change raises a data-access error, the Group Management system shall report the failure and not apply the change.

---

## Module: Group Lookups and Reference Feeds

> **Domain:** Supporting reference-data feeds for the group screens
> **Scope:** Project, office, project-officer, and group autocomplete and reference feeds backing the group create/edit/search panels.
> **Entry Points:** Grails controller actions (`autoCompleteGroupList`, `getCOList`, `getBranchWiseCOList`, `jsonProjectListForSearchPanel`, `jsonOfficeListByProjectForSearchPanel`, `getAllOffice`, `getOffice`, `getGroupDataByProject`, `listCollectionFrequencyByProject`) delegating to AJAX action classes and services.
> **Source files:** `plugins/mf/grails-app/controllers/com/docu/sbicloud/program/group/GroupInfoController.groovy`, `plugins/mf/src/groovy/com/docu/sbicloud/program/groupinfo/action/AjaxGroupInfoAction.groovy`, `plugins/applicationCommon/src/groovy/com/docu/office/action/officeinfo/AjaxOfficeInfoAction.groovy`, `plugins/mf/grails-app/services/com/docu/sbicloud/program/group/GroupService.groovy`

### Project-Officer and Group Feeds

> **Source files:** `plugins/mf/src/groovy/com/docu/sbicloud/program/groupinfo/action/AjaxGroupInfoAction.groovy`

When an operator requests the project-officer list for a group screen, the Group Management system shall return the matching project officers and shall append a placeholder "NO NAME" project-officer entry to the list.

When an operator requests the active-group autocomplete feed, the Group Management system shall return active groups matching the supplied criteria.

### Project-Policy and Frequency Feeds

> **Source files:** `plugins/mf/grails-app/controllers/com/docu/sbicloud/program/group/GroupInfoController.groovy`, `plugins/mf/grails-app/services/com/docu/sbicloud/program/group/GroupService.groovy`

When an operator selects a project on a group screen, the Group Management system shall return the selected project's policy information.

When an operator requests the collection frequencies for a project, the Group Management system shall return the project's configured collection frequencies excluding the single (one-off) frequency.

### Office Feeds

> **Source files:** `plugins/mf/grails-app/controllers/com/docu/sbicloud/program/group/GroupInfoController.groovy`, `plugins/applicationCommon/src/groovy/com/docu/office/action/officeinfo/AjaxOfficeInfoAction.groovy`

When an operator requests the full office list, the Group Management system shall return the field offices, scoping the results to the requester's country when the requester is an internal user.

When an operator requests offices for a project search panel, the Group Management system shall return the offices mapped to the selected project.

---

## Domain Entities and Properties

> Shared audit fields (creating actor and creation timestamp, modifying actor and modification timestamp), the optimistic-locking version, and the active/inactive soft-status flag apply to all entities below and are described once under Cross-Cutting Requirements → Audit and Record Lifecycle; they are not repeated per entity. Where an entity appears in both source specs, the most complete property list is shown and the cross-reference note explains the view the other spec takes.

### Project

> **Source files (authoritative — Project system):** `plugins/applicationCommon/grails-app/domain/com/docu/project/ProjectInfo.groovy`
> **Cross-reference (Group Management system):** Groups reference this entity via `projectInfo`; the Group spec lists only the subset of properties read by the Group domain (`projectCode`, `projectName`, `projectCountry`, `projectStartDate`, `projectEndDate`, `parentProjectInfoId`). The full property list below is authoritative.

Represents an operational project belonging to one program and one country, with its scheduling dates, financial commitment and operational flags.

| Property | Type | Meaning | Constraints |
|----------|------|---------|-------------|
| proposalId | Text | Reference to an originating proposal | optional |
| projectCountry | Reference to Country | Country the project operates in | required |
| projectCode | Text | Business code identifying the project | required; unique by business rule |
| projectRefCode | Text | External reference code | optional; unique by business rule |
| projectName | Text | Display name of the project | required, not blank; unique by business rule |
| projectDescription | Text | Free-text description | optional |
| projectShortCode | Text | Abbreviated code | optional |
| projectSetupDate | Date | Date the project was established | required |
| projectEffectiveDate | Date | Date the project becomes effective | required |
| projectStartDate | Date | Project commencement date | required |
| projectEndDate | Date | Project completion date | required; must be on or after the start date |
| domainStatus | Reference to DomainStatus | Active/inactive status of the project | required |
| programInfo | Reference to ProgramInfo | Program the project belongs to | required |
| bookClosing | Boolean | Whether the project's book is closed | default false |
| parentProjectInfoId | Identifier | Parent project for a sub-project | optional |
| departmentId | Identifier | Linked human-resource department | optional |
| isIndependent | Boolean | Whether the project is independent | optional; default false |
| isOverhead | Boolean | Whether the project is overhead | optional; default false |
| hoType | Text | Head-office classification | optional |
| boType | Text | Branch-office classification | optional |
| mfProjectRefCode | Text | Microfinance project reference code | optional |
| isNgoBeuro | Boolean | NGO-bureau registration flag | optional |
| beuroFromDate | Date | NGO-bureau registration start | optional |
| beuroToDate | Date | NGO-bureau registration end | optional |
| isTrendxProject | Boolean | Trendx integration flag | optional |
| isSmartCollection | Boolean | Smart-collection flag | optional |
| hasMfOperation | Boolean | Whether the project runs microfinance | required |
| projectStatus | Enum (ProjectStatus) | Operational status of the project | optional |
| startMonth | Number | Fiscal start month | optional |
| endMonth | Number | Fiscal end month | optional |
| mfEndMonth | Number | Microfinance end month | optional |
| hasFinOperation | Boolean | Whether the project runs finance operations | optional |
| sourceOfFundId | Identifier | Funding source | optional |
| remarks | Text | Commitment notes (stored as long text) | optional |
| foreignCurrency | Text | Foreign currency code | optional |
| localCurrency | Text | Local currency code | optional |
| foreignAmount | Amount | Foreign currency commitment amount | default 0 |
| localAmount | Amount | Local currency commitment amount | default 0 |
| signingDate | Date | Date the agreement was signed | optional |

### Project Change Log

> **Source files:** `plugins/applicationCommon/grails-app/domain/com/docu/project/ProjectInfoLog.groovy`

Holds a point-in-time copy of a project's values captured when the project is created or updated, for historical tracking.

| Property | Type | Meaning | Constraints |
|----------|------|---------|-------------|
| projectId | Identifier | The project this log entry belongs to | required |
| proposalId | Text | Originating proposal reference at the time of the change | optional |
| projectCountry | Reference to Country | Country at the time of the change | — |
| projectCode | Text | Project code at the time of the change | — |
| projectRefCode | Text | Reference code at the time of the change | — |
| projectName | Text | Project name at the time of the change | — |
| projectDescription | Text | Description at the time of the change | — |
| projectShortCode | Text | Short code at the time of the change | — |
| projectSetupDate | Date | Setup date at the time of the change | — |
| projectEffectiveDate | Date | Effective date at the time of the change | — |
| projectStartDate | Date | Start date at the time of the change | — |
| projectEndDate | Date | End date at the time of the change | — |
| domainStatus | Reference to DomainStatus | Status at the time of the change | — |
| programInfo | Reference to ProgramInfo | Program at the time of the change | — |
| bookClosing | Boolean | Book-closing flag at the time of the change | — |
| parentProjectInfoId | Identifier | Parent project at the time of the change | — |
| departmentId | Identifier | Linked department at the time of the change | — |
| isIndependent | Boolean | Independence flag at the time of the change | — |
| isOverhead | Boolean | Overhead flag at the time of the change | — |
| hoType | Text | Head-office classification at the time of the change | — |
| boType | Text | Branch-office classification at the time of the change | — |
| mfProjectRefCode | Text | Microfinance reference code at the time of the change | — |
| isNgoBeuro | Boolean | NGO-bureau flag at the time of the change | — |
| beuroFromDate | Date | NGO-bureau start at the time of the change | — |
| beuroToDate | Date | NGO-bureau end at the time of the change | — |
| isTrendxProject | Boolean | Trendx flag at the time of the change | — |
| isSmartCollection | Boolean | Smart-collection flag at the time of the change | — |
| hasMfOperation | Boolean | Microfinance flag at the time of the change | — |
| projectStatus | Enum (ProjectStatus) | Operational status at the time of the change | — |
| startMonth | Number | Fiscal start month at the time of the change | — |
| endMonth | Number | Fiscal end month at the time of the change | — |
| sourceOfFundId | Identifier | Funding source at the time of the change | — |
| remarks | Text | Commitment notes at the time of the change | — |
| foreignCurrency | Text | Foreign currency at the time of the change | — |
| localCurrency | Text | Local currency at the time of the change | — |
| foreignAmount | Amount | Foreign amount at the time of the change | default 0 |
| localAmount | Amount | Local amount at the time of the change | default 0 |

### Project Office Mapping

> **Source files:** `plugins/applicationCommon/grails-app/domain/com/docu/project/ProjectOfficeMapping.groovy`

Represents the deployment of a project at a single office, with the office's area and growth classification and its group category.

| Property | Type | Meaning | Constraints |
|----------|------|---------|-------------|
| projectInfoId | Identifier | The mapped project | required |
| officeId | Identifier | The mapped office | required |
| officeTypeId | Identifier | The type of the mapped office | required |
| areaType | Enum (AreaType) | Urban or rural classification of the office | optional |
| branchGrowthType | Enum (BranchGrowthType) | Growth classification of the office | required |
| domainStatus | Reference to DomainStatus | Active/inactive status of the mapping | required |
| parentOfficeId | Identifier | Parent office in the hierarchy | optional |
| groupCategoryId | Identifier | Group category applied at the office | required |
| branchCaCode | Text | Branch code used for finance reconciliation | optional |
| parentProjectId | Identifier | Parent project for an independent branch | optional |

### Program

> **Source files:** `plugins/applicationCommon/grails-app/domain/com/docu/program/ProgramInfo.groovy`

Represents a program (or division/department) that owns a set of projects and classifies their operation and entity type.

| Property | Type | Meaning | Constraints |
|----------|------|---------|-------------|
| programCode | Text | Business code identifying the program | required |
| programRefCode | Text | External reference code | optional; up to 20 characters |
| programName | Text | Display name of the program | required, not blank; unique; up to 150 characters |
| programShortName | Text | Abbreviated name | optional; up to 150 characters |
| programDescription | Text | Free-text description | optional; up to 255 characters |
| operationType | Reference to OperationType | Type of operations the program runs | — |
| programType | Reference to ProgramType | Classification such as core, support or enterprise | — |
| entityCategory | Reference to EntityCategory | Hierarchy level such as program, division or department | — |
| hasFieldOffice | Boolean | Whether the program operates through field offices | — |
| setupDate | Date | Date the program was established | required |
| effectiveDate | Date | Date the program becomes effective | required; must be on or after the setup date |
| domainStatusId | Identifier | Active/inactive status of the program | — |

### Country

> **Source files:** `plugins/applicationCommon/grails-app/domain/com/docu/commons/Country.groovy`
> **Used by:** both the Project system (full definition) and the Group Management system (working-day calendar governs valid meeting days; scopes office feeds). The Group spec's slim view (`name`, `code`, `shortName`, `hasOperation`, `localCurrencyName`) is a subset of the full definition below.

Represents a country in which the organisation operates, with its currency and timezone settings.

| Property | Type | Meaning | Constraints |
|----------|------|---------|-------------|
| name | Text | Country name | required, not blank; up to 50 characters; unique |
| code | Text | Country code | required, not blank; up to 10 characters; unique |
| shortName | Text | Two-to-three letter code | length 2–3 |
| shortCode | Text | Abbreviated code | required |
| callingCode | Text | International dialing code | required, not blank; up to 10 characters; digits and plus only |
| hasOperation | Boolean | Whether the country has active operations | default true |
| localCurrencyName | Text | Local currency name | required, not blank; up to 50 characters |
| foreignCurrencyName | Text | Foreign currency name | required, not blank; up to 50 characters |
| minimumDenomination | Number | Smallest currency unit | required; minimum 0 |
| timeZone | Text | Country timezone | required, not blank |
| nCities | List of City | Cities belonging to the country | — |

### City

> **Source files:** `plugins/applicationCommon/grails-app/domain/com/docu/commons/City.groovy`

Represents a city belonging to a country.

| Property | Type | Meaning | Constraints |
|----------|------|---------|-------------|
| name | Text | City name | required, not blank; length 2–50 |
| description | Text | Additional city information | up to 255 characters |
| country | Reference to Country | The country the city belongs to | required |

### Domain Status

> **Source files:** `plugins/applicationCommon/grails-app/domain/com/docu/commons/DomainStatus.groovy`
> **Used by:** both the Project system (active/inactive lifecycle status on projects, mappings, programs, types) and the Group Management system (data status governing soft deletion of groups). Both specs define this entity; this is the canonical merged definition. Identifiers used by the Group domain: active=1, inactive=2.

Represents the active/inactive lifecycle status applied to many records across both systems.

| Property | Type | Meaning | Constraints |
|----------|------|---------|-------------|
| id | Identifier | Data-status identifier | — |
| statusName / name | Text | Name of the status | required; unique |
| description | Text | Description of the status | optional |

### Group Category

> **Source files:** `plugins/applicationCommon/grails-app/domain/com/docu/project/GroupCategory.groovy`

Represents a category assigned to an office within a project-office mapping (Project system) and referenced during bulk import validation.

| Property | Type | Meaning | Constraints |
|----------|------|---------|-------------|
| categoryName | Text | Category name | required, not blank; unique |
| description | Text | Category description | optional |

### Operation Type

> **Source files:** `plugins/applicationCommon/grails-app/domain/com/docu/program/OperationType.groovy`

Represents the type of operations a program runs.

| Property | Type | Meaning | Constraints |
|----------|------|---------|-------------|
| operationCode | Text | Operation type code | required |
| operationDescription | Text | Operation type description | required |

### Program Type

> **Source files:** `plugins/applicationCommon/grails-app/domain/com/docu/program/ProgramType.groovy`

Represents the classification of a program, such as core, support or enterprise.

| Property | Type | Meaning | Constraints |
|----------|------|---------|-------------|
| typeName | Text | Type name | required |
| description | Text | Type description | optional |
| domainStatus | Reference to DomainStatus | Active/inactive status of the type | required |

### Entity Category

> **Source files:** `plugins/applicationCommon/grails-app/domain/com/docu/program/EntityCategory.groovy`

Represents the hierarchy level of a program, such as program, division or department.

| Property | Type | Meaning | Constraints |
|----------|------|---------|-------------|
| entityName | Text | Category name | required |
| description | Text | Category description | optional |
| domainStatus | Reference to DomainStatus | Active/inactive status of the category | required |

### Group (Village Organization)

> **Source files:** `plugins/mf/grails-app/domain/com/docu/sbicloud/program/group/GroupInfo.groovy`

The central record representing a microfinance group within a branch and project, carrying its meeting schedule and loan/savings collection plans.

| Property | Type | Meaning | Constraints |
|----------|------|---------|-------------|
| groupCode | Identifier | Business code of the group; equals the generated identifier when created with automatic coding | Optional/blank allowed; set to the group identifier when "AUTO" |
| groupName | Text | Name of the group | Required; length 2–64; must start with a non-digit and match the permitted character pattern |
| assignedPO | Reference to EmployeeCoreInfo | The project officer currently assigned to the group | Required |
| orientationDate | Date | Date the group was oriented | Required; must be on or after groupCreationDate; must not be before the branch business day |
| groupCreationDate | Date | Date the group was formed | Required; must not be before the branch business day |
| lastPOAssignedDate | Date | Date the current project officer was assigned | Set to creation date on create; updated on PO reassignment |
| groupReferenceNumber | Text | VO reference number, generated from the branch | Optional; max 25 characters; system-generated on create |
| spotAddress | Text | Physical spot address of the group | Optional; max 255 characters |
| groupStatus | Reference to GroupStatus | Operational status of the group | Required; defaults to active on create |
| domainStatus | Reference to DomainStatus | Data status (active/inactive) governing soft deletion | Defaults to active; set to inactive on soft delete |
| closeReason | Reference to GroupCloseReason | Reason the group was closed | Optional; cleared when status set back to active |
| closingDate | Date | Date the group was closed | Optional |
| meetingDay | Reference to Day | Weekday on which the group meets | Required; must be a working day for the configured country |
| meetingTime | Text | Time of the group meeting | Required; default "10:00 AM" |
| demarcationArea | Text | Geographic demarcation of the group | Optional; max 255 characters |
| weekNumber | Number | Week-of-month index used for monthly collection scheduling | — |
| loanCollectionFrequency | Reference to CollectionFrequency | Frequency of loan collection | Required; must equal savingsCollectionFrequency |
| loanCollectionStartDate | Date | First loan collection date | Required; must not precede the business day; must fall on the meeting day; must satisfy the frequency minimum gap |
| savingsCollectionFrequency | Reference to CollectionFrequency | Frequency of savings collection | Required; must equal loanCollectionFrequency |
| savingsCollectionStartDate | Date | First savings collection date | Required; must not precede the business day; must fall on the meeting day |
| nextCollectionDate | Date | Next scheduled collection date | Optional; set to loan collection start date on create; recomputed on collection-date change |
| branchInfo | Reference to PhysicalOfficeInfo | The branch office owning the group | Set to the operator's current office on create |
| projectInfo | Reference to ProjectInfo | The microfinance project the group belongs to | Required |
| groupScannedForm | Text | File name of the scanned survey form | Optional |
| isTransferredGroup | Boolean | Whether the group was transferred from another branch | — |
| groupCategoryId | Number | Group category indicator | Default 1 (village organization) |
| voCategoryId | Number | Reference to the VO category | Optional |
| serviceTerritoryId | Number | Reference to the service territory | Optional; editable only by programme administrators |
| applicableGenderId | Enum (Applicable Gender) | The gender of members the group accepts (male=1, female=2, both=3) | Required |
| longitude | Text | Group location longitude | Optional |
| latitude | Text | Group location latitude | Optional |

### Group Status

> **Source files:** `plugins/mf/grails-app/domain/com/docu/sbicloud/setup/GroupStatus.groovy`

Lookup of operational group statuses. Its status values are listed in Domain Concepts and States.

| Property | Type | Meaning | Constraints |
|----------|------|---------|-------------|
| id | Identifier | Status identifier | Assigned |
| name | Text | Status name | Required; unique |
| description | Text | Status description | — |

### Group Close Reason

> **Source files:** `plugins/mf/grails-app/domain/com/docu/sbicloud/setup/GroupCloseReason.groovy`

Lookup of reasons a group may be closed.

| Property | Type | Meaning | Constraints |
|----------|------|---------|-------------|
| id | Identifier | Close-reason identifier | Assigned |
| name | Text | Reason name | Required; unique |
| description | Text | Reason description | — |

### VO Category

> **Source files:** `plugins/mf/grails-app/domain/com/docu/sbicloud/setup/VOCategory.groovy`

Lookup categorising the type of village organization.

| Property | Type | Meaning | Constraints |
|----------|------|---------|-------------|
| id | Identifier | VO category identifier | Assigned |
| name | Text | Category name | — |
| hasAsset | Boolean | Whether the category carries assets | — |
| hasLoan | Boolean | Whether the category carries loans | — |
| memberClassificationId | Number | Associated member classification | — |
| domainStatusId | Number | Data status of the category | — |

### Service Territory

> **Source files:** `plugins/mf/grails-app/domain/com/docu/sbicloud/setup/TerritorySetUp.groovy`

Lookup of service territories scoped to an office.

| Property | Type | Meaning | Constraints |
|----------|------|---------|-------------|
| id | Identifier | Territory identifier | Assigned |
| officeId | Number | Office the territory belongs to | — |
| territoryCode | Text | Territory code | — |
| territoryName | Text | Territory name | — |
| domainStatusId | Number | Data status of the territory | — |

### Day

> **Source files:** `plugins/applicationCommon/grails-app/domain/com/docu/commons/Day.groovy`

Weekday lookup used for the group's meeting day. Its values are listed in Domain Concepts and States.

| Property | Type | Meaning | Constraints |
|----------|------|---------|-------------|
| id | Identifier | Day identifier (ordered) | — |
| name | Text | Day name | Required; unique |
| description | Text | Day description | — |

### Collection Frequency

> **Source files:** `plugins/mf/grails-app/domain/com/docu/project/CollectionFrequency.groovy`

A project-scoped collection-frequency configuration that points to a frequency type.

| Property | Type | Meaning | Constraints |
|----------|------|---------|-------------|
| country | Reference to Country | Country the configuration belongs to | Required |
| projectInfo | Reference to ProjectInfo | Project the configuration belongs to | Required |
| frequency | Reference to Frequency | The underlying frequency type | Required |
| description | Text | Description of the configuration | Optional |
| status | Reference to DomainStatus | Data status of the configuration | — |

### Frequency

> **Source files:** `plugins/applicationCommon/grails-app/domain/com/docu/commons/Frequency.groovy`

The underlying frequency type (daily, weekly, monthly, etc.). Its values are listed in Domain Concepts and States.

| Property | Type | Meaning | Constraints |
|----------|------|---------|-------------|
| id | Identifier | Frequency identifier | Identity-generated |
| frequencyName | Text | Frequency name (e.g. Weekly, Monthly) | Required; unique |
| description | Text | Frequency description | Optional |

### Project-Officer Group History

> **Source files:** `plugins/mf/grails-app/domain/com/docu/sbicloud/program/group/EmployeeGroupHistory.groovy`

A history record created when a group's assigned project officer changes, capturing the released project officer's tenure over the group.

| Property | Type | Meaning | Constraints |
|----------|------|---------|-------------|
| officeInfoId | Number | Branch office of the group | — |
| groupInfoId | Number | The group | — |
| poInfoId | Number | The released project officer | — |
| assignedDate | Date | When the released officer was assigned | — |
| releasedDate | Date | When the officer was released | — |

### Project-Officer Member History

> **Source files:** `plugins/mf/grails-app/domain/com/docu/sbicloud/program/member/EmployeeMemberHistory.groovy`

A history record created when a member is reassigned to a new project officer as part of a group's project-officer change.

| Property | Type | Meaning | Constraints |
|----------|------|---------|-------------|
| officeInfo | Reference to PhysicalOfficeInfo | Branch office of the member | — |
| memberInfo | Reference to MemberInfo | The member | — |
| coInfo | Reference to EmployeeCoreInfo | The released project officer | — |
| assignedDate | Date | When the released officer was assigned to the member | — |
| releasedDate | Date | When the officer was released | Optional |

### Member

> **Source files:** `plugins/mf/grails-app/domain/com/docu/sbicloud/program/member/MemberInfo.groovy`

Externally owned by the member domain; referenced here to enforce member-aware guards on group gender, status, and deletion. Member status values are listed in Domain Concepts and States.

| Property | Type | Meaning | Constraints |
|----------|------|---------|-------------|
| branchInfo | Reference to PhysicalOfficeInfo | Member's branch | — |
| assignedPO | Reference to EmployeeCoreInfo | Member's assigned project officer | Reassigned when the group's officer changes |
| groupInfo | Reference to Group | The group the member belongs to | — |
| memberStatusId | Number | Member status (active, expired, etc.) | Drives active/expired member guards |
| lastPOAssignedDate | Date | When the member's current officer was assigned | Updated on reassignment |
| memberClassificationId | Number | Member classification | — |
| passbookNo | Text | Member passbook number | — |

### Project Policy

> **Source files:** `plugins/mf/grails-app/domain/com/docu/project/ProjectPolicyInfo.groovy`

Externally owned by the project domain; the microfinance policy configuration of a project. A group cannot be created or updated for a project that has no policy.

| Property | Type | Meaning | Constraints |
|----------|------|---------|-------------|
| projectInfo | Reference to ProjectInfo | The project the policy belongs to | — |
| associationType | Enum (Project Association Type) | Whether the project associates by group, member, or neither | — |
| hasLoans | Boolean | Whether the project supports loans | — |
| hasSavings | Boolean | Whether the project supports savings | — |
| isTUP | Boolean | Whether the project is an ultra-poor (TUP) project | — |
| newLoanTimeLimit | Number | Time limit for new loans | — |
| repeatLoanTimeLimit | Number | Time limit for repeat loans | — |

### Project Officer (Employee Core Info)

> **Source files:** `plugins/applicationCommon/grails-app/domain/com/docu/hr/employee/EmployeeCoreInfo.groovy`

Externally owned by the HR domain; the employee who serves as a group's project officer.

| Property | Type | Meaning | Constraints |
|----------|------|---------|-------------|
| pinNo | Text | Employee PIN number | — |
| firstName | Text | Employee first name | — |
| lastName | Text | Employee last name | — |
| genderId | Number | Employee gender | — |
| domainStatusId | Number | Data status of the employee | — |
| joiningDate | Date | Employee joining date | — |

### Branch Office (Physical Office Info)

> **Source files:** `plugins/applicationCommon/grails-app/domain/com/docu/office/PhysicalOfficeInfo.groovy`

Externally owned by the office domain; the branch that owns a group, and the type of office referenced during project-office mapping.

| Property | Type | Meaning | Constraints |
|----------|------|---------|-------------|
| officeCode | Text | Office code | — |
| officeName | Text | Office name | — |
| officeStatusId | Number | Office status | — |
| isMfOffice | Boolean | Whether the office is a microfinance office | — |
| mfBranchId | Text | Microfinance branch identifier | — |

---

## Domain Concepts and States

### Project

> **Source files:** `plugins/applicationCommon/grails-app/domain/com/docu/project/ProjectInfo.groovy`, `plugins/applicationCommon/grails-app/domain/com/docu/project/ProjectStatus.groovy`, `plugins/applicationCommon/grails-app/domain/com/docu/commons/DomainStatus.groovy`

A project carries two independent status notions: the lifecycle soft-status (active/inactive) drawn from the shared status taxonomy, and an operational status enumeration. A project participates in lists, counts and trees only while its lifecycle status is active.

**Project lifecycle status (soft-status):**

| State Name | Business Meaning |
|------------|-----------------|
| Active | The project is in use and appears in lists, counts and trees |
| Inactive | The project is retained for history but excluded from active lists and counts |
| Deprecated | The status value reserved for retired records |

**Project operational status:**

| Value | Business Meaning |
|-------|-----------------|
| ACTIVE | The project is actively operating |
| INACTIVE | The project is not currently operating but is not closed |
| CLOSE | The project is closed or completed |

**State Transitions:**

| From State | To State | Triggered by |
|------------|----------|-------------|
| (new) | Active | Creation of a project |
| Active | Active | Update of a project (status retained) |

### Group (Village Organization) Status

> **Source files:** `plugins/mf/grails-app/domain/com/docu/sbicloud/setup/GroupStatus.groovy`, `plugins/applicationCommon/src/groovy/com/docu/sbicloud/util/ApplicationConstants.groovy`

A group's operational status. The identifiers are fixed by the application: active=1, inactive=2, closed=3.

| State Name | Business Meaning |
|------------|-----------------|
| Active | The group is operational and accepts members and collections |
| Inactive | The group is not operational; may only be set when the group has no active or expired members |
| Closed | The group is closed; may only be set when the group has no active or expired members, and may carry a close reason |

**State Transitions:**

| From State | To State | Triggered by |
|------------|----------|-------------|
| (new) | Active | Group creation |
| Active | Inactive | Update setting status to inactive (no active/expired members) |
| Active | Closed | Update setting status to closed (no active/expired members) |
| Inactive / Closed | Active | Update setting status back to active (clears the close reason) |

### Data Status (Domain Status)

> **Source files:** `plugins/applicationCommon/grails-app/domain/com/docu/commons/DomainStatus.groovy`, `plugins/applicationCommon/src/groovy/com/docu/sbicloud/util/ApplicationConstants.groovy`
> **Used by:** both systems. The Project system uses this for the active/inactive lifecycle of projects and mappings; the Group Management system uses it for the soft-deletion data lifecycle of group records. Identifiers: active=1, inactive=2.

The data lifecycle status governing soft deletion and active/inactive distinction.

| State Name | Business Meaning |
|------------|-----------------|
| Active | The record is live and visible to read operations |
| Inactive | The record is soft-deleted or retired and excluded from read operations |

**State Transitions (Group domain):**

| From State | To State | Triggered by |
|------------|----------|-------------|
| (new) | Active | Group or project creation |
| Active | Inactive | Group soft deletion (no active/expired members); project deactivation |

### Area Type

> **Source files:** `plugins/applicationCommon/grails-app/domain/com/docu/office/setup/AreaType.groovy`

| Value | Business Meaning |
|-------|-----------------|
| URBAN | The mapped office serves an urban area |
| RURAL | The mapped office serves a rural area |

### Branch Growth Type

> **Source files:** `plugins/applicationCommon/grails-app/domain/com/docu/office/setup/BranchGrowthType.groovy`

| Value | Business Meaning |
|-------|-----------------|
| HIGH | High growth potential office |
| MEDIUM | Medium growth potential office |
| LOW | Low growth potential office |
| NA | Growth classification not applicable |

### Applicable Gender

> **Source files:** `plugins/applicationCommon/grails-app/domain/com/docu/project/ApplicableGender.groovy`, `plugins/applicationCommon/src/groovy/com/docu/sbicloud/util/ApplicationConstants.groovy`

The gender of members a group accepts. Identifiers: male=1, female=2, both=3.

| Value | Display Name | Business Meaning |
|-------|--------------|-----------------|
| 1 | Male | The group accepts male members only |
| 2 | Female | The group accepts female members only |
| 3 | Both | The group accepts members of any gender |

### Collection Frequency (Frequency Type)

> **Source files:** `plugins/applicationCommon/grails-app/domain/com/docu/commons/Frequency.groovy`, `plugins/applicationCommon/src/groovy/com/docu/sbicloud/util/ApplicationConstants.groovy`

The frequency at which loan and savings collections occur. Known frequency-type identifiers: weekly=2, monthly=3, bi-weekly=5, single=8.

| Frequency Name | Business Meaning | Minimum gap from group creation to first collection |
|----------------|------------------|-----------------------------------------------------|
| Daily | Collection occurs every day | At least 1 day |
| Weekly | Collection occurs weekly | Frequency-gap check disabled; date must fall on meeting day |
| Bi-Weekly | Collection occurs every two weeks | Frequency-gap check disabled; date must fall on meeting day |
| Monthly | Collection occurs monthly | First date must match the meeting day and configured week-of-month |
| Quarterly | Collection occurs every quarter | At least 84 days |
| Six Monthly | Collection occurs twice a year | At least 168 days |
| Yearly | Collection occurs annually | At least 365 days |
| Single | One-off collection | Excluded from the project frequency selection list |

### Member Status (used for member-aware guards)

> **Source files:** `plugins/applicationCommon/src/groovy/com/docu/sbicloud/util/ApplicationConstants.groovy`

Member statuses relevant to group guards. Identifiers: active=1, expired=3. A group is considered to "have active or expired members" when at least one of its members holds one of these statuses.

| Value | Display Name | Business Meaning |
|-------|--------------|-----------------|
| 1 | Active | Member is active in the group |
| 3 | Expired | Member's tenure has expired but the member still constrains the group |

### Project Association Type

> **Source files:** `plugins/mf/grails-app/domain/com/docu/project/ProjectAssociationType.groovy`

How a project associates its participants. The create and edit screens list only group-association projects.

| Value | Business Meaning |
|-------|-----------------|
| GROUP | The project organises participants into groups |
| MEMBER | The project associates participants individually |
| NotApplicable | The project has no association type |

### Application User Type

> **Source files:** `plugins/applicationCommon/grails-app/domain/com/docu/security/ApplicationUserType.groovy`

The category of the requesting user, governing project/office scoping.

| Value | Business Meaning |
|-------|-----------------|
| INTERNAL | An internal staff user, subject to project/office scoping |
| EXTERNAL | An external user, not subject to project/office scoping |
| AFFILIATE | An affiliated user |

---

## Business Rules Summary

> Rules 1–22 cover the Project system; rules 23–47 cover the Group Management system.

### Project System Rules

1. A project name must be unique across all projects.
2. A project code must be unique across all projects.
3. A project reference code must be unique across all projects (checked on creation).
4. A program must be selected on every project before it is saved.
5. A project's end date must be on or after its start date.
6. A program's effective date must be on or after its setup date.
7. On creation, a project's effective date is forced equal to its start date and its setup date is set to the current system date.
8. A newly created project defaults to active lifecycle status; when no country is supplied it defaults to Bangladesh.
9. An absent source-of-fund defaults to none, and absent foreign/local amounts default to zero.
10. A project-office mapping must have a branch-growth type and a group category.
11. An office-mapping update is rejected if the named project does not exist.
12. A bulk-import row is rejected if its office code is blank, does not resolve to an office, or its group category is not valid for that office.
13. A bulk-import row for an office already mapped to the project replaces the existing mapping and carries forward its parent office, rather than duplicating it.
14. Project name, code, setup date, effective date, start date, end date, country and the microfinance-operation flag are all mandatory fields.
15. Project lists, the operational running-project count, and the selection tree include only active projects.
16. The running-project count is office-scoped: a head office counts all running projects (a country head office only within its country), other offices count only projects mapped to their permitted offices.
17. The program-and-project tree is filtered to the actor's authorised programs/projects unless the actor's office is a top-level institutional, country-head, or head office; it shows only core microfinance, loan-bearing projects.
18. When creating a project at the global head office the project code is left blank for manual entry; otherwise a country-scoped project code is generated.
19. Creating, updating, or mapping a project always refreshes the relevant cache and, on project save, evicts the accounting project-setup and collection-application project caches.
20. Every project save forwards the project to the human-resource integration service and asynchronously pushes the project and its department to outbound endpoints; a create fires a create-project notification and an update fires an update-project notification.
21. Creation, update, mapping update, office-wise mapping update, and bulk import must be submitted as form submissions; other transport methods are rejected.
22. Any persistence failure surfaces the generic message "Exception occurred in database operation" rather than the raw error.

### Group Management System Rules

23. A group is created as active (both operational status and data status active) within the operator's current branch office and the selected project.
24. A group can only be created or updated when the selected project has a defined policy.
25. Within a project and branch, the reserved VO name "Wash" may exist at most once; a duplicate "Wash" name is rejected on create and on update.
26. The orientation date, group creation date, loan collection start date, and savings collection start date must each be on or after the branch business day.
27. The orientation date must be on or after the group creation date.
28. The meeting day must be a working day for the configured country.
29. Both the loan collection start date and the savings collection start date must fall on the group's meeting day.
30. The loan collection frequency and savings collection frequency must be identical.
31. Minimum gap between group creation date and loan collection start date by frequency: Daily ≥ 1 day, Quarterly ≥ 84 days, Six-Monthly ≥ 168 days, Yearly ≥ 365 days; Weekly and Bi-Weekly gap checks are currently disabled.
32. For monthly frequency, the collection start date must coincide with the meeting day on the configured week-of-month.
33. Bi-weekly next-collection recomputation advances dates in 14-day steps until not earlier than the business day.
34. A group's applicable gender cannot be changed away from "both" while the group has active or expired members of the previous gender.
35. A group's status cannot be set to inactive or closed, and a group cannot be deleted, while it has active or expired members.
36. Group deletion is always a soft delete (data status set to inactive, version incremented); groups are never physically removed.
37. On a project-officer change, the system records release-history entries for the group and each member and reassigns every member to the new officer, all in one atomic transaction.
38. A group's collection start dates cannot be changed on a day that is the group's own current collection day.
39. New loan and savings collection dates must be on or after the group creation date and must fall on the group's meeting day.
40. When created with automatic coding, the group code equals the generated group identifier, and a VO reference number is generated from the branch office.
41. All persisted group changes are guarded by optimistic locking; a stale version is rejected as a concurrent-edit conflict.
42. Internal users may only view or edit groups within their authorised project and office scope, unless they hold the microfinance or finance programme administrator role; external users are unscoped.
43. Only microfinance or finance programme administrators may change a group's service territory.
44. The group grid and autocomplete feeds return only active-data-status groups, scoped to the requester's authorised offices and projects.
45. The automatically-closeable group list returns only active-status groups with no active members, no outstanding loan balance, and no savings balance.
46. The project collection-frequency list excludes the single (one-off) frequency.
47. Group creation, edit, save, and update require an open branch business day; save and update accept only POST submissions and the main listing only GET.

### Cross-System Rules

48. A group belongs to exactly one project; the project must exist in the Project system and must carry a defined policy before any group can be created or updated against it.
49. Groups are associated with branch offices that are themselves subject to project-office mappings maintained by the Project system; the Group Management system reads office reference data from the shared office domain.

---

## Open Questions

### Project System

No unresolved `[NEEDS REVIEW]` items remain. All referenced action bodies, validators, enums, message keys, and the generic-exception and plugin-name constants were located and read during extraction.

### Group Management System

No unresolved `[NEEDS REVIEW]` items remained after extraction. The frequency-gap and monthly-week-of-month rejection branches reference message keys (`groupInfo.loanCollectionStartDate.weekNo.error` and the per-frequency `dateDifference*` keys) that are confirmed absent from the microfinance message catalogue; the conditions are documented above and the absence of catalogue text is stated as fact rather than raised as a question.

---

## Extraction Summary

### Project System

| Metric | Count |
|--------|-------|
| Controllers processed | 1 (`ProjectController`) |
| Action services processed | 11 (`ListProjectAction`, `ShowProjectAction`, `AjaxProjectAction`, `CreateProjectAction`, `UpdateProjectAction`, `EditProjectAction`, `ShowOfficeMappingAction`, `UpdateProjectOfficeMappingAction`, `ShowProjectMappingAction`, `UpdateOfficeWiseProjectMappingAction`, `CreateBulkProjectMappingAction`) |
| Quartz jobs processed | 0 |
| Rabbit / Mercure actions processed | 0 |
| Plugins traced | 1 (`applicationCommon`) |
| Total EARS statements | 92 |
| Event-Driven (`When` + `After`) | 52 |
| State-Driven (`While`) | 8 |
| Unwanted Behaviour (`If`) | 24 |
| Optional (`Where`) | 1 |
| Ubiquitous (`The Project system shall`) | 7 |
| Complex (`While … when`) | 0 |
| [NEEDS REVIEW] items (residual, unresolved) | 0 |
| [UNRESOLVED] items | 0 |
| [DISABLED] items | 0 |
| Rule-sites inventoried | 53 |
| Rule-sites covered by a statement | 53 |
| Rule-sites uncovered | 0 |

**Per-file coverage ledger:**
- `ProjectService.groovy` (1603 LOC): 26 rule-sites · 26 accounted · 0 uncovered

Action-service rejection/branch rule-sites (each file < 500 LOC, read in full): `CreateProjectAction` 6 · `UpdateProjectAction` 4 · `CreateBulkProjectMappingAction` 6 · `UpdateProjectOfficeMappingAction` 3 · `UpdateOfficeWiseProjectMappingAction` 2 · `AjaxProjectAction` 6 — all accounted, 0 uncovered.

**Extraction completed:** Sunday, 14 June 2026

### Group Management System

| Metric | Count |
|--------|-------|
| Controllers processed | 1 (`GroupInfoController`) |
| Action services processed | 8 (`CreateGroupInfoAction`, `UpdateGroupInfoAction`, `DeleteGroupInfoAction`, `ChangeCollectionStartDateAction`, `ShowGroupInfoAction`, `EditGroupInfoAction`, `ListGroupInfoAction`, `AjaxGroupInfoAction`) |
| Quartz jobs processed | 0 |
| Rabbit / Mercure actions processed | 0 |
| Plugins traced | 3 (`mf`, `applicationCommon`, plus shared HR/office/project domains) |
| Total EARS statements | ~108 |
| Event-Driven (`When` + `After`) | ~31 |
| State-Driven (`While`) | ~7 |
| Unwanted Behaviour (`If`) | ~58 |
| Optional (`Where`) | ~3 |
| Ubiquitous (`The Group Management system shall`) | ~9 |
| Complex (`While … when`) | 0 |
| [NEEDS REVIEW] items (residual, unresolved) | 0 |
| [UNRESOLVED] items | 0 |
| [DISABLED] items | 1 (Weekly/Bi-Weekly creation frequency-gap day checks are commented out and not enforced) |

**Per-file coverage ledger:**
- `GroupService.groovy` (2346 LOC): targeted-method protocol — `save`, `saveGroupInfo`, `updateGroup(Map)`, `getGroupListJson`, `getActiveGroupList`, `readGroup`, `listOfCollectionFrequencyByProject`, `getAllActiveGroupHavingNoMember`, `isGroupNameExists`, `groupCountHasLoanByGroupId`, `groupCountHasSavingsByGroupId`, `readGroupInfo`, `updateGroup(GroupInfo)`, `updateGroupSafeQuery` — all read; rule-sites accounted.
- `MemberService.groovy` (7104 LOC): targeted methods `readMemberListByGroup`, `isMemberExistsForGroup`, `hasActiveAndExpiredMemberWithPreviousGender` read; member active/expired and active-data-status filters accounted.
- `AjaxOfficeInfoAction.groovy` (841 LOC): only the controller-invoked office-feed methods traced.

**Extraction completed:** Friday, 12 June 2026

---

## Review by Developer — Project System (code)

<!-- Developer: after reviewing the Project system spec against the codebase, list source-code references to rules
     that are MISSING from this spec. One finding per line. Pointer precision helps the agent:
       - [ ] `File.groovy#method`           — what rule is missing   (most precise)
       - [ ] `File.groovy:120-145`          — what rule is missing
       - [ ] `File.groovy`                  — what rule is missing   (whole file)
       - [ ] a plain note with no pointer   (agent auto-locates from the description)
     Optionally force placement by appending:  → Module: <Module> › <Subsection> -->

_None yet — add findings above._

---

## Review by Developer — Project System (business requirements)

<!-- Developer: list business decisions/requirements that need a human answer (no code expected).
     One per line; these become [NEEDS REVIEW] Open Questions.
       - [ ] <the business decision or requirement needed, one sentence>   | context: `File.groovy`
     Optionally append:  → Module: <Module> › <Subsection> -->

_None yet — add findings above._

---

## Review by Developer — Group Management System (code)

<!-- Developer: after reviewing the Group Management system spec against the codebase, list source-code references to rules
     that are MISSING from this spec. One finding per line. Same pointer conventions as above. -->

_None yet — add findings above._

---

## Review by Developer — Group Management System (business requirements)

<!-- Developer: list business decisions/requirements that need a human answer (no code expected).
     One per line; these become [NEEDS REVIEW] Open Questions. -->

_None yet — add findings above._
