---
name: doc-to-markdown
description: Convert a doc/docx file to markdown format.
---

# Doc to Markdown Conversion Skill

## When to Use

- Converting a `.doc` or `.docx` file to Markdown format
- Extracting readable text from a Word document for further processing
- The user provides a `.docx` path and asks for a Markdown equivalent

## When NOT to Use

- Files that are already Markdown, plain text, or HTML — read them directly
- PDF files — use a PDF-specific tool or the `excel-parsing` skill for spreadsheets
- `.odt` or LibreOffice formats that are not `.docx` — compatibility may vary

This skill takes a docx file as input and converts it to markdown format. The output is a string containing the markdown representation of the original docx file.

Strictly follow the steps below. No virtual environment or manual dependency installation needed — `uv run` handles everything inline.

## Write the conversion script

Run the bash script below. The script uses the `markitdown` library to perform the conversion. You don't need to worry about installing the library or setting up a Python environment; `uv run` will take care of that for you.

1. Replace `{{ path_to_docx_file }}` with the actual path to your docx file.
1. Replace `{{ path_to_md_file }}` with the desired path for the output markdown file.

```shell
uv run --script - <<'EOP'
# /// script
# requires-python = ">=3.12"
# dependencies = ["markitdown[all]"]
# ///

from markitdown import MarkItDown

def main():
    md = MarkItDown()
    result = md.convert("{{ path_to_docx_file }}")

    with open("{{ path_to_md_file }}", "w") as f:
        f.write(result.markdown)
        f.flush()

if __name__ == "__main__":
    main()
EOP
```
