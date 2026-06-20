from envspec import Config, Field, doctor


class C(Config):
    api_url = Field(str, required=True)
    timeout_s = Field(int, default=30)
    api_token = Field(str, secret=True, default="")


def test_doctor_reports_error_for_missing_required():
    rep = doctor.diagnose(C, use_environ=False, overrides={})
    statuses = {r.name: r.status for r in rep.rows}
    assert statuses["API_URL"] == "error"
    assert rep.ok is False


def test_doctor_tracks_origin():
    rep = doctor.diagnose(C, use_environ=False, overrides={"API_URL": "https://x"})
    row = next(r for r in rep.rows if r.name == "API_URL")
    assert row.status == "ok" and row.origin == "override"


def test_doctor_masks_secret():
    rep = doctor.diagnose(
        C, use_environ=False, overrides={"API_URL": "https://x", "API_TOKEN": "sekret"}
    )
    row = next(r for r in rep.rows if r.name == "API_TOKEN")
    assert row.value == "***" and "sekret" not in doctor.render_text(rep)


def test_doctor_json_shape():
    rep = doctor.diagnose(C, use_environ=False, overrides={"API_URL": "https://x"})
    d = doctor.to_dict(rep)
    assert "vars" in d and d["ok"] is True
