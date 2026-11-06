# v7 (2026-10-21): deepen the SAME pentest-tool theme with packet interception
# (Wireshark guide, mitmproxy), mobile/app dynamic analysis (Frida) and
# post-exploitation / reverse shells (GTFOBins). 8 seeds, 7 hosts, <= 1000 pages.
# Kali cap lowered 600 -> 430 so it no longer dominates; Metasploit /api/
# developer reference excluded (not useful for "which tool / how to" queries).
SEED_URLS = [
    "https://www.kali.org/tools/",
    "https://www.kali.org/docs/",
    "https://nmap.org/book/toc.html",
    "https://docs.metasploit.com/",
    "https://www.wireshark.org/docs/wsug_html_chunked/",
    "https://docs.mitmproxy.org/stable/",
    "https://frida.re/docs/home/",
    "https://gtfobins.org/",
]
ALLOWED_HOSTS = {"www.kali.org", "nmap.org", "docs.metasploit.com",
                 "www.wireshark.org", "docs.mitmproxy.org", "frida.re", "gtfobins.org"}
ALLOWED_PATH_PREFIXES = {
    "www.kali.org": ("/tools/", "/docs/"),
    "nmap.org": ("/book/",),
    "docs.metasploit.com": ("/",),
    "www.wireshark.org": ("/docs/wsug_html_chunked/",),
    "docs.mitmproxy.org": ("/stable/",),
    "frida.re": ("/docs/",),
    "gtfobins.org": ("/",),
}
EXCLUDED_PATH_PREFIXES = {
    "www.kali.org": ("/docs/nethunter/", "/docs/arm/", "/docs/installation/",
                     "/docs/virtualization/", "/docs/usb/", "/docs/cloud/"),
    "docs.metasploit.com": ("/api/",),
    "docs.mitmproxy.org": ("/stable/api/",),
}
MAX_PAGES_PER_HOST = {"www.kali.org": 430, "nmap.org": 150, "docs.metasploit.com": 150,
                      "www.wireshark.org": 80, "docs.mitmproxy.org": 50,
                      "frida.re": 40, "gtfobins.org": 100}
USER_AGENT = "NUK-IR-SearchEngine/1.0 (course project; contact: tree.gavin@gmail.com)"
DELAY_PER_HOST = 2.0
TIMEOUT = 10
MAX_VALID_PAGES = 1000
MAX_ATTEMPTS = 2500
MIN_TEXT_CHARS = 200
