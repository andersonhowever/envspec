import pytest

from envspec import sources
from envspec.errors import SourceError


def test_json_source(tmp_path):
    p = tmp_path / "c.json"
    p.write_text('{"API_URL": "https://x", "TIMEOUT_S": 5}', encoding="utf-8")
    d = sources.load_json_file(p)
    assert d == {"API_URL": "https://x", "TIMEOUT_S": "5"}


def test_json_invalid_raises(tmp_path):
    p = tmp_path / "c.json"
    p.write_text("{bad}", encoding="utf-8")
    with pytest.raises(SourceError):
        sources.load_json_file(p)


def test_layered_priority(tmp_path, monkeypatch):
    ef = tmp_path / ".env"
    ef.write_text("A=dot\nB=dot\n", encoding="utf-8")
    jf = tmp_path / "c.json"
    jf.write_text('{"B": "json", "C": "json"}', encoding="utf-8")
    monkeypatch.setenv("C", "env")
    layers = sources.layered(ef, json_path=jf, overrides={"A": "ovr"})
    merged, origin = sources.merge_with_origin(layers)
    assert merged["A"] == "ovr" and origin["A"] == "override"
    assert merged["B"] == "json" and origin["B"] == "json"
    assert merged["C"] == "env" and origin["C"] == "environ"
