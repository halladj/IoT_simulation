"""
Visualization Manager

Manages network visualization using NetSimulyzer (3D) or NetAnim (2D).
"""

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.config import SimulationConfig
    from ..nodes.manager import NodeManager

try:
    from ns import ns
except ModuleNotFoundError:
    raise SystemExit("NS-3 Python bindings not found")

from ..core.constants import ANIMATION_OUTPUT_FILENAME, OUTPUT_DIR
from ..core.exceptions import VisualizationError


class VisualizationManager:
    """Manages network visualization with NetSimulyzer/NetAnim.
    
    Attempts to use NetSimulyzer for 3D visualization, falling back
    to NetAnim (2D) if unavailable.
    
    Attributes:
        config (SimulationConfig): Simulation configuration
        node_manager (NodeManager): Node manager instance
        orchestrator: NetSimulyzer orchestrator (if available)
        anim: NetAnim animation interface (fallback)
    """

    def __init__(self, config: "SimulationConfig", node_manager: "NodeManager") -> None:
        """Initialize visualization manager.
        
        Args:
            config: Simulation configuration
            node_manager: Node manager with created nodes
        """
        self.config = config
        self.node_manager = node_manager
        self.orchestrator = None
        self.anim = None

    def setup_visualization(self) -> None:
        """Configure visualization - tries NetSimulyzer first, falls back to NetAnim."""
        try:
            if hasattr(ns, 'netsimulyzer'):
                self._setup_netsimulyzer()
            else:
                print("NetSimulyzer module not found, using NetAnim instead...\n")
                self._setup_netanim()
        except (AttributeError, Exception) as e:
            print(f"NetSimulyzer not available ({e}), falling back to NetAnim...\n")
            self._setup_netanim()

    def _setup_netsimulyzer(self) -> None:
        """Configure NetSimulyzer 3D visualization."""
        self.orchestrator = ns.netsimulyzer.Orchestrator("discovery-collab-visualization.json")

        # Fixed nodes - Red cubes
        for i in range(self.config.num_fixed_nodes):
            node = self.node_manager.get_fixed_nodes().Get(i)
            fixed_decoration = ns.netsimulyzer.NodeConfiguration(self.orchestrator)
            fixed_decoration.Set(node)
            fixed_decoration.SetAttribute("Model", ns.StringValue("Cube.obj"))
            fixed_decoration.SetAttribute("Scale", ns.DoubleValue(2.0))
            fixed_decoration.SetAttribute("Color",
                ns.netsimulyzer.Color3Value(ns.netsimulyzer.Color3(255, 0, 0)))
            label = ns.netsimulyzer.NodeLabel(self.orchestrator, node)
            label.SetAttribute("Text", ns.StringValue(f"Fixed-{i}"))

        # Mobile nodes - Blue spheres
        for i in range(self.config.num_mobile_nodes):
            node = self.node_manager.get_mobile_nodes().Get(i)
            mobile_decoration = ns.netsimulyzer.NodeConfiguration(self.orchestrator)
            mobile_decoration.Set(node)
            mobile_decoration.SetAttribute("Model", ns.StringValue("Sphere.obj"))
            mobile_decoration.SetAttribute("Scale", ns.DoubleValue(1.5))
            mobile_decoration.SetAttribute("Color",
                ns.netsimulyzer.Color3Value(ns.netsimulyzer.Color3(0, 0, 255)))
            label = ns.netsimulyzer.NodeLabel(self.orchestrator, node)
            label.SetAttribute("Text", ns.StringValue(f"Mobile-{i}"))

        print("NetSimulyzer 3D visualization configured")
        print("Output file: discovery-collab-visualization.json\n")

    def _setup_netanim(self) -> None:
        """Configure NetAnim 2D visualization."""
        try:
            anim_path = os.path.join(OUTPUT_DIR, ANIMATION_OUTPUT_FILENAME)
            self.anim = ns.AnimationInterface(anim_path)

            # Configure fixed nodes (red)
            for i in range(self.config.num_fixed_nodes):
                node = self.node_manager.get_fixed_nodes().Get(i)
                node_id = node.GetId()
                self.anim.UpdateNodeDescription(node, f"Fixed-{i}")
                self.anim.UpdateNodeColor(node, 255, 0, 0)
                self.anim.UpdateNodeSize(node_id, 5.0, 5.0)

            # Configure mobile nodes (blue)
            for i in range(self.config.num_mobile_nodes):
                node = self.node_manager.get_mobile_nodes().Get(i)
                node_id = node.GetId()
                self.anim.UpdateNodeDescription(node, f"Mobile-{i}")
                self.anim.UpdateNodeColor(node, 0, 0, 255)
                self.anim.UpdateNodeSize(node_id, 3.0, 3.0)

            # Enable packet metadata for better visualization
            self.anim.SetMaxPktsPerTraceFile(500000)
            # Disable packet metadata for smoother playback (can cause hangs with large sims)
            # self.anim.EnablePacketMetadata(True)

            print("NetAnim visualization configured")
            print("Buildings and structures can be added in NetAnim:")
            print("  - File -> Add Resource (for background images)")
            print("  - Or edit the XML to add <rectangle> elements\\n")
            
        except Exception as e:
            # Visualization is non-critical, log warning but don't fail
            print(f"Warning: NetAnim setup had issues: {e}")
            print("Continuing without visualization...\n")
