#!/usr/bin/env python3
"""LanternLink: authenticated, cloud-free LAN signals with a visual beacon."""

import argparse
import hashlib
import hmac
import json
import os
import re
import secrets
import threading
import time
import urllib.error
import urllib.request
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, Optional, Set, Tuple


VERSION = "LL1"
DEFAULT_PORT = 8782
MAX_BODY_BYTES = 4096
MAX_CLOCK_SKEW_SECONDS = 90
NONCE_TTL_SECONDS = 180
ALLOWED_MESSAGES = {
    "CHECK_IN": "CHECK IN",
    "READY": "READY",
    "ASSIST": "ASSIST",
    "ALL_CLEAR": "ALL CLEAR",
}
LABEL_RE = re.compile(r"^[A-Z0-9][A-Z0-9_-]{0,23}$")
NONCE_RE = re.compile(r"^[a-f0-9]{24,64}$")

MORSE = {
    "A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".",
    "F": "..-.", "G": "--.", "H": "....", "I": "..", "J": ".---",
    "K": "-.-", "L": ".-..", "M": "--", "N": "-.", "O": "---",
    "P": ".--.", "Q": "--.-", "R": ".-.", "S": "...", "T": "-",
    "U": "..-", "V": "...-", "W": ".--", "X": "-..-", "Y": "-.--",
    "Z": "--..", "0": "-----", "1": ".----", "2": "..---",
    "3": "...--", "4": "....-", "5": ".....", "6": "-....",
    "7": "--...", "8": "---..", "9": "----.",
}


def encode_morse(text: str) -> str:
    """Encode supported display text with spaces represented by `/`."""
    words = []
    for word in text.upper().split():
        words.append(" ".join(MORSE[char] for char in word if char in MORSE))
    return " / ".join(words)


def canonical_payload(sender: str, message: str, timestamp: int, nonce: str) -> bytes:
    return f"{VERSION}|{sender}|{message}|{timestamp}|{nonce}".encode("utf-8")


def sign_payload(secret: bytes, sender: str, message: str, timestamp: int, nonce: str) -> str:
    return hmac.new(
        secret,
        canonical_payload(sender, message, timestamp, nonce),
        hashlib.sha256,
    ).hexdigest()


def validate_secret(secret: bytes) -> None:
    if len(secret) < 16:
        raise ValueError("LANTERNLINK_SECRET must be at least 16 characters")


