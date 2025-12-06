"""
Hardware Abstraction Layer for Ego_Reactor.

Provides a unified interface for sensors whether running in simulation
or on real hardware (ESP32, Raspberry Pi, etc.).

Usage:
    # Simulation
    sensor = create_sensor('door', backend='fake')
    
    # Real hardware (Raspberry Pi)
    sensor = create_sensor('door', backend='rpi', pin=17)
    
    # Read value
    event = sensor.read()
"""

from abc import ABC, abstractmethod
from typing import Optional, Any
from dataclasses import dataclass
from enum import Enum
import time

from Ego_Reactor.core.symbols import Symbol, Event, EventType


class SensorBackend(Enum):
    FAKE = "fake"
    RPI = "rpi"       # Raspberry Pi GPIO
    ESP32 = "esp32"   # ESP32 (future)
    MQTT = "mqtt"     # MQTT broker (future)


@dataclass
class SensorConfig:
    """Configuration for a hardware sensor."""
    domain: str
    states: list[str]
    backend: SensorBackend = SensorBackend.FAKE
    pin: Optional[int] = None
    poll_interval: float = 0.5
    invert: bool = False
    extra: dict = None
    
    def __post_init__(self):
        if self.extra is None:
            self.extra = {}


class BaseSensor(ABC):
    """Abstract base class for all sensors."""
    
    def __init__(self, config: SensorConfig, node_id: str):
        self.config = config
        self.node_id = node_id
        self.last_state: Optional[str] = None
        self.last_read: float = 0.0
    
    @abstractmethod
    def _read_raw(self) -> Any:
        """Read raw value from hardware. Override in subclasses."""
        pass
    
    @abstractmethod
    def _raw_to_state(self, raw: Any) -> str:
        """Convert raw value to state string. Override in subclasses."""
        pass
    
    def read(self) -> Optional[Event]:
        """Read sensor and return Event if state changed."""
        now = time.time()
        if now - self.last_read < self.config.poll_interval:
            return None
        
        self.last_read = now
        raw = self._read_raw()
        state = self._raw_to_state(raw)
        
        if state == self.last_state:
            return None
        
        self.last_state = state
        return Event(
            symbol=Symbol(self.config.domain, state),
            timestamp=now,
            event_type=EventType.POSITIVE,
            confidence=0.95,
            source_node=self.node_id
        )
    
    def force_read(self) -> Event:
        """Force a read regardless of state change."""
        raw = self._read_raw()
        state = self._raw_to_state(raw)
        self.last_state = state
        return Event(
            symbol=Symbol(self.config.domain, state),
            timestamp=time.time(),
            confidence=0.95,
            source_node=self.node_id
        )


class FakeDigitalSensor(BaseSensor):
    """Simulated digital sensor (door, motion, etc.)."""
    
    def __init__(self, config: SensorConfig, node_id: str):
        super().__init__(config, node_id)
        import random
        self._random = random
        self._state_idx = 0
    
    def _read_raw(self) -> bool:
        # Simulate state changes with some probability
        if self._random.random() < 0.1:
            self._state_idx = (self._state_idx + 1) % len(self.config.states)
        return self._state_idx
    
    def _raw_to_state(self, raw: int) -> str:
        return self.config.states[raw]


class RPiDigitalSensor(BaseSensor):
    """Raspberry Pi GPIO digital sensor."""
    
    def __init__(self, config: SensorConfig, node_id: str):
        super().__init__(config, node_id)
        if config.pin is None:
            raise ValueError("RPi sensor requires pin number")
        
        try:
            import RPi.GPIO as GPIO
            self.GPIO = GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(config.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        except ImportError:
            raise ImportError("RPi.GPIO not available. Install with: pip install RPi.GPIO")
    
    def _read_raw(self) -> bool:
        value = self.GPIO.input(self.config.pin)
        return not value if self.config.invert else value
    
    def _raw_to_state(self, raw: bool) -> str:
        # Assumes binary sensor with 2 states
        return self.config.states[1] if raw else self.config.states[0]


def create_sensor(domain: str, node_id: str, 
                  backend: str = "fake", **kwargs) -> BaseSensor:
    """
    Factory function to create sensors.
    
    Args:
        domain: Sensor domain (door, motion, light, etc.)
        node_id: ID of the node this sensor belongs to
        backend: "fake", "rpi", "esp32", "mqtt"
        **kwargs: Backend-specific arguments (pin, etc.)
    
    Returns:
        Configured sensor instance
    """
    # Default state mappings
    state_maps = {
        "door": ["closed", "open"],
        "motion": ["idle", "detected"],
        "window": ["closed", "open"],
        "light": ["off", "on"],
        "button": ["released", "pressed"],
    }
    
    states = kwargs.pop("states", state_maps.get(domain, ["off", "on"]))
    backend_enum = SensorBackend(backend)
    
    config = SensorConfig(
        domain=domain,
        states=states,
        backend=backend_enum,
        **kwargs
    )
    
    if backend_enum == SensorBackend.FAKE:
        return FakeDigitalSensor(config, node_id)
    elif backend_enum == SensorBackend.RPI:
        return RPiDigitalSensor(config, node_id)
    else:
        raise ValueError(f"Backend {backend} not yet implemented")


# Preset sensor configurations for common hardware
PRESETS = {
    "rpi_door": lambda node_id, pin: create_sensor(
        "door", node_id, backend="rpi", pin=pin, invert=True
    ),
    "rpi_motion": lambda node_id, pin: create_sensor(
        "motion", node_id, backend="rpi", pin=pin, poll_interval=0.1
    ),
    "fake_door": lambda node_id: create_sensor("door", node_id, backend="fake"),
    "fake_motion": lambda node_id: create_sensor("motion", node_id, backend="fake"),
}
