from dataclasses import dataclass
from enum import IntEnum
from typing import ClassVar


# ─── CRC ─────────────────────────────────────────────────────────────────────

def _crc8_atm(data: bytes) -> int:
    crc = 0
    for byte in data:
        for _ in range(8):
            if (crc >> 7) ^ (byte & 0x01):
                crc = ((crc << 1) ^ 0x07) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
            byte >>= 1
    return crc


# ─── Register Addresses ───────────────────────────────────────────────────────

class RegisterAddress(IntEnum):
    GCONF        = 0x00
    GSTAT        = 0x01
    IFCNT        = 0x02
    SLAVECONF    = 0x03
    OTP_PROG     = 0x04
    OTP_READ     = 0x05
    IOIN         = 0x06
    FACTORY_CONF = 0x07
    IHOLD_IRUN   = 0x10
    TPOWERDOWN   = 0x11
    TSTEP        = 0x12
    TPWMTHRS     = 0x13
    TCOOLTHRS    = 0x14
    VACTUAL      = 0x22
    SGTHRS       = 0x40
    SG_RESULT    = 0x41
    COOLCONF     = 0x42
    MSCNT        = 0x6A
    MSCURACT     = 0x6B
    CHOPCONF     = 0x6C
    DRV_STATUS   = 0x6F
    PWMCONF      = 0x70
    PWM_SCALE    = 0x71
    PWM_AUTO     = 0x72


# ─── Enumerations ─────────────────────────────────────────────────────────────

class MicrostepResolution(IntEnum):
    STEP_256 = 0b0000
    STEP_128 = 0b0001
    STEP_64  = 0b0010
    STEP_32  = 0b0011
    STEP_16  = 0b0100
    STEP_8   = 0b0101
    STEP_4   = 0b0110
    STEP_2   = 0b0111
    FULLSTEP = 0b1000


class BlankingTime(IntEnum):
    CYCLES_16 = 0b00
    CYCLES_24 = 0b01
    CYCLES_32 = 0b10
    CYCLES_40 = 0b11


class PWMFrequency(IntEnum):
    F_2_1024 = 0b00  # fPWM = 2/1024 * fCLK
    F_2_683  = 0b01  # fPWM = 2/683  * fCLK
    F_2_512  = 0b10  # fPWM = 2/512  * fCLK
    F_2_410  = 0b11  # fPWM = 2/410  * fCLK


class FreewheelMode(IntEnum):
    NORMAL           = 0b00  # Uses IHOLD current
    FREEWHEEL        = 0b01  # Open coils
    PASSIVE_BRAKE_LS = 0b10  # Short to GND via low-side MOSFETs
    PASSIVE_BRAKE_HS = 0b11  # Short to GND via high-side MOSFETs


class OTTrimMode(IntEnum):
    OT_143_OTPW_120 = 0b00
    OT_150_OTPW_120 = 0b01
    OT_150_OTPW_143 = 0b10
    OT_157_OTPW_143 = 0b11


class CoolStepCurrentIncrement(IntEnum):
    INC_1 = 0b00
    INC_2 = 0b01
    INC_4 = 0b10
    INC_8 = 0b11


class CoolStepCurrentDecrement(IntEnum):
    DEC_PER_32_READINGS = 0b00
    DEC_PER_8_READINGS  = 0b01
    DEC_PER_2_READINGS  = 0b10
    DEC_PER_READING     = 0b11


# ─── Registers ────────────────────────────────────────────────────────────────

