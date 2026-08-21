import asyncio
import sys
import threading
from types import ModuleType
from unittest.mock import MagicMock, patch
import pytest
from httpx import ASGITransport, AsyncClient

from pathlib import Path

root_dir = Path(__file__).resolve().parents[2]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from acquisition.app import app, settings


@pytest.mark.asyncio
async def test_acquisition_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_acquisition_extract_requires_auth():
    settings.acquisition_admin_key = "secret123"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/extract", json={"url": "https://example.com"})
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_acquisition_extract_runs_in_thread_pool():
    settings.acquisition_admin_key = "secret123"
    main_thread_id = threading.get_ident()
    executed_thread_id = None

    def fake_run():
        nonlocal executed_thread_id
        executed_thread_id = threading.get_ident()
        return {
            "company": "Test Store",
            "country_code": "SA",
            "platform": "salla",
            "public_email": "info@test.sa",
            "public_phone": "+966500000000",
            "social_profiles": [],
            "evidence": {"cod_available": True, "whatsapp_available": True},
        }

    mock_graph_instance = MagicMock()
    mock_graph_instance.run.side_effect = fake_run

    # Create dummy modules for scrapegraphai and langchain
    mock_sg_module = ModuleType("scrapegraphai")
    mock_sg_graphs = ModuleType("scrapegraphai.graphs")
    mock_sg_graphs.SmartScraperGraph = MagicMock(return_value=mock_graph_instance)
    mock_sg_module.graphs = mock_sg_graphs

    mock_lc_module = ModuleType("langchain_community")
    mock_lc_chat = ModuleType("langchain_community.chat_models")
    mock_lc_chat.ChatOllama = MagicMock()
    mock_lc_module.chat_models = mock_lc_chat

    modules_to_patch = {
        "scrapegraphai": mock_sg_module,
        "scrapegraphai.graphs": mock_sg_graphs,
        "langchain_community": mock_lc_module,
        "langchain_community.chat_models": mock_lc_chat,
    }

    with patch.dict(sys.modules, modules_to_patch), \
         patch("acquisition.app._assert_public_url", return_value="https://test-store.sa"), \
         patch("acquisition.app._ensure_model", return_value=None):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            res = await ac.post(
                "/extract",
                json={"url": "https://test-store.sa", "country_hint": "sa"},
                headers={"x-mujeeb-acquisition-key": "secret123"},
            )
            assert res.status_code == 200
            data = res.json()
            assert data["company"] == "Test Store"
            assert data["country_code"] == "SA"
            assert executed_thread_id is not None
            assert executed_thread_id != main_thread_id


@pytest.mark.asyncio
async def test_acquisition_extract_handles_invalid_payload():
    settings.acquisition_admin_key = "secret123"
    mock_graph_instance = MagicMock()
    mock_graph_instance.run.return_value = "not a dict"

    mock_sg_module = ModuleType("scrapegraphai")
    mock_sg_graphs = ModuleType("scrapegraphai.graphs")
    mock_sg_graphs.SmartScraperGraph = MagicMock(return_value=mock_graph_instance)
    mock_sg_module.graphs = mock_sg_graphs

    mock_lc_module = ModuleType("langchain_community")
    mock_lc_chat = ModuleType("langchain_community.chat_models")
    mock_lc_chat.ChatOllama = MagicMock()
    mock_lc_module.chat_models = mock_lc_chat

    modules_to_patch = {
        "scrapegraphai": mock_sg_module,
        "scrapegraphai.graphs": mock_sg_graphs,
        "langchain_community": mock_lc_module,
        "langchain_community.chat_models": mock_lc_chat,
    }

    with patch.dict(sys.modules, modules_to_patch), \
         patch("acquisition.app._assert_public_url", return_value="https://test-store.sa"), \
         patch("acquisition.app._ensure_model", return_value=None):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            res = await ac.post(
                "/extract",
                json={"url": "https://test-store.sa"},
                headers={"x-mujeeb-acquisition-key": "secret123"},
            )
            assert res.status_code == 502
