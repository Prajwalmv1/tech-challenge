"""
Tech Challenge - SDET (Python) - Single File Suite

API Under Test:
  https://jsonplaceholder.typicode.com/posts

What this suite demonstrates (Interview-ready):
  1) Contract validation:
     - HTTP status codes
     - Response headers (Content-Type)
     - Response body structure/schema (required keys)
     - Data types (int/str)
     - Basic data sanity checks (non-empty title/body)
  2) Behavior validation:
     - Query param filtering: /posts?userId=1 returns only userId=1 posts
  3) Negative test:
     - /posts/{id} for a non-existent ID returns 404
  4) Maintainability:
     - Centralized config
     - Small API client wrapper
     - Reusable assertion helpers
  5) Observability:
     - Logs show on console (readable)
     - Full details saved to a log file (traceability)

How to run (live logs on screen):
  pytest -vv -s test_posts_api.py

How to run via python3 (also runs pytest):
  python3 test_posts_api.py
"""

import json
import logging
import os
import time
from datetime import datetime, timezone

import pytest
import requests


# =============================================================================
# 1) CONFIGURATION (single place to change base url / timeouts / log behavior)
# =============================================================================
BASE_URL = "https://jsonplaceholder.typicode.com"
TIMEOUT_SECONDS = 10

# Log file name (override without code changes):
#   API_TEST_LOG_FILE=my_run.log pytest -vv -s test_posts_api.py
LOG_FILE = os.getenv("API_TEST_LOG_FILE", "api_test_run.log")

# How many items to print to CONSOLE for list responses (keeps screen readable)
CONSOLE_JSON_LIST_PREVIEW_COUNT = int(os.getenv("CONSOLE_JSON_LIST_PREVIEW_COUNT", "3"))

# Required schema fields for a /posts item
REQUIRED_POST_KEYS = {"userId", "id", "title", "body"}


# =============================================================================
# 2) LOGGING SETUP (Console + File)
#    - Console: readable + preview body (no huge spam)
#    - File: full debug + full body (complete trace)
# =============================================================================
def _configure_logging():
    logger = logging.getLogger("api_tests")
    logger.setLevel(logging.DEBUG)

    # Prevent duplicate handlers if re-imported
    if logger.handlers:
        return logger

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler (INFO/DEBUG visible on screen)
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(fmt)

    # File handler (store EVERYTHING)
    file_handler = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)

    logger.addHandler(console)
    logger.addHandler(file_handler)

    # Header per run
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    logger.info("=" * 90)
    logger.info("TEST RUN START (UTC): %s", now)
    logger.info("Working dir: %s", os.getcwd())
    logger.info("Log file   : %s", os.path.abspath(LOG_FILE))
    logger.info("=" * 90)

    return logger


LOGGER = _configure_logging()


def _pretty_json(obj):
    """Human readable JSON for logs."""
    try:
        return json.dumps(obj, indent=2, ensure_ascii=False)
    except Exception:
        return str(obj)


def _truncate_text(text, limit=2000):
    """Avoid flooding console with massive payloads."""
    if text is None:
        return ""
    return text if len(text) <= limit else text[:limit] + "\n... <truncated> ..."


# =============================================================================
# 3) API CLIENT (simple wrapper: keeps tests clean and maintainable)
# =============================================================================
class PostsClient:
    """
    Minimal client to isolate HTTP calls from assertions.

    Why useful:
      - Tests read like requirements (GET posts / validate)
      - Easy to add new endpoints later without duplicating requests.get everywhere
    """

    def __init__(self, base_url=BASE_URL, timeout=TIMEOUT_SECONDS):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def get_posts(self, params=None):
        url = f"{self.base_url}/posts"
        return self._get(url, params=params)

    def get_post_by_id(self, post_id):
        url = f"{self.base_url}/posts/{post_id}"
        return self._get(url)

    def _get(self, url, params=None):
        # Log request details
        LOGGER.info("REQUEST  | GET %s | params=%s", url, params)

        start = time.perf_counter()
        response = requests.get(url, params=params, timeout=self.timeout)
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        _log_response(response, elapsed_ms)
        return response


def _log_response(response, elapsed_ms):
    """
    Log response details:
      - status code
      - content-type
      - response time (latency)
      - headers
      - body
    """
    ct = response.headers.get("Content-Type", "")
    LOGGER.info("RESPONSE | status=%s | latency_ms=%.2f | content-type=%s",
                response.status_code, elapsed_ms, ct)

    # Headers (use DEBUG so it doesn't clutter too much)
    LOGGER.debug("HEADERS:\n%s", _pretty_json(dict(response.headers)))

    # Body logging:
    # - For console readability, preview list JSON (first N items)
    # - For file traceability, we still print the full body under DEBUG
    body_text = response.text or ""

    if "application/json" in ct:
        try:
            data = response.json()
            # FILE (full JSON)
            LOGGER.debug("BODY (json) FULL:\n%s", _pretty_json(data))

            # CONSOLE (preview if list)
            if isinstance(data, list):
                preview = data[:CONSOLE_JSON_LIST_PREVIEW_COUNT]
                LOGGER.info("BODY (json) PREVIEW | total_items=%s | showing_first=%s",
                            len(data), len(preview))
                LOGGER.info("BODY (json) PREVIEW:\n%s", _pretty_json(preview))
            else:
                # Non-list JSON (single object), print it on console too
                LOGGER.info("BODY (json) OBJECT:\n%s", _pretty_json(data))

        except Exception:
            # JSON parse failed: log raw text
            LOGGER.debug("BODY (text):\n%s", _truncate_text(body_text))
    else:
        LOGGER.debug("BODY (text):\n%s", _truncate_text(body_text))


