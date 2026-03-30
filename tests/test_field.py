from envspec.field import Field


def test_field_init() -> None:
    field = Field(str, required=True, env="API_URL")
    assert field.type_ is str
    assert field.required is True
    assert field.env == "API_URL"