@dataclass
class GCONF:
    """General configuration. R/W. Address 0x00."""
    ADDRESS: ClassVar[RegisterAddress] = RegisterAddress.GCONF

    i_scale_analog:   bool = False  # bit 0: use external voltage reference
    internal_rsense:  bool = False  # bit 1: use internal sense resistors
    en_spreadcycle:   bool = False  # bit 2: 0=StealthChop, 1=SpreadCycle
    shaft:            bool = False  # bit 3: invert motor direction
    index_otpw:       bool = False  # bit 4: INDEX pin shows overtemp warning
    index_step:       bool = False  # bit 5: INDEX pin toggles on every step
    pdn_disable:      bool = False  # bit 6: 1=use PDN_UART pin for UART
    mstep_reg_select: bool = False  # bit 7: 1=microstep from MSTEP register
    multistep_filt:   bool = True   # bit 8: step pulse averaging filter
    test_mode:        bool = False  # bit 9: factory test, do not set

    def to_raw(self) -> int:
        return (
            int(self.i_scale_analog)   << 0 |
            int(self.internal_rsense)  << 1 |
            int(self.en_spreadcycle)   << 2 |
            int(self.shaft)            << 3 |
            int(self.index_otpw)       << 4 |
            int(self.index_step)       << 5 |
            int(self.pdn_disable)      << 6 |
            int(self.mstep_reg_select) << 7 |
            int(self.multistep_filt)   << 8 |
            int(self.test_mode)        << 9
        )

    @classmethod
    def from_raw(cls, value: int) -> "GCONF":
        return cls(
            i_scale_analog   = bool(value & (1 << 0)),
            internal_rsense  = bool(value & (1 << 1)),
            en_spreadcycle   = bool(value & (1 << 2)),
            shaft            = bool(value & (1 << 3)),
            index_otpw       = bool(value & (1 << 4)),
            index_step       = bool(value & (1 << 5)),
            pdn_disable      = bool(value & (1 << 6)),
            mstep_reg_select = bool(value & (1 << 7)),
            multistep_filt   = bool(value & (1 << 8)),
            test_mode        = bool(value & (1 << 9)),
        )


@dataclass
class GSTAT:
    """Global status flags. R/W (write 1 to clear). Address 0x01."""
    ADDRESS: ClassVar[RegisterAddress] = RegisterAddress.GSTAT

    reset:   bool = False  # bit 0: IC was reset since last read
    drv_err: bool = False  # bit 1: driver stopped due to overtemp or short
    uv_cp:   bool = False  # bit 2: charge pump undervoltage (not latched)

    def to_raw(self) -> int:
        return (
            int(self.reset)   << 0 |
            int(self.drv_err) << 1 |
            int(self.uv_cp)   << 2
        )

    @classmethod
    def from_raw(cls, value: int) -> "GSTAT":
        return cls(
            reset   = bool(value & (1 << 0)),
            drv_err = bool(value & (1 << 1)),
            uv_cp   = bool(value & (1 << 2)),
        )


@dataclass
class IFCNT:
    """UART write counter. R-Only. Address 0x02."""
    ADDRESS: ClassVar[RegisterAddress] = RegisterAddress.IFCNT

    interface_transmission_counter: int = 0  # bits 7..0, wraps at 255

    @classmethod
    def from_raw(cls, value: int) -> "IFCNT":
        return cls(interface_transmission_counter=value & 0xFF)


@dataclass
class SLAVECONF:
    """Slave configuration. R/W. Address 0x03."""
    ADDRESS: ClassVar[RegisterAddress] = RegisterAddress.SLAVECONF

    # bits 11..8: reply delay in bit-times
    # 0,1=8; 2,3=3*8; 4,5=5*8; ... 14,15=15*8
    senddelay: int = 0

    def to_raw(self) -> int:
        return (self.senddelay & 0xF) << 8

    @classmethod
    def from_raw(cls, value: int) -> "SLAVECONF":
        return cls(senddelay=(value >> 8) & 0xF)


@dataclass
class IOIN:
    """Input pin state. R-Only. Address 0x06."""
    ADDRESS: ClassVar[RegisterAddress] = RegisterAddress.IOIN

    enn:       bool = False  # bit 0: ENN pin state (active low)
    ms1:       bool = False  # bit 2: MS1 pin state
    ms2:       bool = False  # bit 3: MS2 pin state
    diag:      bool = False  # bit 4: DIAG pin state
    pdn_uart:  bool = False  # bit 6: PDN_UART pin state
    step:      bool = False  # bit 7: STEP pin state
    spread_en: bool = False  # bit 8: SpreadCycle/StealthChop selector pin
    dir:       bool = False  # bit 9: DIR pin state
    version:   int  = 0x21  # bits 31..24: IC version (0x21)

    @classmethod
    def from_raw(cls, value: int) -> "IOIN":
        return cls(
            enn       = bool(value & (1 << 0)),
            ms1       = bool(value & (1 << 2)),
            ms2       = bool(value & (1 << 3)),
            diag      = bool(value & (1 << 4)),
            pdn_uart  = bool(value & (1 << 6)),
            step      = bool(value & (1 << 7)),
            spread_en = bool(value & (1 << 8)),
            dir       = bool(value & (1 << 9)),
            version   = (value >> 24) & 0xFF,
        )


