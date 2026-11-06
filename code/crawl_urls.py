"""URL identity and scope. References: TP §2; U2 p.29–31; HTTP §4.2.3."""
from urllib.parse import urljoin, urlsplit, urlunsplit, unquote

from requests import Request

import config


def normalize(url, base=None):
    parts = urlsplit(urljoin(base, url) if base else url)
    scheme = parts.scheme.lower()
    if scheme not in ("http", "https"):
        raise ValueError("Only public HTTP/HTTPS URLs are supported")
    if not parts.hostname or parts.username is not None or parts.password is not None:
        raise ValueError("A public URL must have a hostname and no user information")
    host = parts.hostname.lower()
    port = parts.port  # malformed ports raise ValueError before any request
    authority = f"[{host}]" if ":" in host else host
    if port is not None and (scheme, port) not in (("http", 80), ("https", 443)):
        authority += f":{port}"
    decoded_path = unquote(parts.path)
    if "\\" in decoded_path or any(part in (".", "..") for part in decoded_path.split("/")):
        raise ValueError("Ambiguous absolute dot-segment/backslash path")
    absolute = urlunsplit((scheme, authority, parts.path or "/", parts.query, ""))
    # Match the actual Requests URL before robots and scope checks, not only urlsplit's spelling.
    return Request("GET", absolute).prepare().url


def in_scope(url, settings=config, *, robots=False):
    try:
        parts = urlsplit(normalize(url))
    except (ValueError, TypeError):
        return False
    if parts.scheme not in ("http", "https") or parts.netloc not in settings.ALLOWED_HOSTS:
        return False
    if robots:
        return True  # /robots.txt is outside content prefixes, still inside host allowlist
    prefixes = settings.ALLOWED_PATH_PREFIXES.get(parts.netloc, ())
    excluded = settings.EXCLUDED_PATH_PREFIXES.get(parts.netloc, ())
    return (not prefixes or parts.path.startswith(prefixes)) and not parts.path.startswith(excluded)
