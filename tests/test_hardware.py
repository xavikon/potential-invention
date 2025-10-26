"""
Tests for the emulated hardware interface.
"""
import pytest
from typing import Generator
from .emulation.base import EmulatedModule
from .emulation.hardware import EmulatedHardwareInterface, EmulationError

@pytest.fixture
def hardware() -> EmulatedHardwareInterface:
    """Provide an emulated hardware interface"""
    return EmulatedHardwareInterface()

def test_module_attachment(hardware: EmulatedHardwareInterface, sff_module: EmulatedModule):
    """Test module attachment and detection"""
    assert not hardware.get_module_present()
    
    hardware.attach_module(sff_module)
    assert hardware.get_module_present()
    
    hardware.detach_module()
    assert not hardware.get_module_present()

def test_i2c_access(hardware: EmulatedHardwareInterface, sff_module: EmulatedModule):
    """Test I2C register access"""
    hardware.attach_module(sff_module)
    
    # Select page A0h and read identifier
    sff_module.memory_map.select_page(0xA0)
    identifier = hardware.read_register(0xA0, 0x00)
    assert identifier == sff_module.get_identifier()
    
    # Write and read back a test value
    hardware.write_register(0xA0, 0x01, 0x55)
    value = hardware.read_register(0xA0, 0x01)
    assert value == 0x55

def test_gpio_control(hardware: EmulatedHardwareInterface, sff_module: EmulatedModule):
    """Test GPIO control signals"""
    hardware.attach_module(sff_module)
    
    # Test low power mode
    hardware.set_low_power_mode(True)
    assert hardware.gpio.get_pin('lpmode')
    
    hardware.set_low_power_mode(False)
    assert not hardware.gpio.get_pin('lpmode')
    
    # Test reset
    hardware.reset_module()
    # After reset, interrupts should be cleared
    assert not hardware.get_module_interrupt()

def test_multi_byte_access(hardware: EmulatedHardwareInterface, sff_module: EmulatedModule):
    """Test multi-byte register access"""
    hardware.attach_module(sff_module)
    
    # Write multiple bytes
    test_data = bytes([0x11, 0x22, 0x33, 0x44])
    hardware.write_registers(0xA0, 0x10, test_data)
    
    # Read back the bytes
    read_data = hardware.read_registers(0xA0, 0x10, 4)
    assert bytes(read_data) == test_data

def test_page_selection(hardware: EmulatedHardwareInterface, sff_module: EmulatedModule):
    """Test memory page selection"""
    hardware.attach_module(sff_module)
    
    # Write to A0h page
    sff_module.memory_map.select_page(0xA0)
    hardware.write_register(0xA0, 0x01, 0x55)
    value_a0 = hardware.read_register(0xA0, 0x01)
    assert value_a0 == 0x55
    
    # Write to A2h page
    sff_module.memory_map.select_page(0xA2)
    hardware.write_register(0xA2, 0x01, 0xAA)
    value_a2 = hardware.read_register(0xA2, 0x01)
    assert value_a2 == 0xAA
    
    # Verify values in different pages are preserved
    sff_module.memory_map.select_page(0xA0)
    assert hardware.read_register(0xA0, 0x01) == 0x55
    
    sff_module.memory_map.select_page(0xA2)
    assert hardware.read_register(0xA2, 0x01) == 0xAA

def test_error_handling(hardware: EmulatedHardwareInterface, sff_module: EmulatedModule):
    """Test error handling"""
    # Test accessing non-existent device
    with pytest.raises(EmulationError):
        hardware.read_register(0xA0, 0x00)
    
    # Attach module and test invalid operations
    hardware.attach_module(sff_module)
    
    with pytest.raises(EmulationError):
        # Invalid I2C address
        hardware.read_register(0x60, 0x00)
    
    with pytest.raises(EmulationError):
        # Invalid GPIO pin
        hardware.gpio.set_pin('invalid_pin', True)
    
    # Test detach and access
    hardware.detach_module()
    with pytest.raises(EmulationError):
        hardware.read_register(0xA0, 0x00)