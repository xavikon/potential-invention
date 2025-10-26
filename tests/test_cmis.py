"""
Tests specific to CMIS module functionality.
"""
import pytest
from tests.emulation.cmis import CMISEmulatedModule
from tests.emulation.base import EmulationError

def test_cmis_application_selection(cmis_module: CMISEmulatedModule):
    """Test application selection functionality"""
    # Default application should be valid
    assert cmis_module.get_active_application() == 1
    
    # Test setting a supported application
    cmis_module.set_application(0x1)  # 10G
    assert cmis_module.get_active_application() == 0x1
    
    # Test setting an unsupported application
    with pytest.raises(EmulationError):
        cmis_module.set_application(0xFF)

def test_cmis_channel_control(cmis_module: CMISEmulatedModule):
    """Test per-channel control functionality"""
    # Test TX disable control
    cmis_module.set_tx_disable(0, True)
    assert cmis_module._tx_disable_mask == 0x01
    
    cmis_module.set_tx_disable(0, False)
    assert cmis_module._tx_disable_mask == 0x00
    
    # Test invalid channel
    with pytest.raises(EmulationError):
        cmis_module.set_tx_disable(99, True)

def test_cmis_fault_simulation(cmis_module: CMISEmulatedModule):
    """Test fault simulation functionality"""
    # Test TX fault
    cmis_module.simulate_fault(0, 'tx_fault', True)
    assert cmis_module._tx_fault_mask == 0x01
    assert cmis_module._tx_power_mw[0] == 0.0
    
    # Test RX LOS
    cmis_module.simulate_fault(0, 'rx_los', True)
    assert cmis_module._rx_los_mask == 0x01
    assert cmis_module._rx_power_mw[0] == 0.0
    
    # Test invalid fault type
    with pytest.raises(EmulationError):
        cmis_module.simulate_fault(0, 'invalid_fault', True)

def test_cmis_monitoring_updates(cmis_module: CMISEmulatedModule):
    """Test monitoring value updates"""
    initial_tx_power = cmis_module._tx_power_mw[0]
    initial_rx_power = cmis_module._rx_power_mw[0]
    
    # Update monitoring values
    cmis_module.update_monitoring()
    
    # Values should change slightly due to random variation
    assert cmis_module._tx_power_mw[0] != initial_tx_power
    assert cmis_module._rx_power_mw[0] != initial_rx_power

def test_cmis_temperature_alarms(cmis_module: CMISEmulatedModule):
    """Test temperature alarm functionality"""
    # Set temperature above alarm threshold
    cmis_module.set_temperature(75.0)
    cmis_module.update_monitoring()
    
    # Check alarm flags
    cmis_module.memory_map.select_page(0x83)
    flags = cmis_module.memory_map.read_byte(0x00)
    assert flags & 0x80  # High temp alarm should be set