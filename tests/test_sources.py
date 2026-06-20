from envspec.sources import collect, parse_dotenv


def test_parse_dotenv_basic():
    parsed = parse_dotenv("# comment\nAPI_URL=https://x\nexport TOKEN='abc'\nEMPTY=\n")
    assert (
        parsed["API_URL"] == "https://x"
        and parsed["TOKEN"] == "abc"
        and parsed["EMPTY"] == ""
        and "comment" not in parsed
    )


def test_collect_priority(tmp_path, monkeypatch):
    ef = tmp_path / ".env"
    ef.write_text("A=from_dotenv\nB=from_dotenv\n", encoding="utf-8")
    monkeypatch.setenv("B", "from_environ")
    m = collect(ef, overrides={"A": "from_override"})
    assert m["A"] == "from_override" and m["B"] == "from_environ"
