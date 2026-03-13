# api_client.py
# HTTP client wrapper so we don't repeat requests logic 

import json
import time


class PostsClient(object):
    def __init__(self, session, base_url, timeout, logger, preview_count=3):
        self.session = session
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.log = logger
        self.preview_count = preview_count

    def get_posts(self, params=None):
        url = self.base_url + "/posts"
        return self._get(url, params=params)

    def get_post_by_id(self, post_id):
        url = self.base_url + "/posts/%s" % post_id
        return self._get(url)

    def _get(self, url, params=None):
        # Request logging
        self.log.info("REQUEST  | GET %s | params=%s", url, params)

        start = time.time()
        resp = self.session.get(url, params=params, timeout=self.timeout)
        elapsed_ms = (time.time() - start) * 1000.0

        self._log_response(resp, elapsed_ms)
        return resp

    def _log_response(self, resp, elapsed_ms):
        ct = resp.headers.get("Content-Type", "")
        self.log.info("RESPONSE | status=%s | latency_ms=%.2f | content-type=%s",
                      resp.status_code, elapsed_ms, ct)

        # Headers to DEBUG (file gets it; console can show if DEBUG enabled)
        self.log.debug("HEADERS:\n%s", _pretty_json(dict(resp.headers)))

        # Body handling: preview to INFO, full to DEBUG
        body_text = resp.text or ""
        if "application/json" in ct:
            try:
                data = resp.json()
                # Full body to debug log (file)
                self.log.debug("BODY (json) FULL:\n%s", _pretty_json(data))

                # Preview to info (console readable)
                if isinstance(data, list):
                    preview = data[: self.preview_count]
                    self.log.info("BODY (json) PREVIEW | total_items=%s | showing_first=%s",
                                  len(data), len(preview))
                    self.log.info("BODY (json) PREVIEW:\n%s", _pretty_json(preview))
                else:
                    self.log.info("BODY (json) OBJECT:\n%s", _pretty_json(data))
            except Exception:
                self.log.debug("BODY (text):\n%s", _truncate(body_text))
        else:
            self.log.debug("BODY (text):\n%s", _truncate(body_text))


def _pretty_json(obj):
    try:
        return json.dumps(obj, indent=2, ensure_ascii=False)
    except Exception:
        return str(obj)


def _truncate(text, limit=2000):
    if text is None:
        return ""
    if len(text) <= limit:
        return text
    return text[:limit] + "\n... <truncated> ..."

