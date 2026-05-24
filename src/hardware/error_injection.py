"""
Error Injection and Bus Fault Simulation Skill.
Provides mechanisms to simulate hardware-level interface failures like I2C NACKs, clock stretching, and GPIO locks.
"""
import time
from typing import Dict, Set, Any, Optional, Callable, Union

class ErrorInjectionError(Exception):
    """Exception raised when an injected hardware fault occurs."""
    pass

class ErrorInjector:
    """
    Wraps or hooks into a HardwareInterface to dynamically simulate bus faults, 
    clock stretching, and signal anomalies for robust driver resilience testing.
    """
    
    def __init__(self, hardware: Any):
        """
        Initialize with a target hardware interface.
        
        Args:
            hardware: The hardware interface instance (actual or emulated).
        """
        self._hw = hardware
        self._nacked_addresses: Dict[int, int] = {}  # bus_addr or reg_addr -> count of NACKs to inject
        self._clock_stretch_delay: float = 0.0       # seconds of delay to inject per transaction
        self._corrupted_registers: Dict[int, int] = {}  # reg_addr -> XOR bitmask to apply
        self._gpio_overrides: Dict[str, bool] = {}    # signal_name -> overridden state
        
    def inject_nack(self, address: int, count: int = 1) -> None:
        """
        Inject an I2C NACK (bus reject) on subsequent accesses to a specific register address.
        
        Args:
            address: The register address or device bus address to trigger a NACK.
            count: Number of subsequent calls that will raise an error.
        """
        self._nacked_addresses[address] = count
        
    def inject_clock_stretch(self, delay_seconds: float) -> None:
        """
        Inject clock stretching (bus latency delay) on every I2C transaction.
        
        Args:
            delay_seconds: Latency in seconds.
        """
        self._clock_stretch_delay = delay_seconds
        
    def inject_bit_corruption(self, address: int, xor_mask: int) -> None:
        """
        Inject register bit corruptions on reads.
        
        Args:
            address: The target register offset.
            xor_mask: XOR mask applied to the read byte value.
        """
        self._corrupted_registers[address] = xor_mask
        
    def inject_gpio_failure(self, signal: str, state: bool) -> None:
        """
        Override the state of a GPIO pin, locking it to a specific boolean value regardless of updates.
        
        Args:
            signal: Name of the GPIO pin (e.g. 'reset', 'interrupt').
            state: Overridden state.
        """
        self._gpio_overrides[signal] = state
        
    def clear_faults(self) -> None:
        """Clear all active injected errors, NACKs, and signal overrides."""
        self._nacked_addresses.clear()
        self._clock_stretch_delay = 0.0
        self._corrupted_registers.clear()
        self._gpio_overrides.clear()
        
    def read_register(self, bus_address: int, reg_address: int) -> int:
        """
        Intercept register reads, applying injected faults/NACKs/corruptions.
        """
        # 1. Process Bus NACKs
        for addr in (bus_address, reg_address):
            if addr in self._nacked_addresses and self._nacked_addresses[addr] > 0:
                self._nacked_addresses[addr] -= 1
                raise ErrorInjectionError(f"I2C Bus Fault: NACK received on access to address 0x{addr:02X}")
                
        # 2. Process Clock Stretching
        if self._clock_stretch_delay > 0.0:
            time.sleep(self._clock_stretch_delay)
            
        # 3. Read actual value
        if hasattr(self._hw, 'read_register'):
            # Some signatures might be read_register(reg_address) or read_register(bus_address, reg_address)
            try:
                val = self._hw.read_register(bus_address, reg_address)
            except TypeError:
                val = self._hw.read_register(reg_address)
        else:
            raise AttributeError("Target hardware interface does not support read_register.")
            
        # 4. Process Bit Corruptions
        if reg_address in self._corrupted_registers:
            val ^= self._corrupted_registers[reg_address]
            
        return val
        
    def write_register(self, bus_address: int, reg_address: int, value: int) -> None:
        """
        Intercept register writes, applying injected faults/NACKs.
        """
        # 1. Process Bus NACKs
        for addr in (bus_address, reg_address):
            if addr in self._nacked_addresses and self._nacked_addresses[addr] > 0:
                self._nacked_addresses[addr] -= 1
                raise ErrorInjectionError(f"I2C Bus Fault: NACK received on write to address 0x{addr:02X}")
                
        # 2. Process Clock Stretching
        if self._clock_stretch_delay > 0.0:
            time.sleep(self._clock_stretch_delay)
            
        # 3. Write actual value
        if hasattr(self._hw, 'write_register'):
            try:
                self._hw.write_register(bus_address, reg_address, value)
            except TypeError:
                self._hw.write_register(reg_address, value)
        else:
            raise AttributeError("Target hardware interface does not support write_register.")

    def get_gpio_state(self, signal: str) -> bool:
        """Read GPIO state, applying overrides if set."""
        if signal in self._gpio_overrides:
            return self._gpio_overrides[signal]
        if hasattr(self._hw, 'get_gpio_state'):
            return self._hw.get_gpio_state(signal)
        return False

    def set_gpio_state(self, signal: str, state: bool) -> None:
        """Set GPIO state, ignoring updates if overrides are set."""
        if signal in self._gpio_overrides:
            # Override is locked, ignore write
            return
        if hasattr(self._hw, 'set_gpio_state'):
            self._hw.set_gpio_state(signal, state)
