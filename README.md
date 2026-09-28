# plane-he — Hebrew + RTL for Plane

A downstream patch that gives [Plane](https://github.com/makeplane/plane) (AGPL-3.0-only) a
**Hebrew interface with right-to-left layout**, built into an artifact the office's
`apps/project-pln` consumes.

Upstream ships **19 locales and not one of them is right-to-left** — Hebrew is not a setting that
can be switched on, and it is not a translation-only job:

* `packages/i18n` has no `he` locale and `TLanguage` has no `"he"`;
* `setLanguage()` sets `document.documentElement.lang` and **never `dir`**;
* there is not a single `rtl:` Tailwind variant and no logical-property utility (`ms-`/`me-`) in
  `apps/` or `packages/`, so direction has to come from the document root;
* the app shell hardcodes `<html lang="en">`.

Open upstream work in the same area: [#3314](https://github.com/makeplane/plane/issues/3314) (RTL
text, open since 2024), [#9299](https://github.com/makeplane/plane/pull/9299) (Persian + RTL — the
approach taken here), [#8722](https://github.com/makeplane/plane/pull/8722) (Hebrew, closed
unmerged, written against the obsolete `.ts` locale layout).

## What is here

```
VERSION                      the upstream tag this patch is derived against (one line)
overrides/                   whole replacement files for the upstream sources we change
locales/he/*.json            28 namespace files — the translation itself
tools/apply.py               lay the patch over a clean upstream clone (fails loudly on drift)
tools/check-parity.py        key + placeholder parity against upstream English
.github/workflows/build.yml  build the frontend on a native arm64 runner, publish it
```

### The overrides, and why they are whole files

| upstream file | what the patch adds |
|---|---|
| `packages/i18n/src/types/language.ts` | `"he"` in the `TLanguage` union |
| `packages/i18n/src/constants/language.ts` | the `עברית` option, `RTL_LANGUAGES`, `isRTLLanguage()`, `getLanguageDirection()` — and Hebrew first in the list, because on this deployment it is the default |
| `packages/i18n/src/core/set-language.ts` | sets `document.documentElement.dir` when the language changes |
| `packages/i18n/src/core/instance.ts` | applies `lang`/`dir` at module import (before the first React render, from the stored language) and again once i18next resolves — so a Hebrew user never sees a left-to-right flash |
| `packages/i18n/src/index.ts` | exports the direction helpers |

Whole files, not diffs: the files are tiny, and a diff against a moving upstream is a patch that
applies cleanly one day and silently corrupts the next. Every edit is marked `BINA PATCH` so a
rebase can find it.

## Build

The workflow runs on `ubuntu-24.04-arm` — the office is Apple Silicon, and emulating this build on
an amd64 runner takes hours.

```bash
# locally, against a clone:
git clone --depth 1 --branch "$(cat VERSION)" https://github.com/makeplane/plane.git upstream
python3 tools/apply.py upstream
python3 tools/check-parity.py upstream/packages/i18n/src/locales/en locales/he
```

It publishes two things:

1. **a release asset** — `plane-web-he-<tag>.tar.gz`, the built SPA. Public, anonymous, no registry
   login. This is what the office consumes.
2. **an image on GHCR** — the same bytes. Warns loudly if it could not flip the package to public.

## What is NOT fixed (deliberately, for now)

* **Layouts that do not mirror.** Setting `dir="rtl"` flips flexbox order, text alignment and
  logical spacing, which covers most of the app — but upstream markup uses physical utilities
  (`ml-*`, `mr-*`, `left-*`, `text-left`) and physical icons in places, so individual screens need
  `rtl:` variants. That is per-screen work, done against a running instance, not in one patch.
* **Hebrew glyphs.** The font stack is Inter + Material Symbols + IBM Plex Mono; Inter has no
  Hebrew, so Hebrew falls back to a system face. It renders — it just is not a chosen typeface yet.
* **Upstream's own checks.** `pnpm check:sync --ci` in `packages/i18n` validates the same parity
  `tools/check-parity.py` does; running the monorepo's toolchain in CI is a later refinement.

## Licence

The patched work is a derivative of Plane, **AGPL-3.0-only**. This repository is public for exactly
that reason: offering the modified frontend as a network service carries a source-availability
obligation, and a public repo satisfies it.
