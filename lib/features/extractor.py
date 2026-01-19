"""
Feature Extractor

Extracts network flow and mobility features from simulation for ML/IDS research.
"""

import csv
import os
from typing import TYPE_CHECKING, Dict, List
from collections import defaultdict

if TYPE_CHECKING:
    from ..core.config import SimulationConfig
    from ..nodes.manager import NodeManager

try:
    from ns import ns
except ModuleNotFoundError:
    raise SystemExit("NS-3 Python bindings not found")

from ..core.constants import CSV_OUTPUT_FILENAME, OUTPUT_DIR
from ..core.exceptions import FeatureExtractionError


class FeatureExtractor:
    """Extracts and exports network flow and mobility features.
    
    Uses NS-3 FlowMonitor to collect network statistics and calculates
    mobility-specific metrics like node density.
    
    Attributes:
        config (SimulationConfig): Simulation configuration
        flow_monitor: NS-3 FlowMonitor instance
        monitor_helper: NS-3 FlowMonitorHelper
        node_manager: Node manager reference
        node_densities: Dict mapping node_id to list of neighbor counts
    """

    def __init__(self, config: "SimulationConfig") -> None:
        """Initialize feature extractor.
        
        Args:
            config: Simulation configuration
        """
        self.config = config
        self.flow_monitor = None
        self.monitor_helper = None
        self.node_manager = None
        self.node_densities: Dict[int, List[int]] = defaultdict(list)

    def setup_flow_monitor(
        self,
        fixed_interfaces: "ns.Ipv4InterfaceContainer",
        mobile_interfaces: "ns.Ipv4InterfaceContainer"
    ) -> None:
        """Install FlowMonitor on all nodes to track network flows.
        
        Args:
            fixed_interfaces: IPv4 interfaces for fixed nodes
            mobile_interfaces: IPv4 interfaces for mobile nodes
        """
        self.monitor_helper = ns.FlowMonitorHelper()
        self.flow_monitor = self.monitor_helper.InstallAll()
        print("FlowMonitor feature extraction configured")

    def schedule_density_sampling(self, node_manager: "NodeManager") -> None:
        """Prepare density calculation (computed post-simulation).
        
        Args:
            node_manager: Node manager to access node positions
        """
        self.node_manager = node_manager
        
        # Initialize storage for density values
        for i in range(node_manager.get_all_nodes().GetN()):
            node = node_manager.get_all_nodes().Get(i)
            self.node_densities[node.GetId()] = []
        
        print("Density will be computed post-simulation from node positions")

    def _compute_average_density_per_node(self) -> None:
        """Compute average node density based on final positions.
        
        Calculates number of neighbors within discovery range for each node
        at the end of simulation.
        """
        if not self.node_manager:
            return
            
        all_nodes = self.node_manager.get_all_nodes()
        n = all_nodes.GetN()
        
        # Calculate density based on final positions
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

    def extract_features(self) -> None:
        """Extract flow statistics and save to CSV.
        
        Collects network flow metrics from FlowMonitor and mobility
        metrics, then exports to CSV file.
        
        Raises:
            FeatureExtractionError: If feature extraction fails
        """
        try:
            print("Extracting features (this may take a moment)...")
            
            # Compute density snapshot at end of simulation
            self._compute_average_density_per_node()
            
            self.flow_monitor.CheckForLostPackets()
            classifier = self.monitor_helper.GetClassifier()

            csv_path = os.path.join(OUTPUT_DIR, CSV_OUTPUT_FILENAME)
            with open(csv_path, 'w', newline='') as csvfile:
                fieldnames = [
                    'FlowID', 'SourceIP', 'DestIP', 'Protocol', 'Duration',
                    'TxPackets', 'RxPackets', 'TxBytes', 'RxBytes',
                    'MeanDelay', 'MeanJitter', 'LostPackets', 'Throughput_Kbps',
                    'AvgNodeSpeed_mps', 'DistToAP_meters', 'AvgNodeDensity'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for flow_id, flow_stats in self.flow_monitor.GetFlowStats():
                    t = classifier.FindFlow(flow_id)
                    proto = {6: 'TCP', 17: 'UDP'}.get(t.protocol, str(t.protocol))
                    
                    source_addr = t.sourceAddress
                    dest_addr = t.destinationAddress

                    # Skip flows with no packets
                    if flow_stats.txPackets == 0:
                        continue

                    duration = flow_stats.timeLastRxPacket.GetSeconds() - flow_stats.timeFirstTxPacket.GetSeconds()
                    if duration <= 0:
                        duration = 1.0 

                    throughput = (flow_stats.rxBytes * 8.0) / duration / 1000.0 if duration > 0 else 0

                    # Calculate average density for source node
                    avg_density = self._get_node_density(source_addr)

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
                        'AvgNodeSpeed_mps': "N/A",  # Placeholder for future implementation
                        'DistToAP_meters': "N/A",    # Placeholder for future implementation
                        'AvgNodeDensity': avg_density
                    })
            
            print(f"Features saved to '{csv_path}'")
            
        except Exception as e:
            raise FeatureExtractionError(f"Feature extraction failed: {e}")

    def _get_node_density(self, source_addr: "ns.Ipv4Address") -> str:
        """Get average density for a node based on its IP address.
        
        Args:
            source_addr: Source IPv4 address
            
        Returns:
            Average density as string or "N/A" if unavailable
        """
        try:
            # Map IP address to node ID
            # Assuming sequential assignment: 10.1.1.1 = Node 0, 10.1.1.2 = Node 1, etc.
            ip_str = str(source_addr)
            if ip_str.startswith("10.1.1."):
                octet = int(ip_str.split('.')[-1])
                node_id = octet - 1  # Convert to 0-based index
                if node_id in self.node_densities:
                    counts = self.node_densities[node_id]
                    if counts:
                        return f"{sum(counts) / len(counts):.2f}"
        except Exception:
            pass
        
        return "N/A"
