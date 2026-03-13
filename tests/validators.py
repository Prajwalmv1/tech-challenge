# validators.py
# Central place for API contract/schema assertions 

REQUIRED_POST_KEYS = {"userId", "id", "title", "body"}


def assert_json_content_type(response):
    ct = response.headers.get("Content-Type", "")
    assert ct, "Missing Content-Type header"
    assert "application/json" in ct, "Expected JSON response, got Content-Type=%r" % ct


def assert_post_shape(post):
    """
    Validates important parts of the /posts object:
      - required keys exist
      - correct data types
      - non-empty title/body
    """
    assert isinstance(post, dict), "Post must be a dict/json object"

    missing = REQUIRED_POST_KEYS - set(post.keys())
    assert not missing, "Missing keys in post: %s" % sorted(list(missing))

    assert isinstance(post["userId"], int), "userId must be int"
    assert isinstance(post["id"], int), "id must be int"
    assert isinstance(post["title"], str), "title must be str"
    assert isinstance(post["body"], str), "body must be str"

    assert post["title"].strip(), "title must not be empty"
    assert post["body"].strip(), "body must not be empty"
