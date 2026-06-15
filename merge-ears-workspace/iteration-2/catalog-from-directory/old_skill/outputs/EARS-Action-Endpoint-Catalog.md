# EARS Action / Endpoint Catalog

> **Scope:** Every action / endpoint described by the EARS specifications under `docs/ears/`
> (including the `member/` subfolder).
> **Source specifications cataloged (4):**
> - `docs/ears/GroupCreation-EARS-Specification.md`
> - `docs/ears/member/MemberAdmissionApproval-EARS-Specification.md`
> - `docs/ears/member/MemberDomain-EARS-Specification.md`
> - `docs/ears/member/MemberManagement-EARS-Specification-Resolved.md`
> **Built on:** 14 June 2026
> **Note:** "Action / endpoint" rows are the distinct operations (controller actions, action-service
> flows, and validation / integration entry points) described in each spec's `## Module:` sections
> and their `###` subsections. The **Source file(s)** column carries the literal paths from each
> subsection's `> **Source files:**` annotation. The **Spec(s)** column names every input
> specification that describes that action; where the same action is documented in more than one spec
> the rows are merged and all source specs are listed.

---

## Catalog

| # | Action / Endpoint | Module | Source file(s) | Spec(s) |
|---|-------------------|--------|----------------|---------|
| 1 | Group Creation Form (`create` action) | Group Creation | `plugins/mf/grails-app/controllers/com/docu/sbicloud/program/group/GroupInfoController.groovy` | GroupCreation |
| 2 | Group Creation and Persistence (`save` action) | Group Creation | `plugins/mf/src/groovy/com/docu/sbicloud/program/groupinfo/action/CreateGroupInfoAction.groovy`, `plugins/mf/grails-app/services/com/docu/sbicloud/program/group/GroupService.groovy` | GroupCreation |
| 3 | Survey Form Handling (post-save relocation) | Group Creation | `plugins/mf/src/groovy/com/docu/sbicloud/program/groupinfo/action/CreateGroupInfoAction.groovy` | GroupCreation |
| 4 | Group Creation Validation — Project Policy Requirement | Group Creation Validation Rules | `plugins/mf/src/groovy/com/docu/sbicloud/program/groupinfo/action/CreateGroupInfoAction.groovy` | GroupCreation |
| 5 | Group Creation Validation — Reserved Group Name Uniqueness | Group Creation Validation Rules | `plugins/mf/src/groovy/com/docu/sbicloud/program/groupinfo/action/CreateGroupInfoAction.groovy`, `plugins/mf/grails-app/services/com/docu/sbicloud/program/group/GroupService.groovy` | GroupCreation |
| 6 | Group Creation Validation — Business-Day Date Guards | Group Creation Validation Rules | `plugins/mf/src/groovy/com/docu/sbicloud/program/groupinfo/action/CreateGroupInfoAction.groovy` | GroupCreation |
| 7 | Group Creation Validation — Frequency-Specific Collection Start Gap | Group Creation Validation Rules | `plugins/mf/src/groovy/com/docu/sbicloud/program/groupinfo/action/CreateGroupInfoAction.groovy`, `plugins/applicationCommon/src/groovy/com/docu/sbicloud/util/ApplicationConstants.groovy`, `plugins/applicationCommon/grails-app/services/com/docu/commons/InternationalizationService.groovy` | GroupCreation |
| 8 | Group Creation Validation — Meeting Day and Frequency Alignment | Group Creation Validation Rules | `plugins/mf/src/groovy/com/docu/sbicloud/program/groupinfo/action/CreateGroupInfoAction.groovy` | GroupCreation |
| 9 | Group Creation Validation — Domain Validation | Group Creation Validation Rules | `plugins/mf/src/groovy/com/docu/sbicloud/program/groupinfo/action/CreateGroupInfoAction.groovy`, `plugins/mf/grails-app/domain/com/docu/sbicloud/program/group/GroupInfo.groovy` | GroupCreation |
| 10 | Member Registration (registration form + `save`/`create`) | Member Management | `plugins/mf/src/groovy/com/docu/sbicloud/program/member/CreateMemberInfoAction.groovy`, `plugins/mf/grails-app/controllers/com/docu/sbicloud/program/member/MemberInfoController.groovy` | MemberDomain, MemberManagement |
| 11 | Member Edit Form Loading | Member Management | `plugins/mf/src/groovy/com/docu/sbicloud/program/member/EditMemberInfoAction.groovy`, `plugins/mf/grails-app/controllers/com/docu/sbicloud/program/member/MemberInfoController.groovy` | MemberDomain, MemberManagement |
| 12 | Member Profile Update | Member Management | `plugins/mf/src/groovy/com/docu/sbicloud/program/member/UpdateMemberInfoAction.groovy`, `plugins/mf/grails-app/controllers/com/docu/sbicloud/program/member/MemberInfoController.groovy` | MemberDomain, MemberManagement |
| 13 | Member Deletion | Member Management | `plugins/mf/src/groovy/com/docu/sbicloud/program/member/DeleteMemberInfoAction.groovy`, `plugins/mf/grails-app/controllers/com/docu/sbicloud/program/member/MemberInfoController.groovy` | MemberDomain, MemberManagement |
| 14 | Member Family Information (create + update) | Member Management | `plugins/mf/src/groovy/com/docu/sbicloud/program/member/CreateMemberFamilyAction.groovy`, `plugins/mf/src/groovy/com/docu/sbicloud/program/member/UpdateFamilyInfoAction.groovy`, `plugins/mf/grails-app/controllers/com/docu/sbicloud/program/member/MemberInfoController.groovy` | MemberDomain, MemberManagement |
| 15 | Member Asset Information | Member Management | `plugins/mf/src/groovy/com/docu/sbicloud/program/member/UpdateAssetInfoAction.groovy`, `plugins/mf/grails-app/controllers/com/docu/sbicloud/program/member/MemberInfoController.groovy` | MemberDomain, MemberManagement |
| 16 | Member Signature | Member Management | `plugins/mf/src/groovy/com/docu/sbicloud/program/member/UpdateSignatureAction.groovy`, `plugins/mf/grails-app/controllers/com/docu/sbicloud/program/member/MemberInfoController.groovy` | MemberDomain, MemberManagement |
| 17 | Member Photo | Member Management | `plugins/mf/src/groovy/com/docu/sbicloud/program/member/CreateMemberPhotoAction.groovy`, `plugins/mf/grails-app/controllers/com/docu/sbicloud/program/member/MemberInfoController.groovy` | MemberDomain, MemberManagement |
| 18 | Membership Documents | Member Management | `plugins/mf/src/groovy/com/docu/sbicloud/program/member/UpdateMembershipDocumentAction.groovy`, `plugins/mf/grails-app/controllers/com/docu/sbicloud/program/member/MemberInfoController.groovy` | MemberDomain, MemberManagement |
| 19 | Member Viewing and Listing (show + list + AJAX lookups) | Member Management | `plugins/mf/src/groovy/com/docu/sbicloud/program/member/ShowMemberInfoAction.groovy`, `plugins/mf/src/groovy/com/docu/sbicloud/program/member/ListMemberInfoAction.groovy`, `plugins/mf/grails-app/controllers/com/docu/sbicloud/program/member/MemberInfoController.groovy` | MemberDomain, MemberManagement |
| 20 | Member Activation (listing + activate) | Member Activation | `plugins/mf/src/groovy/com/docu/sbicloud/program/member/SaveMemberActivationAction.groovy`, `plugins/mf/grails-app/controllers/com/docu/sbicloud/program/member/MemberInfoController.groovy` | MemberDomain, MemberManagement |
| 21 | Member Project-Officer Reassignment | Member Project-Officer Reassignment | `plugins/mf/src/groovy/com/docu/sbicloud/program/member/ChangeNonGroupMemberPoAction.groovy`, `plugins/mf/grails-app/controllers/com/docu/sbicloud/program/member/MemberInfoController.groovy` | MemberDomain, MemberManagement |
| 22 | Member Validation Rules (real-time AJAX checks) | Member Validation Rules | `plugins/mf/src/groovy/com/docu/sbicloud/program/member/AjaxMemberInfoAction.groovy`, `plugins/mf/grails-app/controllers/com/docu/sbicloud/program/member/MemberInfoController.groovy` | MemberDomain, MemberManagement |
| 23 | New-Admission Approval Flow (`approveMemberAdmission` action) | Member Admission Approval | `plugins/mf/grails-app/controllers/com/docu/sbicloud/program/dcs/DcsMemberAdmissionBufferController.groovy`, `plugins/mf/src/groovy/com/docu/sbicloud/program/dcs/CreateMemberAdmissionApiAction.groovy` | MemberAdmissionApproval, MemberDomain |
| 24 | Member-Update Approval Flow (`approveMemberUpdate` action) | Member Admission Approval | `plugins/mf/grails-app/controllers/com/docu/sbicloud/program/dcs/DcsMemberAdmissionBufferController.groovy`, `plugins/mf/src/groovy/com/docu/sbicloud/program/dcs/UpdateMemberAdmissionApiAction.groovy` | MemberAdmissionApproval, MemberDomain |
| 25 | Required-Field and Format Validation — New Admission Request | Member Admission Validation Rules | `plugins/mf/grails-app/services/com/docu/api/feeder/MemberApiService.groovy`, `plugins/mf/grails-app/services/com/docu/api/feeder/CommonApiService.groovy` | MemberAdmissionApproval, MemberDomain |
| 26 | Identity-Document Structure Validation — Per Party | Member Admission Validation Rules | `plugins/mf/grails-app/services/com/docu/api/feeder/CommonApiService.groovy` | MemberAdmissionApproval, MemberDomain |
| 27 | Nominee Field Validation — New Admission Request | Member Admission Validation Rules | `plugins/mf/grails-app/services/com/docu/api/feeder/CommonApiService.groovy` | MemberAdmissionApproval, MemberDomain |
| 28 | Business Validation — New Admission Request | Member Admission Validation Rules | `plugins/mf/grails-app/services/com/docu/api/feeder/MemberApiService.groovy` | MemberAdmissionApproval, MemberDomain |
| 29 | Required-Field, Format and Business Validation — Member-Update Request | Member Admission Validation Rules | `plugins/mf/grails-app/services/com/docu/api/feeder/MemberApiUpdateService.groovy`, `plugins/mf/grails-app/services/com/docu/api/feeder/CommonApiService.groovy` | MemberAdmissionApproval, MemberDomain |
| 30 | Identity Uniqueness Check (cross-organisation de-dupe) | Sub-Validators | `plugins/applicationCommon/grails-app/services/com/docu/rest/DeDupeRestWebService.groovy`, `plugins/mf/grails-app/services/com/docu/api/feeder/MemberApiService.groovy` | MemberAdmissionApproval, MemberDomain |
| 31 | Cross-Plugin Integrations (business day, vouchers, projects/offices/groups/employees, de-dupe, insurance, message queue) | Cross-Plugin and External Integrations | `plugins/mf/src/groovy/com/docu/sbicloud/program/member/CreateMemberInfoAction.groovy`, `plugins/mf/src/groovy/com/docu/sbicloud/program/member/UpdateMemberInfoAction.groovy`, `plugins/mf/src/groovy/com/docu/sbicloud/program/member/DeleteMemberInfoAction.groovy`, `plugins/mf/src/groovy/com/docu/sbicloud/program/member/AjaxMemberInfoAction.groovy`, `plugins/mf/grails-app/controllers/com/docu/sbicloud/program/member/MemberInfoController.groovy`, `plugins/mf/grails-app/services/com/docu/api/feeder/CommonApiService.groovy`, `plugins/applicationCommon/grails-app/services/com/docu/rest/DeDupeRestWebService.groovy` | MemberDomain, MemberManagement |
| 32 | DCS Member Channel (retrieve buffer, post approve/reject/update-messages) | Cross-Plugin and External Integrations | `plugins/mf/grails-app/services/com/docu/api/feeder/CommonApiService.groovy` | MemberAdmissionApproval, MemberDomain |
| 33 | Cross-Organisation De-Duplication Bridge (search-by-identity-card) | Cross-Plugin and External Integrations | `plugins/applicationCommon/grails-app/services/com/docu/rest/DeDupeRestWebService.groovy` | MemberAdmissionApproval, MemberDomain |

