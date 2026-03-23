"""OpenDivination — Quantum-entropy oracle SDK for divination systems."""

from opendivination.config import (
    OpenDivinationConfig,
    configured_default_source,
    configured_remote_source_api_key,
    default_config_path,
    load_config,
    save_config,
)

__version__ = "0.1.0"
__author__ = "Amenti Labs"

__all__ = [
    "OpenDivinationConfig",
    "configured_default_source",
    "configured_remote_source_api_key",
    "default_config_path",
    "load_config",
    "save_config",
]
