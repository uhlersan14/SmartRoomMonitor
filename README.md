# SmartRoomMonitor

IoT Raumluftüberwachung auf Raspberry Pi 4 – ZHAW FS26
Modul: w.BA.XX.2IoTData.XX.G – IoT Data Streaming & Analytics

## Team
- Sandro – Projektleitung, Node-RED, Flask, Doku
- Sivanujan – Python Sensor-Skript, I2C, RGB-LED, systemd
- Alban – Grafana Dashboard, Analytics, SQLite-Plugin
- Jaden – SQLite Setup, CSV-Export, Testing, README

## Projektbeschreibung
SCD40-Sensor misst CO₂, Temperatur und Luftfeuchtigkeit alle 30s.
RGB-LED signalisiert Lüftungsbedarf (grün/gelb/rot).
Grafana-Dashboard für Visualisierung, Node-RED für Alerting, Flask für Konfiguration.

## Ordnerstruktur
```
sensor/     # Python Sensor-Skript (SCD40, RGB-LED, systemd)
database/   # SQLite Schema, Migrations, CSV-Export
grafana/    # Dashboard JSON Export
nodered/    # Flow Export
flask/      # Web Backend (Grenzwerte konfigurieren)
docs/       # Dokumentation, Verkabelung, Architektur
```

## Tech Stack
- Python 3 + scd4x Library
- SQLite 3
- Grafana + frser-sqlite-datasource Plugin (Port 3000)
- Node-RED (Port 1880)
- Flask (Port 5000)

## Abgabe
28. Juni 2026, 23:59 Uhr
