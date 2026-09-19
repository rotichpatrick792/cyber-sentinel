"""Live flow monitor + ML classification.

Sniffs packets, groups them into flows, and sends each completed flow to
the CyberSentinel prediction API. Prints alerts for non-BENIGN flows.

Prerequisites:
    - The FastAPI backend must be running on http://127.0.0.1:8000
    - The model must be loaded (see /health)

Usage:
    python network-monitor/detect.py

Press Ctrl+C to stop.
"""

from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from scapy.all import sniff  # type: ignore[attr-defined]

from flows import Flow, FlowTable

INTERFACE = r"\Device\NPF_Loopback"
BPF_FILTER = "ip and host 127.0.0.1"
IDLE_TIMEOUT_S = 3.0
API_URL = "http://127.0.0.1:8000/api/v1/predict"


def classify(features: dict[str, float]) -> dict | None:
    """POST features to the API. Returns the parsed response or None on error."""
    body = json.dumps({"features": features}).encode("utf-8")
    req = Request(API_URL, data=body, headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        print(f"  [api error] HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:200]}")
    except URLError as e:
        print(f"  [api error] {e}")
    except Exception as e:
        print(f"  [api error] {type(e).__name__}: {e}")
    return None


def report_flow(flow: Flow) -> None:
    """Classify a completed flow and print the verdict."""
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

    if label == "BENIGN":
        print(f"[.] {src} -> {dst}  BENIGN  ({confidence:.2f})")
    else:
        print(f"[!] {src} -> {dst}  {label.upper()}  ({confidence:.2f})  <-- ALERT")
        # Show the top alternatives for context.
        probs = sorted(result["probabilities"].items(), key=lambda x: -x[1])[:3]
        for name, p in probs:
            print(f"      {name:<15s} {p:.4f}")


def main() -> None:
    table = FlowTable(idle_timeout_s=IDLE_TIMEOUT_S)

    # Quick sanity check: is the API up and the model loaded?
    try:
        with urlopen("http://127.0.0.1:8000/health", timeout=3) as resp:
            health = json.loads(resp.read().decode("utf-8"))
        if not health.get("model_loaded"):
            print(f"WARNING: API is up but model not loaded: {health.get('model_error')}")
    except Exception as e:
        print(f"WARNING: Cannot reach API at {API_URL}: {e}")
        print("Start the backend first: uvicorn app.main:app --reload")
        return

    def handle(packet) -> None:
        now = float(packet.time)
        for flow in table.expire_idle(now):
            report_flow(flow)
        flow = table.add(packet)
        if flow is not None:
            report_flow(flow)

    print(f"CyberSentinel live detection on {INTERFACE}")
    print(f"Filter: {BPF_FILTER}")
    print(f"API:    {API_URL}")
    print("Press Ctrl+C to stop.\n")

    try:
        sniff(iface=INTERFACE, filter=BPF_FILTER, prn=handle, store=False)
    except KeyboardInterrupt:
        print("\n\nStopped by user.")
        for flow in table.expire_idle(now=1e18):
            report_flow(flow)


if __name__ == "__main__":
    main()
