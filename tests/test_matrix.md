# Module Test Feature Matrix

## Module Types
- SFF-8472 (SFP)
- SFF-8636 (QSFP)
- CMIS 4.0 (SFP/QSFP/OSFP)

## Common Features (All Module Types)
- [x] Module presence detection
- [x] Module identification
  - Vendor name
  - Part number
  - Serial number
  - Revision
- [x] Temperature monitoring
- [x] Voltage monitoring
- [x] Status flags
  - Temperature alarms
  - Voltage alarms

## SFF-8472 Specific Features
- [x] Digital diagnostics
  - TX bias current
  - TX output power
  - RX input power
  - TX disable control
  - RX loss of signal
  - TX fault
- [x] Alarm/warning thresholds
- [x] Calibration constants
- [x] External calibration

## SFF-8636 Specific Features
- [x] Per-channel diagnostics (4 channels)
- [x] Channel TX disable control
- [x] Power class support
- [x] CDR control
- [x] Page switching
- [x] Extended identifier support
- [x] Module state control

## CMIS 4.0 Specific Features
- [x] Application advertisement
- [x] Data path configuration
- [x] Module state machine
- [x] Active/inactive firmware
- [x] Bank selection
- [x] Advanced monitoring
  - Per-lane statistics
  - FEC statistics
  - PRBS diagnostics
- [x] Control features
  - TX equalization
  - RX emphasis
  - Pre-emphasis
  - Post-emphasis
- [x] Module capabilities
  - Supported data rates
  - Media type support
  - Host interface support

## Test Categories
1. Basic Functionality
   - Module detection
   - Memory map access
   - Basic identification
   - Temperature/voltage monitoring

2. Digital Diagnostics
   - Power measurements
   - Current measurements
   - Status flags
   - Thresholds

3. Control Functions
   - TX disable
   - Reset control
   - Page selection
   - Bank switching

4. Advanced Features
   - Application switching
   - Data path configuration
   - Diagnostics
   - Statistics

5. Error Handling
   - Invalid memory access
   - Unsupported features
   - Protocol violations
   - Timing constraints

6. State Machine
   - State transitions
   - Error recovery
   - Power management

7. Performance
   - Read/write timing
   - Multiple page access
   - Bulk operations

## Test Environment Requirements
1. Module Emulation
   - Hardware interface emulation
   - Memory map simulation
   - Timing simulation
   - Error injection

2. Test Framework
   - Automated test execution
   - Test case organization
   - Fixture management
   - Result reporting

3. Reporting Requirements
   - Test coverage metrics
   - Pass/fail statistics
   - Performance metrics
   - Error logs
   - Test execution time