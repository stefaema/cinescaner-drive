from dataclasses import dataclass, field
from registers import (
    GCONF, SLAVECONF, FACTORY_CONF, TPOWERDOWN, CHOPCONF, PWMCONF,
    IHOLD_IRUN, TPWMTHRS, TCOOLTHRS, SGTHRS, COOLCONF,
)

@dataclass
class BaseConf:
    """Structural driver configuration. Rarely changed after init."""
    gconf:        GCONF        = field(default_factory=GCONF)
    slaveconf:    SLAVECONF    = field(default_factory=SLAVECONF)
    factory_conf: FACTORY_CONF = field(default_factory=FACTORY_CONF)
    tpowerdown:   TPOWERDOWN   = field(default_factory=TPOWERDOWN)
    chopconf:     CHOPCONF     = field(default_factory=CHOPCONF)
    pwmconf:      PWMCONF      = field(default_factory=PWMCONF)

@dataclass
class MotionConf:
    """Motion tuning parameters. May change during operation."""
    ihold_irun: IHOLD_IRUN = field(default_factory=IHOLD_IRUN)
    tpwmthrs:   TPWMTHRS   = field(default_factory=TPWMTHRS)
    tcoolthrs:  TCOOLTHRS  = field(default_factory=TCOOLTHRS)
    sgthrs:     SGTHRS     = field(default_factory=SGTHRS)
    coolconf:   COOLCONF   = field(default_factory=COOLCONF)
