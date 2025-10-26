"""
Tests for SFF module-specific features.
"""
import pytest
import random
from typing import Generator
from .emulation.base import EmulatedModule
from .emulation.sff import SFFEmulatedModule
from .emulation.hardware import EmulatedHardwareInterface, EmulationError

def test_digital_diagnostics(hardware: EmulatedHardwareInterface, sff_module: SFFEmulatedModule):
    """Test digital diagnostic monitoring capabilities"""
    hardware.attach_module(sff_module)
    
    # Set some test values
    temp_value = 45.0
    voltage_value = 3.3
    bias_value = 30.0
    tx_power = 0.5
    rx_power = 0.4
    
    sff_module.set_temperature(temp_value)
    sff_module.set_voltage(voltage_value)
    
    # Read A2h page diagnostics
    hardware.write_register(0xA2, 0x7F, 0xA2)  # Select A2h page
    
    # Read temperature (bytes 96-97)
    temp_raw = (hardware.read_register(0xA2, 96) << 8) | hardware.read_register(0xA2, 97)
    temp_read = temp_raw / 256.0
    assert abs(temp_read - temp_value) < 0.1
    
    # Read voltage (bytes 98-99)
    voltage_raw = (hardware.read_register(0xA2, 98) << 8) | hardware.read_register(0xA2, 99)
    voltage_read = voltage_raw / 10000.0
    assert abs(voltage_read - voltage_value) < 0.01

def test_alarm_thresholds(hardware: EmulatedHardwareInterface, sff_module: SFFEmulatedModule):
    """Test alarm threshold monitoring"""
    hardware.attach_module(sff_module)
    hardware.write_register(0xA2, 0x7F, 0xA2)  # Select A2h page
    
    # Set temperature above alarm threshold
    sff_module.set_temperature(80.0)  # Above 75°C threshold
    
    # Read alarm flags
    alarm_flags = hardware.read_register(0xA2, 112)
    assert alarm_flags & 0x80  # Temperature high alarm should be set
    
    # Set temperature back to normal
    sff_module.set_temperature(45.0)
    alarm_flags = hardware.read_register(0xA2, 112)
    assert not (alarm_flags & 0x80)  # Temperature high alarm should be cleared

def test_tx_disable_control(hardware: EmulatedHardwareInterface, sff_module: SFFEmulatedModule):
    """Test TX disable functionality"""
    hardware.attach_module(sff_module)
    hardware.write_register(0xA2, 0x7F, 0xA2)  # Select A2h page
    
    # Enable TX disable
    sff_module.set_tx_disable(True)
    status = hardware.read_register(0xA2, 110)
    assert status & 0x40  # TX disable bit should be set
    
    # Read TX power - should be zero when disabled
    tx_power_raw = (hardware.read_register(0xA2, 102) << 8) | hardware.read_register(0xA2, 103)
    tx_power = tx_power_raw * 0.0001  # Convert to mW
    assert tx_power == 0.0
    
    # Disable TX disable
    sff_module.set_tx_disable(False)
    status = hardware.read_register(0xA2, 110)
    assert not (status & 0x40)  # TX disable bit should be cleared
    
    # TX power should be restored
    tx_power_raw = (hardware.read_register(0xA2, 102) << 8) | hardware.read_register(0xA2, 103)
    tx_power = tx_power_raw * 0.0001  # Convert to mW
    assert tx_power > 0.0

def test_fault_conditions(hardware: EmulatedHardwareInterface, sff_module: SFFEmulatedModule):
    """Test fault condition handling"""
    hardware.attach_module(sff_module)
    hardware.write_register(0xA2, 0x7F, 0xA2)  # Select A2h page
    
    # Simulate TX fault
    sff_module.simulate_fault('tx_fault', True)
    status = hardware.read_register(0xA2, 110)
    assert status & 0x20  # TX fault bit should be set
    
    # TX power should be zero during fault
    tx_power_raw = (hardware.read_register(0xA2, 102) << 8) | hardware.read_register(0xA2, 103)
    tx_power = tx_power_raw * 0.0001  # Convert to mW
    assert tx_power == 0.0
    
    # Clear TX fault
    sff_module.simulate_fault('tx_fault', False)
    status = hardware.read_register(0xA2, 110)
    assert not (status & 0x20)  # TX fault bit should be cleared
    
    # Simulate RX LOS
    sff_module.simulate_fault('rx_los', True)
    status = hardware.read_register(0xA2, 110)
    assert status & 0x10  # RX LOS bit should be set
    
    # RX power should be zero during LOS
    rx_power_raw = (hardware.read_register(0xA2, 104) << 8) | hardware.read_register(0xA2, 105)
    rx_power = rx_power_raw * 0.0001  # Convert to mW
    assert rx_power == 0.0

def test_identification(hardware: EmulatedHardwareInterface, sff_module: SFFEmulatedModule):
    """Test module identification information"""
    # Configure module with test values
    sff_module.config.vendor_name = "Test Vendor"
    sff_module.config.part_number = "TEST-PART-001"
    
    # Re-initialize to apply new config
    sff_module._initialize_memory_map()
    
    hardware.attach_module(sff_module)
    hardware.write_register(0xA0, 0x7F, 0xA0)  # Select A0h page
    
    # Read vendor name
    vendor_name = ""
    for i in range(16):
        char = hardware.read_register(0xA0, 0x14 + i)
        if char == 0:  # Stop at null termination
            break
        vendor_name += chr(char)
    assert vendor_name == "Test Vendor"
    
    # Read part number
    part_number = ""
    for i in range(16):
        char = hardware.read_register(0xA0, 0x28 + i)
        if char == 0:  # Stop at null termination
            break
        part_number += chr(char)
    assert part_number == "TEST-PART-001"

def test_random_monitoring(hardware: EmulatedHardwareInterface, sff_module: SFFEmulatedModule):
    """Test that monitoring values show expected random variations"""
    hardware.attach_module(sff_module)
    hardware.write_register(0xA2, 0x7F, 0xA2)  # Select A2h page
    
    # Read initial values
    temp1 = (hardware.read_register(0xA2, 96) << 8) | hardware.read_register(0xA2, 97)
    bias1 = (hardware.read_register(0xA2, 100) << 8) | hardware.read_register(0xA2, 101)
    
    # Force an update
    sff_module.update_monitoring()
    
    # Read new values
    temp2 = (hardware.read_register(0xA2, 96) << 8) | hardware.read_register(0xA2, 97)
    bias2 = (hardware.read_register(0xA2, 100) << 8) | hardware.read_register(0xA2, 101)
    
    # Values should be slightly different due to random variation
    assert temp1 != temp2
    assert bias1 != bias2