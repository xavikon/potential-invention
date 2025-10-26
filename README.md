# CMIS Emulator Framework

[![CI Status](https://github.com/xavikon/silver-octo-invention/workflows/CI/badge.svg)](https://github.com/xavikon/silver-octo-invention/actions)
[![Documentation Status](https://github.com/xavikon/silver-octo-invention/workflows/Documentation/badge.svg)](https://xavikon.github.io/silver-octo-invention/)
[![codecov](https://codecov.io/gh/xavikon/silver-octo-invention/branch/main/graph/badge.svg)](https://codecov.io/gh/xavikon/silver-octo-invention)

The CMIS Emulator Framework is a Python-based testing framework designed to emulate various types of pluggable modules following industry standards such as SFF-8472, SFF-8636, and CMIS. It provides a flexible and extensible platform for testing module management software, control systems, and diagnostics.

## Features

- **Modular Design**: Easily extensible framework for different module types
- **Standards Compliance**: Support for SFF and CMIS standards
- **Hardware Emulation**: Complete I2C and GPIO interface emulation
- **Diagnostic Support**: Real-time monitoring and fault simulation
- **Comprehensive Testing**: Built-in test framework with pytest integration

## Quick Start

### Installation

```bash
git clone https://github.com/yourusername/cmis-emulator.git
cd cmis-emulator
pip install -r requirements.txt
```

### Basic Usage

Here's a simple example of using the emulator:

```python
from cmis.tests.emulation.hardware import EmulatedHardwareInterface
from cmis.tests.emulation.sff import SFFEmulatedModule
from cmis.tests.emulation.base import ModuleConfig, FormFactor, ModuleType, MediaType

# Create module configuration
config = ModuleConfig(
    form_factor=FormFactor.SFP,
    module_type=ModuleType.SFF,
    media_type=MediaType.MMF,
    identifier=0x03,  # SFP/SFP+
    vendor_name="Test Vendor",
    part_number="TEST-001",
    serial_number="12345",
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

# Attach module to hardware
hardware.attach_module(module)

# Read module identifier
identifier = hardware.read_register(0xA0, 0x00)
print(f"Module identifier: 0x{identifier:02X}")
```

## Architecture

The framework consists of several key components:

### Base Classes

- `EmulatedModule`: Abstract base class for all module emulators
- `MemoryMap`: Handles register-based memory access and paging
- `ModuleConfig`: Configuration data structure for modules

### Hardware Interface

The `EmulatedHardwareInterface` class provides:
- I2C read/write operations
- GPIO signal handling
- Module attachment/detachment

### Module Types

1. SFF-based Modules
   - SFP/SFP+
   - QSFP/QSFP+
   - OSFP

2. CMIS-based Modules
   - All form factors with CMIS support
   - Advanced features like individual lane control

## Testing Framework

The framework includes comprehensive testing capabilities:

- Pytest fixtures for hardware and modules
- Diagnostic monitoring tests
- Alarm and threshold tests
- Fault condition simulation
- Status monitoring

## Advanced Features

### Diagnostic Monitoring

```python
# Set and monitor temperature
module.set_temperature(45.0)
temp_raw = (hardware.read_register(0xA2, 96) << 8) | hardware.read_register(0xA2, 97)
temp = temp_raw / 256.0
```

### Fault Simulation

```python
# Simulate TX fault
module.simulate_fault('tx_fault', True)
status = hardware.read_register(0xA2, 110)
assert status & 0x20  # Check TX fault bit
```

## Contributing

Please refer to our [Contributing Guidelines](CONTRIBUTING.md) for information on how to contribute to the project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.