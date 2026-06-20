from envspec import Config, Field
from envspec.render import dotenv, markdown


class C(Config):
    api_url = Field(str, required=True, doc="Base API URL", example="https://x")
    timeout_s = Field(int, default=30, doc="Таймаут")
    api_token = Field(str, secret=True, doc="Токен")
    old = Field(str, deprecated=True, default="")


def test_dotenv_deterministic():
    a = dotenv.render(C)
    b = dotenv.render(C)
    assert a == b


def test_dotenv_content():
    out = dotenv.render(C)
    assert "# Base API URL (required)" in out
    assert "API_URL=https://x" in out
    assert "TIMEOUT_S=30" in out
    assert "secret" in out and "API_TOKEN=" in out


def test_dotenv_secret_not_revealed():
    class S(Config):
        token = Field(str, secret=True, default="REALSECRET")

    out = dotenv.render(S)
    assert "REALSECRET" not in out


def test_markdown_deterministic_and_table():
    a = markdown.render(C)
    b = markdown.render(C)
    assert a == b
    assert "| Переменная |" in a
    assert "`API_URL`" in a and "да" in a  # required


def test_markdown_secret_default_hidden():
    class S(Config):
        token = Field(str, secret=True, default="REALSECRET")

    out = markdown.render(S)
    assert "REALSECRET" not in out
