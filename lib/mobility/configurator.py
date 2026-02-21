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
        
        Places fixed nodes in a density gradient (e.g. quadratic curve) 
        so they are sparse at x=0 and dense at x=arena_width.
        
        Raises:
            MobilityConfigurationError: If mobility setup fails
        """
        try:
            fixed_mobility = ns.MobilityHelper()
            position_alloc = ns.ListPositionAllocator()

            n = self.config.num_fixed_nodes
            for i in range(n):
                # Quadratic density distribution
                normalized = (i / max(1, n - 1)) ** 2
                x = normalized * self.config.arena_width
                
                # Scatter slightly along Y to create a path and avoid collisions
                y_offset = (i % 5 - 2) * 5.0  # -10, -5, 0, 5, 10
                y = 25.0 + y_offset
                
                position_alloc.Add(ns.Vector(x, y, 0.0))

            fixed_mobility.SetPositionAllocator(position_alloc)
            fixed_mobility.SetMobilityModel("ns3::ConstantPositionMobilityModel")
            fixed_mobility.Install(self.node_manager.get_fixed_nodes())

            print(f"Fixed nodes: {n} nodes placed in a density gradient over {self.config.arena_width}m")
            
        except Exception as e:
            raise MobilityConfigurationError(f"Fixed mobility setup failed: {e}")

    def setup_mobile_mobility(self) -> None:
        """Configure ConstantVelocity mobility for mobile node.
        
        The mobile node starts at x=0 and moves in a straight line 
        through the density gradient of fixed nodes.
        
        Raises:
            MobilityConfigurationError: If mobility setup fails
        """
        try:
            mobile_mobility = ns.MobilityHelper()
            mobile_position = ns.ListPositionAllocator()
            
            num_mobile = self.node_manager.get_mobile_nodes().GetN()
            
            # Start mobile nodes at the sparse end (x=0) and center them (y=25)
            for i in range(num_mobile):
                mobile_position.Add(ns.Vector(0.0, 25.0 + (i * 2.0), 0.0))
            
            mobile_mobility.SetPositionAllocator(mobile_position)
            mobile_mobility.SetMobilityModel("ns3::ConstantVelocityMobilityModel")
            
            mobile_nodes = self.node_manager.get_mobile_nodes()
            mobile_mobility.Install(mobile_nodes)

            # Set velocity to traverse the arena within the simulation time
            speed_x = self.config.arena_width / self.config.sim_time
            for i in range(num_mobile):
                node = mobile_nodes.Get(i)
                mob = node.GetObject[ns.MobilityModel]()
                mob.SetVelocity(ns.Vector(speed_x, 0.0, 0.0))

            print(f"Mobile nodes: Constant velocity configured ({speed_x:.2f} m/s)\n")
            
        except Exception as e:
            raise MobilityConfigurationError(f"Mobile mobility setup failed: {e}")
