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

    def test_key_manager_rotation_and_cooldown(self):
        from utils.key_manager import KeyManager

        km = KeyManager("test", ["key1", "key2", "key3"], cooldown_seconds=10.0)

        # 1. Test round robin
        self.assertEqual(km.get_key(), "key1")
        self.assertEqual(km.get_key(), "key2")
        self.assertEqual(km.get_key(), "key3")
        self.assertEqual(km.get_key(), "key1")

        # 2. Test cooldown
        km.report_rate_limit("key2")
        # key2 is on cooldown. Rotation should skip key2.
        # Next expected key after key1 is key2, but key2 is skipped, so it should return key3
        self.assertEqual(km.get_key(), "key3")
        self.assertEqual(km.get_key(), "key1")
        self.assertEqual(km.get_key(), "key3")

        # 3. All on cooldown fallback
        km.report_rate_limit("key1")
        km.report_rate_limit("key3")
        # All keys on cooldown. Should pick the one with the earliest cooldown expiry.
        # key2 was cooled down first, so it has earliest expiry.
        self.assertEqual(km.get_key(), "key2")

    def test_call_gemini_rotates_groq_keys_on_rate_limit(self):
        from agents.base import _get_groq_key_manager

        # Reset groq key manager to use fake keys
        fake_settings = SimpleNamespace(
            executive_model="gemini-3.5-flash",
            PRO_MODEL="gemini-3.5-flash",
            FLASH_MODEL="gemini-3.5-flash",
            LLM_PROVIDER="groq",
            groq_api_keys=["key1", "key2"],
            GROQ_API_KEY="key1",
            GROQ_MODEL="llama-3.3-70b-versatile",
        )

        class FakeResponse:
            def raise_for_status(self):
                return None

            def json(self):
                return {"choices": [{"message": {"content": '{"summary": "ok"}'}}]}

        # We will capture the keys used in requests
        used_keys = []

        class FakeAsyncClient:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            async def post(self, url, headers, json, *args, **kwargs):
                auth_header = headers.get("Authorization", "")
                key = auth_header.split(" ")[1] if " " in auth_header else auth_header
                used_keys.append(key)

                # If key1, return rate limit
                if key == "key1":
                    raise RuntimeError("429 Too Many Requests")
                return FakeResponse()

        # Reset the key manager so it loads the test keys
        groq_km = _get_groq_key_manager()
        groq_km.update_keys(["key1", "key2"])

        with patch("agents.base.httpx.AsyncClient", FakeAsyncClient), patch("agents.base.asyncio.sleep", new=AsyncMock()), patch("agents.base.settings", fake_settings):
            result = asyncio.run(call_gemini("prompt", "system", max_retries=3))

        self.assertEqual(result["summary"], "ok")
        # We expect that "key1" was tried, hit 429, reported rate limit, and then "key2" was tried and succeeded.
        self.assertEqual(used_keys, ["key1", "key2"])


if __name__ == "__main__":
    unittest.main()
