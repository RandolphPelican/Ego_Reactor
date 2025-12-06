#!/usr/bin/env python3
"""Quick launcher for Ego_Reactor demo."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from Ego_Reactor.demo.run_demo import main

if __name__ == "__main__":
    main()
