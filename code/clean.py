"""clean.py — strip site boilerplate from page text BEFORE indexing (v6).

Why: every Kali tool page ends with the same template blocks. Two of them
pollute the index:
  * "Learn more with OffSec ... PEN-200: 9.3. Common Web Application Attacks ..."
    — a training ad that names attack topics. It put jd-gui (a Java
    decompiler, nothing to do with SQL) in the top 5 for "sql injection tool"
    because its ad said "... SQL Injection RCE".
  * "Updated on: ... Edit this page <previous tool> <next tool>" — the prev/next
    navigation puts OTHER tools' names into every page.
Kali docs add "Author: ... Create a new page <prev title> <next title>", and the
Metasploit API pages repeat "Documentation by YARD 0.9.x".

pages.json (the crawl output) is NOT changed; cleaning happens only when the
indexer reads it, so the crawl statistics stay the same.
"""
import re

_PATTERNS = [
    r"Learn more with OffSec.*?(?=Updated on:|$)",   # Kali training ad block
    r"Edit this page.*$",                            # Kali prev/next tool nav (end of page)
    r"Create a new page.*$",                         # Kali docs prev/next nav
    r"Updated on:\s*\d{4}-[A-Za-z]+-\d+",
    r"Author:\s*\S+",
    r"Table of Contents",
    r"Documentation by YARD[\d. ]*",                 # Metasploit API template
    # v7 new sites
    r"(?:Sponsor Fork Star\s*)+",                    # GTFOBins GitHub buttons
    r"Source \| History\s*$",                        # GTFOBins footer
    r"Edit on GitHub",                               # mitmproxy
    r"Improve this page",                            # Frida
    r"\bPrev\b(?= Chapter| Part| \d)",                # Wireshark guide header nav
]
_BP = re.compile("|".join(_PATTERNS), re.S)


def clean_text(text):
    return re.sub(r"\s+", " ", _BP.sub(" ", text)).strip()


if __name__ == "__main__":
    demo = ("Packages and Binaries: laudanum Collection of injectable web files ... "
            "Learn more with OffSec Want to learn more about laudanum? PEN-200: 9.3. "
            "Common Web Application Attacks WEB-200 course Updated on: 2025-Dec-09 "
            "Edit this page knocker lbd")
    print(clean_text(demo))


# ---------------------------------------------------------------- v7.1 hub pages
# "Hub" pages are navigation pages whose body is only a list of links to other
# pages (section tables of contents, the full tool/binary/module listings).
# They are kept in the collection (they were crawled and they lead the crawler
# to the real pages) but are NOT returned as results: a user asking "sql
# injection tool" wants the sqlmap page, not a menu that happens to list it.
# Short menus are exactly what cosine similarity over-rewards (34-49 tokens,
# every word a keyword), so this is the biggest single fix for pure TF-IDF.
HUB_URLS = {
    "https://www.kali.org/tools/",              # list of all Kali tools
    "https://www.kali.org/tools/all-tools/",    # same, alphabetical
    "https://gtfobins.org/",                    # list of all GTFOBins binaries
    "https://nmap.org/book/toc.html",           # book table of contents
    "https://docs.metasploit.com/docs/modules.html",   # list of 7,000+ modules
}


def is_hub(url, text):
    """Section index pages on docs.metasploit.com start with 'Table of contents'
    followed only by child-page titles; the rest are the listing pages above."""
    return url in HUB_URLS or text.lstrip().lower().startswith("table of contents")
