"""!
@mainpage CMIS Emulator Framework
@section intro_sec Introduction
The CMIS Emulator Framework provides a flexible foundation for emulating various types of pluggable
modules including SFP, QSFP, and OSFP in both SFF and CMIS variants. It enables testing of module
management software through a complete emulation of I2C and GPIO interfaces.

@section features_sec Key Features
- Complete emulation of module memory maps and control interfaces
- Support for SFF-8472, SFF-8636, and CMIS standards
- Real-time monitoring and diagnostic capabilities
- Fault injection and error simulation
- Comprehensive test framework

@copyright 2025 Your Company
@license MIT License

@file base.py
@brief Base classes and interfaces for emulating pluggable modules
@details This module provides the foundation for creating software-based models
of various types of pluggable modules, including the base EmulatedModule class,
memory map handling, and configuration structures.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Optional, List, Any

class EmulationError(Exception):
    """!
    Base class for emulation-related errors.
    All custom exceptions in the emulation framework should inherit from this class.
    """
    pass

class FormFactor(Enum):
    """!
    Supported module form factors.
    
    Enumerates the physical form factors supported by the emulation framework:
    - SFP: Small Form-factor Pluggable
    - QSFP: Quad Small Form-factor Pluggable
    - OSFP: Octal Small Form-factor Pluggable
    """
    SFP = "SFP"   #!< Small Form-factor Pluggable
    QSFP = "QSFP" #!< Quad Small Form-factor Pluggable
    OSFP = "OSFP" #!< Octal Small Form-factor Pluggable

class ModuleType(Enum):
    """!
    Types of modules that can be emulated.
    
    Defines the management interface standards supported:
    - SFF: Basic SFF-8472 management interface
    - SFP_PLUS: Enhanced SFF-8472 features
    - QSFP_PLUS: SFF-8636 management interface
    - CMIS: Common Management Interface Specification
    """
    SFF = "SFF"           #!< Basic SFF-8472 management interface
    SFP_PLUS = "SFP+"     #!< Enhanced SFF-8472 features
    QSFP_PLUS = "QSFP+"   #!< SFF-8636 management interface
    CMIS = "CMIS"         #!< Common Management Interface Specification

class MediaType(Enum):
    """!
    Types of media supported by modules.
    
    Enumerates the physical media types that can be emulated:
    - COPPER_PASSIVE: Direct Attach Copper cable
    - COPPER_ACTIVE: Active Copper cable
    - MMF: Multi-mode Fiber interface
    - SMF: Single-mode Fiber interface
    - SR: Short Reach (850nm over MMF)
    - LR: Long Reach (1310nm over SMF)
    """
    COPPER_PASSIVE = "Copper (Passive)" #!< Direct Attach Copper cable
    COPPER_ACTIVE = "Copper (Active)"   #!< Active Copper cable
    MMF = "Multi-mode Fiber"           #!< Multi-mode Fiber interface
    SMF = "Single-mode Fiber"          #!< Single-mode Fiber interface
    SR = "SR (850nm MMF)"              #!< Short Reach (850nm over MMF)
    LR = "LR (1310nm SMF)"             #!< Long Reach (1310nm over SMF)

@dataclass
class ModuleConfig:
    """!
    Configuration for an emulated module.
    
    This dataclass holds all the configuration parameters needed to define a module's
    characteristics and capabilities. It is used when initializing any emulated module.
    
    Example usage:
    @code
    config = ModuleConfig(
        form_factor=FormFactor.SFP,
        module_type=ModuleType.SFP_PLUS,
        media_type=MediaType.SR,
        identifier=0x03,
        vendor_name="Test Vendor",
        part_number="TEST-001",
        serial_number="12345",
        revision="1.0",
        nominal_bit_rate=10.3125,
        max_case_temp=70.0,
        supported_rates=[10.3125],
        num_channels=1,
        max_power_draw=1.0,
        wavelength_nm=850.0
    )
    @endcode
    """
    form_factor: FormFactor       #!< Physical form factor of the module
    module_type: ModuleType       #!< Management interface standard
    media_type: MediaType        #!< Type of physical media supported
    identifier: int              #!< Module identifier code (per SFF-8024)
    vendor_name: str             #!< Module vendor name (max 16 chars)
    part_number: str             #!< Module part number (max 16 chars)
    serial_number: str           #!< Module serial number (max 16 chars)
    revision: str                #!< Module hardware revision (max 4 chars)
    nominal_bit_rate: float      #!< Nominal bit rate in Gbps
    max_case_temp: float        #!< Maximum case temperature in °C
    supported_rates: List[float] #!< List of supported bit rates in Gbps
    num_channels: int           #!< Number of channels (1 for SFP, 4 for QSFP, etc.)
    max_power_draw: float       #!< Maximum power consumption in Watts
    length_meters: Optional[float] = None  #!< Cable length in meters (for copper cables)
    wavelength_nm: Optional[float] = None  #!< Operating wavelength in nanometers (for optical modules)

class MemoryMap:
    """!
    Represents a module's memory map.
    
    The MemoryMap class provides a complete emulation of a module's register-based
    memory interface, including:
    - Multiple memory pages (like A0h and A2h in SFF modules)
    - Page selection mechanism
    - Byte and word access methods
    - Bounds checking and error handling
    
    Example usage:
    @code
    memory = MemoryMap(size=256)  # Create 256-byte pages
    memory.add_page(0xA0)         # Add A0h page
    memory.add_page(0xA2)         # Add A2h page
    
    memory.select_page(0xA0)      # Select A0h page
    memory.write_byte(0, 0x03)    # Write identifier
    
    memory.select_page(0xA2)      # Switch to A2h page
    temp = memory.read_word(96)   # Read temperature register
    @endcode
    """
    
    def __init__(self, size: int = 256):
        """!
        Initialize memory map.
        
        @param size Size of each memory page in bytes (default: 256)
        
        Creates a new memory map with an initial page 0. Additional pages
        can be added using the add_page() method.
        """
        ## Dictionary mapping page numbers to byte arrays
        self._pages: Dict[int, bytearray] = {0: bytearray(size)}
        ## Currently selected memory page
        self._current_page = 0
        ## Size of each memory page in bytes
        self._size = size
    
    def add_page(self, page_number: int) -> None:
        """!
        Add a new memory page to the map.
        
        @param page_number The page number to add (e.g., 0xA0, 0xA2)
        
        Creates a new page initialized to all zeros. If the page already exists,
        this method has no effect.
        """
        if page_number not in self._pages:
            self._pages[page_number] = bytearray(self._size)
    
    @property
    def current_page(self) -> int:
        """!
        Get the currently selected page number.
        
        @return The page number that is currently selected for access
        """
        return self._current_page
    
    def select_page(self, page: int) -> None:
        """!
        Select a memory page for subsequent access.
        
        @param page The page number to select
        @throws EmulationError if the page does not exist
        
        All subsequent read and write operations will access the selected page
        until a different page is selected.
        """
        if page not in self._pages:
            raise EmulationError(f"Page {page} does not exist")
        self._current_page = page
    
    def read_byte(self, address: int) -> int:
        """!
        Read a byte from the current page.
        
        @param address Memory address to read (0-255)
        @return The byte value at the specified address
        @throws EmulationError if address is out of range
        
        Reads a single byte from the specified address in the currently
        selected memory page.
        """
        if not 0 <= address < self._size:
            raise EmulationError(f"Address {address} out of range")
        return self._pages[self._current_page][address]
    
    def write_byte(self, address: int, value: int) -> None:
        """!
        Write a byte to the current page.
        
        @param address Memory address to write (0-255)
        @param value Byte value to write (0-255)
        @throws EmulationError if address or value is out of range
        
        Writes a single byte to the specified address in the currently
        selected memory page.
        """
        if not 0 <= address < self._size:
            raise EmulationError(f"Address {address} out of range")
        if not 0 <= value <= 255:
            raise EmulationError(f"Value {value} out of range")
        self._pages[self._current_page][address] = value
    
    def write_bytes(self, start_address: int, data: bytes) -> None:
        """!
        Write multiple consecutive bytes starting at an address.
        
        @param start_address Starting memory address
        @param data Bytes to write
        @throws EmulationError if the operation would exceed page boundaries
        
        Writes a sequence of bytes to consecutive addresses starting at
        the specified address in the currently selected page.
        """
        if not 0 <= start_address < self._size:
            raise EmulationError(f"Start address {start_address} out of range")
        if start_address + len(data) > self._size:
            raise EmulationError("Data would exceed page size")
        for i, value in enumerate(data):
            self._pages[self._current_page][start_address + i] = value
    
    def read_word(self, address: int) -> int:
        """!
        Read a 16-bit word from the current page.
        
        @param address Memory address of MSB (must have valid LSB at address+1)
        @return 16-bit value composed of [address]=MSB, [address+1]=LSB
        @throws EmulationError if address is out of range
        
        Reads two consecutive bytes and combines them into a 16-bit word.
        The byte at the specified address is treated as the MSB.
        """
        if not 0 <= address < self._size - 1:
            raise EmulationError(f"Address {address} out of range for word access")
        msb = self.read_byte(address)
        lsb = self.read_byte(address + 1)
        return (msb << 8) | lsb
    
    def write_word(self, address: int, value: int) -> None:
        """!
        Write a 16-bit word to the current page.
        
        @param address Memory address for MSB (LSB will be at address+1)
        @param value 16-bit value to write
        @throws EmulationError if address or value is out of range
        
        Splits a 16-bit value into two bytes and writes them to consecutive
        addresses, with the MSB at the specified address.
        """
        if not 0 <= address < self._size - 1:
            raise EmulationError(f"Address {address} out of range for word access")
        if not 0 <= value <= 65535:
            raise EmulationError(f"Value {value} out of range for word")
        msb = (value >> 8) & 0xFF
        lsb = value & 0xFF
        self.write_byte(address, msb)
        self.write_byte(address + 1, lsb)

class EmulatedModule(ABC):
    """!
    Base class for emulated modules.
    
    The EmulatedModule class provides the foundation for implementing module
    emulators. It handles:
    - Memory map management
    - GPIO signal states
    - Basic module status
    - Monitoring values
    - Configuration storage
    
    Derived classes must implement the _initialize_memory_map() and
    update_monitoring() methods to provide module-specific functionality.
    
    Example:
    @code
    class SFFModule(EmulatedModule):
        def _initialize_memory_map(self):
            self.add_memory_pages([0xA0, 0xA2])
            self.memory_map.select_page(0xA0)
            self.memory_map.write_byte(0, self.config.identifier)
            # ... initialize other registers
        
        def update_monitoring(self):
            self.memory_map.select_page(0xA2)
            temp = self._encode_temperature(self._temperature)
            self.memory_map.write_word(96, temp)
            # ... update other monitoring values
    @endcode
    """
    
    def __init__(self, config: ModuleConfig):
        """!
        Initialize emulated module.
        
        @param config Configuration parameters for the module
        
        Sets up the base memory map and initializes all monitoring values
        to their defaults. Derived classes should call this before their
        own initialization.
        """
        self.config = config
        self.memory_map = MemoryMap()
        self._gpio_states = {
            'mod_present': True,
            'interrupt': False,
            'reset': False,
            'lpmode': False
        }
        self._temperature = 25.0  # Default temperature in Celsius
        self._voltage = 3.3      # Default voltage in V
        
        # Initialize monitoring values
        self._tx_disable = False
        self._tx_fault = False
        self._rx_los = False
        self._tx_bias_ma = 0.0
        self._tx_power_mw = 0.0
        self._rx_power_mw = 0.0
        
        # Set default monitoring values based on module type
        if not config.media_type.name.startswith('COPPER'):
            self._tx_bias_ma = 30.0  # Typical bias current
            self._tx_power_mw = 0.5   # Typical TX power
            self._rx_power_mw = 0.4   # Typical RX power
        
        self._initialize_memory_map()
    
    @abstractmethod
    def _initialize_memory_map(self) -> None:
        """Initialize the memory map with module-specific data"""
        pass
    
    def is_present(self) -> bool:
        """Check if module is present"""
        return self.get_gpio_state('mod_present')

    def get_identifier(self) -> int:
        """Get module identifier"""
        return self.config.identifier

    def get_vendor_name(self) -> str:
        """Get module vendor name"""
        return self.config.vendor_name

    def get_part_number(self) -> str:
        """Get module part number"""
        return self.config.part_number

    def get_serial_number(self) -> str:
        """Get module serial number"""
        return self.config.serial_number

    def get_revision(self) -> str:
        """Get module revision"""
        return self.config.revision

    def get_temperature(self) -> float:
        """Get module temperature"""
        return self._temperature

    def get_voltage(self) -> float:
        """Get module voltage"""
        return self._voltage

    def set_temperature(self, temperature: float) -> None:
        """Set module temperature"""
        self._temperature = temperature
        self.update_monitoring()

    def set_voltage(self, voltage: float) -> None:
        """Set module voltage"""
        self._voltage = voltage
        self.update_monitoring()

    def get_gpio_state(self, signal: str) -> bool:
        """Get state of a GPIO signal"""
        if signal not in self._gpio_states:
            raise EmulationError(f"Unknown GPIO signal: {signal}")
        return self._gpio_states[signal]
    
    def set_gpio_state(self, signal: str, state: bool) -> None:
        """Set state of a GPIO signal"""
        if signal not in self._gpio_states:
            raise EmulationError(f"Unknown GPIO signal: {signal}")
        self._gpio_states[signal] = state
        
        # Handle special signals
        if signal == 'reset' and state:
            self._handle_reset()
    
    def read_register(self, address: int) -> int:
        """Read from module's memory map"""
        return self.memory_map.read_byte(address)
    
    def write_register(self, address: int, value: int) -> None:
        """Write to module's memory map"""
        self.memory_map.write_byte(address, value)
    
    def _handle_reset(self) -> None:
        """Handle module reset"""
        # Re-initialize memory map
        self._initialize_memory_map()
        # Reset GPIO states except mod_present
        self._gpio_states.update({
            'interrupt': False,
            'reset': False,
            'lpmode': False
        })
    
    def _encode_temperature(self, temp: float) -> int:
        """Encode temperature value for memory map"""
        # Convert to 16-bit signed value in 1/256 degree units
        # Round to nearest 1/256 to avoid precision loss
        val = round(temp * 256.0)
        # Handle negative temperatures correctly
        if val < 0:
            val = val & 0xFFFF  # Convert to unsigned 16-bit
        return val & 0xFFFF  # Ensure 16-bit unsigned value
    
    def _encode_voltage(self, voltage: float) -> int:
        """Encode voltage value for memory map"""
        return int(voltage * 10000.0)  # Convert to units of 100µV
    
    def _encode_power(self, power: float) -> int:
        """Encode optical power value for memory map"""
        # Clamp power to non-negative value
        power = max(0.0, power)
        # Convert to units of 0.1µW and ensure 16-bit unsigned
        return int(power * 10000.0) & 0xFFFF
    
    def _encode_bias(self, bias: float) -> int:
        """Encode bias current value for memory map"""
        return int(bias * 500.0)  # Convert to units of 2µA
    
    def _write_string(self, start_address: int, string: str, max_length: int) -> None:
        """Write a string to memory map with null termination"""
        # Convert string to bytes, limiting length to max_length - 1 to leave room for null termination
        encoded = string.encode('ascii')[:max_length-1]
        # Write string bytes
        self.memory_map.write_bytes(start_address, encoded)
        # Add null terminator
        self.memory_map.write_byte(start_address + len(encoded), 0)
        # Fill remaining space with zeros
        remaining = max_length - len(encoded) - 1
        if remaining > 0:
            self.memory_map.write_bytes(start_address + len(encoded) + 1, b'\x00' * remaining)
    
    def add_memory_pages(self, pages: List[int]) -> None:
        """Add multiple memory pages"""
        for page in pages:
            self.memory_map.add_page(page)
    
    @abstractmethod
    def update_monitoring(self) -> None:
        """Update monitoring values in memory map"""
        pass