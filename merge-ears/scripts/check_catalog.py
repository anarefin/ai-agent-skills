#!/usr/bin/env python3
"""Structural-invariant checker for an EARS action/endpoint catalog.

Usage:
    python3 check_catalog.py <catalog.md> --inputs <in1.md> <in2.md> ...

It reports *signals* the cataloguing agent should act on, not semantic truth. Exit code is 0 when no
problems are found, 1 otherwise, so it can gate the skill's Step 4 self-check.

Checks:
  1. The catalog contains a markdown table with the five required columns
     (Action/Endpoint, Purpose, Module/Domain, Source Code Reference, Originating EARS File).
  2. No data row is missing a Source Code Reference.
  3. No data row is missing an Action/Endpoint.
  4. No data row is missing a Purpose.
  5. Every input EARS file appears (by basename) in the Originating EARS File column.
  6. Every source-file path named in each input's entry-point header
     (`Source Entry Point(s):` / `Source Controller(s):`) surfaces in the catalog's
     Source Code Reference column (no dropped entry point).
"""
import argparse
import os
import re
import sys
from pathlib import Path

REQUIRED_COLUMNS = {
    "action": ["action", "endpoint"],
    "purpose": ["purpose"],
    "module": ["module", "domain"],
    "source": ["source code reference", "source", "reference"],
    "origin": ["originating", "ears file", "origin"],
}


def read(path):
    return Path(path).read_text(encoding="utf-8")


def backtick_paths(line):
    """Every backtick-wrapped token on a line."""
    return re.findall(r"`([^`]+)`", line)


def looks_like_path(token):
    """A source-file reference, not a bare action name. Paths contain a '/' or a code extension;
    action-name qualifiers (e.g. `approveMemberAdmission`) do not."""
    return "/" in token or token.endswith((".groovy", ".java", ".kt", ".py"))


def entry_point_files(text):
    """Source-file paths cited in the front-matter entry-point header of an input spec.
    Only file paths are returned — backtick-wrapped action names inside qualifiers are excluded."""
    files = set()
    for line in text.splitlines():
        if "**Source Entry Point(s):**" in line or "**Source Controller(s):**" in line:
            files.update(t for t in backtick_paths(line) if looks_like_path(t))
    return files


def parse_table(text):
    """Return (header_cells, [row_cells, ...]) for the first markdown table with a header
    separator row. Cells are stripped strings."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith("|") and i + 1 < len(lines):
            sep = lines[i + 1].strip()
            if re.match(r"^\|?[\s:|-]+\|?$", sep) and "-" in sep:
                header = [c.strip() for c in line.strip().strip("|").split("|")]
                rows = []
                for row in lines[i + 2:]:
                    if not row.strip().startswith("|"):
                        break
                    cells = [c.strip() for c in row.strip().strip("|").split("|")]
                    rows.append(cells)
                return header, rows
    return None, None


def col_index(header, keywords):
    for idx, h in enumerate(header):
        hl = h.lower()
        if any(k in hl for k in keywords):
            return idx
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("catalog")
    ap.add_argument("--inputs", nargs="*", default=[])
    args = ap.parse_args()

    text = read(args.catalog)
    problems, info = [], []

    header, rows = parse_table(text)
    if header is None:
        problems.append("No markdown table with a header separator row found in the catalog.")
        print_report(args.catalog, info, problems)
        return 1

    idx = {key: col_index(header, kws) for key, kws in REQUIRED_COLUMNS.items()}
    missing_cols = [k for k, v in idx.items() if v is None]
    if missing_cols:
        problems.append(
            f"Catalog table is missing required column(s): {missing_cols}. Header was: {header}"
        )
        print_report(args.catalog, info, problems)
        return 1

    info.append(f"Table found with {len(rows)} data row(s); columns: {header}")

    # Per-row content checks
    src_idx, act_idx, org_idx, pur_idx = (
        idx["source"], idx["action"], idx["origin"], idx["purpose"]
    )
    catalog_sources = set()
    catalog_origins = set()
    rows_missing_source, rows_missing_action, rows_missing_purpose = 0, 0, 0
    for r in rows:
        if max(src_idx, act_idx, org_idx, pur_idx) >= len(r):
            problems.append(f"Malformed row (too few cells): {r}")
            continue
        src = r[src_idx].strip()
        act = r[act_idx].strip()
        pur = r[pur_idx].strip()
        if not src:
            rows_missing_source += 1
        else:
            catalog_sources.update(backtick_paths(src) or [src])
        if not act:
            rows_missing_action += 1
        if not pur:
            rows_missing_purpose += 1
        catalog_origins.add(os.path.basename(r[org_idx].strip().strip("`")))

    if rows_missing_source:
        problems.append(f"{rows_missing_source} row(s) missing a Source Code Reference.")
    if rows_missing_action:
        problems.append(f"{rows_missing_action} row(s) missing an Action/Endpoint.")
    if rows_missing_purpose:
        problems.append(f"{rows_missing_purpose} row(s) missing a Purpose.")

    # Input coverage: originating files + entry-point source coverage
    for p in args.inputs:
        base = os.path.basename(p)
        if base not in catalog_origins:
            problems.append(f"Input '{base}' does not appear in the Originating EARS File column.")
        ep_files = entry_point_files(read(p))
        missing = {f for f in ep_files if f not in catalog_sources}
        if missing:
            problems.append(
                f"Entry-point source file(s) from '{base}' missing from the catalog's Source Code "
                f"Reference column: {sorted(missing)}"
            )
        else:
            info.append(f"'{base}': all {len(ep_files)} entry-point source file(s) catalogued.")

    print_report(args.catalog, info, problems)
    return 1 if problems else 0


def print_report(catalog, info, problems):
    print("=== merge-ears catalog check ===")
    print(f"file: {catalog}\n")
    print("INFO:")
    for i in info:
        print(f"  - {i}")
    if problems:
        print("\nPROBLEMS:")
        for p in problems:
            print(f"  ✗ {p}")
        print(f"\n{len(problems)} problem(s) found.")
    else:
        print("\n✓ No structural problems found.")


if __name__ == "__main__":
    sys.exit(main())
