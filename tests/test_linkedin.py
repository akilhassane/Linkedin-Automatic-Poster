from unittest import mock

import pytest  # type: ignore

from src.utils.linkedin import post_to_linkedin
from src.utils.exceptions import TokenExpiredError


def test_token_expired(monkeypatch):
    with mock.patch("src.utils.linkedin.requests.post") as fake_post:
        fake_resp = mock.Mock()
        fake_resp.status_code = 401
        fake_resp.text = "expired"
        fake_post.return_value = fake_resp

        with pytest.raises(TokenExpiredError):
            post_to_linkedin("badtoken", "urn:li:person:xyz", "hi", image_path=None)