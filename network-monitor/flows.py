"""Flow tracking and feature extraction for CyberSentinel.

A "flow" is defined by the standard 5-tuple:
    (src_ip, src_port, dst_ip, dst_port, protocol)

All packets sharing the 5-tuple are considered part of the same flow.
The first packet determines the "forward" direction (client -> server);
reverse packets are "backward".

Feature names match CICIDS2017 exactly so that the output can be fed
directly into the trained Random Forest model.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field

from scapy.all import ICMP, IP, TCP, UDP  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FlowKey:
    """The 5-tuple identifying a flow."""
    src_ip: str
    src_port: int
    dst_ip: str
    dst_port: int
    protocol: int  # 6 = TCP, 17 = UDP, 1 = ICMP

    def reversed(self) -> "FlowKey":
        return FlowKey(self.dst_ip, self.dst_port, self.src_ip, self.src_port, self.protocol)


@dataclass
class Flow:
    """All packets belonging to a single flow, plus derived features."""

    key: FlowKey
    fwd_packets: list = field(default_factory=list)
    bwd_packets: list = field(default_factory=list)
    start_time: float = 0.0
    last_time: float = 0.0
    finished: bool = False

    # ------------------------------------------------------------------
    # Packet intake
    # ------------------------------------------------------------------

    def add(self, packet) -> None:
        """Add a packet to the flow. Determines direction from the 5-tuple.

        Direction is based on source PORT, not source IP. On loopback both
        endpoints share the same IP (127.0.0.1), so IP alone can't tell
        forward from backward. Port is the reliable signal.
        """
        ts = float(packet.time)
        if self.start_time == 0.0:
            self.start_time = ts
        self.last_time = ts

        if IP not in packet:
            return

        # Extract the source port for this packet.
        src_port = 0
        if TCP in packet:
            src_port = int(packet[TCP].sport)
        elif UDP in packet:
            src_port = int(packet[UDP].sport)

        if src_port == self.key.src_port:
            self.fwd_packets.append(packet)
        else:
            self.bwd_packets.append(packet)

        self._check_end(packet)

    def _check_end(self, packet) -> None:
        """Mark the flow as finished if FIN or RST is present."""
        if TCP in packet:
            flags = int(packet[TCP].flags)
            if flags & 0x01 or flags & 0x04:  # FIN or RST
                self.finished = True

    # ------------------------------------------------------------------
    # Feature extraction
    # ------------------------------------------------------------------

    def features(self) -> dict[str, float]:
        """Compute the 40 features the model expects."""
        fwd_lens = [len(p) for p in self.fwd_packets]
        bwd_lens = [len(p) for p in self.bwd_packets]
        all_lens = fwd_lens + bwd_lens

        duration = max(self.last_time - self.start_time, 1e-6)
        duration_us = duration * 1_000_000

        total_fwd_bytes = sum(fwd_lens)
        total_bwd_bytes = sum(bwd_lens)

        fwd_iat = self._inter_arrival_times(self.fwd_packets)
        bwd_iat = self._inter_arrival_times(self.bwd_packets)

        init_win_fwd = self._first_tcp_window(self.fwd_packets)
        init_win_bwd = self._first_tcp_window(self.bwd_packets)

        return {
            "Destination Port": float(self.key.dst_port),
            "Flow Duration": float(duration_us),
            "Total Fwd Packets": float(len(self.fwd_packets)),
            "Total Backward Packets": float(len(self.bwd_packets)),
            "Total Length of Fwd Packets": float(total_fwd_bytes),
            "Total Length of Bwd Packets": float(total_bwd_bytes),
            "Fwd Packet Length Max": float(max(fwd_lens, default=0)),
            "Fwd Packet Length Min": float(min(fwd_lens, default=0)),
            "Fwd Packet Length Mean": float(statistics.fmean(fwd_lens)) if fwd_lens else 0.0,
            "Fwd Packet Length Std": float(statistics.pstdev(fwd_lens)) if len(fwd_lens) > 1 else 0.0,
            "Bwd Packet Length Max": float(max(bwd_lens, default=0)),
            "Bwd Packet Length Min": float(min(bwd_lens, default=0)),
            "Bwd Packet Length Mean": float(statistics.fmean(bwd_lens)) if bwd_lens else 0.0,
            "Bwd Packet Length Std": float(statistics.pstdev(bwd_lens)) if len(bwd_lens) > 1 else 0.0,
            "Flow Bytes/s": float((total_fwd_bytes + total_bwd_bytes) / duration),
            "Flow Packets/s": float((len(self.fwd_packets) + len(self.bwd_packets)) / duration),
            "Flow IAT Mean": float(statistics.fmean(fwd_iat + bwd_iat)) if (fwd_iat or bwd_iat) else 0.0,
            "Flow IAT Std": float(statistics.pstdev(fwd_iat + bwd_iat)) if len(fwd_iat + bwd_iat) > 1 else 0.0,
            "Flow IAT Max": float(max(fwd_iat + bwd_iat, default=0)),
            "Flow IAT Min": float(min(fwd_iat + bwd_iat, default=0)),
            "Fwd IAT Total": float(sum(fwd_iat)),
            "Fwd IAT Mean": float(statistics.fmean(fwd_iat)) if fwd_iat else 0.0,
            "Fwd IAT Std": float(statistics.pstdev(fwd_iat)) if len(fwd_iat) > 1 else 0.0,
            "Fwd IAT Max": float(max(fwd_iat, default=0)),
            "Fwd IAT Min": float(min(fwd_iat, default=0)),
            "Bwd IAT Total": float(sum(bwd_iat)),
            "Bwd IAT Mean": float(statistics.fmean(bwd_iat)) if bwd_iat else 0.0,
            "Bwd IAT Std": float(statistics.pstdev(bwd_iat)) if len(bwd_iat) > 1 else 0.0,
            "Bwd IAT Max": float(max(bwd_iat, default=0)),
            "Bwd IAT Min": float(min(bwd_iat, default=0)),
            "Fwd PSH Flags": float(sum(1 for p in self.fwd_packets if TCP in p and int(p[TCP].flags) & 0x08)),
            "Bwd PSH Flags": float(sum(1 for p in self.bwd_packets if TCP in p and int(p[TCP].flags) & 0x08)),
            "Fwd URG Flags": float(sum(1 for p in self.fwd_packets if TCP in p and int(p[TCP].flags) & 0x20)),
            "Bwd URG Flags": float(sum(1 for p in self.bwd_packets if TCP in p and int(p[TCP].flags) & 0x20)),
            "Fwd Header Length": float(sum(self._header_len(p) for p in self.fwd_packets)),
            "Bwd Header Length": float(sum(self._header_len(p) for p in self.bwd_packets)),
            "Fwd Header Length.1": float(sum(self._header_len(p) for p in self.fwd_packets)),
            "Min Packet Length": float(min(all_lens, default=0)),
            "Max Packet Length": float(max(all_lens, default=0)),
            "Packet Length Mean": float(statistics.fmean(all_lens)) if all_lens else 0.0,
            "Packet Length Std": float(statistics.pstdev(all_lens)) if len(all_lens) > 1 else 0.0,
            "Packet Length Variance": float(statistics.pvariance(all_lens)) if len(all_lens) > 1 else 0.0,
            "Average Packet Size": float(statistics.fmean(all_lens)) if all_lens else 0.0,
            "Avg Fwd Segment Size": float(statistics.fmean(fwd_lens)) if fwd_lens else 0.0,
            "Avg Bwd Segment Size": float(statistics.fmean(bwd_lens)) if bwd_lens else 0.0,
            "Subflow Fwd Packets": float(len(self.fwd_packets)),
            "Subflow Bwd Packets": float(len(self.bwd_packets)),
            "Subflow Fwd Bytes": float(total_fwd_bytes),
            "Subflow Bwd Bytes": float(total_bwd_bytes),
            "Bwd Packets/s": float(len(self.bwd_packets) / duration),
            "Init_Win_bytes_forward": float(init_win_fwd),
            "Init_Win_bytes_backward": float(init_win_bwd),
            "act_data_pkt_fwd": float(sum(1 for p in self.fwd_packets if TCP in p and len(p[TCP].payload) > 0)),
            "min_seg_size_forward": float(self._first_tcp_header_len(self.fwd_packets)),
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _inter_arrival_times(packets: list) -> list[float]:
        if len(packets) < 2:
            return []
        times = [float(p.time) for p in packets]
        return [(times[i + 1] - times[i]) * 1_000_000 for i in range(len(times) - 1)]

    @staticmethod
    def _first_tcp_window(packets: list) -> int:
        for p in packets:
            if TCP in p:
                return int(p[TCP].window)
        return 0

    @staticmethod
    def _header_len(packet) -> int:
        if IP in packet:
            return int(packet[IP].ihl) * 4
        return 0

    @staticmethod
    def _first_tcp_header_len(packets: list) -> int:
        for p in packets:
            if TCP in p:
                return int(p[TCP].dataofs) * 4
        return 0


# ---------------------------------------------------------------------------
# Flow table
# ---------------------------------------------------------------------------

class FlowTable:
    """Tracks active flows. Hands them back when they finish or time out."""

    def __init__(self, idle_timeout_s: float = 5.0) -> None:
        self.flows: dict[FlowKey, Flow] = {}
        self.idle_timeout_s = idle_timeout_s

    def add(self, packet) -> Flow | None:
        """Feed a packet in.

        Returns the finished Flow if this packet finished one, else None.
        """
        if IP not in packet:
            return None

        key = self._make_key(packet)
        if key is None:
            return None

        if key not in self.flows and key.reversed() not in self.flows:
            self.flows[key] = Flow(key=key)

        flow = self.flows.get(key) or self.flows[key.reversed()]
        flow.add(packet)

        if flow.finished:
            del self.flows[flow.key]
            return flow
        return None

    def expire_idle(self, now: float) -> list[Flow]:
        """Return and remove flows idle for longer than the timeout."""
        expired = []
        for key in list(self.flows.keys()):
            flow = self.flows[key]
            if now - flow.last_time > self.idle_timeout_s:
                del self.flows[key]
                expired.append(flow)
        return expired

    @staticmethod
    def _make_key(packet) -> FlowKey | None:
        if IP not in packet:
            return None
        ip = packet[IP]
        if TCP in packet:
            tcp = packet[TCP]
            return FlowKey(ip.src, int(tcp.sport), ip.dst, int(tcp.dport), 6)
        if UDP in packet:
            udp = packet[UDP]
            return FlowKey(ip.src, int(udp.sport), ip.dst, int(udp.dport), 17)
        if ICMP in packet:
            return FlowKey(ip.src, 0, ip.dst, 0, 1)
        return None
