import logging
import time
import serial

log = logging.getLogger(__name__)


class UARTError(Exception):
    """Raised when a UART-level protocol error occurs (incomplete echo or reply)."""


class UARTBus:
    """Single-wire UART bus for TMC2209 communication.

    TX and RX share the same wire, so every transmitted byte is echoed back
    on RX. The echo must be discarded before reading any reply from the device.
    """

    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 0.1):
        self._serial   = serial.Serial(port, baudrate=baudrate, timeout=timeout)
        self._bit_time = 1.0 / baudrate
        log.debug("opened %s  baudrate=%d  timeout=%.3fs", port, baudrate, timeout)

    def close(self) -> None:
        self._serial.close()
        log.debug("port closed")

    def __enter__(self) -> "UARTBus":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def send_write_datagram(self, datagram: bytes) -> None:
        """Send an 8-byte write datagram and discard the echo."""
        if len(datagram) != 8:
            raise ValueError(f"Write datagram must be 8 bytes, got {len(datagram)}")
        log.debug("TX write  %s", datagram.hex(" ").upper())
        self._serial.write(datagram)
        echo = self._serial.read(8)
        log.debug("RX echo   %s  (%d bytes)", echo.hex(" ").upper(), len(echo))
        if len(echo) != 8:
            raise UARTError(f"Incomplete echo: expected 8 bytes, got {len(echo)}")

    def send_read_request(self, request: bytes) -> bytes:
        """Send a 4-byte read request, discard the echo, and return the 8-byte reply."""
        if len(request) != 4:
            raise ValueError(f"Read request must be 4 bytes, got {len(request)}")
        self._serial.reset_input_buffer()
        log.debug("TX read   %s", request.hex(" ").upper())
        self._serial.write(request)
        # Wait for echo (4B) + senddelay (8 bit-times) + reply (8B) to fully arrive.
        frame_time = ((4 + 8) * 10 + 8) * self._bit_time
        sleep_s = frame_time * 3
        log.debug("sleeping %.1f ms before read", sleep_s * 1000)
        time.sleep(sleep_s)
        waiting = self._serial.in_waiting
        log.debug("in_waiting=%d bytes", waiting)
        frame = self._serial.read(waiting)
        log.debug("RX frame  %s  (%d bytes)", frame.hex(" ").upper(), len(frame))
        if len(frame) < 12:
            raise UARTError(f"Incomplete frame: expected 12 bytes, got {len(frame)}")
        reply = frame[4:12]
        log.debug("reply     %s", reply.hex(" ").upper())
        return reply
