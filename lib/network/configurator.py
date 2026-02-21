"""
Network Configurator

Configures WiFi network devices and channel parameters.
"""

from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from ..core.config import SimulationConfig
    from ..nodes.manager import NodeManager

try:
    from ns import ns
except ModuleNotFoundError:
    raise SystemExit("NS-3 Python bindings not found")

from ..core.constants import NETWORK_SSID
from ..core.exceptions import NetworkSetupError


class NetworkConfigurator:
    """Configures WiFi 802.11n network and devices.
    
    Sets up access points (AP) for fixed nodes and stations (STA) for
    mobile nodes using the YANS WiFi helper and channel model.
    
    Attributes:
        config (SimulationConfig): Simulation configuration
        node_manager (NodeManager): Node manager instance
        fixed_devices (ns.NetDeviceContainer): WiFi devices for fixed nodes
        mobile_devices (ns.NetDeviceContainer): WiFi devices for mobile nodes
    """

    def __init__(self, config: "SimulationConfig", node_manager: "NodeManager") -> None:
        """Initialize network configurator.
        
        Args:
            config: Simulation configuration
            node_manager: Node manager with created nodes
        """
        self.config = config
        self.node_manager = node_manager
        self.fixed_devices = None
        self.mobile_devices = None

    def setup_wifi(self) -> "ns.YansWifiPhyHelper":
        """Configure WiFi 802.11n network with AP and STA modes.
        
        Fixed nodes are configured as Access Points (AP) and mobile nodes
        as Stations (STA) using the specified SSID.
        
        Returns:
            YANS WiFi PHY helper for potential further configuration
            
        Raises:
            NetworkSetupError: If WiFi setup fails
        """
        try:
            wifi = ns.WifiHelper()
            wifi.SetStandard(ns.WIFI_STANDARD_80211n)

            wifi_phy = ns.YansWifiPhyHelper()
            wifi_channel = ns.YansWifiChannelHelper.Default()
            
            # Enforce a strict physical signal cutoff matching our context discovery range
            wifi_channel.AddPropagationLoss("ns3::RangePropagationLossModel", 
                                            "MaxRange", ns.DoubleValue(self.config.discovery_range))
                                            
            wifi_phy.SetChannel(wifi_channel.Create())
            
            # TxPower approximations
            tx_power = getattr(self, '_calculate_tx_power', lambda x: 16.0)(self.config.discovery_range)
            try:
                wifi_phy.Set("TxPowerStart", ns.DoubleValue(tx_power))
                wifi_phy.Set("TxPowerEnd", ns.DoubleValue(tx_power))
            except Exception:
                pass # Newer versions of NS-3 deprecate TxPowerStart in favor of other attributes

            wifi_mac = ns.WifiMacHelper()
            ssid = ns.Ssid(NETWORK_SSID)

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

            print(f"WiFi network configured (802.11n)")
            print(f"Discovery range: {self.config.discovery_range}m (TX power: {tx_power:.1f} dBm)")
            return wifi_phy
            
        except Exception as e:
            raise NetworkSetupError(f"WiFi setup failed: {e}")

    def _calculate_tx_power(self, range_meters: float) -> float:
        """Calculate WiFi transmission power from desired range.
        
        Rough approximation based on free-space path loss.
        
        Args:
            range_meters: Desired transmission range in meters
            
        Returns:
            Transmission power in dBm
        """
        # Empirical approximation for 802.11n at 2.4 GHz
        # These values give approximate ranges in typical conditions
        if range_meters <= 30:
            return 5.0  # ~30m range
        elif range_meters <= 50:
            return 10.0  # ~50m range
        elif range_meters <= 80:
            return 16.0  # ~80m range (default)
        elif range_meters <= 100:
            return 20.0  # ~100m range
        else:
            # For larger ranges, scale logarithmically
            return min(30.0, 20 + (range_meters - 100) / 20)

    def get_devices(self) -> Tuple["ns.NetDeviceContainer", "ns.NetDeviceContainer"]:
        """Get configured network devices.
        
        Returns:
            Tuple of (fixed_devices, mobile_devices)
        """
        return self.fixed_devices, self.mobile_devices
