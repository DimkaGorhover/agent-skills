#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pyyaml",
#     "click",
#     "rich",
# ]
# ///
"""Count tokens in GitLab CI `rules:if` expressions the way GitLab's lexer does.

GitLab's expression lexer (lib/gitlab/ci/pipeline/expression/lexer.rb) has a hard
limit of MAX_TOKENS = 100. Exceeding it raises `Lexer::SyntaxError: Too many
tokens!`, which GitLab surfaces as the generic and misleading error:

    jobs:<job>:rules:rule if invalid expression syntax

This script tokenizes every `rules:if` in a GitLab CI YAML file (or a single
expression via --expr) and flags any that exceed the limit.

Dependencies are declared inline (PEP 723); `uv run` installs them on the fly.

Usage:
    uv run count_expression_tokens.py all.yml
    uv run count_expression_tokens.py all.yml --job .template:mirror-push
    ./count_expression_tokens.py --expr '$CI_COMMIT_BRANCH == "main" && $FOO'

Exit code is non-zero if any expression is over the limit (2 on a syntax error).
"""
import logging
import re

import click
import yaml
from rich.logging import RichHandler
from rich.markup import escape

MAX_TOKENS = 100

# GitLab lexemes, scanned left-to-right; whitespace (incl. newlines) is skipped.
# Order matters: multi-char operators must come before shorter overlapping ones
# (e.g. != and !~ before a bare !). Precompiled once at import.
_LEXEMES = [re.compile(p) for p in (
    r"\(",              # ParenthesisOpen
    r"\)",              # ParenthesisClose
    r"==",              # Equals
    r"!=",              # NotEquals
    r"=~",              # Matches
    r"!~",              # NotMatches
    r"!",               # Not (GitLab 18.11+: !$VAR, !($A || $B))
    r"&&",              # And
    r"\|\|",            # Or
    r"\$\w+",           # Variable ($CI_COMMIT_BRANCH); $\w+ only, not the ${VAR} form
    r'"[^"]*"',         # double-quoted string
    r"'[^']*'",         # single-quoted string
    r"/(?:\\.|[^/\n])*/[imsxU]*",  # pattern /regex/flags
    r"null\b",
    r"true\b",          # Boolean
    r"false\b",         # Boolean
)]
_WS = re.compile(r"\s+")

logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(show_time=False, show_path=False, markup=True)],
)
log = logging.getLogger("count-expression-tokens")


def count_tokens(expr: str) -> int:
    """Return the number of lexer tokens in a GitLab expression string.

    Raises SyntaxError if a substring cannot be tokenized (a real syntax error,
    distinct from the token-count problem this script targets).
    """
    pos, n = 0, 0
    while pos < len(expr):
        m = _WS.match(expr, pos)
        if m:
            pos = m.end()
            continue
        for lexeme in _LEXEMES:
            m = lexeme.match(expr, pos)
            if m and m.end() > pos:
                n += 1
                pos = m.end()
                break
        else:
            raise SyntaxError(f"untokenizable near: {expr[pos:pos + 30]!r}")
    return n


def _construct_reference(loader, node):
    """Represent GitLab's `!reference [...]` tag as a plain sequence."""
    return loader.construct_sequence(node)


def _ignore_unknown_tag(loader, tag_suffix, node):
    """Drop any other custom `!tag` so PyYAML can still parse the document."""
    return None


def _iter_if_expressions(node, path="$"):
    """Yield (yaml_path, expression) for every rules:if in a parsed CI tree."""
    if isinstance(node, dict):
        for key, val in node.items():
            if key == "rules" and isinstance(val, list):
                for i, rule in enumerate(val):
                    if isinstance(rule, dict) and isinstance(rule.get("if"), str):
                        yield f"{path}.rules[{i}]", rule["if"]
            else:
                yield from _iter_if_expressions(val, f"{path}.{key}")
    elif isinstance(node, list):
        for i, item in enumerate(node):
            yield from _iter_if_expressions(item, f"{path}[{i}]")


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument(
    "ci_file",
    required=False,
    metavar="[FILE]",
    type=click.Path(exists=True, dir_okay=False),
)
@click.option("--expr", help="Count a single expression string instead of a file.")
@click.option("--job", help="Only report rules under YAML keys containing this substring.")
def cli(ci_file: str | None, expr: str | None, job: str | None) -> None:
    """Tokenize GitLab CI rules:if expressions and flag any over the 100-token cap."""
    if expr:
        try:
            n = count_tokens(expr)
        except SyntaxError as err:
            log.error("syntax error: %s", escape(str(err)))
            raise SystemExit(2) from None
        if n > MAX_TOKENS:
            log.error("[bold]%d[/] tokens — over the %d-token limit", n, MAX_TOKENS)
            raise SystemExit(1)
        log.info("[bold]%d[/] tokens — ok (limit %d)", n, MAX_TOKENS)
        return

    if not ci_file:
        raise click.UsageError("provide a YAML FILE argument or --expr")

    # GitLab custom tags (!reference) must not break parsing.
    yaml.SafeLoader.add_constructor("!reference", _construct_reference)
    yaml.SafeLoader.add_multi_constructor("!", _ignore_unknown_tag)

    with open(ci_file) as f:
        tree = yaml.safe_load(f)

    over = reported = 0
    for path, expression in _iter_if_expressions(tree):
        if job and job not in path:
            continue
        reported += 1
        loc = escape(path)
        try:
            n = count_tokens(expression)
        except SyntaxError as err:
            over += 1
            log.error("%s: %s", loc, escape(str(err)))
            continue
        if n > MAX_TOKENS:
            over += 1
            log.error("%s: [bold]%d[/] tokens (over the %d-token limit)", loc, n, MAX_TOKENS)
        else:
            log.info("%s: %d tokens", loc, n)

    summary = f"{reported} expression(s) checked, {over} over the {MAX_TOKENS}-token limit"
    if over:
        log.error(summary)
        raise SystemExit(1)
    log.info(summary)


if __name__ == "__main__":
    cli()
