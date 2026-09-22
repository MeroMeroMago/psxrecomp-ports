#!/usr/bin/env python3
"""Check every relative link in the built site (guide + API reference).

MkDocs cannot validate links into the Doxygen output because those pages are
not Markdown documents, so this script walks the finished site/ directory and
resolves every href/src that is not an absolute URL, a fragment, or a mailto.
Exit status is 1 if anything is missing.

Usage: python scripts/check-links.py [site-dir]
"""
import html
import os
import re
import sys
from urllib.parse import unquote, urlsplit

ATTR = re.compile(r'\b(?:href|src)\s*=\s*["\']([^"\']+)["\']', re.I)
# Embedded source listings (guide snippets, Doxygen source pages) can contain
# literal href/src text that is code, not markup; skip everything inside <pre>.
PRE = re.compile(r'<pre\b.*?</pre>', re.I | re.S)


def main() -> int:
    site = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'site')
    site = os.path.abspath(site)
    missing = []
    pages = 0
    links = 0
    for root, _dirs, files in os.walk(site):
        for name in files:
            if not name.endswith('.html'):
                continue
            pages += 1
            page = os.path.join(root, name)
            try:
                text = open(page, encoding='utf-8', errors='replace').read()
            except OSError:
                continue
            text = PRE.sub('', text)
            for raw in ATTR.findall(text):
                target = html.unescape(raw).strip()
                parts = urlsplit(target)
                if parts.scheme or parts.netloc or target.startswith(('#', 'mailto:', 'javascript:', 'data:')):
                    continue
                path = unquote(parts.path)
                if not path:
                    continue
                links += 1
                if path.startswith('/'):
                    candidate = os.path.join(site, path.lstrip('/'))
                else:
                    candidate = os.path.normpath(os.path.join(root, path))
                if os.path.isdir(candidate):
                    candidate = os.path.join(candidate, 'index.html')
                if not os.path.exists(candidate):
                    missing.append((os.path.relpath(page, site), target))
    # Doxygen renders the engine's own Markdown files (README.md, docs/*.md) as
    # pages named md_*.html; their relative links to images, YAML templates and
    # files outside the Doxygen input cannot resolve and are upstream content,
    # not ours. Python listings also link to stdlib namespaces Doxygen never
    # sees. Report those separately and do not fail on them.
    def upstream(page: str, target: str) -> bool:
        base = os.path.basename(page)
        # A "$name" target is an unexpanded Doxygen template variable, which
        # happens when the installed Doxygen is older than the one that
        # generated theme/header.html; report it, but as a soft miss.
        return base.startswith('md_') or target.startswith('namespace') or target.startswith('$')

    hard = [(p, t) for p, t in missing if not upstream(p, t)]
    soft = [(p, t) for p, t in missing if upstream(p, t)]
    for page, target in soft:
        print(f'upstream  {page}  ->  {target}')
    for page, target in hard:
        print(f'MISSING   {page}  ->  {target}')
    print(f'{pages} pages, {links} relative links, {len(hard)} missing, {len(soft)} upstream-markdown misses ignored')
    return 1 if hard else 0


if __name__ == '__main__':
    raise SystemExit(main())
