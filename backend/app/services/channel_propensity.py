from typing import Any

VISUAL_NICHES = {"parfums", "perfume", "fashion", "abayas", "beauty", "cosmetics", "gifts", "dattes", "food"}
TECH_NICHES = {"electronic", "appliances", "gadgets", "tools", "hardware"}


def score_channel_propensity(
    *,
    platform: str | None,
    country_code: str | None,
    public_phone: str | None,
    social_profiles: list | dict | None,
    evidence: dict | None,
    category: str | None = None,
) -> dict[str, Any]:
    """Calculate deterministic and qualitative propensity for Instagram vs WhatsApp outreach.
    
    Adheres strictly to official Meta policy:
    - Instagram cold outbound is user-initiated only -> mode: MANUAL_INSTAGRAM
    - WhatsApp outbound is merchant-assisted -> mode: MANUAL_WHATSAPP
    """
    evidence = evidence or {}
    socials = social_profiles if isinstance(social_profiles, (list, dict)) else []
    social_str = str(socials).lower()
    
    # 1. Instagram Score calculation
    ig_score = 0
    ig_reasons = []
    
    has_ig = "instagram" in social_str or "ig" in social_str or evidence.get("instagram_available") is True
    if has_ig:
        ig_score += 40
        ig_reasons.append("Compte Instagram professionnel public détecté")
    
    # Visual niches perform exceptionally well on Instagram DM / Story replies
    cat_lower = (category or "").lower()
    is_visual = any(n in cat_lower for n in VISUAL_NICHES) or platform in {"salla", "zid", "shopify"}
    if is_visual:
        ig_score += 30
        ig_reasons.append("Secteur visuel à fort engagement Instagram")
        
    if country_code in {"SA", "KW", "AE"}:
        ig_score += 20
        ig_reasons.append("Marché CCG avec pénétration Instagram e-commerce élevée")
        
    if evidence.get("cod_available") is True:
        ig_score += 10
        ig_reasons.append("Option Paiement à la livraison visible")
        
    ig_score = min(ig_score, 100)
    
    # 2. WhatsApp Score calculation
    wa_score = 0
    wa_reasons = []
    
    has_wa = bool(public_phone) or evidence.get("whatsapp_available") is True
    if has_wa:
        wa_score += 45
        wa_reasons.append("Numéro WhatsApp Business vérifié et actif")
        
    if evidence.get("cod_available") is True:
        wa_score += 35
        wa_reasons.append("Fort volume de commandes COD nécessitant validation WhatsApp")
        
    if platform in {"salla", "zid"}:
        wa_score += 20
        wa_reasons.append("Intégration native Salla/Zid compatible Mujeeb FSM")
        
    wa_score = min(wa_score, 100)
    
    # 3. Decision
    if ig_score > wa_score:
        recommended = "INSTAGRAM"
        mode = "MANUAL_INSTAGRAM"
        confidence = ig_score
        reasons = ig_reasons
    else:
        recommended = "WHATSAPP"
        mode = "MANUAL_WHATSAPP"
        confidence = wa_score
        reasons = wa_reasons
        
    return {
        "instagram_score": ig_score,
        "whatsapp_score": wa_score,
        "recommended_channel": recommended,
        "outreach_mode": mode,
        "channel_confidence": confidence,
        "channel_reasons": reasons,
    }
