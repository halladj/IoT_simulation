"""
DDoS Attack Implementation
"""

import math
from .base import BaseAttack
from ..core.exceptions import SimulationError

try:
    from ns import ns
except ModuleNotFoundError:
    raise SystemExit("NS-3 Python bindings not found")

class DdosAttack(BaseAttack):
    """Implements a high-throughput context-based DDoS attack.
    
    Malicious fixed nodes will blast UDP traffic at the mobile node ONLY when it
    is mathematically within their discovery range (the "context").
    """
    
    def setup_attack(self, fixed_interfaces: "ns.Ipv4InterfaceContainer", mobile_interfaces: "ns.Ipv4InterfaceContainer") -> None:
        """Configure UDP DDoS OnOff applications."""
        try:
            # We assume mobile node 0 is the victim
            victim_node = self.node_manager.get_mobile_nodes().Get(0)
            victim_addr = mobile_interfaces.GetAddress(0)
            
            # Setup Packet Sink on the victim to receive attack traffic
            # Uses a unique high port to isolate from discovery/collab phases
            sink_port = 5000
            sink_address = ns.InetSocketAddress(ns.Ipv4Address.GetAny(), sink_port)
            sink_helper = ns.PacketSinkHelper("ns3::UdpSocketFactory", sink_address.ConvertTo())
            victim_sink = sink_helper.Install(victim_node)
            victim_sink.Start(ns.Seconds(0.0))
            victim_sink.Stop(ns.Seconds(self.config.sim_time))
            
            # Setup OnOffHelper for attackers
            onoff_address = ns.InetSocketAddress(victim_addr, sink_port)
            onoff_helper = ns.OnOffHelper("ns3::UdpSocketFactory", onoff_address.ConvertTo())
            # Controlled data rate for DDoS (Lowered to 100Kbps to allow NetAnim to trace the full 300s run)
            onoff_helper.SetAttribute("DataRate", ns.DataRateValue(ns.DataRate("100Kbps")))
            onoff_helper.SetAttribute("PacketSize", ns.UintegerValue(1024))
            
            # Constant traffic while ON
            onoff_helper.SetAttribute("OnTime", ns.StringValue("ns3::ConstantRandomVariable[Constant=1]"))
            onoff_helper.SetAttribute("OffTime", ns.StringValue("ns3::ConstantRandomVariable[Constant=0]"))
            
            # The mobile node moves with a constant velocity across the X axis
            v_x = self.config.arena_width / self.config.sim_time
            r = self.config.discovery_range
            
            # Mobile starts at y=25.0
            mob_y = 25.0 
            
            fixed_nodes = self.node_manager.get_fixed_nodes()
            num_configured = 0
            
            # Iterate through all fixed nodes, pre-calculating exact entry/exit times
            for i in range(fixed_nodes.GetN()):
                node_id = fixed_nodes.Get(i).GetId()
                if self.node_manager.is_malicious(node_id):
                    attacker_node = fixed_nodes.Get(i)
                    attacker_mob = attacker_node.GetObject[ns.MobilityModel]()
                    attacker_pos = attacker_mob.GetPosition()
                    x_f = attacker_pos.x
                    y_f = attacker_pos.y
                    
                    # Math for circle-line intersection: 
                    # Does the mobile path cut through the attacker's context range?
                    # (v*t - x_f)^2 + (mob_y - y_f)^2 = r^2
                    y_dist_sq = (mob_y - y_f)**2
                    r_sq = r**2
                    
                    if y_dist_sq <= r_sq:
                        # Path intersects! Solve for Leg X (distance from center x_f to edge of context)
                        leg_x = math.sqrt(r_sq - y_dist_sq)
                        
                        # Calculate raw entering and exiting times
                        t_enter = (x_f - leg_x) / v_x
                        t_exit = (x_f + leg_x) / v_x
                        
                        # Clamp to simulation bounds
                        t_start = max(0.0, t_enter)
                        t_stop = min(self.config.sim_time, t_exit)
                        
                        # If not negative duration, schedule the burst
                        if t_start < t_stop:
                            apps = onoff_helper.Install(attacker_node)
                            apps.Start(ns.Seconds(t_start))
                            apps.Stop(ns.Seconds(t_stop))
                            num_configured += 1
            
            print(f"DDoS Attack: {num_configured} malicious nodes placed within context trajectory.")
            
        except Exception as e:
            raise SimulationError(f"Failed to setup DDoS attack: {e}")
