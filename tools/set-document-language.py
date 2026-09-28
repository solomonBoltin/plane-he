#!/usr/bin/env python3
"""set-document-language.py — make the served shell Hebrew before any JavaScript runs.

    python3 tools/set-document-language.py <path-to-index.html> [lang] [dir]

The runtime patch in `overrides/` sets `document.documentElement.lang`/`dir`, but it runs with the
bundle — after the browser has already laid out the served shell. On every load that is a
left-to-right flash for a right-to-left user. This closes that window by fixing the document the
server hands over.

Written as a file rather than an inline heredoc in the workflow because a heredoc inside a YAML
block scalar is where indentation quietly changes meaning, and this step is the one that failed the
first time it ran.
"""

from __future__ import annotations

import pathlib
import re
import sys

HTML_TAG = re.compile(r"<html\b([^>]*)>", re.I)
ATTR = re.compile(r"\s(lang|dir)\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)", re.I)


def main() -> int:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    path = pathlib.Path(sys.argv[1])
    lang = sys.argv[2] if len(sys.argv) > 2 else "he"
    direction = sys.argv[3] if len(sys.argv) > 3 else "rtl"

    if not path.is_file():
        sys.exit(f"REFUSING: {path} does not exist — nothing to patch")

    html = path.read_text(encoding="utf-8")
    match = HTML_TAG.search(html)
    if not match:
        sys.exit(f"REFUSING: no <html> tag in {path}. First 400 bytes:\n{html[:400]}")

    kept = ATTR.sub("", match.group(1)).strip()
    attrs = f'lang="{lang}" dir="{direction}"' + (f" {kept}" if kept else "")
    patched = html[: match.start()] + f"<html {attrs}>" + html[match.end():]
    path.write_text(patched, encoding="utf-8")
    print(f"{path}: <html {attrs}>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
