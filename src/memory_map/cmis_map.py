"""
Memory map definitions for CMIS (Common Management Interface Specification).
Based on the CMIS specification.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import IntEnum, auto

class MemoryPages(IntEnum):
    """CMIS Memory Page numbers"""
    LOWER = 0x00
    UPPER = 0x01
    USER_EEPROM = 0x02
    PASSWORD_CHANGE = 0x7F
    STATUS_AND_CONTROL = 0x80
    STATUS_AND_CONTROL_2 = 0x81
    STATUS_AND_CONTROL_3 = 0x82
    FLAGS = 0x83
    MASKS = 0x84
    CUSTOM_MASKS = 0x85
    BANK_MASKS = 0x86
    CUSTOM_BANK_MASKS = 0x87

@dataclass
class MemoryAddress:
    """Represents a memory address with its page and offset"""
    page: int
    offset: int
    
    def __str__(self) -> str:
        return f"Page {self.page:02X}h, Offset {self.offset:02X}h"

class CMISRegisters:
    """CMIS register definitions with their memory locations"""
    
    # Lower Memory Page (0x00)
    IDENTIFIER = MemoryAddress(0x00, 0x00)  # Type of transceiver
    STATUS = MemoryAddress(0x00, 0x01)  # Status indicators
    LANE_STATUS_FLAGS = MemoryAddress(0x00, 0x02)  # Status of each lane
    TEMPERATURE = MemoryAddress(0x00, 0x03)  # Module temperature
    VOLTAGE = MemoryAddress(0x00, 0x05)  # Supply voltage
    VENDOR_NAME = MemoryAddress(0x00, 0x10)  # Vendor name (ASCII)
    VENDOR_PART_NUMBER = MemoryAddress(0x00, 0x20)  # Vendor part number (ASCII)
    VENDOR_REVISION = MemoryAddress(0x00, 0x30)  # Vendor revision (ASCII)
    VENDOR_SERIAL_NUMBER = MemoryAddress(0x00, 0x40)  # Vendor serial number (ASCII)
    
    # Status and Control Pages
    MODULE_TYPE = MemoryAddress(0x80, 0x00)  # Module type identification
    CONFIGURATION = MemoryAddress(0x80, 0x01)  # Module configuration control
    FEATURE_SUPPORT = MemoryAddress(0x80, 0x02)  # Supported features
    DATA_PATH_CONTROL = MemoryAddress(0x80, 0x10)  # Data path configuration
    TX_CONTROL = MemoryAddress(0x80, 0x20)  # Transmitter control
    RX_CONTROL = MemoryAddress(0x80, 0x30)  # Receiver control
    
    # Status Flags and Alarms
    FLAGS = MemoryAddress(0x83, 0x00)  # Status flags and indicators
    ALARMS = MemoryAddress(0x83, 0x01)  # Active alarms
    WARNINGS = MemoryAddress(0x83, 0x02)  # Active warnings

class RequiredFeatures:
    """
    Definition of required features according to CMIS specification.
    Each attribute represents a feature that must be supported.
    """
    TEMPERATURE_MONITORING = True
    VOLTAGE_MONITORING = True
    IDENTIFIER_CHECK = True
    STATUS_MONITORING = True
    
class OptionalFeatures:
    """
    Definition of optional features according to CMIS specification.
    Each attribute represents a feature that may be supported.
    The actual support is determined by reading the module's capabilities.
    """
    LANE_MONITORING = False
    ADVANCED_MONITORING = False
    PROGRAMMABLE_POWER = False
    PROGRAMMABLE_RATES = False