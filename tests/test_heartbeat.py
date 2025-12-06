#!/usr/bin/env python3
"""Test heartbeat coordinator."""
import sys
import time
sys.path.insert(0, "src")

from Ego_Reactor.core.heartbeat import HeartbeatCoordinator
from collections import deque

class FakeNode:
    def __init__(self, nid, surprises):
        self.node_id = nid
        self.recent_surprises = deque(surprises)

def test_heartbeat():
    print("Testing Heartbeat...")
    
    hb = HeartbeatCoordinator(pulse_interval=0.05)
    
    quiet = FakeNode("quiet", [0.1, 0.2])
    active = FakeNode("active", [0.8, 0.9])
    hb.register_node(quiet)
    hb.register_node(active)
    
    time.sleep(0.06)
    pulse = hb.check_pulse()
    assert pulse is not None
    assert pulse.active == True
    assert "active" in pulse.source_nodes
    print("  OK: Active pulse detected")
    
    # Test quiet swarm
    hb2 = HeartbeatCoordinator(pulse_interval=0.05)
    hb2.register_node(FakeNode("q1", [0.1]))
    hb2.register_node(FakeNode("q2", [0.2]))
    time.sleep(0.06)
    pulse2 = hb2.check_pulse()
    assert pulse2.active == False
    print("  OK: Quiet pulse (no activity)")
    
    print("Heartbeat tests passed!")

if __name__ == "__main__":
    test_heartbeat()
