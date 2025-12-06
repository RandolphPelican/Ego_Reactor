"""
One-Bit Heartbeat - Ultra-low-power swarm wake signal.

A single bit broadcast per second: 1 if ANY node saw surprise > threshold,
0 otherwise. All nodes wake briefly to listen. Acts like a thalamic
wake-up call for the whole swarm.

Costs almost nothing, prevents total sleep during important periods.
This is Grok's suggestion #8.

Biological analog: the thalamus gating attention to the cortex.
"""

import time
from dataclasses import dataclass, field
from typing import Optional, Callable
from collections import deque


@dataclass
class HeartbeatPulse:
    """A single heartbeat pulse."""
    timestamp: float
    active: bool  # True = something interesting happened
    source_nodes: list = field(default_factory=list)


class HeartbeatCoordinator:
    """
    Coordinates the one-bit heartbeat across the swarm.
    
    Each tick:
    1. Collect surprise signals from all nodes
    2. If ANY node saw high surprise, pulse = 1
    3. Broadcast pulse to all nodes
    4. Nodes use pulse to decide sleep/wake state
    """
    
    def __init__(self, 
                 pulse_interval: float = 1.0,
                 surprise_threshold: float = 0.5,
                 history_size: int = 60):
        self.pulse_interval = pulse_interval
        self.surprise_threshold = surprise_threshold
        self.last_pulse_time = 0.0
        
        # Track pulse history for analysis
        self.history: deque[HeartbeatPulse] = deque(maxlen=history_size)
        
        # Registered nodes
        self.nodes: list = []
        
        # Stats
        self.total_pulses = 0
        self.active_pulses = 0
        
        # Callbacks for pulse events
        self.on_pulse: Optional[Callable] = None
    
    def register_node(self, node):
        """Register a node to participate in heartbeat."""
        if node not in self.nodes:
            self.nodes.append(node)
    
    def check_pulse(self) -> Optional[HeartbeatPulse]:
        """
        Check if it's time for a pulse and generate it.
        
        Returns HeartbeatPulse if pulse was generated, None otherwise.
        """
        now = time.time()
        if now - self.last_pulse_time < self.pulse_interval:
            return None
        
        self.last_pulse_time = now
        
        # Collect surprise signals from all nodes
        active_nodes = []
        for node in self.nodes:
            # Check if node saw high surprise recently
            if hasattr(node, 'recent_surprises') and node.recent_surprises:
                max_surprise = max(node.recent_surprises)
                if max_surprise >= self.surprise_threshold:
                    active_nodes.append(node.node_id)
        
        # Generate pulse
        pulse = HeartbeatPulse(
            timestamp=now,
            active=len(active_nodes) > 0,
            source_nodes=active_nodes
        )
        
        self.history.append(pulse)
        self.total_pulses += 1
        if pulse.active:
            self.active_pulses += 1
        
        # Fire callback
        if self.on_pulse:
            self.on_pulse(pulse)
        
        return pulse
    
    def get_duty_cycle(self) -> float:
        """
        Calculate what percentage of time the swarm is active.
        
        Lower = more energy savings from sleep.
        """
        if not self.history:
            return 0.0
        return sum(1 for p in self.history if p.active) / len(self.history)
    
    def get_stats(self) -> dict:
        return {
            "total_pulses": self.total_pulses,
            "active_pulses": self.active_pulses,
            "duty_cycle": f"{self.get_duty_cycle():.1%}",
            "registered_nodes": len(self.nodes),
            "energy_saved": f"{(1 - self.get_duty_cycle()) * 100:.0f}%"
        }


class SleepManager:
    """
    Manages node sleep state based on heartbeat.
    
    When heartbeat is 0 (quiet), nodes can enter low-power sleep.
    When heartbeat is 1 (active), nodes wake up to process.
    """
    
    def __init__(self, node, heartbeat: HeartbeatCoordinator):
        self.node = node
        self.heartbeat = heartbeat
        self.is_sleeping = False
        self.sleep_cycles = 0
        self.wake_cycles = 0
        
        # Register with heartbeat
        heartbeat.register_node(node)
    
    def should_process(self) -> bool:
        """Check if node should process or stay asleep."""
        # Check most recent pulse
        if not self.heartbeat.history:
            return True  # No history, stay awake
        
        last_pulse = self.heartbeat.history[-1]
        
        if last_pulse.active:
            if self.is_sleeping:
                self.is_sleeping = False
                self.wake_cycles += 1
            return True
        else:
            if not self.is_sleeping:
                self.is_sleeping = True
                self.sleep_cycles += 1
            return False
    
    def get_stats(self) -> dict:
        return {
            "is_sleeping": self.is_sleeping,
            "sleep_cycles": self.sleep_cycles,
            "wake_cycles": self.wake_cycles,
        }
