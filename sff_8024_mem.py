"""
sff8024_memory_map.py

This file defines the memory spaces and layouts as specified in SFF-8024 v4.12,
SFF-8472 v12.4, and SFF-8636 v2.11.

It provides a structured way to access and interpret the EEPROM data of
optical transceivers conforming to these standards.
"""

# --- Constants and Bit Masks ---

# Common Page 00h addresses
IDENTIFIER_ADDR = 0x00
EXT_IDENTIFIER_ADDR = 0x01
CONNECTOR_ADDR = 0x02
TRANSCEIVER_TECHNOLOGY_ADDR = 0x03
ENCODING_ADDR = 0x0B
NOMINAL_BIT_RATE_ADDR = 0x0D
LENGTH_SMF_KM_ADDR = 0x0E
LENGTH_OM3_ADDR = 0x10
VENDOR_NAME_START_ADDR = 0x14
VENDOR_OUI_START_ADDR = 0x25
VENDOR_PN_START_ADDR = 0x2C
VENDOR_REV_START_ADDR = 0x3C
WAVELENGTH_ADDR = 0x40
CC_DMI_ADDR = 0x5F # Check Code for lower memory
OPTIONS_ADDR = 0x41
DIAG_MON_TYPE_ADDR = 0x5C # For SFF-8472
ENHANCED_OPTIONS_ADDR = 0x5D # For SFF-8472
CC_BASE_ADDR = 0x3F # Check Code for base ID Fields

# SFF-8636 Specific (QSFP/QSFP28)
QSFP_IDENTIFIER_ADDR = 0x00
QSFP_STATUS_INDICATORS_ADDR = 0x02
QSFP_DIAG_CAPABILITY_ADDR = 0x5C
QSFP_REVISION_ADDR = 0x01 # Identifier for 8636 and CMIS
QSFP_VENDOR_NAME_START_ADDR = 0xA1 # Page 00h, SFF-8636
QSFP_VENDOR_OUI_START_ADDR = 0xB2 # Page 00h, SFF-8636
QSFP_PART_NUMBER_START_ADDR = 0xC0 # Page 00h, SFF-8636
QSFP_REVISION_NUMBER_START_ADDR = 0xCE # Page 00h, SFF-8636

# --- Helper Functions (for decoding specific fields) ---

def decode_identifier(byte_value):
    """Decodes the Identifier byte (byte 0) based on SFF-8024."""
    identifiers = {
        0x00: "No transceiver present",
        0x01: "GBIC",
        0x02: "Module (e.g., SFP, XFP, XENPAK, X2, XFP, XFP)",
        0x03: "SFP/SFP+/SFP28/SFP56/SFP-DD",
        0x04: "QSFP/QSFP+/QSFP28/QSFP56/QSFP-DD",
        0x08: "OSFP",
        0x0C: "CMIS (e.g., OSFP-XD, QSFP-DD800)",
        # Add more as per SFF-8024 v4.12 Table 3-1 "Identifier Codes"
    }
    return identifiers.get(byte_value, f"Unknown (0x{byte_value:02X})")

def decode_connector_type(byte_value):
    """Decodes the Connector Type byte (byte 2) based on SFF-8024."""
    connectors = {
        0x00: "Unknown",
        0x01: "SC",
        0x02: "FC",
        0x03: "LC",
        0x04: "MT-RJ",
        0x05: "MU",
        0x06: "SG",
        0x07: "Optical Pigtail",
        0x08: "MPO 1x12",
        0x09: "MPO 2x12",
        0x0A: "MPO 1x16",
        0x20: "Copper pigtail",
        # Add more as per SFF-8024 v4.12 Table 3-3 "Connector Type Codes"
    }
    return connectors.get(byte_value, f"Unknown (0x{byte_value:02X})")

