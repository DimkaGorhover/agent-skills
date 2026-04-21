---
name: cli-opendataloader-pdf
description: Use when converting PDF files to text, markdown, HTML, or JSON using opendataloader-pdf — extracting content for RAG pipelines, chunking for vector stores, handling encrypted PDFs, or processing multi-column/table-heavy documents.
metadata:
  author: d.horkhover
  version: 1.3.0
---

# opendataloader-pdf

## Overview

`opendataloader-pdf` is a CLI tool for structured PDF extraction optimized for RAG pipelines. It preserves reading order, bounding boxes, and semantic structure. **Always run via `uvx opendataloader-pdf ...`** — never install globally. Each invocation starts a JVM (~1–2 s); always batch multiple files in a single call.

## When to Use

- Converting PDFs to markdown, JSON, text, or HTML for LLM ingestion
- Building RAG pipelines that need bounding boxes for precise citations
- Processing multi-column academic papers, table-heavy financial reports, or legal documents
- Batch converting folders of PDFs efficiently
- Handling encrypted, tagged, or scanned (hybrid) PDFs

## When NOT to Use

- Creating, editing, or signing PDFs — use a PDF authoring library instead
- Pure OCR of scanned images with no text layer — use a dedicated OCR tool (e.g., Tesseract)
- Extracting only PDF metadata (author, title) — lighter tools suffice
- Simple text extraction where reading order doesn't matter — `pdftotext` (poppler) or `pypdf` have less overhead

## Quick Reference

| Option                      | Short | Default    | Description                                                                                                                      |
| --------------------------- | ----- | ---------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `--output-dir`              | `-o`  | input dir  | Directory for output files                                                                                                       |
| `--format`                  | `-f`  | `json`     | Output formats (comma-separated): `json`, `text`, `html`, `markdown`, `markdown-with-html`, `markdown-with-images`, `tagged-pdf` |
| `--password`                | `-p`  | —          | Password for encrypted PDFs                                                                                                      |
| `--quiet`                   | `-q`  | `false`    | Suppress console logging                                                                                                         |
| `--pages`                   | —     | all        | Pages to extract, e.g. `"1,3,5-7"`                                                                                               |
| `--to-stdout`               | —     | `false`    | Write to stdout (single format only)                                                                                             |
| `--reading-order`           | —     | `xycut`    | Reading order algorithm: `off`, `xycut`                                                                                          |
| `--use-struct-tree`         | —     | `false`    | Use PDF structure tree (tagged PDFs)                                                                                             |
| `--table-method`            | —     | `default`  | Table detection: `default` (border-based), `cluster` (border + cluster)                                                          |
| `--keep-line-breaks`        | —     | `false`    | Preserve original line breaks                                                                                                    |
| `--replace-invalid-chars`   | —     | space      | Replacement for unrecognized characters (default: single space `" "`)                                                            |
| `--sanitize`                | —     | `false`    | Redact emails, phones, IPs, credit cards, URLs                                                                                   |
| `--content-safety-off`      | —     | —          | Disable filters: `all`, `hidden-text`, `off-page`, `tiny`, `hidden-ocg`                                                          |
| `--include-header-footer`   | —     | `false`    | Include page headers/footers                                                                                                     |
| `--detect-strikethrough`    | —     | `false`    | Detect strikethrough (`~~text~~` in markdown, `<del>` in HTML)                                                                   |
| `--image-output`            | —     | `external` | Image mode: `off`, `embedded` (Base64), `external` (files)                                                                       |
| `--image-format`            | —     | `png`      | Image format: `png`, `jpeg`                                                                                                      |
| `--image-dir`               | —     | —          | Directory for extracted images                                                                                                   |
| `--markdown-page-separator` | —     | none       | Page separator in markdown; use `%page-number%`                                                                                  |
| `--text-page-separator`     | —     | none       | Page separator in text output                                                                                                    |
| `--html-page-separator`     | —     | none       | Page separator in HTML output                                                                                                    |

### Hybrid (AI backend) options

| Option              | Default | Description                                              |
| ------------------- | ------- | -------------------------------------------------------- |
| `--hybrid`          | `off`   | Backend: `off`, `docling-fast` (requires running server) |
| `--hybrid-mode`     | `auto`  | Triage: `auto` (dynamic), `full` (all pages to backend)  |
| `--hybrid-url`      | —       | Remote backend URL                                       |
| `--hybrid-timeout`  | `0`     | Request timeout in ms (0 = no timeout)                   |
| `--hybrid-fallback` | `false` | Fallback to Java on backend error                        |

## Common Recipes

### Basic conversion

```sh
uvx opendataloader-pdf document.pdf -o ./output -f json,markdown
```

### Batch folder (single JVM — fast)

```sh
uvx opendataloader-pdf ./pdf-folder -o ./output -f json,markdown
```

### Multiple specific files

```sh
uvx opendataloader-pdf report1.pdf report2.pdf report3.pdf -o ./output -f json,markdown
```

### Encrypted PDF

```sh
uvx opendataloader-pdf encrypted.pdf -p mypassword -o ./output
```

### Specific pages only

```sh
uvx opendataloader-pdf document.pdf --pages "1,3,5-7" -f markdown -o ./output
```

### Stdout (pipe-friendly)

```sh
uvx opendataloader-pdf document.pdf -f markdown --to-stdout | my-pipeline
```

### Tagged/structured PDF

```sh
uvx opendataloader-pdf document.pdf --use-struct-tree -f json -o ./output
```

### Page separators

