"""
Tests for EmulatorClient — the transparent TCP hardware interface adapter.

Test Strategy
-------------
Each test spins up a real ``I2CBridgeServer`` backed by a real
``SFFEmulatedModule``, then exercises ``EmulatorClient`` through the same
public API that production control software would use.

This validates:
  - The full round-trip: client → TCP → server → emulated memory → TCP → client
  - That ``EmulatorClient`` is a true drop-in for ``EmulatedHardwareInterface``
  - All register read/write, multi-byte, and GPIO paths
  - Graceful error handling (bad addresses, disconnected server)
  - Context-manager and manual connect/disconnect lifecycles
  - GPIOSignal enum compatibility with the production HardwareInterface API
"""
import socket
import time
import pytest

from src.hardware.bridge import I2CBridgeServer
from src.hardware.emulator_client import EmulatorClient, EmulatorClientError
from src.hardware.hal import GPIOSignal

from tests.emulation.hardware import EmulatedHardwareInterface
from tests.emulation.sff import SFFEmulatedModule
from tests.emulation.configs import ModuleConfig, MediaType, FormFactor, ModuleType


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

def _free_port() -> int:
    """Allocate a free local port for this test run."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _make_sff_config() -> ModuleConfig:
    return ModuleConfig(
        identifier=0x0D,
        vendor_name="Test Vendor",
        part_number="TEST-PART-001",
        serial_number="TEST001",
        revision="A1",
        media_type=MediaType.MMF,
        form_factor=FormFactor.SFP,
        module_type=ModuleType.SFP_PLUS,
        num_channels=1,
        max_power_draw=1.0,
        supported_rates=[10.0],
        nominal_bit_rate=10.0,
        max_case_temp=70.0,
    )


@pytest.fixture
def sff_bridge():
    """
    Spin up a real SFFEmulatedModule attached to an I2CBridgeServer.
    Yields (client_port, server, hw) so individual tests can connect.
    Tears down after each test.
    """
    config = _make_sff_config()
    module = SFFEmulatedModule(config)

    hw = EmulatedHardwareInterface()
    hw.attach_module(module)

    port = _free_port()
    server = I2CBridgeServer(hardware=hw, host="127.0.0.1", port=port)
    server.start()
    time.sleep(0.05)  # Allow socket to bind

    yield port, server, hw, module

    server.stop()


# ---------------------------------------------------------------------------
# Connection lifecycle tests
# ---------------------------------------------------------------------------

def test_context_manager_connect_disconnect(sff_bridge):
    """Client connects and disconnects cleanly as a context manager."""
    port, server, hw, module = sff_bridge
    with EmulatorClient(port=port) as client:
        assert client.is_connected()
    assert not client.is_connected()


def test_manual_connect_disconnect(sff_bridge):
    """Client supports explicit connect() / disconnect() lifecycle."""
    port, server, hw, module = sff_bridge
    client = EmulatorClient(port=port)
    assert not client.is_connected()

    client.connect()
    assert client.is_connected()

    client.disconnect()
    assert not client.is_connected()


def test_cannot_send_without_connect(sff_bridge):
    """Calling read_register before connect raises EmulatorClientError."""
    port, server, hw, module = sff_bridge
    client = EmulatorClient(port=port)
    with pytest.raises(EmulatorClientError, match="Not connected"):
        client.read_register(0xA0, 0x00)


# ---------------------------------------------------------------------------
# Register read / write tests
# ---------------------------------------------------------------------------

def test_read_single_register(sff_bridge):
    """Read the module identifier byte from the A0h page."""
    port, server, hw, module = sff_bridge
    module.memory_map.select_page(0xA0)

    with EmulatorClient(port=port) as client:
        identifier = client.read_register(0xA0, 0x00)

    assert identifier == 0x0D  # SFP+ identifier written during init


def test_write_and_read_back_register(sff_bridge):
    """Write a byte and confirm the same value is read back."""
    port, server, hw, module = sff_bridge
    module.memory_map.select_page(0xA0)

    with EmulatorClient(port=port) as client:
        client.write_register(0xA0, 0x01, 0xBE)
        value = client.read_register(0xA0, 0x01)

    assert value == 0xBE


def test_read_multiple_registers(sff_bridge):
    """Read a multi-byte vendor name string from the A0h page."""
    port, server, hw, module = sff_bridge
    module.memory_map.select_page(0xA0)

    with EmulatorClient(port=port) as client:
        raw = client.read_registers(0xA0, 0x14, 11)  # "Test Vendor"

    text = "".join(chr(b) for b in raw if 32 <= b <= 126)
    assert text == "Test Vendor"


def test_write_multiple_registers(sff_bridge):
    """Write a sequence of bytes and confirm each value is stored."""
    port, server, hw, module = sff_bridge
    module.memory_map.select_page(0xA0)
    test_payload = [0xAA, 0xBB, 0xCC, 0xDD]

    with EmulatorClient(port=port) as client:
        client.write_registers(0xA0, 0x02, bytes(test_payload))
        result = client.read_registers(0xA0, 0x02, 4)

    assert result == test_payload


# ---------------------------------------------------------------------------
# GPIO tests
# ---------------------------------------------------------------------------

def test_get_module_present(sff_bridge):
    """Module presence is True after a module is attached to the bridge."""
    port, server, hw, module = sff_bridge
    with EmulatorClient(port=port) as client:
        assert client.get_module_present() is True


def test_module_present_alias(sff_bridge):
    """module_present() is a valid alias matching the HardwareInterface API."""
    port, server, hw, module = sff_bridge
    with EmulatorClient(port=port) as client:
        assert client.module_present() is True


def test_low_power_mode_set_and_verify(sff_bridge):
    """set_low_power_mode toggles the LPMode GPIO pin on the server."""
    port, server, hw, module = sff_bridge
    with EmulatorClient(port=port) as client:
        client.set_low_power_mode(True)
        assert hw.gpio.get_pin("lpmode") is True

        client.set_low_power_mode(False)
        assert hw.gpio.get_pin("lpmode") is False


def test_reset_module(sff_bridge):
    """reset_module() cycles reset high then low; interrupt remains clear."""
    port, server, hw, module = sff_bridge
    with EmulatorClient(port=port) as client:
        client.reset_module()
        # After reset, interrupt should remain deasserted
        assert client.get_module_interrupt() is False
        assert client.get_interrupt_state() is False  # alias


def test_gpio_signal_enum_compatibility(sff_bridge):
    """GPIOSignal enum values are accepted by get_gpio_state / set_gpio_state."""
    port, server, hw, module = sff_bridge
    with EmulatorClient(port=port) as client:
        # Use the enum directly — matches production HardwareInterface callers
        client.set_gpio_state(GPIOSignal.LPMODE, True)
        state = client.get_gpio_state(GPIOSignal.LPMODE)
        assert state is True


# ---------------------------------------------------------------------------
# Real monitoring loop simulation
# ---------------------------------------------------------------------------

def test_temperature_round_trip(sff_bridge):
    """
    Simulate a monitoring agent reading temperature from the A2h diagnostic page.

    This mirrors what a real status-monitoring service would do:
    set a temperature on the emulator side, then read and decode the raw
    register bytes through the TCP client — just as a C driver would.
    """
    port, server, hw, module = sff_bridge

    # Set temperature on the emulator (as the emulator simulator would)
    module.set_temperature(55.0)

    with EmulatorClient(port=port) as client:
        # Switch the module's active page to A2h (diagnostic page)
        # In a real driver this would be done via a page-select write
        module.memory_map.select_page(0xA2)

        # Read two-byte temperature register (bytes 96-97 per SFF-8472 §10)
        raw = client.read_registers(0xA2, 96, 2)

    raw_word = (raw[0] << 8) | raw[1]
    temperature = raw_word / 256.0

    # Should decode to approximately 55.0 °C (within DDM rounding tolerance)
    assert abs(temperature - 55.0) < 0.1


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

def test_connect_to_nonexistent_server():
    """Connecting to a port with no server raises EmulatorClientError."""
    port = _free_port()  # Nothing is listening here
    client = EmulatorClient(host="127.0.0.1", port=port, auto_reconnect=False)
    with pytest.raises(EmulatorClientError, match="Cannot connect"):
        client.connect()