def decode_encoding(byte_value):
    """Decodes the Encoding byte (byte 0x0B) based on SFF-8024."""
    encodings = {
        0x00: "Unspecified",
        0x01: "8B10B",
        0x02: "4B5B",
        0x03: "NRZ",
        0x04: "SONET Scrambled",
        0x05: "64B66B",
        0x06: "Manchester",
        0x07: "PAM4",
        # Add more as per SFF-8024 v4.12 Table 3-7 "Encoding Codes"
    }
    return encodings.get(byte_value, f"Unknown (0x{byte_value:02X})")

# --- Base Memory Space Class ---

class MemorySpace:
    """
    Base class for a memory space. Subclasses define specific layouts.
    """
    def __init__(self, data: bytes):
        """
        Initializes the memory space with raw EEPROM data.
        :param data: A bytes object representing the memory space.
        """
        self._data = data
        self._fields = {} # To store decoded fields

    def get_byte(self, address: int) -> int:
        """Retrieves a single byte from the memory space."""
        if 0 <= address < len(self._data):
            return self._data[address]
        raise IndexError(f"Address 0x{address:02X} out of bounds.")

    def get_bytes(self, start_address: int, length: int) -> bytes:
        """Retrieves a sequence of bytes from the memory space."""
        end_address = start_address + length
        if 0 <= start_address < end_address <= len(self._data):
            return self._data[start_address:end_address]
        raise IndexError(f"Address range 0x{start_address:02X}-0x{end_address-1:02X} out of bounds.")

    def get_string(self, start_address: int, length: int) -> str:
        """Retrieves a string from the memory space, stripping nulls."""
        return self.get_bytes(start_address, length).decode('ascii').strip('\0')

    def _decode_field(self, name, start_addr, length, decoder=None):
        """Helper to decode and store a field."""
        raw_data = self.get_bytes(start_addr, length)
        if decoder:
            decoded_value = decoder(raw_data if length > 1 else raw_data[0])
        else:
            decoded_value = raw_data
        self._fields[name] = decoded_value
        return decoded_value

    def __repr__(self):
        return f"{self.__class__.__name__}(data_len={len(self._data)})"

    def to_dict(self):
        """Returns a dictionary representation of the decoded fields."""
        return self._fields

# --- SFF-8024 Common Base Page (Page 00h) ---

class SFF8024_BasePage00h(MemorySpace):
    """
    Represents the common base page (Page 00h) as defined by SFF-8024.
    This page contains fundamental identification and capability information.
    """
    def __init__(self, data: bytes):
        if len(data) < 128: # SFF-8024 Page 00h is typically 128 bytes
            raise ValueError("SFF-8024 Base Page 00h data must be at least 128 bytes.")
        super().__init__(data[:128]) # Ensure we only use the first 128 bytes

        self._decode_fields()

    def _decode_fields(self):
        self.identifier = self._decode_field("Identifier", IDENTIFIER_ADDR, 1, decode_identifier)
        self.ext_identifier = self._decode_field("Extended Identifier", EXT_IDENTIFIER_ADDR, 1)
        self.connector_type = self._decode_field("Connector Type", CONNECTOR_ADDR, 1, decode_connector_type)
        self.transceiver_technology = self._decode_field("Transceiver Technology", TRANSCEIVER_TECHNOLOGY_ADDR, 8) # SFF-8024 Byte 3-10
        self.encoding = self._decode_field("Encoding", ENCODING_ADDR, 1, decode_encoding)
        self.nominal_bit_rate_mbps = self._decode_field("Nominal Bit Rate (MBd)", NOMINAL_BIT_RATE_ADDR, 1) # SFF-8024 Byte 13 (x 100 MBd for SFP)
        self.length_smf_km = self._decode_field("Length SMF (km)", LENGTH_SMF_KM_ADDR, 1)
        self.length_smf_100m = self._decode_field("Length SMF (100m)", LENGTH_SMF_KM_ADDR + 1, 1) # SFF-8024 Byte 15
        self.length_om3_m = self._decode_field("Length OM3 (m)", LENGTH_OM3_ADDR, 1)
        self.length_om2_m = self._decode_field("Length OM2 (m)", LENGTH_OM3_ADDR + 1, 1)
        self.length_om1_m = self._decode_field("Length OM1 (m)", LENGTH_OM3_ADDR + 2, 1)
        self.length_passive_copper_m = self._decode_field("Length Passive Copper (m)", LENGTH_OM3_ADDR + 3, 1)
        self.vendor_name = self._decode_field("Vendor Name", VENDOR_NAME_START_ADDR, 16, lambda b: b.decode('ascii').strip())
        self.vendor_oui = self._decode_field("Vendor OUI", VENDOR_OUI_START_ADDR, 3)
        self.vendor_pn = self._decode_field("Vendor Part Number", VENDOR_PN_START_ADDR, 16, lambda b: b.decode('ascii').strip())
        self.vendor_rev = self._decode_field("Vendor Revision", VENDOR_REV_START_ADDR, 4, lambda b: b.decode('ascii').strip())
        self.wavelength_nm = self._decode_field("Wavelength (nm)", WAVELENGTH_ADDR, 2, lambda b: int.from_bytes(b, 'big'))
        self.options = self._decode_field("Options", OPTIONS_ADDR, 2)
        self.cc_base = self._decode_field("Check Code Base", CC_BASE_ADDR, 1)


