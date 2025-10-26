"""
Pre-defined configurations for various types of pluggable modules.
These configurations can be used to create emulated modules with
realistic characteristics.
"""
from typing import Dict, List
from .base import ModuleConfig, FormFactor, ModuleType, MediaType

# Direct Attach Copper (DAC) Configurations
DAC_CONFIGS: Dict[str, ModuleConfig] = {
    'SFP_DAC_1M': ModuleConfig(
        form_factor=FormFactor.SFP,
        module_type=ModuleType.SFF,
        media_type=MediaType.COPPER_PASSIVE,
        identifier=0x03,
        vendor_name="Test Vendor",
        part_number="DAC-SFP-1M",
        serial_number="DAC00001",
        revision="A1",
        nominal_bit_rate=25.0,
        max_case_temp=70.0,
        supported_rates=[10.0, 25.0],
        num_channels=1,
        max_power_draw=1.0,
        length_meters=1.0
    ),
    
    'QSFP_DAC_3M': ModuleConfig(
        form_factor=FormFactor.QSFP,
        module_type=ModuleType.SFF,
        media_type=MediaType.COPPER_PASSIVE,
        identifier=0x0C,
        vendor_name="Test Vendor",
        part_number="DAC-QSFP-3M",
        serial_number="DAC00002",
        revision="A1",
        nominal_bit_rate=100.0,
        max_case_temp=70.0,
        supported_rates=[40.0, 100.0],
        num_channels=4,
        max_power_draw=1.5,
        length_meters=3.0
    ),
    
    'OSFP_DAC_2M': ModuleConfig(
        form_factor=FormFactor.OSFP,
        module_type=ModuleType.CMIS,
        media_type=MediaType.COPPER_PASSIVE,
        identifier=0x0D,
        vendor_name="Test Vendor",
        part_number="DAC-OSFP-2M",
        serial_number="DAC00003",
        revision="A1",
        nominal_bit_rate=400.0,
        max_case_temp=70.0,
        supported_rates=[200.0, 400.0],
        num_channels=8,
        max_power_draw=2.0,
        length_meters=2.0
    )
}

# Optical Module Configurations
OPTICAL_CONFIGS: Dict[str, ModuleConfig] = {
    'SFP_SR': ModuleConfig(
        form_factor=FormFactor.SFP,
        module_type=ModuleType.SFF,
        media_type=MediaType.MMF,
        identifier=0x03,
        vendor_name="Test Vendor",
        part_number="SFP-SR-25G",
        serial_number="OPT00001",
        revision="A1",
        nominal_bit_rate=25.0,
        max_case_temp=70.0,
        supported_rates=[10.0, 25.0],
        num_channels=1,
        max_power_draw=1.0,
        wavelength_nm=850.0
    ),
    
    'SFP_LR': ModuleConfig(
        form_factor=FormFactor.SFP,
        module_type=ModuleType.SFF,
        media_type=MediaType.SMF,
        identifier=0x03,
        vendor_name="Test Vendor",
        part_number="SFP-LR-25G",
        serial_number="OPT00002",
        revision="A1",
        nominal_bit_rate=25.0,
        max_case_temp=70.0,
        supported_rates=[10.0, 25.0],
        num_channels=1,
        max_power_draw=1.2,
        wavelength_nm=1310.0
    ),
    
    'QSFP_SR4': ModuleConfig(
        form_factor=FormFactor.QSFP,
        module_type=ModuleType.SFF,
        media_type=MediaType.MMF,
        identifier=0x0C,
        vendor_name="Test Vendor",
        part_number="QSFP-SR4-100G",
        serial_number="OPT00003",
        revision="A1",
        nominal_bit_rate=100.0,
        max_case_temp=70.0,
        supported_rates=[40.0, 100.0],
        num_channels=4,
        max_power_draw=2.5,
        wavelength_nm=850.0
    ),
    
    'QSFP_DR4': ModuleConfig(
        form_factor=FormFactor.QSFP,
        module_type=ModuleType.CMIS,
        media_type=MediaType.SMF,
        identifier=0x0D,
        vendor_name="Test Vendor",
        part_number="QSFP-DR4-400G",
        serial_number="OPT00004",
        revision="A1",
        nominal_bit_rate=400.0,
        max_case_temp=70.0,
        supported_rates=[100.0, 400.0],
        num_channels=4,
        max_power_draw=3.5,
        wavelength_nm=1310.0
    ),
    
    'QSFP_FR4': ModuleConfig(
        form_factor=FormFactor.QSFP,
        module_type=ModuleType.CMIS,
        media_type=MediaType.SMF,
        identifier=0x0D,
        vendor_name="Test Vendor",
        part_number="QSFP-FR4-400G",
        serial_number="OPT00005",
        revision="A1",
        nominal_bit_rate=400.0,
        max_case_temp=70.0,
        supported_rates=[100.0, 400.0],
        num_channels=4,
        max_power_draw=4.0,
        wavelength_nm=1310.0
    ),
    
    'OSFP_LR4': ModuleConfig(
        form_factor=FormFactor.OSFP,
        module_type=ModuleType.CMIS,
        media_type=MediaType.SMF,
        identifier=0x0D,
        vendor_name="Test Vendor",
        part_number="OSFP-LR4-400G",
        serial_number="OPT00006",
        revision="A1",
        nominal_bit_rate=400.0,
        max_case_temp=70.0,
        supported_rates=[200.0, 400.0],
        num_channels=4,
        max_power_draw=4.5,
        wavelength_nm=1310.0
    )
}