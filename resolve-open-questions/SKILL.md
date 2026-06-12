---
name: resolve-open-questions
description: Second-pass automation for an EARS specification file produced by /springboot-to-ears. Walks every `[NEEDS REVIEW]` item in the spec's `## Open Questions` section, executes the breadcrumb commands from the item's `*Hint for reviewer:*` footer, and either resolves the question (rewriting the entry and citing the resolution on every affected EARS statement) or leaves it open untouched. Trigger when the user types `/resolve-open-questions <path-to-EARS-file>`.
---

# Resolve Open Questions in an EARS Specification

> **Note:** `/springboot-to-ears` now auto-resolves its *own* Open Questions on the first pass (its Step 6.5, via a fresh read-only subagent that chases each breadcrumb footer). This skill is therefore the **manual / later-pass** resolver — use it for the residual `[NEEDS REVIEW]` items that survived auto-resolution, for the new questions `/ears-gap-fix` or `/fix-dev-reviews` add (the latter from a developer's `## Review by Developer (business requirements)` entries), or after a human has added breadcrumbs to an open item. A fresh `/springboot-to-ears` output will usually have nothing left for it to do.

You are running a **second-pass resolution** over a Markdown EARS specification file produced by the `/springboot-to-ears` skill. Your input is a single Markdown file path. Your output is the **same file**, edited in place so that:

- Every `[NEEDS REVIEW]` item that you can answer with high confidence becomes `[RESOLVED]`, gains an `*Answer:*` paragraph and a `*Source:*` line, but **keeps** its original `*Where agent looked:*` and `*Hint for reviewer:*` footers so the audit trail survives.
- Every EARS statement whose meaning was refined by a resolution gains a trailing inline citation tag `[Resolved Open Question N]`.
- Every brand-new business rule that the resolution surfaced is added as a new EARS statement in the appropriate Module section, also cited.
- The `## Domain Concepts and States` tables absorb any newly discovered enum values, status transitions, or numeric values.
- The `## Extraction Summary` table's counts are recomputed and the `**Extraction completed:**` date is bumped to today.
- Questions you cannot answer with high confidence are **left entirely unchanged** — including their footers.

You do **not** re-trace the codebase from scratch. You trust and follow the breadcrumbs the parent skill placed in each Open Question's two-line footer.

---

## Prerequisite

The target file was produced by `/springboot-to-ears` (or follows the same Rule 8 footer format). Each `[NEEDS REVIEW]` item must look like:

```
N. **[NEEDS REVIEW]** <Question text on one line.>
   *Where agent looked:* `<file:line>` — <what was read>. `<file:line>` — <what was read>.
   *Hint for reviewer:* Likely answer in `<probable/file>` (<reasoning>). Try `<grep / find / graphify command>` to locate.
```

If the file has no `## Open Questions` section, exit immediately with one line: `No Open Questions section found in <path> — nothing to do.` and do not modify the file.

---

## Step 1 — Invocation Contract

The skill is invoked as:

```
/resolve-open-questions <path-to-EARS-file>
```

Apply these gates **before** any reading or investigation:

| Condition | Action |
|-----------|--------|
| No path argument provided | Print: `Usage: /resolve-open-questions <path-to-EARS-file>` and exit. Do nothing else. |
| Path does not exist | Print: `File not found: <path>` and exit. Do nothing else. |
| Path exists but is not a `.md` file | Print: `Expected a Markdown EARS file; got <path>` and exit. |
| File exists and is readable, but has no `## Open Questions` section | Print: `No Open Questions section found in <path> — nothing to do.` and exit. |
| File exists and every `Open Questions` item is already `[RESOLVED]` | Print: `All N Open Questions already resolved — nothing to do.` and exit. |

Do not auto-discover the file. Do not fall back to "the most recent EARS file." A missing argument is a usage error, not a guess.

---

## Step 2 — Parse the Open Questions Section

Read the target EARS file end-to-end. Locate the `## Open Questions` heading. For each numbered item between that heading and the next `## ` heading, build a structured record:

| Field | Source |
|-------|--------|
| `number` | The leading numeral before `**[NEEDS REVIEW]**` or `**[RESOLVED]**` |
| `status` | Either `[NEEDS REVIEW]` or `[RESOLVED]` |
| `question_text` | The text after the status marker, on the same line |
| `where_agent_looked_lines` | The italicised line beginning `*Where agent looked:*` (may span multiple physical lines if the parent skill wrapped it) |
| `hint_for_reviewer_lines` | The italicised line beginning `*Hint for reviewer:*` |

Skip every item whose `status` is already `[RESOLVED]` — do not re-investigate, do not duplicate footer content, do not re-cite anything.

Skip nothing else. Items whose footers are malformed or missing are still in-scope (see edge cases below).

---

## Step 3 — Investigate Each `[NEEDS REVIEW]` Item

For each open item, in numeric order:

1. **Read what the parent agent already read.** For every `` `<file>:<line(-range)>` `` cited inside `*Where agent looked:*`, open that file at that location with the `Read` tool. The parent agent recorded those reads to say "I checked there and it wasn't enough" — your job is to read the same place with a fresh eye in case the parent agent's read was too narrow or stopped too soon.

2. **Read what the parent agent suggested.** For every `` `<file>` `` named inside `*Hint for reviewer:*` as a "likely answer in" path, open it with `Read`. If the question concerns a constant, read enough of the file to see the constant's full definition (including any list literal that spans multiple lines).

3. **Execute the breadcrumb command(s).** The `*Hint for reviewer:*` line typically embeds one or more shell commands in backticks. Examples of patterns you will see:

   - `` `grep -n "FOO_BAR" path/to/Constants.java` ``
   - `` `grep -rln "endpoint-fragment" src/main/resources/migration/` ``
   - `` `find lib/shared-dto -name "NumberUtil.java"` ``
   - `` `graphify query "<concept>"` ``
   - `` `graphify path "<A>" "<B>"` ``

   Extract each backticked command and run it **verbatim** through the `Bash` tool. Do not modify flags. Do not add or remove paths. If the command writes nothing to stdout, that is a useful signal — the parent agent's hypothesis didn't pan out.

4. **Stop as soon as you have a definitive answer.** Do not improvise additional searches. Do not run broader greps or read sibling files that weren't named. The breadcrumbs are intentionally narrow; the parent skill chose them as the highest-probability leads. If they don't yield an answer, the question stays open (see Step 4) — that is the correct outcome, not a failure.

A "definitive answer" is one of:

| Answer shape | Example |
|--------------|---------|
| A concrete value | `MIN_FIRE_INSURANCE_DURATION_MONTHS = 12` |
| A finite set or list | The forbidden-products list = `[1234L, 5678L, 9012L]` |
| A finite range | The amount range is 5,000 to 50,000 BDT |
| A format pattern | The proposal number is `<branchCode>-<YYMMdd>-<sequence>` |
| A categorical fact | "Yes, this method is also invoked from `EveryNightScheduledServiceImpl` at line 47" |

If the answer requires you to **guess** or **interpolate** between two ambiguous matches, treat the item as unresolved.

---

## Step 4 — Decide Resolved vs. Still Open

A question is **resolved** when Step 3 produced a definitive answer (per the shapes above).

A question is **left open** in any of these cases:

| Reason | What you do |
|--------|-------------|
| The cited file does not exist | Leave the entry exactly as it is. Do nothing. |
| The command returned no matches | Leave the entry exactly as it is. Do nothing. |
| The matches are ambiguous (multiple plausible answers, no way to choose) | Leave the entry exactly as it is. Do nothing. |
| The answer would contradict an existing EARS statement | Leave the entry as-is **except** append exactly one sentence to the end of the `*Where agent looked:*` line: `Investigation contradicted existing statement at <module/subsection>; resolution withheld for human review.` Do not flip status. Do not cite anywhere. |
| A breadcrumb command appears unsafe (references paths outside the repo, uses destructive flags such as `-delete`, `-exec rm`, etc.) | Skip that one command but still run the other commands and read the cited files. If nothing else yields an answer, leave open. Never run an unsafe command. |

When you leave an item open, **do not weaken its footers**. The parent agent's `*Where agent looked:*` and `*Hint for reviewer:*` are the trail; preserving them lets a future human or another run pick up where you stopped.

---

## Step 5 — Apply the Resolution

When an item is resolved, two parallel edits land in the file:

### 5a. Rewrite the Open Question entry

Transform:

```
3. **[NEEDS REVIEW]** What is the exact role-to-API mapping for the OTC loan-proposal endpoints in the access-control library's seed data?
   *Where agent looked:* `lib/access-control/.../AccessControlDaoImpl.java:97-135` — the DAO loads permitted endpoints from `access_api`, `user_role`, `role_authority`, `authority_access_api` tables but the seed data lives in Flyway migrations…
   *Hint for reviewer:* Run `grep -rln "/otc/v1/branches.*loan-proposals" src/main/resources/migration/` to locate the Flyway migration that seeds these endpoints; cross-reference with the role seed rows in the same migration.
```

Into:

```
3. **[RESOLVED]** What is the exact role-to-API mapping for the OTC loan-proposal endpoints in the access-control library's seed data?
   *Answer:* The OTC loan-proposal create endpoint (`POST /otc/v1/branches/{branchId}/loan-proposals`) is permitted to the "BRANCH_MANAGER", "ASSISTANT_BRANCH_MANAGER", and "DEVELOPER" roles; the delete endpoint additionally requires "BRANCH_MANAGER" only; the `sync-missing-loan-account-data` administrative endpoint is restricted to "DEVELOPER" and "OPS_ADMIN".
   *Source:* `src/main/resources/migration/database/local/smart-mf__V1234__seed_access_api.sql:42-58` — seeded `access_api` rows for the four endpoints. `src/main/resources/migration/database/local/smart-mf__V1234__seed_access_api.sql:120-180` — seeded `role_authority` rows that grant each role its endpoint list.
   *Where agent looked:* `lib/access-control/.../AccessControlDaoImpl.java:97-135` — the DAO loads permitted endpoints from `access_api`, `user_role`, `role_authority`, `authority_access_api` tables but the seed data lives in Flyway migrations…
   *Hint for reviewer:* Run `grep -rln "/otc/v1/branches.*loan-proposals" src/main/resources/migration/` to locate the Flyway migration that seeds these endpoints; cross-reference with the role seed rows in the same migration.
```

Rules for the rewrite:

- Replace `**[NEEDS REVIEW]**` with `**[RESOLVED]**` on the entry's heading line. Nothing else on that line changes.
- Insert exactly two new lines between the question text and the original `*Where agent looked:*` line:
  - `*Answer:*` — one paragraph in plain business language. **Quote verbatim** any string literal, enum value, error-message text, or class constant the source code uses. List every value when the answer is a set; do not summarise as "and others". If the answer is a format pattern, give the exact pattern.
  - `*Source:*` — one line citing every file path and line range (or range of lines) you actually read to derive the answer. Format identical to the parent skill's `*Where agent looked:*` format: `` `<path>:<line(-range)>` — <what was read>. `` Repeat for additional sources.
- **Do not modify** the original `*Where agent looked:*` line. **Do not modify** the original `*Hint for reviewer:*` line. They stay verbatim. This preserves the trail of what was tried before resolution succeeded.

### 5b. Apply the answer to EARS statements

For every EARS statement in the file whose meaning is refined by the resolved answer:

- Edit the statement to incorporate the resolved value. Strip any vague placeholder like "the configured X", "the system-defined Y", "(placeholder {0})" and replace it with the concrete value(s) from the resolution.
- Append ` [Resolved Open Question N]` at the very end of the EARS paragraph, with one space separating it from the statement's terminal period (the terminal period stays).

Inline-tag rules:

- The tag is `[Resolved Open Question N]` — exact wording, square brackets, capital R/O/Q, no italics, no Markdown link, no footnote syntax. `N` is the question's numeral as it appears in `## Open Questions`.
- If a statement is informed by **multiple** resolved questions, append multiple tags, space-separated: `[Resolved Open Question 4] [Resolved Open Question 5]`.
- If a statement was rewritten by the resolution but the rewrite is purely stylistic (no change in meaning), **do not** add the tag. The tag means "this statement's content was changed by the answer".

### 5c. Add new EARS statements for newly surfaced rules

If the resolution surfaces brand-new rules that no existing statement covers (e.g., the resolved `FORBIDDEN_DIGITAL_DISBURSEMENT_LOAN_PRODUCT_IDS` list reveals 5 forbidden product types and the original statement only mentioned "money plant"):

- Add new EARS paragraphs in the **appropriate existing Module section and subsection**. Do not invent new sections.
- Choose the EARS pattern using the parent skill's priority order: Event-Driven > State-Driven > Unwanted Behaviour > Optional > Ubiquitous.
- Each new paragraph ends with ` [Resolved Open Question N]`.
- Each new paragraph is a standalone plain-prose sentence; no IDs, no bullets, no nesting (per parent Rule 2).
- Each new paragraph names the precise entity / record / set the resolution revealed (per parent Rule 4).

### 5d. Update Domain Concepts tables

If the resolution surfaces:

- **New enum values** — append rows to the relevant table in `## Domain Concepts and States`. Each row uses the same column structure as the existing table.
- **New status transitions** — append rows to the state-transition table for the relevant entity.
- **New numeric thresholds, ranges, or limits** — if there is a "Numeric Thresholds" or equivalent table, update it; otherwise add the value into the appropriate domain table or as a row of a new sub-table only if the existing tables genuinely cannot host it.

Tables themselves do **not** carry inline `[Resolved Open Question N]` tags. The traceability lives in the resolved Open Question's `*Source:*` line.

---

## Step 6 — Recompute Counts and Refresh the Extraction Summary

After all edits in Step 5 have landed, before exiting:

1. Recount EARS statements in the whole file by leading word:
   - `If ` → Unwanted Behaviour
   - `When ` → Event-Driven
   - `After ` → Event-Driven
   - `While ` → State-Driven
   - `Where ` → Optional
   - `The <DomainName> system shall ` (where `<DomainName>` is whatever the file's header preamble declared) → Ubiquitous
   - `While … when ` → Complex (rare)
2. Recount `[NEEDS REVIEW]` items, `[RESOLVED]` items, `[DISABLED]` items, and `[UNRESOLVED]` items.
3. Overwrite the `## Extraction Summary` table with the recomputed counts. Preserve the existing column structure; only update the right-hand cells. The `Total EARS statements` row equals the sum of the EARS-pattern rows.
4. Update the `**Extraction completed:**` line at the bottom of the Summary to today's runtime date, formatted as `<Day, DD Month YYYY>` (e.g., `Tuesday, 26 May 2026`).

If the file does not have a `## Extraction Summary` section, skip Step 6 and do not invent one — that means the file was not produced by `/springboot-to-ears` and you should not retrofit the structure.

---

## Step 7 — Report to the User

Print a concise stdout summary (≤ 12 lines) so the user can see at a glance what happened:

```
Resolved Open Questions: 6 / 10
  1: resolved — proposal number format
  4: resolved — forbidden products list (3 product IDs)
  5: resolved — UPG project list (4 project IDs)
  6: resolved — MIN_FIRE_INSURANCE_DURATION_MONTHS = 12
  8: resolved — parent validator additional rules
  10: resolved — server-base.url is overridden in prod profile
Still open:
  2: profile gates — could not locate ConditionalHttpSecurity impls
  3: access-control seed — Flyway migrations directory empty
  7: scheduler invocations — no @Scheduled references found
  9: throttling — no captcha annotations on controller

Statements edited: 14
Statements added: 7
```

Format guidelines:

- First line: `Resolved Open Questions: <resolved>/<total>` (treats already-`[RESOLVED]` items as part of the total).
- One line per item, prefixed with the item number and a colon. Resolved items get a half-sentence summary of the answer. Still-open items get a half-sentence reason.
- Last two lines: how many EARS statements were edited in place and how many were added.

Do not print the full resolved answer (that text now lives in the file). Do not print file paths in the stdout summary. The user opens the file to see the rich detail.

---

## Citation Rules — Worked Example

Take the existing EARS statement (before this skill runs):

> If the proposal's loan product identifier appears in the configured forbidden-products list for digital disbursement, the Loan Proposal system shall reject the request with the message "Money Plant loan cannot take in central disbursement payment method.".

Suppose Open Question 4 was resolved as: "The forbidden-products list contains the Money Plant Scheme product (id=1234), the Specialised Lien Loan Term-Savings product (id=5678), and the Pilot Digital Disbursement Sandbox product (id=9012)."

The skill rewrites the statement in place to:

> If the proposal's loan product identifier matches the Money Plant Scheme product, the Specialised Lien Loan Term-Savings product, or the Pilot Digital Disbursement Sandbox product (the configured forbidden-products list for digital disbursement), the Loan Proposal system shall reject the request with the message "Money Plant loan cannot take in central disbursement payment method.". [Resolved Open Question 4]

And — because the existing single statement only covered the "money plant" message, but now there are three distinct products with potentially distinct rejection wordings — the skill **may** add additional EARS statements in the same subsection if the resolution showed each product has a distinct message. Each added statement ends with ` [Resolved Open Question 4]`.

If the existing statement already used wording broad enough to cover all three products and the resolution merely confirms the membership of the set, only the citation tag is added — no rewording is needed.

---

## Edge Cases

| Case | Behaviour |
|------|-----------|
| **Already-`[RESOLVED]` item** | Skip in Step 2. Do not re-investigate. Do not append duplicate `*Source:*` lines. Do not change anything about the entry. |
| **Item with no `*Where agent looked:*` or no `*Hint for reviewer:*` footer** | Investigate best-effort from the question text alone. If you can derive a target file or grep pattern from the wording (e.g., the question names a specific class), use it. If you cannot, leave the entry as-is. **Never** crash. |
| **Resolution contradicts an existing EARS statement** | Do not silently overwrite the existing statement. Do not flip status. Append exactly one sentence at the end of the original `*Where agent looked:*` line: `Investigation contradicted existing statement at <module name and subsection>; resolution withheld for human review.` That's the entire action — no citation, no rewrite. |
| **Unsafe breadcrumb command** | A command is unsafe if it references paths outside the repository (`/etc`, `~`, absolute paths to system locations), uses destructive flags (`-delete`, `-exec rm`, `--force`), or appears designed to mutate state. Skip just that command. Try the cited file reads instead. If no other lead pans out, leave open. |
| **Resolution succeeds, but the value isn't referenced anywhere in the EARS file** | Still mark `[RESOLVED]` with the `*Answer:*` and `*Source:*` lines. No `[Resolved Open Question N]` tag goes anywhere — there is nothing to cite from. Note this case in the stdout report as `resolved — no EARS statements required updating`. |
| **The file has no `## Open Questions` section** | Exit immediately per Step 1's gate. Do not edit. |
| **Multiple Open Questions share a citation** | A single EARS statement may carry multiple inline tags, e.g., `[Resolved Open Question 4] [Resolved Open Question 5]`, space-separated. Order them by question number. |
| **An Open Question's answer reveals that the parent skill missed a whole sub-validator or DAO** | Add the new EARS statements in the most appropriate existing Module section. Do not create a new top-level Module section just for these (that's a parent-skill change, out of scope here). |

---

## Self-Review Checklist (Run Before Exiting)

Verify each of the following before the file is considered ready:

- [ ] Every entry now marked `[RESOLVED]` has both an `*Answer:*` line and a `*Source:*` line.
- [ ] Every `[RESOLVED]` entry still carries its original `*Where agent looked:*` and `*Hint for reviewer:*` lines verbatim (unchanged from the parent skill's wording, except the contradiction-note appended in the rare Step-4 contradiction case).
- [ ] Every EARS statement that was modified or added because of a resolution carries exactly one `[Resolved Open Question N]` tag per contributing question, at the end of the paragraph, space-separated, no Markdown link or footnote.
- [ ] No `[NEEDS REVIEW]` entry has been silently weakened. The footers of any still-open item are byte-for-byte identical to before the run.
- [ ] The `## Extraction Summary` table counts sum correctly: the sum of all EARS-pattern rows equals the `Total EARS statements` row.
- [ ] The `**Extraction completed:**` line is today's runtime date in `<Day, DD Month YYYY>` format.
- [ ] No new Module sections were invented. No new top-level sections were added.
- [ ] Inline tags are exactly `[Resolved Open Question N]` (no `[resolved open question]`, no `[OQ-N]`, no Markdown link).
- [ ] Domain Concepts tables retain their original column structure; new rows match the existing column count and style.
- [ ] The stdout report names every resolved item and every still-open item with a half-sentence each, plus the totals.

If any checklist item fails, fix it before exiting. A failed checklist item is a bug in this skill's output, not an acceptable outcome.

---

## Important Reminders

1. **Trust the parent skill's breadcrumbs.** Do not re-trace from scratch. Do not improvise additional searches. The breadcrumbs are intentionally narrow; if they don't lead anywhere, the question stays open.
2. **Quote verbatim.** When the resolved answer includes a string literal, an enum value, an error-message, or a constant value, quote it character-for-character from the source file. Do not paraphrase.
3. **List every value when the answer is a set.** If the answer is a list of product IDs, project IDs, or enum values, write them all. Do not summarise as "and others".
4. **Preserve the audit trail.** Original `*Where agent looked:*` and `*Hint for reviewer:*` footers stay. The new `*Answer:*` and `*Source:*` are additive, not replacements.
5. **Cite at the paragraph level, not the section level.** Each individual EARS statement that absorbed a resolved answer gets its own `[Resolved Open Question N]` tag. Do not aggregate citations at a section heading.
6. **Leaving questions open is a valid outcome.** If the breadcrumbs don't yield a definitive answer, leaving the entry untouched is correct. Marking something resolved on a guess is worse than leaving it open.
7. **Edits are surgical.** The diff should contain only: the rewritten Open Question entries (`[NEEDS REVIEW]` → `[RESOLVED]` plus two new lines), the modified or added EARS statements with their tags, table-row additions in Domain Concepts where applicable, and the Extraction Summary refresh. Nothing else should change.
8. **The skill is idempotent on already-resolved items.** Running the skill twice on the same file must not produce a different result for items that resolved on the first run. The second run should be a no-op for those items and only attempt the still-open ones.
