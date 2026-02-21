"""
Feature Extractor

Extracts network flow and mobility features from simulation for ML/IDS research.
"""

import csv
import os
import math
from typing import TYPE_CHECKING, Dict, List

if TYPE_CHECKING:
    from ..core.config import SimulationConfig
    from ..nodes.manager import NodeManager

try:
    from ns import ns
except ModuleNotFoundError:
    raise SystemExit("NS-3 Python bindings not found")

from ..core.constants import OUTPUT_DIR
from ..core.exceptions import FeatureExtractionError

class FeatureExtractor:
    """Extracts and exports network flow and mobility features.
    
    Implements a dual-extraction method building:
    1. Time-series window features (N-BaIoT style + Mobility Context)
    2. Flow-based features (IoTID20 style)
    """

    def __init__(self, config: "SimulationConfig", node_manager: "NodeManager") -> None:
        """Initialize feature extractor."""
        self.config = config
        self.node_manager = node_manager
        self.flow_monitor = None
        self.monitor_helper = None
        
        # Time-series storage
        self.time_series_data = [] 
        self.last_rx_bytes = 0
        self.last_tx_bytes = 0
        self.last_rx_packets = 0
        self.last_tx_packets = 0

    def setup_flow_monitor(
        self,
        fixed_interfaces: "ns.Ipv4InterfaceContainer",
        mobile_interfaces: "ns.Ipv4InterfaceContainer"
    ) -> None:
        """Install FlowMonitor on all nodes."""
        self.monitor_helper = ns.FlowMonitorHelper()
        self.flow_monitor = self.monitor_helper.InstallAll()
        print("FlowMonitor feature extraction configured")

    def schedule_density_sampling(self, node_manager: "NodeManager") -> None:
        """Schedule the periodic task to sample N-BaIoT and Context features."""
        # Managed continuously by the Simulation orchestrator step-by-step
        pass

    def sample_time_series(self) -> None:
        """Sample context and network metrics for the current time window."""
        now = ns.Simulator.Now().GetSeconds()
        if now > self.config.sim_time:
            return

        # 1. Calculate Novel Mobility Context Features
        victim_node = self.node_manager.get_mobile_nodes().Get(0)
        victim_mob = victim_node.GetObject[ns.MobilityModel]()
        v_pos = victim_mob.GetPosition()
        
        total_neighbors = 0
        malicious_neighbors = 0
        min_attacker_dist = float('inf')
        
        fixed_nodes = self.node_manager.get_fixed_nodes()
        for i in range(fixed_nodes.GetN()):
            f_node = fixed_nodes.Get(i)
            f_mob = f_node.GetObject[ns.MobilityModel]()
            f_pos = f_mob.GetPosition()
            
            dist = math.sqrt((v_pos.x - f_pos.x)**2 + (v_pos.y - f_pos.y)**2)
            if dist <= self.config.discovery_range:
                total_neighbors += 1
                if self.node_manager.is_malicious(f_node.GetId()):
                    malicious_neighbors += 1
                    if dist < min_attacker_dist:
                        min_attacker_dist = dist

        dist_to_attacker = min_attacker_dist if min_attacker_dist != float('inf') else -1.0
        # If there are malicious nodes within context, we are getting strictly attacked!
        is_under_attack = 1 if malicious_neighbors > 0 else 0
        
        # 2. Calculate N-BaIoT Time-Window Aggregated Features
        self.flow_monitor.CheckForLostPackets()
        stats = self.flow_monitor.GetFlowStats()
        
        current_rx_bytes = 0
        current_tx_bytes = 0
        current_rx_packets = 0
        current_tx_packets = 0
        
        for flow_id, flow_stat in stats:
            current_rx_bytes += flow_stat.rxBytes
            current_tx_bytes += flow_stat.txBytes
            current_rx_packets += flow_stat.rxPackets
            current_tx_packets += flow_stat.txPackets
            
        # Diff against last 1.0s window
        window_rx_bytes = current_rx_bytes - self.last_rx_bytes
        window_tx_bytes = current_tx_bytes - self.last_tx_bytes
        window_rx_packets = current_rx_packets - self.last_rx_packets
        window_tx_packets = current_tx_packets - self.last_tx_packets
        
        # Save state for next tick
        self.last_rx_bytes = current_rx_bytes
        self.last_tx_bytes = current_tx_bytes
        self.last_rx_packets = current_rx_packets
        self.last_tx_packets = current_tx_packets
        
        record = {
            'SimulationTime': float(f"{now:.1f}"),
            'Mobile_X_Pos': float(f"{v_pos.x:.2f}"),
            'Mobile_Y_Pos': float(f"{v_pos.y:.2f}"),
            'Node_Density': total_neighbors,
            'Malicious_Neighbors': malicious_neighbors,
            'Dist_To_Attacker': float(f"{dist_to_attacker:.2f}"),
            'Node_Sending_Rate_Pkts': window_tx_packets,
            'Node_Sending_Rate_Bytes': window_tx_bytes,
            'Rx_Bytes_Per_Sec': window_rx_bytes,
            'Rx_Pkts_Per_Sec': window_rx_packets,
            'Is_Under_Attack': is_under_attack
        }
        self.time_series_data.append(record)

    def extract_features(self) -> None:
        """Extract both Flow and Time-Series statistics to CSVs."""
        try:
            print("Exporting ML datasets (this may take a moment)...")
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            
            # --- Export Time Series Features ---
            ts_path = os.path.join(OUTPUT_DIR, "timeseries_features.csv")
            if self.time_series_data:
                with open(ts_path, 'w', newline='') as csvfile:
                    fieldnames = self.time_series_data[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(self.time_series_data)
                print(f"Time-series features saved to '{ts_path}'")
                
            # --- Export IoTID20 Style Flow Features ---
            self.flow_monitor.CheckForLostPackets()
            classifier = self.monitor_helper.GetClassifier()

            flow_path = os.path.join(OUTPUT_DIR, "flow_features.csv")
            with open(flow_path, 'w', newline='') as csvfile:
                fieldnames = [
                    'Flow_ID', 'Src_IP', 'Dst_IP', 'Protocol', 'Flow_Duration',
                    'Tot_Fwd_Pkts', 'Tot_Bwd_Pkts', 'TotLen_Fwd_Bytes', 'TotLen_Bwd_Bytes',
                    'Flow_Bytes_s', 'Flow_Pkts_s', 'Mean_Delay', 'Mean_Jitter', 'Lost_Packets'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for flow_id, flow_stats in self.flow_monitor.GetFlowStats():
                    t = classifier.FindFlow(flow_id)
                    proto = {6: 'TCP', 17: 'UDP'}.get(t.protocol, str(t.protocol))
                    
                    if flow_stats.txPackets == 0:
                        continue

                    duration = flow_stats.timeLastRxPacket.GetSeconds() - flow_stats.timeFirstTxPacket.GetSeconds()
                    if duration <= 0:
                        duration = 0.0001 

                    throughput_bytes = (flow_stats.rxBytes) / duration
                    packet_rate = (flow_stats.rxPackets) / duration

                    writer.writerow({
                        'Flow_ID': flow_id,
                        'Src_IP': t.sourceAddress,
                        'Dst_IP': t.destinationAddress,
                        'Protocol': proto,
                        'Flow_Duration': f"{duration:.4f}",
                        'Tot_Fwd_Pkts': flow_stats.txPackets,
                        'Tot_Bwd_Pkts': flow_stats.rxPackets,
                        'TotLen_Fwd_Bytes': flow_stats.txBytes,
                        'TotLen_Bwd_Bytes': flow_stats.rxBytes,
                        'Flow_Bytes_s': f"{throughput_bytes:.2f}",
                        'Flow_Pkts_s': f"{packet_rate:.2f}",
                        'Mean_Delay': f"{flow_stats.delaySum.GetSeconds() / flow_stats.rxPackets if flow_stats.rxPackets > 0 else 0:.6f}",
                        'Mean_Jitter': f"{flow_stats.jitterSum.GetSeconds() / (flow_stats.rxPackets - 1) if flow_stats.rxPackets > 1 else 0:.6f}",
                        'Lost_Packets': flow_stats.lostPackets
                    })
            
            print(f"Flow-based features saved to '{flow_path}'")
            
        except Exception as e:
            raise FeatureExtractionError(f"Feature extraction failed: {e}")
