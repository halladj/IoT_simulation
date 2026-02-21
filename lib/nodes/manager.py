"""
Node Manager

Manages creation and organization of fixed and mobile nodes in the simulation.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.config import SimulationConfig

try:
    from ns import ns
except ModuleNotFoundError:
    raise SystemExit(
        "Error: ns3 Python module not found; "
        "Python bindings may not be enabled or PYTHONPATH not configured"
    )

from ..core.exceptions import NodeCreationError


class NodeManager:
    """Manages node creation and organization.
    
    Handles creation of both fixed (stationary access points) and mobile
    (IoT devices) nodes, maintaining separate containers for each type
    and a combined container for all nodes.
    
    Attributes:
        config (SimulationConfig): Simulation configuration
        fixed_nodes (ns.NodeContainer): Container for fixed nodes
        mobile_nodes (ns.NodeContainer): Container for mobile nodes
        all_nodes (ns.NodeContainer): Combined container for all nodes
    """

    def __init__(self, config: "SimulationConfig") -> None:
        """Initialize node manager with configuration.
        
        Args:
            config: Simulation configuration object
        """
        self.config = config
        self.fixed_nodes = ns.NodeContainer()
        self.mobile_nodes = ns.NodeContainer()
        self.all_nodes = ns.NodeContainer()
        self.malicious_node_ids = set()

    def is_malicious(self, node_id: int) -> bool:
        """Check if a node is designated as malicious.
        
        Args:
            node_id: NS-3 global node ID
            
        Returns:
            True if malicious, False otherwise
        """
        return node_id in self.malicious_node_ids

    def create_nodes(self) -> None:
        """Create fixed and mobile nodes according to configuration.
        
        Creates the specified number of fixed and mobile nodes and adds
        them to the combined all_nodes container.
        
        Raises:
            NodeCreationError: If node creation fails
        """
        try:
            self.fixed_nodes.Create(self.config.num_fixed_nodes)
            self.mobile_nodes.Create(self.config.num_mobile_nodes)

            self.all_nodes.Add(self.fixed_nodes)
            self.all_nodes.Add(self.mobile_nodes)

            # Assign malicious roles
            import random
            num_malicious = int(self.config.num_fixed_nodes * self.config.malicious_percentage)
            malicious_indices = random.sample(range(self.config.num_fixed_nodes), num_malicious)
            for i in malicious_indices:
                self.malicious_node_ids.add(self.fixed_nodes.Get(i).GetId())

            print(f"Created {self.config.num_fixed_nodes} fixed nodes ({num_malicious} malicious)")
            print(f"Created {self.config.num_mobile_nodes} mobile nodes\n")
            
        except Exception as e:
            raise NodeCreationError(f"Failed to create nodes: {e}")

    def get_fixed_nodes(self) -> "ns.NodeContainer":
        """Get container of fixed nodes.
        
        Returns:
            NS-3 NodeContainer with all fixed nodes
        """
        return self.fixed_nodes

    def get_mobile_nodes(self) -> "ns.NodeContainer":
        """Get container of mobile nodes.
        
        Returns:
            NS-3 NodeContainer with all mobile nodes
        """
        return self.mobile_nodes

    def get_all_nodes(self) -> "ns.NodeContainer":
        """Get container of all nodes (fixed + mobile).
        
        Returns:
            NS-3 NodeContainer with all nodes
        """
        return self.all_nodes
