"""
Base class for pluggable module implementations.
Defines the common interface and functionality for all module types.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Set

from ..hardware import HardwareInterface
from ..detection import ModuleType
from ..memory_map import CMISRegisters, SFFRegisters

class ModuleCapability(Enum):
    """Enumeration of possible module capabilities"""
    TEMPERATURE_MONITORING = auto()
    VOLTAGE_MONITORING = auto()
    TX_BIAS_MONITORING = auto()
    TX_POWER_MONITORING = auto()
    RX_POWER_MONITORING = auto()
    PAGE_SELECT = auto()
    RATE_SELECT = auto()
    TX_DISABLE = auto()
    TX_FAULT = auto()
    RX_LOS = auto()
    PROGRAMMABLE_POWER = auto()
    PROGRAMMABLE_RATES = auto()
    ALARM_THRESHOLDS = auto()

@dataclass
class ModuleStatus:
    """Represents the current status of a module"""
    temperature: Optional[float] = None
    voltage: Optional[float] = None
    tx_bias: Optional[List[float]] = None
    tx_power: Optional[List[float]] = None
    rx_power: Optional[List[float]] = None
    tx_fault: Optional[List[bool]] = None
    rx_los: Optional[List[bool]] = None
    alarms: Optional[Dict[str, bool]] = None
    warnings: Optional[Dict[str, bool]] = None

@dataclass
class ModuleIdentification:
    """Contains module identification information"""
    type: ModuleType
    vendor_name: str
    part_number: str
    serial_number: str
    revision: str
    date_code: Optional[str] = None
    nominal_bit_rate: Optional[float] = None
    max_case_temp: Optional[float] = None

class BaseModule(ABC):
    """
    Abstract base class for pluggable modules.
    
    This class defines the common interface that all module implementations
    must provide, regardless of whether they are SFF or CMIS based.
    """
    
    def __init__(self, hardware: HardwareInterface):
        """
        Initialize the module with a hardware interface.
        
        Args:
            hardware: The hardware interface for communicating with the module
        """
        self.hw = hardware
        self._required_capabilities: Set[ModuleCapability] = set()
        self._optional_capabilities: Set[ModuleCapability] = set()
        self._supported_capabilities: Set[ModuleCapability] = set()
        
    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the module after power-up or reset.
        This should perform any necessary setup and capability detection.
        
        Raises:
            RuntimeError: If initialization fails
        """
        pass
    
    @abstractmethod
    def get_identification(self) -> ModuleIdentification:
        """
        Get the module's identification information.
        
        Returns:
            Module identification information
        """
        pass
    
    @abstractmethod
    def get_status(self) -> ModuleStatus:
        """
        Get the current status of the module.
        
        Returns:
            Current module status
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> Set[ModuleCapability]:
        """
        Get the set of capabilities supported by this module.
        
        Returns:
            Set of supported capabilities
        """
        return self._supported_capabilities
    
    def has_capability(self, capability: ModuleCapability) -> bool:
        """
        Check if a specific capability is supported.
        
        Args:
            capability: The capability to check for
            
        Returns:
            True if the capability is supported, False otherwise
        """
        return capability in self._supported_capabilities
    
    def validate_capabilities(self) -> bool:
        """
        Validate that all required capabilities are supported.
        
        Returns:
            True if all required capabilities are supported, False otherwise
        """
        return self._required_capabilities.issubset(self._supported_capabilities)
    
    @abstractmethod
    def reset(self) -> None:
        """
        Reset the module to its default state.
        This should perform a soft reset if available, or a hard reset if necessary.
        
        Raises:
            RuntimeError: If reset fails
        """
        pass
    
    @abstractmethod
    def get_configuration(self) -> Dict[str, Any]:
        """
        Get the current module configuration.
        
        Returns:
            Dictionary containing current configuration parameters
        """
        pass
    
    @abstractmethod
    def set_configuration(self, config: Dict[str, Any]) -> None:
        """
        Apply a configuration to the module.
        
        Args:
            config: Dictionary of configuration parameters to apply
            
        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If configuration fails
        """
        pass
    
    def __str__(self) -> str:
        """Get a string representation of the module"""
        try:
            ident = self.get_identification()
            return f"{ident.type.name} Module: {ident.vendor_name} {ident.part_number} Rev {ident.revision}"
        except Exception:
            return f"Unknown Module"