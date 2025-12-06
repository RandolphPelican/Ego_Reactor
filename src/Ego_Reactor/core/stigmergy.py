"""
Stigmergic Symbols - Emergent swarm-level concepts from consensus.

When multiple nodes independently agree on something (e.g., 3+ nodes
see 'door:open' within 2 seconds), the swarm creates a higher-level
symbol like 'quorum_door_open'.

This is Grok's suggestion #6 - emergent coordination without any
node being special. The CRDT itself 'emits' virtual symbols.

Biological analog: ant pheromone trails, where individual actions
create collective intelligence.
"""

import time
from dataclasses import dataclass, field
from typing import Optional
from collections import defaultdict

from Ego_Reactor.core.symbols import Symbol, Event, EventType
from Ego_Reactor.crdt.lww_map import LWWMap


@dataclass
class ConsensusWindow:
    """Tracks observations within a time window for consensus detection."""
    symbol: Symbol
    observations: list = field(default_factory=list)  # [(node_id, timestamp)]
    window_seconds: float = 2.0
    
    def add(self, node_id: str, timestamp: float):
        # Remove old observations outside window
        cutoff = timestamp - self.window_seconds
        self.observations = [(n, t) for n, t in self.observations if t > cutoff]
        self.observations.append((node_id, timestamp))
    
    def node_count(self) -> int:
        """Number of unique nodes that observed this symbol recently."""
        return len(set(n for n, t in self.observations))
    
    def has_quorum(self, min_nodes: int = 3) -> bool:
        return self.node_count() >= min_nodes


class StigmergicManager:
    """
    Detects consensus and emits emergent swarm-level symbols.
    
    Monitors the CRDT for agreement patterns and creates
    quorum symbols when threshold is reached.
    """
    
    def __init__(self, quorum_threshold: int = 3, window_seconds: float = 2.0):
        self.quorum_threshold = quorum_threshold
        self.window_seconds = window_seconds
        
        # Track observations per symbol
        self.windows: dict[str, ConsensusWindow] = {}
        
        # Active quorum symbols
        self.active_quorums: dict[str, float] = {}  # symbol -> activation_time
        
        # Stats
        self.quorums_formed = 0
        self.quorums_dissolved = 0
    
    def observe(self, event: Event) -> Optional[Event]:
        """
        Record an observation and check for quorum.
        
        Returns a quorum Event if consensus just formed.
        """
        sym_key = str(event.symbol)
        
        # Initialize window if needed
        if sym_key not in self.windows:
            self.windows[sym_key] = ConsensusWindow(
                symbol=event.symbol,
                window_seconds=self.window_seconds
            )
        
        # Add observation
        window = self.windows[sym_key]
        window.add(event.source_node or "unknown", event.timestamp)
        
        # Check for new quorum
        quorum_key = f"quorum_{sym_key}"
        
        if window.has_quorum(self.quorum_threshold):
            if quorum_key not in self.active_quorums:
                # NEW QUORUM FORMED!
                self.active_quorums[quorum_key] = time.time()
                self.quorums_formed += 1
                
                # Create quorum symbol
                quorum_symbol = Symbol("quorum", str(event.symbol))
                return Event(
                    symbol=quorum_symbol,
                    timestamp=time.time(),
                    event_type=EventType.POSITIVE,
                    surprise=0.8,  # Quorum events are notable
                    confidence=0.95,
                    source_node="swarm"
                )
        else:
            # Check if quorum dissolved
            if quorum_key in self.active_quorums:
                del self.active_quorums[quorum_key]
                self.quorums_dissolved += 1
                
                # Emit dissolution event
                quorum_symbol = Symbol("quorum_end", str(event.symbol))
                return Event(
                    symbol=quorum_symbol,
                    timestamp=time.time(),
                    event_type=EventType.NEGATIVE,
                    surprise=0.5,
                    confidence=0.9,
                    source_node="swarm"
                )
        
        return None
    
    def get_active_quorums(self) -> list[str]:
        """Get list of currently active quorum symbols."""
        return list(self.active_quorums.keys())
    
    def get_stats(self) -> dict:
        return {
            "active_quorums": len(self.active_quorums),
            "quorums_formed": self.quorums_formed,
            "quorums_dissolved": self.quorums_dissolved,
            "tracked_symbols": len(self.windows),
        }


def integrate_with_swarm(swarm, stigmergic_manager: StigmergicManager):
    """
    Helper to integrate stigmergic detection with existing swarm.
    
    Wraps the swarm tick to check for consensus.
    """
    original_tick = swarm.tick
    
    def enhanced_tick():
        result = original_tick()
        
        # Check all recent events for consensus
        for node in swarm.nodes:
            for log_entry in list(node.event_log)[-10:]:
                sym = Symbol(*log_entry["symbol"].split(":"))
                event = Event(
                    symbol=sym,
                    timestamp=log_entry["time"],
                    source_node=log_entry["node"]
                )
                quorum_event = stigmergic_manager.observe(event)
                if quorum_event:
                    result["quorum_events"] = result.get("quorum_events", [])
                    result["quorum_events"].append(str(quorum_event))
        
        return result
    
    swarm.tick = enhanced_tick
    return swarm
