# Grafana Dashboard

## Auto-Provisioning (empfohlen)

```bash
sudo cp grafana/datasource.yaml /etc/grafana/provisioning/datasources/smartroom.yaml
sudo systemctl restart grafana-server
```

→ Datasource `SmartRoomDB` ist dann automatisch verfügbar (zeigt auf `/home/pi/SmartRoomMonitor/smartroom.db`).

## Dashboard importieren

1. Grafana öffnen: `http://<pi-ip>:3000`
2. Login `admin` / `admin` → Passwort setzen
3. Dashboards → New → Import → JSON-Inhalt aus `grafana/dashboard.json` einfügen
4. Datasource: `SmartRoomDB` auswählen
5. Save

## Panels

| Panel | Beschreibung |
|-------|--------------|
| Aktuelle CO₂ ppm | Stat-Panel, Ampel grün/gelb/rot |
| Temperatur °C | Aktueller Wert |
| Luftfeuchte % | Aktueller Wert |
| CO₂ Verlauf | Zeitreihe letzte 24h |
| Temperatur & Luftfeuchte | Zeitreihe letzte 24h |

## Plugin

`frser-sqlite-datasource` muss installiert sein:
```bash
sudo grafana-cli plugins install frser-sqlite-datasource
sudo systemctl restart grafana-server
```
