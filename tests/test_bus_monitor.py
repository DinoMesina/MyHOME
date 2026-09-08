"""Tests for BusMonitor and BusFrame in-band bus tap."""
import pytest
from custom_components.myhome.bus_monitor import BusFrame, BusMonitor
from custom_components.myhome.ownd.message import OWNEvent, OWNSignaling


def test_bus_frame_parsing():
    """Verify BusFrame extracts semantics from parsed messages and strings."""
    raw_event = "*1*1*12##"
    parsed = OWNEvent.parse(raw_event)
    frame = BusFrame(direction="rx", raw=raw_event, parsed=parsed)

    assert frame.direction == "rx"
    assert frame.raw == "*1*1*12##"
    assert frame.who == 1
    assert frame.where == "12"
    assert frame.what == 1
    assert frame.is_ack is False
    assert frame.is_nack is False

    d = frame.to_dict()
    assert d["direction"] == "rx"
    assert d["who"] == "1"
    assert d["where"] == "12"
    assert d["what"] == "1"
    assert "iso_time" in d
    assert "timestamp" in d


def test_bus_frame_signaling():
    """Verify BusFrame identifies ACK and NACK frames."""
    ack_frame = BusFrame(direction="rx", raw="*#*1##", parsed=OWNSignaling("*#*1##"))
    assert ack_frame.is_ack is True
    assert ack_frame.is_nack is False

    nack_frame = BusFrame(direction="rx", raw="*#*0##", parsed=OWNSignaling("*#*0##"))
    assert nack_frame.is_ack is False
    assert nack_frame.is_nack is True

    # Fallback when parsed is None
    raw_ack = BusFrame(direction="tx", raw="*#*1##")
    assert raw_ack.is_ack is True
    assert raw_ack.is_nack is False

    raw_nack = BusFrame(direction="rx", raw="*#*0##")
    assert raw_nack.is_ack is False
    assert raw_nack.is_nack is True


def test_bus_monitor_bounded_ring_buffer():
    """Verify BusMonitor caps frame storage at maxlen and maintains counters."""
    monitor = BusMonitor(maxlen=5)
    assert monitor.maxlen == 5

    for i in range(10):
        direction = "rx" if i % 2 == 0 else "tx"
        monitor.record_frame(direction=direction, raw=f"*1*{i}*12##")

    assert monitor.total_rx == 5
    assert monitor.total_tx == 5

    stats = monitor.get_stats()
    assert stats["capacity"] == 5
    assert stats["captured"] == 5
    assert stats["total_rx"] == 5
    assert stats["total_tx"] == 5

    recent = monitor.get_recent_frames(limit=3)
    assert len(recent) == 3
    # Check that the most recent frame is the last recorded (i=9)
    assert recent[-1]["raw"] == "*1*9*12##"

    monitor.clear()
    assert monitor.get_stats()["captured"] == 0
    assert monitor.get_stats()["total_rx"] == 0


def test_bus_monitor_subscription():
    """Verify subscribers receive live captured frames and can unsubscribe."""
    monitor = BusMonitor(maxlen=10)
    received = []

    def callback(frame: BusFrame):
        received.append(frame)

    unsub = monitor.subscribe(callback)
    assert monitor.get_stats()["subscribers"] == 1

    monitor.record_frame(direction="rx", raw="*1*1*12##")
    assert len(received) == 1
    assert received[0].raw == "*1*1*12##"

    # Unsubscribe
    unsub()
    assert monitor.get_stats()["subscribers"] == 0
    monitor.record_frame(direction="tx", raw="*1*0*12##")
    # No new frames received by callback
    assert len(received) == 1


def test_bus_monitor_subscriber_exception():
    """Verify subscriber exceptions are safely handled without breaking bus flow."""
    monitor = BusMonitor()

    def faulty_callback(frame: BusFrame):
        raise RuntimeError("Subscriber failed")

    monitor.subscribe(faulty_callback)
    frame = monitor.record_frame(direction="rx", raw="*1*1*12##")
    assert frame.raw == "*1*1*12##"

