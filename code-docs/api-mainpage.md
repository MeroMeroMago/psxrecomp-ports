# API reference {#mainpage}

This is the generated reference for two code bases, indexed together so that a
reader can follow a call from the release kit into the engine:

| Tree | What it is | Where it comes from |
|---|---|---|
| `docs/`, `scripts/`, `kits/diablo-usa/` | The **psxrecomp-ports** glue: the catalog web page, the catalog validation/render scripts, and the Diablo owned-input kit (PowerShell setup, Python disc extractor, CMake). | This repository. |
| `runtime/`, `recompiler/`, `host/`, `tools/`, `docs/` (engine) | The **PSXRecomp engine**: the MIPS-to-C recompiler, the PS1 hardware runtime, the code-generation host, and its Python tooling. | Alexbeav/psxrecomp at the commit pinned in `code-docs/engine-pin.json`. |

The narrative guide, with architecture diagrams and reading paths, is one level
up: [open the guide](../index.html).

## How to read the code here

- **Files** (sidebar → *Files*) lists every source file with a syntax-highlighted
  listing. Identifiers in listings are links; hovering shows a tooltip with the
  declaration.
- **Call graphs** are drawn under each function: *calls* (what it invokes) and
  *called by* (who invokes it). Nodes are clickable.
- **Include graphs** under each file show what it depends on and what depends on it.
- **Directory graphs** (sidebar → *Files* → a directory) show how the subtrees
  hang together.
- Use the search box (top right) to jump to any function, struct, or file.

PowerShell (`.ps1`) and JavaScript (`.js`, `.mjs`) files are not natively
understood by Doxygen. They pass through small line-preserving filters
(`code-docs/filters/`) so that their functions and call graphs appear; the
source listings show the original files unchanged.
