from typing import Type, TypeVar

from registers import (
    RegisterAddress, ReadReplyDatagram,
    build_write_datagram, build_read_request_datagram,
    GSTAT, VACTUAL, IFCNT,
    DRV_STATUS, IOIN, TSTEP, MSCNT, MSCURACT, SG_RESULT, PWM_SCALE, PWM_AUTO,
)
from conf import BaseConf, MotionConf
from uart import UARTBus

T = TypeVar("T")


class TMC2209:
    """TMC2209 single-axis driver."""

    def __init__(self, bus: UARTBus, addr: int = 0):
        self._bus  = bus
        self._addr = addr
        self.base   = BaseConf()   # mirrored; use push_base/pull_base to sync
        self.motion = MotionConf() # mirrored; use push_motion/pull_motion to sync
        self._vactual: int = 0     # last written velocity (µsteps/t)

    # ── Low-level ──────────────────────────────────────────────────────────────

    def write_register(self, reg) -> None:
        datagram = build_write_datagram(self._addr, reg.ADDRESS, reg.to_raw())
        self._bus.send_write_datagram(datagram)

    def read_register(self, reg_cls: Type[T]) -> T:
        request = build_read_request_datagram(self._addr, reg_cls.ADDRESS)
        reply   = ReadReplyDatagram.parse(self._bus.send_read_request(request))
        return reg_cls.from_raw(reply.data)

    # ── Cached conf groups ─────────────────────────────────────────────────────

    def push_base(self) -> None:
        """Write all BaseConf registers to the device."""
        # GCONF first: sets UART/chopper mode before chopconf/pwmconf
        self.write_register(self.base.gconf)
        self.write_register(self.base.slaveconf)
        self.write_register(self.base.factory_conf)
        self.write_register(self.base.tpowerdown)
        self.write_register(self.base.chopconf)
        self.write_register(self.base.pwmconf)

    def pull_base(self) -> None:
        """Read all BaseConf registers from the device into self.base."""
        from registers import GCONF, SLAVECONF, FACTORY_CONF, TPOWERDOWN, CHOPCONF, PWMCONF
        self.base.gconf        = self.read_register(GCONF)
        self.base.slaveconf    = self.read_register(SLAVECONF)
        self.base.factory_conf = self.read_register(FACTORY_CONF)
        self.base.tpowerdown   = self.read_register(TPOWERDOWN)
        self.base.chopconf     = self.read_register(CHOPCONF)
        self.base.pwmconf      = self.read_register(PWMCONF)

    def push_motion(self) -> None:
        """Write all MotionConf registers to the device."""
        self.write_register(self.motion.ihold_irun)
        self.write_register(self.motion.tpwmthrs)
        self.write_register(self.motion.tcoolthrs)
        self.write_register(self.motion.sgthrs)
        self.write_register(self.motion.coolconf)

    def pull_motion(self) -> None:
        """Read all MotionConf registers from the device into self.motion."""
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
