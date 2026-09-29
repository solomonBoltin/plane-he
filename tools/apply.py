#!/usr/bin/env python3
"""apply.py — lay the Hebrew patch over a clean clone of makeplane/plane.

    python3 tools/apply.py <path-to-upstream-clone> [--check]

Two things are applied:

  1. `overrides/<path>` — complete REPLACEMENT files for the handful of upstream sources this patch
     changes (the i18n package's language registry, its instance, `setLanguage`, the app shell, the
     font stacks, the date helpers). They are whole files, not diffs, on purpose: a diff against a
     moving upstream is a patch that applies one day and silently corrupts the next, and the files
     are tiny. Every override carries a `BINA PATCH` marker so a future rebase can find what we
     changed. **Each one must exist upstream** — that check is the whole point of this script.
  2. `additions/<path>` — files that upstream DOES NOT HAVE and this patch brings with it (the
     bundled Hebrew font). Copied verbatim; the existence check cannot apply to them, which is
     exactly why they live in their own tree rather than being waved through inside `overrides/`:
     the first version of this buried the font among the replacements and the build failed with
     "REFUSING: these upstream files do not exist at the pinned tag".
  3. `locales/he/*.json` — the 28 namespace files, copied to
     `packages/i18n/src/locales/he/`.

`--check` reports what would change without writing anything.

The clone's tag is NOT verified here — the workflow pins it (`VERSION` + `--branch`) because a
clone made by `git clone --depth 1` reports no tags. What IS verified is that every file this patch
expects to override exists: an upstream reshuffle must fail loudly here, not produce an image that
builds fine and ignores half the patch.
"""

from __future__ import annotations

import argparse
import filecmp
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent.parent
OVERRIDES = HERE / "overrides"
ADDITIONS = HERE / "additions"
LOCALES = HERE / "locales" / "he"
LOCALE_TARGET = pathlib.Path("packages/i18n/src/locales/he")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("upstream", help="path to a clean clone of makeplane/plane")
    ap.add_argument("--check", action="store_true", help="report only, change nothing")
    args = ap.parse_args()

    root = pathlib.Path(args.upstream).resolve()
    if not (root / "packages/i18n").is_dir():
        sys.exit(f"{root} does not look like a makeplane/plane checkout (no packages/i18n)")

    changed, missing = [], []

    for src in sorted(p for p in OVERRIDES.rglob("*") if p.is_file()):
        rel = src.relative_to(OVERRIDES)
        dst = root / rel
        if not dst.exists():
            missing.append(str(rel))
            continue
        if filecmp.cmp(src, dst, shallow=False):
            continue
        changed.append(str(rel))
        if not args.check:
            shutil.copy2(src, dst)

    # NEW files: copied verbatim, no upstream counterpart to check.
    for src in sorted(p for p in ADDITIONS.rglob("*") if p.is_file()):
        rel = src.relative_to(ADDITIONS)
        dst = root / rel
        if dst.exists() and filecmp.cmp(src, dst, shallow=False):
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        changed.append(str(rel))
        if not args.check:
            shutil.copy2(src, dst)

    he_files = sorted(LOCALES.glob("*.json"))
    if not he_files:
        sys.exit(f"no Hebrew locale files under {LOCALES}")
    (root / LOCALE_TARGET).mkdir(parents=True, exist_ok=True)
    for src in he_files:
        dst = root / LOCALE_TARGET / src.name
        if dst.exists() and filecmp.cmp(src, dst, shallow=False):
            continue
        changed.append(str(LOCALE_TARGET / src.name))
        if not args.check:
            shutil.copy2(src, dst)

    if missing:
        print("REFUSING: these upstream files do not exist at the pinned tag —")
        for m in missing:
            print(f"  {m}")
        print("Upstream moved something this patch depends on. Re-derive the override before building.")
        return 1

    verb = "would change" if args.check else "wrote"
    print(f"{verb} {len(changed)} file(s) ({len(he_files)} Hebrew locale file(s)) under {root}")
    for c in changed[:12]:
        print(f"  {c}")
    if len(changed) > 12:
        print(f"  … and {len(changed) - 12} more")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
