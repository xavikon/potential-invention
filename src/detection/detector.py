"""
Module detection and identification functionality.
Provides tools to detect module presence and identify module type.
"""
from enum import Enum, auto
from typing import Optional, Tuple, Dict, Any, cast

from ..hardware import HardwareInterface, GPIOSignal
from ..memory_map import CMISRegisters, SFFRegisters

class ModuleType(Enum):
    """Supported module types"""
    UNKNOWN = auto()
    SFF = auto()
    CMIS = auto()

class DetectorError(Exception):
    """Base class for detector errors"""
    pass

class NoModuleError(DetectorError):
    """Error raised when no module is present"""
    pass

# Type definitions
ModuleInfo = Dict[str, Any]

class ModuleDetector:
    """
    Handles detection and identification of pluggable modules.
    """
    
    def __init__(self, hardware: HardwareInterface):
        """
        Initialize the detector with a hardware interface.
        
        Args:
            hardware: The hardware interface to use for communication
        """
        self.hw = hardware
        
    def is_module_present(self) -> bool:
        """
        Check if a module is physically present.
        
        Returns:
            True if a module is present, False otherwise
        """
        return self.hw.module_present()
    
    def identify_module_type(self) -> ModuleType:
        """
        Identify the type of module that is present.
        This is done by reading the identifier bytes and checking
        the module's response pattern.
        
        Returns:
            The detected module type
        
        Raises:
            NoModuleError: If no module is present
        """
        if not self.is_module_present():
            raise NoModuleError("No module detected")
        
        # Try reading CMIS identifier first
        try:
            cmis_id = self.hw.read_register(CMISRegisters.IDENTIFIER.offset)
            if cmis_id in [0x0D, 0x11]:  # Common CMIS identifier values
                return ModuleType.CMIS
        except Exception:
            pass  # Continue to SFF check if CMIS read fails
        
        # Try reading SFF identifier
        try:
            sff_id = self.hw.read_register(SFFRegisters.IDENTIFIER.offset)
            if sff_id in [0x03, 0x0C]:  # Common SFF identifier values
                return ModuleType.SFF
        except Exception:
            pass
        
        return ModuleType.UNKNOWN
    
    def wait_for_module(self, timeout_seconds: Optional[float] = None) -> bool:
        """
        Wait for a module to be inserted.
        
        Args:
            timeout_seconds: Maximum time to wait in seconds, or None to wait indefinitely
            
        Returns:
            True if a module was detected within the timeout, False otherwise
        """
        # Note: In a real implementation, this would use a proper timeout mechanism
        # For now, we just do a single check
        return self.is_module_present()
    
    def get_module_info(self) -> Tuple[ModuleType, ModuleInfo]:
        """
        Get detailed information about the detected module.
        
        Returns:
            A tuple containing:
            - The module type
            - A dictionary of basic module information
            
        Raises:
            NoModuleError: If no module is present
        """
        module_type = self.identify_module_type()
        info: ModuleInfo = {"type": module_type}
        
        if module_type == ModuleType.CMIS:
            # Read CMIS basic information
            try:
                vendor_info: Dict[str, str] = {
                    "vendor_name": self._read_string(CMISRegisters.VENDOR_NAME.offset, 16),
                    "part_number": self._read_string(CMISRegisters.VENDOR_PART_NUMBER.offset, 16),
                    "serial_number": self._read_string(CMISRegisters.VENDOR_SERIAL_NUMBER.offset, 16),
                    "revision": self._read_string(CMISRegisters.VENDOR_REVISION.offset, 2)
                }
                info.update(cast(Dict[str, Any], vendor_info))
            except Exception as e:
                info.update(cast(Dict[str, Any], {"error": f"Error reading CMIS info: {str(e)}"}))
                
        elif module_type == ModuleType.SFF:
            # Read SFF basic information
            try:
                vendor_info: Dict[str, str] = {
                    "vendor_name": self._read_string(SFFRegisters.VENDOR_NAME.offset, 16),
                    "part_number": self._read_string(SFFRegisters.VENDOR_PN.offset, 16),
                    "serial_number": self._read_string(SFFRegisters.VENDOR_SN.offset, 16),
                    "revision": self._read_string(SFFRegisters.VENDOR_REV.offset, 4)
                }
                info.update(cast(Dict[str, Any], vendor_info))
            except Exception as e:
                info.update(cast(Dict[str, Any], {"error": f"Error reading SFF info: {str(e)}"}))
        
        return module_type, info
    
    def _read_string(self, start_address: int, length: int) -> str:
        """
        Read a string from consecutive memory addresses.
        
        Args:
            start_address: Starting memory address
            length: Number of bytes to read
            
        Returns:
            The decoded string, with non-printable characters removed
        """
        bytes_data = []
        for offset in range(length):
            try:
                byte = self.hw.read_register(start_address + offset)
                bytes_data.append(byte)
            except Exception:
                break
                
        # Convert bytes to string, removing non-printable characters
        return "".join(chr(b) for b in bytes_data if 32 <= b <= 126)