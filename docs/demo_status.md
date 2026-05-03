# Demo-Status — 03.05.2026

Stand vor Termin mit Dozent Christian Weber (Montag 04.05.2026).

## Was funktioniert

| # | Komponente | Wie demonstrieren |
|---|------------|-------------------|
| 1 | GitHub Repo public mit klarer Struktur | https://github.com/uhlersan14/SmartRoomMonitor anzeigen, `tree` lokal |
| 2 | Pi online (LAN + WLAN parallel) | Pi Connect-Tab, ggf. SSH live |
| 3 | I2C aktiviert | `sudo i2cdetect -y 1` (zeigt leere Matrix, bereit für SCD40) |
| 4 | Pi Camera V2 | `rpicam-hello --timeout 5000` Live-Vorschau, `rpicam-jpeg -o test.jpg` |
| 5 | Python-Code lauffähig | `python sensor/collector.py --mock --once` |
| 6 | SQLite mit Daten | `sqlite3 /var/lib/smartroom-data/smartroom.db "SELECT * FROM measurements;"` |
| 7 | LED-Logik (grün/gelb/rot) | Code in `sensor/led_controller.py` zeigen, Mock-Output `[MOCK LED] R=False G=True B=False` |
| 8 | **Flask Backend live** | http://192.168.1.130:5000 → Threshold-Form + CSV-Export |
| 9 | **Grafana Dashboard live** | http://192.168.1.130:3000 → 5 Panels mit Echtzeit-Mock-Daten (CO₂ Ampel, Temp, RH, 2 Zeitreihen) |
| 10 | Auto-Provisioning | Datasource `SmartRoomDB` automatisch gesetzt via `/etc/grafana/provisioning/datasources/smartroom.yaml` |
| 11 | Doku | `docs/wiring.md`, `docs/setup.md`, dieses File |

## Was offen ist

| Punkt | Grund | Plan |
|-------|-------|------|
| **SCD40 Pins anlöten** | Modul kam ohne vorgelötete Pin-Header (4 Pads + Pin-Leiste lose in Tüte) | Mit Christian besprechen → ZHAW Lötplatz oder FabLab |
| **Jumper-Kabel F-F** | Kein Kit zu Hause, brauchbar für SCD40 (post-löt) + KY-016 | Berrybase 40-pin F-F/M-M/F-M Set CHF 4.90 bestellen |
| **Node-RED Flow** | Geplant für W6 | Nächste Woche: SMTP-E-Mail bei CO₂ > 1200 ppm |
| **Echte Sensor-Werte** | Hardware-Verkabelung pending bis Löten + Kabel da | Mock-Modus nahtlos austauschbar |

## Architektur (aktuell, 03.05.2026)

```
SCD40 (I2C) ──► collector.py ──► /var/lib/smartroom-data/smartroom.db ──► Grafana :3000 ✅
                  │                                                  └──► Flask :5000   ✅
                  └─► KY-016 RGB-LED (GPIO 17/27/22)
                  
   Pi Camera V2 (CSI) ──► rpicam-jpeg ✅ (MediaPipe-Integration kommt W9)
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
