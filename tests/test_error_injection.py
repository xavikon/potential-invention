"""
Unit and integration tests for the Error Injection and Bus Fault Simulation layer.
"""
import time
import pytest
from src.hardware.error_injection import ErrorInjector, ErrorInjectionError

class MockHardware:
    """Mock hardware interface to satisfy ErrorInjector hooks."""
    def __init__(self):
        self.registers = {0x10: 0x55, 0x20: 0xAA}
        self.gpio = {"reset": False, "interrupt": False}
        
    def read_register(self, bus_address: int, reg_address: int) -> int:
        return self.registers.get(reg_address, 0x00)
        
    def write_register(self, bus_address: int, reg_address: int, value: int) -> None:
        self.registers[reg_address] = value
        
    def get_gpio_state(self, signal: str) -> bool:
        return self.gpio.get(signal, False)
        
    def set_gpio_state(self, signal: str, state: bool) -> None:
        self.gpio[signal] = state


def test_error_injection_nack():
    """Verify NACK errors are raised for a configured count and then clear."""
    mock_hw = MockHardware()
    injector = ErrorInjector(mock_hw)
    
    # Inject 2 NACKs on address 0x10
    injector.inject_nack(0x10, count=2)
    
    # First access: should raise ErrorInjectionError
    with pytest.raises(ErrorInjectionError):
        injector.read_register(0xA0, 0x10)
        
    # Second access: should raise ErrorInjectionError
    with pytest.raises(ErrorInjectionError):
        injector.write_register(0xA0, 0x10, 0x99)
        
    # Third access: NACK count is exhausted, should succeed
    val = injector.read_register(0xA0, 0x10)
    assert val == 0x55


def test_error_injection_clock_stretch():
    """Verify clock stretching injects delay into operations."""
    mock_hw = MockHardware()
    injector = ErrorInjector(mock_hw)
    
    injector.inject_clock_stretch(0.1)  # 100ms
    
    start_time = time.time()
    injector.read_register(0xA0, 0x10)
    duration = time.time() - start_time
    
    assert duration >= 0.09  # close to 100ms or greater


def test_error_injection_bit_corruption():
    """Verify read bits are correctly corrupted using the XOR mask."""
    mock_hw = MockHardware()
    injector = ErrorInjector(mock_hw)
    
    # Corrupt register 0x10 with XOR mask 0x0F
    injector.inject_bit_corruption(0x10, 0x0F)
    
    # Raw value is 0x55 (binary: 0101 0101)
    # Corrupted: 0x55 ^ 0x0F = 0x5A (binary: 0101 1010)
    corrupted_val = injector.read_register(0xA0, 0x10)
    assert corrupted_val == 0x5A
    
    # Reset corruption, should return raw 0x55
    injector.clear_faults()
    assert injector.read_register(0xA0, 0x10) == 0x55


def test_error_injection_gpio_override():
    """Verify GPIO signal state overrides lock values against writes."""
    mock_hw = MockHardware()
    injector = ErrorInjector(mock_hw)
    
    # Lock 'interrupt' to True
    injector.inject_gpio_failure("interrupt", True)
    assert injector.get_gpio_state("interrupt") is True
    
    # Set to False should be ignored because override is active
    injector.set_gpio_state("interrupt", False)
    assert injector.get_gpio_state("interrupt") is True
    
    # Unlock via clear, value should return to normal mock state (False)
    injector.clear_faults()
    assert injector.get_gpio_state("interrupt") is False
