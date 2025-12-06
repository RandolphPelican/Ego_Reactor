#!/usr/bin/env python3
"""Simple non-animated test runner."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from Ego_Reactor.core.swarm import Swarm
import time

def main():
    print("\n=== EGO_REACTOR SIMPLE TEST ===\n")
    
    swarm = Swarm(num_nodes=4)
    print("Swarm initialized: 4 nodes, ring topology")
    print("Running for 30 seconds...\n")
    
    start = time.time()
    tick = 0
    
    while time.time() - start < 30:
        result = swarm.tick()
        tick += 1
        
        # Print progress every 50 ticks
        if tick % 50 == 0:
            stats = swarm.get_stats()
            suppressed = stats['total_suppressed']
            total = stats['total_events_generated'] + stats['total_events_received']
            rate = suppressed / max(1, total)
            print(f"  Tick {tick:4d} | Events: {total:4d} | Suppressed: {suppressed:4d} | Rate: {rate:.1%}")
        
        time.sleep(0.05)
    
    # Final stats
    stats = swarm.get_stats()
    print("\n" + "="*50)
    print("FINAL RESULTS:")
    print("="*50)
    print(f"  Total Generated:  {stats['total_events_generated']}")
    print(f"  Total Received:   {stats['total_events_received']}")
    print(f"  Total Propagated: {stats['total_propagated']}")
    print(f"  Total Suppressed: {stats['total_suppressed']}")
    print(f"  Negative Events:  {stats['total_negative_events']}")
    print(f"\n  SUPPRESSION RATE: {stats['suppression_rate']}")
    print(f"  ENERGY SAVED:     {stats['energy_saved']}")
    print("="*50)
    
    print("\nPer-node stats:")
    for node in stats['per_node']:
        print(f"  {node['node_id']}: epsilon={node['epsilon']}, suppression={node['suppression_rate']}")

if __name__ == "__main__":
    main()
