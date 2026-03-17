import time
import serial


class UARTError(Exception):
    """Raised when a UART-level protocol error occurs (incomplete echo or reply)."""


class UARTBus:
    """Single-wire UART bus for TMC2209 communication.

    TX and RX share the same wire, so every transmitted byte is echoed back
    on RX. The echo must be discarded before reading any reply from the device.
    """

    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 0.1):
        self._serial  = serial.Serial(port, baudrate=baudrate, timeout=timeout)
        self._bit_time = 1.0 / baudrate  # seconds per bit

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
        """Send a 4-byte read request, discard the echo, and return the 8-byte reply.

        A calculated sleep ensures the full echo + reply frame (12 bytes) has
        arrived before reading, avoiding early returns caused by Windows COM port
        inter-byte gap detection between the echo and the driver's response.

        Sleep covers: 4-byte echo + 8-bit senddelay + 8-byte reply, with 3× margin.
        """
        if len(request) != 4:
            raise ValueError(f"Read request must be 4 bytes, got {len(request)}")
        self._serial.reset_input_buffer()
        self._serial.write(request)
        # 10 bits per byte (start + 8 data + stop); senddelay default = 8 bit-times
        frame_time = ((4 + 8) * 10 + 8) * self._bit_time
        time.sleep(frame_time * 3)
        frame = self._serial.read(12)   # 4-byte echo + 8-byte reply
        if len(frame) != 12:
            raise UARTError(f"Incomplete frame: expected 12 bytes, got {len(frame)}")
        return frame[4:]                # strip echo, return reply
