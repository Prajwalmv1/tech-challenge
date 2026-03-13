# Tech Challenge - SDET (Python)

## Goal
Automated tests for public API:
https://jsonplaceholder.typicode.com/posts

Covers:
- Contract validations (status, content-type)
- Schema/type validations for post objects
- Query param behavior (userId filter)
- Negative test (non-existent post returns 404)
- Detailed logging to console + log file

## Setup

### Option A (use system pytest if already installed)

pip install -r requirements.txt

### Option B (no pip install; rely on system packages)

python3 -c "import pytest, requests; print(pytest.__version__)"
