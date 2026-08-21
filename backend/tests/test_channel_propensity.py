import pytest
from app.services.channel_propensity import score_channel_propensity

def test_channel_propensity_whatsapp_dominant():
    res = score_channel_propensity(
        platform="salla",
        country_code="SA",
        public_phone="+966539881582",
        social_profiles=[],
        evidence={"cod_available": True, "whatsapp_available": True},
        category="electronics"
    )
    assert res["whatsapp_score"] >= 80
    assert res["outreach_mode"] == "MANUAL_WHATSAPP"
    assert res["recommended_channel"] == "WHATSAPP"

def test_channel_propensity_instagram_dominant():
    res = score_channel_propensity(
        platform="shopify",
        country_code="SA",
        public_phone=None,
        social_profiles=["https://instagram.com/fashion_sa"],
        evidence={"cod_available": False, "instagram_available": True},
        category="fashion"
    )
    assert res["instagram_score"] >= 80
    assert res["outreach_mode"] == "MANUAL_INSTAGRAM"
    assert res["recommended_channel"] == "INSTAGRAM"
