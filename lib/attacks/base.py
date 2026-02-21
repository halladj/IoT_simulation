"""
Modular Attack Framework Base Class
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ns import ns
    from ..core.config import SimulationConfig
    from ..nodes.manager import NodeManager

class BaseAttack(ABC):
    """Abstract base class for all simulated attacks."""
    
    def __init__(self, config: "SimulationConfig", node_manager: "NodeManager") -> None:
        """Initialize the attack module.
        
        Args:
            config: Simulation configuration
            node_manager: Manager containing created nodes (both fixed and mobile)
        """
        self.config = config
        self.node_manager = node_manager
        
    @abstractmethod
    def setup_attack(self, fixed_interfaces: "ns.Ipv4InterfaceContainer", mobile_interfaces: "ns.Ipv4InterfaceContainer") -> None:
        """Configure the attack applications.
        
        This method is called during the main simulation setup phase after IP assignment.
        
        Args:
            fixed_interfaces: IP interfaces of stationary nodes
            mobile_interfaces: IP interfaces of moving nodes
        """
        pass
