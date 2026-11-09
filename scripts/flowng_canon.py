#!/usr/bin/env python3
"""Canonical form of a FlowNG HTML file, used to decide whether a shared file contains released code.

A shared file is released FlowNG code plus one data block (<script id="flowng-bundle">). The app writes
it from the running page's DOM, so its HTML text differs from the source file in harmless ways
(attribute quoting, implied end tags, entity forms). The canonical form removes those differences:

  - the data block is removed (it is validated separately) but only in its exact written form, once, directly
    before the loader script; anything else that looks like a data block stays in the code and changes the hash,
  - the <title> text is ignored (it is the author's file name),
  - the one run-time layout attribute the app adds to <html> (--header-h) is ignored,
  - the HTML is tokenised and re-written as: start tags with attributes sorted, text (whitespace
    collapsed outside <script>/<style>), comments. End tags and parser-inserted <tbody> are ignored.

Script and style text is kept exactly, so any change to the code changes the hash.
"""
import hashlib
import re
from html.parser import HTMLParser

VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}
# The data block as the app writes it. The body has no '<' (the app writes it as \u003c), so it cannot contain a tag,
# a comment opener or a script-escape sequence, and every HTML parser agrees where it ends.
BUNDLE_RE = re.compile(r'<script id="flowng-bundle" type="application/json">([^<]*)</script>')
LOADER_AFTER = '\n<script id="flowng-bundle-loader"'
# End tags kept in the token stream: elements whose parsing mode (raw text, text, template) matters for safety.
KEEP_END = {'script', 'style', 'title', 'noscript', 'textarea', 'template', 'iframe', 'select', 'xmp', 'plaintext'}


def split_bundle(html: str):
    """Return (code_without_bundle, bundle_body or None, problem or None). Exactly one well-placed block is required."""
    ms = list(BUNDLE_RE.finditer(html))
    if not ms:
        return html, None, None                       # a source file: no data block
    if len(ms) > 1:
        return html, None, 'more than one data block'
    m = ms[0]
    if not html.startswith(LOADER_AFTER, m.end()):
        return html, None, 'data block is not directly before the loader script'
    return html[:m.start()] + html[m.end():], m.group(1), None


class _Canon(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.raw_tag = None     # inside script/style
        self.in_title = False
        self.buf = []

    def _flush_text(self):
        if self.buf:
            t = ''.join(self.buf); self.buf = []
            if self.raw_tag:
                self.out.append(('raw', t))
            else:
                t = re.sub(r'\s+', ' ', t).strip()
                if t:
                    self.out.append(('text', t))

    def handle_starttag(self, tag, attrs):
        self._flush_text()
        a = dict(attrs)
        if tag == 'tbody': return                       # inserted by the browser's HTML parser
        if tag == 'title':
            self.in_title = True
        if tag == 'html':
            # The app sets --header-h on <html> at run time (before the page is captured for sharing); it is layout only.
            attrs = [(k, v) for k, v in attrs if not (k == 'style' and re.fullmatch(r'\s*--header-h:\s*[0-9.]+px;?\s*', v or ''))]
        self.out.append(('start', tag, tuple(sorted((k, v if v is not None else '') for k, v in attrs))))
        if tag in ('script', 'style'):
            self.raw_tag = tag

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        self._flush_text()
        if tag in KEEP_END:
            self.out.append(('end', tag))
        if tag in ('script', 'style'):
            self.raw_tag = None
        if tag == 'title':
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            return
        self.buf.append(data)

    def handle_comment(self, data):
        self._flush_text()
        self.out.append(('comment', data))

    def handle_decl(self, decl):
        self._flush_text()
        self.out.append(('decl', decl.lower()))

    def close(self):
        super().close(); self._flush_text()


def canon_tokens(html: str):
    code, body, problem = split_bundle(html)
    p = _Canon()
    p.feed(code); p.close()
    return p.out, (0 if body is None and problem is None else 1), problem


def canon_hash(html: str):
    """(hash, number of data blocks found (0 for a source file), problem or None). A problem means: do not trust."""
    toks, nbundle, problem = canon_tokens(html)
    h = hashlib.sha256()
    for t in toks:
        h.update(repr(t).encode('utf-8')); h.update(b'\n')
    return h.hexdigest(), nbundle, problem


def lite_strip(src: str) -> str:
    """What 'Locked viewer' removes (same rules as the app's share export)."""
    js = re.compile(r'/\*@li' + r'te:begin\*/[\s\S]*?/\*@li' + r'te:end\*/\n?')
    ht = re.compile(r'<!--@li' + r'te:begin-->[\s\S]*?<!--@li' + r'te:end-->\n?')
    out = ht.sub('', js.sub('', src))
    return ''.join(out.split('<button class="primary" onclick="document.getElementById(\'file-input\').click()">Open FCS File</button>'))
