# Member Admission Approval — Endpoint Catalog

> **Built from:** `docs/ears/member/MemberAdmissionApproval-EARS-Specification.md`
> **Date:** 2026-06-14
> **Scope:** Every endpoint / entry point documented by the source EARS specification, with the source file for each.
> **Method note:** The catalog distinguishes externally invokable **controller actions** (HTTP endpoints) from the internal **action-service and validation entry points** that the spec documents as part of the same call chain. Source files are taken verbatim from the spec's `> **Source Entry Point(s):**` header, `> **Entry Points:**` / `> **Source files:**` module annotations.

---

## 1. HTTP Controller Endpoints

These are the externally invokable Grails controller actions documented by the spec.

| # | Endpoint (controller action) | Operation | Module documented under | Source file |
|---|------------------------------|-----------|--------------------------|-------------|
| 1 | `DcsMemberAdmissionBufferController#approveMemberAdmission` | Approve a buffered new-member admission request from the DCS channel | Member Admission Approval › New-Admission Approval Flow | `plugins/mf/grails-app/controllers/com/docu/sbicloud/program/dcs/DcsMemberAdmissionBufferController.groovy` |
| 2 | `DcsMemberAdmissionBufferController#approveMemberUpdate` | Approve a buffered member-update request from the DCS channel | Member Admission Approval › Member-Update Approval Flow | `plugins/mf/grails-app/controllers/com/docu/sbicloud/program/dcs/DcsMemberAdmissionBufferController.groovy` |

---

## 2. Action-Service Entry Points

The controller actions delegate to these action services, documented by the spec as the primary flow entry points.

| # | Entry point (action service) | Invoked by | Module documented under | Source file |
|---|------------------------------|------------|--------------------------|-------------|
| 3 | New-admission approval action (`CreateMemberAdmissionApiAction`) | `approveMemberAdmission` | Member Admission Approval › New-Admission Approval Flow | `plugins/mf/src/groovy/com/docu/sbicloud/program/dcs/CreateMemberAdmissionApiAction.groovy` |
| 4 | Member-update approval action (`UpdateMemberAdmissionApiAction`) | `approveMemberUpdate` | Member Admission Approval › Member-Update Approval Flow | `plugins/mf/src/groovy/com/docu/sbicloud/program/dcs/UpdateMemberAdmissionApiAction.groovy` |

---

## 3. Internal Service Entry Points (validation, sub-validators, integrations)

The spec documents these as `> **Entry Points:**` "invoked internally by the approval flows above." They are not directly HTTP-exposed but are the documented entry points of their respective modules.

| # | Internal entry point | Module documented under | Source file(s) |
|---|----------------------|--------------------------|----------------|
| 5 | New-admission validation (required-field, format, business) | Member Admission Validation Rules | `plugins/mf/grails-app/services/com/docu/api/feeder/MemberApiService.groovy`, `plugins/mf/grails-app/services/com/docu/api/feeder/CommonApiService.groovy` |
| 6 | Member-update validation (required-field, format, business) | Member Admission Validation Rules | `plugins/mf/grails-app/services/com/docu/api/feeder/MemberApiUpdateService.groovy`, `plugins/mf/grails-app/services/com/docu/api/feeder/CommonApiService.groovy` |
| 7 | Per-party identity-document structure validation | Member Admission Validation Rules › Identity-Document Structure Validation | `plugins/mf/grails-app/services/com/docu/api/feeder/CommonApiService.groovy` |
| 8 | Identity uniqueness check (cross-organisation de-duplication) | Sub-Validators › Identity Uniqueness Check | `plugins/applicationCommon/grails-app/services/com/docu/rest/DeDupeRestWebService.groovy`, `plugins/mf/grails-app/services/com/docu/api/feeder/MemberApiService.groovy` |
| 9 | DCS member channel calls (retrieve buffer; post approve / reject / update-messages) | Cross-Plugin and External Integrations › DCS Member Channel | `plugins/mf/grails-app/services/com/docu/api/feeder/CommonApiService.groovy` |
| 10 | Cross-organisation de-duplication bridge (search-by-identity-card) | Cross-Plugin and External Integrations › Cross-Organisation De-Duplication Bridge | `plugins/applicationCommon/grails-app/services/com/docu/rest/DeDupeRestWebService.groovy` |

---

## Summary

- **HTTP controller endpoints documented:** 2 (both on `DcsMemberAdmissionBufferController`)
- **Action-service entry points documented:** 2 (`CreateMemberAdmissionApiAction`, `UpdateMemberAdmissionApiAction`)
- **Internal service entry points documented:** 6 (across `MemberApiService`, `MemberApiUpdateService`, `CommonApiService`, `DeDupeRestWebService`)
- **Plugins traced:** `mf`, `applicationCommon`
- **Distinct source files referenced as entry points:**
  - `plugins/mf/grails-app/controllers/com/docu/sbicloud/program/dcs/DcsMemberAdmissionBufferController.groovy`
  - `plugins/mf/src/groovy/com/docu/sbicloud/program/dcs/CreateMemberAdmissionApiAction.groovy`
  - `plugins/mf/src/groovy/com/docu/sbicloud/program/dcs/UpdateMemberAdmissionApiAction.groovy`
  - `plugins/mf/grails-app/services/com/docu/api/feeder/MemberApiService.groovy`
  - `plugins/mf/grails-app/services/com/docu/api/feeder/MemberApiUpdateService.groovy`
  - `plugins/mf/grails-app/services/com/docu/api/feeder/CommonApiService.groovy`
  - `plugins/applicationCommon/grails-app/services/com/docu/rest/DeDupeRestWebService.groovy`

### Note on skill fit

The invoked skill (`merge-ears`) is designed to **merge two or more EARS files into one**, and requires at least two inputs. The requested task is a **single-file endpoint catalog**, which the merge workflow does not directly cover. I therefore applied the skill's structure-awareness (parsing the title front-matter `Source Entry Point(s)`, the `## Module:` headings, and their `> **Entry Points:**` / `> **Source files:**` annotations) to produce the catalog the user asked for. The bundled merge self-check script (`check_merged_spec.py`) was not run because it validates merged-spec invariants, which do not apply to a catalog output.
