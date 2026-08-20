from urllib.parse import urlsplit, urlunsplit

GCC_COUNTRIES = {"SA", "AE", "KW", "BH", "QA", "OM"}
SUPPORTED_PLATFORMS = {"salla", "zid", "shopify", "woocommerce", "custom"}


def canonicalize_website(value: str) -> str:
    parts = urlsplit(value.strip())
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        raise ValueError("website must be a public http(s) URL")
    host = parts.hostname.lower().removeprefix("www.")
    port = f":{parts.port}" if parts.port and parts.port not in {80, 443} else ""
    return urlunsplit(("https", f"{host}{port}", parts.path.rstrip("/") or "", "", ""))


def prospect_score(*, country_code: str | None, platform: str | None, public_email: str | None,
                   public_phone: str | None, evidence: dict) -> int:
    """Transparent ICP score; it never infers sensitive traits."""

    score = 0
    if country_code in GCC_COUNTRIES:
        score += 25
    if platform in SUPPORTED_PLATFORMS:
        score += 25
    if public_email:
        score += 12
    if public_phone:
        score += 8
    if evidence.get("cod_available") is True:
        score += 20
    if evidence.get("whatsapp_available") is True:
        score += 10
    return min(score, 100)
