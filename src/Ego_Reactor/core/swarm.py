"""
Swarm - Orchestrates a collection of SwarmNodes.

Handles:
- Creating nodes and wiring them in ring topology
- Running the simulation loop
- Collecting statistics across all nodes
- Providing visualization data
"""

import time
from typing import Optional
from Ego_Reactor.nodes.swarm_node import SwarmNode


class Swarm:
    """
    A swarm of interconnected nodes.
    
    Default topology is a ring: each node connects to its neighbors.
    This gives O(1) connections per node while maintaining connectivity.
    """
    
    def __init__(self, num_nodes: int = 4):
        self.nodes: list[SwarmNode] = []
        self.start_time: float = time.time()
        
        # Create nodes
        for i in range(num_nodes):
            node = SwarmNode(node_id=f"node_{i}")
            self.nodes.append(node)
        
        # Wire ring topology
        self._wire_ring()
    
    def _wire_ring(self):
        """Connect nodes in a ring topology."""
        n = len(self.nodes)
        for i, node in enumerate(self.nodes):
            # Connect to neighbors
            left = self.nodes[(i - 1) % n]
            right = self.nodes[(i + 1) % n]
            node.add_peer(left)
            node.add_peer(right)
            
            # Optional: add one long-range link for small-world property
            if n > 4:
                far = self.nodes[(i + n // 2) % n]
                node.add_peer(far)
    
    def tick(self) -> dict:
        """
        Run one tick across all nodes.
        
        Returns summary of what happened.
        """
        all_propagated = []
        
        for node in self.nodes:
            propagated = node.tick()
            all_propagated.extend(propagated)
        
        return {
            "timestamp": time.time(),
            "events_propagated": len(all_propagated),
            "events": [str(e) for e in all_propagated]
        }
    
    def run(self, duration: float = 30.0, tick_interval: float = 0.1,
            callback: Optional[callable] = None):
        """
        Run the swarm simulation.
        
        Args:
            duration: How long to run (seconds)
            tick_interval: Time between ticks
            callback: Optional function called each tick with stats
        """
        self.start_time = time.time()
        tick_count = 0
        
        while time.time() - self.start_time < duration:
            result = self.tick()
            tick_count += 1
            
            if callback:
                callback(tick_count, result, self.get_stats())
            
            time.sleep(tick_interval)
        
        return self.get_stats()
    
    def get_stats(self) -> dict:
        """Aggregate statistics from all nodes."""
        total_generated = sum(n.stats.events_generated for n in self.nodes)
        total_received = sum(n.stats.events_received for n in self.nodes)
        total_propagated = sum(n.stats.events_propagated for n in self.nodes)
        total_suppressed = sum(n.stats.events_suppressed for n in self.nodes)
        total_negative = sum(n.stats.negative_events for n in self.nodes)
        
        all_events = total_generated + total_received
        suppression_rate = total_suppressed / max(1, all_events)
        
        return {
            "runtime": f"{time.time() - self.start_time:.1f}s",
            "num_nodes": len(self.nodes),
            "total_events_generated": total_generated,
            "total_events_received": total_received,
            "total_propagated": total_propagated,
            "total_suppressed": total_suppressed,
            "total_negative_events": total_negative,
            "suppression_rate": f"{suppression_rate:.1%}",
            "energy_saved": f"{suppression_rate * 100:.0f}%",
            "per_node": [n.get_status() for n in self.nodes]
        }
    
    def get_recent_events(self, limit: int = 20) -> list[dict]:
        """Get recent events across all nodes for visualization."""
        all_events = []
        for node in self.nodes:
            all_events.extend(list(node.event_log))
        
        # Sort by time, return most recent
        all_events.sort(key=lambda e: e["time"], reverse=True)
        return all_events[:limit]