@dataclass
class FACTORY_CONF:
    """Factory configuration. R/W. Address 0x07."""
    ADDRESS: ClassVar[RegisterAddress] = RegisterAddress.FACTORY_CONF

    fclktrim: int        = 0                        # bits 4..0: internal clock trim (0..31)
    ottrim:   OTTrimMode = OTTrimMode.OT_143_OTPW_120  # bits 9..8: OT/OTPW thresholds

    def to_raw(self) -> int:
        return (self.fclktrim & 0x1F) | (int(self.ottrim) & 0x3) << 8

    @classmethod
    def from_raw(cls, value: int) -> "FACTORY_CONF":
        return cls(
            fclktrim = value & 0x1F,
            ottrim   = OTTrimMode((value >> 8) & 0x3),
        )


@dataclass
class IHOLD_IRUN:
    """Current control. R/W. Address 0x10."""
    ADDRESS: ClassVar[RegisterAddress] = RegisterAddress.IHOLD_IRUN

    ihold:      int = 0   # bits 4..0:  standstill current (0=1/32 .. 31=32/32)
    irun:       int = 31  # bits 12..8: run current       (0=1/32 .. 31=32/32)
    iholddelay: int = 1   # bits 19..16: current ramp-down delay (0=instant, 1..15)

    def to_raw(self) -> int:
        return (
            (self.ihold       & 0x1F)      |
            (self.irun        & 0x1F) << 8 |
            (self.iholddelay  & 0x0F) << 16
        )

    @classmethod
    def from_raw(cls, value: int) -> "IHOLD_IRUN":
        return cls(
            ihold      = value & 0x1F,
            irun       = (value >> 8) & 0x1F,
            iholddelay = (value >> 16) & 0x0F,
        )


@dataclass
class TPOWERDOWN:
    """Standstill power-down delay. R/W. Address 0x11."""
    ADDRESS: ClassVar[RegisterAddress] = RegisterAddress.TPOWERDOWN

    # bits 7..0: delay from standstill to current reduction (0..255 ≈ 0..5.6s)
    # minimum 2 required for StealthChop auto-tuning
    tpowerdown: int = 20

    def to_raw(self) -> int:
        return self.tpowerdown & 0xFF

    @classmethod
    def from_raw(cls, value: int) -> "TPOWERDOWN":
        return cls(tpowerdown=value & 0xFF)


@dataclass
class TSTEP:
    """Measured microstep period. R-Only. Address 0x12."""
    ADDRESS: ClassVar[RegisterAddress] = RegisterAddress.TSTEP

    # bits 19..0: time between two 1/256 microsteps in 1/fCLK units
    # (2^20)-1 when stopped or overflowed
    tstep: int = 0

    @classmethod
    def from_raw(cls, value: int) -> "TSTEP":
        return cls(tstep=value & 0xFFFFF)


@dataclass
class TPWMTHRS:
    """StealthChop upper velocity threshold. R/W. Address 0x13."""
    ADDRESS: ClassVar[RegisterAddress] = RegisterAddress.TPWMTHRS

    # bits 19..0: StealthChop active when TSTEP >= TPWMTHRS; 0 = disabled
    tpwmthrs: int = 0

    def to_raw(self) -> int:
        return self.tpwmthrs & 0xFFFFF

    @classmethod
    def from_raw(cls, value: int) -> "TPWMTHRS":
        return cls(tpwmthrs=value & 0xFFFFF)


@dataclass
class TCOOLTHRS:
    """CoolStep/StallGuard lower velocity threshold. R/W. Address 0x14."""
    ADDRESS: ClassVar[RegisterAddress] = RegisterAddress.TCOOLTHRS

    # bits 19..0: CoolStep active when TCOOLTHRS >= TSTEP > TPWMTHRS
    tcoolthrs: int = 0

    def to_raw(self) -> int:
        return self.tcoolthrs & 0xFFFFF

    @classmethod
    def from_raw(cls, value: int) -> "TCOOLTHRS":
        return cls(tcoolthrs=value & 0xFFFFF)


@dataclass
class VACTUAL:
    """UART velocity control. R/W. Address 0x22."""
    ADDRESS: ClassVar[RegisterAddress] = RegisterAddress.VACTUAL

    # bits 23..0: signed velocity in microsteps/t; 0 = use STEP pin
    vactual: int = 0

    def to_raw(self) -> int:
        return self.vactual & 0xFFFFFF

    @classmethod
    def from_raw(cls, value: int) -> "VACTUAL":
        raw = value & 0xFFFFFF
        if raw & (1 << 23):
            raw -= (1 << 24)
        return cls(vactual=raw)


