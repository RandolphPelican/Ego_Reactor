"""
Ego_Reactor: Neuromorphic Event-Driven Swarm Intelligence
"""

from Ego_Reactor.core.symbols import Symbol, Event, EventType
from Ego_Reactor.core.ego_core import EgoCore
from Ego_Reactor.core.swarm import Swarm
from Ego_Reactor.nodes.swarm_node import SwarmNode
from Ego_Reactor.crdt.lww_map import LWWMap

__version__ = "0.1.0"
__all__ = ["Symbol", "Event", "EventType", "EgoCore", "Swarm", "SwarmNode", "LWWMap"]
