"""KY-016 RGB LED Controller (common cathode)."""
from __future__ import annotations

try:
    import RPi.GPIO as GPIO
    HAS_GPIO = True
except (ImportError, RuntimeError):
    HAS_GPIO = False

PIN_RED = 17
PIN_GREEN = 27
PIN_BLUE = 22


class LedController:
    def __init__(self, mock: bool = False) -> None:
        self.mock = mock or not HAS_GPIO
        if self.mock:
            return
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        for pin in (PIN_RED, PIN_GREEN, PIN_BLUE):
            GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)

    def set_color(self, red: bool, green: bool, blue: bool) -> None:
        if self.mock:
            print(f"[MOCK LED] R={red} G={green} B={blue}")
            return
        GPIO.output(PIN_RED, GPIO.HIGH if red else GPIO.LOW)
        GPIO.output(PIN_GREEN, GPIO.HIGH if green else GPIO.LOW)
        GPIO.output(PIN_BLUE, GPIO.HIGH if blue else GPIO.LOW)

    def green(self) -> None:
        self.set_color(False, True, False)

    def yellow(self) -> None:
        self.set_color(True, True, False)

    def red(self) -> None:
        self.set_color(True, False, False)

    def off(self) -> None:
        self.set_color(False, False, False)

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


if __name__ == "__main__":
    import time
    led = LedController()
    try:
        for _ in range(2):
            led.green(); time.sleep(0.5)
            led.yellow(); time.sleep(0.5)
            led.red(); time.sleep(0.5)
        led.off()
    finally:
        led.cleanup()
