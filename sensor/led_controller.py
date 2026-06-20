"""KY-016 RGB LED Controller (common cathode).

Wird vom Node-RED-Flow per CLI aufgerufen:
    python led_controller.py --set red|yellow|green|off

WICHTIG: Im --set-Modus wird KEIN GPIO.cleanup() aufgerufen, damit der
gesetzte Output-Zustand (Farbe) nach Skriptende erhalten bleibt.
"""
from __future__ import annotations

import argparse
import sys

try:
    import RPi.GPIO as GPIO
    HAS_GPIO = True
except (ImportError, RuntimeError):
    HAS_GPIO = False

PIN_RED = 17
PIN_GREEN = 27
PIN_BLUE = 22

COLORS = {
    "green": (False, True, False),
    "yellow": (True, True, False),
    "red": (True, False, False),
    "off": (False, False, False),
}


class LedController:
    def __init__(self, mock: bool = False) -> None:
        self.mock = mock or not HAS_GPIO
        if self.mock:
            return
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        for pin in (PIN_RED, PIN_GREEN, PIN_BLUE):
            GPIO.setup(pin, GPIO.OUT)

    def set_color(self, red: bool, green: bool, blue: bool) -> None:
        if self.mock:
            print(f"[MOCK LED] R={red} G={green} B={blue}")
            return
        GPIO.output(PIN_RED, GPIO.HIGH if red else GPIO.LOW)
        GPIO.output(PIN_GREEN, GPIO.HIGH if green else GPIO.LOW)
        GPIO.output(PIN_BLUE, GPIO.HIGH if blue else GPIO.LOW)

    def set_named(self, name: str) -> None:
        self.set_color(*COLORS[name])

    def green(self) -> None:
        self.set_named("green")

    def yellow(self) -> None:
        self.set_named("yellow")

    def red(self) -> None:
        self.set_named("red")

    def off(self) -> None:
        self.set_named("off")

    def update_by_co2(self, co2_ppm: int, warn: int = 800, crit: int = 1200) -> str:
        if co2_ppm >= crit:
            self.red()
            return "red"
        if co2_ppm >= warn:
            self.yellow()
            return "yellow"
        self.green()
        return "green"

    def cleanup(self) -> None:
        if self.mock:
            return
        GPIO.cleanup()


def main() -> int:
    parser = argparse.ArgumentParser(description="KY-016 RGB-LED steuern")
    parser.add_argument("--set", dest="color", choices=list(COLORS),
                        help="LED auf Farbe setzen (Zustand bleibt erhalten)")
    parser.add_argument("--demo", action="store_true", help="Farb-Durchlauf zum Testen")
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args()

    led = LedController(mock=args.mock)

    if args.color:
        # KEIN cleanup() -> Pin-Zustand bleibt nach Skriptende erhalten
        led.set_named(args.color)
        return 0

    if args.demo:
        import time
        try:
            for _ in range(2):
                led.green(); time.sleep(0.5)
                led.yellow(); time.sleep(0.5)
                led.red(); time.sleep(0.5)
            led.off()
        finally:
            led.cleanup()
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
