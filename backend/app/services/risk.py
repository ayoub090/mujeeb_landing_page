from app.models import RiskLevel
from app.schemas import RiskInput, RiskResult


def calculate_risk(payload: RiskInput) -> RiskResult:
    reasons: dict[str, int] = {}
    if payload.is_new_customer:
        reasons["new_customer"] = 15
    if 0 <= payload.ordered_at_hour <= 5:
        reasons["overnight_order"] = 10
    if payload.prior_store_rto_count > 0:
        reasons["prior_store_rto"] = min(30, payload.prior_store_rto_count * 10)
    if not payload.address_valid:
        reasons["address_unverified"] = 20
    if payload.checkout_vpn_detected:
        reasons["checkout_vpn"] = 25
    if payload.amount > 1000:
        reasons["high_value"] = 15

    score = min(100, sum(reasons.values()))
    level = RiskLevel.low if score <= 30 else RiskLevel.medium if score <= 65 else RiskLevel.high
    return RiskResult(score=score, level=level, reasons=reasons)