# =============================================================================
# 4) REUSABLE ASSERTIONS (contract checks / schema checks)
# =============================================================================
def assert_json_response(response):
    """
    Important API contract validation:
      - Content-Type should indicate JSON
    """
    assert response.headers.get("Content-Type"), "Missing Content-Type header"
    assert "application/json" in response.headers.get("Content-Type", ""), "Response is not JSON"


def assert_post_shape(post):
    """
    Important API contract validation for a post object:
      - required keys exist
      - types match expected
      - basic sanity: title/body are not empty
    """
    assert isinstance(post, dict), "Post must be a JSON object/dict"

    missing = REQUIRED_POST_KEYS - set(post.keys())
    assert not missing, "Missing keys in post: %s" % missing

    assert isinstance(post["userId"], int), "userId must be int"
    assert isinstance(post["id"], int), "id must be int"
    assert isinstance(post["title"], str), "title must be str"
    assert isinstance(post["body"], str), "body must be str"

    assert post["title"].strip(), "title must not be empty"
    assert post["body"].strip(), "body must not be empty"


# =============================================================================
# 5) PYTEST FIXTURES (shared setup + auto logging per test)
# =============================================================================
@pytest.fixture(scope="session")
def client():
    """Session-wide client instance."""
    return PostsClient()


@pytest.fixture(autouse=True)
def _log_test_start_end(request):
    """
    Automatically logs the start and end of each test.
    This makes it obvious on screen and in the log file which test is running.
    """
    LOGGER.info("--- TEST START: %s ---", request.node.name)
    yield
    LOGGER.info("--- TEST END  : %s ---", request.node.name)


# =============================================================================
# 6) TEST CASES
# =============================================================================
def test_get_posts_returns_200_and_json(client):
    """
    TEST PURPOSE:
      Verify GET /posts is reachable and returns JSON.

    VALIDATIONS:
      - status code == 200
      - Content-Type indicates JSON
    """
    response = client.get_posts()
    assert response.status_code == 200
    assert_json_response(response)


def test_get_posts_returns_list_and_has_data(client):
    """
    TEST PURPOSE:
      Verify GET /posts returns a list and it is not empty.

    VALIDATIONS:
      - response.json() is a list
      - list has at least one element
    """
    response = client.get_posts()
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list), "Expected list of posts"
    assert len(data) > 0, "Expected at least one post"


def test_posts_schema_and_types_for_sample(client):
    """
    TEST PURPOSE:
      Validate important parts of the API response:
      post schema keys + types + basic content sanity.

    WHY SAMPLE?
      We validate first 10 items to keep test fast and still meaningful.
    """
    response = client.get_posts()
    assert response.status_code == 200

    data = response.json()
    for post in data[:10]:
        assert_post_shape(post)


@pytest.mark.parametrize("post_id", [1, 2, 3])
def test_get_post_by_id_returns_correct_post(client, post_id):
    """
    TEST PURPOSE:
      Verify GET /posts/{id} returns the correct post.

    VALIDATIONS:
      - status code == 200
      - response is JSON
      - post schema is valid
      - returned post['id'] == requested id
    """
    response = client.get_post_by_id(post_id)

    assert response.status_code == 200
    assert_json_response(response)

    post = response.json()
    assert_post_shape(post)
    assert post["id"] == post_id, "Returned post id should match requested id"


def test_filter_posts_by_userId(client):
    """
    TEST PURPOSE:
      Validate filtering behavior using query params:
        GET /posts?userId=1

    VALIDATIONS:
      - status code == 200
      - response JSON list is not empty
      - all returned posts have userId == 1
    """
    response = client.get_posts(params={"userId": 1})

    assert response.status_code == 200
    assert_json_response(response)

    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0, "Expected posts for userId=1"
    assert all(p["userId"] == 1 for p in data), "All posts should have userId=1"


def test_get_nonexistent_post_returns_404(client):
    """
    NEGATIVE TEST (Required):
      Request a post ID that does not exist.

    EXPECTED:
      - 404 Not Found
    """
    response = client.get_post_by_id(999999)
    assert response.status_code == 404


# =============================================================================
# run via python3 (convenience)
#    This prints the list of tests first, then runs them with logs.
# =============================================================================
if __name__ == "__main__":
    LOGGER.info("Running via python3. First listing collected tests, then executing...")
    # 1) Show test collection on screen
    pytest.main([__file__, "--collect-only", "-q"])
    # 2) Run tests with live logs on screen
    raise SystemExit(pytest.main([__file__, "-vv", "-s"]))
