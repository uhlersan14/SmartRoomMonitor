# Setup — Raspberry Pi

## Voraussetzungen

- Raspberry Pi 4 mit Pi OS Bookworm 64-bit
- I2C aktiviert (`sudo raspi-config` → Interfaces → I2C)
- Camera aktiviert (auto-detect bei Bookworm)
- Hardware: SCD40 (4 Pins gelötet), KY-016 LED, Camera V2

## Installation

```bash
# Pakete
sudo apt-get install -y i2c-tools python3-pip python3-venv sqlite3 git rpicam-apps

# Repo
cd ~
git clone https://github.com/uhlersan14/SmartRoomMonitor.git
cd SmartRoomMonitor

# Python venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# DB-Verzeichnis ausserhalb /home/ (wegen systemd ProtectHome=true bei Grafana)
sudo mkdir -p /var/lib/smartroom-data
sudo chown $USER:grafana /var/lib/smartroom-data
sudo chmod 775 /var/lib/smartroom-data

# DB initial anlegen
sqlite3 /var/lib/smartroom-data/smartroom.db < database/schema.sql
sudo chmod 664 /var/lib/smartroom-data/smartroom.db

# Symlink für Code-Kompatibilität (collector.py default path)
ln -sf /var/lib/smartroom-data/smartroom.db ~/SmartRoomMonitor/smartroom.db

# Mock-Test (ohne Hardware)
python sensor/collector.py --mock --once

# Mit echtem Sensor (sobald SCD40 gelötet + verkabelt)
sudo i2cdetect -y 1   # Adresse 0x62 muss auftauchen
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
rpicam-hello --timeout 5000      # 5s Live-Vorschau
rpicam-jpeg -o test.jpg          # Foto speichern
```

## Grafana

```bash
# Repo hinzufügen
sudo mkdir -p /etc/apt/keyrings/
sudo wget -q -O /tmp/grafana.gpg.key https://apt.grafana.com/gpg.key
sudo gpg --batch --yes --dearmor -o /etc/apt/keyrings/grafana.gpg /tmp/grafana.gpg.key
echo 'deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com stable main' | sudo tee /etc/apt/sources.list.d/grafana.list

# IPv4 forcen (apt.grafana.com hat IPv6-Probleme über manche Provider)
echo 'Acquire::ForceIPv4 true;' | sudo tee /etc/apt/apt.conf.d/99force-ipv4

# Install (LAN-Kabel empfohlen, ~150 MB Download)
sudo DEBIAN_FRONTEND=noninteractive apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y grafana

# SQLite-Plugin
sudo grafana cli --homepath /usr/share/grafana plugins install frser-sqlite-datasource

# Datasource auto-provisionieren
sudo cp grafana/datasource.yaml /etc/grafana/provisioning/datasources/smartroom.yaml

# Service starten
sudo systemctl daemon-reload
sudo systemctl enable --now grafana-server
```

**Erreichbar:** `http://<pi-ip>:3000` — Login `admin` / `admin` → Passwort setzen.

**Dashboard importieren:** Grafana → Dashboards → New → Import → Raw URL:
`https://raw.githubusercontent.com/uhlersan14/SmartRoomMonitor/main/grafana/dashboard.json`

## Wichtige Hinweise

### `systemd ProtectHome=true`

Der `grafana-server.service` hat `ProtectHome=true` aktiviert. Das blockiert **jeglichen Zugriff** auf `/home/` für den Grafana-Dienst, **unabhängig** von Datei-Permissions.

→ DB **muss** ausserhalb von `/home/` liegen. Wir verwenden `/var/lib/smartroom-data/smartroom.db` mit Symlink in `~/SmartRoomMonitor/smartroom.db` für Code-Kompatibilität.

### Bookworm Camera-Tools

Die alten `libcamera-*` Befehle wurden durch `rpicam-*` ersetzt. Code in unserem Repo nutzt `rpicam-jpeg` / `rpicam-hello`.

### dpkg lockup nach Updates

Falls `apt` hängt mit "dpkg was interrupted":
```bash
# Defektes Paket finden
sudo dpkg --audit
# Falls rpi-chromium-mods o.ä.:
sudo dpkg --remove --force-remove-reinstreq <paketname>
sudo DEBIAN_FRONTEND=noninteractive dpkg --configure -a
```
