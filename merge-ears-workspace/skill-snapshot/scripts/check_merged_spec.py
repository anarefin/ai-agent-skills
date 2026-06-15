#!/usr/bin/env python3
"""Structural-invariant checker for a merged EARS specification.

Usage:
    python3 check_merged_spec.py <merged.md> \
        [--inputs <in1.md> <in2.md> ...] \
        [--system-name "the Foo system"]

It is deliberately conservative: it reports *signals* a human (or the merging agent) should act on,
not hard pass/fail truth about semantics. Exit code is 0 when no problems are found, 1 otherwise, so
it can gate a merge in CI or in the skill's Step 3 self-check.

Checks:
  1. Duplicate entity headings under "Domain Entities and Properties".
  2. Duplicate entity *source files* (same domain file under two entity headings = un-deduped).
  3. Business Rules Summary numbering is contiguous from 1.
  4. Duplicate (condition, message) rows in the Error Response Format table.
  5. Every [NEEDS REVIEW...] marker that signals a conflict names sources (heuristic).
  6. The merged system name is the dominant subject; reports other "the X system" subjects.
  7. If --inputs given: every entity source-file path present in the inputs survives in the output.
"""
import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


def read(path):
    return Path(path).read_text(encoding="utf-8")


def split_sections(text, level):
    """Return list of (heading, body) for headings at the given markdown level."""
    pat = re.compile(rf"^{'#' * level} (?!#)(.+)$", re.MULTILINE)
    out = []
    matches = list(pat.finditer(text))
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out.append((m.group(1).strip(), text[start:end]))
    return out


def section_body(text, name):
    """Body of a level-2 (##) section whose heading startswith `name`, until the next ## ."""
    for heading, body in split_sections(text, 2):
        if heading.lower().startswith(name.lower()):
            return body
    return None


def source_files_in(body):
    """All file paths cited in `> **Source files:**` lines within a block."""
    files = set()
    for line in body.splitlines():
        if "**Source files:**" in line:
            # paths are backtick-wrapped
            files.update(re.findall(r"`([^`]+)`", line))
    return files


def check_entities(text, problems, info):
    body = section_body(text, "Domain Entities")
    if body is None:
        info.append("No 'Domain Entities and Properties' section found.")
        return set()
    entities = split_sections(body, 3)
    headings = [h for h, _ in entities]
    dup_headings = [h for h, c in Counter(headings).items() if c > 1]
    if dup_headings:
        problems.append(f"Duplicate entity headings: {dup_headings}")

    # map source-file -> list of entity headings using it
    file_to_entities = defaultdict(list)
    all_files = set()
    for h, b in entities:
        for f in source_files_in(b):
            file_to_entities[f].append(h)
            all_files.add(f)
    for f, hs in file_to_entities.items():
        if len(hs) > 1:
            problems.append(
                f"Entity source file '{f}' appears under {len(hs)} headings {hs} "
                f"(likely un-deduped entity)."
            )
    info.append(f"Entities: {len(entities)} headings, {len(all_files)} distinct source files.")
    return all_files


def check_business_rules(text, problems, info):
    body = section_body(text, "Business Rules Summary")
    if body is None:
        info.append("No 'Business Rules Summary' section found.")
        return
    nums = [int(n) for n in re.findall(r"^\s*(\d+)\.\s", body, re.MULTILINE)]
    if not nums:
        info.append("Business Rules Summary present but no numbered items detected.")
        return
    expected = list(range(1, len(nums) + 1))
    if nums != expected:
        problems.append(
            f"Business Rules numbering not contiguous from 1: got {nums[:5]}...{nums[-3:]} "
            f"({len(nums)} items)."
        )
    else:
        info.append(f"Business Rules: {len(nums)} items, contiguous 1..{len(nums)}.")


def _error_format_body(text):
    """Body of the 'Error Response Format' sub-block, up to the next ## or ### heading."""
    m = re.search(r"^#{2,3}\s+Error Response Format\s*$", text, re.MULTILINE)
    if not m:
        return None
    rest = text[m.end():]
    nxt = re.search(r"^#{2,3}\s+\S", rest, re.MULTILINE)
    return rest[: nxt.start()] if nxt else rest


