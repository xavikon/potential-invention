"""
Integration and protocol tests for the TCP Socket I2C Bridge Server.
"""
import socket
import time
import pytest
from src.hardware.bridge import I2CBridgeServer

class MockHardwareBridgeTarget:
    """Mock target satisfying the interface read/write and GPIO signatures."""
    def __init__(self):
        self.registers = {0x10: 0x55, 0x11: 0x66}
        self.gpio = {"reset": False}
        
    def read_registers(self, bus_address: int, reg_address: int, count: int) -> list:
        return [self.registers.get(reg_address + i, 0x00) for i in range(count)]
        
    def write_registers(self, bus_address: int, reg_address: int, values: bytes) -> None:
        for i, val in enumerate(values):
            self.registers[reg_address + i] = val
            
    def get_gpio_state(self, signal: str) -> bool:
        return self.gpio.get(signal, False)
        
    def set_gpio_state(self, signal: str, state: bool) -> None:
        self.gpio[signal] = state


def get_free_port() -> int:
    """Helper to dynamically allocate a free port on localhost."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def test_bridge_protocol():
    """Verify standard TCP client read/write and GPIO set/get transactions."""
    mock_hw = MockHardwareBridgeTarget()
    port = get_free_port()
    
    server = I2CBridgeServer(hardware=mock_hw, host="127.0.0.1", port=port)
    server.start()
    
    # Wait briefly for socket binding to complete
    time.sleep(0.1)
    
    try:
        # Create client socket
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("127.0.0.1", port))
        
        # Test READ command: read 2 bytes from 0x10
        client.sendall(b"READ 0xA0 0x10 2\n")
        response = client.recv(1024).decode("utf-8").strip()
        assert response == "55 66"
        
        # Test WRITE command: write values 0xAA 0xBB starting at 0x10
        client.sendall(b"WRITE 0xA0 0x10 AA BB\n")
        response = client.recv(1024).decode("utf-8").strip()
        assert response == "OK"
        
        # Verify write worked by reading back
        client.sendall(b"READ 0xA0 0x10 2\n")
        response = client.recv(1024).decode("utf-8").strip()
        assert response == "AA BB"
        
        # Test GPIO_GET command
        client.sendall(b"GPIO_GET reset\n")
        response = client.recv(1024).decode("utf-8").strip()
        assert response == "0"
        
        # Test GPIO_SET command
        client.sendall(b"GPIO_SET reset 1\n")
        response = client.recv(1024).decode("utf-8").strip()
        assert response == "OK"
        
        # Verify GPIO set succeeded
        client.sendall(b"GPIO_GET reset\n")
        response = client.recv(1024).decode("utf-8").strip()
        assert response == "1"
        
        # Test closing session
        client.sendall(b"BYE\n")
        response = client.recv(1024).decode("utf-8").strip()
        assert response == "BYE"
        
        client.close()
        
    finally:
        server.stop()
