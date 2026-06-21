# SmartRoomMonitor

IoT-Raumluftüberwachung auf Raspberry Pi 4 — ZHAW FS26
Modul: w.BA.XX.2IoTData.XX.G — IoT Data Streaming & Analytics

Vollständig lokales System (Privacy by Design, kein Cloud-Upload): Ein SCD40-Sensor misst CO₂, Temperatur und Luftfeuchtigkeit, eine RGB-LED signalisiert den Lüftungsbedarf, Grafana visualisiert die Daten, und bei kritischem CO₂ kommt ein Telegram-Alarm aufs Handy.

## Team

| Person | Schwerpunkt |
|--------|-------------|
| Sandro | Projektleitung, Backend/Automatisierung, Doku |
| Sivanujan | Python Sensor-Skript, I2C, RGB-LED, systemd |
| Alban | Grafana Dashboard, Analytics, SQLite-Plugin |
| Jaden | SQLite Setup, CSV-Export, Testing, README |

## Funktion

Der **SCD40**-Sensor misst alle 30 Sekunden CO₂, Temperatur und Luftfeuchtigkeit. `collector.py`:

1. schreibt jede Messung in **SQLite**,
2. steuert die **RGB-LED** als Ampel (grün < 800 ppm, gelb 800–1200 ppm, rot > 1200 ppm),
3. schickt bei **kritischem CO₂** einen **Telegram-Alarm** (mit Entwarnung, max. 1 Alarm / 30 min).

**Grafana** zeigt Live-Werte und Verläufe, ein **Flask**-Backend erlaubt das Konfigurieren der Schwellwerte (ohne Neustart) und den CSV-Export. Die Grenzwerte liegen in der DB und werden vom Sensor jede Runde frisch gelesen.

## Datenpipeline

```
SCD40 (I2C, alle 30 s)
   └─ collector.py ─┬─► /var/lib/smartroom-data/smartroom.db
                    │         ├─► Grafana :3000  (Visualisierung)
                    │         └─► Flask   :5000  (Grenzwerte + CSV-Export)
                    ├─► RGB-LED (GPIO 17/27/22)  grün/gelb/rot
                    └─► Telegram-Alarm  bei rot (Bot API)

Pi Camera V2 (CSI) ─► rpicam-jpeg  (Personenzählung via MediaPipe, optionales Feature)
```

**Live-Endpunkte** (Pi im WLAN `192.168.1.131`, Hostname `smartroom`):
- Grafana Dashboard: http://smartroom.local:3000 (Login `admin`)
- Flask Backend: http://smartroom.local:5000

## Tech Stack

- **Python 3** mit `sensirion-i2c-scd` (SCD40) + `RPi.GPIO` (LED) — Alerting via Telegram Bot API (`urllib`, keine Extra-Lib)
- **SQLite 3** lokal
- **Grafana** mit `frser-sqlite-datasource` Plugin
- **Flask** für Konfiguration + CSV-Export
- **systemd** für Autostart (Sensor + Flask)

> **Alerting-Entscheid:** Statt Node-RED + E-Mail wird der Alarm direkt in `collector.py` per **Telegram** verschickt — weniger bewegliche Teile, robuster, und LED + Alarm reagieren im selben Mess-Loop. Node-RED ist laut Modulvorgaben nicht zwingend; der frühere Flow liegt als optionale Beilage unter `nodered/`.

## Repo-Struktur

```
sensor/      collector.py (Sensor→DB, LED, Telegram), led_controller.py, .env.example, smartroom-sensor.service
database/    SQLite-Schema
flask/       Web-Backend (Grenzwerte + CSV-Export + /api/latest)
grafana/     Dashboard-Export (dashboard.json) + datasource.yaml
nodered/     Optionaler Flow-Export (nicht im Live-Betrieb genutzt)
docs/        Verkabelung, Setup, Architektur
```

## Quickstart auf dem Pi

Komplette Anleitung: [docs/setup.md](docs/setup.md). Kurzfassung:

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

# Telegram-Alert konfigurieren (Token von @BotFather)
cp sensor/.env.example .env
nano .env          # TELEGRAM_BOT_TOKEN und TELEGRAM_CHAT_ID eintragen

# Test ohne Hardware
python sensor/collector.py --mock --once

# Mit echtem SCD40
sudo i2cdetect -y 1            # Adresse 0x62 muss erscheinen
python sensor/collector.py --once

# Als Autostart-Service (Sensor + Flask)
sudo cp sensor/smartroom-sensor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now smartroom-sensor
```

## Telegram-Alarm einrichten

1. In Telegram **@BotFather** öffnen → `/newbot` → Token kopieren.
2. Dem neuen Bot eine beliebige Nachricht schreiben.
3. `chat_id` holen: `https://api.telegram.org/bot<TOKEN>/getUpdates` aufrufen → `chat.id` ablesen.
4. Beides in `.env` eintragen (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`) und Sensor-Service neu starten.

> Die `.env` mit den Credentials wird **nie committet** (siehe `.gitignore`). Vorlage: `sensor/.env.example`.

**Demo:** Im Flask-Formular (`:5000`) die Grenzwerte kurz tief setzen (z.B. Warnung 500 / Kritisch 600) → LED wird rot + Telegram-Alarm. Oder einfach kurz an den Sensor atmen, dann steigt CO₂ real. Danach Grenzwerte zurück auf 800 / 1200.

## Verkabelung

Siehe [docs/wiring.md](docs/wiring.md). Wichtig: Module brauchen **Female-Female** Jumper-Kabel (Pi-Header und Modul-Pins sind beide männlich).

| Modul | Pin → Pi |
|-------|----------|
| SCD40 | VDD→1 (3.3 V), SDA→3, SCL→5, GND→6 (I2C `0x62`) |
| KY-016 LED | R→11, G→13, B→15, GND→9 (GPIO 17/27/22) |

## Hardware

| Komponente | Status |
|------------|--------|
| Raspberry Pi 4 (4 GB) | ✅ Bookworm 64-bit, hostname `smartroom` |
| Pi Camera Module V2 | ✅ Angeschlossen via CSI, getestet (`imx219`) |
| SCD40 CO₂/T/RH Sensor | ✅ Gelötet, verkabelt, liefert Live-Daten |
| KY-016 RGB-LED Modul | ✅ Verkabelt, Ampel funktioniert |

## Software-Stand

| Komponente | Status |
|------------|--------|
| `collector.py` (Sensor → DB, LED, Telegram) | ✅ Live als systemd-Service |
| SQLite-DB | ✅ Echte Messdaten alle 30 s |
| Flask Backend (:5000) | ✅ Live als systemd-Service (Grenzwerte + CSV + /api/latest) |
| Grafana (:3000) | ✅ Dashboard mit 5 Panels, echte Daten |
| Telegram-Alarm | ✅ End-to-End getestet |
| systemd Autostart | ✅ `smartroom-sensor` + `smartroom-flask` (überleben Reboot) |

## Bekannte Punkte / Ausblick

- Der SCD40 liest die Temperatur leicht erhöht (Eigenerwärmung + Nähe zur Pi-Platine) — für genauere Werte den Sensor mit längeren Kabeln etwas abgesetzt platzieren oder einen Temperatur-Offset kalibrieren.
- Optionale Erweiterungen: Personenzählung per Kamera (MediaPipe), Multi-Room via MQTT, Analytics-Dashboard.

## Abgabe

28. Juni 2026, 23:59 Uhr (GitHub-Repository + Präsentation).
