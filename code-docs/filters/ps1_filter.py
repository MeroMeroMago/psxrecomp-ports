#!/usr/bin/env python3
"""Doxygen input filter: rewrite a PowerShell script into C-like text.

Doxygen has no PowerShell parser. This filter turns a .ps1 file into text the
C++ parser accepts well enough to produce a function list and call graphs.
It is line-preserving: Doxygen requires filters to keep line numbers stable so
the source-browser anchors still point at the original lines. The source
browser itself shows the ORIGINAL file (FILTER_SOURCE_FILES = NO).

What comes out:
  * "function Verb-Noun([type]$a, $b) {"  ->  "void Verb_Noun(type a, b) {"
    with the body kept (strings blanked), so calls inside it are visible.
  * calls to functions defined in this file become C-style calls:
    "Install-Artifact $x $y"  ->  "Install_Artifact(x y);"
  * "$Name" -> "Name", "[type]$x" -> "type x".
  * the "param(...)" block becomes "void __script_params__(...)" with
    attributes and default values blanked.
  * the script's top-level "try {" (or first non-assignment statement after the
    last function) opens "void __script_main__() {", closed on the last line,
    so the main body gets a call graph too.
  * every other file-scope line (variable assignments, loose statements) is
    turned into a "//" comment so it cannot derail the parser.
  * "#" comments -> "//", "<# #>" blocks -> "/* */".
"""
import re
import sys

FUNC_DEF = re.compile(r'^(\s*)function\s+([A-Za-z][\w-]*)\s*(\(.*\))?\s*(\{?)(.*)$')
TYPED_VAR = re.compile(r'\[([A-Za-z][\w.]*)(?:\[\])?\]\s*\$([A-Za-z_]\w*)')
PLAIN_VAR = re.compile(r'\$([A-Za-z_]\w*)')


def blank_strings(line: str) -> str:
    """Replace the contents of quoted strings with spaces, keeping length."""
    out = []
    quote = None
    i = 0
    while i < len(line):
        c = line[i]
        if quote is None:
            out.append(c)
            if c in ('"', "'"):
                quote = c
        else:
            if c == quote:
                quote = None
                out.append(c)
            elif c == '`' and quote == '"' and i + 1 < len(line):
                out.append('  ')
                i += 1
            else:
                out.append(' ')
        i += 1
    return ''.join(out)


