"""Live flow monitor on the loopback interface.

Captures packets in real time, groups them into flows, and prints a
summary + feature vector when each flow completes (FIN/RST or idle timeout).

This is step 2 of Phase 6 — no API calls yet. Just verify flow extraction
works on live traffic.

Usage:
    python network-monitor/live_monitor.py

Press Ctrl+C to stop.
"""

from __future__ import annotations

import time
from collections import Counter

from scapy.all import sniff  # type: ignore[attr-defined]

from flows import Flow, FlowTable

INTERFACE = r"\Device\NPF_Loopback"
BPF_FILTER = "ip and host 127.0.0.1"
IDLE_TIMEOUT_S = 3.0


def print_flow(flow: Flow) -> None:
    """Print a summary of a completed flow."""
    k = flow.key
    print(
        f"\n[flow] {k.src_ip}:{k.src_port} -> {k.dst_ip}:{k.dst_port} "
        f"(proto={k.protocol}, fwd={len(flow.fwd_packets)}, bwd={len(flow.bwd_packets)})"
    )
    # Show the top few most informative features for now.
    features = flow.features()
    interesting = [
        "Destination Port",
        "Flow Duration",
        "Total Fwd Packets",
        "Total Backward Packets",
        "Flow Bytes/s",
        "Flow Packets/s",
        "Init_Win_bytes_forward",
    ]
    for name in interesting:
        print(f"  {name:<28s} {features[name]:>15.2f}")


def main() -> None:
    table = FlowTable(idle_timeout_s=IDLE_TIMEOUT_S)
    counts = Counter()  # for stats at the end

    def handle(packet) -> None:
        now = float(packet.time)

        # Flush idle flows before adding the new packet.
        for flow in table.expire_idle(now):
            counts["expired"] += 1
            print_flow(flow)

        flow = table.add(packet)
        if flow is not None:
            counts["finished"] += 1
            print_flow(flow)
        counts["packets"] += 1

    print(f"Listening on {INTERFACE}")
    print(f"Filter: {BPF_FILTER}")
    print(f"Idle timeout: {IDLE_TIMEOUT_S}s")
    print("Generate traffic: ping 127.0.0.1 -n 20  (from another terminal)")
    print("Press Ctrl+C to stop.\n")

    try:
        sniff(
            iface=INTERFACE,
            filter=BPF_FILTER,
            prn=handle,
            store=False,
        )
    except KeyboardInterrupt:
        print("\n\nStopped by user.")

    # Flush whatever is left.
    print("\nFlushing remaining flows...")
    for flow in table.expire_idle(now=time.time() + 3600):
        print_flow(flow)


if __name__ == "__main__":
    main()
