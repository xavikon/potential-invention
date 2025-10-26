"""!
@file sff.py
@brief SFF module emulator implementation.

This module provides emulation of SFF-8472 and SFF-8636 compliant modules.
It implements digital diagnostics monitoring (DDM), alarm thresholds,
and fault handling as specified in the standards.

The implementation supports:
- Register-based memory access on A0h and A2h pages
- Temperature and voltage monitoring
- Optical power and bias current monitoring
- Alarm and warning thresholds
- TX disable and fault conditions
- RX loss of signal detection

Key features:
- Real-time monitoring value updates with random variations
- Configurable alarm thresholds
- Complete fault condition simulation
- Vendor/device string management

Example usage:
@code
# Create and configure an SFF module
config = ModuleConfig(
    form_factor=FormFactor.SFP,
    module_type=ModuleType.SFP_PLUS,
    media_type=MediaType.SR,
    identifier=0x03,
    vendor_name="Test Vendor",
    part_number="TEST-001",
    serial_number="12345",
    revision="1.0",
    nominal_bit_rate=10.3125,
    max_case_temp=70.0,
    supported_rates=[10.3125],
    num_channels=1,
    max_power_draw=1.0,
    wavelength_nm=850.0
)

# Create module instance
module = SFFEmulatedModule(config)

# Simulate temperature change
module.set_temperature(45.0)

# Simulate fault condition
module.simulate_fault('tx_fault', True)
@endcode

@see EmulatedModule
@see ModuleConfig
"""
import random
import struct
from typing import Dict, List, Optional
from .base import EmulatedModule, ModuleConfig, EmulationError

