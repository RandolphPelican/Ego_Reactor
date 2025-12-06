"""
Last-Writer-Wins Map (LWW-Map) CRDT for Ego_Reactor.

CRDTs (Conflict-free Replicated Data Types) allow distributed nodes
to share state without coordination. Each node can update locally,
and merges are always consistent regardless of order.

LWW-Map: Each key has a value and timestamp. On merge, the value
with the latest timestamp wins. Simple, effective, battle-tested.

This is how the swarm maintains shared beliefs about the world
without a central coordinator.
"""

from dataclasses import dataclass, field
from typing import Any, Optional
import time
import copy


@dataclass
class LWWEntry:
    """A single entry in the LWW-Map."""
    value: Any
    timestamp: float
    node_id: str  # Which node wrote this
    
    def __repr__(self):
        return f"LWWEntry({self.value}, t={self.timestamp:.2f}, from={self.node_id})"


class LWWMap:
    """
    Last-Writer-Wins Map CRDT.
    
    Properties:
    - Convergent: All nodes eventually reach same state
    - Commutative: Merge order doesn't matter
    - Idempotent: Merging same data twice = same result
    
    Perfect for gossip protocols where messages may arrive
    out of order or be duplicated.
    """
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        self._data: dict[str, LWWEntry] = {}
        self._tombstones: dict[str, float] = {}  # Deleted keys + deletion time
    
    def set(self, key: str, value: Any, timestamp: Optional[float] = None):
        """
        Set a value. Uses current time if timestamp not provided.
        
        Args:
            key: The key to set
            value: The value (any serializable object)
            timestamp: Optional explicit timestamp (for replaying events)
        """
        ts = timestamp if timestamp is not None else time.time()
        
        # Check if key was deleted after this timestamp
        if key in self._tombstones and self._tombstones[key] > ts:
            return  # Ignore write that predates deletion
        
        # Check if existing entry is newer
        if key in self._data and self._data[key].timestamp > ts:
            return  # Ignore older write
        
        self._data[key] = LWWEntry(value=value, timestamp=ts, node_id=self.node_id)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value by key."""
        if key in self._data:
            return self._data[key].value
        return default
    
    def get_entry(self, key: str) -> Optional[LWWEntry]:
        """Get the full entry (value + metadata) by key."""
        return self._data.get(key)
    
    def delete(self, key: str, timestamp: Optional[float] = None):
        """
        Delete a key. Records tombstone to prevent resurrection.
        """
        ts = timestamp if timestamp is not None else time.time()
        
        # Only delete if this is newer than existing data
        if key in self._data and self._data[key].timestamp > ts:
            return
        
        if key in self._data:
            del self._data[key]
        
        # Record tombstone
        if key not in self._tombstones or self._tombstones[key] < ts:
            self._tombstones[key] = ts
    
    def merge(self, other: 'LWWMap') -> int:
        """
        Merge another LWW-Map into this one.
        
        This is the magic of CRDTs - merge is commutative and idempotent.
        Call this when receiving gossip from another node.
        
        Args:
            other: The remote LWW-Map to merge
            
        Returns:
            Number of entries updated
        """
        updates = 0
        
        # Merge data entries
        for key, entry in other._data.items():
            # Check against our tombstones
            if key in self._tombstones and self._tombstones[key] > entry.timestamp:
                continue  # Our deletion is newer
            
            # Check against our data
            if key not in self._data or self._data[key].timestamp < entry.timestamp:
                self._data[key] = copy.copy(entry)
                updates += 1
        
        # Merge tombstones
        for key, ts in other._tombstones.items():
            if key not in self._tombstones or self._tombstones[key] < ts:
                self._tombstones[key] = ts
                # Apply deletion if needed
                if key in self._data and self._data[key].timestamp < ts:
                    del self._data[key]
                    updates += 1
        
        return updates
    
    def keys(self) -> list[str]:
        """Return all active keys."""
        return list(self._data.keys())
    
    def items(self) -> list[tuple[str, Any]]:
        """Return all (key, value) pairs."""
        return [(k, e.value) for k, e in self._data.items()]
    
    def to_dict(self) -> dict:
        """Export state for serialization/gossip."""
        return {
            "node_id": self.node_id,
            "data": {k: {"value": e.value, "timestamp": e.timestamp, "node_id": e.node_id} 
                     for k, e in self._data.items()},
            "tombstones": self._tombstones.copy()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'LWWMap':
        """Reconstruct from serialized state."""
        lww = cls(data["node_id"])
        for k, entry in data["data"].items():
            lww._data[k] = LWWEntry(
                value=entry["value"],
                timestamp=entry["timestamp"],
                node_id=entry["node_id"]
            )
        lww._tombstones = data.get("tombstones", {})
        return lww
    
    def __len__(self):
        return len(self._data)
    
    def __repr__(self):
        return f"LWWMap({self.node_id}, {len(self._data)} entries)"


# Convenience function for swarm-wide symbol confidence tracking
class SymbolConfidenceMap(LWWMap):
    """
    Specialized LWW-Map for tracking symbol confidence across the swarm.
    
    Keys are symbol strings, values are (confidence, last_event_type) tuples.
    This lets nodes share their beliefs about current world state.
    """
    
    def update_symbol(self, symbol_str: str, confidence: float, 
                      event_type: str = "positive"):
        """Update belief about a symbol's state."""
        self.set(symbol_str, {"confidence": confidence, "event_type": event_type})
    
    def get_confidence(self, symbol_str: str) -> float:
        """Get swarm confidence for a symbol."""
        entry = self.get(symbol_str)
        if entry and isinstance(entry, dict):
            return entry.get("confidence", 0.0)
        return 0.0
    
    def get_high_confidence_symbols(self, threshold: float = 0.7) -> list[str]:
        """Get all symbols the swarm is confident about."""
        return [
            k for k, v in self.items() 
            if isinstance(v, dict) and v.get("confidence", 0) >= threshold
        ]
