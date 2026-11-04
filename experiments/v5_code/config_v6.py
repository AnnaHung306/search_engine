SEED_URLS = [
    "https://www.kali.org/tools/",
    "https://www.kali.org/docs/",
    "https://www.kali.org/docs/tools/",
    "https://www.kali.org/docs/general-use/",
    "https://www.kali.org/docs/introduction/",
    "https://www.kali.org/docs/troubleshooting/",
    "https://nmap.org/book/toc.html",
    "https://docs.metasploit.com/",
]
ALLOWED_HOSTS = {"www.kali.org", "nmap.org", "docs.metasploit.com"}
ALLOWED_PATH_PREFIXES = {
    "www.kali.org": ("/tools/", "/docs/"),
    "nmap.org": ("/book/",),
    "docs.metasploit.com": ("/",),
}
EXCLUDED_PATH_PREFIXES = {
    "www.kali.org": ("/docs/nethunter/", "/docs/arm/", "/docs/installation/",
                     "/docs/virtualization/", "/docs/usb/", "/docs/cloud/"),
}
MAX_PAGES_PER_HOST = {"www.kali.org": 600, "nmap.org": 200, "docs.metasploit.com": 200}
USER_AGENT = "NUK-IR-SearchEngine/1.0 (course project; contact: tree.gavin@gmail.com)"
DELAY_PER_HOST = 2.0
TIMEOUT = 10
MAX_VALID_PAGES = 1000
MAX_ATTEMPTS = 1500
MIN_TEXT_CHARS = 200
