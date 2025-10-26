"""
Module capability management system.
Handles tracking, validation, and management of module capabilities.
"""
from typing import Dict, Set, Optional, List
from enum import Enum, auto

from .modules import BaseModule, ModuleCapability
from .detection import ModuleType, ModuleDetector
from .hardware import HardwareInterface

class CapabilityRequirement(Enum):
    """Requirement level for a capability"""
    REQUIRED = auto()
    OPTIONAL = auto()

class CapabilityManager:
    """
    Manages and validates module capabilities.
    Tracks required and optional capabilities for different module types
    and provides capability validation and verification.
    """
    
    def __init__(self):
        """Initialize capability requirements for different module types"""
        self._requirements: Dict[ModuleType, Dict[ModuleCapability, CapabilityRequirement]] = {
            ModuleType.SFF: {
                ModuleCapability.TEMPERATURE_MONITORING: CapabilityRequirement.REQUIRED,
                ModuleCapability.VOLTAGE_MONITORING: CapabilityRequirement.REQUIRED,
                ModuleCapability.TX_BIAS_MONITORING: CapabilityRequirement.OPTIONAL,
                ModuleCapability.TX_POWER_MONITORING: CapabilityRequirement.OPTIONAL,
                ModuleCapability.RX_POWER_MONITORING: CapabilityRequirement.OPTIONAL,
                ModuleCapability.TX_DISABLE: CapabilityRequirement.OPTIONAL,
                ModuleCapability.TX_FAULT: CapabilityRequirement.OPTIONAL,
                ModuleCapability.RX_LOS: CapabilityRequirement.OPTIONAL,
                ModuleCapability.ALARM_THRESHOLDS: CapabilityRequirement.OPTIONAL
            },
            ModuleType.CMIS: {
                ModuleCapability.TEMPERATURE_MONITORING: CapabilityRequirement.REQUIRED,
                ModuleCapability.VOLTAGE_MONITORING: CapabilityRequirement.REQUIRED,
                ModuleCapability.PAGE_SELECT: CapabilityRequirement.REQUIRED,
                ModuleCapability.TX_BIAS_MONITORING: CapabilityRequirement.OPTIONAL,
                ModuleCapability.TX_POWER_MONITORING: CapabilityRequirement.OPTIONAL,
                ModuleCapability.RX_POWER_MONITORING: CapabilityRequirement.OPTIONAL,
                ModuleCapability.TX_DISABLE: CapabilityRequirement.OPTIONAL,
                ModuleCapability.TX_FAULT: CapabilityRequirement.OPTIONAL,
                ModuleCapability.RX_LOS: CapabilityRequirement.OPTIONAL,
                ModuleCapability.PROGRAMMABLE_POWER: CapabilityRequirement.OPTIONAL,
                ModuleCapability.PROGRAMMABLE_RATES: CapabilityRequirement.OPTIONAL,
                ModuleCapability.ALARM_THRESHOLDS: CapabilityRequirement.OPTIONAL
            }
        }
    
    def get_required_capabilities(self, module_type: ModuleType) -> Set[ModuleCapability]:
        """
        Get the set of required capabilities for a module type.
        
        Args:
            module_type: The type of module
            
        Returns:
            Set of required capabilities
        """
        if module_type not in self._requirements:
            return set()
        
        return {
            cap for cap, req in self._requirements[module_type].items()
            if req == CapabilityRequirement.REQUIRED
        }
    
    def get_optional_capabilities(self, module_type: ModuleType) -> Set[ModuleCapability]:
        """
        Get the set of optional capabilities for a module type.
        
        Args:
            module_type: The type of module
            
        Returns:
            Set of optional capabilities
        """
        if module_type not in self._requirements:
            return set()
        
        return {
            cap for cap, req in self._requirements[module_type].items()
            if req == CapabilityRequirement.OPTIONAL
        }
    
    def validate_module(self, module: BaseModule) -> Dict[str, List[ModuleCapability]]:
        """
        Validate a module's capabilities against requirements.
        
        Args:
            module: The module to validate
            
        Returns:
            Dictionary containing:
            - 'missing_required': List of required capabilities that are missing
            - 'supported_optional': List of optional capabilities that are supported
            - 'unsupported_optional': List of optional capabilities that are not supported
        """
        module_type = module.get_identification().type
        supported = module.get_capabilities()
        
        required = self.get_required_capabilities(module_type)
        optional = self.get_optional_capabilities(module_type)
        
        missing_required = [cap for cap in required if cap not in supported]
        supported_optional = [cap for cap in optional if cap in supported]
        unsupported_optional = [cap for cap in optional if cap not in supported]
        
        return {
            'missing_required': missing_required,
            'supported_optional': supported_optional,
            'unsupported_optional': unsupported_optional
        }
    
    def verify_capability(self, module: BaseModule, capability: ModuleCapability) -> bool:
        """
        Verify if a specific capability is supported and functional.
        
        Args:
            module: The module to verify
            capability: The capability to verify
            
        Returns:
            True if the capability is supported and functional, False otherwise
        """
        if not module.has_capability(capability):
            return False
            
        # Implement specific verification tests for each capability
        try:
            if capability == ModuleCapability.TEMPERATURE_MONITORING:
                status = module.get_status()
                return status.temperature is not None
                
            elif capability == ModuleCapability.VOLTAGE_MONITORING:
                status = module.get_status()
                return status.voltage is not None
                
            elif capability in (ModuleCapability.TX_POWER_MONITORING, 
                             ModuleCapability.RX_POWER_MONITORING,
                             ModuleCapability.TX_BIAS_MONITORING):
                status = module.get_status()
                return bool(status.tx_power or status.rx_power or status.tx_bias)
                
            elif capability == ModuleCapability.ALARM_THRESHOLDS:
                config = module.get_configuration()
                return 'thresholds' in config
                
            # Add more specific verification tests as needed
                
            return True  # Default to True for capabilities without specific tests
            
        except Exception:
            return False  # If testing the capability fails, consider it non-functional
    
    def describe_capability(self, capability: ModuleCapability) -> str:
        """
        Get a human-readable description of a capability.
        
        Args:
            capability: The capability to describe
            
        Returns:
            Description of the capability
        """
        descriptions = {
            ModuleCapability.TEMPERATURE_MONITORING: 
                "Monitor module temperature",
            ModuleCapability.VOLTAGE_MONITORING:
                "Monitor supply voltage",
            ModuleCapability.TX_BIAS_MONITORING:
                "Monitor transmitter bias current",
            ModuleCapability.TX_POWER_MONITORING:
                "Monitor transmitter optical power",
            ModuleCapability.RX_POWER_MONITORING:
                "Monitor receiver optical power",
            ModuleCapability.PAGE_SELECT:
                "Select memory pages for extended functions",
            ModuleCapability.TX_DISABLE:
                "Enable/disable transmitter",
            ModuleCapability.TX_FAULT:
                "Monitor transmitter fault status",
            ModuleCapability.RX_LOS:
                "Monitor receiver loss of signal",
            ModuleCapability.PROGRAMMABLE_POWER:
                "Configure module power settings",
            ModuleCapability.PROGRAMMABLE_RATES:
                "Configure data rates and operating modes",
            ModuleCapability.ALARM_THRESHOLDS:
                "Configure and monitor alarm thresholds"
        }
        
        return descriptions.get(capability, "Unknown capability")