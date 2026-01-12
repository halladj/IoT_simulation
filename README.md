# IoT Simulation - Discovery and Collaboration Protocol

NS-3 simulation implementing a two-phase Discovery and Collaboration protocol for Mobile IoT devices.

## Overview

This simulation demonstrates a network of fixed (Access Points) and mobile (IoT devices) agents that:
1. **Discovery Phase (2s-22s)**: Agents broadcast UDP messages to discover neighbors within range
2. **Collaboration Phase (25s-95s)**: Discovered agents establish peer-to-peer communication channels

## Features

- WiFi 802.11n network simulation
- Fixed agents (infrastructure APs) with constant positions
- Mobile agents with RandomWalk2dMobilityModel
- NetAnim/NetSimulyzer visualization support
- PCAP tracing capability

## Requirements

- NS-3 (3.45 or 3.46)
- Python 3.11+
- Qt5 (for NetAnim visualization)

## Usage

```bash
# Run the simulation
cd ns-3.45
./ns3 run scenarios/discovery_collab_simulation.py

# With custom parameters
./ns3 run scenarios/discovery_collab_simulation.py -- --numFixed=4 --numMobile=8 --simTime=200

# Enable PCAP tracing
./ns3 run scenarios/discovery_collab_simulation.py -- --pcap
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--numFixed` | 2 | Number of fixed nodes (APs) |
| `--numMobile` | 4 | Number of mobile nodes |
| `--simTime` | 100 | Simulation time (seconds) |
| `--distance` | 50 | Distance between fixed nodes (meters) |
| `--pcap` | false | Enable PCAP tracing |
| `--verbose` | true | Enable verbose logging |

## Visualization

After running the simulation, open the generated animation file with NetAnim:

```bash
./netanim/build/netanim discovery-collab-animation.xml
```

- 🔴 **Red nodes**: Fixed APs (stationary)
- 🔵 **Blue nodes**: Mobile IoT devices

## Protocol Design

See [NS-3-Network-Simulation:Discovery-and-Collaboration-Protocol.pdf](docs/NS-3-Network-Simulation:Discovery-and-Collaboration-Protocol.pdf) for detailed protocol specification.

## Structure

```
├── scenarios/
│   └── discovery_collab_simulation.py   # Main simulation script
├── docs/
│   └── NS-3-Network-Simulation:Discovery-and-Collaboration-Protocol.pdf
└── README.md
```

## License

MIT License
