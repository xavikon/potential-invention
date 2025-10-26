"""
Pluggable Module Management System
Provides interfaces and implementations for managing high-speed pluggable modules.
"""

from .hardware import HardwareInterface, GPIOSignal
from .detection import ModuleDetector, ModuleType
from .memory_map import CMISRegisters, SFFRegisters
from .modules import (
    BaseModule,
    ModuleCapability,
    ModuleStatus,
    ModuleIdentification,
    SFFModule,
    CMISModule
)
from .capabilities import CapabilityManager, CapabilityRequirement

__all__ = [
    # Hardware abstraction
    'HardwareInterface',
    'GPIOSignal',
    
    # Module detection
    'ModuleDetector',
    'ModuleType',
    
    # Memory maps
    'CMISRegisters',
    'SFFRegisters',
    
    # Module base types
    'BaseModule',
    'ModuleCapability',
    'ModuleStatus',
    'ModuleIdentification',
    
    # Module implementations
    'SFFModule',
    'CMISModule',
    
    # Capability management
    'CapabilityManager',
    'CapabilityRequirement'
]

__version__ = '0.1.0'