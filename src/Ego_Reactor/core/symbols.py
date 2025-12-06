"""
Symbolic event system for Ego_Reactor.

Symbols are the atomic units of meaning - discrete tokens like "door_open", 
"motion_detected", "light_high". Events are timestamped observations of symbols
with associated surprise/confidence values.

This is the lingua franca of the swarm.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import time


class EventType(Enum):
    """Whether we observed presence or absence of expected state."""
    POSITIVE = "positive"      # We saw something
    NEGATIVE = "negative"      # We expected something but didn't see it


@dataclass(frozen=True)
class Symbol:
    """
    Atomic unit of meaning in the swarm vocabulary.
    
    Symbols are immutable identifiers. The swarm builds predictions
    about symbol sequences and co-occurrences.
    
    Examples: Symbol("door", "open"), Symbol("motion", "detected")
    """
    domain: str          # Category: "door", "motion", "light", "temp"
    state: str           # Value: "open", "closed", "detected", "high"
    
    def __str__(self):
        return f"{self.domain}:{self.state}"
    
    def __repr__(self):
        return f"Symbol({self.domain}, {self.state})"


@dataclass
class Event:
    """
    A timestamped observation of a symbol with surprise metadata.
    
    Events flow through the swarm. High-surprise events propagate
    further; low-surprise events may be gated (not forwarded).
    
    The 'surprise' field is the key to energy savings - it's computed
    by comparing observation against prediction.
    """
    symbol: Symbol
    timestamp: float = field(default_factory=time.time)
    event_type: EventType = EventType.POSITIVE
    surprise: float = 0.0          # 0.0 = fully predicted, 1.0 = total surprise
    confidence: float = 1.0        # How sure the sensor is about this reading
    source_node: Optional[str] = None   # Which node generated this
    hops: int = 0                  # How many gossip hops so far
    
    def __str__(self):
        direction = "+" if self.event_type == EventType.POSITIVE else "-"
        return f"[{direction}{self.symbol} s={self.surprise:.2f} h={self.hops}]"
    
    def should_propagate(self, epsilon: float = 0.3) -> bool:
        """
        Gating decision: should this event be gossiped to neighbors?
        
        This is THE key energy-saving mechanism. Only surprising 
        events get forwarded. Predictable events die locally.
        
        Args:
            epsilon: Surprise threshold. Higher = fewer messages.
        """
        return self.surprise >= epsilon
    
    def with_hop(self) -> 'Event':
        """Return a copy with incremented hop count for forwarding."""
        return Event(
            symbol=self.symbol,
            timestamp=self.timestamp,
            event_type=self.event_type,
            surprise=self.surprise,
            confidence=self.confidence,
            source_node=self.source_node,
            hops=self.hops + 1
        )


@dataclass
class SymbolLifecycle:
    """
    Tracks symbol birth/death for open-ended vocabulary.
    
    New symbols start provisional. If reinforced by multiple nodes,
    they become permanent. If not seen for N cycles, they're garbage
    collected. Keeps vocabulary tight (<200 symbols).
    """
    symbol: Symbol
    birth_time: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    observation_count: int = 1
    confirming_nodes: set = field(default_factory=set)
    is_permanent: bool = False
    
    def observe(self, node_id: str):
        """Record an observation from a node."""
        self.last_seen = time.time()
        self.observation_count += 1
        self.confirming_nodes.add(node_id)
        
        # Promote to permanent if confirmed by 2+ nodes
        if len(self.confirming_nodes) >= 2 and not self.is_permanent:
            self.is_permanent = True
    
    def age(self) -> float:
        """Seconds since last observation."""
        return time.time() - self.last_seen
    
    def should_garbage_collect(self, max_age: float = 3600.0) -> bool:
        """Should this symbol be removed from vocabulary?"""
        if self.is_permanent:
            return False
        return self.age() > max_age


# Common smart-home symbol vocabulary (pre-seeded)
SMART_HOME_SYMBOLS = {
    "door": ["open", "closed"],
    "motion": ["detected", "idle"],
    "light": ["high", "medium", "low", "off"],
    "temperature": ["hot", "warm", "cool", "cold"],
    "sound": ["loud", "quiet", "silent"],
    "presence": ["home", "away"],
}

def create_symbol_vocabulary() -> dict[str, Symbol]:
    """Generate the default symbol vocabulary."""
    vocab = {}
    for domain, states in SMART_HOME_SYMBOLS.items():
        for state in states:
            sym = Symbol(domain, state)
            vocab[str(sym)] = sym
    return vocab
