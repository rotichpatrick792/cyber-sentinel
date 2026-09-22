"""Live flow monitor + ML classification.

Authenticates with the backend as a service account, sniffs packets,
groups them into flows, and sends each completed flow to the prediction
API. Prints alerts for non-BENIGN flows and posts each classified flow
to the live feed.

Credentials are read from network-monitor/.env:
    CYBERSENTINEL_API       — base URL of the backend
    CYBERSENTINEL_USERNAME  — service account username
    CYBERSENTINEL_PASSWORD  — service account password

Usage:
    python network-monitor/detect.py

Press Ctrl+C to stop.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from dotenv import load_dotenv
from scapy.all import sniff  # type: ignore[attr-defined]

from flows import Flow, FlowTable

# Load credentials from network-monitor/.env
ENV_FILE = Path(__file__).parent / ".env"
load_dotenv(ENV_FILE)

API_BASE = os.getenv("CYBERSENTINEL_API", "http://127.0.0.1:8000")
USERNAME = os.getenv("CYBERSENTINEL_USERNAME", "")
PASSWORD = os.getenv("CYBERSENTINEL_PASSWORD", "")

INTERFACE = r"\Device\NPF_Loopback"
BPF_FILTER = "ip and host 127.0.0.1"
IDLE_TIMEOUT_S = 3.0

PREDICT_URL = f"{API_BASE}/api/v1/predict"
FLOWS_URL = f"{API_BASE}/api/v1/flows"
LOGIN_URL = f"{API_BASE}/api/v1/login"
HEALTH_URL = f"{API_BASE}/health"


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

_token: str | None = None
_token_obtained_at: float = 0.0
# Refresh tokens well before they expire (they last 60 minutes).
TOKEN_REFRESH_SECONDS = 50 * 60


def login() -> str | None:
    """Obtain a fresh JWT from the backend. Returns None on failure."""
    global _token, _token_obtained_at

    if not USERNAME or not PASSWORD:
        print("ERROR: missing CYBERSENTINEL_USERNAME or CYBERSENTINEL_PASSWORD")
        return None

    body = json.dumps({"username": USERNAME, "password": PASSWORD}).encode("utf-8")
    req = Request(LOGIN_URL, data=body, headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        _token = data["access_token"]
        _token_obtained_at = time.time()
        print("Authenticated as", USERNAME)
        return _token
    except HTTPError as e:
        print(f"Login failed: HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:200]}")
    except URLError as e:
        print(f"Login failed: {e}")
    except Exception as e:
        print(f"Login failed: {type(e).__name__}: {e}")
    return None


def ensure_token() -> str | None:
    """Return a valid token, refreshing if needed."""
    if _token is None or (time.time() - _token_obtained_at) > TOKEN_REFRESH_SECONDS:
        return login()
    return _token


# ---------------------------------------------------------------------------
# API calls
# ---------------------------------------------------------------------------

def _post_json(url: str, body: dict, token: str | None) -> dict | None:
    global _token
    data = json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(url, data=data, headers=headers)
    try:
        with urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        if e.code == 401:
            # Token expired — force refresh on next call.
            _token = None
            return None
        print(f"  [api error] HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:200]}")
    except URLError as e:
        print(f"  [api error] {e}")
    except Exception as e:
        print(f"  [api error] {type(e).__name__}: {e}")
    return None


def classify(features: dict[str, float]) -> dict | None:
    token = ensure_token()
    if not token:
        return None
    return _post_json(PREDICT_URL, {"features": features}, token)


def post_flow(flow: Flow, result: dict) -> None:
    token = ensure_token()
    if not token:
        return
    body = {
        "src_ip": flow.key.src_ip,
        "src_port": flow.key.src_port,
        "dst_ip": flow.key.dst_ip,
        "dst_port": flow.key.dst_port,
        "protocol": flow.key.protocol,
        "label": result["label"],
        "confidence": result["confidence"],
    }
    _post_json(FLOWS_URL, body, token)


# ---------------------------------------------------------------------------
# Flow handling
# ---------------------------------------------------------------------------

def report_flow(flow: Flow) -> None:
    k = flow.key
    features = flow.features()
    result = classify(features)

    src = f"{k.src_ip}:{k.src_port}"
    dst = f"{k.dst_ip}:{k.dst_port}"

    if result is None:
        print(f"[?] {src} -> {dst}  (classification failed)")
        return

    label = result["label"]
    confidence = result["confidence"]

    post_flow(flow, result)

    if label == "BENIGN":
        print(f"[.] {src} -> {dst}  BENIGN  ({confidence:.2f})")
    else:
        print(f"[!] {src} -> {dst}  {label.upper()}  ({confidence:.2f})  <-- ALERT")
        probs = sorted(result["probabilities"].items(), key=lambda x: -x[1])[:3]
        for name, p in probs:
            print(f"      {name:<15s} {p:.4f}")


def main() -> None:
    # Sanity check the API.
    try:
        with urlopen(HEALTH_URL, timeout=3) as resp:
            health = json.loads(resp.read().decode("utf-8"))
        if not health.get("model_loaded"):
            print(f"WARNING: model not loaded: {health.get('model_error')}")
    except Exception as e:
        print(f"WARNING: cannot reach API at {API_BASE}: {e}")
        print("Start the backend first: uvicorn app.main:app --reload")
        return

    # Authenticate up front so we fail fast.
    if ensure_token() is None:
        print("ERROR: authentication failed. Check network-monitor/.env")
        return

    table = FlowTable(idle_timeout_s=IDLE_TIMEOUT_S)

    def handle(packet) -> None:
        now = float(packet.time)
        for flow in table.expire_idle(now):
            report_flow(flow)
        flow = table.add(packet)
        if flow is not None:
            report_flow(flow)

    print(f"CyberSentinel live detection on {INTERFACE}")
    print(f"Filter: {BPF_FILTER}")
    print(f"API:    {API_BASE}")
    print("Press Ctrl+C to stop.\n")

    try:
        sniff(iface=INTERFACE, filter=BPF_FILTER, prn=handle, store=False)
    except KeyboardInterrupt:
        print("\n\nStopped by user.")
        for flow in table.expire_idle(now=1e18):
            report_flow(flow)


if __name__ == "__main__":
    main()
