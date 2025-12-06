#!/usr/bin/env python3
"""Test that shows learning over time."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from Ego_Reactor.core.swarm import Swarm
import time

def main():
    print("\n=== EGO_REACTOR LEARNING TEST ===")
    print("Watching suppression rate improve as model learns patterns\n")
    
    swarm = Swarm(num_nodes=4)
    
    # Track stats over time windows
    windows = []
    window_duration = 10  # seconds per window
    total_duration = 60   # total runtime
    
    start = time.time()
    window_start = start
    window_generated = 0
    window_suppressed = 0
    
    last_generated = 0
    last_suppressed = 0
    
    while time.time() - start < total_duration:
        swarm.tick()
        
        # Check if window complete
        if time.time() - window_start >= window_duration:
            stats = swarm.get_stats()
            
            # Calculate delta for this window
            gen_delta = stats['total_events_generated'] - last_generated
            sup_delta = stats['total_suppressed'] - last_suppressed
            
            # Local suppression rate (generated events only)
            local_rate = sup_delta / max(1, gen_delta + sup_delta)
            
            window_num = len(windows) + 1
            windows.append({
                'window': window_num,
                'generated': gen_delta,
                'suppressed': sup_delta,
                'local_rate': local_rate
            })
            
            bar = "█" * int(local_rate * 30) + "░" * (30 - int(local_rate * 30))
            print(f"  Window {window_num}: {bar} {local_rate:.1%} suppressed ({gen_delta} gen, {sup_delta} sup)")
            
            # Reset for next window
            last_generated = stats['total_events_generated']
            last_suppressed = stats['total_suppressed']
            window_start = time.time()
        
        time.sleep(0.05)
    
    # Summary
    print("\n" + "="*60)
    print("LEARNING PROGRESSION:")
    print("="*60)
    
    if len(windows) >= 2:
        first_rate = windows[0]['local_rate']
        last_rate = windows[-1]['local_rate']
        improvement = last_rate - first_rate
        
        print(f"  First window suppression:  {first_rate:.1%}")
        print(f"  Last window suppression:   {last_rate:.1%}")
        print(f"  Improvement:               {improvement:+.1%}")
        
        if improvement > 0:
            print("\n  ✓ Model is LEARNING - suppression improves over time!")
        else:
            print("\n  → Model needs tuning or longer runtime")
    
    # Final overall stats
    stats = swarm.get_stats()
    print(f"\n  Final overall suppression: {stats['suppression_rate']}")
    print(f"  Negative events detected:  {stats['total_negative_events']}")

if __name__ == "__main__":
    main()
