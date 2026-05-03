# SmartRoomMonitor

IoT-Raumluftüberwachung auf Raspberry Pi 4 — ZHAW FS26
Modul: w.BA.XX.2IoTData.XX.G — IoT Data Streaming & Analytics

## Team

| Person | Schwerpunkt |
|--------|-------------|
| Sandro | Projektleitung, Node-RED, Flask, Doku |
| Sivanujan | Python Sensor-Skript, I2C, RGB-LED, systemd |
| Alban | Grafana Dashboard, Analytics, SQLite-Plugin |
| Jaden | SQLite Setup, CSV-Export, Testing, README |

## Funktion

SCD40-Sensor misst CO₂, Temperatur und Luftfeuchtigkeit alle 30 Sekunden. Eine RGB-LED zeigt den Lüftungsbedarf an (grün < 800 ppm, gelb 800–1200 ppm, rot > 1200 ppm). Daten landen lokal in SQLite. Grafana visualisiert, Node-RED alarmiert per E-Mail, ein Flask-Backend erlaubt das Konfigurieren der Schwellwerte und CSV-Export. Eine Pi-Camera zählt zusätzlich Personen im Raum (OpenCV/MediaPipe) für Korrelationsanalysen.

## Datenpipeline

```
SCD40 (I2C, 30 s)
   └─ collector.py  ──► SQLite ──► Grafana   (Port 3000)
          │                  └──► Flask     (Port 5000, Config + CSV)
          └─ RGB-LED (GPIO)
   Node-RED (Port 1880) ──► E-Mail-Alert (SMTP)
```

## Tech Stack

- Python 3 mit `sensirion-i2c-scd` (SCD40), `RPi.GPIO`, `Flask`
- SQLite 3 lokal
- Grafana mit `frser-sqlite-datasource` Plugin
- Node-RED für Alerting
- systemd für Autostart

## Repo-Struktur

```
sensor/      Python-Skripte (collector.py, led_controller.py, .service)
database/    SQLite-Schema
flask/       Web-Backend (Grenzwerte + CSV-Export)
grafana/     Dashboard-Export (JSON)
nodered/     Flow-Export (JSON)
docs/        Verkabelung, Setup, Architektur
```

## Quickstart auf dem Pi

Siehe [docs/setup.md](docs/setup.md). Kurzfassung:

```bash
git clone https://github.com/uhlersan14/SmartRoomMonitor.git ~/SmartRoomMonitor
cd ~/SmartRoomMonitor
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
sqlite3 smartroom.db < database/schema.sql

# Test ohne Hardware
python sensor/collector.py --mock --once

# Mit echtem SCD40 (sobald verkabelt)
i2cdetect -y 1   # 0x62 sichtbar?
python sensor/collector.py --once
```

## Verkabelung

Siehe [docs/wiring.md](docs/wiring.md).

## Hardware

| Komponente | Status |
|------------|--------|
| Raspberry Pi 4 (4 GB) | ✅ vorhanden |
| Pi Camera Module V2 | ✅ erhalten |
| SCD40 CO₂/T/RH Sensor | ⚠️ Pins müssen gelötet werden |
| KY-016 RGB-LED Modul | ✅ einsatzbereit |
| Jumper-Kabel (F-F) | ⏳ bestellt (Berrybase) |

## Abgabe

28. Juni 2026, 23:59 Uhr (GitHub-Repo + Präsentation)
