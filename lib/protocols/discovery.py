"""
Discovery Phase Manager

Manages UDP broadcast-based neighbor discovery phase.
"""

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from ..core.config import SimulationConfig
    from ..nodes.manager import NodeManager

try:
    from ns import ns
except ModuleNotFoundError:
    raise SystemExit("NS-3 Python bindings not found")

from ..core.constants import DISCOVERY_PACKET_SIZE
from ..core.exceptions import ProtocolError


class DiscoveryPhaseManager:
    """Manages discovery phase where nodes broadcast to find neighbors.
    
    All nodes run UDP echo servers and broadcast discovery messages to
    identify nearby neighbors within radio range.
    
    Attributes:
        config (SimulationConfig): Simulation configuration
        node_manager (NodeManager): Node manager instance
        discovery_servers (ns.ApplicationContainer): UDP server applications
        discovery_clients (ns.ApplicationContainer): UDP client applications
    """

    def __init__(self, config: "SimulationConfig", node_manager: "NodeManager") -> None:
        """Initialize discovery phase manager.
        
        Args:
            config: Simulation configuration
            node_manager: Node manager with created nodes
        """
        self.config = config
        self.node_manager = node_manager
        self.discovery_servers = ns.ApplicationContainer()
        self.discovery_clients = ns.ApplicationContainer()

    def setup_discovery_phase(
        self,
        fixed_interfaces: "ns.Ipv4InterfaceContainer",
        mobile_interfaces: "ns.Ipv4InterfaceContainer"
    ) -> None:
        """Setup discovery phase for all nodes.
        
        Configures UDP echo servers on all nodes and broadcast clients
        to send discovery messages.
        
        Args:
            fixed_interfaces: IPv4 interfaces for fixed nodes
            mobile_interfaces: IPv4 interfaces for mobile nodes
            
        Raises:
            ProtocolError: If discovery setup fails
        """
        try:
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
            
        except Exception as e:
            raise ProtocolError(f"Discovery phase setup failed: {e}")

    def _create_discovery_server(
        self,
        node: "ns.Node",
        name: str,
        address: "ns.Ipv4Address"
    ) -> None:
        """Create UDP echo server for discovery on a node.
        
        Args:
            node: NS-3 node to install server on
            name: Human-readable node name for logging
            address: IPv4 address of the node
        """
        server = ns.UdpEchoServerHelper(self.config.discovery_port)
        server_app = server.Install(node)
        server_app.Start(ns.Seconds(self.config.discovery_start))
        server_app.Stop(ns.Seconds(self.config.discovery_start +
                                   self.config.discovery_duration))
        self.discovery_servers.Add(server_app)
        print(f"  {name}: Discovery server at {address}:{self.config.discovery_port}")

    def _create_discovery_client(
        self,
        node: "ns.Node",
        all_addresses: List["ns.Ipv4Address"],
        start_time: float,
        name: str
    ) -> None:
        """Create UDP broadcast client for discovery.
        
        Args:
            node: NS-3 node to install client on
            all_addresses: List of all node addresses (for reference)
            start_time: Time to start broadcasting
            name: Human-readable node name for logging
        """
        # Broadcast to subnet broadcast address
        broadcast_addr = ns.Ipv4Address("10.1.1.255")
        remote_address = ns.InetSocketAddress(broadcast_addr, self.config.discovery_port)

        client = ns.UdpEchoClientHelper(remote_address.ConvertTo())
        client.SetAttribute("MaxPackets",
                           ns.UintegerValue(int(self.config.discovery_duration /
                                                self.config.discovery_interval)))
        client.SetAttribute("Interval",
                           ns.TimeValue(ns.Seconds(self.config.discovery_interval)))
        client.SetAttribute("PacketSize", ns.UintegerValue(DISCOVERY_PACKET_SIZE))

        client_app = client.Install(node)
        client_app.Start(ns.Seconds(start_time))
        client_app.Stop(ns.Seconds(self.config.discovery_start +
                                   self.config.discovery_duration))
        self.discovery_clients.Add(client_app)
        print(f"  {name}: Broadcasting discovery messages")
