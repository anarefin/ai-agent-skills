# EARS Action / Endpoint Catalog

> **Scope:** Every Grails action (controller entry point) described across two EARS specifications.
> **Source EARS files:**
> - `docs/ears/GroupCreation-EARS-Specification.md`
> - `docs/ears/member/MemberDomain-EARS-Specification.md`
> **Built on:** 2026-06-14
> **Method:** Extracted from each spec's front-matter `Source Entry Point(s)` line and each `## Module:` / `###` subsection's `> **Entry Points:**` and `> **Source files:**` annotations. Controller actions are the listed Grails entry points; the backing action service / API service that implements each flow is named in the "Backing service / action class" column. Source files are project-relative paths exactly as cited in the EARS specs.

---

## 1. GroupCreation-EARS-Specification.md

> **Plugin / domain:** `mf` — Microfinance Group (VO) Creation
> **Controller:** `plugins/mf/grails-app/controllers/com/docu/sbicloud/program/group/GroupInfoController.groovy`
> Scope is limited to the **create** lifecycle of a microfinance group; the spec explicitly covers the `create` and `save` actions only.

| Controller action | Module / Domain | Backing service / action class | Controller source file | EARS source file |
|---|---|---|---|---|
| `create` (load group creation form) | Group Creation › Group Creation Form | (controller-resolved reference data) | `plugins/mf/grails-app/controllers/com/docu/sbicloud/program/group/GroupInfoController.groovy` | `docs/ears/GroupCreation-EARS-Specification.md` |
| `save` (validate + persist new group) | Group Creation › Group Creation and Persistence; Survey Form Handling; Group Creation Validation Rules | `plugins/mf/src/groovy/com/docu/sbicloud/program/groupinfo/action/CreateGroupInfoAction.groovy`; `plugins/mf/grails-app/services/com/docu/sbicloud/program/group/GroupService.groovy` | `plugins/mf/grails-app/controllers/com/docu/sbicloud/program/group/GroupInfoController.groovy` | `docs/ears/GroupCreation-EARS-Specification.md` |

**Internal (non-controller) rule engine referenced by `save`:** `Group Creation Validation Rules` module — invoked internally by the group save flow, no separate controller action. Source: `CreateGroupInfoAction.groovy`, `GroupService.groovy`, `plugins/applicationCommon/grails-app/domain/com/docu/project/ProjectPolicyInfo.groovy`.

---

## 2. MemberDomain-EARS-Specification.md

> **Plugins / domains:** `mf` (microfinance member lifecycle, DCS admission approval) with cross-plugin reference into `applicationCommon`.
> **Controllers:**
> - `plugins/mf/grails-app/controllers/com/docu/sbicloud/program/member/MemberInfoController.groovy` (back-office channel)
> - `plugins/mf/grails-app/controllers/com/docu/sbicloud/program/dcs/DcsMemberAdmissionBufferController.groovy` (DCS field-collection approval channel)

### 2a. Back-office channel — `MemberInfoController`

The spec describes these flows as "Grails controller actions dispatching to legacy action classes (preCondition / execute / postCondition)." Each flow below corresponds to a controller action backed by the named legacy action class.

