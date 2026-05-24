"""
TCP Emulator Client — Transparent Hardware Interface Adapter.

Purpose
-------
This module provides a client-side interface that is a **drop-in replacement**
for ``EmulatedHardwareInterface`` (tests/emulation/hardware.py) and mirrors the
higher-level methods on ``HardwareInterface`` (src/hardware/hal.py).

Any control or monitoring software that calls::

    hw.read_register(bus_addr, reg_addr)
    hw.write_register(bus_addr, reg_addr, value)
    hw.get_module_present()
    hw.reset_module()
    ...

can be pointed at a remote (or local) ``I2CBridgeServer`` instance by simply
substituting ``EmulatorClient`` for the in-process hardware object.  The TCP
transport is entirely transparent to the calling code.

Genesis
-------
Created May 2026 as part of the CMIS Emulator Framework TCP Bridge integration.
Motivated by the need for native-language drivers (C, Go, Rust) and multi-process
Python applications to exercise the same emulator used in pytest without sharing
a process address space.

Usage — Python drop-in
-----------------------
>>> from src.hardware.emulator_client import EmulatorClient
>>>
>>> # Exactly the same calls as EmulatedHardwareInterface
>>> with EmulatorClient(host="127.0.0.1", port=8024) as hw:
...     identifier = hw.read_register(0xA0, 0x00)
...     hw.write_register(0xA2, 0x60, 0x2D)
...     present = hw.get_module_present()
...     hw.reset_module()

Usage — with GPIOSignal enum (compatible with HardwareInterface callers)
------------------------------------------------------------------------
>>> from src.hardware.hal import GPIOSignal
>>> with EmulatorClient() as hw:
...     hw.set_gpio_state(GPIOSignal.LPMODE, True)
...     state = hw.get_gpio_state(GPIOSignal.INTERRUPT)
"""

import socket
import time
from typing import List, Optional, Union

# Re-export GPIOSignal so callers don't need to import from two places
from .hal import GPIOSignal


class EmulatorClientError(Exception):
    """Raised when the client cannot communicate with the bridge server."""
    pass