@dataclass
class SGTHRS:
    """StallGuard detection threshold. R/W. Address 0x40."""
    ADDRESS: ClassVar[RegisterAddress] = RegisterAddress.SGTHRS

    # bits 7..0: stall detected when SG_RESULT <= SGTHRS * 2
    sgthrs: int = 0

    def to_raw(self) -> int:
        return self.sgthrs & 0xFF

    @classmethod
    def from_raw(cls, value: int) -> "SGTHRS":
        return cls(sgthrs=value & 0xFF)


@dataclass
class SG_RESULT:
    """StallGuard4 load measurement. R-Only. Address 0x41."""
    ADDRESS: ClassVar[RegisterAddress] = RegisterAddress.SG_RESULT

    # bits 9..0: load indicator; higher = less load. Bits 0 and 9 always 0.
    sg_result: int = 0

    @classmethod
    def from_raw(cls, value: int) -> "SG_RESULT":
        return cls(sg_result=value & 0x3FF)


@dataclass
class COOLCONF:
    """CoolStep configuration. R/W. Address 0x42."""
    ADDRESS: ClassVar[RegisterAddress] = RegisterAddress.COOLCONF

    semin:  int                      = 0                                 # bits 3..0:  CoolStep lower threshold; 0=disabled
    seup:   CoolStepCurrentIncrement = CoolStepCurrentIncrement.INC_1   # bits 6..5:  current increment step size
    semax:  int                      = 0                                 # bits 11..8: CoolStep upper hysteresis offset
    sedn:   CoolStepCurrentDecrement = CoolStepCurrentDecrement.DEC_PER_32_READINGS  # bits 14..13: current decrement speed
    seimin: bool                     = False                             # bit 15: 0=min 1/2 IRUN, 1=min 1/4 IRUN

    def to_raw(self) -> int:
        return (
            (self.semin        & 0xF)      |
            (int(self.seup)    & 0x3) << 5 |
            (self.semax        & 0xF) << 8 |
            (int(self.sedn)    & 0x3) << 13 |
            int(self.seimin)          << 15
        )

    @classmethod
    def from_raw(cls, value: int) -> "COOLCONF":
        return cls(
            semin  = value & 0xF,
            seup   = CoolStepCurrentIncrement((value >> 5) & 0x3),
            semax  = (value >> 8) & 0xF,
            sedn   = CoolStepCurrentDecrement((value >> 13) & 0x3),
            seimin = bool(value & (1 << 15)),
        )


@dataclass
class MSCNT:
    """Microstep counter. R-Only. Address 0x6A."""
    ADDRESS: ClassVar[RegisterAddress] = RegisterAddress.MSCNT

    # bits 9..0: position in microstep table for phase A (0..1023)
    mscnt: int = 0

    @classmethod
    def from_raw(cls, value: int) -> "MSCNT":
        return cls(mscnt=value & 0x3FF)


@dataclass
class MSCURACT:
    """Microstep current values. R-Only. Address 0x6B."""
    ADDRESS: ClassVar[RegisterAddress] = RegisterAddress.MSCURACT

    cur_a: int = 0  # bits 8..0:  signed current for phase A (-255..+255)
    cur_b: int = 0  # bits 24..16: signed current for phase B (-255..+255)

    @classmethod
    def from_raw(cls, value: int) -> "MSCURACT":
        cur_a = value & 0x1FF
        if cur_a & (1 << 8):
            cur_a -= (1 << 9)
        cur_b = (value >> 16) & 0x1FF
        if cur_b & (1 << 8):
            cur_b -= (1 << 9)
        return cls(cur_a=cur_a, cur_b=cur_b)


