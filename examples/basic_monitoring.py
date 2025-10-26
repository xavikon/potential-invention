"""!
@file basic_monitoring.py
@brief Example of basic module monitoring and control.

This example demonstrates how to:
1. Create and configure a module
2. Set up monitoring
3. Read diagnostic values
4. Handle alarms and thresholds
"""
from cmis.tests.emulation.hardware import EmulatedHardwareInterface
from cmis.tests.emulation.sff import SFFEmulatedModule
from cmis.tests.emulation.base import ModuleConfig, FormFactor, ModuleType, MediaType
import time

def main():
    # Create module configuration
    config = ModuleConfig(
        form_factor=FormFactor.SFP,
        module_type=ModuleType.SFP_PLUS,
        media_type=MediaType.SR,
        identifier=0x03,  # SFP/SFP+
        vendor_name="Example Vendor",
        part_number="EX-SFP-SR",
        serial_number="ABC123",
        revision="1.0",
        nominal_bit_rate=10.3125,  # 10G
        max_case_temp=70.0,
        supported_rates=[10.3125],
        num_channels=1,
        max_power_draw=1.0,
        wavelength_nm=850.0
    )

    # Create hardware interface and module
    hardware = EmulatedHardwareInterface()
    module = SFFEmulatedModule(config)

    # Attach module and verify presence
    hardware.attach_module(module)
    if not hardware.get_module_present():
        print("Error: Module not present")
        return

    # Read basic information
    print("Module Information:")
    print("-" * 20)
    
    hardware.write_register(0xA0, 0x7F, 0xA0)  # Select A0h page
    identifier = hardware.read_register(0xA0, 0x00)
    print(f"Identifier: 0x{identifier:02X}")
    
    # Read vendor name
    vendor_name = ""
    for i in range(16):
        char = hardware.read_register(0xA0, 0x14 + i)
        if char == 0:
            break
        vendor_name += chr(char)
    print(f"Vendor: {vendor_name}")
    
    # Monitor diagnostics in a loop
    print("\nDiagnostic Monitoring:")
    print("-" * 20)
    
    try:
        while True:
            # Switch to A2h page for diagnostics
            hardware.write_register(0xA2, 0x7F, 0xA2)
            
            # Read temperature (bytes 96-97)
            temp_raw = (hardware.read_register(0xA2, 96) << 8) | hardware.read_register(0xA2, 97)
            temp = temp_raw / 256.0
            
            # Read voltage (bytes 98-99)
            voltage_raw = (hardware.read_register(0xA2, 98) << 8) | hardware.read_register(0xA2, 99)
            voltage = voltage_raw / 10000.0
            
            # Read TX bias current (bytes 100-101)
            bias_raw = (hardware.read_register(0xA2, 100) << 8) | hardware.read_register(0xA2, 101)
            bias = bias_raw * 2.0 / 1000.0  # Convert to mA
            
            # Read status and alarms
            status = hardware.read_register(0xA2, 110)
            alarms = hardware.read_register(0xA2, 112)
            
            # Display values
            print(f"\rTemp: {temp:5.1f}°C  Voltage: {voltage:4.2f}V  Bias: {bias:5.1f}mA", end="")
            
            # Check for alarms
            if alarms & 0x80:
                print("\nWarning: High temperature alarm!")
            
            # Update module state
            module.update_monitoring()
            
            time.sleep(1)  # Update every second
            
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped")
        hardware.detach_module()

if __name__ == "__main__":
    main()