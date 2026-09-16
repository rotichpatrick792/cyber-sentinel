"""Simple packet capture on the loopback interface.

Usage:
    python network-monitor/capture.py

Captures N packets on the Windows loopback interface, prints a live
one-line summary of each, and saves them to network-monitor/captures/sample.pcap.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from scapy.all import ICMP, IP, TCP, UDP, sniff, wrpcap  # type: ignore[attr-defined]

# --- Configuration ---
INTERFACE = r"\Device\NPF_Loopback"
PACKET_COUNT = 20
TIMEOUT_SECONDS = 30

# BPF filter: only loopback IP traffic, no broadcast noise.
# This is the same syntax Wireshark uses in its capture filter bar.
CAPTURE_FILTER = "ip and host 127.0.0.1"

OUTPUT_DIR = Path(__file__).parent / "captures"
OUTPUT_FILE = OUTPUT_DIR / "sample.pcap"


def summarize(packet) -> str:
    """Return a short human-readable summary of a single packet."""
    ts = datetime.fromtimestamp(float(packet.time)).strftime("%H:%M:%S.%f")[:-3]

    if IP in packet:
        ip = packet[IP]
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
        return f"{ts}  IP    {ip.src} -> {ip.dst}  proto={ip.proto}  len={len(packet)}"

    return f"{ts}  {packet.summary()}"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    captured: list = []

    def handle(packet) -> None:
        """Called by Scapy for every packet as it arrives."""
        captured.append(packet)
        print(summarize(packet))

    print(f"Sniffing up to {PACKET_COUNT} packets on {INTERFACE}")
    print(f"Filter: {CAPTURE_FILTER}")
    print("Tip: in another terminal, run:  ping 127.0.0.1 -n 20")
    print("Press Ctrl+C to stop early.\n")

    try:
        sniff(
            iface=INTERFACE,
            filter=CAPTURE_FILTER,
            prn=handle,
            count=PACKET_COUNT,
            timeout=TIMEOUT_SECONDS,
            store=False,   # we store them ourselves in `captured`
        )
    except KeyboardInterrupt:
        print("\nStopped by user.")

    if not captured:
        print("No packets captured.")
        return

    wrpcap(str(OUTPUT_FILE), captured)
    print(f"\nCaptured {len(captured)} packets.")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