@dataclass
class CHOPCONF:
    """Chopper configuration. R/W. Address 0x6C."""
    ADDRESS: ClassVar[RegisterAddress] = RegisterAddress.CHOPCONF

    toff:    int                 = 3                             # bits 3..0:  off time (0=driver off, 1..15)
    hstrt:   int                 = 4                             # bits 6..4:  hysteresis start value (0..7 → adds 1..8)
    hend:    int                 = 1                             # bits 10..7: hysteresis low value / sine offset (-3..12)
    tbl:     BlankingTime        = BlankingTime.CYCLES_24        # bits 16..15: comparator blanking time
    vsense:  bool                = False                         # bit 17: 0=0.325V, 1=0.180V sense voltage
    mres:    MicrostepResolution = MicrostepResolution.STEP_256  # bits 27..24: microstep resolution
    intpol:  bool                = True                          # bit 28: interpolate to 256 microsteps
    dedge:   bool                = False                         # bit 29: step on both STEP edges
    diss2g:  bool                = False                         # bit 30: disable short-to-GND protection
    diss2vs: bool                = False                         # bit 31: disable short-to-VS protection

    def to_raw(self) -> int:
        return (
            (self.toff          & 0xF)       |
            (self.hstrt         & 0x7) << 4  |
            (self.hend          & 0xF) << 7  |
            (int(self.tbl)      & 0x3) << 15 |
            int(self.vsense)           << 17 |
            (int(self.mres)     & 0xF) << 24 |
            int(self.intpol)           << 28 |
            int(self.dedge)            << 29 |
            int(self.diss2g)           << 30 |
            int(self.diss2vs)          << 31
        )

    @classmethod
    def from_raw(cls, value: int) -> "CHOPCONF":
        return cls(
            toff    = value & 0xF,
            hstrt   = (value >> 4) & 0x7,
            hend    = (value >> 7) & 0xF,
            tbl     = BlankingTime((value >> 15) & 0x3),
            vsense  = bool(value & (1 << 17)),
            mres    = MicrostepResolution((value >> 24) & 0xF),
            intpol  = bool(value & (1 << 28)),
            dedge   = bool(value & (1 << 29)),
            diss2g  = bool(value & (1 << 30)),
            diss2vs = bool(value & (1 << 31)),
        )


@dataclass
class DRV_STATUS:
    """Driver status flags and current. R-Only. Address 0x6F."""
    ADDRESS: ClassVar[RegisterAddress] = RegisterAddress.DRV_STATUS

    otpw:      bool = False  # bit 0:  overtemperature pre-warning
    ot:        bool = False  # bit 1:  overtemperature shutdown
    s2ga:      bool = False  # bit 2:  short to GND, phase A
    s2gb:      bool = False  # bit 3:  short to GND, phase B
    s2vsa:     bool = False  # bit 4:  short to VS, phase A low-side
    s2vsb:     bool = False  # bit 5:  short to VS, phase B low-side
    ola:       bool = False  # bit 6:  open load, phase A
    olb:       bool = False  # bit 7:  open load, phase B
    t120:      bool = False  # bit 8:  >120°C threshold exceeded
    t143:      bool = False  # bit 9:  >143°C threshold exceeded
    t150:      bool = False  # bit 10: >150°C threshold exceeded
    t157:      bool = False  # bit 11: >157°C threshold exceeded
    cs_actual: int  = 0      # bits 20..16: actual current scale (0..31)
    stealth:   bool = False  # bit 30: 1=StealthChop active, 0=SpreadCycle
    stst:      bool = False  # bit 31: motor at standstill

    @classmethod
    def from_raw(cls, value: int) -> "DRV_STATUS":
        return cls(
            otpw      = bool(value & (1 << 0)),
            ot        = bool(value & (1 << 1)),
            s2ga      = bool(value & (1 << 2)),
            s2gb      = bool(value & (1 << 3)),
            s2vsa     = bool(value & (1 << 4)),
            s2vsb     = bool(value & (1 << 5)),
            ola       = bool(value & (1 << 6)),
            olb       = bool(value & (1 << 7)),
            t120      = bool(value & (1 << 8)),
            t143      = bool(value & (1 << 9)),
            t150      = bool(value & (1 << 10)),
            t157      = bool(value & (1 << 11)),
            cs_actual = (value >> 16) & 0x1F,
            stealth   = bool(value & (1 << 30)),
            stst      = bool(value & (1 << 31)),
        )