def main() -> int:
    path = sys.argv[1]
    with open(path, encoding='utf-8-sig', errors='replace') as fh:
        lines = fh.read().split('\n')

    names = [m.group(2) for m in (FUNC_DEF.match(l) for l in lines) if m]
    c_names = [n.replace('-', '_') for n in names]
    alt = '|'.join(map(re.escape, names))
    calt = '|'.join(map(re.escape, c_names))
    name_re = re.compile(r'(?<![\w-])(' + alt + r')(?![\w-])') if names else None
    stmt_call = re.compile(r'^(\s*)(' + calt + r')\s+([^{}]*?)\s*$') if names else None
    paren_call = re.compile(r'\(\s*(' + calt + r')\s+([^()]*)\)') if names else None
    assign_call = re.compile(r'(=\s*)(' + calt + r')\s+([^{};]*?)\s*(?=[};]|$)') if names else None
    last_func_line = max((i for i, l in enumerate(lines) if FUNC_DEF.match(l)), default=-1)

    out = []
    in_block = False        # inside <# #>
    in_params = False       # inside param( ... )
    param_depth = 0
    func_depth = 0          # brace depth inside a kept function / main body
    in_func = False
    main_open = False
    stmt_depth = 0          # brace depth of a commented-out file-scope statement

    def convert_calls(text: str) -> str:
        if not name_re:
            return text
        text = name_re.sub(lambda mm: mm.group(1).replace('-', '_'), text)
        text = stmt_call.sub(lambda mm: f'{mm.group(1)}{mm.group(2)}({mm.group(3)});', text)
        text = paren_call.sub(lambda mm: f'({mm.group(1)}({mm.group(2)}))', text)
        text = assign_call.sub(lambda mm: f'{mm.group(1)}{mm.group(2)}({mm.group(3)})', text)
        return text

    def vars_to_c(text: str) -> str:
        text = TYPED_VAR.sub(r'\1 \2', text)
        text = text.replace('$_', '__it').replace('$PID', 'PID')
        return PLAIN_VAR.sub(r'\1', text)

    for idx, raw in enumerate(lines):
        line = raw.rstrip('\r')
        stripped = line.strip()
        indent = line[:len(line) - len(line.lstrip())]

        # --- comments -------------------------------------------------------
        if in_block:
            if '#>' in line:
                in_block = False
                out.append(line.replace('#>', '*/'))
            else:
                out.append(line)
            continue
        if stripped.startswith('<#'):
            if '#>' in line:
                out.append(line.replace('<#', '/*').replace('#>', '*/'))
            else:
                in_block = True
                out.append(line.replace('<#', '/*'))
            continue
        if stripped.startswith('#'):
            out.append(indent + '//' + stripped[1:])
            continue

        work = blank_strings(line)

        # --- param( ... ) block -> void __script_params__( ... ) ------------
        if not in_func and not main_open and re.match(r'^\s*param\s*\(', work):
            in_params = True
            work = re.sub(r'^(\s*)param\s*\(', r'\1void __script_params__(', work)
            param_depth = work.count('(') - work.count(')')
            out.append(work)
            continue
        if in_params:
            param_depth += work.count('(') - work.count(')')
            if re.match(r'^\s*\[[^\]]*\]\s*$', work) or re.match(r'^\s*\[[A-Za-z]\w*\([^)]*\)\]\s*$', work):
                work = ' ' * len(work)                      # attribute line
            else:
                work = TYPED_VAR.sub(r'\1 \2', work)
                work = PLAIN_VAR.sub(r'\1', work)
                mdef = re.match(r'^(\s*\S+\s+\w+)\s*=.*?(,?)\s*$', work)
                if mdef:
                    work = mdef.group(1) + mdef.group(2)
            if param_depth <= 0:
                in_params = False
                work = work.rstrip() + ' {}' if work.rstrip().endswith(')') else work
            out.append(work)
            continue

        # --- inside a kept function or the main body ------------------------
        if in_func:
            work = vars_to_c(work)
            work = convert_calls(work)
            out.append(work)
            func_depth += work.count('{') - work.count('}')
            if func_depth <= 0 and not main_open:
                in_func = False
            continue

        # --- file scope -----------------------------------------------------
        m = FUNC_DEF.match(work)
        if m and stmt_depth == 0:
            ind, name, params, brace, rest = m.groups()
            params = params or '()'
            params = TYPED_VAR.sub(r'\1 \2', params)
            params = PLAIN_VAR.sub(r'\1', params)
            params = re.sub(r'=\s*@\(\)', '= 0', params)
            work = f'{ind}void {name.replace("-", "_")}{params} {brace}{rest}'
            out.append(work)
            func_depth = work.count('{') - work.count('}')
            in_func = func_depth > 0
            continue

        starts_main = (stmt_depth == 0 and idx > last_func_line and stripped
                       and not stripped.startswith(('}', ')', '['))
                       and not re.match(r'^\$[\w.:]+\s*=', stripped))
        if starts_main:
            main_open = True
            in_func = True
            work = 'void __script_main__() { ' + vars_to_c(convert_calls(work.lstrip()))
            out.append(work)
            func_depth = 1 + work.count('{') - work.count('}')
            continue

        # Anything else at file scope becomes a comment (multi-line statements too).
        stmt_depth += work.count('{') - work.count('}')
        if stmt_depth < 0:
            stmt_depth = 0
        out.append(indent + '// ' + stripped if stripped else line)

    if main_open:
        out[-1] = out[-1] + ' }'
    sys.stdout.write('\n'.join(out))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
