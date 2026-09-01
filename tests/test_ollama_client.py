import requests

from app.ollama_client import check_health, stream_chat


class MockResponse:
    def __init__(self, status_code=200, lines=None):
        self.status_code = status_code
        self._lines = lines or []

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(
                f"HTTP {self.status_code}"
            )

    def iter_lines(self):
        return self._lines


def test_check_health_returns_true(monkeypatch):
    def mock_get(*args, **kwargs):
        return MockResponse(status_code=200)

    monkeypatch.setattr(
        requests,
        "get",
        mock_get,
    )

    result = check_health(
        "http://ollama:11434"
    )

    assert result is True


def test_check_health_returns_false_on_connection_error(
    monkeypatch,
):
    def mock_get(*args, **kwargs):
        raise requests.ConnectionError(
            "Server unavailable"
        )

    monkeypatch.setattr(
        requests,
        "get",
        mock_get,
    )

    result = check_health(
        "http://ollama:11434"
    )

    assert result is False


def test_stream_chat_returns_response_chunks(
    monkeypatch,
):
    mock_lines = [
        b'{"message":{"content":"Hello"}}',
        b'{"message":{"content":" world"}}',
    ]

    def mock_post(*args, **kwargs):
        return MockResponse(
            status_code=200,
            lines=mock_lines,
        )

    monkeypatch.setattr(
        requests,
        "post",
        mock_post,
    )

    chunks = list(
        stream_chat(
            "http://ollama:11434",
            "llama3.2:1b",
            [
                {
                    "role": "user",
                    "content": "Hi",
                }
            ],
        )
    )

    assert chunks == [
        "Hello",
        " world",
    ]