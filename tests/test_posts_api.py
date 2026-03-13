# test_posts_api.py
# Test cases only

import pytest

from tests.validators import assert_json_content_type, assert_post_shape


def test_get_posts_returns_200_and_json(posts_client):
    """
    Validates basic endpoint contract:
      - HTTP 200
      - JSON content-type
    """
    resp = posts_client.get_posts()
    assert resp.status_code == 200
    assert_json_content_type(resp)


def test_get_posts_returns_list_and_has_data(posts_client):
    """
    Validates response shape for /posts:
      - JSON list
      - non-empty
    """
    resp = posts_client.get_posts()
    assert resp.status_code == 200

    data = resp.json()
    assert isinstance(data, list), "Expected list response"
    assert len(data) > 0, "Expected at least one post"


def test_posts_schema_and_types_for_sample(posts_client):
    """
    Validates important parts of API response:
      - required keys
      - data types
      - title/body not empty
    Uses a sample of first 10 items for speed.
    """
    resp = posts_client.get_posts()
    assert resp.status_code == 200

    data = resp.json()
    for post in data[:10]:
        assert_post_shape(post)


@pytest.mark.parametrize("post_id", [1, 2, 3])
def test_get_post_by_id_returns_correct_post(posts_client, post_id):
    """
    Validates /posts/{id} returns correct resource:
      - HTTP 200
      - JSON content-type
      - schema valid
      - id matches requested id
    """
    resp = posts_client.get_post_by_id(post_id)
    assert resp.status_code == 200
    assert_json_content_type(resp)

    post = resp.json()
    assert_post_shape(post)
    assert post["id"] == post_id


def test_filter_posts_by_userId(posts_client):
    """
    Validates query param behavior:
      - /posts?userId=1 returns only userId=1
    """
    resp = posts_client.get_posts(params={"userId": 1})
    assert resp.status_code == 200
    assert_json_content_type(resp)

    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0, "Expected some posts for userId=1"
    assert all(p["userId"] == 1 for p in data), "Not all results match userId=1"


def test_get_nonexistent_post_returns_404(posts_client):
    """
    Negative test (required):
      - non-existent post should return 404
    """
    resp = posts_client.get_post_by_id(999999)
    assert resp.status_code == 404
