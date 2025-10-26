"""
Test configuration and fixtures for the module management system.
"""
import os
import pytest
from typing import Generator, Dict, Any
from tests.emulation.base import EmulatedModule
from tests.emulation.sff import SFFEmulatedModule
from tests.emulation.cmis import CMISEmulatedModule
from tests.emulation.configs import ModuleConfig, MediaType, FormFactor, ModuleType
from tests.emulation.hardware import EmulatedHardwareInterface

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "sff: mark test as SFF module test"
    )
    config.addinivalue_line(
        "markers", "cmis: mark test as CMIS module test"
    )
    config.addinivalue_line(
        "markers", "hardware: mark test as requiring hardware interface"
    )

@pytest.fixture
def module_config() -> ModuleConfig:
    """Provide basic module configuration for testing"""
    return ModuleConfig(
        identifier=0x0d,  # SFP+
        vendor_name="Test Vendor",
        part_number="TEST-PART-001",
        serial_number="TEST001",
        revision="A1",
        media_type=MediaType.MMF,  # SR module uses MMF
        form_factor=FormFactor.SFP,
        module_type=ModuleType.SFP_PLUS,
        num_channels=1,
        max_power_draw=1.0,
        supported_rates=[10.0],
        nominal_bit_rate=10.0,
        max_case_temp=70.0
    )

@pytest.fixture
def sff_module(module_config: ModuleConfig) -> Generator[SFFEmulatedModule, None, None]:
    """Provide an emulated SFF module for testing"""
    module = SFFEmulatedModule(module_config)
    yield module

@pytest.fixture
def cmis_module(module_config: ModuleConfig) -> Generator[CMISEmulatedModule, None, None]:
    """Provide an emulated CMIS module for testing"""
    module = CMISEmulatedModule(module_config)
    yield module

@pytest.fixture
def temp_value() -> float:
    """Provide a valid temperature value for testing"""
    return 45.0  # degrees C

@pytest.fixture
def voltage_value() -> float:
    """Provide a valid voltage value for testing"""
    return 3.3  # volts

@pytest.fixture
def hardware() -> Generator[EmulatedHardwareInterface, None, None]:
    """Provide an emulated hardware interface"""
    from tests.emulation.hardware import EmulatedHardwareInterface
    hw = EmulatedHardwareInterface()
    yield hw
    # Clean up by detaching any modules
    hw.detach_module()