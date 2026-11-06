"""synonyms.py — small hand-made domain synonym table for QUERY expansion.

Why: weak query "wifi password cracking" missed aircrack-ng because that page
says "WPA / WEP / key / handshake" instead of "wifi / password". Expansion adds
related terms to the query with a LOWER weight (EXPANSION_WEIGHT), so original
words still dominate. Documents are not changed; tokens still go through the
same preprocess.tokenize(), so docs and queries stay consistent.
"""
EXPANSION_WEIGHT = 0.5

SYNONYMS = {
    "wifi": ["wireless", "wpa", "wep", "802.11", "wlan"],
    "wi-fi": ["wireless", "wpa", "wep", "802.11", "wlan"],
    "wireless": ["wifi", "802.11", "wlan"],
    "password": ["passphrase", "key", "credential"],
    "passwords": ["passphrase", "key", "credential"],
    "cracking": ["crack", "cracker", "recover", "brute"],
    "crack": ["cracking", "cracker", "recover"],
    "sniffer": ["sniff", "sniffing", "capture", "pcap"],
    "sniffing": ["sniff", "sniffer", "capture", "pcap"],
    "scanning": ["scan", "scanner"],
    "scan": ["scanning", "scanner"],
    "scanner": ["scan", "scanning"],
    "enumeration": ["enumerate", "discovery", "bruteforce", "fuzz"],
    "directory": ["directories", "dir", "path", "content"],
    "exploit": ["exploitation", "payload"],
    "vulnerability": ["vulnerabilities", "vuln", "cve"],
    "deauthentication": ["deauth", "disassociation"],
    "deauth": ["deauthentication"],
    "brute": ["bruteforce", "dictionary", "wordlist"],
    "login": ["authentication", "logon", "credential"],
    "hash": ["hashes", "ntlm", "md5"],
    "packet": ["packets", "traffic"],
    "sql": ["sqli"],
    "injection": ["sqli", "inject"],
}

# Chinese -> English, so a demo audience typing Chinese still gets results.
ZH = {
    "破解": "crack", "密碼": "password", "無線": "wireless", "掃描": "scan",
    "連接埠": "port", "埠": "port", "漏洞": "vulnerability", "注入": "injection",
    "暴力": "brute force", "登入": "login", "封包": "packet", "監聽": "sniffer",
    "側錄": "sniffer", "目錄": "directory", "列舉": "enumeration", "雜湊": "hash",
    "網站": "web", "網頁": "web", "攻擊": "attack", "工具": "tool", "滲透": "penetration",
}


def translate_zh(query):
    """Replace known Chinese words with English (longest first)."""
    for zh in sorted(ZH, key=len, reverse=True):
        if zh in query:
            query = query.replace(zh, " " + ZH[zh] + " ")
    return query


def expand(terms):
    """terms: list of tokens -> dict term -> weight (originals 1.0, expansions 0.5)."""
    w = {}
    for t in terms:
        w[t] = max(w.get(t, 0), 1.0)
    for t in terms:
        for s in SYNONYMS.get(t, []):
            if s not in w:
                w[s] = EXPANSION_WEIGHT
    return w