# --- SFF-8472 Specific (SFP/SFP+) ---
# SFF-8472 builds upon SFF-8024 and defines additional fields for DDM, alarms, etc.
# These are typically in the lower memory space (A0h) and higher memory space (A2h).

class SFF8472_DOMMemorySpace(MemorySpace):
    """
    Represents the Digital Diagnostic Monitoring (DDM) memory space for SFF-8472.
    This is typically accessed at A2h for SFP/SFP+ modules.
    """
    def __init__(self, data: bytes):
        if len(data) < 128:
            raise ValueError("SFF-8472 DOM memory space data must be at least 128 bytes.")
        super().__init__(data[:128])

        self._decode_fields()

    def _decode_fields(self):
        # DDM Thresholds (bytes 0-39)
        self.temp_high_alarm = self._decode_field("Temp High Alarm", 0x00, 2, lambda b: int.from_bytes(b, 'big') / 256.0)
        self.temp_low_alarm = self._decode_field("Temp Low Alarm", 0x02, 2, lambda b: int.from_bytes(b, 'big') / 256.0)
        self.temp_high_warning = self._decode_field("Temp High Warning", 0x04, 2, lambda b: int.from_bytes(b, 'big') / 256.0)
        self.temp_low_warning = self._decode_field("Temp Low Warning", 0x06, 2, lambda b: int.from_bytes(b, 'big') / 256.0)

        self.vcc_high_alarm = self._decode_field("Vcc High Alarm", 0x08, 2, lambda b: int.from_bytes(b, 'big') / 10000.0) # V
        self.vcc_low_alarm = self._decode_field("Vcc Low Alarm", 0x0A, 2, lambda b: int.from_bytes(b, 'big') / 10000.0)
        self.vcc_high_warning = self._decode_field("Vcc High Warning", 0x0C, 2, lambda b: int.from_bytes(b, 'big') / 10000.0)
        self.vcc_low_warning = self._decode_field("Vcc Low Warning", 0x0E, 2, lambda b: int.from_bytes(b, 'big') / 10000.0)

        self.bias_high_alarm = self._decode_field("Bias High Alarm (mA)", 0x10, 2, lambda b: int.from_bytes(b, 'big') / 500.0)
        self.bias_low_alarm = self._decode_field("Bias Low Alarm (mA)", 0x12, 2, lambda b: int.from_bytes(b, 'big') / 500.0)
        self.bias_high_warning = self._decode_field("Bias High Warning (mA)", 0x14, 2, lambda b: int.from_bytes(b, 'big') / 500.0)
        self.bias_low_warning = self._decode_field("Bias Low Warning (mA)", 0x16, 2, lambda b: int.from_bytes(b, 'big') / 500.0)

        self.tx_power_high_alarm = self._decode_field("Tx Power High Alarm (mW)", 0x18, 2, lambda b: int.from_bytes(b, 'big') / 10000.0) # mW
        self.tx_power_low_alarm = self._decode_field("Tx Power Low Alarm (mW)", 0x1A, 2, lambda b: int.from_bytes(b, 'big') / 10000.0)
        self.tx_power_high_warning = self._decode_field("Tx Power High Warning (mW)", 0x1C, 2, lambda b: int.from_bytes(b, 'big') / 10000.0)
        self.tx_power_low_warning = self._decode_field("Tx Power Low Warning (mW)", 0x1E, 2, lambda b: int.from_bytes(b, 'big') / 10000.0)

        self.rx_power_high_alarm = self._decode_field("Rx Power High Alarm (mW)", 0x20, 2, lambda b: int.from_bytes(b, 'big') / 10000.0)
        self.rx_power_low_alarm = self._decode_field("Rx Power Low Alarm (mW)", 0x22, 2, lambda b: int.from_bytes(b, 'big') / 10000.0)
        self.rx_power_high_warning = self._decode_field("Rx Power High Warning (mW)", 0x24, 2, lambda b: int.from_bytes(b, 'big') / 10000.0)
        self.rx_power_low_warning = self._decode_field("Rx Power Low Warning (mW)", 0x26, 2, lambda b: int.from_bytes(b, 'big') / 10000.0)

        # DDM Values (bytes 96-105)
        self.temperature_c = self._decode_field("Temperature (C)", 0x60, 2, lambda b: int.from_bytes(b, 'big', signed=True) / 256.0)
        self.vcc_v = self._decode_field("Vcc (V)", 0x62, 2, lambda b: int.from_bytes(b, 'big') / 10000.0)
        self.tx_bias_ma = self._decode_field("Tx Bias (mA)", 0x64, 2, lambda b: int.from_bytes(b, 'big') / 500.0)
        self.tx_power_mw = self._decode_field("Tx Power (mW)", 0x66, 2, lambda b: int.from_bytes(b, 'big') / 10000.0)
        self.rx_power_mw = self._decode_field("Rx Power (mW)", 0x68, 2, lambda b: int.from_bytes(b, 'big') / 10000.0)

        self.cc_dmi = self._decode_field("Check Code DMI", CC_DMI_ADDR, 1)


