"""!
@file temperature_alarm.py
@brief Example of temperature alarm monitoring.

This example demonstrates:
1. Setting temperature alarm thresholds
2. Monitoring temperature changes
3. Detecting and handling alarms
4. Proper alarm recovery
"""
from cmis.tests.emulation.hardware import EmulatedHardwareInterface
from cmis.tests.emulation.sff import SFFEmulatedModule
from cmis.tests.emulation.base import ModuleConfig, FormFactor, ModuleType, MediaType
import time

def set_temp_thresholds(hardware, high_alarm=75.0, low_alarm=0.0,
                       high_warn=70.0, low_warn=5.0):
    """Set temperature alarm and warning thresholds"""
    hardware.write_register(0xA2, 0x7F, 0xA2)  # Select A2h page
    
    # High alarm (bytes 0-1)
    temp = int(high_alarm * 256.0)
    hardware.write_register(0xA2, 0, (temp >> 8) & 0xFF)
    hardware.write_register(0xA2, 1, temp & 0xFF)
    
    # Low alarm (bytes 2-3)
    temp = int(low_alarm * 256.0)
    hardware.write_register(0xA2, 2, (temp >> 8) & 0xFF)
    hardware.write_register(0xA2, 3, temp & 0xFF)
    
    # High warning (bytes 4-5)
    temp = int(high_warn * 256.0)
    hardware.write_register(0xA2, 4, (temp >> 8) & 0xFF)
    hardware.write_register(0xA2, 5, temp & 0xFF)
    
    # Low warning (bytes 6-7)
    temp = int(low_warn * 256.0)
    hardware.write_register(0xA2, 6, (temp >> 8) & 0xFF)
    hardware.write_register(0xA2, 7, temp & 0xFF)

def get_temperature(hardware):
    """Read current temperature"""
    hardware.write_register(0xA2, 0x7F, 0xA2)  # Select A2h page
    temp_raw = (hardware.read_register(0xA2, 96) << 8) | hardware.read_register(0xA2, 97)
    return temp_raw / 256.0

def check_temp_alarms(hardware):
    """Check temperature alarm status"""
    alarms = hardware.read_register(0xA2, 112)
    warnings = hardware.read_register(0xA2, 113)
    
    status = []
    if alarms & 0x80:
        status.append("HIGH ALARM")
    if alarms & 0x40:
        status.append("LOW ALARM")
    if warnings & 0x80:
        status.append("HIGH WARNING")
    if warnings & 0x40:
        status.append("LOW WARNING")
    
    return status

def main():
    # Create module configuration
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

    # Configure temperature thresholds
    print("Setting temperature thresholds:")
    print("High alarm:  75.0°C")
    print("Low alarm:    0.0°C")
    print("High warn:   70.0°C")
    print("Low warn:     5.0°C")
    set_temp_thresholds(hardware)

    try:
        print("\nTemperature monitoring started")
        print("=" * 40)
        
        # Test temperature ramping
        temps = [25.0, 50.0, 65.0, 72.0, 78.0, 65.0, 35.0, 2.0, -2.0, 25.0]
        
        for temp in temps:
            # Set new temperature
            module.set_temperature(temp)
            
            # Read current temperature and check alarms
            current_temp = get_temperature(hardware)
            alarms = check_temp_alarms(hardware)
            
            # Display status
            status = f"Temperature: {current_temp:5.1f}°C"
            if alarms:
                status += f" - {', '.join(alarms)}"
            print(status)
            
            time.sleep(1)
        
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
    finally:
        hardware.detach_module()
        print("\nModule detached")

if __name__ == "__main__":
    main()