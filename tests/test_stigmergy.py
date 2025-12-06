#!/usr/bin/env python3
"""Test stigmergic consensus detection."""
import sys
sys.path.insert(0, "src")

from Ego_Reactor.core.stigmergy import StigmergicManager
from Ego_Reactor.core.symbols import Symbol, Event

def test_stigmergy():
    print("Testing Stigmergic Consensus...")
    
    sm = StigmergicManager(quorum_threshold=3)
    sym = Symbol("door", "open")
    
    # Two nodes - no quorum yet
    sm.observe(Event(symbol=sym, source_node="n0"))
    result = sm.observe(Event(symbol=sym, source_node="n1"))
    assert result is None
    print("  OK: No quorum with 2 nodes")
    
    # Third node - quorum forms!
    result = sm.observe(Event(symbol=sym, source_node="n2"))
    assert result is not None
    assert result.symbol.domain == "quorum"
    print("  OK: Quorum forms with 3 nodes")
    
    # Check active quorums
    assert len(sm.get_active_quorums()) == 1
    print("  OK: Active quorum tracked")
    
    # Stats
    stats = sm.get_stats()
    assert stats["quorums_formed"] == 1
    print("  OK: Stats tracking")
    
    print("Stigmergy tests passed!")

if __name__ == "__main__":
    test_stigmergy()
