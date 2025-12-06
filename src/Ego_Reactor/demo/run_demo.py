"""
Demo runner for Ego_Reactor swarm simulation.

Shows the swarm learning patterns and suppressing predictable events
in real-time with ASCII visualization.
"""

import time
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from Ego_Reactor.core.swarm import Swarm


def clear_screen():
    """Clear terminal (works on Linux/Mac)."""
    print("\033[2J\033[H", end="")


def color(text: str, code: int) -> str:
    """Apply ANSI color code to text."""
    return f"\033[{code}m{text}\033[0m"


def surprise_bar(surprise: float, width: int = 20) -> str:
    """Create a visual bar for surprise level."""
    filled = int(surprise * width)
    bar = "█" * filled + "░" * (width - filled)
    
    if surprise < 0.3:
        return color(bar, 32)  # Green - suppressed
    elif surprise < 0.6:
        return color(bar, 33)  # Yellow - moderate
    else:
        return color(bar, 31)  # Red - high surprise


def format_event(event: dict) -> str:
    """Format an event for display."""
    symbol = event["symbol"]
    surprise = event["surprise"]
    action = event["action"]
    node = event["node"]
    evt_type = event.get("type", "positive")
    
    # Action colors
    action_colors = {
        "propagate": 31,  # Red
        "suppress": 32,   # Green
        "forward": 33,    # Yellow
        "absorb": 36,     # Cyan
        "negative": 35,   # Magenta
    }
    
    action_str = color(f"[{action:^10}]", action_colors.get(action, 0))
    type_indicator = "−" if evt_type == "negative" else "+"
    
    return f"  {node:8} {type_indicator}{symbol:20} {surprise_bar(surprise)} {action_str}"


def print_header():
    """Print the demo header."""
    print(color("=" * 70, 1))
    print(color("  EGO_REACTOR SWARM SIMULATION", 1))
    print(color("  Neuromorphic Event-Driven Intelligence", 36))
    print(color("=" * 70, 1))
    print()


def print_stats(stats: dict):
    """Print swarm statistics."""
    print(color("─" * 70, 90))
    print(f"  Runtime: {stats['runtime']:>10}  |  Nodes: {stats['num_nodes']}")
    print(f"  Generated: {stats['total_events_generated']:>6}  |  Propagated: {stats['total_propagated']:>6}")
    print(f"  Suppressed: {stats['total_suppressed']:>5}  |  Negative Events: {stats['total_negative_events']:>4}")
    print()
    print(f"  {color('SUPPRESSION RATE:', 1)} {color(stats['suppression_rate'], 32)}")
    print(f"  {color('ENERGY SAVED:', 1)}     {color(stats['energy_saved'], 32)} (vs. always-broadcast)")
    print(color("─" * 70, 90))


def print_legend():
    """Print the color legend."""
    print()
    print("  Legend: ", end="")
    print(color("█ Low surprise (suppressed)", 32), end="  ")
    print(color("█ Medium", 33), end="  ")
    print(color("█ High (propagated)", 31))
    print()


def demo_callback(tick: int, result: dict, stats: dict):
    """Callback for each simulation tick."""
    # Only update display every 5 ticks
    if tick % 5 != 0:
        return
    
    clear_screen()
    print_header()
    print_stats(stats)
    
    print()
    print(color("  RECENT EVENTS:", 1))
    print(color("  Node       Symbol               Surprise              Action", 90))
    print()
    
    # Get recent events from swarm (we need to access it somehow)
    # For now, just show what propagated this tick
    if result["events"]:
        for evt_str in result["events"][:8]:
            print(f"    {color(evt_str, 33)}")
    
    print_legend()
    
    # Show per-node epsilon values
    print(color("  NODE STATUS:", 1))
    for node_stat in stats["per_node"][:4]:
        node_id = node_stat["node_id"]
        epsilon = node_stat["epsilon"]
        suppression = node_stat["suppression_rate"]
        print(f"    {node_id}: ε={epsilon}  suppression={suppression}")


def main():
    """Run the demo."""
    print(color("\n  Initializing Ego_Reactor swarm...\n", 36))
    
    # Create swarm with 4 nodes
    swarm = Swarm(num_nodes=4)
    
    print(color("  Swarm initialized with 4 nodes in ring topology.", 32))
    print(color("  Each node has: door, motion, light, temperature sensors.\n", 90))
    print(color("  Starting simulation... (Ctrl+C to stop)\n", 33))
    time.sleep(2)
    
    try:
        # Run for 60 seconds
        final_stats = swarm.run(
            duration=60.0,
            tick_interval=0.1,
            callback=demo_callback
        )
        
        # Final summary
        clear_screen()
        print_header()
        print(color("\n  SIMULATION COMPLETE\n", 32))
        print_stats(final_stats)
        
    except KeyboardInterrupt:
        print(color("\n\n  Simulation stopped by user.\n", 33))
        print_stats(swarm.get_stats())


if __name__ == "__main__":
    main()
