"""SmartRoomMonitor sensor collector.

Liest SCD40 alle 30s und schreibt SQLite.
Die RGB-LED wird vom Node-RED-Flow gesteuert (nicht mehr hier).
Mit --mock laufen ohne echte Hardware (Demo/Test).
"""
from __future__ import annotations

import argparse
import logging
import random
import signal
import sqlite3
import sys
import time
from pathlib import Path

LOG = logging.getLogger("collector")

DEFAULT_DB = Path(__file__).resolve().parent.parent / "smartroom.db"
DEFAULT_INTERVAL_S = 30


class MockSensor:
    """Erzeugt realistische Fake-Daten ohne SCD40."""
    def __init__(self) -> None:
        self.co2 = 600
        self.temp = 22.0
        self.hum = 45.0

    def read(self) -> tuple[int, float, float]:
        self.co2 += random.randint(-30, 50)
        self.co2 = max(400, min(self.co2, 2000))
        self.temp += random.uniform(-0.2, 0.2)
        self.hum += random.uniform(-0.5, 0.5)
        return self.co2, round(self.temp, 1), round(self.hum, 1)


class Scd40Sensor:
    """Echter SCD40 via I2C (sensirion-i2c-scd Library)."""
    def __init__(self) -> None:
        from sensirion_i2c_driver import I2cConnection, LinuxI2cTransceiver
        from sensirion_i2c_scd import Scd4xI2cDevice
        self._t = LinuxI2cTransceiver("/dev/i2c-1")
        self._t.__enter__()
        self._dev = Scd4xI2cDevice(I2cConnection(self._t))
        self._dev.start_periodic_measurement()
        time.sleep(5)

    def read(self) -> tuple[int, float, float]:
        co2, temp, hum = self._dev.read_measurement()
        return int(co2), float(temp), float(hum)

    def close(self) -> None:
        try:
            self._dev.stop_periodic_measurement()
        finally:
            self._t.__exit__(None, None, None)


def init_db(db_path: Path) -> None:
    schema = (Path(__file__).resolve().parent.parent / "database" / "schema.sql").read_text()
    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema)


def insert_measurement(db_path: Path, co2: int, temp: float, hum: float) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO measurements (co2_ppm, temperature, humidity) VALUES (?, ?, ?)",
            (co2, temp, hum),
        )


_running = True
def _stop(*_: object) -> None:
    global _running
    _running = False
    LOG.info("Stop requested")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mock", action="store_true", help="Mock-Sensor ohne Hardware")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL_S)
    parser.add_argument("--once", action="store_true", help="Nur eine Messung schreiben und beenden")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    init_db(args.db)
    LOG.info("DB ready: %s", args.db)

    sensor = MockSensor() if args.mock else Scd40Sensor()
    LOG.info("Sensor=%s", type(sensor).__name__)

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    try:
        while _running:
            co2, temp, hum = sensor.read()
            insert_measurement(args.db, co2, temp, hum)
            LOG.info("CO2=%d ppm  T=%.1f C  RH=%.1f %%", co2, temp, hum)
            if args.once:
                break
            for _ in range(args.interval):
                if not _running:
                    break
                time.sleep(1)
    finally:
        if hasattr(sensor, "close"):
            sensor.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
