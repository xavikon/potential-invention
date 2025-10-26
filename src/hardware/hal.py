"""
Hardware Abstraction Layer for Pluggable Module Management.
Provides a clean interface for I2C and GPIO operations.
"""
from typing import Dict, Union
from enum import Enum, auto
from .hw_access import read_i2c, write_i2c, read_gpio, write_gpio

class GPIOSignal(Enum):
    """Enumeration of available GPIO signals"""
    RESET = "reset"
    INTERRUPT = "interrupt"
    PRESENT = "present"
    LPMODE = "lpmode"

class HardwareInterface:
    """
    Hardware abstraction layer for pluggable module communication.
    Wraps the low-level I2C and GPIO functions into a clean interface.
    """
    
    def __init__(self):
        # Add any initialization needed for hardware interface
        pass
    
    def read_register(self, address: int) -> int:
        """
        Read a value from a specific memory address via I2C.
        
        Args:
            address: The memory address to read from
            
        Returns:
            The value read from the register
        """
        return read_i2c(address)  # Assuming read_i2c is globally available
    
    def write_register(self, address: int, value: int) -> None:
        """
        Write a value to a specific memory address via I2C.
        
        Args:
            address: The memory address to write to
            value: The value to write to the register
        """
        write_i2c(address, value)  # Assuming write_i2c is globally available
    
    def get_gpio_state(self, signal: Union[GPIOSignal, str]) -> bool:
        """
        Read the state of a GPIO signal.
        
        Args:
            signal: The GPIO signal to read (can be GPIOSignal enum or string)
            
        Returns:
            True if signal is asserted, False otherwise
        """
        if isinstance(signal, GPIOSignal):
            signal = signal.value
        return read_gpio(signal)  # Assuming read_gpio is globally available
    
    def set_gpio_state(self, signal: Union[GPIOSignal, str], state: bool) -> None:
        """
        Set the state of a GPIO signal.
        
        Args:
            signal: The GPIO signal to set (can be GPIOSignal enum or string)
            state: True to assert signal, False to deassert
        """
        if isinstance(signal, GPIOSignal):
            signal = signal.value
        write_gpio(signal, state)  # Assuming write_gpio is globally available
    
    def module_present(self) -> bool:
        """
        Check if a module is present.
        
        Returns:
            True if a module is present, False otherwise
        """
        return self.get_gpio_state(GPIOSignal.PRESENT)
    
    def reset_module(self) -> None:
        """Reset the module by asserting and then deasserting the reset signal."""
        self.set_gpio_state(GPIOSignal.RESET, True)
        # TODO: Add appropriate delay here based on specifications
        self.set_gpio_state(GPIOSignal.RESET, False)
    
    def get_interrupt_state(self) -> bool:
        """
        Get the state of the module's interrupt signal.
        
        Returns:
            True if interrupt is asserted, False otherwise
        """
        return self.get_gpio_state(GPIOSignal.INTERRUPT)
    
    def set_low_power_mode(self, enable: bool) -> None:
        """
        Set the module's low power mode state.
        
        Args:
            enable: True to enable low power mode, False to disable
        """
        self.set_gpio_state(GPIOSignal.LPMODE, enable)