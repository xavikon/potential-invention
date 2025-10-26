"""
Basic functionality tests for both SFF and CMIS modules.
"""
import pytest
from tests.emulation.base import EmulatedModule, EmulationError

def test_module_presence(sff_module: EmulatedModule):
    """Test module presence detection"""
    assert sff_module.is_present()

def test_module_identification(sff_module: EmulatedModule):
    """Test basic module identification"""
    assert sff_module.get_identifier() == 0x0d
    assert sff_module.get_vendor_name() == "Test Vendor"
    assert sff_module.get_part_number() == "TEST-PART-001"
    assert sff_module.get_serial_number() == "TEST001"
    assert sff_module.get_revision() == "A1"

def test_temperature_monitoring(sff_module: EmulatedModule, temp_value: float):
    """Test temperature monitoring functionality"""
    sff_module.set_temperature(temp_value)
    assert abs(sff_module.get_temperature() - temp_value) < 0.1

def test_voltage_monitoring(sff_module: EmulatedModule, voltage_value: float):
    """Test voltage monitoring functionality"""
    sff_module.set_voltage(voltage_value)
    assert abs(sff_module.get_voltage() - voltage_value) < 0.01

def test_invalid_memory_access(sff_module: EmulatedModule):
    """Test handling of invalid memory access"""
    with pytest.raises(EmulationError):
        sff_module.memory_map.read_byte(0x1000)  # Invalid address - beyond page size

def test_memory_page_switching(sff_module: EmulatedModule):
    """Test memory page switching functionality"""
    sff_module.memory_map.select_page(0x01)
    assert sff_module.memory_map.current_page == 0x01
    
    with pytest.raises(EmulationError):
        sff_module.memory_map.select_page(0xFF)  # Invalid page