"""Shared quick_ref formatter and dispatcher.

Shared infrastructure: feature modules call :func:`render` rather than
hand-formatting the cheatsheet string, which keeps every module's output
identical in shape so tests can diff it.

Output format::

    == <module> ==
    USAGE
      <example line>
    SIZES
    | Size | ... |
    |------|-----|
    | ...  | ... |
"""

from __future__ import annotations

from typing import Callable


def section_header(module: str) -> str:
    return f"== {module} =="


def usage(usage_lines: list[str]) -> str:
    lines = ["USAGE"]
    lines += [f"  {ln}" for ln in usage_lines]
    return "\n".join(lines)


def table(headers: list[str], rows: list[list[str]]) -> str:
    """Render a GitHub-flavored Markdown table with aligned columns."""
    headers = [str(h) for h in headers]
    str_rows = [[str(c) for c in row] for row in rows]

    widths = [len(h) for h in headers]
    for row in str_rows:
        for i, cell in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(cell))

    def fmt_row(cells: list[str]) -> str:
        padded = [c.ljust(widths[i]) for i, c in enumerate(cells)]
        return "| " + " | ".join(padded) + " |"

    out = [fmt_row(headers)]
    out.append("|" + "|".join("-" * (w + 2) for w in widths) + "|")
    out += [fmt_row(row) for row in str_rows]
    return "\n".join(out)


def render(
    module: str,
    usage_lines: list[str],
    headers: list[str],
    rows: list[list[str]],
) -> str:
    """Build the full ``== module == / USAGE / SIZES`` block (trailing newline)."""
    lines = [
        section_header(module),
        "",
        usage(usage_lines),
        "SIZES",
        table(headers, rows),
    ]
    return "\n".join(lines) + "\n"


def dispatch(
    modules: dict[str, Callable[[], str]],
    module: str | None = None,
) -> str:
    """Return one module's block, or every block concatenated."""
    if module is None:
        return "\n".join(fn() for fn in modules.values())
    try:
        fn = modules[module]
    except KeyError:
        valid = ", ".join(sorted(modules))
        raise ValueError(f"Unknown module {module!r}; valid modules: {valid}") from None
    return fn()
