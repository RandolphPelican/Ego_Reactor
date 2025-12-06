# Ego_Reactor

**Neuromorphic Event-Driven Swarm Intelligence**

A distributed AI architecture achieving **80-95% energy savings** through predictive coding and surprise-gated message passing.
Traditional IoT: Sensor -> Broadcast -> Everyone processes
Ego_Reactor:     Sensor -> Predict -> Surprising? -> Broadcast
## Quick Start

```bash
git clone https://github.com/RandolphPelican/Ego_Reactor.git
cd Ego_Reactor

# See learning in action (80%+ suppression)
python3 run_learning_test.py

# Full integration demo
python3 run_integration.py

# Run tests
python3 tests/test_core.py
Results
=== EGO_REACTOR LEARNING TEST ===
  Window 1: 79.7% suppressed
  Window 2: 82.0% suppressed
  Window 3: 80.8% suppressed
  Window 4: 82.2% suppressed
  Window 5: 82.6% suppressed
  
  Model is LEARNING - suppression improves over time!
Architecture
+------------------+     +------------------+
|     Node 0       |<--->|     Node 1       |
|  +------------+  |     |  +------------+  |
|  |  EgoCore   |  |     |  |  EgoCore   |  |
|  | (predictor)|  |     |  | (predictor)|  |
|  +------------+  |     |  +------------+  |
|  | Sensors    |  |     |  | Sensors    |  |
|  | CRDT State |  |     |  | CRDT State |  |
+--------+---------+     +--------+---------+
         |                        |
         v                        v
+------------------+     +------------------+
|     Node 3       |<--->|     Node 2       |
+------------------+     +------------------+

Ring topology with gossip protocol
Features
Core: Predictive Surprise Gating
Each node predicts what sensors will report. Only surprising events propagate.
80%+ of predictable events suppressed
Energy savings scale with predictability
Symbol Birth/Death
Vocabulary evolves dynamically:
New patterns -> provisional symbols
Confirmed by 2+ nodes -> permanent
Unused symbols -> garbage collected
Stigmergic Consensus
Emergent swarm-level symbols:
3+ nodes agree on state -> quorum symbol emitted
Enables coordination without central authority
Biological analog: ant pheromone trails
One-Bit Heartbeat
Ultra-low-power wake signal:
1 bit/second: "something interesting?"
Nodes sleep during quiet periods
Biological analog: thalamic gating
Hardware Abstraction
Swap simulation for real sensors:
# Simulation
sensor = create_sensor('door', 'node_0', backend='fake')

# Raspberry Pi
sensor = create_sensor('door', 'node_0', backend='rpi', pin=17)
Project Structure
Ego_Reactor/
├── src/Ego_Reactor/
│   ├── core/
│   │   ├── symbols.py      # Symbol, Event types
│   │   ├── ego_core.py     # Predictive engine
│   │   ├── swarm.py        # Swarm orchestrator
│   │   ├── vocabulary.py   # Symbol birth/death
│   │   ├── stigmergy.py    # Consensus detection
│   │   └── heartbeat.py    # Wake signal
│   ├── crdt/
│   │   └── lww_map.py      # Distributed state
│   ├── sensors/
│   │   ├── fake_sensors.py # Simulation
│   │   └── hardware.py     # Real sensors
│   └── demo/
│       └── run_demo.py     # Visualization
├── tests/                   # Unit tests
├── run_learning_test.py     # Learning demo
├── run_integration.py       # Full demo
└── run_simple.py           # Basic test
The Science
Based on:
Predictive Coding: Brain predicts input, only errors propagate
Sparse Coding: Most information is redundant
Gossip Protocols: Epidemic information spread
CRDTs: Coordination-free distributed state
Hardware Setup
Raspberry Pi (~$25):
Pi Zero W: $15
Reed switch (door): $3
PIR motion sensor: $5
Jumper wires: $2
ESP32 (~$15):
ESP32 dev board: $8
Same sensors: $7
License
MIT
"The swarm that thinks by not thinking about the boring stuff."
