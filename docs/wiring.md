# Verkabelung — SmartRoomMonitor

## SCD40 Sensor (I2C)

| SCD40 | Pi GPIO | Pi Pin |
|-------|---------|--------|
| VDD   | 3.3 V   | Pin 1  |
| GND   | GND     | Pin 6  |
| SDA   | GPIO 2  | Pin 3  |
| SCL   | GPIO 3  | Pin 5  |

I2C-Adresse: `0x62`. Verifizieren via `i2cdetect -y 1`.

## KY-016 RGB-LED

| KY-016 | Pi GPIO  | Pi Pin |
|--------|----------|--------|
| R      | GPIO 17  | Pin 11 |
| G      | GPIO 27  | Pin 13 |
| B      | GPIO 22  | Pin 15 |
| GND    | GND      | Pin 9  |

KY-016 = Common Cathode mit integrierten Vorwiderständen.

## Camera Module V2

CSI-Port am Pi (zwischen HDMI und 3.5mm-Audio-Buchse). Silberne Kontakte zur HDMI-Seite.

Test:
```
libcamera-hello --timeout 5000
libcamera-jpeg -o test.jpg
```

## Pinout-Referenz

```
        3V3  (1) (2)  5V
      GPIO2  (3) (4)  5V       <- SDA SCD40
      GPIO3  (5) (6)  GND      <- SCL SCD40 / GND SCD40
      GPIO4  (7) (8)  GPIO14
        GND  (9) (10) GPIO15   <- GND KY-016
     GPIO17 (11) (12) GPIO18   <- R KY-016
     GPIO27 (13) (14) GND      <- G KY-016
     GPIO22 (15) (16) GPIO23   <- B KY-016
```
