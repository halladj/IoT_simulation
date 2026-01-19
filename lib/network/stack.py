"""
Network Stack Configurator

Configures Internet protocol stack and IP addressing.
"""

from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from ..core.config import SimulationConfig
    from ..nodes.manager import NodeManager

try:
    from ns import ns
except ModuleNotFoundError:
    raise SystemExit("NS-3 Python bindings not found")

from ..core.exceptions import NetworkSetupError


class NetworkStackConfigurator:
    """Configures Internet stack and IPv4 addressing.
    
    Installs the Internet protocol stack on all nodes and assigns
    IPv4 addresses from the configured network range.
    
    Attributes:
        config (SimulationConfig): Simulation configuration
        node_manager (NodeManager): Node manager instance
        fixed_interfaces (ns.Ipv4InterfaceContainer): IPv4 interfaces for fixed nodes
        mobile_interfaces (ns.Ipv4InterfaceContainer): IPv4 interfaces for mobile nodes
    """

    def __init__(self, config: "SimulationConfig", node_manager: "NodeManager") -> None:
        """Initialize network stack configurator.
        
        Args:
            config: Simulation configuration
            node_manager: Node manager with created nodes
        """
        self.config = config
        self.node_manager = node_manager
        self.fixed_interfaces = None
        self.mobile_interfaces = None

    def install_internet_stack(self) -> None:
        """Install Internet protocol stack on all nodes.
        
        Installs TCP/IP stack including IPv4, ARP, ICMP, UDP, and TCP.
        
        Raises:
            NetworkSetupError: If stack installation fails
        """
        try:
            internet = ns.InternetStackHelper()
            internet.Install(self.node_manager.get_all_nodes())
            print("Internet stack installed on all nodes")
        except Exception as e:
            raise NetworkSetupError(f"Internet stack installation failed: {e}")

    def assign_ip_addresses(
        self, 
        fixed_devices: "ns.NetDeviceContainer",
        mobile_devices: "ns.NetDeviceContainer"
    ) -> Tuple["ns.Ipv4InterfaceContainer", "ns.Ipv4InterfaceContainer"]:
        """Assign IPv4 addresses to network devices.
        
        Assigns sequential IPv4 addresses from the configured network base
        to all devices.
        
        Args:
            fixed_devices: Network devices for fixed nodes
            mobile_devices: Network devices for mobile nodes
            
        Returns:
            Tuple of (fixed_interfaces, mobile_interfaces)
            
        Raises:
            NetworkSetupError: If IP assignment fails
        """
        try:
            address = ns.Ipv4AddressHelper()
            address.SetBase(ns.Ipv4Address(self.config.network_base),
                           ns.Ipv4Mask(self.config.network_mask))

            self.fixed_interfaces = address.Assign(fixed_devices)
            self.mobile_interfaces = address.Assign(mobile_devices)

            print("IP addresses assigned\n")

            return self.fixed_interfaces, self.mobile_interfaces
            
        except Exception as e:
            raise NetworkSetupError(f"IP address assignment failed: {e}")
