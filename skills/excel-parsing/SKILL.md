---
name: excel-parsing
description: Use when reading, analyzing, or extracting data from .xls or .xlsx binary spreadsheet files. Triggers when Read tool returns "Cannot read binary file", when the user references a spreadsheet, or when structured tabular data must be extracted from Excel format.
metadata:
  author: d.horkhover
  version: 1.0.0
---

# Excel / Spreadsheet Parsing

## When to Use

- The `Read` tool returns `"Cannot read binary file"` on a `.xls` or `.xlsx` file
- The user references a spreadsheet and wants data extracted or analyzed
- Structured tabular data needs to be read from Excel format (e.g. convert to Markdown table, parse rows, extract columns)
- The file has merged cells, multi-row headers, or multiline cell content that requires special handling

## When NOT to Use

- `.csv` files — they are plain text and the `Read` tool handles them directly
- Non-spreadsheet binary files (PDFs, images, Word docs) — use the appropriate tool instead

## Overview

Excel files are binary — the `Read` tool cannot open them. Always use Python with `pandas` + `openpyxl` via `uv run` with **inline script dependencies**. Never attempt `cat`, `Read`, or `head` on `.xls`/`.xlsx` files.

## Quick Reference

| Task                          | Tool / approach                                                           |
| ----------------------------- | ------------------------------------------------------------------------- |
| Read binary `.xlsx` / `.xlsm` | `uv run script.py` — deps: `pandas`, `openpyxl`                           |
| Read legacy `.xls`            | `uv run script.py` — deps: `pandas`, `xlrd` (NOT openpyxl)                |
| Read `.csv`                   | Use `Read` tool directly — CSVs are plain text, no Python needed          |
| List sheets                   | `pd.ExcelFile(path).sheet_names`                                          |
| Read a sheet                  | `pd.read_excel(path, sheet_name=name, header=None)`                       |
| Handle merged-cell NaN        | carry-forward with `current = row[0] if not pd.isna(row[0]) else current` |
| Collapse multiline cell       | `"; ".join(part.strip() for part in val.split("\n") if part.strip())`     |
| Clean any cell value          | `str(val).replace("\\n", "\n").strip() if not pd.isna(val) else ""`       |
| LSP "pandas not resolved"     | **Ignore** — benign, pandas is installed at runtime by uv                 |

## Mandatory First Step — Structure Inspection

**Always inspect before processing.** You cannot assume sheet names, column counts, or header positions.

```python
# /// script
# dependencies = [
#   "openpyxl",
#   "pandas",
# ]
# ///

import pandas as pd

path = "MyFile.xlsx"
xl = pd.ExcelFile(path)
print("Sheets:", xl.sheet_names)

for sheet in xl.sheet_names:
    df = pd.read_excel(path, sheet_name=sheet, header=None)
    print(f"\n{sheet}: {df.shape}")
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_colwidth', 120)
    print(df.head(10).to_string())
```

Run with: `uv run inspect.py`

Decide header row placement **after** reading this output — do not assume row 0.

## Core Pattern — Full Processing Script

```python
# /// script
# dependencies = [
#   "openpyxl",
#   "pandas",
# ]
# ///

import pandas as pd

def clean(val):
    """Convert any cell value to a clean string. Handles NaN and literal \\n."""
    if pd.isna(val):
        return ""
    return str(val).replace("\\n", "\n").strip()

def collapse(val):
    """Flatten multiline cell content to a single line (safe for table cells)."""
    text = clean(val)
    return "; ".join(part.strip() for part in text.split("\n") if part.strip()) or "—"

path = "MyFile.xlsx"

# Always read with header=None so you control indexing
df = pd.read_excel(path, sheet_name="SheetName", header=None)

# ── Handling merged cells (multi-row spans) ──────────────────────────────────
# Excel merged cells populate only the FIRST row; subsequent rows are NaN.
# Carry the last seen value forward:
current_group = None
rows = []
for i in range(2, len(df)):   # start after header rows
    row = df.iloc[i]
    group_label = clean(row[0])
    if group_label:
        current_group = group_label
    rows.append({
        "group":  current_group,
        "col_a":  clean(row[1]),
        "col_b":  clean(row[2]),
    })

# ── Writing output ───────────────────────────────────────────────────────────
lines = ["# Report\n"]
for r in rows:
    if r["col_a"] or r["col_b"]:
        lines.append(f"**{r['group']}**: {r['col_a']} / {r['col_b']}")

with open("output.md", "w") as f:
    f.write("\n".join(lines))
print("Done")
```

## Common Mistakes

| Mistake                                                | Fix                                                                               |
| ------------------------------------------------------ | --------------------------------------------------------------------------------- |
| `Read` / `cat` on .xlsx                                | Always use `uv run` Python script                                                 |
| Assuming row 0 is the header                           | Inspect first; many files have multi-row headers or merged title rows             |
| Putting raw multiline content in a markdown table cell | Use `collapse()` — newlines break table rendering                                 |
| Treating all NaN as "empty data"                       | NaN in continuation rows = merged cell carrying the value above                   |
| Panicking at LSP "pandas not resolved"                 | Benign — pandas is unavailable to the LSP but uv installs it at runtime           |
| Using `openpyxl` with `.xls` files                     | Old `.xls` format requires `xlrd` dep instead; `openpyxl` is `.xlsx`/`.xlsm` only |
| Running without `openpyxl` in deps                     | `pandas` alone cannot open `.xlsx`; both packages are required                    |
| Forgetting `pd.set_option` for wide output             | Without it, pandas truncates columns silently — inspection output is misleading   |
