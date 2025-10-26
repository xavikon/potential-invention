"""!
@file hardware.py
@brief Emulated hardware interface for pluggable modules.

This module provides a complete emulation of the hardware interfaces required
for pluggable module control and communication. It implements:
- I2C bus emulation with support for multiple addresses
- GPIO signal emulation for module control
- Combined hardware interface for high-level operations

The implementation supports both SFF and CMIS modules with appropriate
address mapping and control signals. Key features include:
- Multi-device I2C bus with automatic page handling
- Full GPIO pin control and monitoring
- Module presence detection
- Reset signal handling
- Low power mode control
- Interrupt monitoring

Example usage:
@code
# Create hardware interface and module
hardware = EmulatedHardwareInterface()
module = SFFEmulatedModule(config)

# Attach module and verify presence
hardware.attach_module(module)
assert hardware.get_module_present()

# Read module identifier
identifier = hardware.read_register(0xA0, 0x00)
assert identifier == 0x03  # SFP/SFP+

# Write and read memory
hardware.write_register(0xA0, 0x14, 0x54)  # 'T'
value = hardware.read_register(0xA0, 0x14)
assert value == 0x54

# Control module
hardware.reset_module()
hardware.set_low_power_mode(True)
@endcode
"""
from typing import Dict, Optional, List, Union
from .base import EmulatedModule, EmulationError

class EmulatedI2CBus:
    """!
    Emulates an I2C bus for module communication.
    
    This class provides a complete emulation of an I2C bus interface, supporting:
    - Multiple device addresses (0xA0, 0xA2 for SFF; 0x50, 0x51 for CMIS)
    - Register-based read/write operations
    - Automatic page handling using standard page select registers
    - Multiple devices with independent memory spaces
    
    The I2C bus emulation handles the complexities of:
    - Device addressing and selection
    - Page selection register handling
    - Memory access bounds checking
    - Error reporting for invalid operations
    
    Address map:
    - 0xA0: SFF identification and status (lower pages)
    - 0xA2: SFF diagnostics (upper pages)
    - 0x50: CMIS lower pages
    - 0x51: CMIS upper pages
    
    Page selection:
    - SFF modules: Page register at offset 0x7F
    - CMIS modules: Page register at offset 0x7F
    
    Example:
    @code
    i2c = EmulatedI2CBus()
    i2c.attach_device(0xA0, module)  # Attach at A0h
    
    # Write to page register
    i2c.write_byte(0xA0, 0x7F, 0x01)  # Select page 1
    
    # Write data
    i2c.write_byte(0xA0, 0x00, 0x55)
    
    # Read back
    value = i2c.read_byte(0xA0, 0x00)
    assert value == 0x55
    @endcode
    """
    
    def __init__(self):
        """Initialize I2C bus"""
        self._devices: Dict[int, EmulatedModule] = {}
        self._current_address = 0
        self._page_registers = {
            0xA0: 0x7F,  # SFF page register
            0xA2: 0x7F,  # SFF page register
            0x50: 0x7F,  # CMIS lower page
            0x51: 0x7F,  # CMIS upper page
        }
    
    def attach_device(self, address: int, device: EmulatedModule) -> None:
        """Attach a device to the I2C bus at specified address"""
        if address in self._devices:
            raise EmulationError(f"Address {address:02x} already in use")
        self._devices[address] = device
    
    def detach_device(self, address: int) -> None:
        """Detach a device from the I2C bus"""
        if address in self._devices:
            del self._devices[address]
    
    def write_byte(self, address: int, reg_address: int, value: int) -> None:
        """Write a byte to a device register"""
        if address not in self._devices:
            raise EmulationError(f"No device at address {address:02x}")
        
        device = self._devices[address]
        
        # Handle page selection if this is a page register
        if address in self._page_registers and reg_address == self._page_registers[address]:
            # Convert address to page number for SFF modules
            if address in [0xA0, 0xA2]:
                device.memory_map.select_page(address)
            else:
                device.memory_map.select_page(value)
        else:
            device.memory_map.write_byte(reg_address, value)
    
    def read_byte(self, address: int, reg_address: int) -> int:
        """Read a byte from a device register"""
        if address not in self._devices:
            raise EmulationError(f"No device at address {address:02x}")
        
        device = self._devices[address]
        return device.memory_map.read_byte(reg_address)
    
    def write_bytes(self, address: int, reg_address: int, data: bytes) -> None:
        """Write multiple bytes to consecutive registers"""
        if address not in self._devices:
            raise EmulationError(f"No device at address {address:02x}")
        
        device = self._devices[address]
        device.memory_map.write_bytes(reg_address, data)

