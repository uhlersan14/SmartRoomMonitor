#!/usr/bin/env bash
# Auf dem Raspberry Pi ausfuehren. Richtet die Kamera-Personenzaehlung ein.
set -e

REPO="/home/pi/SmartRoomMonitor"
cd "$REPO"

echo "== 1/5  Neuesten Code holen =="
git pull origin main

echo "== 2/5  OpenCV sicherstellen (prebuilt, keine Kompilierung) =="
if python3 -c 'import cv2' 2>/dev/null; then
  echo "OpenCV bereits vorhanden: $(python3 -c 'import cv2; print(cv2.__version__)')"
else
  sudo apt-get update -qq
  sudo apt-get install -y python3-opencv
fi

echo "== 3/5  Kamera-Test (einmalige Aufnahme + Zaehlung) =="
python3 occupancy/occupancy_counter.py --once

echo "== 4/5  systemd-Dienst installieren =="
sudo cp occupancy/smartroom-occupancy.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now smartroom-occupancy

echo "== 5/5  Status =="
sleep 3
systemctl status smartroom-occupancy --no-pager | head -n 12
echo
echo "Fertig. Live-Log:  journalctl -u smartroom-occupancy -f"
