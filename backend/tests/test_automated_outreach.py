import pytest
from unittest.mock import patch, MagicMock
from app.services.automated_outreach import send_whatsapp_via_waapi, send_whatsapp_media_via_waapi, send_email_via_resend

@pytest.mark.asyncio
async def test_send_whatsapp_via_waapi_mocked():
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success", "messageId": "msg-123"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        res = await send_whatsapp_via_waapi(
            instance_id="102227",
            api_token="test_token",
            phone_number="+966539881582",
            message="Test message"
        )
        assert res["status"] == "success"

@pytest.mark.asyncio
async def test_send_whatsapp_media_via_waapi_mocked():
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success", "mediaId": "media-123"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        res = await send_whatsapp_media_via_waapi(
            instance_id="102227",
            api_token="test_token",
            phone_number="+966539881582",
            media_url="https://usemujeeb.com/videos/video2_workflow.mp4",
            caption="Test video demo caption"
        )
        assert res["status"] == "success"

@pytest.mark.asyncio
async def test_send_email_via_resend_mocked():
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "email-123"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        res = await send_email_via_resend(
            api_key="re_test_key",
            from_email="contact@vellumkey.shop",
            to_email="care@example.com",
            subject="Test subject",
            body_text="Test body"
        )
        assert res["id"] == "email-123"
