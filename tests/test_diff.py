from envspec.diff import diff_envs, render_text, to_dict


def test_added_removed_changed():
    old = {"A": "1", "B": "2", "C": "3"}
    new = {"A": "1", "B": "9", "D": "4"}
    d = diff_envs(old, new)
    assert d.added == {"D": "4"}
    assert d.removed == {"C": "3"}
    assert d.changed == {"B": ("2", "9")}


def test_rename_detection():
    old = {"API_HOST": "x"}
    new = {"API_URL": "x"}
    d = diff_envs(old, new, rename_map={"API_HOST": "API_URL"})
    assert d.renamed == {"API_HOST": "API_URL"}
    assert not d.added and not d.removed


def test_empty_and_render():
    d = diff_envs({"A": "1"}, {"A": "1"})
    assert d.empty and render_text(d) == "Различий нет."


def test_to_dict():
    d = diff_envs({"A": "1"}, {"A": "2"})
    assert to_dict(d)["changed"] == {"A": {"from": "1", "to": "2"}}
