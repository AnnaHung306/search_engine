"""fix_encoding.py — one-off repair for the v7 crawl (2026-10-21).

frida.re serves HTML without a charset, so requests decoded the UTF-8 bytes
as ISO-8859-1 ("•" became "â¢"). crawler.py now uses the detected encoding;
this script repairs the already-saved pages.json in place, re-decoding a
field only when the round trip latin-1 -> utf-8 succeeds.
"""
import json, os
P = os.path.join(os.path.dirname(__file__), "..", "data", "pages.json")

import re
# a UTF-8 multi-byte sequence mis-read as Latin-1/cp1252 looks like
# a lead byte \xc2-\xf4 followed by 1-3 continuation bytes \x80-\xbf
_MOJI = re.compile("[\u00c2-\u00f4][\u0080-\u00bf]{1,3}")


def _seg(m):
    try:
        return m.group(0).encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return m.group(0)


def fix(s):
    """Whole-string round trip first; if the string also contains real
    non-Latin-1 characters, repair each mojibake segment on its own."""
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return _MOJI.sub(_seg, s)

pages = json.load(open(P, encoding="utf-8"))
n = 0
for p in pages:
    for k in ("title", "text"):
        new = fix(p[k])
        if new != p[k]:
            p[k] = new; n += 1
json.dump(pages, open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("repaired fields:", n)