# --- SFF-8636 Specific (QSFP/QSFP28) ---
# SFF-8636 defines a more complex memory map with multiple pages.
# Page 00h for SFF-8636 is different from SFF-8024 Page 00h.
# For simplicity, I'll create a dedicated Page 00h for SFF-8636 and
# common DDM pages (Page 01h, Page 02h, etc.).

class SFF8636_Page00h(MemorySpace):
    """
    Represents the common base page (Page 00h) for SFF-8636 compliant modules.
    This page contains fundamental identification and capability information.
    """
    def __init__(self, data: bytes):
        if len(data) < 256: # SFF-8636 Page 00h is 256 bytes (lower 128, upper 128)
            raise ValueError("SFF-8636 Page 00h data must be at least 256 bytes.")
        super().__init__(data[:256])

        self._decode_fields()

    def _decode_fields(self):
        # Lower Memory Map (Bytes 0-127) - SFF-8636 builds on 8472 here
        self.identifier = self._decode_field("Identifier", QSFP_IDENTIFIER_ADDR, 1, decode_identifier)
        self.rev_id = self._decode_field("Revision Identifier", QSFP_REVISION_ADDR, 1) # SFF-8636 Byte 1
        self.status_indicators = self._decode_field("Status Indicators", QSFP_STATUS_INDICATORS_ADDR, 2)
        self.connector_type = self._decode_field("Connector Type", CONNECTOR_ADDR, 1, decode_connector_type) # SFF-8636 Byte 3
        # Bytes 4-7: Transceiver Technology (SFF-8636 Specific)
        self.ethernet_10g_compliance = self._decode_field("10G Ethernet Compliance Codes", 0x03, 1)
        self.ethernet_compliance = self._decode_field("Ethernet Compliance Codes", 0x04, 1)
        self.sonet_compliance = self._decode_field("SONET Compliance Codes", 0x05, 1)
        self.sas_sata_compliance = self._decode_field("SAS/SATA Compliance Codes", 0x06, 1)
        self.gigabit_ethernet_compliance = self._decode_field("Gigabit Ethernet Compliance Codes", 0x07, 1)
        self.channel_fcc_compliance = self._decode_field("Channel FCO Codes", 0x08, 1)
        self.nominal_bit_rate_mbs = self._decode_field("Nominal Bit Rate (MBd)", 0x0D, 1)
        self.ext_spec_compliance = self._decode_field("Extended Specification Compliance", 0x0E, 1) # SFF-8636 Byte 14

        self.vendor_name = self._decode_field("Vendor Name", 0x14, 16, lambda b: b.decode('ascii').strip()) # Same as SFF-8024

        # Page 00h, Upper Memory Map (Bytes 128-255)
        self.vendor_oui = self._decode_field("Vendor OUI", QSFP_VENDOR_OUI_START_ADDR, 3) # SFF-8636 Byte 178-180
        self.vendor_pn = self._decode_field("Vendor Part Number", QSFP_PART_NUMBER_START_ADDR, 16, lambda b: b.decode('ascii').strip()) # SFF-8636 Byte 192-207
        self.vendor_rev = self._decode_field("Vendor Revision", QSFP_REVISION_NUMBER_START_ADDR, 2, lambda b: b.decode('ascii').strip()) # SFF-8636 Byte 208-209
        self.wavelength_nm = self._decode_field("Wavelength (nm)", 0xCA, 2, lambda b: int.from_bytes(b, 'big')) # SFF-8636 Byte 202-203

        self.ddm_capability = self._decode_field("DDM Capability", QSFP_DIAG_CAPABILITY_ADDR, 1)
        self.cc_base = self._decode_field("Check Code Base", 0x7F, 1) # SFF-8636 Lower Memory Check Code

        # ... (add more fields for Page 00h upper memory as needed from SFF-8636)


