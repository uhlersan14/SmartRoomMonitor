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

SCD40-Sensor misst CO₂, Temperatur und Luftfeuchtigkeit alle 30 Sekunden. Eine RGB-LED zeigt den Lüftungsbedarf an (grün < 800 ppm, gelb 800–1200 ppm, rot > 1200 ppm). Daten landen lokal in SQLite. Grafana visualisiert, **Node-RED steuert die LED und alarmiert per E-Mail**, ein Flask-Backend erlaubt das Konfigurieren der Schwellwerte und CSV-Export. Eine Pi-Camera zählt zusätzlich Personen im Raum (OpenCV/MediaPipe) für Korrelationsanalysen.

## Datenpipeline

```
SCD40 (I2C, 30 s)
   └─ collector.py  ──► /var/lib/smartroom-data/smartroom.db
                              ├─► Grafana :3000 ✅ (Visualisierung)
                              └─► Flask   :5000 ✅ (Config + CSV + /api/latest)

Node-RED :1880 ──► GET /api/latest (30 s)
   ├─► RGB-LED (GPIO 17/27/22) via led_controller.py
   └─► E-Mail-Alert (SMTP) bei rot, max. 1/30 min

Pi Camera V2 (CSI) ──► rpicam-jpeg ✅ (MediaPipe-Integration in W9)
```

**Live-Endpunkte (Pi auf 192.168.1.130 LAN / 192.168.1.131 WLAN):**
- Flask Backend: http://192.168.1.130:5000
- Grafana Dashboard: http://192.168.1.130:3000 (Login `admin`)
- Node-RED: http://192.168.1.130:1880

## Tech Stack

- Python 3 mit `sensirion-i2c-scd` (SCD40), `RPi.GPIO`, `Flask`
- SQLite 3 lokal
- Grafana mit `frser-sqlite-datasource` Plugin
- Node-RED mit `node-red-node-email` für Steuerung + Alerting
- systemd für Autostart

## Repo-Struktur

```
sensor/      Python-Skripte (collector.py, led_controller.py, .service)
database/    SQLite-Schema
flask/       Web-Backend (Grenzwerte + CSV-Export + /api/latest)
grafana/     Dashboard-Export (JSON)
nodered/     Flow-Export (flow.json) + Anleitung
docs/        Verkabelung, Setup, Architektur
```

## Quickstart auf dem Pi

Siehe [docs/setup.md](docs/setup.md) und [nodered/README.md](nodered/README.md). Kurzfassung:

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

# LED manuell testen
python sensor/led_controller.py --demo
```

## Verkabelung

Siehe [docs/wiring.md](docs/wiring.md). Wichtig: Module brauchen **Female-Female** Jumper-Kabel (Pi-Header und Modul-Pins sind beide männlich).

## Hardware

| Komponente | Status |
|------------|--------|
| Raspberry Pi 4 (4 GB) | ✅ Bookworm 64-bit, hostname `smartroom` |
| Pi Camera Module V2 | ✅ Angeschlossen via CSI, getestet (`imx219`) |
| SCD40 CO₂/T/RH Sensor | ✅ Pin-Header gelötet |
| KY-016 RGB-LED Modul | ✅ Pins vorgelötet, einsatzbereit |
| Jumper-Kabel F-F | ⏳ zu beschaffen (Pi ↔ Sensor/LED) |

## Software-Stand

| Komponente | Status |
|------------|--------|
| Pi-Konfiguration (I2C, Camera) | ✅ Aktiviert |
| Python venv + Dependencies | ✅ Installiert |
| `collector.py` Mock + echter SCD40-Pfad | ✅ |
| SQLite-DB | ✅ Schema komplett |
| Flask Backend (:5000) | ✅ Threshold + CSV-Export + /api/latest |
| Grafana 13.0.1 (:3000) | ✅ 5 Panels, Auto-Provisioning |
| Node-RED (:1880) | ✅ Flow: LED-Steuerung + E-Mail-Alert |
| systemd-Service (Sensor) | 🟡 Service-Datei vorhanden, Deployment nach Verkabelung |

## Offen bis zur Abgabe

- Sensor + LED physisch verkabeln (F-F-Kabel), `i2cdetect` → `0x62` prüfen
- systemd-Service deployen (`sudo systemctl enable --now smartroom-sensor`)
- Node-RED E-Mail-Credentials eintragen (siehe nodered/README.md)
- End-to-End-Test: Sensor → DB → Grafana → Node-RED → LED + Mail

## Abgabe

28. Juni 2026, 23:59 Uhr (GitHub-Präsentation)
