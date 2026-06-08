"""OceanX — marine AIS + VHF receiver and tracker for HackRF."""

__version__ = "1.0.0"
__app_name__ = "OceanX"

from oceanx.app.sniffer import OceanXSniffer
from oceanx.config import SnifferConfig

__all__ = ["OceanXSniffer", "SnifferConfig", "__app_name__", "__version__"]