class EmulatorClient:
    """
    Transparent TCP client that mirrors the full ``EmulatedHardwareInterface``
    and ``HardwareInterface`` APIs.

    All register and GPIO operations are translated to the bridge text protocol
    and sent over a persistent TCP connection to an ``I2CBridgeServer`` instance.

    Connection Management
    ---------------------
    The client maintains a single persistent connection and automatically
    attempts to reconnect once if the connection is dropped mid-session
    (common during long-running monitoring loops that outlive server restarts).

    Parameters
    ----------
    host : str
        Hostname or IP address of the bridge server. Defaults to loopback.
    port : int
        TCP port the bridge server is listening on. Defaults to 8024 (SFF-8024).
    timeout : float
        Socket timeout in seconds for individual operations. Defaults to 5.0 s.
    auto_reconnect : bool
        If True, transparently reconnect once on a dropped connection before
        raising ``EmulatorClientError``. Defaults to True.

    Examples
    --------
    As a context manager (recommended — guarantees cleanup)::

        with EmulatorClient() as hw:
            val = hw.read_register(0xA0, 0x00)

    As a persistent object::

        hw = EmulatorClient(host="192.168.1.10", port=8024)
        hw.connect()
        try:
            val = hw.read_register(0xA0, 0x00)
        finally:
            hw.disconnect()
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8024,
        timeout: float = 5.0,
        auto_reconnect: bool = True,
    ):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.auto_reconnect = auto_reconnect

        self._sock: Optional[socket.socket] = None
        self._recv_buffer: str = ""

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def connect(self) -> None:
        """Open the TCP connection to the bridge server."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.host, self.port))
            self._sock = sock
            self._recv_buffer = ""
        except OSError as exc:
            raise EmulatorClientError(
                f"Cannot connect to emulator bridge at {self.host}:{self.port} — {exc}"
            ) from exc

    def disconnect(self) -> None:
        """Close the TCP connection gracefully."""
        if self._sock:
            try:
                self._sock.sendall(b"BYE\n")
                self._sock.close()
            except Exception:
                pass
            finally:
                self._sock = None
                self._recv_buffer = ""

    def is_connected(self) -> bool:
        """Return True if the client currently has an open connection."""
        return self._sock is not None

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    def __enter__(self) -> "EmulatorClient":
        self.connect()
        return self

    def __exit__(self, *_) -> None:
        self.disconnect()

    # ------------------------------------------------------------------
    # Register access  (matches EmulatedHardwareInterface exactly)
    # ------------------------------------------------------------------

    def read_register(self, bus_address: int, reg_address: int) -> int:
        """
        Read a single byte register from the emulated module.

        Parameters
        ----------
        bus_address : int
            I2C device address (e.g. 0xA0 for SFF ID page, 0x50 for CMIS).
        reg_address : int
            Register offset within the selected memory page.

        Returns
        -------
        int
            Byte value (0–255) read from the register.
        """
        results = self.read_registers(bus_address, reg_address, count=1)
        return results[0]

    def write_register(
        self, bus_address: int, reg_address: int, value: int
    ) -> None:
        """
        Write a single byte to a register on the emulated module.

        Parameters
        ----------
        bus_address : int
            I2C device address.
        reg_address : int
            Register offset.
        value : int
            Byte value (0–255) to write.
        """
        self.write_registers(bus_address, reg_address, bytes([value]))

    def read_registers(
        self, bus_address: int, reg_address: int, count: int
    ) -> List[int]:
        """
        Read *count* consecutive bytes starting at *reg_address*.

        Returns
        -------
        List[int]
            List of *count* byte values.
        """
        cmd = f"READ 0x{bus_address:02X} 0x{reg_address:02X} {count}"
        response = self._send(cmd)
        try:
            return [int(tok, 16) for tok in response.split()]
        except ValueError as exc:
            raise EmulatorClientError(
                f"Unexpected READ response from server: {response!r}"
            ) from exc

    def write_registers(
        self, bus_address: int, reg_address: int, values: Union[bytes, List[int]]
    ) -> None:
        """
        Write multiple consecutive bytes starting at *reg_address*.

        Parameters
        ----------
        values : bytes or List[int]
            Sequence of byte values to write.
        """
        if isinstance(values, list):
            values = bytes(values)
        hex_vals = " ".join(f"{b:02X}" for b in values)
        cmd = f"WRITE 0x{bus_address:02X} 0x{reg_address:02X} {hex_vals}"
        response = self._send(cmd)
        if response != "OK":
            raise EmulatorClientError(f"WRITE failed — server responded: {response!r}")

    # ------------------------------------------------------------------
    # GPIO access  (matches both HardwareInterface and EmulatedHardwareInterface)
    # ------------------------------------------------------------------

    def get_gpio_state(self, signal: Union[GPIOSignal, str]) -> bool:
        """
        Read the current state of a GPIO signal.

        Accepts either a ``GPIOSignal`` enum value or a plain string name,
        making this compatible with callers written against the production
        ``HardwareInterface``.
        """
        signal_name = signal.value if isinstance(signal, GPIOSignal) else signal
        response = self._send(f"GPIO_GET {signal_name}")
        if response not in ("0", "1"):
            raise EmulatorClientError(
                f"Unexpected GPIO_GET response: {response!r}"
            )
        return response == "1"

    def set_gpio_state(
        self, signal: Union[GPIOSignal, str], state: bool
    ) -> None:
        """
        Set a GPIO signal to the given state.

        Accepts either a ``GPIOSignal`` enum value or a plain string name.
        """
        signal_name = signal.value if isinstance(signal, GPIOSignal) else signal
        response = self._send(f"GPIO_SET {signal_name} {'1' if state else '0'}")
        if response != "OK":
            raise EmulatorClientError(
                f"GPIO_SET failed — server responded: {response!r}"
            )

    # ------------------------------------------------------------------
    # High-level module helpers  (mirrors both hardware interface classes)
    # ------------------------------------------------------------------

    def get_module_present(self) -> bool:
        """Return True if a module is currently attached to the emulator."""
        return self.get_gpio_state("mod_present")

    def module_present(self) -> bool:
        """Alias for ``get_module_present`` — compatible with HardwareInterface."""
        return self.get_module_present()

    def reset_module(self) -> None:
        """
        Perform a hardware reset cycle — assert then deassert the reset signal.

        Equivalent to ``hw.gpio.set_pin('reset', True)`` followed by
        ``hw.gpio.set_pin('reset', False)`` on ``EmulatedHardwareInterface``.
        """
        self.set_gpio_state("reset", True)
        self.set_gpio_state("reset", False)

    def get_module_interrupt(self) -> bool:
        """Return True if the module interrupt line is currently asserted."""
        return self.get_gpio_state("interrupt")

    def get_interrupt_state(self) -> bool:
        """Alias for ``get_module_interrupt`` — compatible with HardwareInterface."""
        return self.get_module_interrupt()

    def set_low_power_mode(self, enable: bool) -> None:
        """Enable or disable the module low-power mode signal (LPMode pin)."""
        self.set_gpio_state("lpmode", enable)

    # ------------------------------------------------------------------
    # Internal protocol transport
    # ------------------------------------------------------------------

    def _send(self, command: str) -> str:
        """
        Send a single newline-terminated command and return the response line.

        Transparently reconnects once if the connection has been dropped
        (controlled by ``auto_reconnect``).
        """
        try:
            return self._transact(command)
        except (OSError, EmulatorClientError) as exc:
            if self.auto_reconnect and self._sock is not None:
                # Connection dropped — attempt a single reconnect
                try:
                    self._sock.close()
                except Exception:
                    pass
                self._sock = None
                self._recv_buffer = ""
                self.connect()
                return self._transact(command)
            raise EmulatorClientError(
                f"Lost connection to emulator bridge — {exc}"
            ) from exc

    def _transact(self, command: str) -> str:
        """
        Low-level send/receive of a single command/response pair.

        Raises
        ------
        EmulatorClientError
            If not connected or if the server returns an ERR response.
        """
        if self._sock is None:
            raise EmulatorClientError(
                "Not connected. Call connect() or use as a context manager."
            )

        self._sock.sendall((command + "\n").encode("utf-8"))

        # Read until we have a complete newline-terminated response
        while "\n" not in self._recv_buffer:
            chunk = self._sock.recv(4096)
            if not chunk:
                raise EmulatorClientError("Server closed the connection unexpectedly.")
            self._recv_buffer += chunk.decode("utf-8")

        line, self._recv_buffer = self._recv_buffer.split("\n", 1)
        line = line.strip()

        if line.startswith("ERR"):
            raise EmulatorClientError(f"Bridge server error: {line}")

        return line
