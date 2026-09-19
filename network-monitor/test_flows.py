"""Load a pcap, feed packets through the FlowTable, print extracted features.

Usage:
    python network-monitor/test_flows.py
"""

from __future__ import annotations

from pathlib import Path

from scapy.all import rdpcap  # type: ignore[attr-defined]

from flows import FlowTable

PCAP = Path(__file__).parent / "captures" / "sample.pcap"


def main() -> None:
    if not PCAP.exists():
        print(f"No pcap at {PCAP}. Run capture.py first.")
        return

    print(f"Reading {PCAP} ...")
    packets = rdpcap(str(PCAP))
    print(f"Loaded {len(packets)} packets\n")

    table = FlowTable(idle_timeout_s=5.0)
    finished: list = []

    for pkt in packets:
        flow = table.add(pkt)
        if flow is not None:
            finished.append(flow)

    # Flush any flows still in the table.
    last_time = float(packets[-1].time) if packets else 0.0
    finished.extend(table.expire_idle(last_time))

    print(f"Extracted {len(finished)} flows\n")

    for i, flow in enumerate(finished, start=1):
        print(f"--- Flow {i}: {flow.key.src_ip}:{flow.key.src_port} -> "
              f"{flow.key.dst_ip}:{flow.key.dst_port} "
              f"(proto={flow.key.protocol}, "
              f"fwd={len(flow.fwd_packets)}, bwd={len(flow.bwd_packets)}) ---")
        features = flow.features()
        for k, v in features.items():
            print(f"  {k:<32s} {v:>15.2f}")
        print()


if __name__ == "__main__":
    main()
