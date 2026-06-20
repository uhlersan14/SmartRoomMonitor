# Node-RED Flow — CO₂ Alert

Dieser Flow ist die vom Dozenten geforderte Automatisierungs-Komponente:
Grenzwert-Check → RGB-LED steuern + E-Mail-Alert.

## Was der Flow macht

```
[inject 30s] → [HTTP GET /api/latest] → [function: Grenzwert pruefen]
                                                  ├─→ [exec: led_controller.py --set <farbe>]
                                                  └─→ [rate-limit] → [e-mail] (nur bei rot)
```

- Holt alle 30s den letzten Messwert vom Flask-Backend (`/api/latest`).
- Bestimmt die Ampel-Farbe: gruen < Warnung, gelb Warnung–Kritisch, rot ≥ Kritisch.
- Setzt die RGB-LED ueber `sensor/led_controller.py --set <farbe>`.
- Schickt bei **rot** eine E-Mail — maximal **1 Mail pro 30 Minuten** (rate-limit verhindert Spam).

Die Grenzwerte kommen live aus der SQLite-DB (im Flask-Formular auf Port 5000 einstellbar) — kein Neustart noetig.

## Installation auf dem Pi

```bash
# 1. Node-RED installieren (offizielles Pi-Script)
bash <(curl -sL https://raw.githubusercontent.com/node-red/linux-installers/master/deb/update-nodejs-and-nodered)

# 2. Als Autostart aktivieren
sudo systemctl enable --now nodered.service

# 3. E-Mail-Node-Palette installieren
cd ~/.node-red
npm install node-red-node-email
sudo systemctl restart nodered.service
```

Node-RED ist danach erreichbar unter `http://<pi-ip>:1880`.

## Flow importieren

1. Node-RED-Editor oeffnen (`http://<pi-ip>:1880`).
2. Menue (oben rechts) → **Import** → Inhalt von `nodered/flow.json` einfuegen → **Import**.
3. **Deploy** klicken.

## E-Mail konfigurieren (Gmail-Beispiel)

Doppelklick auf den **E-Mail Alert** Node:

| Feld | Wert |
|------|------|
| Server | `smtp.gmail.com` |
| Port | `465` |
| To | deine Empfaenger-Adresse |
| Userid | deine Gmail-Adresse |
| Password | **Gmail App-Passwort** (nicht das normale Passwort!) |

> Gmail braucht ein **App-Passwort**: Google-Konto → Sicherheit → 2FA aktivieren → App-Passwoerter → neues erzeugen.

Danach **Deploy**.

## Sicherheit / Datenschutz

- **Keine Zugangsdaten im Repo!** Node-RED speichert Userid/Password verschluesselt in
  `~/.node-red/flows_cred.json` — diese Datei wird **nie** committet.
- Der exportierte `flow.json` enthaelt bewusst keine Credentials.

## Testen ohne hohen CO₂-Wert

Grenzwerte im Flask-Formular (`http://<pi-ip>:5000`) kurz tief setzen (z.B. Warnung 500, Kritisch 600).
Dann sollte die LED auf gelb/rot springen und — bei rot — eine Test-Mail kommen. Danach Grenzwerte zurueckstellen.
