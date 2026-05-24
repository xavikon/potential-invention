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
from .modules.state_machine import ModuleStateMachine, ModuleState, DataPathState, StateMachineError
from .hardware.error_injection import ErrorInjector, ErrorInjectionError
from .hardware.bridge import I2CBridgeServer
from .hardware.emulator_client import EmulatorClient, EmulatorClientError

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
    'CapabilityRequirement',
    
    # State Machine Emulation
    'ModuleStateMachine',
    'ModuleState',
    'DataPathState',
    'StateMachineError',
    
    # Error Injection
    'ErrorInjector',
    'ErrorInjectionError',
    
    # TCP Bridge Server
    'I2CBridgeServer',

    # TCP Client (drop-in hardware interface replacement)
    'EmulatorClient',
    'EmulatorClientError'
]

__version__ = '0.1.0'