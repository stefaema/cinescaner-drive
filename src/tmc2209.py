import logging
from typing import Type, TypeVar

from registers import (
    RegisterAddress, ReadReplyDatagram,
    build_write_datagram, build_read_request_datagram,
    GSTAT, VACTUAL, IFCNT,
    DRV_STATUS, IOIN, TSTEP, MSCNT, MSCURACT, SG_RESULT, PWM_SCALE, PWM_AUTO,
)
from conf import BaseConf, MotionConf
from uart import UARTBus

log = logging.getLogger(__name__)

T = TypeVar("T")


class TMC2209:
    """TMC2209 single-axis driver."""

    def __init__(self, bus: UARTBus, addr: int = 0):
        self._bus  = bus
        self._addr = addr
        self.base   = BaseConf()
        self.motion = MotionConf()
        self._vactual: int = 0
        log.debug("TMC2209 created  addr=%d", addr)

    # ── Low-level ──────────────────────────────────────────────────────────────

    def write_register(self, reg) -> None:
        raw = reg.to_raw()
        log.debug("write  %-12s addr=0x%02X  raw=0x%08X", type(reg).__name__, int(reg.ADDRESS), raw)
        datagram = build_write_datagram(self._addr, reg.ADDRESS, raw)
        self._bus.send_write_datagram(datagram)

    def read_register(self, reg_cls: Type[T]) -> T:
        log.debug("read   %-12s addr=0x%02X", reg_cls.__name__, int(reg_cls.ADDRESS))
        request = build_read_request_datagram(self._addr, reg_cls.ADDRESS)
        reply   = ReadReplyDatagram.parse(self._bus.send_read_request(request))
        result  = reg_cls.from_raw(reply.data)
        log.debug("       %-12s raw=0x%08X  →  %s", reg_cls.__name__, reply.data, result)
        return result

    # ── Cached conf groups ─────────────────────────────────────────────────────

    def push_base(self) -> None:
        """Write all BaseConf registers to the device."""
        log.info("push_base")
        self.write_register(self.base.gconf)
        self.write_register(self.base.slaveconf)
        self.write_register(self.base.factory_conf)
        self.write_register(self.base.tpowerdown)
        self.write_register(self.base.chopconf)
        self.write_register(self.base.pwmconf)

    def pull_base(self) -> None:
        """Read all BaseConf registers from the device into self.base."""
        log.info("pull_base")
        from registers import GCONF, SLAVECONF, FACTORY_CONF, TPOWERDOWN, CHOPCONF, PWMCONF
        self.base.gconf        = self.read_register(GCONF)
        self.base.slaveconf    = self.read_register(SLAVECONF)
        self.base.factory_conf = self.read_register(FACTORY_CONF)
        self.base.tpowerdown   = self.read_register(TPOWERDOWN)
        self.base.chopconf     = self.read_register(CHOPCONF)
        self.base.pwmconf      = self.read_register(PWMCONF)

    def push_motion(self) -> None:
        """Write all MotionConf registers to the device."""
        log.info("push_motion")
        self.write_register(self.motion.ihold_irun)
        self.write_register(self.motion.tpwmthrs)
        self.write_register(self.motion.tcoolthrs)
        self.write_register(self.motion.sgthrs)
        self.write_register(self.motion.coolconf)

    def pull_motion(self) -> None:
        """Read all MotionConf registers from the device into self.motion."""
        log.info("pull_motion")
        from registers import IHOLD_IRUN, TPWMTHRS, TCOOLTHRS, SGTHRS, COOLCONF
        self.motion.ihold_irun = self.read_register(IHOLD_IRUN)
        self.motion.tpwmthrs   = self.read_register(TPWMTHRS)
        self.motion.tcoolthrs  = self.read_register(TCOOLTHRS)
        self.motion.sgthrs     = self.read_register(SGTHRS)
        self.motion.coolconf   = self.read_register(COOLCONF)

    # ── Live status — always from UART, never cached ───────────────────────────

    def drv_status(self) -> DRV_STATUS: return self.read_register(DRV_STATUS)
    def ioin(self)       -> IOIN:       return self.read_register(IOIN)
    def tstep(self)      -> TSTEP:      return self.read_register(TSTEP)
    def mscnt(self)      -> MSCNT:      return self.read_register(MSCNT)
    def mscuract(self)   -> MSCURACT:   return self.read_register(MSCURACT)
    def sg_result(self)  -> SG_RESULT:  return self.read_register(SG_RESULT)
    def pwm_scale(self)  -> PWM_SCALE:  return self.read_register(PWM_SCALE)
    def pwm_auto(self)   -> PWM_AUTO:   return self.read_register(PWM_AUTO)

    # ── Specials ───────────────────────────────────────────────────────────────

    def set_velocity(self, v: int) -> None:
        """Write VACTUAL immediately. Negative = reverse. 0 = revert to STEP pin."""
        log.info("set_velocity  v=%d", v)
        self._vactual = v
        self.write_register(VACTUAL(vactual=v))

    def read_flags(self) -> GSTAT:
        """Read latched GSTAT flags from the device."""
        return self.read_register(GSTAT)

    def clear_flags(self, gstat: GSTAT) -> None:
        """Write 1s back to latched bits to clear them."""
        self.write_register(gstat)

    def read_ifcnt(self) -> int:
        """Read UART write counter (wraps at 255)."""
        return self.read_register(IFCNT).interface_transmission_counter
