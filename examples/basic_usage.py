"""
Example usage of the pluggable module management system.
This script demonstrates how to use the various components to manage
and monitor pluggable modules.
"""

from typing import Optional
import time
from src.hardware import HardwareInterface
from src.detection import ModuleDetector
from src.modules import ModuleCapability, BaseModule, SFFModule, CMISModule
from src.capabilities import CapabilityManager

def print_module_info(module: BaseModule) -> None:
    """Print detailed information about a module"""
    ident = module.get_identification()
    print(f"\nModule Information:")
    print(f"  Type: {ident.type.name}")
    print(f"  Vendor: {ident.vendor_name}")
    print(f"  Part Number: {ident.part_number}")
    print(f"  Serial Number: {ident.serial_number}")
    print(f"  Revision: {ident.revision}")

def print_module_status(module: BaseModule) -> None:
    """Print current module status"""
    status = module.get_status()
    print(f"\nModule Status:")
    if status.temperature is not None:
        print(f"  Temperature: {status.temperature:.2f}°C")
    if status.voltage is not None:
        print(f"  Voltage: {status.voltage:.3f}V")
    if status.tx_power:
        print(f"  TX Power: {', '.join(f'{p:.2f}dBm' for p in status.tx_power)}")
    if status.rx_power:
        print(f"  RX Power: {', '.join(f'{p:.2f}dBm' for p in status.rx_power)}")
    if status.tx_bias:
        print(f"  TX Bias: {', '.join(f'{b:.2f}mA' for b in status.tx_bias)}")

def print_capability_info(module: BaseModule, capability_mgr: CapabilityManager) -> None:
    """Print capability information for a module"""
    validation = capability_mgr.validate_module(module)
    print(f"\nCapability Information:")
    
    if validation['missing_required']:
        print("  Missing Required Capabilities:")
        for cap in validation['missing_required']:
            print(f"    - {capability_mgr.describe_capability(cap)}")
    
    print("\n  Supported Optional Capabilities:")
    for cap in validation['supported_optional']:
        verified = capability_mgr.verify_capability(module, cap)
        status = "Functional" if verified else "Non-functional"
        print(f"    - {capability_mgr.describe_capability(cap)} ({status})")
    
    print("\n  Unsupported Optional Capabilities:")
    for cap in validation['unsupported_optional']:
        print(f"    - {capability_mgr.describe_capability(cap)}")

def monitor_module(module: BaseModule, interval: float = 1.0) -> None:
    """Continuously monitor a module's status"""
    try:
        print("\nStarting module monitoring (Ctrl+C to stop)...")
        while True:
            status = module.get_status()
            print(f"\rTemp: {status.temperature:.1f}°C, "
                  f"Voltage: {status.voltage:.2f}V", end='')
            if status.tx_power:
                print(f", TX Power: {status.tx_power[0]:.1f}dBm", end='')
            if status.rx_power:
                print(f", RX Power: {status.rx_power[0]:.1f}dBm", end='')
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")

def main() -> None:
    """Main function demonstrating module management"""
    print("Initializing module management system...")
    
    # Create hardware interface
    hw = HardwareInterface()
    
    # Create module detector
    detector = ModuleDetector(hw)
    
    # Create capability manager
    capability_mgr = CapabilityManager()
    
    # Wait for module
    print("Waiting for module insertion...")
    while not detector.is_module_present():
        time.sleep(0.1)
    
    print("Module detected!")
    
    # Identify module type
    module_type = detector.identify_module_type()
    print(f"Detected module type: {module_type.name}")
    
    # Create appropriate module handler
    module: Optional[BaseModule] = None
    if module_type == module_type.SFF:
        module = SFFModule(hw)
    elif module_type == module_type.CMIS:
        module = CMISModule(hw)
    else:
        print("Unknown module type!")
        return
    
    # Initialize module
    try:
        module.initialize()
    except Exception as e:
        print(f"Error initializing module: {str(e)}")
        return
    
    # Print module information
    print_module_info(module)
    
    # Print capability information
    print_capability_info(module, capability_mgr)
    
    # Print current status
    print_module_status(module)
    
    # Monitor the module
    monitor_module(module)

if __name__ == '__main__':
    main()