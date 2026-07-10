import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from agents.base import call_gemini


class GeminiFallbackTests(unittest.TestCase):
    def test_call_gemini_retries_with_fallback_model_when_requested_model_is_missing(self):
        class FakeResponse:
            text = '{"summary": "ok"}'

        async def fake_generate_content(*args, **kwargs):
            model = kwargs.get("model")
            if model == "gemini-3.1-pro":
                raise Exception("404 NOT_FOUND models/gemini-3.1-pro is not found")
            return FakeResponse()

        class FakeModels:
            def __init__(self):
                self.generate_content = fake_generate_content

        class FakeAio:
            def __init__(self):
                self.models = FakeModels()

        class FakeClient:
            def __init__(self):
                self.aio = FakeAio()

        fake_settings = SimpleNamespace(
            executive_model="gemini-3.1-pro",
            PRO_MODEL="gemini-3.1-pro",
            FLASH_MODEL="gemini-3.1-pro",
            LLM_PROVIDER="gemini",
            GROQ_API_KEY="",
            GROQ_MODEL="llama-3.3-70b-versatile",
        )

        with patch("agents.base._get_client", return_value=FakeClient()), patch("agents.base.settings", fake_settings):
            result = asyncio.run(call_gemini("prompt", "system", model="gemini-3.1-pro", max_retries=2))

        self.assertEqual(result["summary"], "ok")

    def test_call_gemini_retries_groq_when_rate_limited(self):
        fake_settings = SimpleNamespace(
            executive_model="gemini-3.5-flash",
            PRO_MODEL="gemini-3.5-flash",
            FLASH_MODEL="gemini-3.5-flash",
            LLM_PROVIDER="groq",
            GROQ_API_KEY="test-key",
            GROQ_MODEL="llama-3.3-70b-versatile",
        )

        class FakeResponse:
            def raise_for_status(self):
                return None

            def json(self):
                return {"choices": [{"message": {"content": '{"summary": "ok"}'}}]}

        class FakeAsyncClient:
            calls = 0

            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            async def post(self, *args, **kwargs):
                type(self).calls += 1
                if type(self).calls == 1:
                    raise RuntimeError("429 Too Many Requests")
                return FakeResponse()

        with patch("agents.base.httpx.AsyncClient", FakeAsyncClient), patch("agents.base.asyncio.sleep", new=AsyncMock()), patch("agents.base.settings", fake_settings):
            result = asyncio.run(call_gemini("prompt", "system", max_retries=2))

        self.assertEqual(result["summary"], "ok")


if __name__ == "__main__":
    unittest.main()
