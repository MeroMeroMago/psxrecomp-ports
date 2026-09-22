# Building these docs

The site is two generators glued together. Everything lives under `code-docs/`;
the public catalog in `docs/` is untouched.

| Piece | Tool | Input | Output |
|---|---|---|---|
| Narrative guide (this site) | [MkDocs](https://www.mkdocs.org/) with [Material](https://squidfunk.github.io/mkdocs-material/), Mermaid diagrams, source snippets | `code-docs/guide/*.md`, `code-docs/mkdocs.yml` | `code-docs/site/` |
| API reference | [Doxygen](https://www.doxygen.nl/) with [Graphviz](https://graphviz.org/) and the [doxygen-awesome](https://github.com/jothepro/doxygen-awesome-css) theme | `code-docs/Doxyfile`, this repo's glue code, the engine checkout | `code-docs/site/api/` |

## Prerequisites

- Python 3.10+ with `pip install mkdocs-material`
- Doxygen 1.9.1 or newer (tested with 1.10)
- Graphviz (`dot`) on `PATH` or in `C:\Program Files\Graphviz\bin`
- Git, to fetch the engine

## Build

```powershell
pwsh code-docs/scripts/build.ps1 -Open
```

The script fetches the engine at the pinned commit into `code-docs/.engine`
(git-ignored), runs `mkdocs build --strict`, then `doxygen`. The full Doxygen
pass with call graphs over the engine takes a while; use `-SkipDoxygen` while
editing guide pages, `-SkipMkDocs` when only the Doxyfile changed.

Preview the guide with live reload while writing (run from the repository
root so snippet paths resolve):

```powershell
python -m mkdocs serve -f code-docs/mkdocs.yml
```

## Updating the engine pin

Edit `code-docs/engine-pin.json`, then run `scripts/fetch-engine.ps1` and a
full build. Also update `PROJECT_NUMBER` in the Doxyfile and the commit hash in
the GitHub permalinks used by the engine pages (search for the old hash).

## How the pieces connect

- Guide pages embed source with `--8<-- "path:from:to"`; paths are relative
  to the repository root, and `check_paths: true` makes a build fail if a file
  moves. Line numbers in the fence (`linenums="98"`) are set by hand to match.
- Guide pages link to Doxygen pages as `../../api/<name>.html`. Doxygen names a
  file page from its basename: `.` → `_8`, `_` → `__`, upper-case letters →
  `_` plus the lower-case letter (`SETUP.ps1` → `_s_e_t_u_p_8ps1.html`).
- The Doxyfile maps `.ps1`, `.js`, and `.mjs` onto the C++ parser after the
  filters in `code-docs/filters/` rewrite them; both filters preserve line
  numbers so listings and anchors line up.

## Continuous integration

`.github/workflows/code-docs.yml` builds the site on every push to the
`code-docs` branch and on manual dispatch, and publishes it with GitHub Pages
(source: GitHub Actions). On a fork, enable Pages once under *Settings → Pages*
and pick *GitHub Actions* as the source.