class EmulatedGPIO:
    """!
    Emulates GPIO pins for module control.
    
    This class provides emulation of the GPIO signals used for module control
    and status monitoring. It supports:
    - Module presence detection
    - Module selection/deselection
    - Reset signal control
    - Low power mode control
    - Interrupt monitoring
    
    Supported GPIO pins:
    - mod_present: Module presence detection (input)
    - mod_select: Module selection for multi-module systems (output)
    - reset: Module reset control (output)
    - lpmode: Low power mode control (output)
    - interrupt: Module interrupt signal (input)
    
    Pin states:
    - True: Logic high (3.3V/presence/active)
    - False: Logic low (0V/absence/inactive)
    
    Example:
    @code
    gpio = EmulatedGPIO()
    gpio.attach_device(module)
    
    # Check initial state
    assert not gpio.get_pin('mod_present')
    
    # Control module
    gpio.set_pin('mod_select', True)
    gpio.set_pin('reset', True)
    gpio.set_pin('reset', False)
    
    # Monitor status
    if gpio.get_pin('interrupt'):
        print("Module is requesting attention")
    @endcode
    
    @note Input pins (mod_present, interrupt) reflect the module's state,
          while output pins (mod_select, reset, lpmode) control the module.
    """
    
    def __init__(self):
        """Initialize GPIO controller"""
        self._pins: Dict[str, bool] = {
            'mod_present': False,
            'mod_select': False,
            'reset': False,
            'lpmode': False,
            'interrupt': False
        }
        self._device: Optional[EmulatedModule] = None
    
    def attach_device(self, device: EmulatedModule) -> None:
        """Attach a module to the GPIO controller"""
        self._device = device
    
    def detach_device(self) -> None:
        """Detach the module from the GPIO controller"""
        self._device = None
        self._pins['mod_present'] = False
    
    def set_pin(self, pin_name: str, state: bool) -> None:
        """Set GPIO pin state"""
        if pin_name not in self._pins:
            raise EmulationError(f"Unknown GPIO pin: {pin_name}")
        
        self._pins[pin_name] = state
        
        if self._device:
            self._device.set_gpio_state(pin_name, state)
    
    def get_pin(self, pin_name: str) -> bool:
        """Get GPIO pin state"""
        if pin_name not in self._pins:
            raise EmulationError(f"Unknown GPIO pin: {pin_name}")
        
        if self._device and pin_name in ['mod_present', 'interrupt']:
            return self._device.get_gpio_state(pin_name)
        
        return self._pins[pin_name]

