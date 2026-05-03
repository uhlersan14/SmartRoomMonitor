# Setup — Raspberry Pi

## Voraussetzungen

- Raspberry Pi 4 mit Pi OS Bookworm 64-bit
- I2C aktiviert (`sudo raspi-config` → Interfaces → I2C)
- Camera aktiviert (auto-detect bei Bookworm)
- Hardware: SCD40 (4 Pins gelötet), KY-016 LED, Camera V2

## Installation

```bash
# Pakete
sudo apt-get install -y i2c-tools python3-pip python3-venv sqlite3 git libcamera-apps

# Repo
cd ~
git clone https://github.com/uhlersan14/SmartRoomMonitor.git
cd SmartRoomMonitor

# Python venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# DB Schema initial anlegen
sqlite3 smartroom.db < database/schema.sql

# Mock-Test (ohne Hardware)
python sensor/collector.py --mock --once

# Mit echtem Sensor (sobald SCD40 verkabelt)
i2cdetect -y 1   # Adresse 0x62 muss auftauchen
python sensor/collector.py --once
```

## systemd Service

```bash
sudo cp sensor/smartroom-sensor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now smartroom-sensor
sudo systemctl status smartroom-sensor
```

## Flask Backend

```bash
source .venv/bin/activate
python flask/app.py
# http://<pi-ip>:5000
```

## Camera Test

```bash
libcamera-hello --timeout 5000      # 5s Live-Vorschau
libcamera-jpeg -o test.jpg          # Foto speichern
```
