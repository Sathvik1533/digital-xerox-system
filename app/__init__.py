"""
Digital Xerox & Stationery Ordering System
FastAPI Modular Monolith
"""
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("digital-xerox-system")
except PackageNotFoundError:
    __version__ = "0.1.0"
