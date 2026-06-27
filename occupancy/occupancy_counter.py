#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SmartRoomMonitor - Personenzaehlung per Kamera.

Nimmt periodisch ein Foto mit der Pi-Kamera auf (rpicam-still), zaehlt darauf
die Personen mit dem OpenCV-HOG-Detektor und schreibt die Anzahl in die
Tabelle `room_occupancy`. So laesst sich die Raumbelegung im Grafana-Dashboard
gegen den CO2-Verlauf darstellen.

Datenschutz by Design: Es wird ausschliesslich die ANZAHL Personen gespeichert.
Das aufgenommene Bild wird nach der Auswertung sofort geloescht - es verlaesst
den Pi nie und wird nicht persistiert.

Aufruf:
    python3 occupancy_counter.py            # Endlosschleife (alle 60 s)
    python3 occupancy_counter.py --once     # einmalig (zum Testen)
    python3 occupancy_counter.py --interval 30 --db /pfad/smartroom.db
"""

import argparse
import os
import sqlite3
import subprocess
import sys
import tempfile
import time

import cv2

DEFAULT_DB = os.path.expanduser("~/SmartRoomMonitor/smartroom.db")
DEFAULT_INTERVAL = 60           # Sekunden zwischen zwei Aufnahmen
MIN_WEIGHT = 0.6                # HOG-Konfidenzschwelle (schwache Treffer verwerfen)


def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def capture(path, width=640, height=480):
    """Nimmt mit rpicam-still ein einzelnes JPEG auf (Bookworm-Standardtool)."""
    cmd = [
        "rpicam-still", "-n", "--immediate", "-t", "400",
        "--width", str(width), "--height", str(height),
        "-o", path,
    ]
    subprocess.run(cmd, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   timeout=25)


def make_detector():
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    return hog


def count_people(hog, img):
    """Zaehlt Personen im Bild via HOG + Non-Maximum-Suppression."""
    rects, weights = hog.detectMultiScale(
        img, winStride=(8, 8), padding=(8, 8), scale=1.05)
    boxes, scores = [], []
    for (x, y, w, h), wt in zip(rects, weights):
        score = float(wt[0]) if hasattr(wt, "__len__") else float(wt)
        if score < MIN_WEIGHT:
            continue
        boxes.append([int(x), int(y), int(w), int(h)])
        scores.append(score)
    if not boxes:
        return 0
    # Ueberlappende Boxen zusammenfassen, damit eine Person nicht doppelt zaehlt
    idx = cv2.dnn.NMSBoxes(boxes, scores, score_threshold=MIN_WEIGHT,
                           nms_threshold=0.4)
    return len(idx) if len(idx) else 0


def write_count(db, count):
    con = sqlite3.connect(db, timeout=10)
    try:
        con.execute(
            "INSERT INTO room_occupancy (person_count) VALUES (?)", (count,))
        con.commit()
    finally:
        con.close()


def one_cycle(hog, db):
    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    tmp.close()
    try:
        capture(tmp.name)
        img = cv2.imread(tmp.name)
        if img is None:
            log("WARN: Bild konnte nicht gelesen werden - ueberspringe Zyklus")
            return
        count = count_people(hog, img)
        write_count(db, count)
        log(f"Personen erkannt: {count} -> in DB geschrieben")
    finally:
        # Privacy: Bild IMMER sofort loeschen (auch im Fehlerfall)
        try:
            os.remove(tmp.name)
        except OSError:
            pass


def main():
    ap = argparse.ArgumentParser(description="Personenzaehlung per Pi-Kamera")
    ap.add_argument("--db", default=DEFAULT_DB, help="Pfad zur SQLite-DB")
    ap.add_argument("--interval", type=int, default=DEFAULT_INTERVAL,
                    help="Sekunden zwischen den Aufnahmen")
    ap.add_argument("--once", action="store_true",
                    help="nur einmal ausfuehren (zum Testen)")
    args = ap.parse_args()

    if not os.path.exists(args.db):
        log(f"FEHLER: DB nicht gefunden: {args.db}")
        sys.exit(1)

    hog = make_detector()
    log(f"Occupancy-Counter gestartet (DB={args.db}, Intervall={args.interval}s)")

    if args.once:
        one_cycle(hog, args.db)
        return

    while True:
        try:
            one_cycle(hog, args.db)
        except subprocess.TimeoutExpired:
            log("WARN: Kamera-Timeout - ueberspringe Zyklus")
        except Exception as e:  # robust: ein Fehler darf den Dienst nicht killen
            log(f"WARN: Fehler im Zyklus: {e}")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
