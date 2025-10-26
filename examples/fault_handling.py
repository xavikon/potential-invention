"""!
@file fault_handling.py
@brief Example of fault detection and handling.

This example demonstrates:
1. Setting up fault monitoring
2. Handling TX faults
3. Detecting RX LOS conditions
4. Proper fault recovery
"""
from cmis.tests.emulation.hardware import EmulatedHardwareInterface
from cmis.tests.emulation.sff import SFFEmulatedModule
from cmis.tests.emulation.base import ModuleConfig, FormFactor, ModuleType, MediaType
import time

def check_alarms(hardware):
    """Helper function to check and report alarm conditions"""
    status = hardware.read_register(0xA2, 110)
    
    alarms = []
    if status & 0x40:
        alarms.append("TX Disabled")
    if status & 0x20:
        alarms.append("TX Fault")
    if status & 0x10:
        alarms.append("RX LOS")
    
    return alarms

def main():
    # Create configuration for an optical module
    config = ModuleConfig(
        form_factor=FormFactor.SFP,
        module_type=ModuleType.SFP_PLUS,
        media_type=MediaType.SR,
        identifier=0x03,
        vendor_name="Example Vendor",
        part_number="EX-SFP-SR",
        serial_number="ABC123",
        revision="1.0",
        nominal_bit_rate=10.3125,
        max_case_temp=70.0,
        supported_rates=[10.3125],
        num_channels=1,
        max_power_draw=1.0,
        wavelength_nm=850.0
    )

    # Set up hardware and module
    hardware = EmulatedHardwareInterface()
    module = SFFEmulatedModule(config)
    hardware.attach_module(module)

    print("Module Fault Handling Demo")
    print("=" * 40)
    print("Initial state:")
    alarms = check_alarms(hardware)
    if alarms:
        print(f"Active alarms: {', '.join(alarms)}")
    else:
        print("No active alarms")

    try:
        # Demonstrate TX fault handling
        print("\n1. Simulating TX fault")
        module.simulate_fault('tx_fault', True)
        time.sleep(1)
        
        print("Checking alarms...")
        alarms = check_alarms(hardware)
        print(f"Active alarms: {', '.join(alarms)}")
        
        # Read TX power during fault
        power_raw = (hardware.read_register(0xA2, 102) << 8) | hardware.read_register(0xA2, 103)
        power = power_raw * 0.0001  # Convert to mW
        print(f"TX Power during fault: {power:.3f} mW")
        
        # Clear TX fault
        print("\nClearing TX fault")
        module.simulate_fault('tx_fault', False)
        time.sleep(1)
        
        alarms = check_alarms(hardware)
        if alarms:
            print(f"Active alarms: {', '.join(alarms)}")
        else:
            print("No active alarms")
        
        # Demonstrate RX LOS handling
        print("\n2. Simulating RX LOS")
        module.simulate_fault('rx_los', True)
        time.sleep(1)
        
        print("Checking alarms...")
        alarms = check_alarms(hardware)
        print(f"Active alarms: {', '.join(alarms)}")
        
        # Read RX power during LOS
        power_raw = (hardware.read_register(0xA2, 104) << 8) | hardware.read_register(0xA2, 105)
        power = power_raw * 0.0001  # Convert to mW
        print(f"RX Power during LOS: {power:.3f} mW")
        
        # Clear RX LOS
        print("\nClearing RX LOS")
        module.simulate_fault('rx_los', False)
        time.sleep(1)
        
        alarms = check_alarms(hardware)
        if alarms:
            print(f"Active alarms: {', '.join(alarms)}")
        else:
            print("No active alarms")
        
        # Demonstrate TX disable
        print("\n3. Testing TX disable")
        module.set_tx_disable(True)
        time.sleep(1)
        
        print("Checking alarms...")
        alarms = check_alarms(hardware)
        print(f"Active alarms: {', '.join(alarms)}")
        
        print("\nRe-enabling TX")
        module.set_tx_disable(False)
        time.sleep(1)
        
        alarms = check_alarms(hardware)
        if alarms:
            print(f"Active alarms: {', '.join(alarms)}")
        else:
            print("No active alarms")

    except KeyboardInterrupt:
        print("\nDemo stopped by user")
    finally:
        hardware.detach_module()
        print("\nModule detached")

if __name__ == "__main__":
    main()