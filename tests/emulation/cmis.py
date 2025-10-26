"""
CMIS module emulator implementation.
Emulates modules that follow the Common Management Interface Specification.
"""
import random
from typing import Dict, List, Optional, Union
from .base import EmulatedModule, ModuleConfig, EmulationError

class CMISEmulatedModule(EmulatedModule):
    """
    Emulates a CMIS-compliant module.
    Implements memory pages and control interfaces according to the CMIS specification.
    """
    # Constants for monitoring registers
    _SFF8024_ATTR_TX_POWER_OFFSET = 0x20
    _SFF8024_ATTR_RX_POWER_OFFSET = 0x30
    _SFF8024_ATTR_TX_BIAS_OFFSET = 0x40
    
    # Class-level type annotations
    _tx_bias_ma: List[float]
    _tx_power_mw: List[float]
    _rx_power_mw: List[float]
    
    # Class-level variable for type hints
    _tx_bias_ma: List[float]
    _tx_power_mw: List[float]
    _rx_power_mw: List[float]
    
    def __init__(self, config: ModuleConfig):
        """Initialize CMIS module emulator"""
        # Initialize member variables before calling parent class
        self._tx_disable_mask = 0x00
        self._tx_fault_mask = 0x00
        self._rx_los_mask = 0x00
        self._active_application = 1  # Default application
        self._power_class = 1  # Default power class
        self._temperature = 25.0  # Default temperature
        self._voltage = 3.3  # Default voltage
        
        # Initialize arrays for monitoring values
        init_value = 0.0
        if not config.media_type.name.startswith('COPPER'):
            init_values = {"bias": 30.0, "tx_power": 0.5, "rx_power": 0.4}
        else:
            init_values = {"bias": 0.0, "tx_power": 0.0, "rx_power": 0.0}
            
        self._tx_bias_ma = [init_values["bias"]] * config.num_channels
        self._tx_power_mw = [init_values["tx_power"]] * config.num_channels  
        self._rx_power_mw = [init_values["rx_power"]] * config.num_channels
        
        # Call parent class initialization
        super().__init__(config)
        
    def initialize_channels(self) -> None:
        """Initialize per-channel values"""
        # Set initial values based on module type
        if not self.config.media_type.name.startswith('COPPER'):
            init_values = {"bias": 30.0, "tx_power": 0.5, "rx_power": 0.4}
        else:
            init_values = {"bias": 0.0, "tx_power": 0.0, "rx_power": 0.0}
            
        # Initialize arrays with proper values
        self._tx_bias_ma = [init_values["bias"]] * self.config.num_channels
        self._tx_power_mw = [init_values["tx_power"]] * self.config.num_channels  
        self._rx_power_mw = [init_values["rx_power"]] * self.config.num_channels
    
    def _initialize_memory_map(self) -> None:
        """Initialize the CMIS memory map"""
        # Lower Memory Page (Page 0)
        self.memory_map.write_byte(0x00, self.config.identifier)  # Identifier
        self._write_string(0x10, self.config.vendor_name, 16)
        self._write_string(0x20, self.config.part_number, 16)
        self._write_string(0x30, self.config.revision, 2)
        self._write_string(0x40, self.config.serial_number, 16)
        
        # Status and Control Pages
        for page in [0x80, 0x81, 0x82, 0x83, 0x84, 0x85]:
            self.memory_map.add_page(page)
        
        # Module Features (Page 0x80)
        self.memory_map.select_page(0x80)
        features = 0x00
        if not self.config.media_type.name.startswith('COPPER'):
            features |= 0x07  # Power monitoring supported
        if len(self.config.supported_rates) > 1:
            features |= 0x20  # Programmable rates supported
        self.memory_map.write_byte(0x02, features)
        
        # Application Advertisement (Page 0x10)
        self.memory_map.add_page(0x10)
        self.memory_map.select_page(0x10)
        
        # Write supported rates as application codes
        for i, rate in enumerate(self.config.supported_rates):
            app_code = self._encode_application(rate)
            self.memory_map.write_word(0x20 + (i * 2), app_code)
        
        # Data Path Configuration (Page 0x10)
        self.memory_map.write_byte(0x10, self._power_class)
        self.memory_map.write_word(0x11, int(self.config.max_power_draw * 10))  # Power in 100mW units
        
        # Status/Monitor Pages
        self.memory_map.add_page(0x11)  # Data Path Status/Monitor
        
        # Update initial monitoring values
        self.update_monitoring()
    
    def update_monitoring(self) -> None:
        """Update monitoring values in memory map"""
        # Initialize arrays if needed
        if not isinstance(self._tx_power_mw, list):
            self.initialize_channels()
            
        # Add some random variation
        temp_variation = random.uniform(-0.5, 0.5)
        voltage_variation = random.uniform(-0.02, 0.02)
        
        # Update base page monitoring
        self.memory_map.select_page(0x00)
        self.memory_map.write_word(0x03, self._encode_temperature(self._temperature + temp_variation))
        self.memory_map.write_word(0x05, self._encode_voltage(self._voltage + voltage_variation))
        
        # Update per-lane monitoring if applicable
        if not self.config.media_type.name.startswith('COPPER'):
            self.memory_map.select_page(0x11)
            for i in range(self.config.num_channels):
                base_addr = 0x10 + (i * 12)
                
                # Add variations and update array values
                bias_variation = random.uniform(-0.2, 0.2)
                power_variation = random.uniform(-0.01, 0.01)
                
                # Update array values with variations
                if not self._tx_disable_mask & (1 << i):
                    self._tx_power_mw[i] += power_variation
                    self._rx_power_mw[i] += power_variation
                    self._tx_bias_ma[i] += bias_variation
                
                # Write updated values to memory map
                self.memory_map.write_word(base_addr + 0,
                    self._encode_power(self._tx_power_mw[i]))
                self.memory_map.write_word(base_addr + 2,
                    self._encode_power(self._rx_power_mw[i]))
                self.memory_map.write_word(base_addr + 4,
                    self._encode_bias(self._tx_bias_ma[i]))
        
        # Update status flags
        self.memory_map.select_page(0x83)  # Flags page
        flags = 0x00
        # Add temperature and voltage alarm flags if needed
        if self._temperature > 70.0:
            flags |= 0x80  # Temperature high alarm
        if self._voltage > 3.5:
            flags |= 0x20  # Voltage high alarm
        self.memory_map.write_byte(0x00, flags)
    
    def set_tx_disable(self, channel: int, disable: bool) -> None:
        """Set TX disable state for a channel"""
        if not 0 <= channel < self.config.num_channels:
            raise EmulationError(f"Invalid channel number: {channel}")
        
        mask = 1 << channel
        if disable:
            self._tx_disable_mask |= mask
            self._tx_power_mw[channel] = 0.0
        else:
            self._tx_disable_mask &= ~mask
            self._tx_power_mw[channel] = 0.5
        
        self.update_monitoring()
    
    def set_application(self, app_code: int) -> None:
        """Set active application (data rate)"""
        # Verify application code is supported
        self.memory_map.select_page(0x10)
        supported = False
        for i in range(len(self.config.supported_rates)):
            if self.memory_map.read_word(0x20 + (i * 2)) == app_code:
                supported = True
                break
        
        if not supported:
            raise EmulationError(f"Unsupported application code: {app_code}")
        
        self._active_application = app_code
        self.update_monitoring()
    
    def simulate_fault(self, channel: int, fault_type: str, state: bool) -> None:
        """Simulate various fault conditions on a specific channel"""
        if not 0 <= channel < self.config.num_channels:
            raise EmulationError(f"Invalid channel number: {channel}")
        
        if fault_type == 'tx_fault':
            mask = 1 << channel
            if state:
                self._tx_fault_mask |= mask
                self._tx_power_mw[channel] = 0.0
            else:
                self._tx_fault_mask &= ~mask
                if not self._tx_disable_mask & mask:
                    self._tx_power_mw[channel] = 0.5
        elif fault_type == 'rx_los':
            mask = 1 << channel
            if state:
                self._rx_los_mask |= mask
                self._rx_power_mw[channel] = 0.0
            else:
                self._rx_los_mask &= ~mask
                if not (self._tx_disable_mask & mask or self._tx_fault_mask & mask):
                    self._rx_power_mw[channel] = 0.4
        else:
            raise EmulationError(f"Unknown fault type: {fault_type}")
            
        # Update the memory map but prevent random variations
        self.memory_map.select_page(0x11)
        base_addr = 0x10 + (channel * 12)
        self.memory_map.write_word(base_addr + 0, self._encode_power(self._tx_power_mw[channel]))
        self.memory_map.write_word(base_addr + 2, self._encode_power(self._rx_power_mw[channel]))
        self.memory_map.write_word(base_addr + 4, self._encode_bias(self._tx_bias_ma[channel]))
    
    def set_temperature(self, temperature: float) -> None:
        """Set module temperature"""
        self._temperature = temperature
        self.update_monitoring()
    
    def set_voltage(self, voltage: float) -> None:
        """Set module voltage"""
        self._voltage = voltage
        self.update_monitoring()
    
    def get_active_application(self) -> int:
        """Get the currently active application"""
        return self._active_application
    
    def _encode_application(self, rate: float) -> int:
        """Encode a bit rate as a CMIS application code"""
        # This is a simplified encoding - real modules use standardized application codes
        if rate == 10.0:
            return 0x1
        elif rate == 25.0:
            return 0x2
        elif rate == 40.0:
            return 0x3
        elif rate == 100.0:
            return 0x4
        elif rate == 200.0:
            return 0x5
        elif rate == 400.0:
            return 0x6
        else:
            return 0x0