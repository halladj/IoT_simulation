"""
Simulation Constants

Global constants for NS-3 network simulation including network configuration,
timing parameters, physical parameters, and output settings.
"""

# =============================================================================
# NETWORK CONFIGURATION
# =============================================================================

NETWORK_SSID = "discovery-collab-network"
"""str: WiFi SSID for the simulation network"""

IP_BASE_ADDRESS = "10.1.1.0"
"""str: Base IPv4 address for the network"""

IP_NETMASK = "255.255.255.0"
"""str: Network mask for IP assignment"""


# =============================================================================
# PORT CONFIGURATION
# =============================================================================

DISCOVERY_PORT = 8000
"""int: UDP port for discovery phase broadcasts"""

COLLABORATION_BASE_PORT = 9000
"""int: Base TCP port for collaboration phase (increments per node)"""


# =============================================================================
# PHYSICAL PARAMETERS
# =============================================================================

DISCOVERY_RANGE_METERS = 80.0
"""float: Radio range for neighbor discovery in meters"""

FIXED_NODE_SPACING_METERS = 50.0
"""float: Default spacing between fixed access points in meters"""


# =============================================================================
# TIMING PARAMETERS (seconds)
# =============================================================================

DISCOVERY_START_TIME = 2.0
"""float: Simulation time when discovery phase begins"""

DISCOVERY_DURATION = 20.0
"""float: Duration of discovery phase"""

DISCOVERY_INTERVAL = 2.0
"""float: Time between discovery broadcast messages"""

COLLABORATION_START_TIME = 25.0
"""float: Simulation time when collaboration phase begins"""

COLLABORATION_DURATION = 70.0
"""float: Duration of collaboration phase"""


# =============================================================================
# PACKET SIZES (bytes)
# =============================================================================

DISCOVERY_PACKET_SIZE = 128
"""int: Size of discovery broadcast packets"""

COLLABORATION_PACKET_SIZE = 1024
"""int: Size of collaboration data packets"""


# =============================================================================
# OUTPUT CONFIGURATION
# =============================================================================

OUTPUT_DIR = "simulation_output"
"""str: Directory for all simulation output files"""

CSV_OUTPUT_FILENAME = "simulation_features.csv"
"""str: Output filename for feature dataset"""

ANIMATION_OUTPUT_FILENAME = "discovery-collab-animation.xml"
"""str: Output filename for NetAnim visualization"""


# =============================================================================
# MOBILE NODE INITIAL POSITIONS
# =============================================================================

MOBILE_NODE_POSITIONS = [
    (15.0, 20.0, 0.0),
    (35.0, 25.0, 0.0),
    (55.0, 15.0, 0.0),
    (25.0, 35.0, 0.0),
]
"""List[Tuple[float, float, float]]: Default (x, y, z) positions for mobile nodes"""

