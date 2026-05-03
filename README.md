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
   └─ collector.py  ──► /var/lib/smartroom-data/smartroom.db
                              ├─► Grafana :3000 ✅
                              └─► Flask   :5000 ✅ (Config + CSV)
   └─ RGB-LED (GPIO 17/27/22)
   Pi Camera V2 (CSI) ──► rpicam-jpeg ✅ (MediaPipe-Integration in W9)
   Node-RED (Port 1880) ──► E-Mail-Alert (SMTP) ⏳ W6
```

**Live-Endpunkte (Pi auf 192.168.1.130 LAN / 192.168.1.131 WLAN):**
- Flask Backend: http://192.168.1.130:5000
- Grafana Dashboard: http://192.168.1.130:3000 (Login `admin`)

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

Siehe [docs/setup.md](docs/setup.md) für komplette Anleitung. Kurzfassung:

```bash
git clone https://github.com/uhlersan14/SmartRoomMonitor.git ~/SmartRoomMonitor
cd ~/SmartRoomMonitor
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# DB ausserhalb /home/ wegen systemd ProtectHome=true (Grafana)
sudo mkdir -p /var/lib/smartroom-data
sudo chown $USER:grafana /var/lib/smartroom-data
sqlite3 /var/lib/smartroom-data/smartroom.db < database/schema.sql
ln -sf /var/lib/smartroom-data/smartroom.db ~/SmartRoomMonitor/smartroom.db

# Test ohne Hardware
python sensor/collector.py --mock --once

# Mit echtem SCD40 (sobald verkabelt)
sudo i2cdetect -y 1   # 0x62 sichtbar?
python sensor/collector.py --once
```

## Verkabelung

Siehe [docs/wiring.md](docs/wiring.md).

## Hardware

| Komponente | Status |
|------------|--------|
| Raspberry Pi 4 (4 GB) | ✅ Bookworm 64-bit, hostname `smartroom` |
| Pi Camera Module V2 | ✅ Angeschlossen via CSI, getestet (`imx219`) |
| SCD40 CO₂/T/RH Sensor | ⚠️ Pin-Header lose → Löten erforderlich |
| KY-016 RGB-LED Modul | ✅ Pins vorgelötet, einsatzbereit |
| Jumper-Kabel F-F | ⏳ Berrybase Set CHF 4.90 zu bestellen |

## Software-Stand (03.05.2026)

| Komponente | Status |
|------------|--------|
| Pi-Konfiguration (I2C, Camera) | ✅ Aktiviert |
| Python venv + Dependencies | ✅ Installiert |
| `collector.py` Mock-Modus | ✅ Schreibt SQLite |
| SQLite-DB | ✅ 20+ Datenpunkte, Schema komplett |
| Flask Backend (:5000) | ✅ Live, Threshold + CSV-Export |
| Grafana 13.0.1 (:3000) | ✅ Installiert mit `frser-sqlite-datasource` Plugin |
| Grafana Dashboard | ✅ 5 Panels live, Auto-Provisioning |
| systemd-Service | 🟡 Service-Datei vorbereitet, Deployment offen |
| Node-RED | ⏳ Geplant W6 |

## Abgabe

28. Juni 2026, 23:59 Uhr (GitHub-Repo + Präsentation)
