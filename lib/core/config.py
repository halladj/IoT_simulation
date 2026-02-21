"""
Simulation Configuration

Configuration management with command-line argument parsing and validation.
"""

from typing import List
import argparse

from .constants import (
    DISCOVERY_START_TIME,
    DISCOVERY_DURATION,
    DISCOVERY_INTERVAL,
    DISCOVERY_RANGE_METERS,
    DISCOVERY_PORT,
    COLLABORATION_START_TIME,
    COLLABORATION_DURATION,
    COLLABORATION_BASE_PORT,
    FIXED_NODE_SPACING_METERS,
    IP_BASE_ADDRESS,
    IP_NETMASK,
)
from .exceptions import ConfigurationError

try:
    from ns import ns
except ModuleNotFoundError:
    ns = None  # Will be handled by main script


class SimulationConfig:
    """Simulation configuration with command-line argument parsing.
    
    Attributes:
        num_fixed_nodes (int): Number of stationary access points
        num_mobile_nodes (int): Number of mobile IoT devices
        sim_time (float): Total simulation duration in seconds
        distance (float): Spacing between fixed nodes in meters
        enable_pcap (bool): Enable PCAP packet capture
        verbose (bool): Enable verbose console output
        discovery_start (float): Discovery phase start time (seconds)
        discovery_duration (float): Discovery phase duration (seconds)
        discovery_interval (float): Time between discovery broadcasts (seconds)
        discovery_range (float): Radio range for discovery (meters)
        discovery_port (int): UDP port for discovery broadcasts
        collab_start (float): Collaboration phase start time (seconds)
        collab_duration (float): Collaboration phase duration (seconds)
        collab_base_port (int): Base TCP port for collaboration
        network_base (str): IPv4 network base address
        network_mask (str): IPv4 network mask
    """

    def __init__(self) -> None:
        """Initialize configuration with default values from constants."""
        # Node configuration
        self.num_fixed_nodes: int = 2
        self.num_mobile_nodes: int = 4
        self.sim_time: float = 100.0
        self.distance: float = FIXED_NODE_SPACING_METERS
        # New DDoS scenario settings
        self.malicious_percentage: float = 0.2
        self.arena_width: float = 1000.0
        self.attack_type: str = "none"
        
        # Output options
        self.enable_pcap: bool = False
        self.verbose: bool = False

        # Phase timings (use constants)
        self.discovery_start: float = DISCOVERY_START_TIME
        self.discovery_duration: float = DISCOVERY_DURATION
        self.discovery_interval: float = DISCOVERY_INTERVAL
        self.discovery_range: float = DISCOVERY_RANGE_METERS
        
        self.collab_start: float = COLLABORATION_START_TIME
        self.collab_duration: float = COLLABORATION_DURATION

        # Port configuration (use constants)
        self.discovery_port: int = DISCOVERY_PORT
        self.collab_base_port: int = COLLABORATION_BASE_PORT

        # Network configuration (use constants)
        self.network_base: str = IP_BASE_ADDRESS
        self.network_mask: str = IP_NETMASK

    def parse_arguments(self, argv: List[str]) -> None:
        """Parse command-line arguments to override default configuration.
        
        Args:
            argv: Command-line argument list from sys.argv
            
        Raises:
            ConfigurationError: If arguments are invalid
        """
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
        parser.add_argument('--maliciousPercentage', type=float, default=self.malicious_percentage,
                          help='Percentage of fixed nodes that act maliciously (0.0 to 1.0)')
        parser.add_argument('--arenaWidth', type=float, default=self.arena_width,
                          help='Total X-axis length for the density gradient')
        parser.add_argument('--attackType', type=str, default="none", choices=["none", "ddos"],
                          help='Attack module to activate')
        parser.add_argument('--pcap', action='store_true', default=self.enable_pcap,
                          help='Enable PCAP tracing')
        parser.add_argument('--verbose', action='store_true', default=self.verbose,
                          help='Enable verbose logging')
        parser.add_argument('--discoveryDuration', type=float, default=self.discovery_duration,
                          help='Discovery phase duration')
        parser.add_argument('--collabDuration', type=float, default=self.collab_duration,
                          help='Collaboration phase duration')
        parser.add_argument('--discoveryRange', type=float, default=self.discovery_range,
                          help='Discovery range in meters (also sets WiFi transmission range)')
        
        try:
            args = parser.parse_args(argv[1:])
        except SystemExit as e:
            raise ConfigurationError(f"Invalid arguments: {e}")
        
        # Validate and assign
        self._validate_and_assign(args)

    def _validate_and_assign(self, args: argparse.Namespace) -> None:
        """Validate parsed arguments and assign to instance variables.
        
        Args:
            args: Parsed arguments from argparse
            
        Raises:
            ConfigurationError: If validation fails
        """
        if args.numFixed < 1:
            raise ConfigurationError("Number of fixed nodes must be at least 1")
        if args.numMobile < 1:
            raise ConfigurationError("Number of mobile nodes must be at least 1")
        if args.simTime <= 0:
            raise ConfigurationError("Simulation time must be positive")
        if args.distance <= 0:
            raise ConfigurationError("Distance must be positive")
        if args.discoveryRange <= 0:
            raise ConfigurationError("Discovery range must be positive")
        if not (0.0 <= args.maliciousPercentage <= 1.0):
            raise ConfigurationError("Malicious percentage must be between 0.0 and 1.0")
        if args.arenaWidth <= 0:
            raise ConfigurationError("Arena width must be positive")
            
        self.num_fixed_nodes = args.numFixed
        self.num_mobile_nodes = args.numMobile
        self.sim_time = args.simTime
        self.distance = args.distance
        self.malicious_percentage = args.maliciousPercentage
        self.arena_width = args.arenaWidth
        self.attack_type = args.attackType
        self.enable_pcap = args.pcap
        self.verbose = args.verbose
        self.discovery_duration = args.discoveryDuration
        self.collab_duration = args.collabDuration
        self.discovery_range = args.discoveryRange

    def enable_logging(self) -> None:
        """Enable NS-3 logging components if verbose mode is on."""
        if self.verbose and ns:
            ns.LogComponentEnable("UdpEchoClientApplication", ns.LOG_LEVEL_INFO)
            ns.LogComponentEnable("UdpEchoServerApplication", ns.LOG_LEVEL_INFO)

    def print_summary(self) -> None:
        """Print simulation configuration summary to console."""
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
