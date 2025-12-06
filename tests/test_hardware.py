#!/usr/bin/env python3
"""Test hardware abstraction layer."""
import sys
sys.path.insert(0, "src")

from Ego_Reactor.sensors.hardware import create_sensor, SensorBackend

def test_hardware():
    print("Testing Hardware Abstraction...")
    
    sensor = create_sensor("door", "node_0", backend="fake")
    assert sensor.config.backend == SensorBackend.FAKE
    print("  OK: Fake sensor creation")
    
    event = sensor.force_read()
    assert event is not None
    assert event.symbol.domain == "door"
    print("  OK: Sensor read")
    
    for domain in ["motion", "window", "light"]:
        s = create_sensor(domain, "node_0", backend="fake")
        assert s.config.domain == domain
    print("  OK: Multiple sensor types")
    
    print("Hardware tests passed!")

if __name__ == "__main__":
    test_hardware()