| Controller action (flow) | Module / Domain | Backing action class | Controller source file | EARS source file |
|---|---|---|---|---|
| Member registration (form load + save) | Member Management › Member Registration | `plugins/mf/src/groovy/com/docu/sbicloud/program/member/CreateMemberInfoAction.groovy` | `MemberInfoController.groovy` | `docs/ears/member/MemberDomain-EARS-Specification.md` |
| Member edit-form loading | Member Management › Member Edit Form Loading | `plugins/mf/src/groovy/com/docu/sbicloud/program/member/EditMemberInfoAction.groovy` | `MemberInfoController.groovy` | `docs/ears/member/MemberDomain-EARS-Specification.md` |
| Member profile update | Member Management › Member Profile Update | `plugins/mf/src/groovy/com/docu/sbicloud/program/member/UpdateMemberInfoAction.groovy` | `MemberInfoController.groovy` | `docs/ears/member/MemberDomain-EARS-Specification.md` |
| Member deletion (logical) | Member Management › Member Deletion | `plugins/mf/src/groovy/com/docu/sbicloud/program/member/DeleteMemberInfoAction.groovy` | `MemberInfoController.groovy` | `docs/ears/member/MemberDomain-EARS-Specification.md` |
| Member family / nominee information | Member Management › Member Family Information | `plugins/mf/src/groovy/com/docu/sbicloud/program/member/CreateMemberFamilyAction.groovy`; `plugins/mf/src/groovy/com/docu/sbicloud/program/member/UpdateFamilyInfoAction.groovy` | `MemberInfoController.groovy` | `docs/ears/member/MemberDomain-EARS-Specification.md` |
| Member asset information | Member Management › Member Asset Information | `plugins/mf/src/groovy/com/docu/sbicloud/program/member/UpdateAssetInfoAction.groovy` | `MemberInfoController.groovy` | `docs/ears/member/MemberDomain-EARS-Specification.md` |
| Member signature | Member Management › Member Signature | `plugins/mf/src/groovy/com/docu/sbicloud/program/member/UpdateSignatureAction.groovy` | `MemberInfoController.groovy` | `docs/ears/member/MemberDomain-EARS-Specification.md` |
| Member photo | Member Management › Member Photo | `plugins/mf/src/groovy/com/docu/sbicloud/program/member/CreateMemberPhotoAction.groovy` | `MemberInfoController.groovy` | `docs/ears/member/MemberDomain-EARS-Specification.md` |
| Membership documents | Member Management › Membership Documents | `plugins/mf/src/groovy/com/docu/sbicloud/program/member/UpdateMembershipDocumentAction.groovy` | `MemberInfoController.groovy` | `docs/ears/member/MemberDomain-EARS-Specification.md` |
| Member viewing (show) | Member Management › Member Viewing and Listing | `plugins/mf/src/groovy/com/docu/sbicloud/program/member/ShowMemberInfoAction.groovy` | `MemberInfoController.groovy` | `docs/ears/member/MemberDomain-EARS-Specification.md` |
| Member listing + reference-data lookups (list / member categories / savings products / minimum target amount / passbook availability / districts / sub-districts) | Member Management › Member Viewing and Listing | `plugins/mf/src/groovy/com/docu/sbicloud/program/member/ListMemberInfoAction.groovy` | `MemberInfoController.groovy` | `docs/ears/member/MemberDomain-EARS-Specification.md` |
| Member activation (listing + activate) | Member Activation | `plugins/mf/src/groovy/com/docu/sbicloud/program/member/SaveMemberActivationAction.groovy` | `MemberInfoController.groovy` | `docs/ears/member/MemberDomain-EARS-Specification.md` |
| Member project-officer reassignment (non-group members) | Member Project-Officer Reassignment | `plugins/mf/src/groovy/com/docu/sbicloud/program/member/ChangeNonGroupMemberPoAction.groovy` | `MemberInfoController.groovy` | `docs/ears/member/MemberDomain-EARS-Specification.md` |
| Real-time member validation (AJAX identity / wallet / guarantor / other-identity / insurance-age checks) | Member Validation Rules | `plugins/mf/src/groovy/com/docu/sbicloud/program/member/AjaxMemberInfoAction.groovy` | `MemberInfoController.groovy` | `docs/ears/member/MemberDomain-EARS-Specification.md` |

> **Note:** The spec describes the `MemberInfoController` flows by behaviour rather than naming each literal Grails action method (except where it dispatches to the legacy action classes above). The flow groupings reflect the spec's `###` subsections and `> **Source files:**` annotations. The Member Viewing and Listing subsection additionally documents several reference-data/AJAX read endpoints (member categories, savings products, minimum target amount, passbook availability, districts, sub-districts) backed by `ListMemberInfoAction`.