class SignalState:
    """In-memory latest-signal state and bounded nonce replay cache."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._nonces: Dict[str, float] = {}
        self._sequence = 0
        self._signal = {
            "sequence": 0,
            "sender": "NONE",
            "message": "WAITING",
            "display": "WAITING FOR SIGNAL",
            "morse": encode_morse("WAITING"),
            "received_at": None,
            "integrity": "NO SIGNAL",
        }

    def snapshot(self) -> Dict[str, object]:
        with self._lock:
            return dict(self._signal)

    def apply(
        self,
        secret: bytes,
        sender: object,
        message: object,
        timestamp: object,
        nonce: object,
        signature: object,
        now: Optional[int] = None,
    ) -> Tuple[bool, str, Optional[Dict[str, object]]]:
        current = int(time.time()) if now is None else now
        if not isinstance(sender, str) or not LABEL_RE.fullmatch(sender):
            return False, "invalid_sender", None
        if not isinstance(message, str) or message not in ALLOWED_MESSAGES:
            return False, "invalid_message", None
        if not isinstance(timestamp, int) or abs(current - timestamp) > MAX_CLOCK_SKEW_SECONDS:
            return False, "stale_timestamp", None
        if not isinstance(nonce, str) or not NONCE_RE.fullmatch(nonce):
            return False, "invalid_nonce", None
        if not isinstance(signature, str) or not re.fullmatch(r"[a-f0-9]{64}", signature):
            return False, "invalid_signature", None
        expected = sign_payload(secret, sender, message, timestamp, nonce)
        if not hmac.compare_digest(expected, signature):
            return False, "invalid_signature", None

        with self._lock:
            self._nonces = {
                seen_nonce: seen_at
                for seen_nonce, seen_at in self._nonces.items()
                if current - seen_at <= NONCE_TTL_SECONDS
            }
            if nonce in self._nonces:
                return False, "replayed_nonce", None
            self._nonces[nonce] = float(current)
            self._sequence += 1
            display = ALLOWED_MESSAGES[message]
            self._signal = {
                "sequence": self._sequence,
                "sender": sender,
                "message": message,
                "display": display,
                "morse": encode_morse(display),
                "received_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(current)),
                "integrity": "SIGNED + FRESH + UNIQUE",
            }
            return True, "accepted", dict(self._signal)


class LanternServer(ThreadingHTTPServer):
    allow_reuse_address = True

    def __init__(self, address, handler, secret: bytes, web_root: Path) -> None:
        super().__init__(address, handler)
        self.secret = secret
        self.web_root = web_root
        self.signal_state = SignalState()


class LanternHandler(BaseHTTPRequestHandler):
    server_version = "LanternLink/1.0"
    sys_version = ""

    @property
    def lantern_server(self) -> LanternServer:
        return self.server  # type: ignore[return-value]

    def log_message(self, _format: str, *_args) -> None:
        # Deliberately suppress BaseHTTPRequestHandler's client-IP request log.
        return

    def _send_bytes(self, status: int, content_type: str, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'",
        )
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: int, payload: Dict[str, object]) -> None:
        body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        self._send_bytes(status, "application/json; charset=utf-8", body)

    def do_GET(self) -> None:  # noqa: N802 - HTTP handler API
        path = self.path.split("?", 1)[0]
        if path == "/health":
            self._send_json(HTTPStatus.OK, {"status": "ok", "service": "LanternLink"})
            return
        if path == "/api/state":
            self._send_json(HTTPStatus.OK, self.lantern_server.signal_state.snapshot())
            return
        file_name = "index.html" if path == "/" else path.lstrip("/")
        if file_name not in {"index.html", "app.js", "style.css"}:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
            return
        target = self.lantern_server.web_root / file_name
        if not target.is_file():
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
            return
        types = {
            ".html": "text/html; charset=utf-8",
            ".js": "text/javascript; charset=utf-8",
            ".css": "text/css; charset=utf-8",
        }
        self._send_bytes(HTTPStatus.OK, types[target.suffix], target.read_bytes())

    def do_POST(self) -> None:  # noqa: N802 - HTTP handler API
        if self.path.split("?", 1)[0] != "/api/signal":
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length <= 0 or length > MAX_BODY_BYTES:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid_body"})
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid_json"})
            return
        if not isinstance(payload, dict):
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid_json"})
            return
        accepted, reason, signal = self.lantern_server.signal_state.apply(
            self.lantern_server.secret,
            payload.get("sender"),
            payload.get("message"),
            payload.get("timestamp"),
            payload.get("nonce"),
            payload.get("signature"),
        )
        if not accepted:
            self._send_json(HTTPStatus.UNAUTHORIZED, {"accepted": False, "error": reason})
            return
        self._send_json(HTTPStatus.ACCEPTED, {"accepted": True, "signal": signal})


def create_server(host: str, port: int, secret: bytes, web_root: Path) -> LanternServer:
    validate_secret(secret)
    return LanternServer((host, port), LanternHandler, secret, web_root)


def signal_document(secret: bytes, sender: str, message: str, now: Optional[int] = None) -> Dict[str, object]:
    validate_secret(secret)
    if not LABEL_RE.fullmatch(sender):
        raise ValueError("sender must match [A-Z0-9][A-Z0-9_-]{0,23}")
    if message not in ALLOWED_MESSAGES:
        raise ValueError("message must be one of: " + ", ".join(sorted(ALLOWED_MESSAGES)))
    timestamp = int(time.time()) if now is None else now
    nonce = secrets.token_hex(16)
    return {
        "sender": sender,
        "message": message,
        "timestamp": timestamp,
        "nonce": nonce,
        "signature": sign_payload(secret, sender, message, timestamp, nonce),
    }


def send_signal(server_url: str, secret: bytes, sender: str, message: str) -> Dict[str, object]:
    payload = signal_document(secret, sender, message)
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        server_url.rstrip("/") + "/api/signal",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"receiver rejected signal ({error.code}): {detail}") from error


def secret_from_environment() -> bytes:
    value = os.environ.get("LANTERNLINK_SECRET", "")
    if not value:
        raise ValueError("set LANTERNLINK_SECRET before serving or sending")
    secret = value.encode("utf-8")
    validate_secret(secret)
    return secret


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    serve = subparsers.add_parser("serve", help="run the receiver and visual beacon")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=DEFAULT_PORT)

    send = subparsers.add_parser("send", help="send one authenticated signal")
    send.add_argument("--server", default=f"http://127.0.0.1:{DEFAULT_PORT}")
    send.add_argument("--sender", default="WORKSHOP-1")
    send.add_argument("--message", choices=sorted(ALLOWED_MESSAGES), required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    secret = secret_from_environment()
    if args.command == "serve":
        web_root = Path(__file__).resolve().parent / "web"
        server = create_server(args.host, args.port, secret, web_root)
        print(f"LanternLink receiver ready on {args.host}:{args.port}")
        try:
            server.serve_forever(poll_interval=0.2)
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
        return 0
    result = send_signal(args.server, secret, args.sender, args.message)
    signal = result["signal"]
    print(
        "accepted sequence={sequence} sender={sender} message={message} integrity={integrity}".format(
            **signal
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

