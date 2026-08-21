import pytest
from app.services.google_maps_ingestion import generate_review_hook_pitch, GCC_MAPS_SEEDS

def test_generate_review_hook_pitch():
    store = GCC_MAPS_SEEDS[0]
    pitch = generate_review_hook_pitch(store)
    assert store["company"].split("(")[0].strip() in pitch
    assert "بالفيديو أعلاه (20 ثانية)" in pitch
    assert str(store["google_rating"]) in pitch
    assert store["delivery_pain_snippet"] in pitch