@dataclass
class PWMCONF:
    """StealthChop PWM configuration. R/W. Address 0x70."""
    ADDRESS: ClassVar[RegisterAddress] = RegisterAddress.PWMCONF

    pwm_ofs:       int           = 36                      # bits 7..0:   user-defined PWM amplitude offset (0..255)
    pwm_grad:      int           = 14                      # bits 15..8:  user-defined PWM gradient (0..255)
    pwm_freq:      PWMFrequency  = PWMFrequency.F_2_1024   # bits 17..16: PWM chopper frequency
    pwm_autoscale: bool          = True                    # bit 18: automatic amplitude regulation
    pwm_autograd:  bool          = True                    # bit 19: automatic gradient adaptation
    freewheel:     FreewheelMode = FreewheelMode.NORMAL    # bits 21..20: standstill behaviour when IHOLD=0
    pwm_reg:       int           = 4                       # bits 27..24: regulation loop gradient (1..15)
    pwm_lim:       int           = 12                      # bits 31..28: amplitude limit when switching to StealthChop

    def to_raw(self) -> int:
        return (
            (self.pwm_ofs          & 0xFF)      |
            (self.pwm_grad         & 0xFF) << 8 |
            (int(self.pwm_freq)    & 0x3)  << 16 |
            int(self.pwm_autoscale)        << 18 |
            int(self.pwm_autograd)         << 19 |
            (int(self.freewheel)   & 0x3)  << 20 |
            (self.pwm_reg          & 0xF)  << 24 |
            (self.pwm_lim          & 0xF)  << 28
        )

    @classmethod
    def from_raw(cls, value: int) -> "PWMCONF":
        return cls(
            pwm_ofs       = value & 0xFF,
            pwm_grad      = (value >> 8) & 0xFF,
            pwm_freq      = PWMFrequency((value >> 16) & 0x3),
            pwm_autoscale = bool(value & (1 << 18)),
            pwm_autograd  = bool(value & (1 << 19)),
            freewheel     = FreewheelMode((value >> 20) & 0x3),
            pwm_reg       = (value >> 24) & 0xF,
            pwm_lim       = (value >> 28) & 0xF,
        )


@dataclass
class PWM_SCALE:
    """PWM scaling readback. R-Only. Address 0x71."""
    ADDRESS: ClassVar[RegisterAddress] = RegisterAddress.PWM_SCALE

    pwm_scale_sum:  int = 0  # bits 7..0:   actual PWM duty cycle (0..255)
    pwm_scale_auto: int = 0  # bits 24..16: automatic amplitude offset (-255..+255)

    @classmethod
    def from_raw(cls, value: int) -> "PWM_SCALE":
        auto = (value >> 16) & 0x1FF
        if auto & (1 << 8):
            auto -= (1 << 9)
        return cls(pwm_scale_sum=value & 0xFF, pwm_scale_auto=auto)


@dataclass
class PWM_AUTO:
    """Automatically determined PWM values. R-Only. Address 0x72."""
    ADDRESS: ClassVar[RegisterAddress] = RegisterAddress.PWM_AUTO

    pwm_ofs_auto:  int = 0  # bits 7..0:   auto-determined PWM offset (0..255)
    pwm_grad_auto: int = 0  # bits 23..16: auto-determined PWM gradient (0..255)

    @classmethod
    def from_raw(cls, value: int) -> "PWM_AUTO":
        return cls(
            pwm_ofs_auto  = value & 0xFF,
            pwm_grad_auto = (value >> 16) & 0xFF,
        )


# ─── UART Datagrams ───────────────────────────────────────────────────────────

_SYNC_BYTE     = 0x05
_MASTER_ADDR   = 0xFF


def build_write_datagram(slave_address: int, register_address: RegisterAddress, data: int) -> bytes:
    payload = bytes([0x05, slave_address & 0x3, (int(register_address) | 0x80) & 0xFF,
                     (data >> 24) & 0xFF, (data >> 16) & 0xFF, (data >> 8) & 0xFF, data & 0xFF])
    return payload + bytes([_crc8_atm(payload)])


def build_read_request_datagram(slave_address: int, register_address: RegisterAddress) -> bytes:
    payload = bytes([0x05, slave_address & 0x3, int(register_address) & 0xFF])
    return payload + bytes([_crc8_atm(payload)])


@dataclass
class ReadReplyDatagram:
    """8-byte reply datagram sent by the TMC2209 in response to a read request."""
    register_address: RegisterAddress
    data:             int  # 32-bit register value
    crc:              int

    @classmethod
    def parse(cls, raw: bytes) -> "ReadReplyDatagram":
        if len(raw) != 8:
            raise ValueError(f"Expected 8 bytes, got {len(raw)}")
        if raw[0] != _SYNC_BYTE:
            raise ValueError(f"Invalid sync byte: {raw[0]:#04x}")
        if raw[1] != _MASTER_ADDR:
            raise ValueError(f"Expected master address 0xFF, got {raw[1]:#04x}")
        reg  = RegisterAddress(raw[2])
        data = (raw[3] << 24) | (raw[4] << 16) | (raw[5] << 8) | raw[6]
        crc  = raw[7]
        if crc != _crc8_atm(raw[:7]):
            raise ValueError(f"CRC mismatch: got {crc:#04x}, expected {_crc8_atm(raw[:7]):#04x}")
        return cls(register_address=reg, data=data, crc=crc)


