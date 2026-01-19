#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NS-3 Discovery and Collaboration Protocol Simulation - Entry Point

Simplified entry point using modular architecture.
See lib/ directory for component implementations.

Usage:
    ./ns3 run "scenarios/discovery_collab_simulation.py"
    ./ns3 run "scenarios/discovery_collab_simulation.py -- --simTime=100 --numMobile=8"
"""

import sys
import os

# Add parent directory to path to import lib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lib.simulation import main

if __name__ == "__main__":
    sys.exit(main(sys.argv))
