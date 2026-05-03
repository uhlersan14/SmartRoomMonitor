# Demo-Status — 03.05.2026

Stand vor Termin mit Dozent Christian Weber (Montag 04.05.2026).

## Was funktioniert

| # | Komponente | Wie demonstrieren |
|---|------------|-------------------|
| 1 | GitHub Repo public mit klarer Struktur | https://github.com/uhlersan14/SmartRoomMonitor anzeigen, `tree` lokal |
| 2 | Pi online im neuen WLAN | Pi Connect-Tab im Browser, ggf. SSH live |
| 3 | I2C aktiviert | `sudo i2cdetect -y 1` (zeigt leere Matrix, bereit für SCD40) |
| 4 | Pi Camera V2 | `rpicam-hello --timeout 5000` Live-Vorschau, `rpicam-jpeg -o test.jpg` |
| 5 | Python-Code lauffähig | `python sensor/collector.py --mock --once` |
| 6 | SQLite mit Daten | `sqlite3 smartroom.db "SELECT * FROM measurements;"` |
| 7 | LED-Logik (grün/gelb/rot) | Code in `sensor/led_controller.py` zeigen, Mock-Output `[MOCK LED] R=False G=True B=False` |
| 8 | Flask Backend live | Browser auf http://192.168.1.131:5000 → Threshold-Form + CSV-Export |
| 9 | Grafana-Dashboard JSON | `grafana/dashboard.json` im Repo (5 Panels: CO₂ Stat, Temp, RH, Zeitreihen) |
| 10 | Doku | `docs/wiring.md`, `docs/setup.md` |

## Was offen ist

| Punkt | Grund | Plan |
|-------|-------|------|
| **SCD40 Pins anlöten** | Modul kam ohne vorgelötete Pin-Header (4 Pads + Pin-Leiste lose in Tüte) | Mit Christian besprechen → ZHAW Lötplatz oder FabLab |
| **Jumper-Kabel F-F** | Kein Kit zu Hause, brauchbar für SCD40 (post-löt) + KY-016 | Berrybase 40-pin F-F/M-M/F-M Set CHF 4.90 bestellen |
| **Grafana installieren** | 4 Versuche heute — WLAN zu schwach (-66 dBm) für 150 MB Download, .deb wurde korrupt | Morgen in ZHAW-WLAN (5 Min). Dashboard-JSON ist bereits im Repo bereit. |
| **Node-RED Flow** | Geplant für W6 | Nächste Woche: SMTP-E-Mail bei CO₂ > 1200 ppm |

## Architektur (aktuell)

```
SCD40 (I2C) ──► collector.py ──► SQLite ──► Grafana (geplant)
                  │                    └─► Flask (live)
                  └─► RGB-LED (GPIO)
```

## Argumente fürs Projekt

- **Privacy by Design:** komplett lokal, kein Cloud-Upload (Pi → SQLite → lokales Grafana). DSGVO-konform.
- **Korrelations-Analyse:** Camera + MediaPipe für Personenzählung (geplant W9–11) → Validierung dass CO₂ wirklich von Menschen kommt.
- **Hardware Made in CH:** SCD40 von Sensirion (Schweizer Hersteller).
- **Modular:** alle Komponenten via systemd, Code Review-fähig auf GitHub.
- **Ehrliche Hindernis-Kommunikation:** Hardware-Engpass (Löten) wurde proaktiv erkannt und beim Dozent angesprochen statt verschwiegen.

## Repo-Struktur

```
sensor/
  collector.py          # Hauptloop, Mock + echter SCD40
  led_controller.py     # KY-016 RGB-LED Logik
  smartroom-sensor.service  # systemd unit
database/
  schema.sql            # measurements, thresholds, room_occupancy
flask/
  app.py                # Config + CSV-Export, Port 5000
grafana/
  dashboard.json        # 5-Panel Dashboard
  datasource.yaml       # Provisioning für SQLite
  README.md             # Install-Doku
docs/
  wiring.md             # Pin-Belegung
  setup.md              # Installation auf Pi
  demo_status.md        # diese Datei
README.md               # Projektübersicht
requirements.txt        # Python deps
```