class SFFEmulatedModule(EmulatedModule):
    """!
    Emulates an SFF-compliant module.
    
    This class implements a complete emulation of SFF-8472 and SFF-8636 compliant
    modules. It provides:
    - Full A0h and A2h page memory maps
    - Real-time monitoring with configurable values
    - Alarm threshold monitoring
    - TX disable control
    - Fault condition simulation
    
    The emulator maintains internal state for:
    - Temperature and voltage
    - TX bias current and optical power
    - RX optical power
    - TX disable state
    - Various fault conditions
    
    All monitoring values can be updated in real-time, and the emulator
    will automatically handle status bits, alarm flags, and value encoding
    according to the standards.
    """
    
    def __init__(self, config: ModuleConfig):
        """Initialize SFF module emulator"""
        super().__init__(config)
    
    def _initialize_memory_map(self) -> None:
        """!
        Initialize the SFF memory map.
        
        This method sets up the complete memory map for an SFF module including:
        - A0h page: Basic identification and capability info
        - A2h page: Diagnostic monitoring
        
        Memory map initialization includes:
        1. Creating required memory pages
        2. Writing identification information
        3. Setting up diagnostic monitoring capabilities
        4. Configuring alarm thresholds
        5. Initializing monitoring values
        
        The memory map follows either SFF-8472 (for SFP) or SFF-8636 (for QSFP)
        depending on the module configuration.
        
        @note This is called automatically by the constructor and during reset.
        """
        # Initialize pages
        self.add_memory_pages([0x00, 0x01, 0xA0, 0xA2])  # Add standard and diagnostic pages
        
        # Clear all memory pages first
        for page in [0x00, 0x01, 0xA0, 0xA2]:
            self.memory_map.select_page(page)
            for addr in range(256):
                self.memory_map.write_byte(addr, 0x00)
        
        # Select A0 page for writing basic information
        self.memory_map.select_page(0xA0)
        # Basic module information
        self.memory_map.write_byte(0x00, self.config.identifier)  # Identifier
        self._write_string(0x14, self.config.vendor_name, 16)
        self._write_string(0x28, self.config.part_number, 16)
        self._write_string(0x38, self.config.revision, 4)
        self._write_string(0x44, self.config.serial_number, 16)
        
        # Switch to A2 page for diagnostics setup
        self.memory_map.select_page(0xA2)
        
        # Enable digital diagnostics
        self.memory_map.write_byte(0x5C, 0x40)  # Digital diagnostics implemented
        
        # Initial monitoring values
        self.update_monitoring()
        
        # Basic module information
        self.memory_map.write_byte(0x00, self.config.identifier)  # Identifier
        self.memory_map.write_byte(0x01, 0x00)  # Status
        self._write_string(0x14, self.config.vendor_name, 16)
        self._write_string(0x28, self.config.part_number, 16)
        self._write_string(0x38, self.config.revision, 4)
        self._write_string(0x44, self.config.serial_number, 16)
        
        # Module characteristics
        self.memory_map.write_byte(0x3C, int(self.config.nominal_bit_rate))
        
        if self.config.length_meters is not None:
            self.memory_map.write_byte(0x12, int(self.config.length_meters))
        if self.config.wavelength_nm is not None:
            wavelength = int(self.config.wavelength_nm / 20)  # Convert to 20nm units
            self.memory_map.write_word(0x3C, wavelength)
        
        # Select A2 page for diagnostics
        self.memory_map.select_page(0xA2)
        
        # Diagnostic capabilities
        self.memory_map.write_byte(0x5C, 0x40)  # Digital diagnostics implemented
        
        # Alarm thresholds (example values)
        self.memory_map.write_word(0x00, self._encode_temperature(75.0))  # Temp high alarm
        self.memory_map.write_word(0x02, self._encode_temperature(-5.0))  # Temp low alarm
        self.memory_map.write_word(0x04, self._encode_voltage(3.6))  # Voltage high alarm
        self.memory_map.write_word(0x06, self._encode_voltage(3.0))  # Voltage low alarm
        
        # Update initial monitoring values
        self.update_monitoring()
    
    def update_monitoring(self) -> None:
        """!
        Update monitoring values in memory map.
        
        Updates all diagnostic monitoring values in the A2h page including:
        - Temperature (bytes 96-97)
        - Voltage (bytes 98-99)
        - TX bias current (bytes 100-101)
        - TX output power (bytes 102-103)
        - RX input power (bytes 104-105)
        
        Each value is updated with small random variations to simulate
        real-world behavior. The variation ranges are:
        - Temperature: ±0.05°C
        - Voltage: ±0.01V
        - Bias current: ±0.2mA
        - Optical power: ±0.01mW
        
        The method also updates:
        - Status bits (byte 110)
        - Alarm flags (byte 112)
        
        @note The current page selection is preserved across the update.
        """
        # Add some random variation to values (reduced for stability)
        temp_variation = random.uniform(-0.05, 0.05)
        voltage_variation = random.uniform(-0.01, 0.01)
        
        # Get current page
        current_page = self.memory_map.current_page
        
        # Select A2h page for diagnostics
        self.memory_map.select_page(0xA2)
        
        # Temperature and voltage (mandatory)
        temp = self._temperature + temp_variation
        self.memory_map.write_word(0x60, self._encode_temperature(temp))
        self.memory_map.write_word(0x62, self._encode_voltage(self._voltage + voltage_variation))
        
        # Optional monitoring values for optical modules
        if not self.config.media_type.name.startswith('COPPER'):
            bias_variation = random.uniform(-0.2, 0.2)
            power_variation = random.uniform(-0.01, 0.01)
            
            self.memory_map.write_word(0x64, self._encode_bias(self._tx_bias_ma + bias_variation))
            self.memory_map.write_word(0x66, self._encode_power(self._tx_power_mw + power_variation))
            self.memory_map.write_word(0x68, self._encode_power(self._rx_power_mw + power_variation))
        
        # Update status and alarm flags
        status = 0x00
        alarms = 0x00
        
        # Status bits
        if self._tx_disable:
            status |= 0x40
        if self._tx_fault:
            status |= 0x20
        if self._rx_los:
            status |= 0x10
            
        # Alarm bits
        if temp > 75.0:  # High temp alarm
            alarms |= 0x80
        if temp < -5.0:  # Low temp alarm
            alarms |= 0x40
        if self._voltage > 3.6:  # High voltage alarm
            alarms |= 0x20
        if self._voltage < 3.0:  # Low voltage alarm
            alarms |= 0x10
        
        self.memory_map.write_byte(0x6E, status)
        self.memory_map.write_byte(0x70, alarms)
        
        # Restore original page
        self.memory_map.select_page(current_page)
    
    def set_tx_disable(self, disable: bool) -> None:
        """!
        Set TX disable state.
        
        @param disable True to disable TX output, False to enable
        
        Controls the transmitter disable state:
        - When disabled (True):
          - TX power drops to 0
          - TX disable bit (bit 6) is set in status register
          - Power registers are updated immediately
        - When enabled (False):
          - TX power returns to normal
          - TX disable bit is cleared
          - Normal monitoring resumes
        
        The TX disable state is reflected in:
        - Status byte (110): bit 6
        - TX power registers (102-103)
        
        Example:
        @code
        module.set_tx_disable(True)   # Disable TX
        status = hardware.read_register(0xA2, 110)
        assert status & 0x40          # Check TX disable bit
        
        module.set_tx_disable(False)  # Enable TX
        status = hardware.read_register(0xA2, 110)
        assert not (status & 0x40)    # Bit should be cleared
        @endcode
        
        @note The current page selection is preserved.
        """
        # Save current page
        current_page = self.memory_map.current_page

        self._tx_disable = disable
        if disable:
            self._tx_power_mw = 0.0
            # Force update with exactly zero power and skip random variation
            self.memory_map.select_page(0xA2)
            self.memory_map.write_word(0x66, 0)
            # Set TX disable bit
            status = self.memory_map.read_byte(0x6E)
            status |= 0x40
            self.memory_map.write_byte(0x6E, status)
        else:
            self._tx_power_mw = 0.5  # Return to typical power
            # Update TX power value
            self.memory_map.select_page(0xA2)
            power_value = self._encode_power(self._tx_power_mw)
            self.memory_map.write_word(0x66, power_value)
            # Clear TX disable bit
            status = self.memory_map.read_byte(0x6E)
            status &= ~0x40
            self.memory_map.write_byte(0x6E, status)
        
        # Restore original page
        self.memory_map.select_page(current_page)
    
    def simulate_fault(self, fault_type: str, state: bool) -> None:
        """!
        Simulate various fault conditions.
        
        @param fault_type Type of fault to simulate ('tx_fault' or 'rx_los')
        @param state True to activate the fault, False to clear it
        @throws EmulationError if fault_type is unknown
        
        Supported fault types:
        - 'tx_fault': Transmitter fault
          - Sets/clears bit 5 in status register
          - Forces TX power to 0 when active
        - 'rx_los': Receiver loss of signal
          - Sets/clears bit 4 in status register
          - Forces RX power to 0 when active
        
        For each fault type:
        1. Updates internal state
        2. Modifies status register
        3. Updates affected monitoring values
        4. Preserves page selection
        
        Example:
        @code
        # Simulate TX fault
        module.simulate_fault('tx_fault', True)
        status = hardware.read_register(0xA2, 110)
        assert status & 0x20  # Check TX fault bit
        
        # Clear TX fault
        module.simulate_fault('tx_fault', False)
        status = hardware.read_register(0xA2, 110)
        assert not (status & 0x20)
        @endcode
        """
        # Save current page
        current_page = self.memory_map.current_page

        if fault_type == 'tx_fault':
            self._tx_fault = state
            if state:
                self._tx_power_mw = 0.0
                # Force update with exactly zero power and skip random variation
                self.memory_map.select_page(0xA2)
                self.memory_map.write_word(0x66, 0)
                # Update status bits
                status = self.memory_map.read_byte(0x6E)
                status |= 0x20  # Set TX fault bit
                self.memory_map.write_byte(0x6E, status)
            else:
                self._tx_power_mw = 0.5
                # Clear TX fault bit
                self.memory_map.select_page(0xA2)
                status = self.memory_map.read_byte(0x6E)
                status &= ~0x20
                self.memory_map.write_byte(0x6E, status)
        elif fault_type == 'rx_los':
            self._rx_los = state
            if state:
                self._rx_power_mw = 0.0
                # Force update with exactly zero power and skip random variation
                self.memory_map.select_page(0xA2)
                self.memory_map.write_word(0x68, 0)
                # Update status bits
                status = self.memory_map.read_byte(0x6E)
                status |= 0x10  # Set RX LOS bit
                self.memory_map.write_byte(0x6E, status)
            else:
                self._rx_power_mw = 0.4
                # Clear RX LOS bit
                self.memory_map.select_page(0xA2)
                status = self.memory_map.read_byte(0x6E)
                status &= ~0x10
                self.memory_map.write_byte(0x6E, status)
        else:
            raise EmulationError(f"Unknown fault type: {fault_type}")
        
        # Restore original page
        self.memory_map.select_page(current_page)
    
    def set_temperature(self, temperature: float) -> None:
        """Set module temperature"""
        self._temperature = temperature
        self.update_monitoring()
    
    def set_voltage(self, voltage: float) -> None:
        """Set module voltage"""
        self._voltage = voltage
        self.update_monitoring()