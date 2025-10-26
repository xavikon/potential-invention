"""
SFF module implementation.
Supports SFF-8472 and SFF-8636 compliant modules.
"""
import struct
import time
from typing import Dict, List, Optional, Set, Any, Tuple, cast

from ..hardware import HardwareInterface, GPIOSignal
from ..memory_map import SFFRegisters
from ..detection import ModuleType
from .base import BaseModule, ModuleCapability, ModuleStatus, ModuleIdentification

class SFFModule(BaseModule):
    """Implementation of SFF-compliant optical modules"""
    
    def __init__(self, hardware: HardwareInterface):
        """
        Initialize an SFF module instance.
        
        Args:
            hardware: Hardware interface for module communication
        """
        super().__init__(hardware)
        
        # Define required capabilities for SFF modules
        self._required_capabilities = {
            ModuleCapability.TEMPERATURE_MONITORING,
            ModuleCapability.VOLTAGE_MONITORING
        }
        
        # Define optional capabilities
        self._optional_capabilities = {
            ModuleCapability.TX_BIAS_MONITORING,
            ModuleCapability.TX_POWER_MONITORING,
            ModuleCapability.RX_POWER_MONITORING,
            ModuleCapability.TX_DISABLE,
            ModuleCapability.TX_FAULT,
            ModuleCapability.RX_LOS,
            ModuleCapability.ALARM_THRESHOLDS
        }
    
    def initialize(self) -> None:
        """
        Initialize the SFF module.
        Performs basic setup and capability detection.
        
        Raises:
            RuntimeError: If initialization fails
        """
        # Reset the module
        self.reset()
        
        # Wait for module to stabilize
        time.sleep(0.5)
        
        # Detect supported capabilities
        self._detect_capabilities()
        
        # Validate required capabilities
        if not self.validate_capabilities():
            missing = self._required_capabilities - self._supported_capabilities
            raise RuntimeError(f"Module missing required capabilities: {missing}")
    
    def get_identification(self) -> ModuleIdentification:
        """
        Get the module's identification information.
        
        Returns:
            Module identification information
        
        Raises:
            RuntimeError: If reading identification fails
        """
        try:
            # Read basic identification fields
            vendor_name = self._read_string(SFFRegisters.VENDOR_NAME.offset, 16)
            part_number = self._read_string(SFFRegisters.VENDOR_PN.offset, 16)
            serial_number = self._read_string(SFFRegisters.VENDOR_SN.offset, 16)
            revision = self._read_string(SFFRegisters.VENDOR_REV.offset, 4)
            
            return ModuleIdentification(
                type=ModuleType.SFF,
                vendor_name=vendor_name.strip(),
                part_number=part_number.strip(),
                serial_number=serial_number.strip(),
                revision=revision.strip()
            )
        except Exception as e:
            raise RuntimeError(f"Failed to read module identification: {str(e)}")
    
    def get_status(self) -> ModuleStatus:
        """
        Get the current status of the module.
        
        Returns:
            Current module status
        
        Raises:
            RuntimeError: If reading status fails
        """
        status = ModuleStatus()
        
        try:
            # Read temperature (mandatory capability)
            raw_temp = self._read_word(SFFRegisters.TEMPERATURE.offset)
            status.temperature = self._decode_temperature(raw_temp)
            
            # Read voltage (mandatory capability)
            raw_voltage = self._read_word(SFFRegisters.VOLTAGE.offset)
            status.voltage = self._decode_voltage(raw_voltage)
            
            # Read optional monitoring values if supported
            if self.has_capability(ModuleCapability.TX_BIAS_MONITORING):
                status.tx_bias = [self._decode_bias(self._read_word(SFFRegisters.TX_BIAS.offset))]
                
            if self.has_capability(ModuleCapability.TX_POWER_MONITORING):
                status.tx_power = [self._decode_power(self._read_word(SFFRegisters.TX_POWER.offset))]
                
            if self.has_capability(ModuleCapability.RX_POWER_MONITORING):
                status.rx_power = [self._decode_power(self._read_word(SFFRegisters.RX_POWER.offset))]
            
            return status
            
        except Exception as e:
            raise RuntimeError(f"Failed to read module status: {str(e)}")
    
    def get_capabilities(self) -> Set[ModuleCapability]:
        """
        Get the set of capabilities supported by this module.
        
        Returns:
            Set of supported capabilities
        """
        return self._supported_capabilities
    
    def reset(self) -> None:
        """
        Reset the module using the hardware reset signal.
        
        Raises:
            RuntimeError: If reset fails
        """
        try:
            self.hw.reset_module()
            time.sleep(0.5)  # Wait for module to stabilize
        except Exception as e:
            raise RuntimeError(f"Failed to reset module: {str(e)}")
    
    def get_configuration(self) -> Dict[str, Any]:
        """
        Get the current module configuration.
        
        Returns:
            Dictionary containing current configuration parameters
        """
        config: Dict[str, Any] = {}
        
        # Read TX disable state if supported
        if self.has_capability(ModuleCapability.TX_DISABLE):
            config["tx_disable"] = self._get_tx_disable()
            
        # Read alarm thresholds if supported
        if self.has_capability(ModuleCapability.ALARM_THRESHOLDS):
            config["thresholds"] = self._get_alarm_thresholds()
        
        return config
    
    def set_configuration(self, config: Dict[str, Any]) -> None:
        """
        Apply a configuration to the module.
        
        Args:
            config: Dictionary of configuration parameters to apply
            
        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If configuration fails
        """
        # Apply TX disable state if supported and provided
        if "tx_disable" in config:
            if not self.has_capability(ModuleCapability.TX_DISABLE):
                raise ValueError("TX disable not supported by this module")
            self._set_tx_disable(config["tx_disable"])
            
        # Apply alarm thresholds if supported and provided
        if "thresholds" in config:
            if not self.has_capability(ModuleCapability.ALARM_THRESHOLDS):
                raise ValueError("Alarm thresholds not supported by this module")
            self._set_alarm_thresholds(config["thresholds"])
    
    def _detect_capabilities(self) -> None:
        """
        Detect which optional capabilities are supported by the module.
        Updates the _supported_capabilities set.
        """
        # Start with required capabilities
        self._supported_capabilities = self._required_capabilities.copy()
        
        try:
            # Read diagnostic monitoring type
            diag_type = self.hw.read_register(0x5C)  # SFF-8472 diagnostic monitoring type
            
            # Check for optional monitoring capabilities
            if diag_type & 0x40:  # Digital diagnostic monitoring implemented
                self._supported_capabilities.update({
                    ModuleCapability.TX_BIAS_MONITORING,
                    ModuleCapability.TX_POWER_MONITORING,
                    ModuleCapability.RX_POWER_MONITORING
                })
            
            if diag_type & 0x08:  # External calibration
                self._supported_capabilities.add(ModuleCapability.ALARM_THRESHOLDS)
            
            # Check for optional control capabilities
            control_bits = self.hw.read_register(0x6E)  # Enhanced options
            if control_bits & 0x40:  # TX_DISABLE implemented
                self._supported_capabilities.add(ModuleCapability.TX_DISABLE)
            if control_bits & 0x20:  # TX_FAULT implemented
                self._supported_capabilities.add(ModuleCapability.TX_FAULT)
            if control_bits & 0x10:  # RX_LOS implemented
                self._supported_capabilities.add(ModuleCapability.RX_LOS)
                
        except Exception as e:
            # Log warning but continue - we'll work with just required capabilities
            print(f"Warning: Error detecting optional capabilities: {str(e)}")
    
    def _read_string(self, start_address: int, length: int) -> str:
        """Read a string from consecutive memory addresses"""
        bytes_data = []
        for offset in range(length):
            try:
                byte = self.hw.read_register(start_address + offset)
                bytes_data.append(byte)
            except Exception:
                break
                
        return "".join(chr(b) for b in bytes_data if 32 <= b <= 126)
    
    def _read_word(self, address: int) -> int:
        """Read a 16-bit word from memory"""
        msb = self.hw.read_register(address)
        lsb = self.hw.read_register(address + 1)
        return (msb << 8) | lsb
    
    def _decode_temperature(self, raw: int) -> float:
        """Decode raw temperature value to degrees Celsius"""
        return raw * 1.0 / 256.0
    
    def _decode_voltage(self, raw: int) -> float:
        """Decode raw voltage value to volts"""
        return raw * 0.1 / 1000.0
    
    def _decode_bias(self, raw: int) -> float:
        """Decode raw bias current value to mA"""
        return raw * 2.0 / 1000.0
    
    def _decode_power(self, raw: int) -> float:
        """Decode raw optical power value to mW"""
        return raw * 0.1 / 1000.0
    
    def _get_tx_disable(self) -> bool:
        """Get the current TX disable state"""
        control = self.hw.read_register(0x6E)
        return bool(control & 0x40)
    
    def _set_tx_disable(self, disable: bool) -> None:
        """Set the TX disable state"""
        control = self.hw.read_register(0x6E)
        if disable:
            control |= 0x40
        else:
            control &= ~0x40
        self.hw.write_register(0x6E, control)
    
    def _get_alarm_thresholds(self) -> Dict[str, float]:
        """Read all alarm thresholds"""
        thresholds = {}
        
        # Temperature thresholds
        thresholds["temp_high"] = self._decode_temperature(self._read_word(SFFRegisters.TEMP_HIGH_ALARM.offset))
        thresholds["temp_low"] = self._decode_temperature(self._read_word(SFFRegisters.TEMP_LOW_ALARM.offset))
        
        # Voltage thresholds
        thresholds["voltage_high"] = self._decode_voltage(self._read_word(SFFRegisters.VOLTAGE_HIGH_ALARM.offset))
        thresholds["voltage_low"] = self._decode_voltage(self._read_word(SFFRegisters.VOLTAGE_LOW_ALARM.offset))
        
        return thresholds
    
    def _set_alarm_thresholds(self, thresholds: Dict[str, float]) -> None:
        """Set alarm thresholds"""
        # This would need careful implementation to properly encode values
        # and write them to the correct registers
        raise NotImplementedError("Setting alarm thresholds not yet implemented")