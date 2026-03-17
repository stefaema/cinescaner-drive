"""
probe.py — read all TMC2209 registers and emit a Markdown report.

Usage:
    python probe.py --port /dev/ttyUSB0 [--baud 115200] [--addr 0] [--out probe.md]
"""

import argparse
import dataclasses
from datetime import datetime
from enum import IntEnum
from pathlib import Path

from registers import (
    GCONF, SLAVECONF, FACTORY_CONF, TPOWERDOWN, CHOPCONF, PWMCONF,
    IHOLD_IRUN, TPWMTHRS, TCOOLTHRS, SGTHRS, COOLCONF,
    GSTAT, IFCNT,
    DRV_STATUS, IOIN, TSTEP, MSCNT, MSCURACT, SG_RESULT, PWM_SCALE, PWM_AUTO,
)
from tmc2209 import TMC2209
from uart import UARTBus


# ── Snapshot ───────────────────────────────────────────────────────────────────

@dataclasses.dataclass(frozen=True)
class DriverSnapshot:
    # BaseConf group
    gconf:        GCONF
    slaveconf:    SLAVECONF
    factory_conf: FACTORY_CONF
    tpowerdown:   TPOWERDOWN
    chopconf:     CHOPCONF
    pwmconf:      PWMCONF
    # MotionConf group
    ihold_irun:   IHOLD_IRUN
    tpwmthrs:     TPWMTHRS
    tcoolthrs:    TCOOLTHRS
    sgthrs:       SGTHRS
    coolconf:     COOLCONF
    # Live status
    drv_status:   DRV_STATUS
    ioin:         IOIN
    tstep:        TSTEP
    mscnt:        MSCNT
    mscuract:     MSCURACT
    sg_result:    SG_RESULT
    pwm_scale:    PWM_SCALE
    pwm_auto:     PWM_AUTO
    # Specials
    gstat:        GSTAT
    ifcnt:        int   # read_ifcnt()


def probe(driver: TMC2209) -> DriverSnapshot:
    """Read all registers from the device and return an immutable snapshot."""
    r = driver.read_register
    return DriverSnapshot(
        # BaseConf
        gconf        = r(GCONF),
        slaveconf    = r(SLAVECONF),
        factory_conf = r(FACTORY_CONF),
        tpowerdown   = r(TPOWERDOWN),
        chopconf     = r(CHOPCONF),
        pwmconf      = r(PWMCONF),
        # MotionConf
        ihold_irun   = r(IHOLD_IRUN),
        tpwmthrs     = r(TPWMTHRS),
        tcoolthrs    = r(TCOOLTHRS),
        sgthrs       = r(SGTHRS),
        coolconf     = r(COOLCONF),
        # Live status
        drv_status   = r(DRV_STATUS),
        ioin         = r(IOIN),
        tstep        = r(TSTEP),
        mscnt        = r(MSCNT),
        mscuract     = r(MSCURACT),
        sg_result    = r(SG_RESULT),
        pwm_scale    = r(PWM_SCALE),
        pwm_auto     = r(PWM_AUTO),
        # Specials
        gstat        = r(GSTAT),
        ifcnt        = driver.read_ifcnt(),
    )


# ── Markdown formatter ─────────────────────────────────────────────────────────

def _fmt(value) -> str:
    if isinstance(value, bool):
        return "✓" if value else "✗"
    if isinstance(value, IntEnum):
        return f"`{value.name}` ({int(value)})"
    if isinstance(value, int):
        return f"`{value}`"
    return str(value)


def _reg_table(reg) -> str:
    cls = type(reg)
    addr = f"0x{int(cls.ADDRESS):02X}"
    lines = [
        f"### {cls.__name__} `{addr}`\n",
        "| Field | Value |",
        "|---|---|",
    ]
    for f in dataclasses.fields(reg):
        lines.append(f"| `{f.name}` | {_fmt(getattr(reg, f.name))} |")
    return "\n".join(lines)


def snapshot_to_markdown(
    snap: DriverSnapshot,
    port: str,
    addr: int,
    captured_at: datetime,
) -> str:
    ts = captured_at.strftime("%Y-%m-%d %H:%M:%S")
    sections = [
        f"# TMC2209 Driver Probe\n",
        f"**Port:** `{port}` · **Slave address:** `{addr}` · **Captured:** {ts}\n",
        "---\n",

        "## Structural Configuration (BaseConf)\n",
        _reg_table(snap.gconf),
        _reg_table(snap.slaveconf),
        _reg_table(snap.factory_conf),
        _reg_table(snap.tpowerdown),
        _reg_table(snap.chopconf),
        _reg_table(snap.pwmconf),

        "## Motion Configuration (MotionConf)\n",
        _reg_table(snap.ihold_irun),
        _reg_table(snap.tpwmthrs),
        _reg_table(snap.tcoolthrs),
        _reg_table(snap.sgthrs),
        _reg_table(snap.coolconf),

        "## Live Status\n",
        _reg_table(snap.drv_status),
        _reg_table(snap.ioin),
        _reg_table(snap.tstep),
        _reg_table(snap.mscnt),
        _reg_table(snap.mscuract),
        _reg_table(snap.sg_result),
        _reg_table(snap.pwm_scale),
        _reg_table(snap.pwm_auto),

        "## Specials\n",
        _reg_table(snap.gstat),
        "### IFCNT `0x02`\n",
        "| Field | Value |",
        "|---|---|",
        f"| `interface_transmission_counter` | {_fmt(snap.ifcnt)} |",
    ]
    return "\n\n".join(sections)


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Probe a TMC2209 and write a Markdown report.")
    parser.add_argument("--port", required=True,  help="Serial port (e.g. /dev/ttyUSB0)")
    parser.add_argument("--baud", type=int, default=115200, help="Baud rate (default: 115200)")
    parser.add_argument("--addr", type=int, default=0,      help="Slave address 0-3 (default: 0)")
    parser.add_argument("--out",  default=None,             help="Output file (default: probe_<timestamp>.md)")
    args = parser.parse_args()

    now     = datetime.now()
    outfile = Path(args.out) if args.out else Path(f"probe_{now.strftime('%Y%m%d_%H%M%S')}.md")

    with UARTBus(args.port, baudrate=args.baud) as bus:
        driver   = TMC2209(bus, addr=args.addr)
        snapshot = probe(driver)

    md = snapshot_to_markdown(snapshot, port=args.port, addr=args.addr, captured_at=now)
    outfile.write_text(md)
    print(md)
    print(f"\n---\nReport written to: {outfile.resolve()}")