class SFF8636_Page01h_CD(MemorySpace):
    """
    Represents Page 01h (Application Select Table) and Page 02h (Diagnostic Monitoring)
    for SFF-8636 compliant modules.
    """
    def __init__(self, data: bytes):
        if len(data) < 256: # Page 01h and 02h are each 128 bytes, 256 total if concatenated
            raise ValueError("SFF-8636 Page 01h/02h data must be at least 256 bytes.")
        super().__init__(data) # This class can handle combined data if needed

        self._decode_fields()

    def _decode_fields(self):
        # Page 01h - Application Select Table (Bytes 0-127)
        # SFF-8636 details this as a bitfield for supported applications.
        # This will be quite detailed, so for brevity I'll just put a placeholder:
        self.app_selection_byte_1 = self._decode_field("Application Selection Byte 1", 0x00, 1)
        # ... many more application bytes ...

        # Page 02h - Diagnostic Monitoring (Bytes 128-255 relative to start of combined data)
        # These are analogous to SFF-8472 DOM, but for 4 channels.
        # Temperatures
        self.temp_c = self._decode_field("Temperature (C)", 0x80, 2, lambda b: int.from_bytes(b, 'big', signed=True) / 256.0)
        self.vcc_v = self._decode_field("Vcc (V)", 0x82, 2, lambda b: int.from_bytes(b, 'big') / 10000.0)

        # Channel 1-4 DDM values
        self.ch1_tx_bias_ma = self._decode_field("Ch1 Tx Bias (mA)", 0x84, 2, lambda b: int.from_bytes(b, 'big') * 2 / 1000.0) # SFF-8636 specific scaling
        self.ch2_tx_bias_ma = self._decode_field("Ch2 Tx Bias (mA)", 0x86, 2, lambda b: int.from_bytes(b, 'big') * 2 / 1000.0)
        self.ch3_tx_bias_ma = self._decode_field("Ch3 Tx Bias (mA)", 0x88, 2, lambda b: int.from_bytes(b, 'big') * 2 / 1000.0)
        self.ch4_tx_bias_ma = self._decode_field("Ch4 Tx Bias (mA)", 0x8A, 2, lambda b: int.from_bytes(b, 'big') * 2 / 1000.0)

        self.ch1_tx_power_mw = self._decode_field("Ch1 Tx Power (mW)", 0x8C, 2, lambda b: int.from_bytes(b, 'big') / 10000.0)
        self.ch2_tx_power_mw = self._decode_field("Ch2 Tx Power (mW)", 0x8E, 2, lambda b: int.from_bytes(b, 'big') / 10000.0)
        self.ch3_tx_power_mw = self._decode_field("Ch3 Tx Power (mW)", 0x90, 2, lambda b: int.from_bytes(b, 'big') / 10000.0)
        self.ch4_tx_power_mw = self._decode_field("Ch4 Tx Power (mW)", 0x92, 2, lambda b: int.from_bytes(b, 'big') / 10000.0)

        self.ch1_rx_power_mw = self._decode_field("Ch1 Rx Power (mW)", 0x94, 2, lambda b: int.from_bytes(b, 'big') / 10000.0)
        self.ch2_rx_power_mw = self._decode_field("Ch2 Rx Power (mW)", 0x96, 2, lambda b: int.from_bytes(b, 'big') / 10000.0)
        self.ch3_rx_power_mw = self._decode_field("Ch3 Rx Power (mW)", 0x98, 2, lambda b: int.from_bytes(b, 'big') / 10000.0)
        self.ch4_rx_power_mw = self._decode_field("Ch4 Rx Power (mW)", 0x9A, 2, lambda b: int.from_bytes(b, 'big') / 10000.0)

        self.cc_dmi = self._decode_field("Check Code DMI", 0xEF, 1) # Check Code for Page 02h


