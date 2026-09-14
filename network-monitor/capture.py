"""Simple packet capture on the loopback interface.

Usage:
    python network-monitor/capture.py

Captures N packets on the Windows loopback interface, prints a one-line
summary of each, and saves them to network-monitor/captures/sample.pcap.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from scapy.all import IP, TCP, UDP, ICMP, Raw, sniff, wrpcap  # type: ignore[attr-defined]

# --- Configuration ---
INTERFACE = r"\Device\NPF_Loopback"
PACKET_COUNT = 20
OUTPUT_DIR = Path(__file__).parent / "captures"
OUTPUT_FILE = OUTPUT_DIR / "sample.pcap"


def summarize(packet) -> str:
    """Return a short human-readable summary of a single packet."""
    ts = datetime.fromtimestamp(float(packet.time)).strftime("%H:%M:%S.%f")[:-3]

    if IP in packet:
        ip = packet[IP]
        proto = ip.proto
        if TCP in packet:
            tcp = packet[TCP]
            flags = tcp.sprintf("%TCP.flags%")
            return f"{ts}  TCP   {ip.src}:{tcp.sport} -> {ip.dst}:{tcp.dport}  flags={flags}  len={len(packet)}"
        if UDP in packet:
            udp = packet[UDP]
            return f"{ts}  UDP   {ip.src}:{udp.sport} -> {ip.dst}:{udp.dport}  len={len(packet)}"
        if ICMP in packet:
            icmp = packet[ICMP]
            return f"{ts}  ICMP  {ip.src} -> {ip.dst}  type={icmp.type}  len={len(packet)}"
        return f"{ts}  IP    {ip.src} -> {ip.dst}  proto={proto}  len={len(packet)}"

    return f"{ts}  {packet.summary()}"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Sniffing {PACKET_COUNT} packets on {INTERFACE} ...")
    print("Tip: open another terminal and run:")
    print("    ping 127.0.0.1 -n 20")
    print("or hit a local endpoint to generate traffic.\n")

    packets = sniff(iface=INTERFACE, count=PACKET_COUNT, timeout=30)

    if not packets:
        print("No packets captured. Did you generate any traffic?")
        return

    print(f"\nCaptured {len(packets)} packets:\n")
    for pkt in packets:
        print(summarize(pkt))

    wrpcap(str(OUTPUT_FILE), packets)
    print(f"\nSaved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
