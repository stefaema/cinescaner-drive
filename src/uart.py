import serial


class UARTError(Exception):
    """Raised when a UART-level protocol error occurs (incomplete echo or reply)."""


class UARTBus:
    """Single-wire UART bus for TMC2209 communication.

    TX and RX share the same wire, so every transmitted byte is echoed back
    on RX. The echo must be discarded before reading any reply from the device.
    """

    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 0.1):
        self._serial = serial.Serial(port, baudrate=baudrate, timeout=timeout)

    def close(self) -> None:
        self._serial.close()

    def __enter__(self) -> "UARTBus":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def send_write_datagram(self, datagram: bytes) -> None:
        """Send an 8-byte write datagram and discard the echo."""
        if len(datagram) != 8:
            raise ValueError(f"Write datagram must be 8 bytes, got {len(datagram)}")
        self._serial.write(datagram)
        echo = self._serial.read(8)
        if len(echo) != 8:
            raise UARTError(f"Incomplete echo: expected 8 bytes, got {len(echo)}")

    def send_read_request(self, request: bytes) -> bytes:
        """Send a 4-byte read request, discard the echo, and return the 8-byte reply."""
        if len(request) != 4:
            raise ValueError(f"Read request must be 4 bytes, got {len(request)}")
        self._serial.write(request)
        echo = self._serial.read(4)
        if len(echo) != 4:
            raise UARTError(f"Incomplete echo: expected 4 bytes, got {len(echo)}")
        reply = self._serial.read(8)
        if len(reply) != 8:
            raise UARTError(f"Incomplete reply: expected 8 bytes, got {len(reply)}")
        return reply