---

## Notes on overlaps and module ownership

- **GroupCreation** is the only spec covering group (VO) creation; its two modules (Group Creation,
  Group Creation Validation Rules) are unique to it. Single controller action pair: `create` + `save`
  on `GroupInfoController`.
- **MemberManagement-EARS-Specification-Resolved** and **MemberDomain** describe the *same*
  `MemberInfoController`-backed member-lifecycle modules (Member Management, Member Activation, Member
  Project-Officer Reassignment, Member Validation Rules) with identical source files. Those rows
  (#10–22, #31) are merged and list both specs.
- **MemberDomain** is a superset: it additionally absorbs the DCS admission-approval modules (Member
  Admission Approval, Member Admission Validation Rules, Sub-Validators) that originate in
  **MemberAdmissionApproval**. Those rows (#23–30, #32–33) list both specs. MemberManagement does NOT
  cover the DCS admission flow.
- **Entry points by controller:**
  - `GroupInfoController` — `create`, `save` (rows 1–9, GroupCreation).
  - `MemberInfoController` — registration/edit/update/delete/family/asset/signature/photo/documents/
    view-list/activation/PO-reassignment/AJAX validation (rows 10–22, 31; MemberDomain + MemberManagement).
  - `DcsMemberAdmissionBufferController` — `approveMemberAdmission`, `approveMemberUpdate`
    (rows 23–24; MemberAdmissionApproval + MemberDomain).
- All cataloged actions live in the **`mf`** plugin (microfinance) except the cross-organisation
  de-duplication bridge / identity-uniqueness check, which resides in **`applicationCommon`**
  (`DeDupeRestWebService`). Several validation rows reach into `applicationCommon` constants/services
  as secondary source files.