### 2b. DCS field-collection approval channel — `DcsMemberAdmissionBufferController`

The spec names these controller actions explicitly.

| Controller action | Module / Domain | Backing action class | Controller source file | EARS source file |
|---|---|---|---|---|
| `approveMemberAdmission` | Member Admission Approval › New-Admission Approval Flow | `plugins/mf/src/groovy/com/docu/sbicloud/program/dcs/CreateMemberAdmissionApiAction.groovy` | `plugins/mf/grails-app/controllers/com/docu/sbicloud/program/dcs/DcsMemberAdmissionBufferController.groovy` | `docs/ears/member/MemberDomain-EARS-Specification.md` |
| `approveMemberUpdate` | Member Admission Approval › Member-Update Approval Flow | `plugins/mf/src/groovy/com/docu/sbicloud/program/dcs/UpdateMemberAdmissionApiAction.groovy` | `plugins/mf/grails-app/controllers/com/docu/sbicloud/program/dcs/DcsMemberAdmissionBufferController.groovy` | `docs/ears/member/MemberDomain-EARS-Specification.md` |

### 2c. Internal modules (no controller action — invoked by the flows above)

These modules in the Member spec describe validation/integration logic, not controller entry points. They are listed for completeness and to show what each action delegates to.

| Module / Domain | Kind | Source files | EARS source file |
|---|---|---|---|
| Member Admission Validation Rules (required-field, format, identity-structure, nominee, business validation for new admission and update) | Internal validation services — invoked by `approveMemberAdmission` / `approveMemberUpdate` | `plugins/mf/grails-app/services/com/docu/api/feeder/MemberApiService.groovy`; `plugins/mf/grails-app/services/com/docu/api/feeder/MemberApiUpdateService.groovy`; `plugins/mf/grails-app/services/com/docu/api/feeder/CommonApiService.groovy` | `docs/ears/member/MemberDomain-EARS-Specification.md` |
| Sub-Validators (cross-organisation identity de-duplication, identity uniqueness check) | Internal validation service | `plugins/mf/grails-app/services/com/docu/api/feeder/MemberApiService.groovy`; `plugins/mf/grails-app/services/com/docu/api/feeder/MemberApiUpdateService.groovy`; `plugins/applicationCommon/grails-app/services/com/docu/rest/DeDupeRestWebService.groovy` | `docs/ears/member/MemberDomain-EARS-Specification.md` |
| Cross-Plugin and External Integrations (DCS member channel bridge, cross-organisation de-duplication bridge) | Internal integration services | `plugins/mf/grails-app/services/com/docu/api/feeder/CommonApiService.groovy`; `plugins/applicationCommon/grails-app/services/com/docu/rest/DeDupeRestWebService.groovy`; plus the member/DCS action classes already listed above | `docs/ears/member/MemberDomain-EARS-Specification.md` |

---

## Summary

| EARS source file | Controllers | Distinct controller actions / flows | Internal-only modules |
|---|---|---|---|
| `docs/ears/GroupCreation-EARS-Specification.md` | 1 (`GroupInfoController`) | 2 (`create`, `save`) | 1 (Group Creation Validation Rules) |
| `docs/ears/member/MemberDomain-EARS-Specification.md` | 2 (`MemberInfoController`, `DcsMemberAdmissionBufferController`) | 16 (14 back-office flows + `approveMemberAdmission` + `approveMemberUpdate`) | 3 (Admission Validation Rules, Sub-Validators, Cross-Plugin & External Integrations) |
| **Total** | **3 controllers** | **18 actions / flows** | **4 internal modules** |

> All actions belong to the `mf` (microfinance) plugin. Some backing validation/integration services and reference entities live in `applicationCommon`. Action names shown literally where the spec names them (`create`, `save`, `approveMemberAdmission`, `approveMemberUpdate`); the remaining `MemberInfoController` rows are flow-level groupings taken from the spec's module subsections, since that spec documents those entry points by behaviour and by their backing legacy action class rather than by literal Grails action method name.
