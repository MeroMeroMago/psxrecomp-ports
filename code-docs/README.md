# code-docs — read the code through the documentation

A generated documentation site for this repository's glue code **and** the
PSXRecomp engine it downloads. Two layers:

- **Guide** (`guide/`, MkDocs Material): architecture pages with Mermaid
  diagrams, embedded source, and guided reading paths.
- **API reference** (`Doxyfile`, Doxygen + Graphviz): every file with a
  syntax-highlighted listing, call graphs, caller graphs, include graphs, and
  directory graphs. PowerShell and JavaScript go through the line-preserving
  filters in `filters/` so their functions and calls appear too.

```
code-docs/
├─ guide/            MkDocs pages (docs_dir)
├─ mkdocs.yml        guide configuration
├─ Doxyfile          API reference configuration (run from this directory)
├─ api-mainpage.md   landing page of the API reference
├─ filters/          ps1_filter.py, js_filter.py
├─ theme/            doxygen-awesome (MIT) + header.html + custom.css
├─ scripts/          fetch-engine.ps1, build.ps1
├─ engine-pin.json   which Alexbeav/psxrecomp commit is documented
├─ .engine/          engine checkout (git-ignored, created by fetch-engine.ps1)
└─ site/             build output (git-ignored); site/api/ is the reference
```

Build: `pwsh code-docs/scripts/build.ps1 -Open` (needs Python with
`mkdocs-material`, Doxygen, Graphviz). Details and CI notes:
`guide/building.md`.

Why not `docs/`? That folder is the public GitHub Pages catalog; this site is
published separately by `.github/workflows/code-docs.yml`.
