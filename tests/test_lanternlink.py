import json
import os
import pathlib
import re
import threading
import time
import unittest
import urllib.error
import urllib.request


ROOT = pathlib.Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT))

import lanternlink  # noqa: E402


TEST_SECRET = b"test-only-secret-32-characters!!"


class ServerFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.server = lanternlink.create_server("127.0.0.1", 0, TEST_SECRET, ROOT / "web")
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address
        self.base_url = f"http://{host}:{port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def post(self, payload):
        request = urllib.request.Request(
            self.base_url + "/api/signal",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=2) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            return error.code, json.loads(error.read().decode("utf-8"))

    def test_valid_signal_crosses_http_boundary(self) -> None:
        result = lanternlink.send_signal(self.base_url, TEST_SECRET, "WORKSHOP-1", "READY")
        self.assertTrue(result["accepted"])
        self.assertEqual(result["signal"]["display"], "READY")
        self.assertEqual(result["signal"]["integrity"], "SIGNED + FRESH + UNIQUE")

    def test_bad_signature_is_rejected(self) -> None:
        payload = lanternlink.signal_document(TEST_SECRET, "WORKSHOP-1", "ASSIST")
        payload["signature"] = "0" * 64
        status, response = self.post(payload)
        self.assertEqual(status, 401)
        self.assertEqual(response["error"], "invalid_signature")

    def test_stale_timestamp_is_rejected(self) -> None:
        now = int(time.time()) - lanternlink.MAX_CLOCK_SKEW_SECONDS - 1
        payload = lanternlink.signal_document(TEST_SECRET, "WORKSHOP-1", "CHECK_IN", now=now)
        status, response = self.post(payload)
        self.assertEqual(status, 401)
        self.assertEqual(response["error"], "stale_timestamp")

    def test_nonce_replay_is_rejected(self) -> None:
        payload = lanternlink.signal_document(TEST_SECRET, "WORKSHOP-1", "ALL_CLEAR")
        first_status, _ = self.post(payload)
        second_status, response = self.post(payload)
        self.assertEqual(first_status, 202)
        self.assertEqual(second_status, 401)
        self.assertEqual(response["error"], "replayed_nonce")

    def test_sender_and_message_are_bounded(self) -> None:
        state = lanternlink.SignalState()
        bad_sender = state.apply(TEST_SECRET, "home address", "READY", 1, "a" * 24, "0" * 64, now=1)
        bad_message = state.apply(TEST_SECRET, "WORKSHOP-1", "FREE TEXT", 1, "a" * 24, "0" * 64, now=1)
        self.assertEqual(bad_sender[1], "invalid_sender")
        self.assertEqual(bad_message[1], "invalid_message")

    def test_receiver_ui_and_security_headers(self) -> None:
        with urllib.request.urlopen(self.base_url + "/", timeout=2) as response:
            page = response.read().decode("utf-8")
            self.assertIn("Make the connection", page)
            self.assertIn("MORSE-TIMED", page)
            self.assertEqual(response.headers["X-Frame-Options"], "DENY")
            self.assertIn("default-src 'self'", response.headers["Content-Security-Policy"])


class StaticTests(unittest.TestCase):
    def test_morse_encoding(self) -> None:
        self.assertEqual(lanternlink.encode_morse("READY"), ".-. . .- -.. -.--")
        self.assertEqual(lanternlink.encode_morse("ALL CLEAR"), ".- .-.. .-.. / -.-. .-.. . .- .-.")

    def test_public_tree_has_no_private_identifiers_or_secret(self) -> None:
        text_parts = []
        ignored_parts = {".git", "node_modules", "out", "review", "__pycache__"}
        for path in ROOT.rglob("*"):
            if not path.is_file() or ignored_parts.intersection(path.parts):
                continue
            if path.name == "ELEMENT14_HANDOFF.md":
                continue
            if path.suffix.lower() in {".py", ".md", ".html", ".css", ".js", ".svg", ".json"}:
                text_parts.append(path.read_text(encoding="utf-8"))
        combined = "\n".join(text_parts)
        banned = [
            r"\b\d{5}\s+[A-Z][A-Za-z'-]+(?:\s+[A-Z][A-Za-z'-]+){0,3}\s+(?:Lane|Ln|Street|St|Road|Rd|Drive|Dr|Court|Ct|Boulevard|Blvd)\b",
            r"\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b",
            r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
            r"\b(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})\b",
            r"AKIA[0-9A-Z]{16}",
            r"ghp_[A-Za-z0-9]{20,}",
        ]
        for pattern in banned:
            self.assertIsNone(re.search(pattern, combined, re.IGNORECASE), pattern)
        live_secret = os.environ.get("LANTERNLINK_SECRET")
        if live_secret:
            self.assertNotIn(live_secret, combined)


if __name__ == "__main__":
    unittest.main()
