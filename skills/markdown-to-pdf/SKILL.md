---
name: markdown-to-pdf
description: Use when generating a PDF file from markdown content or converting a markdown file to PDF using Python.
metadata:
  author: d.horkhover
  version: 1.0.0
---

# Markdown to PDF Conversion Skill

## When to Use

- Generating a PDF from a Markdown string or `.md` file using Python
- Producing a styled, paginated document (with TOC, tables, images) from Markdown source
- The user asks to "convert markdown to PDF" or "export as PDF"

## When NOT to Use

- Generating PDFs from non-Markdown sources (HTML, Word, Excel) — use a different conversion approach
- Environments where `uv` is unavailable — the scripts depend on `uv run` for dependency management
- High-fidelity print layouts requiring precise CSS/page control — consider Pandoc + LaTeX for those

This skill generates a PDF file from markdown content using the `markdown-pdf` Python library. It supports tables, images, hyperlinks, TOC, CSS styling, and UTF-8 text.

Strictly follow the steps below. All Python scripts use the `uv` inline script header so no manual venv setup is needed — just run them with `uv run`.

## Convert markdown to PDF

### Basic usage — from a markdown string

Write this to a `.py` file and run it with `uv run script.py`:

```python
# /// script
# requires-python = ">=3.12"
# dependencies = ["markdown-pdf"]
# ///

from markdown_pdf import MarkdownPdf, Section

pdf = MarkdownPdf(toc_level=2)
pdf.add_section(Section("# Hello World\n\nThis is **bold** and *italic* text.\n"))
pdf.meta["title"] = "My Document"
pdf.meta["author"] = "Author Name"
pdf.save("{{ output_pdf_path }}")
```

### From a markdown file

```python
# /// script
# requires-python = ">=3.12"
# dependencies = ["markdown-pdf"]
# ///

from pathlib import Path
from markdown_pdf import MarkdownPdf, Section

md_content = Path("{{ path_to_md_file }}").read_text(encoding="utf-8")

pdf = MarkdownPdf(toc_level=2)
pdf.add_section(Section(md_content))
pdf.save("{{ output_pdf_path }}")
```

### With custom CSS styling

```python
# /// script
# requires-python = ">=3.12"
# dependencies = ["markdown-pdf"]
# ///

from markdown_pdf import MarkdownPdf, Section

css = "table, th, td {border: 1px solid black;} h1 {text-align: center;}"

pdf = MarkdownPdf(toc_level=2)
pdf.add_section(Section(md_content), user_css=css)
pdf.save("{{ output_pdf_path }}")
```

## Quick Reference

| Feature                  | How                                                               |
| ------------------------ | ----------------------------------------------------------------- |
| New page                 | Add a new `Section()`                                             |
| Exclude heading from TOC | `Section(text, toc=False)`                                        |
| Set paper size           | `Section(text, paper_size="A4-L")` for landscape, `"Letter"` etc. |
| Set borders              | `Section(text, borders=(36, 36, -36, -36))`                       |
| Set image root dir       | `Section(text, root="./images")`                                  |
| Document metadata        | `pdf.meta["title"]`, `pdf.meta["author"]`, etc.                   |
| Compress output          | `MarkdownPdf(toc_level=2, optimize=True)`                         |