def check_error_table(text, problems, info):
    body = _error_format_body(text)
    if body is None:
        info.append("No 'Error Response Format' section found.")
        return
    pairs = []
    for line in body.splitlines():
        if not (line.strip().startswith("|") and line.count("|") >= 3):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        cond, msg = cells[0], cells[1]
        if not cond or set(cond) <= set("-: "):  # separator / empty
            continue
        if cond.lower().startswith("error condition"):  # header
            continue
        pairs.append((cond, msg))
    dups = [p for p, c in Counter(pairs).items() if c > 1]
    if dups:
        problems.append(f"Duplicate (condition, message) error rows: {len(dups)} (e.g. {dups[0]}).")
    else:
        info.append(f"Error table: {len(pairs)} condition/message rows, no exact duplicates.")


def check_needs_review(text, problems, info):
    markers = re.findall(r"\[NEEDS REVIEW[^\]]*\]", text)
    info.append(f"[NEEDS REVIEW] markers: {len(markers)}.")
    # conflict-style markers should name sources (heuristic: contain 'vs' or 'and' + a filename-ish token)
    weak = [m for m in markers if "vs" not in m.lower() and " and " not in m.lower() and len(m) < 18]
    if weak:
        info.append(
            f"{len(weak)} bare [NEEDS REVIEW] markers (no source attribution) — fine if they are "
            f"pre-existing open questions, but conflict flags should name sources."
        )


def check_system_name(text, system_name, problems, info):
    subjects = Counter(re.findall(r"\bthe ([A-Z][\w&'’\- ]*? system)\b", text))
    if not subjects:
        info.append("No 'the X system' subjects detected.")
        return
    if system_name:
        target = re.sub(r"^the\s+", "", system_name.strip(), flags=re.IGNORECASE)
        others = {s: c for s, c in subjects.items() if s.lower() != target.lower()}
        if others:
            problems.append(
                f"Statements use system subjects other than '{target}': "
                + ", ".join(f"'{s}'×{c}" for s, c in sorted(others.items(), key=lambda x: -x[1]))
            )
        else:
            info.append(f"All {sum(subjects.values())} subjects use '{target}'.")
    else:
        if len(subjects) > 1:
            problems.append(
                "Multiple system-name subjects present (pass --system-name to enforce one): "
                + ", ".join(f"'{s}'×{c}" for s, c in sorted(subjects.items(), key=lambda x: -x[1]))
            )


def check_source_coverage(out_files, inputs, problems, info):
    in_files = set()
    for p in inputs:
        in_files |= source_files_in(read(p))
    missing = in_files - out_files
    # only meaningful for entity-level files; report a sample
    if missing:
        sample = sorted(missing)[:8]
        info.append(
            f"{len(missing)} source-file path(s) cited in inputs not found among merged entity "
            f"refs (may be module-level rather than entity-level): e.g. {sample}"
        )
    else:
        info.append("All entity-level input source files are represented in the output.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("merged")
    ap.add_argument("--inputs", nargs="*", default=[])
    ap.add_argument("--system-name", default=None)
    args = ap.parse_args()

    text = read(args.merged)
    problems, info = [], []

    out_entity_files = check_entities(text, problems, info)
    check_business_rules(text, problems, info)
    check_error_table(text, problems, info)
    check_needs_review(text, problems, info)
    check_system_name(text, args.system_name, problems, info)
    if args.inputs:
        check_source_coverage(out_entity_files, args.inputs, problems, info)

    print("=== merge-ears structural check ===")
    print(f"file: {args.merged}\n")
    print("INFO:")
    for i in info:
        print(f"  - {i}")
    if problems:
        print("\nPROBLEMS:")
        for p in problems:
            print(f"  ✗ {p}")
        print(f"\n{len(problems)} problem(s) found.")
        return 1
    print("\n✓ No structural problems found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
