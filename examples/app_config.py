from envspec import Config, Field, Profile, migration


class AppConfig(Config):
    api_url = Field(str, required=True, doc="Base API URL", example="https://api.example.com")
    timeout_s = Field(int, default=30, min=1, max=300, doc="HTTP timeout, секунды")
    verify_ssl = Field(bool, default=True, doc="Проверять TLS-сертификат")
    api_token = Field(str, secret=True, default="", doc="Токен доступа к API")
    log_level = Field(
        str,
        default="info",
        choices=["debug", "info", "warning", "error"],
        doc="Уровень логирования",
    )

    profiles = {
        "prod": Profile(overrides={"VERIFY_SSL": "true"}, require=["api_token"]),
        "dev": Profile(overrides={"LOG_LEVEL": "debug"}),
    }


@migration("0.1 -> 0.2")
def _(m):
    m.rename("API_HOST", "API_URL")
    m.transform("VERIFY_SSL", "TLS_MODE", lambda v: "insecure" if v in ("0", "false") else "verify")
    m.deprecate("OLD_FLAG", reason="больше не используется")
