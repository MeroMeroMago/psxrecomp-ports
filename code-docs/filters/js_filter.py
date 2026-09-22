#!/usr/bin/env python3
"""Doxygen input filter: make modern JavaScript digestible by the C++ parser.

Doxygen has no JavaScript parser. With EXTENSION_MAPPING js=C++ its C++ parser
gets close enough to list "function name(...)" definitions and draw call
graphs, provided the constructs that derail it are removed. This filter does
that while preserving line count (the source browser shows the original file):
  * contents of template literals (`...`, possibly multi-line) and of quoted
    strings are blanked to spaces, so HTML and braces inside them are ignored
  * an outer IIFE wrapper "(() => {" ... "})();" is made transparent
  * "const name = (args) => {" is rewritten to "function name(args) {" and
    "const name = (args) => expr;" to a one-line function returning expr
  * function bodies are kept (so calls are visible); every other file-scope
    line -- imports, top-level statements, event wiring -- becomes a "//"
    comment so the parser stays in sync
"""
import re
import sys

ARROW_BLOCK = re.compile(r'^(\s*)(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\(([^)]*)\)\s*=>\s*\{\s*$')
ARROW_EXPR = re.compile(r'^(\s*)(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\(([^)]*)\)\s*=>\s*(.+)$')
FUNC = re.compile(r'^(\s*)(?:async\s+)?function\s*\*?\s*([A-Za-z_$][\w$]*)\s*\(([^)]*)\)\s*\{')
IIFE_OPEN = re.compile(r'^\s*\(\s*(?:async\s*)?(?:\(\s*\)\s*=>|function\s*\(\s*\))\s*\{\s*$')
IIFE_CLOSE = re.compile(r'^\s*\}\s*\)\s*\(\s*\)\s*;?\s*$')


def blank_literals(text: str) -> str:
    out = []
    i = 0
    n = len(text)
    mode = None  # None | '`' | '"' | "'" | '//' | '/*'
    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ''
        if mode is None:
            out.append(c)
            if c == '/' and nxt == '/':
                mode = '//'
            elif c == '/' and nxt == '*':
                mode = '/*'
            elif c in ('`', '"', "'"):
                mode = c
        elif mode == '//':
            out.append(c)
            if c == '\n':
                mode = None
        elif mode == '/*':
            out.append(c)
            if c == '*' and nxt == '/':
                out.append('/')
                i += 1
                mode = None
        else:
            if c == '\\' and nxt:
                out.append('  ' if nxt != '\n' else ' \n')
                i += 1
            elif c == mode:
                mode = None
                out.append(c)
            elif c == '\n':
                out.append('\n')
            else:
                out.append(' ')
        i += 1
    return ''.join(out)


def main() -> int:
    with open(sys.argv[1], encoding='utf-8-sig', errors='replace') as fh:
        text = fh.read()
    text = blank_literals(text)
    out = []
    in_func = False
    depth = 0
    stmt_depth = 0
    in_block_comment = False
    for line in text.split('\n'):
        s = line.strip()
        indent = line[:len(line) - len(line.lstrip())]

        if in_block_comment:
            out.append(line)
            if '*/' in line:
                in_block_comment = False
            continue
        if s.startswith('/*'):
            out.append(line)
            if '*/' not in line:
                in_block_comment = True
            continue
        if s.startswith('//') or not s:
            out.append(line)
            continue

        if in_func:
            out.append(line)
            depth += line.count('{') - line.count('}')
            if depth <= 0:
                in_func = False
            continue

        # File scope (or inside a transparent IIFE).
        if IIFE_OPEN.match(line) or IIFE_CLOSE.match(line):
            out.append(indent + '// ' + s)
            continue
        if stmt_depth == 0:
            m = ARROW_BLOCK.match(line)
            if m:
                new = f'{m.group(1)}function {m.group(2)}({m.group(3)}) {{'
                out.append(new)
                depth = 1
                in_func = True
                continue
            m = ARROW_EXPR.match(line)
            if m and not m.group(4).lstrip().startswith('{'):
                body = m.group(4).rstrip()
                if body.endswith(';'):
                    body = body[:-1]
                out.append(f'{m.group(1)}function {m.group(2)}({m.group(3)}) {{ return {body}; }}')
                continue
            m = FUNC.match(line)
            if m:
                out.append(f'{m.group(1)}function {m.group(2)}({m.group(3)}) {{' + line[m.end():])
                depth = line.count('{') - line.count('}')
                in_func = depth > 0
                continue
        # Anything else at file scope: comment it out, tracking multi-line statements.
        stmt_depth += line.count('{') - line.count('}')
        if stmt_depth < 0:
            stmt_depth = 0
        out.append(indent + '// ' + s)
    sys.stdout.write('\n'.join(out))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
