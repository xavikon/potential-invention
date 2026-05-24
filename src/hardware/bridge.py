"""
TCP Socket I2C Bridge Server Skill.
Exposes the emulated transceiver memory map and GPIO pins to external C/Rust/Go drivers or VMs over a TCP socket.
"""
import socket
import threading
import traceback
from typing import Any, Optional

class I2CBridgeServer:
    """
    A lightweight, multi-threaded TCP Socket Server that acts as a bridge.
    Translates TCP text commands into internal transceiver memory/GPIO transactions.
    
    Protocol:
    - READ <bus_addr_hex> <reg_addr_hex> <count>
      Example: READ 0xA0 0x14 4 -> Responds with: 54 65 73 74 (or ERR <msg>)
    - WRITE <bus_addr_hex> <reg_addr_hex> <val_hex_1> [val_hex_2 ...]
      Example: WRITE 0xA0 0x01 55 -> Responds with: OK (or ERR <msg>)
    - GPIO_GET <signal_name>
      Example: GPIO_GET interrupt -> Responds with: 0 or 1
    - GPIO_SET <signal_name> <0|1>
      Example: GPIO_SET lpmode 1 -> Responds with: OK
    - BYE
      Closes active connection.
    """

    def __init__(self, hardware: Any, host: str = "127.0.0.1", port: int = 8024):
        """
        Initialize the bridge server.
        
        Args:
            hardware: An instance of EmulatedHardwareInterface or HardwareInterface.
            host: Bind host interface.
            port: Port to listen on (SFF-8024 -> 8024 by default).
        """
        self.hardware = hardware
        self.host = host
        self.port = port
        self._server_socket: Optional[socket.socket] = None
        self._is_running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the socket bridge server in a background thread."""
        if self._is_running:
            return
            
        self._is_running = True
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind((self.host, self.port))
        self._server_socket.listen(5)
        
        self._thread = threading.Thread(target=self._run_loop, name="I2CBridgeServer", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the bridge server and clean up socket connections."""
        self._is_running = False
        if self._server_socket:
            try:
                # Trigger socket cleanup by self-connecting or shutting down
                self._server_socket.close()
            except Exception:
                pass
        if self._thread:
            self._thread.join(timeout=1.0)

    def _run_loop(self) -> None:
        """Background thread main connection acceptance loop."""
        while self._is_running:
            try:
                client_sock, client_addr = self._server_socket.accept()
                client_thread = threading.Thread(
                    target=self._handle_client, 
                    args=(client_sock,), 
                    daemon=True
                )
                client_thread.start()
            except Exception:
                # Socket closed or shutdown
                break

    def _handle_client(self, sock: socket.socket) -> None:
        """Handles commands from an active connection."""
        sock.settimeout(10.0)  # prevent hanging client connections
        buffer = ""
        
        with sock:
            while self._is_running:
                try:
                    data = sock.recv(1024)
                    if not data:
                        break
                        
                    buffer += data.decode("utf-8")
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if not line:
                            continue
                            
                        if line.upper() == "BYE":
                            sock.sendall(b"BYE\n")
                            return
                            
                        response = self._process_command(line)
                        sock.sendall((response + "\n").encode("utf-8"))
                except socket.timeout:
                    break
                except Exception as e:
                    try:
                        sock.sendall(f"ERR Internal socket error: {str(e)}\n".encode("utf-8"))
                    except Exception:
                        pass
                    break

    def _process_command(self, cmd_line: str) -> str:
        """Parses and executes a command string, returning a text response."""
        parts = cmd_line.split()
        if not parts:
            return "ERR Empty command"
            
        action = parts[0].upper()
        
        try:
            if action == "READ":
                if len(parts) != 4:
                    return "ERR Format: READ <bus_addr> <reg_addr> <count>"
                bus_addr = int(parts[1], 16)
                reg_addr = int(parts[2], 16)
                count = int(parts[3])
                
                # Check for reading multiple registers
                if hasattr(self.hardware, 'read_registers'):
                    vals = self.hardware.read_registers(bus_addr, reg_addr, count)
                elif hasattr(self.hardware, 'read_register'):
                    vals = [self.hardware.read_register(bus_addr, reg_addr + i) for i in range(count)]
                else:
                    return "ERR Hardware does not support register reading"
                    
                return " ".join(f"{val:02X}" for val in vals)
                
            elif action == "WRITE":
                if len(parts) < 4:
                    return "ERR Format: WRITE <bus_addr> <reg_addr> <hex_byte_1> [hex_byte_2 ...]"
                bus_addr = int(parts[1], 16)
                reg_addr = int(parts[2], 16)
                vals = [int(val, 16) for val in parts[3:]]
                
                if hasattr(self.hardware, 'write_registers'):
                    self.hardware.write_registers(bus_addr, reg_addr, bytes(vals))
                elif hasattr(self.hardware, 'write_register'):
                    for i, val in enumerate(vals):
                        self.hardware.write_register(bus_addr, reg_addr + i, val)
                else:
                    return "ERR Hardware does not support register writing"
                    
                return "OK"
                
            elif action == "GPIO_GET":
                if len(parts) != 2:
                    return "ERR Format: GPIO_GET <signal>"
                signal = parts[1].lower()
                
                # Dynamic check for GPIO capabilities
                if hasattr(self.hardware, 'get_gpio_state'):
                    state = self.hardware.get_gpio_state(signal)
                elif hasattr(self.hardware, 'gpio') and hasattr(self.hardware.gpio, 'get_pin'):
                    state = self.hardware.gpio.get_pin(signal)
                else:
                    return "ERR Hardware does not support GPIO reading"
                    
                return "1" if state else "0"
                
            elif action == "GPIO_SET":
                if len(parts) != 3:
                    return "ERR Format: GPIO_SET <signal> <0|1>"
                signal = parts[1].lower()
                state = parts[2] == "1"
                
                if hasattr(self.hardware, 'set_gpio_state'):
                    self.hardware.set_gpio_state(signal, state)
                elif hasattr(self.hardware, 'gpio') and hasattr(self.hardware.gpio, 'set_pin'):
                    self.hardware.gpio.set_pin(signal, state)
                else:
                    return "ERR Hardware does not support GPIO writing"
                    
                return "OK"
                
            else:
                return f"ERR Unknown command '{action}'"
                
        except ValueError:
            return "ERR Invalid integer/hex representation in command args"
        except Exception as e:
            return f"ERR Exception during processing: {str(e)}"
