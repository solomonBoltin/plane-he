#!/usr/bin/env python3
"""check-parity.py — the Hebrew locale must be structurally identical to upstream English.

    python3 tools/check-parity.py <en-dir> <he-dir>

Upstream enforces this itself (`pnpm check:sync --ci` in packages/i18n), and for good reason: a
translation that drops a key does not fail — the UI silently falls back to English in one corner
of one screen, and nobody notices for months. This is the same check, runnable here without the
monorepo's toolchain.

Per namespace it checks:

  * every English file has a Hebrew counterpart (and no Hebrew file is an orphan);
  * the key path set is identical at every level of nesting;
  * every real ICU placeholder (`{count}`, `{entity}`, `{pageCount}` …) survives — a dropped
    `{count}` renders the literal word instead of the number;
  * ICU plural expressions keep their variable, their category set and the placeholders inside
    each branch.

The distinction that matters and is easy to get wrong: braces inside a plural BRANCH are prose, not
placeholders. `{count, plural, one {View} other {Views}}` must become
`{count, plural, one {תצוגה} other {תצוגות}}` — a checker that reads `{View}` as a placeholder
would demand the Hebrew keep saying "View", which is the opposite of the job. So plural expressions
are located by balanced-brace scan and removed before placeholders are compared.

  * no value was translated to an empty string (unless the English one is empty too — upstream has
    a few of those).
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

IDENT = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")
PLURAL_HEAD = re.compile(r"\{\s*(\w+)\s*,\s*plural\s*,")
BRANCH = re.compile(r"(\w+)\s*\{")

# Deliberate, reviewed exceptions — each one is a string where Hebrew CANNOT mirror the English
# structure and the code supplying the values is oblivious to that. Such a path is exempt from the
# placeholder and ICU comparison (structure is still checked). Keeping them visible here is the
# point: an allowlist entry is a decision someone made, not a check that quietly stopped looking.
#
#   workspace.members_import.summary.message.success
#     English: "Successfully added {count} member{plural} to the workspace."
#     The CODE supplies {plural} as an English plural SUFFIX ("member" + "s"). Hebrew's plural is
#     not a suffix, so the Hebrew is rewritten as an ICU plural and never references {plural}.
#     i18next ignores a value the translation never asks for, which is strictly better than
#     rendering "חברs".
#
#   common.good / morning / afternoon / evening
#     The app composes the greeting as `{good} {time_of_day}` — English word order, with `good` as
#     one adjective shared by all three. Hebrew says it the other way round and the adjective AGREES
#     with the noun ("בוקר טוב" but "צהריים טובים"), which one shared value cannot express. So the
#     whole phrase moves into the time key and `good` becomes empty — verified on screen, where the
#     un-fixed version rendered "טוב בוקר".
ALLOWED_RESTRUCTURES: dict[tuple[str, str], str] = {
    ("workspace.json", "workspace.members_import.summary.message.success"): "English plural suffix supplied by code; Hebrew uses ICU instead",
    ("common.json", "good"): "greeting is composed as '{good} {time}'; Hebrew puts the time first, so the phrase lives in the time key and this one is a zero-width space — NOT empty, because i18next is configured with returnEmptyString:false, which turns an empty value back into the English 'Good' (measured: the greeting rendered 'Good בוקר טוב')",
}


def leaves(node, prefix=""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from leaves(v, f"{prefix}.{k}" if prefix else k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from leaves(v, f"{prefix}[{i}]")
    else:
        yield prefix, node


def keys(node, prefix=""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from keys(v, f"{prefix}.{k}" if prefix else k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from keys(v, f"{prefix}[{i}]")
    else:
        yield prefix


def _balanced(value: str, start: int) -> int:
    """Index just past the `}` that closes the `{` at `start` (assumes it opens one)."""
    depth = 0
    i = start
    while i < len(value):
        if value[i] == "{":
            depth += 1
        elif value[i] == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return len(value)


def split_plurals(value: str):
    """-> (text with plural expressions removed, [(variable, {category: body})])."""
    out, rest, i = [], [], 0
    while i < len(value):
        m = PLURAL_HEAD.match(value, i)
        if m:
            end = _balanced(value, i)
            inner = value[m.end():end - 1]
            categories, k = {}, 0
            while k < len(inner):
                bm = BRANCH.search(inner, k)
                if not bm:
                    break
                body_start = bm.end() - 1
                body_end = _balanced(inner, body_start) - 1
                categories[bm.group(1)] = inner[body_start + 1:body_end]
                k = body_end + 1
            out.append((m.group(1), categories))
            i = end
            continue
        rest.append(value[i])
        i += 1
    return "".join(rest), out


def describe(value: str):
    """Placeholders outside plural expressions + a normalised plural signature."""
    outside, plurals = split_plurals(value)
    signature = []
    for var, categories in plurals:
        signature.append(
            (var, tuple(sorted((cat, tuple(sorted(set(IDENT.findall(body))))) for cat, body in categories.items())))
        )
    return tuple(sorted(set(IDENT.findall(outside)))), tuple(sorted(signature))


def main() -> int:
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    en_dir, he_dir = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])

    problems: list[str] = []
    en_files = sorted(p.name for p in en_dir.glob("*.json"))
    he_files = sorted(p.name for p in he_dir.glob("*.json"))

    for missing in sorted(set(en_files) - set(he_files)):
        problems.append(f"missing Hebrew file: {missing}")
    for extra in sorted(set(he_files) - set(en_files)):
        problems.append(f"Hebrew file with no upstream counterpart: {extra}")

    total = 0
    untranslated: list[str] = []
    for name in en_files:
        he_path = he_dir / name
        if not he_path.exists():
            continue
        en = json.loads((en_dir / name).read_text(encoding="utf-8"))
        he = json.loads(he_path.read_text(encoding="utf-8"))

        # A file that is still a byte-identical copy of upstream English passes every structural
        # check above — the checking of structure is what would have caught a HALF-translated file,
        # so it must not also be what hides a file that was never translated at all.
        hebrew_chars = sum(1 for ch in he_path.read_text(encoding="utf-8") if "\u0590" <= ch <= "\u05FF")
        if hebrew_chars == 0:
            problems.append(f"{name}: contains no Hebrew at all — untranslated copy of upstream")
        else:
            same = sum(
                1
                for path, value in leaves(en)
                if isinstance(value, str)
                and value.strip()
                and dict(leaves(he)).get(path) == value
            )
            if same:
                untranslated.append(f"{name} ({same})")

        en_keys, he_keys = set(keys(en)), set(keys(he))
        for k in sorted(en_keys - he_keys)[:5]:
            problems.append(f"{name}: key missing in Hebrew — {k}")
        for k in sorted(he_keys - en_keys)[:5]:
            problems.append(f"{name}: key not in English — {k}")

        he_leaves = dict(leaves(he))
        for path, value in leaves(en):
            if not isinstance(value, str):
                continue
            total += 1
            got = he_leaves.get(path, "")
            allowed = (name, path) in ALLOWED_RESTRUCTURES
            if not got.strip():
                # upstream ships a few intentionally-empty strings; an allowlisted path may also be
                # deliberately empty (see ALLOWED_RESTRUCTURES — the greeting's shared adjective)
                if value.strip() and not allowed:
                    problems.append(f"{name}:{path}: empty translation (English is not empty)")
                continue

            if allowed:
                continue
            want, have = describe(value), describe(got)
            if want[0] != have[0]:
                problems.append(f"{name}:{path}: placeholders {list(want[0])} -> {list(have[0])}")
            if want[1] != have[1]:
                problems.append(f"{name}:{path}: ICU plural {want[1]} -> {have[1]}")

    if problems:
        print(f"PARITY FAILED — {len(problems)} problem(s):")
        for p in problems[:40]:
            print(f"  {p}")
        if len(problems) > 40:
            print(f"  … and {len(problems) - 40} more")
        return 1

    print(
        f"PARITY OK — {len(he_files)} namespace(s), {total} translated string(s); "
        "keys, placeholders and ICU plural structure identical to upstream English"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
