#!/usr/bin/env python3
"""
NS-3 Simulation: Fixed and Mobile Agents with Discovery and Collaboration
Compatible with NS-3.45/NS-3.46

This modular simulation demonstrates:
- Discovery Phase: Agents broadcast to discover nearby neighbors
- Collaboration Phase: Discovered agents establish connections and communicate
- Both fixed and mobile agents perform both phases

Visualization: Uses NetSimulyzer (3D) if available, falls back to NetAnim (2D)
"""

import sys
import csv
from datetime import datetime

# Fixed import statement
try:
    from ns import ns
except ModuleNotFoundError:
    raise SystemExit(
        "Error: ns3 Python module not found;"
        " Python bindings may not be enabled"
        " or your PYTHONPATH might not be properly configured"
    )


class SimulationConfig:
    """Configuration parameters for the simulation"""

    def __init__(self):
        self.num_fixed_nodes = 2
        self.num_mobile_nodes = 4
        self.sim_time = 100.0
        self.distance = 50.0
        self.enable_pcap = False
        self.verbose = True

        # Phase timings
        self.discovery_start = 2.0
        self.discovery_duration = 20.0
        self.collab_start = 25.0
        self.collab_duration = 70.0

        # Port configuration
        self.discovery_port = 8000
        self.collab_base_port = 9000

        # Discovery parameters
        self.discovery_range = 80.0  # meters
        self.discovery_interval = 2.0  # seconds

        # Network configuration
        self.network_base = "10.1.1.0"
        self.network_mask = "255.255.255.0"

    def parse_arguments(self, argv):
        """Parse command line arguments using argparse (NS-3 Python bindings compatible)"""
        import argparse
        parser = argparse.ArgumentParser(
            description='NS-3 Discovery and Collaboration Simulation',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        parser.add_argument('--numFixed', type=int, default=self.num_fixed_nodes,
                          help='Number of fixed nodes')
        parser.add_argument('--numMobile', type=int, default=self.num_mobile_nodes,
                          help='Number of mobile nodes')
        parser.add_argument('--simTime', type=float, default=self.sim_time,
                          help='Simulation time in seconds')
        parser.add_argument('--distance', type=float, default=self.distance,
                          help='Distance between fixed nodes')
        parser.add_argument('--pcap', action='store_true', default=self.enable_pcap,
                          help='Enable PCAP tracing')
        parser.add_argument('--verbose', action='store_true', default=self.verbose,
                          help='Enable verbose logging')
        parser.add_argument('--discoveryDuration', type=float, default=self.discovery_duration,
                          help='Discovery phase duration')
        parser.add_argument('--collabDuration', type=float, default=self.collab_duration,
                          help='Collaboration phase duration')
        
        args = parser.parse_args(argv[1:])
        
        self.num_fixed_nodes = args.numFixed
        self.num_mobile_nodes = args.numMobile
        self.sim_time = args.simTime
        self.distance = args.distance
        self.enable_pcap = args.pcap
        self.verbose = args.verbose
        self.discovery_duration = args.discoveryDuration
        self.collab_duration = args.collabDuration

    def enable_logging(self):
        """Enable NS-3 logging components"""
        if self.verbose:
            ns.LogComponentEnable("UdpEchoClientApplication", ns.LOG_LEVEL_INFO)
            ns.LogComponentEnable("UdpEchoServerApplication", ns.LOG_LEVEL_INFO)

    def print_summary(self):
        """Print simulation configuration summary"""
        print(f"\n{'='*70}")
        print(f"NS-3 Discovery and Collaboration Simulation")
        print(f"{'='*70}")
        print(f"Fixed nodes: {self.num_fixed_nodes}")
        print(f"Mobile nodes: {self.num_mobile_nodes}")
        print(f"Total simulation time: {self.sim_time}s")
        print(f"\nPhase Timeline:")
        print(f"  Discovery Phase: {self.discovery_start}s - {self.discovery_start + self.discovery_duration}s")
        print(f"  Collaboration Phase: {self.collab_start}s - {self.collab_start + self.collab_duration}s")
        print(f"\nDiscovery range: {self.discovery_range}m")
        print(f"{'='*70}\n")


class NodeManager:
    """Manages node creation and organization"""

    def __init__(self, config: SimulationConfig):
        self.config = config
        self.fixed_nodes = ns.NodeContainer()
        self.mobile_nodes = ns.NodeContainer()
        self.all_nodes = ns.NodeContainer()

    def create_nodes(self):
        """Create fixed and mobile nodes"""
        self.fixed_nodes.Create(self.config.num_fixed_nodes)
        self.mobile_nodes.Create(self.config.num_mobile_nodes)

        self.all_nodes.Add(self.fixed_nodes)
        self.all_nodes.Add(self.mobile_nodes)

        print(f"Created {self.config.num_fixed_nodes} fixed nodes")
        print(f"Created {self.config.num_mobile_nodes} mobile nodes\n")

    def get_fixed_nodes(self):
        return self.fixed_nodes

    def get_mobile_nodes(self):
        return self.mobile_nodes

    def get_all_nodes(self):
        return self.all_nodes


class NetworkConfigurator:
    """Configures WiFi network and devices"""

    def __init__(self, config: SimulationConfig, node_manager: NodeManager):
        self.config = config
        self.node_manager = node_manager
        self.fixed_devices = None
        self.mobile_devices = None

    def setup_wifi(self):
        """Configure WiFi network"""
        wifi = ns.WifiHelper()
        wifi.SetStandard(ns.WIFI_STANDARD_80211n)

        wifi_phy = ns.YansWifiPhyHelper()
        wifi_channel = ns.YansWifiChannelHelper.Default()
        wifi_phy.SetChannel(wifi_channel.Create())

        wifi_mac = ns.WifiMacHelper()
        ssid = ns.Ssid("discovery-collab-network")

        # Fixed nodes as Access Points
        wifi_mac.SetType("ns3::ApWifiMac",
                        "Ssid", ns.SsidValue(ssid))
        self.fixed_devices = wifi.Install(wifi_phy, wifi_mac,
                                         self.node_manager.get_fixed_nodes())

        # Mobile nodes as Stations
        wifi_mac.SetType("ns3::StaWifiMac",
                        "Ssid", ns.SsidValue(ssid),
                        "ActiveProbing", ns.BooleanValue(False))
        self.mobile_devices = wifi.Install(wifi_phy, wifi_mac,
                                          self.node_manager.get_mobile_nodes())

        print("WiFi network configured (802.11n)")
        return wifi_phy

    def get_devices(self):
        return self.fixed_devices, self.mobile_devices


class MobilityConfigurator:
    """Configures mobility models for nodes"""

    def __init__(self, config: SimulationConfig, node_manager: NodeManager):
        self.config = config
        self.node_manager = node_manager

    def setup_fixed_mobility(self):
        """Configure stationary positions for fixed nodes"""
        fixed_mobility = ns.MobilityHelper()
        position_alloc = ns.ListPositionAllocator()

        for i in range(self.config.num_fixed_nodes):
            position_alloc.Add(ns.Vector(i * self.config.distance, 0.0, 0.0))

        fixed_mobility.SetPositionAllocator(position_alloc)
        fixed_mobility.SetMobilityModel("ns3::ConstantPositionMobilityModel")
        fixed_mobility.Install(self.node_manager.get_fixed_nodes())

        print("Fixed nodes: Stationary positions configured")

    def setup_mobile_mobility(self):
        """Configure random walk mobility for mobile nodes"""
        mobile_mobility = ns.MobilityHelper()

        # Create position allocator - constrained to avoid propagation delay overflow
        mobile_position = ns.RandomRectanglePositionAllocator()

        # Mobile nodes: Use ListPositionAllocator with explicit positions to avoid overlap
        mobile_position = ns.ListPositionAllocator()
        
        # Set distinct starting positions for each mobile node (avoiding fixed node positions)
        # Fixed nodes are at (0,0) and (50,0), so place mobiles away from these
        mobile_positions = [
            (15.0, 20.0, 0.0),   # Mobile-0
            (35.0, 25.0, 0.0),   # Mobile-1
            (55.0, 15.0, 0.0),   # Mobile-2
            (25.0, 35.0, 0.0),   # Mobile-3
        ]
        
        for i in range(min(len(mobile_positions), self.node_manager.get_mobile_nodes().GetN())):
            x, y, z = mobile_positions[i]
            mobile_position.Add(ns.Vector(x, y, z))
        
        # If more mobile nodes than predefined positions, add with offset
        num_mobile = self.node_manager.get_mobile_nodes().GetN()
        for i in range(len(mobile_positions), num_mobile):
            x = 20.0 + (i * 10.0)
            y = 20.0 + ((i % 3) * 8.0)
            mobile_position.Add(ns.Vector(x, y, 0.0))
        
        mobile_mobility.SetPositionAllocator(mobile_position)

        mobile_mobility.SetMobilityModel("ns3::RandomWalk2dMobilityModel",
                                        "Bounds", ns.RectangleValue(
                                            ns.Rectangle(0, 80, 0, 50)),
                                        "Speed", ns.StringValue(
                                            "ns3::UniformRandomVariable[Min=1.0|Max=5.0]"),
                                        "Distance", ns.DoubleValue(15.0))
        mobile_mobility.Install(self.node_manager.get_mobile_nodes())

        print("Mobile nodes: Random walk mobility configured\n")


class NetworkStackConfigurator:
    """Configures Internet stack and IP addressing"""

    def __init__(self, config: SimulationConfig, node_manager: NodeManager):
        self.config = config
        self.node_manager = node_manager
        self.fixed_interfaces = None
        self.mobile_interfaces = None

    def install_internet_stack(self):
        """Install Internet protocol stack on all nodes"""
        internet = ns.InternetStackHelper()
        internet.Install(self.node_manager.get_all_nodes())
        print("Internet stack installed on all nodes")

    def assign_ip_addresses(self, fixed_devices, mobile_devices):
        """Assign IP addresses to devices"""
        address = ns.Ipv4AddressHelper()
        address.SetBase(ns.Ipv4Address(self.config.network_base),
                       ns.Ipv4Mask(self.config.network_mask))

        self.fixed_interfaces = address.Assign(fixed_devices)
        self.mobile_interfaces = address.Assign(mobile_devices)

        print("IP addresses assigned\n")

        return self.fixed_interfaces, self.mobile_interfaces


class DiscoveryPhaseManager:
    """Manages the discovery phase where agents broadcast to find neighbors"""

    def __init__(self, config: SimulationConfig, node_manager: NodeManager):
        self.config = config
        self.node_manager = node_manager
        self.discovery_servers = ns.ApplicationContainer()
        self.discovery_clients = ns.ApplicationContainer()

    def setup_discovery_phase(self, fixed_interfaces, mobile_interfaces):
        """Setup discovery phase for all nodes"""
        print(f"{'='*70}")
        print("PHASE 1: DISCOVERY")
        print(f"{'='*70}")
        print("Setting up discovery broadcast servers on all nodes:")

        # All nodes run discovery servers
        for i in range(self.config.num_fixed_nodes):
            node = self.node_manager.get_fixed_nodes().Get(i)
            addr = fixed_interfaces.GetAddress(i)
            self._create_discovery_server(node, f"Fixed-{i}", addr)

        for i in range(self.config.num_mobile_nodes):
            node = self.node_manager.get_mobile_nodes().Get(i)
            addr = mobile_interfaces.GetAddress(i)
            self._create_discovery_server(node, f"Mobile-{i}", addr)

        print("\nSetting up discovery broadcast clients on all nodes:")

        # All nodes broadcast discovery messages
        all_addresses = []
        for i in range(self.config.num_fixed_nodes):
            all_addresses.append(fixed_interfaces.GetAddress(i))
        for i in range(self.config.num_mobile_nodes):
            all_addresses.append(mobile_interfaces.GetAddress(i))

        # Fixed nodes discover
        for i in range(self.config.num_fixed_nodes):
            node = self.node_manager.get_fixed_nodes().Get(i)
            self._create_discovery_client(node, all_addresses,
                                         self.config.discovery_start + i * 0.2,
                                         f"Fixed-{i}")

        # Mobile nodes discover
        for i in range(self.config.num_mobile_nodes):
            node = self.node_manager.get_mobile_nodes().Get(i)
            self._create_discovery_client(node, all_addresses,
                                         self.config.discovery_start +
                                         (self.config.num_fixed_nodes + i) * 0.2,
                                         f"Mobile-{i}")

        print(f"\nDiscovery phase: {self.config.discovery_start}s to " +
              f"{self.config.discovery_start + self.config.discovery_duration}s")
        print(f"{'='*70}\n")

    def _create_discovery_server(self, node, name, address):
        """Create discovery server on a node"""
        server = ns.UdpEchoServerHelper(self.config.discovery_port)
        server_app = server.Install(node)
        server_app.Start(ns.Seconds(self.config.discovery_start))
        server_app.Stop(ns.Seconds(self.config.discovery_start +
                                   self.config.discovery_duration))
        self.discovery_servers.Add(server_app)
        print(f"  {name}: Discovery server at {address}:{self.config.discovery_port}")

    def _create_discovery_client(self, node, all_addresses, start_time, name):
        """Create discovery client that broadcasts"""
        # For simplicity, we broadcast to the subnet broadcast address
        broadcast_addr = ns.Ipv4Address("10.1.1.255")

        # Convert Ipv4Address to InetSocketAddress
        remote_address = ns.InetSocketAddress(broadcast_addr, self.config.discovery_port)

        client = ns.UdpEchoClientHelper(remote_address.ConvertTo())
        client.SetAttribute("MaxPackets",
                           ns.UintegerValue(int(self.config.discovery_duration /
                                                self.config.discovery_interval)))
        client.SetAttribute("Interval",
                           ns.TimeValue(ns.Seconds(self.config.discovery_interval)))
        client.SetAttribute("PacketSize", ns.UintegerValue(128))

        client_app = client.Install(node)
        client_app.Start(ns.Seconds(start_time))
        client_app.Stop(ns.Seconds(self.config.discovery_start +
                                   self.config.discovery_duration))
        self.discovery_clients.Add(client_app)
        print(f"  {name}: Broadcasting discovery messages")


class CollaborationPhaseManager:
    """Manages the collaboration phase where discovered agents communicate"""

    def __init__(self, config: SimulationConfig, node_manager: NodeManager):
        self.config = config
        self.node_manager = node_manager
        self.collab_servers = ns.ApplicationContainer()
        self.collab_clients = ns.ApplicationContainer()

    def setup_collaboration_phase(self, fixed_interfaces, mobile_interfaces):
        """Setup collaboration phase based on discovered neighbors"""
        print(f"{'='*70}")
        print("PHASE 2: COLLABORATION")
        print(f"{'='*70}")
        print("Setting up collaboration servers on all nodes:")

        # Setup collaboration servers on all nodes
        for i in range(self.config.num_fixed_nodes):
            node = self.node_manager.get_fixed_nodes().Get(i)
            addr = fixed_interfaces.GetAddress(i)
            port = self.config.collab_base_port + i
            self._create_collab_server(node, port, addr, f"Fixed-{i}")

        for i in range(self.config.num_mobile_nodes):
            node = self.node_manager.get_mobile_nodes().Get(i)
            addr = mobile_interfaces.GetAddress(i)
            port = self.config.collab_base_port + self.config.num_fixed_nodes + i
            self._create_collab_server(node, port, addr, f"Mobile-{i}")

        print("\nSetting up collaboration connections:")
        print("(Simulating discovered neighbors within range)\n")

        # Simulate discovered neighbors and create connections
        self._setup_collab_connections(fixed_interfaces, mobile_interfaces)

        print(f"\nCollaboration phase: {self.config.collab_start}s to " +
              f"{self.config.collab_start + self.config.collab_duration}s")
        print(f"{'='*70}\n")

    def _create_collab_server(self, node, port, address, name):
        """Create collaboration server on a node using TCP"""
        # Use PacketSink for TCP server
        local_address = ns.InetSocketAddress(ns.Ipv4Address.GetAny(), port)
        server = ns.PacketSinkHelper("ns3::TcpSocketFactory", local_address.ConvertTo())
        
        server_app = server.Install(node)
        server_app.Start(ns.Seconds(self.config.collab_start))
        server_app.Stop(ns.Seconds(self.config.collab_start +
                                   self.config.collab_duration))
        self.collab_servers.Add(server_app)
        print(f"  {name}: Collaboration TCP server at {address}:{port}")

    def _setup_collab_connections(self, fixed_interfaces, mobile_interfaces):
        """Setup peer-to-peer collaboration connections"""

        # Get all node positions to determine neighbors
        neighbors = self._find_neighbors()

        # Fixed nodes collaborate with discovered neighbors
        for i in range(self.config.num_fixed_nodes):
            node = self.node_manager.get_fixed_nodes().Get(i)

            for neighbor_idx, neighbor_type in neighbors.get(('fixed', i), []):
                if neighbor_type == 'fixed':
                    target_addr = fixed_interfaces.GetAddress(neighbor_idx)
                    target_port = self.config.collab_base_port + neighbor_idx
                    self._create_collab_client(node, target_addr, target_port,
                                              self.config.collab_start + i * 0.3,
                                              f"Fixed-{i}", f"Fixed-{neighbor_idx}")
                else:  # mobile
                    target_addr = mobile_interfaces.GetAddress(neighbor_idx)
                    target_port = self.config.collab_base_port + self.config.num_fixed_nodes + neighbor_idx
                    self._create_collab_client(node, target_addr, target_port,
                                              self.config.collab_start + i * 0.3,
                                              f"Fixed-{i}", f"Mobile-{neighbor_idx}")

        # Mobile nodes collaborate with discovered neighbors
        for i in range(self.config.num_mobile_nodes):
            node = self.node_manager.get_mobile_nodes().Get(i)

            for neighbor_idx, neighbor_type in neighbors.get(('mobile', i), []):
                if neighbor_type == 'fixed':
                    target_addr = fixed_interfaces.GetAddress(neighbor_idx)
                    target_port = self.config.collab_base_port + neighbor_idx
                    self._create_collab_client(node, target_addr, target_port,
                                              self.config.collab_start +
                                              (self.config.num_fixed_nodes + i) * 0.3,
                                              f"Mobile-{i}", f"Fixed-{neighbor_idx}")
                else:  # mobile
                    target_addr = mobile_interfaces.GetAddress(neighbor_idx)
                    target_port = self.config.collab_base_port + self.config.num_fixed_nodes + neighbor_idx
                    self._create_collab_client(node, target_addr, target_port,
                                              self.config.collab_start +
                                              (self.config.num_fixed_nodes + i) * 0.3,
                                              f"Mobile-{i}", f"Mobile-{neighbor_idx}")

    def _find_neighbors(self):
        """Simulate neighbor discovery based on distance"""
        neighbors = {}

        # Simple neighbor discovery: connect nodes that would be in range
        # For fixed nodes
        for i in range(self.config.num_fixed_nodes):
            neighbors[('fixed', i)] = []
            # Connect to nearby fixed nodes
            for j in range(self.config.num_fixed_nodes):
                if i != j and abs(i - j) <= 1:  # Adjacent fixed nodes
                    neighbors[('fixed', i)].append((j, 'fixed'))
            # Connect to some mobile nodes (simulating discovery)
            for j in range(min(2, self.config.num_mobile_nodes)):
                neighbors[('fixed', i)].append((j, 'mobile'))

        # For mobile nodes
        for i in range(self.config.num_mobile_nodes):
            neighbors[('mobile', i)] = []
            # Connect to fixed nodes
            fixed_neighbor = i % self.config.num_fixed_nodes
            neighbors[('mobile', i)].append((fixed_neighbor, 'fixed'))
            # Connect to other mobile nodes
            next_mobile = (i + 1) % self.config.num_mobile_nodes
            if next_mobile != i:
                neighbors[('mobile', i)].append((next_mobile, 'mobile'))

        return neighbors

    def _create_collab_client(self, node, target_addr, target_port,
                             start_time, source_name, target_name):
        """Create collaboration client connection using TCP"""
        # Use OnOffApplication for TCP client
        address = ns.InetSocketAddress(target_addr, target_port)
        client = ns.OnOffHelper("ns3::TcpSocketFactory", address.ConvertTo())
        
        # Configure traffic: 8kbps constant
        client.SetAttribute("DataRate", ns.StringValue("8192bps"))
        client.SetAttribute("PacketSize", ns.UintegerValue(1024))
        client.SetAttribute("OnTime", ns.StringValue("ns3::ConstantRandomVariable[Constant=1]"))
        client.SetAttribute("OffTime", ns.StringValue("ns3::ConstantRandomVariable[Constant=0]"))

        client_app = client.Install(node)
        client_app.Start(ns.Seconds(start_time))
        client_app.Stop(ns.Seconds(self.config.collab_start +
                                   self.config.collab_duration))
        self.collab_clients.Add(client_app)
        print(f"  {source_name} (TCP) → {target_name}")


class VisualizationManager:
    """Manages NetSimulyzer 3D visualization with NetAnim fallback"""

    def __init__(self, config: SimulationConfig, node_manager: NodeManager):
        self.config = config
        self.node_manager = node_manager
        self.orchestrator = None
        self.anim = None

    def setup_visualization(self):
        """Configure visualization - tries NetSimulyzer first, falls back to NetAnim"""
        try:
            if hasattr(ns, 'netsimulyzer'):
                self._setup_netsimulyzer()
            else:
                print("NetSimulyzer module not found, using NetAnim instead...\n")
                self._setup_netanim()
        except (AttributeError, Exception) as e:
            print(f"NetSimulyzer not available ({e}), falling back to NetAnim...\n")
            self._setup_netanim()

    def _setup_netsimulyzer(self):
        """Configure NetSimulyzer 3D visualization"""
        self.orchestrator = ns.netsimulyzer.Orchestrator("discovery-collab-visualization.json")

        # Fixed nodes - Red boxes
        for i in range(self.config.num_fixed_nodes):
            node = self.node_manager.get_fixed_nodes().Get(i)
            fixed_decoration = ns.netsimulyzer.NodeConfiguration(self.orchestrator)
            fixed_decoration.Set(node)
            fixed_decoration.SetAttribute("Model", ns.StringValue("Cube.obj"))
            fixed_decoration.SetAttribute("Scale", ns.DoubleValue(2.0))
            fixed_decoration.SetAttribute("Color",
                ns.netsimulyzer.Color3Value(ns.netsimulyzer.Color3(255, 0, 0)))
            label = ns.netsimulyzer.NodeLabel(self.orchestrator, node)
            label.SetAttribute("Text", ns.StringValue(f"Fixed-{i}"))

        # Mobile nodes - Blue spheres
        for i in range(self.config.num_mobile_nodes):
            node = self.node_manager.get_mobile_nodes().Get(i)
            mobile_decoration = ns.netsimulyzer.NodeConfiguration(self.orchestrator)
            mobile_decoration.Set(node)
            mobile_decoration.SetAttribute("Model", ns.StringValue("Sphere.obj"))
            mobile_decoration.SetAttribute("Scale", ns.DoubleValue(1.5))
            mobile_decoration.SetAttribute("Color",
                ns.netsimulyzer.Color3Value(ns.netsimulyzer.Color3(0, 0, 255)))
            label = ns.netsimulyzer.NodeLabel(self.orchestrator, node)
            label.SetAttribute("Text", ns.StringValue(f"Mobile-{i}"))

        print("NetSimulyzer 3D visualization configured")
        print("Output file: discovery-collab-visualization.json\n")

    def _setup_netanim(self):
        """Configure NetAnim 2D visualization"""
        self.anim = ns.AnimationInterface("discovery-collab-animation.xml")

        # Configure fixed nodes (red)
        for i in range(self.config.num_fixed_nodes):
            node = self.node_manager.get_fixed_nodes().Get(i)
            node_id = node.GetId()
            self.anim.UpdateNodeDescription(node, f"Fixed-{i}")
            self.anim.UpdateNodeColor(node, 255, 0, 0)
            self.anim.UpdateNodeSize(node_id, 5.0, 5.0)

        # Configure mobile nodes (blue)
        for i in range(self.config.num_mobile_nodes):
            node = self.node_manager.get_mobile_nodes().Get(i)
            node_id = node.GetId()
            self.anim.UpdateNodeDescription(node, f"Mobile-{i}")
            self.anim.UpdateNodeColor(node, 0, 0, 255)
            self.anim.UpdateNodeSize(node_id, 3.0, 3.0)

        # Add buildings/rooms as rectangles
        # Building 1: Server Room (where fixed nodes are)
        self.anim.AddResource("/media/hambz/Elements/simulation/ns-allinone-3.45/netanim/resources/icons/server.png")
        
        # You can also add rectangles directly in NetAnim by adding to the XML
        # For now, let's enable mobility updates for smoother animation
        self.anim.SetMaxPktsPerTraceFile(500000)
        self.anim.EnablePacketMetadata(True)
        # self.anim.EnableIpv4RouteTracking("routingtable-wireless.xml", 
        #                                    ns.Seconds(0), ns.Seconds(5), ns.Seconds(0.25))
        
        print("NetAnim visualization configured")
        print("Buildings and structures can be added in NetAnim:")
        print("  - File -> Add Resource (for background images)")
        print("  - Or edit the XML to add <rectangle> elements\\n")


class FeatureExtractor:
    """Extracts network features using FlowMonitor"""

    def __init__(self, config: SimulationConfig):
        self.config = config
        self.flow_monitor = None
        self.monitor_helper = None
        self.node_densities = {} # node_id -> list of neighbor counts

    def setup_flow_monitor(self, fixed_interfaces, mobile_interfaces):
        """Install FlowMonitor on all nodes"""
        self.monitor_helper = ns.FlowMonitorHelper()
        self.flow_monitor = self.monitor_helper.InstallAll()
        print("FlowMonitor feature extraction configured")

    def schedule_density_sampling(self, node_manager):
        """Schedule periodic sampling of node density"""
        # Store node_manager reference for later sampling
        self.node_manager = node_manager
        
        # Initialize storage - we'll compute density at the end instead of during simulation
        for i in range(node_manager.get_all_nodes().GetN()):
            node = node_manager.get_all_nodes().Get(i)
            self.node_densities[node.GetId()] = []
        
        print("Density will be computed post-simulation from node positions")

    def _compute_average_density_per_node(self):
        """Compute average density for each node based on final positions"""
        all_nodes = self.node_manager.get_all_nodes()
        n = all_nodes.GetN()
        
        # Calculate density based on current positions
        for i in range(n):
            node_i = all_nodes.Get(i)
            mob_i = node_i.GetObject[ns.MobilityModel]()
            
            neighbor_count = 0
            for j in range(n):
                if i == j: 
                    continue
                node_j = all_nodes.Get(j)
                mob_j = node_j.GetObject[ns.MobilityModel]()
                
                dist = mob_i.GetDistanceFrom(mob_j)
                # Using config.discovery_range as the density measurement radius
                if dist <= self.config.discovery_range:
                    neighbor_count += 1
            
            # Store single snapshot of density
            self.node_densities[node_i.GetId()].append(neighbor_count)

    def extract_features(self):
        """Extract flow statistics and save to CSV"""
        print("Extracting features (this may take a moment)...")
        
        # Compute density snapshot at end of simulation
        self._compute_average_density_per_node()
        
        self.flow_monitor.CheckForLostPackets()
        classifier = self.monitor_helper.GetClassifier()

        with open('simulation_features.csv', 'w', newline='') as csvfile:
            fieldnames = ['FlowID', 'SourceIP', 'DestIP', 'Protocol', 'Duration',
                         'TxPackets', 'RxPackets', 'TxBytes', 'RxBytes',
                         'MeanDelay', 'MeanJitter', 'LostPackets', 'Throughput_Kbps',
                         'AvgNodeSpeed_mps', 'DistToAP_meters', 'AvgNodeDensity']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for flow_id, flow_stats in self.flow_monitor.GetFlowStats():
                t = classifier.FindFlow(flow_id)
                proto = {6: 'TCP', 17: 'UDP'}.get(t.protocol, str(t.protocol))
                
                source_addr = t.sourceAddress
                dest_addr = t.destinationAddress

                # Avoid exporting flows with no packets
                if flow_stats.txPackets == 0:
                    continue

                duration = flow_stats.timeLastRxPacket.GetSeconds() - flow_stats.timeFirstTxPacket.GetSeconds()
                if duration <= 0:
                    duration = 1.0 

                throughput = (flow_stats.rxBytes * 8.0) / duration / 1000.0 if duration > 0 else 0

                # Calculate Average Density for the source node
                # Note: We need to map IP to Node ID to find the correct density stats
                # This is tricky with just FlowClassifier.
                # Heuristic: We won't map perfectly in this simplified block without an IP-NodeID map.
                # However, we can map sequentially if we know the IP assignment logic.
                # Fixed: 10.1.1.1, .2
                # Mobile: 10.1.1.3, .4, .5, .6
                
                # Simple parsing of last octet to estimate node ID (0-based)
                # Network Base is 10.1.1.0. IPs start at 1.
                # Node 0 (Fixed-0) -> 10.1.1.1
                # Node 1 (Fixed-1) -> 10.1.1.2
                # Node 2 (Mobile-0) -> 10.1.1.3
                
                avg_density = "N/A"
                try:
                    # Convert source address string "10.1.1.X" to int X
                    # This relies on standard string representation
                    ip_str = str(source_addr)
                    if ip_str.startswith("10.1.1."):
                        octet = int(ip_str.split('.')[-1])
                        # Assuming sequential assignment starting at 1 for Node 0
                        node_id = octet - 1
                        if node_id in self.node_densities:
                            counts = self.node_densities[node_id]
                            if counts:
                                avg_density = f"{sum(counts) / len(counts):.2f}"
                except Exception:
                    pass

                writer.writerow({
                    'FlowID': flow_id,
                    'SourceIP': source_addr,
                    'DestIP': dest_addr,
                    'Protocol': proto,
                    'Duration': f"{duration:.4f}",
                    'TxPackets': flow_stats.txPackets,
                    'RxPackets': flow_stats.rxPackets,
                    'TxBytes': flow_stats.txBytes,
                    'RxBytes': flow_stats.rxBytes,
                    'MeanDelay': f"{flow_stats.delaySum.GetSeconds() / flow_stats.rxPackets if flow_stats.rxPackets > 0 else 0:.6f}",
                    'MeanJitter': f"{flow_stats.jitterSum.GetSeconds() / (flow_stats.rxPackets - 1) if flow_stats.rxPackets > 1 else 0:.6f}",
                    'LostPackets': flow_stats.lostPackets,
                    'Throughput_Kbps': f"{throughput:.2f}",
                    'AvgNodeSpeed_mps': "N/A",
                    'DistToAP_meters': "N/A",
                    'AvgNodeDensity': avg_density
                })
        
        print(f"Features saved to 'simulation_features.csv'")

    def setup_mobility_tracing(self, node_manager):
        """Setup mobility tracing"""
        # This function would attach to CourseChange triggers to log X,Y,Z over time
        # For now, we'll rely on the existing visualization traces or FlowMonitor
        pass


class Simulation:
    """Main simulation orchestrator"""

    def __init__(self):
        self.config = SimulationConfig()
        self.node_manager = None
        self.network_config = None
        self.mobility_config = None
        self.stack_config = None
        self.discovery_manager = None
        self.collab_manager = None
        self.collab_manager = None
        self.viz_manager = None
        self.feature_extractor = None

    def initialize(self, argv):
        """Initialize simulation components"""
        self.config.parse_arguments(argv)
        self.config.enable_logging()
        self.config.print_summary()

        # Create managers
        self.node_manager = NodeManager(self.config)
        self.network_config = NetworkConfigurator(self.config, self.node_manager)
        self.mobility_config = MobilityConfigurator(self.config, self.node_manager)
        self.stack_config = NetworkStackConfigurator(self.config, self.node_manager)
        self.discovery_manager = DiscoveryPhaseManager(self.config, self.node_manager)
        self.collab_manager = CollaborationPhaseManager(self.config, self.node_manager)
        self.viz_manager = VisualizationManager(self.config, self.node_manager)
        self.feature_extractor = FeatureExtractor(self.config)

    def setup(self):
        """Setup all simulation components"""
        # Create nodes
        self.node_manager.create_nodes()

        # Configure network
        wifi_phy = self.network_config.setup_wifi()
        fixed_devices, mobile_devices = self.network_config.get_devices()

        # Configure mobility
        self.mobility_config.setup_fixed_mobility()
        self.mobility_config.setup_mobile_mobility()

        # Install Internet stack and assign IPs
        self.stack_config.install_internet_stack()
        fixed_intf, mobile_intf = self.stack_config.assign_ip_addresses(
            fixed_devices, mobile_devices)

        # Setup discovery phase
        self.discovery_manager.setup_discovery_phase(fixed_intf, mobile_intf)

        # Setup collaboration phase
        self.collab_manager.setup_collaboration_phase(fixed_intf, mobile_intf)

        # Enable routing
        ns.Ipv4GlobalRoutingHelper.PopulateRoutingTables()

        # Enable PCAP if requested
        if self.config.enable_pcap:
            wifi_phy.EnablePcapAll("discovery-collab-simulation")
            print("PCAP tracing enabled\n")

        # Setup visualization
        self.viz_manager.setup_visualization()

        # Setup feature extraction
        self.feature_extractor.setup_flow_monitor(fixed_intf, mobile_intf)
        self.feature_extractor.setup_mobility_tracing(self.node_manager)
        self.feature_extractor.schedule_density_sampling(self.node_manager)

    def run(self):
        """Run the simulation"""
        print(f"{'='*70}")
        print("Starting simulation...")
        print(f"{'='*70}\n")

        ns.Simulator.Stop(ns.Seconds(self.config.sim_time))
        ns.Simulator.Run()

        # Extract and save features
        self.feature_extractor.extract_features()
        print(f"\n{'='*70}")
        print("Simulation completed successfully!")
        print(f"{'='*70}\n")

        ns.Simulator.Destroy()


def main(argv):
    """Main entry point"""
    simulation = Simulation()
    simulation.initialize(argv)
    simulation.setup()
    simulation.run()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
