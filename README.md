# IoT Simulation - Discovery and Collaboration Protocol

NS-3 simulation implementing a two-phase Discovery and Collaboration protocol for Mobile IoT devices with comprehensive feature extraction for security research.

## Overview

This simulation demonstrates a network of fixed (Access Points) and mobile (IoT devices) agents that:
1. **Discovery Phase (2s-22s)**: Agents broadcast UDP messages to discover neighbors within range
2. **Collaboration Phase (25s-95s)**: Discovered agents establish peer-to-peer TCP communication channels

## Features

- WiFi 802.11n network simulation
- Fixed agents (infrastructure APs) with constant positions
- Mobile agents with RandomWalk2dMobilityModel
- **Dual-protocol implementation**: UDP (Discovery) + TCP (Collaboration)
- **Comprehensive dataset generation** with network flow and mobility-specific features
- NetAnim/NetSimulyzer visualization support
- PCAP tracing capability

## Dataset Features

The simulation generates a CSV file (`simulation_features.csv`) with the following metrics:

### Network Flow Features
- **FlowID**: Unique identifier for each network flow
- **SourceIP, DestIP**: IPv4 addresses of communicating nodes
- **Protocol**: Transport protocol (UDP or TCP)
- **Duration**: Flow duration in seconds
- **TxPackets, RxPackets**: Transmitted and received packet counts
- **TxBytes, RxBytes**: Transmitted and received byte counts
- **MeanDelay**: Average packet delay (seconds)
- **MeanJitter**: Average jitter between packets (seconds)
- **LostPackets**: Number of lost packets
- **Throughput_Kbps**: Flow throughput in kilobits per second

### Mobility-Specific Features
- **AvgNodeSpeed_mps**: Average node speed in meters per second (planned)
- **DistToAP_meters**: Distance to nearest access point (planned)
- **AvgNodeDensity**: Average number of neighbors within discovery range (80m) - **Novel contribution**

## Requirements

- NS-3 (3.45 or later)
- Python 3.11+
- Qt5 (for NetAnim visualization)

## Usage

```bash
# Navigate to NS-3 installation
cd /media/hambz/Elements/simulation/ns-allinone-3.45/ns-3.45

# Activate virtual environment
source .venv/bin/activate

# Run the simulation
./ns3 run "scenarios/discovery_collab_simulation.py"

# With custom parameters (recommended: simTime >= 35s to capture collaboration phase)
./ns3 run "scenarios/discovery_collab_simulation.py -- --numFixed=2 --numMobile=4 --simTime=100"

# Enable PCAP tracing
./ns3 run "scenarios/discovery_collab_simulation.py -- --pcap"
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--numFixed` | 2 | Number of fixed nodes (APs) |
| `--numMobile` | 4 | Number of mobile nodes |
| `--simTime` | 100 | Simulation time (seconds) - **min 35s for full protocol** |
| `--distance` | 50 | Distance between fixed nodes (meters) |
| `--pcap` | false | Enable PCAP tracing |
| `--verbose` | true | Enable verbose logging |

## Visualization

After running the simulation, open the generated animation file with NetAnim:

```bash
/media/hambz/Elements/simulation/ns-allinone-3.45/netanim/build/netanim discovery-collab-animation.xml
```

- 🔴 **Red nodes**: Fixed APs (stationary)
- 🔵 **Blue nodes**: Mobile IoT devices

## Protocol Design

See [NS-3-Network-Simulation:Discovery-and-Collaboration-Protocol.pdf](docs/NS-3-Network-Simulation:Discovery-and-Collaboration-Protocol.pdf) for detailed protocol specification.

### Phase 1: Discovery (UDP)
- Port: 8000
- Broadcast interval: 2 seconds
- Range: 80 meters

### Phase 2: Collaboration (TCP)
- Ports: 9000+ (unique per node)
- Peer-to-peer connections based on discovery results
- Continuous data exchange

## Output Files

- `simulation_features.csv`: Dataset with all collected metrics
- `discovery-collab-animation.xml`: NetAnim visualization file
- `*.pcap`: Packet capture files (if enabled)

## Research Application

This simulation is designed for **Mobile IoT Security Research**, specifically:
- Intrusion Detection System (IDS) development
- DDoS attack detection in mobile environments
- Machine Learning model training with mobility-aware features
- Federated Learning datasets with realistic network behavior

**Key Innovation**: Node Density metric captures the unique characteristic of mobile IoT networks where neighbor relationships change dynamically.

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

