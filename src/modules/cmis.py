"""
CMIS module implementation.
Supports modules compliant with Common Management Interface Specification.
"""
import struct
import time
from typing import Dict, List, Optional, Set, Any, Tuple, cast

from ..hardware import HardwareInterface, GPIOSignal
from ..memory_map import CMISRegisters
from ..detection import ModuleType
from .base import BaseModule, ModuleCapability, ModuleStatus, ModuleIdentification

class CMISModule(BaseModule):
    """Implementation of CMIS-compliant optical modules"""
    
    def __init__(self, hardware: HardwareInterface):
        """
        Initialize a CMIS module instance.
        
        Args:
            hardware: Hardware interface for module communication
        """
        super().__init__(hardware)
        
        # Define required capabilities for CMIS modules
        self._required_capabilities = {
            ModuleCapability.TEMPERATURE_MONITORING,
            ModuleCapability.VOLTAGE_MONITORING,
            ModuleCapability.PAGE_SELECT
        }
        
        # Define optional capabilities
        self._optional_capabilities = {
            ModuleCapability.TX_BIAS_MONITORING,
            ModuleCapability.TX_POWER_MONITORING,
            ModuleCapability.RX_POWER_MONITORING,
            ModuleCapability.TX_DISABLE,
            ModuleCapability.TX_FAULT,
            ModuleCapability.RX_LOS,
            ModuleCapability.PROGRAMMABLE_POWER,
            ModuleCapability.PROGRAMMABLE_RATES,
            ModuleCapability.ALARM_THRESHOLDS
        }
        
        self._current_page = 0
    
    def initialize(self) -> None:
        """
        Initialize the CMIS module.
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
        
        # Initialize to lower page
        self._select_page(0)
    
    def get_identification(self) -> ModuleIdentification:
        """
        Get the module's identification information.
        
        Returns:
            Module identification information
        
        Raises:
            RuntimeError: If reading identification fails
        """
        try:
            # Ensure we're on the correct page
            self._select_page(0)
            
            # Read basic identification fields
            vendor_name = self._read_string(CMISRegisters.VENDOR_NAME.offset, 16)
            part_number = self._read_string(CMISRegisters.VENDOR_PART_NUMBER.offset, 16)
            serial_number = self._read_string(CMISRegisters.VENDOR_SERIAL_NUMBER.offset, 16)
            revision = self._read_string(CMISRegisters.VENDOR_REVISION.offset, 2)
            
            return ModuleIdentification(
                type=ModuleType.CMIS,
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
            # Read status from page 0
            self._select_page(0)
            
            # Read temperature (mandatory)
            raw_temp = self._read_word(CMISRegisters.TEMPERATURE.offset)
            status.temperature = self._decode_temperature(raw_temp)
            
            # Read voltage (mandatory)
            raw_voltage = self._read_word(CMISRegisters.VOLTAGE.offset)
            status.voltage = self._decode_voltage(raw_voltage)
            
            # Read lane status if supported
            if self.has_capability(ModuleCapability.TX_POWER_MONITORING):
                status.tx_power = []
                status.rx_power = []
                status.tx_bias = []
                
                # Read per-lane status from status/monitor pages
                self._select_page(0x11)  # Data Path Status/Monitor
                for lane in range(8):  # CMIS supports up to 8 lanes
                    base_addr = 0x10 + (lane * 12)
                    status.tx_power.append(self._decode_power(self._read_word(base_addr)))
                    status.rx_power.append(self._decode_power(self._read_word(base_addr + 2)))
                    status.tx_bias.append(self._decode_bias(self._read_word(base_addr + 4)))
            
            # Read flags and alarms
            if self.has_capability(ModuleCapability.ALARM_THRESHOLDS):
                self._select_page(CMISRegisters.FLAGS.page)
                flags = self._read_word(0x00)  # Flags register
                
                status.alarms = {
                    "temp_high": bool(flags & (1 << 7)),
                    "temp_low": bool(flags & (1 << 6)),
                    "voltage_high": bool(flags & (1 << 5)),
                    "voltage_low": bool(flags & (1 << 4))
                }
            
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
            self._current_page = 0  # Reset page tracking
        except Exception as e:
            raise RuntimeError(f"Failed to reset module: {str(e)}")
    
    def get_configuration(self) -> Dict[str, Any]:
        """
        Get the current module configuration.
        
        Returns:
            Dictionary containing current configuration parameters
        """
        config: Dict[str, Any] = {}
        
        try:
            # Read data path configuration
            self._select_page(CMISRegisters.DATA_PATH_CONTROL.page)
            config["data_path"] = self._read_word(CMISRegisters.DATA_PATH_CONTROL.offset)
            
            # Read power configuration if supported
            if self.has_capability(ModuleCapability.PROGRAMMABLE_POWER):
                self._select_page(0x10)  # Application Advertisement
                config["power_class"] = self.hw.read_register(0x10)
                config["max_power"] = self._read_word(0x11)
            
            # Read rate configuration if supported
            if self.has_capability(ModuleCapability.PROGRAMMABLE_RATES):
                self._select_page(0x10)  # Application Advertisement
                config["supported_rates"] = []
                for i in range(8):  # Up to 8 application codes
                    app_code = self._read_word(0x20 + (i * 2))
                    if app_code != 0:
                        config["supported_rates"].append(app_code)
            
            return config
            
        except Exception as e:
            raise RuntimeError(f"Failed to read configuration: {str(e)}")
    
    def set_configuration(self, config: Dict[str, Any]) -> None:
        """
        Apply a configuration to the module.
        
        Args:
            config: Dictionary of configuration parameters to apply
            
        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If configuration fails
        """
        try:
            # Apply data path configuration if provided
            if "data_path" in config:
                self._select_page(CMISRegisters.DATA_PATH_CONTROL.page)
                self.hw.write_register(CMISRegisters.DATA_PATH_CONTROL.offset, config["data_path"])
            
            # Apply power configuration if supported and provided
            if "power_class" in config:
                if not self.has_capability(ModuleCapability.PROGRAMMABLE_POWER):
                    raise ValueError("Programmable power not supported")
                self._select_page(0x10)
                self.hw.write_register(0x10, config["power_class"])
            
            # Apply rate configuration if supported and provided
            if "rate" in config:
                if not self.has_capability(ModuleCapability.PROGRAMMABLE_RATES):
                    raise ValueError("Programmable rates not supported")
                self._select_page(0x10)
                self.hw.write_register(0x12, config["rate"])
                
        except Exception as e:
            raise RuntimeError(f"Failed to apply configuration: {str(e)}")
    
    def _detect_capabilities(self) -> None:
        """
        Detect which optional capabilities are supported by the module.
        Updates the _supported_capabilities set.
        """
        # Start with required capabilities
        self._supported_capabilities = self._required_capabilities.copy()
        
        try:
            # Read feature support from status page
            self._select_page(CMISRegisters.FEATURE_SUPPORT.page)
            features = self._read_word(CMISRegisters.FEATURE_SUPPORT.offset)
            
            # Check for monitoring capabilities
            if features & (1 << 0):  # Tx power monitoring
                self._supported_capabilities.add(ModuleCapability.TX_POWER_MONITORING)
            if features & (1 << 1):  # Rx power monitoring
                self._supported_capabilities.add(ModuleCapability.RX_POWER_MONITORING)
            if features & (1 << 2):  # Tx bias monitoring
                self._supported_capabilities.add(ModuleCapability.TX_BIAS_MONITORING)
                
            # Check for programmable features
            if features & (1 << 4):  # Programmable power
                self._supported_capabilities.add(ModuleCapability.PROGRAMMABLE_POWER)
            if features & (1 << 5):  # Programmable rates
                self._supported_capabilities.add(ModuleCapability.PROGRAMMABLE_RATES)
            if features & (1 << 6):  # Alarm thresholds
                self._supported_capabilities.add(ModuleCapability.ALARM_THRESHOLDS)
                
        except Exception as e:
            # Log warning but continue - we'll work with just required capabilities
            print(f"Warning: Error detecting optional capabilities: {str(e)}")
    
    def _select_page(self, page: int) -> None:
        """
        Select a memory page for subsequent reads/writes.
        
        Args:
            page: The page number to select
            
        Raises:
            RuntimeError: If page selection fails
        """
        if page == self._current_page:
            return
            
        try:
            # Write page number to page select register
            self.hw.write_register(0x7F, page)
            self._current_page = page
            time.sleep(0.05)  # Wait for page switch to complete
        except Exception as e:
            raise RuntimeError(f"Failed to select page {page}: {str(e)}")
    
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
        # CMIS temperature is signed 16-bit fixed point with 1/256 degree resolution
        if raw & 0x8000:  # Negative temperature
            raw = -((~raw + 1) & 0xFFFF)
        return raw / 256.0
    
    def _decode_voltage(self, raw: int) -> float:
        """Decode raw voltage value to volts"""
        # CMIS voltage is unsigned 16-bit fixed point with 100µV resolution
        return raw * 0.0001
    
    def _decode_bias(self, raw: int) -> float:
        """Decode raw bias current value to mA"""
        # CMIS current is unsigned 16-bit fixed point with 2µA resolution
        return raw * 0.002
    
    def _decode_power(self, raw: int) -> float:
        """Decode raw optical power value to mW"""
        # CMIS power is unsigned 16-bit fixed point with 0.1µW resolution
        return raw * 0.0001