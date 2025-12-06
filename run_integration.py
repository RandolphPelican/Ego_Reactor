#!/usr/bin/env python3
"""Ego_Reactor Full Integration Demo"""

import sys
import time
sys.path.insert(0, "src")

from Ego_Reactor.core.swarm import Swarm
from Ego_Reactor.core.vocabulary import VocabularyManager
from Ego_Reactor.core.stigmergy import StigmergicManager
from Ego_Reactor.core.heartbeat import HeartbeatCoordinator
from Ego_Reactor.core.symbols import Symbol, Event

def main():
    print("\n" + "="*60)
    print("  EGO_REACTOR - FULL INTEGRATION DEMO")
    print("="*60 + "\n")
    
    print(">> INITIALIZING")
    swarm = Swarm(num_nodes=4)
    vocab = VocabularyManager()
    stigmergy = StigmergicManager(quorum_threshold=3)
    heartbeat = HeartbeatCoordinator(pulse_interval=0.5)
    
    for node in swarm.nodes:
        heartbeat.register_node(node)
    
    print(f"   Nodes: {len(swarm.nodes)}")
    print(f"   Vocabulary: {len(vocab)} symbols")
    
    print("\n>> RUNNING (20 seconds)")
    print("-"*40)
    
    start = time.time()
    tick = 0
    seen_symbols = set()
    
    while time.time() - start < 20:
        swarm.tick()
        tick += 1
        heartbeat.check_pulse()
        
        for node in swarm.nodes:
            for entry in list(node.event_log)[-3:]:
                parts = entry["symbol"].split(":")
                if len(parts) == 2:
                    sym = Symbol(parts[0], parts[1])
                    sym_key = str(sym)
                    
                    if sym_key not in seen_symbols:
                        action = vocab.observe(sym, node.node_id)
                        seen_symbols.add(sym_key)
                        if action == "born":
                            print(f"   + BIRTH: {sym}")
        
        if tick % 40 == 0:
            s = swarm.get_stats()
            print(f"   [{time.time()-start:.0f}s] suppression={s['suppression_rate']}")
        
        time.sleep(0.05)
    
    print("\n" + "="*60)
    print("  RESULTS")
    print("="*60)
    
    s = swarm.get_stats()
    print(f"  Suppression Rate: {s['suppression_rate']}")
    print(f"  Energy Saved:     {s['energy_saved']}")
    
    v = vocab.get_stats()
    print(f"  Vocabulary:       {v['total']} symbols")
    
    st = stigmergy.get_stats()
    print(f"  Quorums Formed:   {st['quorums_formed']}")
    
    h = heartbeat.get_stats()
    print(f"  Heartbeat Duty:   {h['duty_cycle']}")
    
    print("\n  DEMO COMPLETE\n")

if __name__ == "__main__":
    main()
