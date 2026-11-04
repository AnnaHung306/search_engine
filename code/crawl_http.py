"""One request gate for content, robots and redirects. TP §2; U2 p.22–31.

No network-error allow-all policy. A temporary robots failure or rate limit
pauses that host for this crawl; a new crawl can try it again explicitly.
"""
import time
from collections import Counter
from datetime import timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin, urlsplit
from protego import Protego

import requests

from crawl_urls import in_scope, normalize


class FetchRejected(Exception):
    def __init__(self, reason, url):
        self.reason, self.url = reason, url
        super().__init__(f"{reason}: {url}")


class AttemptLimitReached(Exception):
    pass


def retry_after(value, now):
    """HTTP §10.2.3: seconds or HTTP date. Invalid/missing is explicit None."""
    if value is None:
        return None
    value = value.strip()
    if value.isdigit():
        return float(value)
    try:
        date = parsedate_to_datetime(value)
        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)
        return max(0.0, date.timestamp() - now)
    except (ValueError, TypeError, OverflowError):
        return None


class CrawlHTTP:
    """fetch(url) enforces every hop; dependencies also support controlled checks."""
    def __init__(self, settings, emit, *, session=None, clock=time.monotonic,
                 wall=time.time, sleep=time.sleep, state=None):
        self.settings, self.emit = settings, emit
        self.session = session if session is not None else requests.Session()
        self.session.headers.update({"User-Agent": settings.USER_AGENT})
        self.clock, self.wall, self.sleep = clock, wall, sleep
        state = state or {}
        self.counts = Counter(state.get("counts", {}))
        self.blocked = dict(state.get("blocked", {}))
        self.last_wall = dict(state.get("last_finished_at", {}))
        self.last = {h: clock() - max(0.0, wall() - finished)
                     for h, finished in self.last_wall.items()}
        self.robots = {}
        self.delays = dict(state.get("delays", {}))

    @property
    def attempts(self):
        return self.counts["total"]

    def state(self):
        return {"counts": dict(self.counts), "blocked": self.blocked,
                "last_finished_at": self.last_wall, "delays": self.delays}

    def _block(self, host, reason, **details):
        self.blocked[host] = {"reason": reason, **details}
        self.emit({"status": "host_paused", "host": host, "reason": reason, **details})

    def _send(self, url, kind):
        if self.attempts >= self.settings.MAX_ATTEMPTS:
            raise AttemptLimitReached()
        host = urlsplit(url).netloc
        if host in self.blocked:
            raise FetchRejected("host_paused", url)
        delay = max(self.settings.DELAY_PER_HOST, self.delays.get(host, 0.0))
        remaining = delay - (self.clock() - self.last.get(host, float("-inf")))
        if remaining > 0:
            self.sleep(remaining)
        started = self.wall()
        self.counts["total"] += 1
        self.counts[kind] += 1
        try:
            response = self.session.get(url, timeout=self.settings.TIMEOUT,
                                        allow_redirects=False)
        except requests.RequestException as error:
            self.counts["network_failures"] += 1
            self.emit({"status": "http_request", "kind": kind, "url": url,
                       "started_at": started, "finished_at": self.wall(),
                       "error": type(error).__name__})
            raise FetchRejected("network_error", url) from error
        finally:
            self.last[host] = self.clock()
            self.last_wall[host] = self.wall()
        self.emit({"status": "http_request", "kind": kind, "url": url,
                   "started_at": started, "finished_at": self.last_wall[host],
                   "code": response.status_code})
        if response.status_code >= 400 and not (kind == "robots" and response.status_code in (404, 410)):
            self.counts["http_failures"] += 1
        if response.status_code == 429:
            self.counts["rate_limited"] += 1
            self._block(host, "rate_limit", retry_after_seconds=retry_after(
                response.headers.get("Retry-After"), self.wall()),
                retry_after_raw=response.headers.get("Retry-After"))
            response.close()
            raise FetchRejected("rate_limit", url)
        return response

    def _robots(self, url):
        origin = "{0.scheme}://{0.netloc}".format(urlsplit(url))
        host = urlsplit(url).netloc
        if origin in self.robots:
            return self.robots[origin]
        try:
            response = self._follow(origin + "/robots.txt", "robots")
        except FetchRejected:
            if host not in self.blocked:
                self._block(host, "robots_unreachable")
            raise
        try:
            if response.status_code == 200:
                if len(response.content) > 512 * 1024:
                    self._block(host, "robots_too_large")
                    raise FetchRejected("robots_too_large", url)
                try:
                    text = response.content.decode("utf-8-sig")
                except UnicodeDecodeError as error:
                    self._block(host, "robots_invalid_encoding")
                    raise FetchRejected("robots_invalid_encoding", url) from error
                rp = Protego.parse(text)
                self.delays[host] = max(self.delays.get(host, 0.0),
                    float(rp.crawl_delay(self.settings.USER_AGENT) or 0.0))
                rate = rp.request_rate(self.settings.USER_AGENT)
                if rate and rate.requests > 0:
                    self.delays[host] = max(self.delays[host], rate.seconds / rate.requests)
            elif response.status_code in (404, 410):
                rp = Protego.parse("")  # declared absent, distinct from network failure
                self.emit({"status": "robots_absent", "url": origin + "/robots.txt",
                           "code": response.status_code})
            else:
                self._block(host, "robots_unavailable", code=response.status_code)
                raise FetchRejected("robots_unavailable", url)
        finally:
            response.close()
        self.robots[origin] = rp
        return rp

    def _follow(self, url, kind):
        seen = set()
        for _ in range(9):  # initial request + at most eight redirects
            try:
                url = normalize(url)
            except (ValueError, TypeError) as error:
                raise FetchRejected("invalid_url", url) from error
            if url in seen:
                raise FetchRejected("redirect_loop", url)
            seen.add(url)
            if not in_scope(url, self.settings, robots=kind == "robots"):
                raise FetchRejected("redirect_out_of_scope" if len(seen) > 1 else "out_of_scope", url)
            if kind == "content" and not self._robots(url).can_fetch(url, self.settings.USER_AGENT):
                raise FetchRejected("robots_disallowed", url)
            response = self._send(url, kind)
            if response.status_code not in (301, 302, 303, 307, 308):
                return response
            location = response.headers.get("Location")
            response.close()
            if not location:
                raise FetchRejected("redirect_without_location", url)
            url = urljoin(url, location)
        raise FetchRejected("redirect_limit", url)

    def fetch(self, url):
        return self._follow(url, "content")