# --- CMIS (Common Management Interface Specification) ---
# CMIS defines a much more extensive memory map and is used by OSFP, QSFP-DD, etc.
# Due to its complexity and variable pages, providing a full definition here would
# be very extensive. I'll provide a minimal placeholder for CMIS's Page 00h.

class CMIS_Page00h(MemorySpace):
    """
    Represents CMIS Page 00h (Lower Memory Map).
    CMIS memory map is significantly more complex and organized than SFF-8472/8636.
    This is a basic placeholder and would require extensive definition to be complete.
    """
    def __init__(self, data: bytes):
        if len(data) < 256: # CMIS lower memory is 256 bytes
            raise ValueError("CMIS Page 00h data must be at least 256 bytes.")
        super().__init__(data[:256])

        self._decode_fields()

    def _decode_fields(self):
        self.identifier = self._decode_field("Identifier", 0x00, 1, decode_identifier) # Should be 0x0C for CMIS
        self.revision = self._decode_field("Revision", 0x01, 1)
        self.status = self._decode_field("Status", 0x02, 2)
        self.module_temperature = self._decode_field("Module Temperature (C)", 0x16, 2, lambda b: int.from_bytes(b, 'big', signed=True) / 256.0)
        self.module_vcc = self._decode_field("Module Vcc (V)", 0x18, 2, lambda b: int.from_bytes(b, 'big') / 10000.0)

        # Basic identification for CMIS
        self.vendor_name = self._decode_field("Vendor Name", 0x21, 16, lambda b: b.decode('ascii').strip())
        self.vendor_oui = self._decode_field("Vendor OUI", 0x32, 3)
        self.vendor_pn = self._decode_field("Vendor Part Number", 0x35, 16, lambda b: b.decode('ascii').strip())
        self.vendor_rev = self._decode_field("Vendor Revision", 0x45, 2, lambda b: b.decode('ascii').strip())

        self.cc_base = self._decode_field("Check Code Base", 0x7F, 1)


