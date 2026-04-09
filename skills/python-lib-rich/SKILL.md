---
name: python-lib-rich
description: Use when writing Python CLI tools, scripts, or terminal applications that need formatted terminal output — tables, progress bars, colored text, syntax highlighting, trees, status spinners, tracebacks, or pretty-printed data. Triggers on any terminal formatting need, "make output pretty", styled logging, or Rich library usage.
metadata:
  author: d.horkhover
  version: 1.0.0
---

# Rich Terminal Output

## Overview

Rich is a Python library for rich text and beautiful formatting in the terminal. It provides tables, progress bars, markdown rendering, syntax highlighting, tracebacks, trees, columns, spinners, and styled text — all with minimal code via the `rich` module.

## When to Use

- Adding color, bold, italic, or styled text to CLI output
- Rendering data as formatted tables
- Showing progress bars for long-running operations
- Displaying status spinners during async work
- Pretty-printing data structures, dicts, lists
- Rendering markdown or syntax-highlighted code in terminal
- Replacing Python's default traceback with readable ones
- Building tree views (file structures, hierarchies)
- Laying out content in columns
- Any "make terminal output look better" request

## When NOT to Use

- Simple one-line `print()` output — Rich adds a dependency for no gain
- Non-interactive scripts where output is piped or redirected to a file — Rich's ANSI codes may pollute the output (use `Console(force_terminal=False)` or plain `print()`)
- Logging-heavy server applications — use structured logging (JSON) instead of Rich formatting

## Quick Reference

| Task               | Code                                                                    |
| ------------------ | ----------------------------------------------------------------------- |
| Install            | `uv add rich`                                                           |
| Test output        | `uv run -m rich`                                                        |
| Styled print       | `from rich import print; print("[bold magenta]Hello[/bold magenta]")`   |
| Pretty REPL        | `from rich import pretty; pretty.install()`                             |
| Console object     | `from rich.console import Console; console = Console()`                 |
| Styled line        | `console.print("text", style="bold red")`                               |
| Inline markup      | `console.print("[bold cyan]name[/bold cyan] is [u]underlined[/u]")`     |
| Log with timestamp | `console.log("msg", log_locals=True)`                                   |
| Inspect object     | `from rich import inspect; inspect(obj, methods=True)`                  |
| Emoji              | `console.print(":thumbs_up: :fire:")`                                   |
| Status spinner     | `with console.status("[bold green]Working..."): ...`                    |
| Render markdown    | `from rich.markdown import Markdown; console.print(Markdown(text))`     |
| Syntax highlight   | `from rich.syntax import Syntax; console.print(Syntax(code, "python"))` |
| Rich tracebacks    | `from rich.traceback import install; install()`                         |

## Console Markup Syntax

Rich uses bbcode-like tags for inline styling:

```python
console.print("[bold]Bold[/bold], [italic]italic[/italic], [underline]underline[/underline]")
console.print("[red]Red[/red], [bold cyan]Bold cyan[/bold cyan], [on white]White bg[/on white]")
console.print("[link=https://example.com]Clickable[/link]")
console.print("[bold red on white]Combined styles[/bold red on white]")
# Escape markup: console.print("\[not bold]")
```

## Tables

```python
from rich.console import Console
from rich.table import Table

console = Console()
table = Table(show_header=True, header_style="bold magenta")
table.add_column("Name", style="dim", width=20)
table.add_column("Status")
table.add_column("Count", justify="right")
table.add_row("Alpha", "[green]Active[/green]", "42")
table.add_row("Beta", "[red]Inactive[/red]", "7")
console.print(table)
```

Key options: `title=`, `show_lines=True`, `box=rich.box.ROUNDED`, `expand=True`, `row_styles=["", "dim"]` (alternating).

## Progress Bars

```python
from rich.progress import track

# Simple — wrap any iterable
for item in track(range(100), description="Processing..."):
    do_work(item)
```

Advanced multi-bar progress:

```python
from rich.progress import Progress

with Progress() as progress:
    task1 = progress.add_task("[red]Downloading...", total=1000)
    task2 = progress.add_task("[green]Processing...", total=500)
    while not progress.finished:
        progress.update(task1, advance=5)
        progress.update(task2, advance=3)
```

## Status Spinner

```python
from rich.console import Console

console = Console()
with console.status("[bold green]Fetching data...") as status:
    data = fetch()  # spinner animates while blocking
    status.update("[bold blue]Processing...")
    process(data)
```

Available spinners: `spinner="dots"`, `"line"`, `"bouncingBar"`, etc. List all: `uv run -m rich.spinner`.

## Tree

```python
from rich.tree import Tree

tree = Tree("[bold blue]Project")
src = tree.add("[bold]src/")
src.add("main.py")
src.add("utils.py")
tree.add("[bold]tests/").add("test_main.py")

console.print(tree)
```

## Columns

```python
from rich.columns import Columns
from rich.panel import Panel

items = [Panel(f"Item {i}", expand=True) for i in range(12)]
console.print(Columns(items, equal=True))
```

## Logging Handler

```python
import logging
from rich.logging import RichHandler

logging.basicConfig(level="INFO", format="%(message)s", datefmt="[%X]", handlers=[RichHandler()])
log = logging.getLogger("myapp")
log.info("Server started", extra={"markup": True})
```

## Syntax Highlighting

```python
from rich.syntax import Syntax

syntax = Syntax.from_path("script.py", theme="monokai", line_numbers=True)
console.print(syntax)

# Or from string
syntax = Syntax(code_string, "python", theme="monokai", line_numbers=True)
```

## Rich Tracebacks

Install once at program start — all uncaught exceptions render beautifully:

```python
from rich.traceback import install
install(show_locals=True)
```

Shows more code context, local variables, and color-coded output vs default Python tracebacks.

## Panels and Layout

```python
from rich.panel import Panel
from rich.layout import Layout

# Panel wraps content in a box
console.print(Panel("Hello", title="Greeting", border_style="green"))

# Layout splits terminal into regions
layout = Layout()
layout.split_column(Layout(name="header", size=3), Layout(name="body"))
layout["body"].split_row(Layout(name="left"), Layout(name="right"))
```

## Common Mistakes

| Mistake                                      | Fix                                                                                 |
| -------------------------------------------- | ----------------------------------------------------------------------------------- |
| Using `print()` instead of `console.print()` | Only `console.print()` renders markup and Rich objects                              |
| Forgetting closing tags `[/bold]`            | Every `[style]` needs `[/style]` or `[/]` to reset all                              |
| Not word-wrapping long text                  | `Console(width=80)` or let Rich auto-detect terminal width                          |
| Mixing `rich.print` and `console.print`      | Pick one — `Console()` gives more control (log, status, etc.)                       |
| Progress bar not updating                    | `track()` only works with iterables; for manual control use `Progress()`            |
| Spinner blocks event loop                    | `console.status()` is synchronous; for async use `rich.progress` with async support |
| Markdown not rendering                       | Pass `Markdown(string)` object to `console.print()`, not raw string                 |
| Traceback not showing locals                 | Pass `show_locals=True` to `install()`                                              |
| Table columns too narrow                     | Use `min_width=`, `no_wrap=True`, or `expand=True` on Table                         |
| LSP "rich not resolved" warning              | Benign if using `uv run` — Rich installs at runtime                                 |
