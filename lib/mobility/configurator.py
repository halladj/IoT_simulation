"""
Mobility Configurator

Configures mobility models for fixed and mobile nodes.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.config import SimulationConfig
    from ..nodes.manager import NodeManager

try:
    from ns import ns
except ModuleNotFoundError:
    raise SystemExit("NS-3 Python bindings not found")

from ..core.constants import MOBILE_NODE_POSITIONS
from ..core.exceptions import MobilityConfigurationError


class MobilityConfigurator:
    """Configures mobility models for nodes.
    
    Sets up constant position mobility for fixed nodes and RandomWalk2d
    mobility for mobile nodes with predefined starting positions to avoid
    overlap.
    
    Attributes:
        config (SimulationConfig): Simulation configuration
        node_manager (NodeManager): Node manager instance
    """

    def __init__(self, config: "SimulationConfig", node_manager: "NodeManager") -> None:
        """Initialize mobility configurator.
        
        Args:
            config: Simulation configuration
            node_manager: Node manager with created nodes
        """
        self.config = config
        self.node_manager = node_manager

    def setup_fixed_mobility(self) -> None:
        """Configure stationary positions for fixed nodes.
        
        Places fixed nodes in a line with configured spacing.
        Position of node i is (i * distance, 0, 0).
        
        Raises:
            MobilityConfigurationError: If mobility setup fails
        """
        try:
            fixed_mobility = ns.MobilityHelper()
            position_alloc = ns.ListPositionAllocator()

            for i in range(self.config.num_fixed_nodes):
                position_alloc.Add(ns.Vector(i * self.config.distance, 0.0, 0.0))

            fixed_mobility.SetPositionAllocator(position_alloc)
            fixed_mobility.SetMobilityModel("ns3::ConstantPositionMobilityModel")
            fixed_mobility.Install(self.node_manager.get_fixed_nodes())

            print("Fixed nodes: Stationary positions configured")
            
        except Exception as e:
            raise MobilityConfigurationError(f"Fixed mobility setup failed: {e}")

    def setup_mobile_mobility(self) -> None:
        """Configure RandomWalk2d mobility for mobile nodes.
        
        Dynamically generates distinct starting positions to avoid node overlap
        which can cause propagation delay calculation errors.
        
        Raises:
            MobilityConfigurationError: If mobility setup fails
        """
        try:
            mobile_mobility = ns.MobilityHelper()

            # Use ListPositionAllocator with dynamically generated positions
            mobile_position = ns.ListPositionAllocator()
            
            # Generate distinct starting positions for all mobile nodes
            num_mobile = self.node_manager.get_mobile_nodes().GetN()
            
            # Use predefined positions first, then generate additional ones
            for i in range(num_mobile):
                if i < len(MOBILE_NODE_POSITIONS):
                    # Use predefined position
                    x, y, z = MOBILE_NODE_POSITIONS[i]
                else:
                    # Generate position in a grid pattern within bounds
                    # Bounds are (0, 80) x (0, 50) from RandomWalk2d config
                    grid_cols = 4  # 4 columns
                    col = i % grid_cols
                    row = i // grid_cols
                    x = 15.0 + (col * 20.0)  # Spread across X: 15, 35, 55, 75
                    y = 15.0 + (row * 10.0)  # Spread across Y: 15, 25, 35, 45
                    z = 0.0
                    
                    # Ensure position is within bounds (safety check)
                    x = min(max(x, 5.0), 75.0)
                    y = min(max(y, 5.0), 45.0)
                
                mobile_position.Add(ns.Vector(x, y, z))
            
            mobile_mobility.SetPositionAllocator(mobile_position)

            # RandomWalk2d with bounds to prevent excessive movement
            mobile_mobility.SetMobilityModel("ns3::RandomWalk2dMobilityModel",
                                            "Bounds", ns.RectangleValue(
                                                ns.Rectangle(0, 80, 0, 50)),
                                            "Speed", ns.StringValue(
                                                "ns3::UniformRandomVariable[Min=1.0|Max=5.0]"),
                                            "Distance", ns.DoubleValue(15.0))
            mobile_mobility.Install(self.node_manager.get_mobile_nodes())

            print(f"Mobile nodes: Random walk mobility configured ({num_mobile} nodes)\n")
            
        except Exception as e:
            raise MobilityConfigurationError(f"Mobile mobility setup failed: {e}")
