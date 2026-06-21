"""SmartRoomMonitor sensor collector.

Liest SCD40 alle 30s, schreibt SQLite, steuert RGB-LED und schickt bei
kritischem CO2 einen Telegram-Alert.
Mit --mock laufen ohne echte Hardware (Demo/Test).

Telegram-Credentials kommen aus .env (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
und landen NIE im Repo.
"""
from __future__ import annotations

import argparse
import logging
import os
import random
import signal
import sqlite3
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

from led_controller import LedController

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

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
        # Falls ein frueherer Lauf noch im Messmodus haengt: erst stoppen.
        try:
            self._dev.stop_periodic_measurement()
            time.sleep(1)
        except Exception:
            pass
        self._dev.start_periodic_measurement()
        time.sleep(5)

    def read(self) -> tuple[int, float, float]:
        # read_measurement() liefert (Scd4xCarbonDioxide, Scd4xTemperature, Scd4xHumidity)
        co2, temp, hum = self._dev.read_measurement()
        return int(co2.co2), round(temp.degrees_celsius, 1), round(hum.percent_rh, 1)

    def close(self) -> None:
        try:
            self._dev.stop_periodic_measurement()
        finally:
            self._t.__exit__(None, None, None)


class TelegramNotifier:
    """Schickt Alerts per Telegram Bot API (urllib, keine externe Lib).

    - Edge-getriggert: Alarm beim Wechsel nach rot, Entwarnung beim Verlassen.
    - Rate-Limit: waehrend dauerhaft rot max. 1 Erinnerung pro 30 Minuten.
    """
    def __init__(self, min_interval_s: int = 1800) -> None:
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.enabled = bool(self.token and self.chat_id)
        self._min_interval = min_interval_s
        self._last_sent = 0.0
        self._was_critical = False
        if not self.enabled:
            LOG.warning("Telegram deaktiviert (TELEGRAM_BOT_TOKEN/CHAT_ID fehlen in .env)")

    def _send(self, text: str) -> None:
        if not self.enabled:
            return
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        data = urllib.parse.urlencode({"chat_id": self.chat_id, "text": text}).encode()
        try:
            urllib.request.urlopen(url, data=data, timeout=10)
        except Exception as e:  # noqa: BLE001
            LOG.warning("Telegram-Versand fehlgeschlagen: %s", e)

    def handle(self, status: str, co2: int, crit: int, temp: float, hum: float) -> None:
        now = time.time()
        if status == "red":
            first = not self._was_critical
            due = now - self._last_sent >= self._min_interval
            if first or due:
                self._send(
                    f"\U0001F534 SmartRoom Alarm: CO₂ {co2} ppm "
                    f"(Grenzwert {crit} ppm)\nTemp {temp} °C, Feuchte {hum} %\n"
                    f"Bitte den Raum lüften."
                )
                self._last_sent = now
            self._was_critical = True
        else:
            if self._was_critical:
                self._send(f"\U0001F7E2 Entwarnung: CO₂ wieder bei {co2} ppm. Luft ist ok.")
            self._was_critical = False


def init_db(db_path: Path) -> None:
    schema = (Path(__file__).resolve().parent.parent / "database" / "schema.sql").read_text()
    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema)


def get_thresholds(db_path: Path) -> tuple[int, int]:
    with sqlite3.connect(db_path) as conn:
        row = conn.execute("SELECT co2_warning, co2_critical FROM thresholds WHERE id=1").fetchone()
    return (row[0], row[1]) if row else (800, 1200)


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
    parser.add_argument("--mock", action="store_true", help="Mock-Sensor + Mock-LED ohne Hardware")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL_S)
    parser.add_argument("--once", action="store_true", help="Nur eine Messung schreiben und beenden")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    init_db(args.db)
    LOG.info("DB ready: %s", args.db)

    sensor = MockSensor() if args.mock else Scd40Sensor()
    led = LedController(mock=args.mock)
    notifier = TelegramNotifier()
    LOG.info("Sensor=%s LED=%s Telegram=%s", type(sensor).__name__,
             "mock" if args.mock else "gpio", "an" if notifier.enabled else "aus")

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    try:
        while _running:
            warn, crit = get_thresholds(args.db)
            co2, temp, hum = sensor.read()
            insert_measurement(args.db, co2, temp, hum)
            color = led.update_by_co2(co2, warn, crit)
            notifier.handle(color, co2, crit, temp, hum)
            LOG.info("CO2=%d ppm  T=%.1f C  RH=%.1f %%  led=%s", co2, temp, hum, color)
            if args.once:
                break
            for _ in range(args.interval):
                if not _running:
                    break
                time.sleep(1)
    finally:
        led.off()
        led.cleanup()
        if hasattr(sensor, "close"):
            sensor.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
