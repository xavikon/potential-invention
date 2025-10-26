"""
Memory map definitions for SFF (Small Form Factor) modules.
Based on SFF-8472 and SFF-8636 specifications.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import IntEnum, auto

class MemoryPages(IntEnum):
    """SFF Memory Page numbers"""
    A0 = 0xA0  # ID/Status Memory Space (read-only)
    A2 = 0xA2  # Diagnostic Memory Space (read/write)

@dataclass
class MemoryAddress:
    """Represents a memory address with its page and offset"""
    page: int
    offset: int
    
    def __str__(self) -> str:
        return f"Page {self.page:02X}h, Offset {self.offset:02X}h"

class SFFRegisters:
    """SFF register definitions with their memory locations"""
    
    # A0h Page Registers (ID/Status)
    IDENTIFIER = MemoryAddress(0xA0, 0x00)  # Type of transceiver
    STATUS = MemoryAddress(0xA0, 0x01)  # Basic module status
    TEMPERATURE = MemoryAddress(0xA2, 0x60)  # Internal temperature
    VOLTAGE = MemoryAddress(0xA2, 0x62)  # Supply voltage
    TX_BIAS = MemoryAddress(0xA2, 0x64)  # TX bias current
    TX_POWER = MemoryAddress(0xA2, 0x66)  # TX output power
    RX_POWER = MemoryAddress(0xA2, 0x68)  # RX input power
    
    # Identification Information
    VENDOR_NAME = MemoryAddress(0xA0, 0x14)  # Vendor name (ASCII)
    VENDOR_OUI = MemoryAddress(0xA0, 0x25)  # Vendor IEEE company ID
    VENDOR_PN = MemoryAddress(0xA0, 0x28)  # Vendor part number
    VENDOR_REV = MemoryAddress(0xA0, 0x38)  # Vendor revision
    VENDOR_SN = MemoryAddress(0xA0, 0x44)  # Vendor serial number
    
    # Diagnostic and Control (A2h Page)
    TEMP_HIGH_ALARM = MemoryAddress(0xA2, 0x00)  # Temperature high alarm threshold
    TEMP_LOW_ALARM = MemoryAddress(0xA2, 0x02)  # Temperature low alarm threshold
    VOLTAGE_HIGH_ALARM = MemoryAddress(0xA2, 0x04)  # Voltage high alarm threshold
    VOLTAGE_LOW_ALARM = MemoryAddress(0xA2, 0x06)  # Voltage low alarm threshold

class RequiredFeatures:
    """
    Definition of required features according to SFF specification.
    Each attribute represents a feature that must be supported.
    """
    IDENTIFIER_CHECK = True
    BASIC_STATUS = True
    VENDOR_INFO = True
    
class OptionalFeatures:
    """
    Definition of optional features according to SFF specification.
    Each attribute represents a feature that may be supported.
    The actual support is determined by reading the module's capabilities.
    """
    TEMPERATURE_MONITORING = False
    VOLTAGE_MONITORING = False
    TX_POWER_MONITORING = False
    RX_POWER_MONITORING = False
    TX_BIAS_MONITORING = False
    ALARM_THRESHOLDS = False