```sh
uvx opendataloader-pdf document.pdf -f markdown --markdown-page-separator "--- Page %page-number% ---"
```

### Disable reading order (pre-sorted PDFs)

```sh
uvx opendataloader-pdf document.pdf -f json --reading-order off
```

## RAG Pipeline Integration

### Recommended formats

| Format          | Use Case                                                      |
| --------------- | ------------------------------------------------------------- |
| `markdown`      | Simple text chunking/embedding (smallest output)              |
| `json`          | Structured data with bounding boxes for citations             |
| `json,markdown` | Both (recommended — use JSON for metadata, markdown for text) |

### JSON output structure

JSON keys use space-separated names (verified against official schema):

```python
import json

with open("output/document.json", encoding="utf-8") as f:
    doc = json.load(f)

# Root fields: "file name", "number of pages", "kids"
for element in doc["kids"]:
    element_type = element["type"]  # "paragraph", "heading", "list", "table", "image"
    text = element.get(
        "content", ""
    )  # present on paragraph, heading, caption, list item
    page = element.get("page number")  # integer, 1-indexed
    bbox = element.get("bounding box")  # [left, bottom, right, top]
```

### Chunking strategies

**Merged chunks — minimum size** (most practical for RAG, reduces noise):

```python
def chunk_with_min_size(doc, min_chars=200):
    chunks, buffer_text, buffer_pages = [], "", []
    for element in doc["kids"]:
        if element["type"] in ("paragraph", "heading", "list"):
            buffer_text += element.get("content", "") + "\n"
            page = element.get("page number")
            if page and page not in buffer_pages:
                buffer_pages.append(page)
            if len(buffer_text) >= min_chars:
                chunks.append(
                    {
                        "text": buffer_text.strip(),
                        "metadata": {"pages": buffer_pages.copy()},
                    }
                )
                buffer_text, buffer_pages = "", []
    if buffer_text.strip():
        chunks.append(
            {"text": buffer_text.strip(), "metadata": {"pages": buffer_pages}}
        )
    return chunks
```

**By semantic element** (fine-grained retrieval, precise citations):

```python
def chunk_by_element(doc):
    return [
        {
            "text": el.get("content", ""),
            "metadata": {
                "type": el["type"],
                "page": el.get("page number"),
                "bbox": el.get("bounding box"),
                "source": doc.get("file name"),
            },
        }
        for el in doc["kids"]
        if el["type"] in ("paragraph", "heading", "list")
    ]
```

**By section heading** (context-rich, topic-based):

```python
def chunk_by_section(doc):
    chunks, heading, content, start_page = [], None, [], None
    for el in doc["kids"]:
        if el["type"] == "heading":
    if content and len(content) > 1:
                chunks.append(
                    {
                        "text": "\n".join(content),
                        "metadata": {"heading": heading, "page": start_page},
                    }
                )
            heading, content, start_page = (
                el.get("content", ""),
                [el.get("content", "")],
                el.get("page number"),
            )
        elif el["type"] in ("paragraph", "list") and el.get("content"):
            content.append(el["content"])
    if content:
        chunks.append(
            {
                "text": "\n".join(content),
                "metadata": {"heading": heading, "page": start_page},
            }
        )
    return chunks
```

### Precise citations from bounding boxes

```python
def format_citation(metadata):
    citation = f"Source: {metadata.get('source', 'unknown')}"
    if metadata.get("page"):
        citation += f", Page {metadata['page']}"
    if metadata.get("bbox"):
        bbox = metadata["bbox"]
        citation += f", Position ({bbox[0]:.0f}, {bbox[1]:.0f})"
    return citation


# Output: "Source: document.pdf, Page 3, Position (72, 450)"
```

### LangChain integration

Use a [PEP 723 inline script header](https://peps.python.org/pep-0723/) so the script is self-contained — no manual `pip install` or venv setup required:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "langchain-opendataloader-pdf",
# ]
# ///

from langchain_opendataloader_pdf import OpenDataLoaderPDFLoader

loader = OpenDataLoaderPDFLoader(
    file_path=["document.pdf", "folder/"],
    format="text",
    quiet=True,
)
documents = loader.load()
```

Run with:

```sh
uv run script.py
```

## Document Type Recommendations

| Document Type                   | Recommended Flags                          |
| ------------------------------- | ------------------------------------------ |
| Academic papers (multi-column)  | default (XY-Cut handles columns)           |
| Financial reports (table-heavy) | `-f json` (preserves row/column structure) |
| Legal documents (long text)     | `-f markdown`                              |
| Tagged/accessible PDFs          | `--use-struct-tree`                        |
| Scanned/complex layout          | `--hybrid docling-fast`                    |

## Common Mistakes

| Mistake                                  | Fix                                                                                       |
| ---------------------------------------- | ----------------------------------------------------------------------------------------- |
| Running `opendataloader-pdf` directly    | Always use `uvx opendataloader-pdf ...`                                                   |
| One file per call in a loop              | Pass all files/folder in a single call (one JVM)                                          |
| Using `--content-safety-off all` for RAG | Keep safety filters on — they remove headers, watermarks, hidden text that pollute chunks |
| Using `markdown` when you need citations | Use `json` or `json,markdown` to get bounding boxes                                       |
| Tables losing structure in markdown      | Use `-f json` for table-heavy documents                                                   |
| Too many tiny chunks                     | Use `chunk_with_min_size(doc, min_chars=500)`                                             |
| Forgetting `-q` in automated pipelines   | Add `--quiet` to suppress JVM logging noise                                               |
