"""
Collaboration Phase Manager

Manages TCP-based peer-to-peer collaboration between discovered neighbors.
"""

from typing import TYPE_CHECKING, Dict, List, Tuple

if TYPE_CHECKING:
    from ..core.config import SimulationConfig
    from ..nodes.manager import NodeManager

try:
    from ns import ns
except ModuleNotFoundError:
    raise SystemExit("NS-3 Python bindings not found")

from ..core.constants import COLLABORATION_PACKET_SIZE
from ..core.exceptions import ProtocolError


class CollaborationPhaseManager:
    """Manages collaboration phase with TCP peer-to-peer communication.
    
    Discovered neighbors establish TCP connections and exchange data
    continuously during the collaboration phase.
    
    Attributes:
        config (SimulationConfig): Simulation configuration
        node_manager (NodeManager): Node manager instance
        collab_servers (ns.ApplicationContainer): TCP server applications
        collab_clients (ns.ApplicationContainer): TCP client applications
    """

    def __init__(self, config: "SimulationConfig", node_manager: "NodeManager") -> None:
        """Initialize collaboration phase manager.
        
        Args:
            config: Simulation configuration
            node_manager: Node manager with created nodes
        """
        self.config = config
        self.node_manager = node_manager
        self.collab_servers = ns.ApplicationContainer()
        self.collab_clients = ns.ApplicationContainer()

    def setup_collaboration_phase(
        self,
        fixed_interfaces: "ns.Ipv4InterfaceContainer",
        mobile_interfaces: "ns.Ipv4InterfaceContainer"
    ) -> None:
        """Setup collaboration phase based on discovered neighbors.
        
        Args:
            fixed_interfaces: IPv4 interfaces for fixed nodes
            mobile_interfaces: IPv4 interfaces for mobile nodes
            
        Raises:
            ProtocolError: If collaboration setup fails
        """
        try:
            print(f"{'='*70}")
            print("PHASE 2: COLLABORATION")
            print(f"{'='*70}")
            print("Setting up collaboration servers on all nodes:")

            # Setup TCP servers on all nodes
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

            # Setup peer-to-peer connections
            self._setup_collab_connections(fixed_interfaces, mobile_interfaces)

            print(f"\nCollaboration phase: {self.config.collab_start}s to " +
                  f"{self.config.collab_start + self.config.collab_duration}s")
            print(f"{'='*70}\n")
            
        except Exception as e:
            raise ProtocolError(f"Collaboration phase setup failed: {e}")

    def _create_collab_server(
        self,
        node: "ns.Node",
        port: int,
        address: "ns.Ipv4Address",
        name: str
    ) -> None:
        """Create TCP server for collaboration on a node.
        
        Args:
            node: NS-3 node to install server on
            port: TCP port number
            address: IPv4 address of the node  
            name: Human-readable node name for logging
        """
        local_address = ns.InetSocketAddress(ns.Ipv4Address.GetAny(), port)
        server = ns.PacketSinkHelper("ns3::TcpSocketFactory", local_address.ConvertTo())
        
        server_app = server.Install(node)
        server_app.Start(ns.Seconds(self.config.collab_start))
        server_app.Stop(ns.Seconds(self.config.collab_start +
                                   self.config.collab_duration))
        self.collab_servers.Add(server_app)
        print(f"  {name}: Collaboration TCP server at {address}:{port}")

    def _setup_collab_connections(
        self,
        fixed_interfaces: "ns.Ipv4InterfaceContainer",
        mobile_interfaces: "ns.Ipv4InterfaceContainer"
    ) -> None:
        """Setup peer-to-peer collaboration connections between neighbors."""
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

    def _find_neighbors(self) -> Dict[Tuple[str, int], List[Tuple[int, str]]]:
        """Simulate neighbor discovery based on distance.
        
        Returns:
            Dictionary mapping (node_type, node_id) to list of (neighbor_id, neighbor_type)
        """
        neighbors = {}

        # For fixed nodes
        for i in range(self.config.num_fixed_nodes):
            neighbors[('fixed', i)] = []
            # Connect to adjacent fixed nodes
            for j in range(self.config.num_fixed_nodes):
                if i != j and abs(i - j) <= 1:
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

    def _create_collab_client(
        self,
        node: "ns.Node",
        target_addr: "ns.Ipv4Address",
        target_port: int,
        start_time: float,
        source_name: str,
        target_name: str
    ) -> None:
        """Create TCP client for collaboration.
        
        Args:
            node: NS-3 node to install client on
            target_addr: Target IPv4 address
            target_port: Target TCP port
            start_time: Time to start sending
            source_name: Source node name for logging
            target_name: Target node name for logging
        """
        address = ns.InetSocketAddress(target_addr, target_port)
        client = ns.OnOffHelper("ns3::TcpSocketFactory", address.ConvertTo())
        
        # Configure traffic: 8kbps constant
        client.SetAttribute("DataRate", ns.StringValue("8192bps"))
        client.SetAttribute("PacketSize", ns.UintegerValue(COLLABORATION_PACKET_SIZE))
        client.SetAttribute("OnTime", ns.StringValue("ns3::ConstantRandomVariable[Constant=1]"))
        client.SetAttribute("OffTime", ns.StringValue("ns3::ConstantRandomVariable[Constant=0]"))

        client_app = client.Install(node)
        client_app.Start(ns.Seconds(start_time))
        client_app.Stop(ns.Seconds(self.config.collab_start +
                                   self.config.collab_duration))
        self.collab_clients.Add(client_app)
        print(f"  {source_name} (TCP) → {target_name}")
