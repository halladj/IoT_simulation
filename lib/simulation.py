"""
Main Simulation Orchestrator

Coordinates all components to run the complete simulation.
"""

import sys
import os
from typing import List

try:
    from ns import ns
except ModuleNotFoundError:
    raise SystemExit("NS-3 Python bindings not found")

from .core.config import SimulationConfig
from .core.constants import OUTPUT_DIR
from .core.exceptions import SimulationError
from .nodes.manager import NodeManager
from .network.configurator import NetworkConfigurator
from .network.stack import NetworkStackConfigurator
from .mobility.configurator import MobilityConfigurator
from .protocols.discovery import DiscoveryPhaseManager
from .protocols.collaboration import CollaborationPhaseManager
from .visualization.manager import VisualizationManager
from .features.extractor import FeatureExtractor
from .attacks import DdosAttack


class Simulation:
    """Main simulation orchestrator that coordinates all components.
    
    Manages the complete lifecycle of the simulation from initialization
    through setup, execution, and feature extraction.
    
    Attributes:
        config (SimulationConfig): Simulation configuration
        node_manager (NodeManager): Node creation and management
        network_config (NetworkConfigurator): WiFi network setup
        mobility_config (MobilityConfigurator): Mobility model configuration
        stack_config (NetworkStackConfigurator): Internet stack setup
        discovery_manager (DiscoveryPhaseManager): Discovery phase protocol
        collab_manager (CollaborationPhaseManager): Collaboration phase protocol
        viz_manager (VisualizationManager): Visualization setup
        feature_extractor (FeatureExtractor): Feature extraction and export
    """

    def __init__(self) -> None:
        """Initialize simulation orchestrator."""
        self.config = SimulationConfig()
        self.node_manager = None
        self.network_config = None
        self.mobility_config = None
        self.stack_config = None
        self.discovery_manager = None
        self.collab_manager = None
        self.viz_manager = None
        self.feature_extractor = None
        self.attack_manager = None

    def initialize(self, argv: List[str]) -> None:
        """Initialize simulation components with configuration.
        
        Args:
            argv: Command-line arguments from sys.argv
            
        Raises:
            SimulationError: If initialization fails
        """
        try:
            self.config.parse_arguments(argv)
            self.config.enable_logging()
            self.config.print_summary()

            # Create output directory for all generated files
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            print(f"Output directory: {OUTPUT_DIR}/\n")

            # Create all component managers with dependency injection
            self.node_manager = NodeManager(self.config)
            self.network_config = NetworkConfigurator(self.config, self.node_manager)
            self.mobility_config = MobilityConfigurator(self.config, self.node_manager)
            self.stack_config = NetworkStackConfigurator(self.config, self.node_manager)
            self.discovery_manager = DiscoveryPhaseManager(self.config, self.node_manager)
            self.collab_manager = CollaborationPhaseManager(self.config, self.node_manager)
            self.viz_manager = VisualizationManager(self.config, self.node_manager)
            self.feature_extractor = FeatureExtractor(self.config, self.node_manager)
            
            if self.config.attack_type == "ddos":
                self.attack_manager = DdosAttack(self.config, self.node_manager)
            
        except Exception as e:
            raise SimulationError(f"Initialization failed: {e}")

    def setup(self) -> None:
        """Setup all simulation components.
        
        Configures nodes, network, mobility, protocols, and monitoring.
        
        Raises:
            SimulationError: If setup fails
        """
        try:
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
            fixed_interfaces, mobile_interfaces = self.stack_config.assign_ip_addresses(
                fixed_devices, mobile_devices
            )

            # Enable PCAP tracing if requested
            if self.config.enable_pcap:
                wifi_phy.EnablePcapAll("discovery-collab")
                print("PCAP tracing enabled\n")

            # Setup protocols
            self.discovery_manager.setup_discovery_phase(fixed_interfaces, mobile_interfaces)
            self.collab_manager.setup_collaboration_phase(fixed_interfaces, mobile_interfaces)

            # Setup attacks
            if self.attack_manager:
                self.attack_manager.setup_attack(fixed_interfaces, mobile_interfaces)

            # Setup visualization
            self.viz_manager.setup_visualization()

            # Setup feature extraction
            self.feature_extractor.setup_flow_monitor(fixed_interfaces, mobile_interfaces)
            self.feature_extractor.schedule_density_sampling(self.node_manager)
            
        except Exception as e:
            raise SimulationError(f"Setup failed: {e}")

    def run(self) -> None:
        """Run the simulation step-by-step.
        
        Executes the NS-3 simulation in 1.0 second increments to extract dynamic time-series features.
        
        Raises:
            SimulationError: If simulation execution fails
        """
        try:
            print("="*70)
            print("Starting simulation...")
            print("="*70 + "\n")

            # Run simulation in increments to safely allow python feature extraction
            now = 0.0
            step = 1.0
            while now < self.config.sim_time:
                # Tell simulator to stop at the next step interval
                ns.Simulator.Stop(ns.Seconds(now + step))
                ns.Simulator.Run()
                
                # We are now paused exactly at 'now + step' Simulation Time
                self.feature_extractor.sample_time_series()
                
                now += step

            # Final feature extraction and CSV export
            self.feature_extractor.extract_features()

            # Cleanup
            ns.Simulator.Destroy()

            print("\n" + "="*70)
            print("Simulation completed successfully!")
            print("="*70)
            
        except Exception as e:
            ns.Simulator.Destroy()
            raise SimulationError(f"Simulation execution failed: {e}")


def main(argv: List[str] = None) -> int:
    """Main entry point for simulation.
    
    Args:
        argv: Command-line arguments (defaults to sys.argv)
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    if argv is None:
        argv = sys.argv

    try:
        simulation = Simulation()
        simulation.initialize(argv)
        simulation.setup()
        simulation.run()
        return 0
        
    except SimulationError as e:
        print(f"\nSimulation Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\nUnexpected Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
