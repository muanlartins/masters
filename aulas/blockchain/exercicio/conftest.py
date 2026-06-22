import os
import sys

# Garante que `import minichain` funcione rodando pytest de qualquer lugar.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