# --- Module-Specific Memory Map Wrappers ---

class SFP_MemoryMap:
    """
    Represents the complete memory map for an SFP/SFP+ module,
    combining SFF-8024 base page and SFF-8472 DDM.
    """
    def __init__(self, lower_memory_a0h: bytes, diagnostic_memory_a2h: bytes = None):
        self.base_id_fields = SFF8024_BasePage00h(lower_memory_a0h)
        if diagnostic_memory_a2h:
            self.dom_fields = SFF8472_DOMMemorySpace(diagnostic_memory_a2h)
        else:
            self.dom_fields = None

    def to_dict(self):
        data = {"base_id_fields": self.base_id_fields.to_dict()}
        if self.dom_fields:
            data["dom_fields"] = self.dom_fields.to_dict()
        return data


class QSFP_MemoryMap:
    """
    Represents the complete memory map for a QSFP/QSFP28 module,
    combining SFF-8636 Page 00h and Page 01h/02h (DDM).
    """
    def __init__(self, page00h_data: bytes, page01h_02h_data: bytes = None):
        self.page00h = SFF8636_Page00h(page00h_data)
        if page01h_02h_data:
            self.page01h_02h = SFF8636_Page01h_CD(page01h_02h_data)
        else:
            self.page01h_02h = None

    def to_dict(self):
        data = {"page00h": self.page00h.to_dict()}
        if self.page01h_02h:
            data["page01h_02h"] = self.page01h_02h.to_dict()
        return data

class OSFP_MemoryMap:
    """
    Represents the memory map for an OSFP module, primarily based on CMIS.
    This is a conceptual placeholder as CMIS is highly dynamic and multi-page.
    """
    def __init__(self, lower_memory_page00h: bytes):
        self.page00h = CMIS_Page00h(lower_memory_page00h)
        # In a real implementation, you would dynamically load other CMIS pages
        # (e.g., Page 01h for Module State, Page 10h-1Fh for Lane State)
        # based on the Revision and other indicators.

    def to_dict(self):
        return {"page00h": self.page00h.to_dict()}


# --- Example Usage (How to use this file) ---