class EmulatedHardwareInterface:
    """!
    Main hardware interface for module interaction.
    
    This class provides the primary interface for interacting with emulated
    modules. It combines I2C and GPIO functionality into a cohesive interface
    that mimics real hardware behavior. Features include:
    
    1. Module Management:
       - Module attachment and detachment
       - Automatic I2C address configuration
       - GPIO signal initialization
       - Module presence detection
    
    2. Memory Access:
       - Register read/write operations
       - Multi-byte register access
       - Automatic page handling
       - Error checking and reporting
    
    3. Control Operations:
       - Module reset
       - Low power mode control
       - Interrupt monitoring
       - Status checking
    
    The interface automatically handles:
    - Address mapping based on module type (SFF vs CMIS)
    - GPIO signal routing
    - Error conditions and reporting
    - Resource cleanup
    
    Example:
    @code
    # Create interface and module
    hw = EmulatedHardwareInterface()
    module = SFFEmulatedModule(config)
    
    # Initialize
    hw.attach_module(module)
    if not hw.get_module_present():
        raise RuntimeError("Module not present")
    
    # Read identification
    identifier = hw.read_register(0xA0, 0)
    print(f"Module type: 0x{identifier:02X}")
    
    # Write configuration
    hw.write_register(0xA2, 0x6E, 0x40)  # Set TX disable
    
    # Control operations
    hw.reset_module()
    hw.set_low_power_mode(True)
    
    # Cleanup
    hw.detach_module()
    @endcode
    
    @see EmulatedI2CBus
    @see EmulatedGPIO
    @see EmulatedModule
    """
    
    def __init__(self):
        """Initialize hardware interface"""
        self.i2c = EmulatedI2CBus()
        self.gpio = EmulatedGPIO()
        self._module: Optional[EmulatedModule] = None
    
    def attach_module(self, module: EmulatedModule) -> None:
        """
        Attach a module to the interface.
        Sets up I2C and GPIO connections.
        """
        self._module = module
        
        # Attach to GPIO
        self.gpio.attach_device(module)
        self.gpio.set_pin('mod_present', True)
        
        # Attach to I2C based on module type
        if module.config.module_type.name == 'CMIS':
            self.i2c.attach_device(0x50, module)  # Lower pages
            self.i2c.attach_device(0x51, module)  # Upper pages
        else:  # SFF
            self.i2c.attach_device(0xA0, module)  # ID/Status pages
            self.i2c.attach_device(0xA2, module)  # Diagnostic pages
    
    def detach_module(self) -> None:
        """
        Detach the current module.
        Cleans up I2C and GPIO connections.
        """
        if not self._module:
            return
        
        # Detach from GPIO
        self.gpio.detach_device()
        
        # Detach from I2C
        for address in [0x50, 0x51, 0xA0, 0xA2]:
            try:
                self.i2c.detach_device(address)
            except EmulationError:
                pass
        
        self._module = None
    
    def reset_module(self) -> None:
        """
        Reset the module.
        Cycles reset signal and reinitializes module state.
        """
        if not self._module:
            raise EmulationError("No module attached")
        
        # Assert reset
        self.gpio.set_pin('reset', True)
        # Deassert reset
        self.gpio.set_pin('reset', False)
    
    def read_register(self, bus_address: int, reg_address: int) -> int:
        """Read a register from the module"""
        if not self._module:
            raise EmulationError("No module attached")
        
        return self.i2c.read_byte(bus_address, reg_address)
    
    def write_register(self, bus_address: int, reg_address: int, value: int) -> None:
        """Write to a module register"""
        if not self._module:
            raise EmulationError("No module attached")
        
        self.i2c.write_byte(bus_address, reg_address, value)
    
    def read_registers(self, bus_address: int, reg_address: int, count: int) -> List[int]:
        """Read multiple consecutive registers"""
        if not self._module:
            raise EmulationError("No module attached")
        
        return [self.i2c.read_byte(bus_address, reg_address + i) for i in range(count)]
    
    def write_registers(self, bus_address: int, reg_address: int, values: Union[bytes, List[int]]) -> None:
        """Write to multiple consecutive registers"""
        if not self._module:
            raise EmulationError("No module attached")
        
        if isinstance(values, list):
            values = bytes(values)
        
        self.i2c.write_bytes(bus_address, reg_address, values)
    
    def get_module_present(self) -> bool:
        """Check if a module is present"""
        return self.gpio.get_pin('mod_present')
    
    def get_module_interrupt(self) -> bool:
        """Check module interrupt status"""
        return self.gpio.get_pin('interrupt')
    
    def set_low_power_mode(self, enable: bool) -> None:
        """Set module low power mode"""
        if not self._module:
            raise EmulationError("No module attached")
        
        self.gpio.set_pin('lpmode', enable)