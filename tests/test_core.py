#!/usr/bin/env python3
"""Unit tests for Ego_Reactor."""
import sys
import time
sys.path.insert(0, "src")

from Ego_Reactor.core.symbols import Symbol, Event, EventType
from Ego_Reactor.core.ego_core import EgoCore
from Ego_Reactor.core.vocabulary import VocabularyManager
from Ego_Reactor.crdt.lww_map import LWWMap

def test_symbols():
    print("Testing Symbols...")
    sym = Symbol("door", "open")
    assert str(sym) == "door:open", "Symbol string failed"
    assert sym == Symbol("door", "open"), "Symbol equality failed"
    print("  OK: Symbol creation and equality")
    
    event = Event(symbol=sym, surprise=0.5)
    assert event.surprise == 0.5, "Event surprise failed"
    assert not Event(symbol=sym, surprise=0.1).should_propagate(0.3)
    assert Event(symbol=sym, surprise=0.8).should_propagate(0.3)
    print("  OK: Event creation and gating")

def test_ego_core():
    print("Testing EgoCore...")
    core = EgoCore("test")
    assert core.node_id == "test"
    print("  OK: EgoCore creation")
    
    event = Event(symbol=Symbol("door", "open"))
    result = core.observe(event)
    assert 0 <= result.surprise <= 1
    print("  OK: EgoCore observation")
    
    for _ in range(5):
        core.observe(Event(symbol=Symbol("door", "open")))
        core.observe(Event(symbol=Symbol("door", "closed")))
    assert core.total_events == 11
    print("  OK: EgoCore learning")

def test_vocabulary():
    print("Testing Vocabulary...")
    vm = VocabularyManager()
    assert len(vm) > 0
    print("  OK: Vocabulary creation")
    
    action = vm.observe(Symbol("window", "open"), "n0")
    assert action == "born"
    print("  OK: Symbol birth")
    
    action = vm.observe(Symbol("window", "open"), "n1")
    assert action == "promoted"
    print("  OK: Symbol promotion")

def test_crdt():
    print("Testing CRDT...")
    c1 = LWWMap("n0")
    c1.set("k1", "v1")
    assert c1.get("k1") == "v1"
    print("  OK: CRDT set/get")
    
    c2 = LWWMap("n1")
    c2.set("k2", "v2")
    c1.merge(c2)
    assert c1.get("k2") == "v2"
    print("  OK: CRDT merge")

if __name__ == "__main__":
    print("=" * 40)
    print("EGO_REACTOR UNIT TESTS")
    print("=" * 40)
    try:
        test_symbols()
        test_ego_core()
        test_vocabulary()
        test_crdt()
        print("=" * 40)
        print("ALL TESTS PASSED")
        print("=" * 40)
    except AssertionError as e:
        print(f"FAILED: {e}")
        sys.exit(1)
