"""
SwarmNode - A complete node in the Ego_Reactor swarm.

Each SwarmNode has:
- An EgoCore for prediction and surprise computation
- Sensors that generate events
- A CRDT for shared state
- Gossip connections to peer nodes
- Event queue for incoming messages

Nodes operate autonomously, sharing only surprising information.
"""

import time
import random
from typing import Optional, Callable
from collections import deque
from dataclasses import dataclass, field

from Ego_Reactor.core.symbols import Symbol, Event, EventType
from Ego_Reactor.core.ego_core import EgoCore
from Ego_Reactor.crdt.lww_map import LWWMap, SymbolConfidenceMap
from Ego_Reactor.sensors.fake_sensors import FakeSensor, create_smart_home_sensors


@dataclass
class GossipMessage:
    """A message passed between nodes."""
    event: Event
    sender_id: str
    crdt_snapshot: Optional[dict] = None  # Optional state sync


@dataclass 
class NodeStats:
    """Statistics for monitoring node behavior."""
    events_generated: int = 0
    events_received: int = 0
    events_propagated: int = 0
    events_suppressed: int = 0
    negative_events: int = 0
    gossip_sent: int = 0
    gossip_received: int = 0


class SwarmNode:
    """
    A single node in the Ego_Reactor swarm.
    
    The node runs a simple loop:
    1. Poll sensors for new events
    2. Process events through EgoCore (compute surprise)
    3. Gate events: suppress low-surprise, propagate high-surprise
    4. Merge incoming gossip into CRDT
    5. Periodically check for negative events (expected-but-missing)
    """
    
    def __init__(self, node_id: str, sensors: Optional[list[FakeSensor]] = None):
        self.node_id = node_id
        self.ego_core = EgoCore(node_id)
        
        # Sensors (use default smart home set if not provided)
        self.sensors = sensors or create_smart_home_sensors(node_id)
        
        # Shared state via CRDT
        self.crdt = SymbolConfidenceMap(node_id)
        
        # Peer connections (ring topology)
        self.peers: list['SwarmNode'] = []
        
        # Incoming message queue
        self.inbox: deque[GossipMessage] = deque(maxlen=100)
        
        # Stats
        self.stats = NodeStats()
        
        # Timing for negative event checks
        self.last_negative_check: float = time.time()
        self.negative_check_interval: float = 5.0  # seconds
        
        # Layer 2: Recent surprise tracking for precision adjustment
        self.recent_surprises: deque[float] = deque(maxlen=50)
        self.precision_update_interval: float = 10.0
        self.last_precision_update: float = time.time()
        
        # Event log for visualization
        self.event_log: deque[dict] = deque(maxlen=200)
        
    def add_peer(self, peer: 'SwarmNode'):
        """Add a gossip peer (typically 2-4 for ring topology)."""
        if peer not in self.peers and peer.node_id != self.node_id:
            self.peers.append(peer)
    
    def tick(self) -> list[Event]:
        """
        Run one iteration of the node's main loop.
        
        Returns list of events that were propagated (for visualization).
        """
        propagated = []
        current_time = time.time()
        
        # --- 1. Poll Sensors ---
        for sensor in self.sensors:
            event = sensor.generate_event()
            if event:
                processed = self._process_local_event(event)
                if processed and processed.should_propagate(self.ego_core.epsilon):
                    propagated.append(processed)
                    self._gossip(processed)
        
        # --- 2. Process Incoming Gossip ---
        while self.inbox:
            msg = self.inbox.popleft()
            self.stats.gossip_received += 1
            
            # Merge CRDT if included
            if msg.crdt_snapshot:
                remote_crdt = SymbolConfidenceMap.from_dict(msg.crdt_snapshot)
                self.crdt.merge(remote_crdt)
            
            # Process the event
            if msg.event.hops < 3:  # TTL to prevent infinite loops
                processed = self._process_remote_event(msg.event)
                if processed and processed.should_propagate(self.ego_core.epsilon):
                    propagated.append(processed)
                    self._gossip(processed)
        
        # --- 3. Check for Negative Events ---
        if current_time - self.last_negative_check > self.negative_check_interval:
            negative_events = self.ego_core.check_negative_events(current_time)
            for neg_event in negative_events:
                self.stats.negative_events += 1
                self._log_event(neg_event, "negative")
                if neg_event.should_propagate(self.ego_core.epsilon):
                    propagated.append(neg_event)
                    self._gossip(neg_event)
            self.last_negative_check = current_time
        
        # --- 4. Update Precision (Layer 2) ---
        if current_time - self.last_precision_update > self.precision_update_interval:
            self._update_precision()
            self.last_precision_update = current_time
        
        return propagated
    
    def _process_local_event(self, event: Event) -> Event:
        """Process an event from local sensors."""
        self.stats.events_generated += 1
        
        # Run through EgoCore to compute surprise
        processed = self.ego_core.observe(event)
        
        # Track surprise for precision adjustment
        self.recent_surprises.append(processed.surprise)
        
        # Update CRDT
        self.crdt.update_symbol(
            str(processed.symbol),
            processed.confidence,
            processed.event_type.value
        )
        
        # Log for visualization
        action = "propagate" if processed.should_propagate(self.ego_core.epsilon) else "suppress"
        self._log_event(processed, action)
        
        if not processed.should_propagate(self.ego_core.epsilon):
            self.stats.events_suppressed += 1
        else:
            self.stats.events_propagated += 1
        
        return processed
    
    def _process_remote_event(self, event: Event) -> Optional[Event]:
        """Process an event received via gossip."""
        self.stats.events_received += 1
        
        # Run through EgoCore (may have different surprise based on local model)
        processed = self.ego_core.observe(event.with_hop())
        
        # Track surprise
        self.recent_surprises.append(processed.surprise)
        
        # Update CRDT
        self.crdt.update_symbol(
            str(processed.symbol),
            processed.confidence,
            processed.event_type.value
        )
        
        # Log
        action = "forward" if processed.should_propagate(self.ego_core.epsilon) else "absorb"
        self._log_event(processed, action)
        
        if processed.should_propagate(self.ego_core.epsilon):
            self.stats.events_propagated += 1
            return processed
        else:
            self.stats.events_suppressed += 1
            return None
    
    def _gossip(self, event: Event):
        """Send event to peer nodes."""
        msg = GossipMessage(
            event=event,
            sender_id=self.node_id,
            crdt_snapshot=self.crdt.to_dict() if random.random() < 0.2 else None
        )
        
        for peer in self.peers:
            if peer.node_id != event.source_node:  # Don't send back to source
                peer.receive(msg)
                self.stats.gossip_sent += 1
    
    def receive(self, message: GossipMessage):
        """Receive a gossip message (adds to inbox for processing)."""
        self.inbox.append(message)
    
    def _update_precision(self):
        """Layer 2: Adjust epsilon based on recent surprise rate."""
        if not self.recent_surprises:
            return
        
        avg_surprise = sum(self.recent_surprises) / len(self.recent_surprises)
        high_surprise_count = sum(1 for s in self.recent_surprises if s > 0.5)
        surprise_rate = high_surprise_count / len(self.recent_surprises)
        
        self.ego_core.adjust_precision(surprise_rate)
    
    def _log_event(self, event: Event, action: str):
        """Log event for visualization."""
        self.event_log.append({
            "time": time.time(),
            "node": self.node_id,
            "symbol": str(event.symbol),
            "surprise": event.surprise,
            "action": action,
            "epsilon": self.ego_core.epsilon,
            "type": event.event_type.value
        })
    
    def get_status(self) -> dict:
        """Get node status for monitoring."""
        return {
            "node_id": self.node_id,
            "stats": {
                "generated": self.stats.events_generated,
                "received": self.stats.events_received,
                "propagated": self.stats.events_propagated,
                "suppressed": self.stats.events_suppressed,
                "negative": self.stats.negative_events,
            },
            "suppression_rate": (
                f"{self.stats.events_suppressed / max(1, self.stats.events_generated + self.stats.events_received):.1%}"
            ),
            "epsilon": f"{self.ego_core.epsilon:.2f}",
            "peers": len(self.peers),
            "crdt_size": len(self.crdt),
            "ego_core": self.ego_core.get_stats()
        }