if __name__ == "__main__":
    # Example raw EEPROM data (dummy data for demonstration)
    # In a real scenario, this data would be read from the transceiver's EEPROM.

    # --- SFP/SFP+ Example (using SFF-8024 and SFF-8472) ---
    print("--- SFP/SFP+ Example (SFF-8024 & SFF-8472) ---")
    sfp_lower_memory_a0h_data = bytearray([0] * 128)
    sfp_lower_memory_a0h_data[IDENTIFIER_ADDR] = 0x03  # SFP/SFP+
    sfp_lower_memory_a0h_data[CONNECTOR_ADDR] = 0x07   # Optical Pigtail
    sfp_lower_memory_a0h_data[NOMINAL_BIT_RATE_ADDR] = 0x0A # 1000 MBd (10 x 100)
    sfp_lower_memory_a0h_data[VENDOR_NAME_START_ADDR:VENDOR_NAME_START_ADDR+16] = b"ACME Corp       "
    sfp_lower_memory_a0h_data[VENDOR_PN_START_ADDR:VENDOR_PN_START_ADDR+16] = b"SFP-1G-LX       "
    sfp_lower_memory_a0h_data[WAVELENGTH_ADDR:WAVELENGTH_ADDR+2] = (1310).to_bytes(2, 'big') # 1310nm
    sfp_lower_memory_a0h_data[CC_BASE_ADDR] = sum(sfp_lower_memory_a0h_data[0:63]) % 256 # Simple checksum

    sfp_dom_memory_a2h_data = bytearray([0] * 128)
    sfp_dom_memory_a2h_data[0x60:0x62] = (25.5 * 256).astype(int).to_bytes(2, 'big', signed=True) # Temp: 25.5 C
    sfp_dom_memory_a2h_data[0x62:0x64] = (3.3 * 10000).astype(int).to_bytes(2, 'big') # Vcc: 3.3 V
    sfp_dom_memory_a2h_data[0x64:0x66] = (8.5 * 500).astype(int).to_bytes(2, 'big') # Tx Bias: 8.5 mA
    sfp_dom_memory_a2h_data[0x66:0x68] = (0.5 * 10000).astype(int).to_bytes(2, 'big') # Tx Power: 0.5 mW
    sfp_dom_memory_a2h_data[0x68:0x6A] = (0.3 * 10000).astype(int).to_bytes(2, 'big') # Rx Power: 0.3 mW
    sfp_dom_memory_a2h_data[CC_DMI_ADDR] = sum(sfp_dom_memory_a2h_data[64:95]) % 256 # Simple checksum for DDM area

    sfp_module = SFP_MemoryMap(bytes(sfp_lower_memory_a0h_data), bytes(sfp_dom_memory_a2h_data))
    print(sfp_module.base_id_fields.to_dict())
    print(sfp_module.dom_fields.to_dict())


    # --- QSFP/QSFP28 Example (using SFF-8636) ---
    print("\n--- QSFP/QSFP28 Example (SFF-8636) ---")
    qsfp_page00h_data = bytearray([0] * 256)
    qsfp_page00h_data[QSFP_IDENTIFIER_ADDR] = 0x0C # CMIS (often seen with QSFP-DD)
    qsfp_page00h_data[QSFP_REVISION_ADDR] = 0x01 # Rev 1.0
    qsfp_page00h_data[QSFP_VENDOR_NAME_START_ADDR:QSFP_VENDOR_NAME_START_ADDR+16] = b"XYZ Optics      "
    qsfp_page00h_data[QSFP_PART_NUMBER_START_ADDR:QSFP_PART_NUMBER_START_ADDR+16] = b"QSFP28-100G-SR4 "
    qsfp_page00h_data[0x7F] = sum(qsfp_page00h_data[0:127]) % 256 # Lower Memory Checksum

    qsfp_page01h_02h_data = bytearray([0] * 256) # Combined Page 01h (0-127) and Page 02h (128-255)
    qsfp_page01h_02h_data[0x80:0x82] = (35.0 * 256).astype(int).to_bytes(2, 'big', signed=True) # Temp: 35.0 C
    qsfp_page01h_02h_data[0x84:0x86] = (5.0 * 500).astype(int).to_bytes(2, 'big') # Ch1 Tx Bias
    qsfp_page01h_02h_data[0x8C:0x8E] = (1.2 * 10000).astype(int).to_bytes(2, 'big') # Ch1 Tx Power
    qsfp_page01h_02h_data[0x94:0x96] = (0.8 * 10000).astype(int).to_bytes(2, 'big') # Ch1 Rx Power
    qsfp_page01h_02h_data[0xEF] = sum(qsfp_page01h_02h_data[128:239]) % 256 # Page 02h Checksum

    qsfp_module = QSFP_MemoryMap(bytes(qsfp_page00h_data), bytes(qsfp_page01h_02h_data))
    print(qsfp_module.page00h.to_dict())
    print(qsfp_module.page01h_02h.to_dict())

    # --- OSFP Example (using CMIS - very basic) ---
    print("\n--- OSFP Example (CMIS) ---")
    osfp_page00h_data = bytearray([0] * 256)
    osfp_page00h_data[0x00] = 0x08 # OSFP Identifier (from SFF-8024)
    osfp_page00h_data[0x01] = 0x50 # CMIS Revision 5.0
    osfp_page00h_data[0x16:0x18] = (40.0 * 256).astype(int).to_bytes(2, 'big', signed=True) # Module Temp: 40.0 C
    osfp_page00h_data[0x21:0x21+16] = b"Big Telecom Inc."
    osfp_page00h_data[0x7F] = sum(osfp_page00h_data[0:127]) % 256 # Checksum for CMIS Lower Memory

    osfp_module = OSFP_MemoryMap(bytes(osfp_page00h_data))
    print(osfp_module.page00h.to_dict())