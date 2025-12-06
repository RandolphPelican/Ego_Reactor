"""
Fake sensor generators for simulation.

These generate realistic-ish patterns that the EgoCore can learn.
The goal is to have predictable patterns (which get suppressed)
punctuated by occasional surprises (which propagate).
"""

import random
import time
import math
from typing import Generator, Optional
from dataclasses import dataclass

from Ego_Reactor.core.symbols import Symbol, Event, EventType


@dataclass
class SensorConfig:
    """Configuration for a fake sensor."""
    domain: str
    states: list[str]
    base_interval: float = 2.0      # Average seconds between events
    pattern_strength: float = 0.8   # How predictable (0=random, 1=deterministic)
    noise_probability: float = 0.05 # Chance of random state


class FakeSensor:
    """
    A fake sensor that generates events with learnable patterns.
    
    Patterns:
    - Door: mostly closed, opens occasionally, always closes after
    - Motion: bursts of activity, then quiet periods
    - Light: follows time-of-day cycle (compressed for demo)
    - Temperature: slow drift with occasional jumps
    """
    
    def __init__(self, config: SensorConfig, node_id: str):
        self.config = config
        self.node_id = node_id
        self.current_state: str = config.states[0]
        self.last_event_time: float = time.time()
        self.state_history: list[str] = []
        
    def generate_event(self) -> Optional[Event]:
        """
        Generate the next event based on patterns.
        
        Returns None if no event should fire yet.
        """
        now = time.time()
        elapsed = now - self.last_event_time
        
        # Check if enough time has passed
        interval = self.config.base_interval * (0.5 + random.random())
        if elapsed < interval:
            return None
        
        # Determine next state
        next_state = self._get_next_state()
        
        # Only emit if state changed (or small chance of re-emission)
        if next_state == self.current_state and random.random() > 0.1:
            self.last_event_time = now
            return None
        
        self.current_state = next_state
        self.state_history.append(next_state)
        if len(self.state_history) > 100:
            self.state_history.pop(0)
        
        self.last_event_time = now
        
        return Event(
            symbol=Symbol(self.config.domain, next_state),
            timestamp=now,
            event_type=EventType.POSITIVE,
            surprise=0.0,  # Will be computed by EgoCore
            confidence=0.9 + random.random() * 0.1,
            source_node=self.node_id
        )
    
    def _get_next_state(self) -> str:
        """Determine next state based on domain-specific patterns."""
        states = self.config.states
        
        # Random noise override
        if random.random() < self.config.noise_probability:
            return random.choice(states)
        
        # Domain-specific patterns
        if self.config.domain == "door":
            return self._door_pattern()
        elif self.config.domain == "motion":
            return self._motion_pattern()
        elif self.config.domain == "light":
            return self._light_pattern()
        elif self.config.domain == "temperature":
            return self._temperature_pattern()
        else:
            # Generic alternating pattern
            idx = states.index(self.current_state) if self.current_state in states else 0
            if random.random() < self.config.pattern_strength:
                return states[(idx + 1) % len(states)]
            return random.choice(states)
    
    def _door_pattern(self) -> str:
        """Door: closed -> open -> closed (rarely stays open)."""
        if self.current_state == "closed":
            # Sometimes opens
            return "open" if random.random() < 0.3 else "closed"
        else:
            # Usually closes quickly after opening
            return "closed" if random.random() < 0.85 else "open"
    
    def _motion_pattern(self) -> str:
        """Motion: bursts of detected, then idle periods."""
        # Count recent motion events
        recent_motion = sum(1 for s in self.state_history[-10:] if s == "detected")
        
        if self.current_state == "idle":
            # Occasional bursts of activity
            return "detected" if random.random() < 0.2 else "idle"
        else:
            # Motion tends to continue briefly then stop
            if recent_motion > 5:
                return "idle" if random.random() < 0.7 else "detected"
            return "detected" if random.random() < 0.4 else "idle"
    
    def _light_pattern(self) -> str:
        """Light: follows compressed day cycle."""
        # Use a sine wave for time-of-day simulation (fast cycle for demo)
        cycle = (time.time() % 60) / 60  # 60-second "day"
        brightness = (math.sin(cycle * 2 * math.pi) + 1) / 2  # 0 to 1
        
        if brightness > 0.75:
            return "high"
        elif brightness > 0.5:
            return "medium"
        elif brightness > 0.25:
            return "low"
        else:
            return "off"
    
    def _temperature_pattern(self) -> str:
        """Temperature: slow drift with occasional jumps."""
        states = ["cold", "cool", "warm", "hot"]
        idx = states.index(self.current_state) if self.current_state in states else 1
        
        # Small drift up or down
        if random.random() < 0.7:
            # Stay same or drift by 1
            drift = random.choice([-1, 0, 0, 1])  # Bias toward staying
            idx = max(0, min(len(states) - 1, idx + drift))
        else:
            # Occasional larger change (AC kicked on, window opened)
            idx = random.randint(0, len(states) - 1)
        
        return states[idx]


def create_smart_home_sensors(node_id: str) -> list[FakeSensor]:
    """Create a standard set of smart home sensors."""
    return [
        FakeSensor(SensorConfig(
            domain="door",
            states=["open", "closed"],
            base_interval=3.0,
            pattern_strength=0.85
        ), node_id),
        FakeSensor(SensorConfig(
            domain="motion",
            states=["detected", "idle"],
            base_interval=1.5,
            pattern_strength=0.7
        ), node_id),
        FakeSensor(SensorConfig(
            domain="light",
            states=["high", "medium", "low", "off"],
            base_interval=5.0,
            pattern_strength=0.9
        ), node_id),
        FakeSensor(SensorConfig(
            domain="temperature",
            states=["hot", "warm", "cool", "cold"],
            base_interval=8.0,
            pattern_strength=0.8
        ), node_id),
    ]
