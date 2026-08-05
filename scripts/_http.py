"""Shared HTTP helper for the data-pipeline scripts.

Every pipeline in this directory talks to a third-party API that can rate-limit
us, return a transient 5xx, or drop the connection. They all want the same
behaviour, so it lives here once:

  * retry on connection errors, 429, and 5xx
  * honour ``Retry-After`` when present
  * honour a provider-specific rate-limit reset header when present
    (GitHub sends ``X-RateLimit-Reset`` and signals exhaustion with 403)
  * exponential backoff otherwise
  * give up after ``max_retries`` and raise, so callers decide how to degrade

Requires: requests
"""

from __future__ import annotations

import time

import requests

DEFAULT_MAX_RETRIES = 4
DEFAULT_BACKOFF_BASE = 2  # seconds: 2, 4, 8, 16
# Never wait longer than this for a rate-limit reset; a scheduled job that
# sleeps for an hour is worse than one that fails and retries tomorrow.
MAX_RESET_WAIT = 300


def _rate_limited(resp: requests.Response, remaining_header: str | None) -> bool:
    """True if the response means "you are out of quota" rather than "forbidden"."""
    if resp.status_code == 429:
        return True
    # GitHub returns 403 (not 429) when the hourly quota is spent, distinguished
    # from a genuine permission error by the remaining-requests header.
    if resp.status_code == 403 and remaining_header:
        return resp.headers.get(remaining_header) == "0"
    return False


def _wait_seconds(
    resp: requests.Response,
    attempt: int,
    backoff_base: int,
    reset_header: str | None,
    is_rate_limit: bool,
) -> int:
    backoff = backoff_base ** (attempt + 1)

    retry_after = resp.headers.get("Retry-After")
    if retry_after and retry_after.isdigit():
        return min(int(retry_after), MAX_RESET_WAIT)

    if is_rate_limit and reset_header:
        reset = resp.headers.get(reset_header)
        if reset and reset.isdigit():
            # Header is an absolute epoch timestamp; +1s to land after the reset.
            return max(backoff, min(int(reset) - int(time.time()) + 1, MAX_RESET_WAIT))

    return backoff


def _detail(resp: requests.Response, limit: int = 400) -> str:
    """Short, log-safe rendition of an error response body.

    APIs put the actionable reason in the body, not the status line: Strava
    answers a missing OAuth scope with 403 and
    ``{"errors":[{"resource":"AccessToken","field":"activity:read_permission",
    "code":"missing"}]}``. Without this, a scope problem is indistinguishable
    from a rate limit or an outage — which is exactly how a broken pipeline can
    fail identically for weeks. Only ever called for non-2xx responses.
    """
    body = (resp.text or "").strip().replace("\n", " ")
    if len(body) > limit:
        body = body[:limit] + "…"
    return f"HTTP {resp.status_code} {resp.reason} — {body}" if body else f"HTTP {resp.status_code} {resp.reason}"


def request_with_retry(
    method: str,
    url: str,
    *,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_base: int = DEFAULT_BACKOFF_BASE,
    reset_header: str | None = None,
    remaining_header: str | None = None,
    log=print,
    **kwargs,
) -> requests.Response:
    """Perform an HTTP request, retrying transient failures.

    Returns the successful response. Raises ``requests.RequestException`` (or
    ``HTTPError`` via ``raise_for_status``) once retries are exhausted, and
    raises immediately for non-retryable 4xx such as 401/404. Error responses
    are logged with the provider's own explanation (see ``_detail``).
    """
    for attempt in range(max_retries + 1):
        try:
            resp = requests.request(method, url, **kwargs)
        except requests.RequestException as e:
            if attempt == max_retries:
                raise
            wait = backoff_base ** (attempt + 1)
            log(f"  Network error ({e}); retrying in {wait}s [{attempt + 1}/{max_retries}]")
            time.sleep(wait)
            continue

        is_rate_limit = _rate_limited(resp, remaining_header)
        if is_rate_limit or resp.status_code >= 500:
            if attempt == max_retries:
                raise requests.HTTPError(
                    f"{_detail(resp)} (after {max_retries} retries): {url}", response=resp
                )
            wait = _wait_seconds(resp, attempt, backoff_base, reset_header, is_rate_limit)
            log(f"  {_detail(resp, 200)}; retrying in {wait}s [{attempt + 1}/{max_retries}]")
            time.sleep(wait)
            continue

        if not resp.ok:
            # Non-retryable (401/403/404/…). Surface the provider's reason so the
            # fix is obvious from the log alone.
            log(f"  {_detail(resp)}: {url}")
            raise requests.HTTPError(f"{_detail(resp)}: {url}", response=resp)
        return resp

    raise RuntimeError("request_with_retry exhausted retries without returning")


def get_json(url: str, *, log=print, **kwargs):
    """GET and parse JSON, returning None on any failure.

    For callers that prefer to skip one item and carry on rather than abort.
    """
    try:
        return request_with_retry("GET", url, log=log, **kwargs).json()
    except Exception as e:  # noqa: BLE001 - deliberately broad; caller degrades
        log(f"  Failed: {url} — {e}")
        return None
